"""
Regression Discontinuity (RD) robust local polynomial estimator.

Implements a minimal but verifiable sharp RD estimation path,
aligning with Calonico, Cattaneo, and Titiunik (2014a) and
subsequent rdrobust package literature.

This is a clean re-implementation of the core algorithm
(local polynomial WLS + bias correction + robust inference)
using only NumPy/SciPy, adapted to the statapy ResultSchema.

Supported:
- Sharp RD (deriv=0) only in this minimal subset
- p (polynomial order for point est.), q (for bias correction)
- Explicit bandwidth h, optional bias bandwidth b
- Kernels: triangular, epanechnikov, uniform
- VCE: nn (nearest-neighbor), hc0

Explicitly unsupported (hard-rejected by wrapper):
- fuzzy RD, covariates, weights, clustering
- deriv > 0 (kink designs)
- Automatic bandwidth selectors (mserd, msetwo, etc.)
"""

from __future__ import annotations

import math
import numpy as np
from scipy import linalg, stats

from statapy.results.result import (
    CoefficientRow,
    DiagnosticsInfo,
    FitInfo,
    ModelInfo,
    ProvenanceInfo,
    ResultSchema,
    SampleInfo,
    VarianceInfo,
)


def _kernel_weight(x: np.ndarray, c: float, h: float, kernel: str) -> np.ndarray:
    """Compute kernel weights for local polynomial regression."""
    u = (x - c) / h
    inside = np.abs(u) <= 1.0
    w = np.zeros_like(u, dtype=float)
    k = kernel.lower()
    if k in ("triangular", "tri"):
        w[inside] = (1.0 - np.abs(u[inside])) / h
    elif k in ("epanechnikov", "epa"):
        w[inside] = 0.75 * (1.0 - u[inside] ** 2) / h
    elif k in ("uniform", "uni"):
        w[inside] = 0.5 / h
    else:
        raise ValueError(f"Unsupported kernel: {kernel}")
    return w


def _wls_poly(y: np.ndarray, x: np.ndarray, c: float, w: np.ndarray, order: int):
    """
    Weighted least squares local polynomial regression.

    Supports both single-column and multi-column y (e.g. when covariates
    are appended as additional RHS columns).

    Returns
    -------
    beta : np.ndarray, shape (order+1,) or (order+1, ncols)
    inv_gram : np.ndarray, shape (order+1, order+1)
    """
    n = len(x)
    R = np.zeros((n, order + 1), dtype=float)
    for j in range(order + 1):
        R[:, j] = (x - c) ** j
    # Cholesky of R' W R using weighted R
    Rw = R * np.sqrt(w[:, None])
    gram = Rw.T @ Rw
    try:
        L = linalg.cholesky(gram, lower=True)
        invL = linalg.solve_triangular(L, np.eye(order + 1), lower=True)
        inv_gram = invL.T @ invL
    except linalg.LinAlgError as exc:
        raise ValueError("Local polynomial design matrix is singular; check variability near cutoff.") from exc
    if y.ndim == 1:
        beta = inv_gram @ (R.T @ (w * y))
    else:
        beta = inv_gram @ (R.T @ (w[:, None] * y))
    return beta, inv_gram


def _nn_residuals(x: np.ndarray, y: np.ndarray, matches: int = 3) -> np.ndarray:
    """
    Nearest-neighbor variance estimator residuals.

    For each observation, find the nearest matches in x (excluding self),
    average their y values, and compute the leave-neighborhood residual.
    """
    n = len(y)
    res = np.empty(n, dtype=float)
    # For efficiency on moderate n, use sorting and linear scan.
    # x is assumed already sorted.
    for i in range(n):
        # search left and right for neighbors
        left = i - 1
        right = i + 1
        collected = []
        while len(collected) < matches and (left >= 0 or right < n):
            dl = x[i] - x[left] if left >= 0 else np.inf
            dr = x[right] - x[i] if right < n else np.inf
            if dl <= dr:
                if left >= 0:
                    collected.append(left)
                    left -= 1
            else:
                if right < n:
                    collected.append(right)
                    right += 1
        inds = collected[:matches]
        y_bar = np.mean(y[inds])
        Ji = len(inds)
        res[i] = math.sqrt(Ji / (Ji + 1)) * (y[i] - y_bar)
    return res


def _vce_nn(inv_gram: np.ndarray, R: np.ndarray, w: np.ndarray, res: np.ndarray) -> np.ndarray:
    """Conventional variance matrix using nearest-neighbor residuals."""
    n = R.shape[0]
    M = np.zeros((R.shape[1], R.shape[1]), dtype=float)
    for i in range(n):
        ri = R[i, :] * w[i] * res[i]
        M += np.outer(ri, ri)
    return inv_gram @ M @ inv_gram


def _vce_hc0(inv_gram: np.ndarray, R: np.ndarray, w: np.ndarray, res: np.ndarray) -> np.ndarray:
    """Heteroskedasticity-robust plug-in residual variance (hc0)."""
    n = R.shape[0]
    M = np.zeros((R.shape[1], R.shape[1]), dtype=float)
    for i in range(n):
        ri = R[i, :] * w[i] * res[i]
        M += np.outer(ri, ri)
    return inv_gram @ M @ inv_gram


def _rdrobust_vce_multi(s: np.ndarray, RX: np.ndarray, res: np.ndarray) -> np.ndarray:
    """
    Multi-dimensional sandwich VCE for rdrobust with covariates.

    Aligns with Mata rdrobust_vce() for d > 0:
    M = sum_{i,j} (RX' diag(s_i*s_j*res_i*res_j) RX)

    Parameters
    ----------
    s : np.ndarray, shape (d+1,)
        Linear combination weights (e.g. [1, -gamma_1, -gamma_2, ...]).
    RX : np.ndarray, shape (n, k)
        Weighted design matrix (already multiplied by kernel weights).
    res : np.ndarray, shape (n, d+1)
        Residual matrix [res_y, res_Z1, ...].
    """
    n, k = RX.shape
    d = len(s) - 1
    M = np.zeros((k, k), dtype=float)
    if d == 0:
        for i in range(n):
            ri = RX[i, :] * res[i, 0]
            M += np.outer(ri, ri)
    else:
        for i in range(d + 1):
            SS = res[:, i:i+1] * res  # (n, d+1)
            for j in range(d + 1):
                factor = s[i] * s[j] * SS[:, j]
                RXf = RX * factor[:, None]
                M += RXf.T @ RX
    return M


def _rdrobust_bw(Y, X, c, o, nu, o_B, h_V, h_B, scale,
                 vce, nnmatch, kernel, covs=None, covs_drop_coll=True):
    """
    Single-side bandwidth component computation.

    Returns (V, B, R, rate) matching Mata rdrobust_bw().
    """
    w = _kernel_weight(X, c, h_V, kernel)
    ind = w > 0
    eY = Y[ind]
    eX = X[ind]
    eW = w[ind]
    n_V = len(eY)

    R_V = np.zeros((n_V, o + 1), dtype=float)
    for j in range(o + 1):
        R_V[:, j] = (eX - c) ** j

    if covs is not None:
        Z = covs[ind, :] if covs.ndim == 2 else covs[ind][:, None]
        if Z.ndim == 1:
            Z = Z[:, None]
        D_V = np.column_stack((eY, Z))
    else:
        D_V = eY[:, None]

    beta_V, invG_V = _wls_poly(D_V, eX, c, eW, o)

    # s vector
    if covs is not None:
        dZ = Z.shape[1]
        U = (R_V * eW[:, None]).T @ D_V
        ZWD = (Z * eW[:, None]).T @ D_V
        colsZ = np.arange(1, 1 + dZ)
        UiGU = U[:, colsZ].T @ (invG_V @ U)
        ZWZ = ZWD[:, colsZ] - UiGU[:, colsZ]
        ZWY = ZWD[:, 0] - UiGU[:, 0]
        if covs_drop_coll:
            gamma = np.linalg.pinv(ZWZ) @ ZWY
        else:
            try:
                L = linalg.cholesky(ZWZ, lower=True)
                gamma = linalg.solve_triangular(L, ZWY, lower=True)
                gamma = linalg.solve_triangular(L.T, gamma, lower=False)
            except linalg.LinAlgError:
                gamma = np.linalg.pinv(ZWZ) @ ZWY
        s = np.append(1.0, -gamma)
    else:
        s = np.array([1.0])
        dZ = 0

    d = len(s) - 1

    # Residuals
    predicts_V = R_V @ beta_V
    if vce == "nn":
        res_V = _nn_residuals(eX, eY, nnmatch)[:, None]
        if covs is not None:
            res_Z = np.zeros((n_V, dZ), dtype=float)
            for i in range(dZ):
                res_Z[:, i] = _nn_residuals(eX, Z[:, i], nnmatch)
            res_V = np.column_stack((res_V, res_Z))
    else:
        res_V = (eY - predicts_V[:, 0])[:, None]
        if covs is not None:
            res_V = np.column_stack((res_V, Z - predicts_V[:, 1:]))

    # V_V
    RX = R_V * eW[:, None]
    M = _rdrobust_vce_multi(s, RX, res_V)
    V_V = (invG_V @ M @ invG_V)[nu, nu]

    # BConst
    v = RX.T @ ((eX - c) / h_V) ** (o + 1)
    Hp = np.zeros(o + 1)
    for j in range(o + 1):
        Hp[j] = h_V ** j
    BConst = (Hp * (invG_V @ v))[nu]

    # Bias bandwidth step
    w_B = _kernel_weight(X, c, h_B, kernel)
    ind_B = w_B > 0
    eY_B = Y[ind_B]
    eX_B = X[ind_B]
    eW_B = w_B[ind_B]
    n_B = len(eY_B)

    R_B = np.zeros((n_B, o_B + 1), dtype=float)
    for j in range(o_B + 1):
        R_B[:, j] = (eX_B - c) ** j

    if covs is not None:
        Z_B = covs[ind_B, :] if covs.ndim == 2 else covs[ind_B][:, None]
        if Z_B.ndim == 1:
            Z_B = Z_B[:, None]
        D_B = np.column_stack((eY_B, Z_B))
    else:
        D_B = eY_B[:, None]

    beta_B, invG_B = _wls_poly(D_B, eX_B, c, eW_B, o_B)

    BWreg = 0
    if scale > 0:
        predicts_B = R_B @ beta_B
        if vce == "nn":
            res_B = _nn_residuals(eX_B, eY_B, nnmatch)[:, None]
            if covs is not None:
                res_Z_B = np.zeros((n_B, dZ), dtype=float)
                for i in range(dZ):
                    res_Z_B[:, i] = _nn_residuals(eX_B, Z_B[:, i], nnmatch)
                res_B = np.column_stack((res_B, res_Z_B))
        else:
            res_B = (eY_B - predicts_B[:, 0])[:, None]
            if covs is not None:
                res_B = np.column_stack((res_B, Z_B - predicts_B[:, 1:]))

        RX_B = R_B * eW_B[:, None]
        M_B = _rdrobust_vce_multi(s, RX_B, res_B)
        V_B = (invG_B @ M_B @ invG_B)[-1, -1]
        BWreg = 3 * BConst ** 2 * V_B

    beta_aux = beta_B[-1, :] if beta_B.ndim > 1 else np.array([beta_B[-1]])
    B = np.sqrt(2 * (o + 1 - nu)) * BConst * np.dot(s, beta_aux)
    V = (2 * nu + 1) * h_V ** (2 * nu + 1) * V_V
    R_term = scale * (2 * (o + 1 - nu)) * BWreg
    rate = 1.0 / (2 * o + 3)

    return V, B, R_term, rate


def _rdbwselect_mserd(Y_l, X_l, Y_r, X_r, c, p, q, deriv, kernel, vce, nnmatch,
                      covs_l=None, covs_r=None, covs_drop_coll=True,
                      scaleregul=1, bwrestrict=True):
    """
    MSE-optimal common bandwidth selector for sharp RD (mserd).

    Implements the three-step plug-in procedure from CCT (2014a)
    and the official rdrobust/rdbwselect Python package.

    Returns (h, b) where h is the main bandwidth and b is the bias bandwidth.
    For mserd, h_l = h_r = h and b_l = b_r = b.
    """
    X_all = np.concatenate([X_l, X_r])
    N = len(X_all)
    x_iq = np.quantile(X_all, 0.75) - np.quantile(X_all, 0.25)
    BWp = min(np.std(X_all, ddof=1), x_iq / 1.349)

    k = kernel.lower()
    if k in ("epanechnikov", "epa"):
        C_c = 2.34
    elif k in ("uniform", "uni"):
        C_c = 1.843
    else:
        C_c = 2.576

    # Mass points handling (simplified: always check and adjust)
    X_uniq_l = np.sort(np.unique(X_l))[::-1]
    X_uniq_r = np.unique(X_r)
    M_l = len(X_uniq_l)
    M_r = len(X_uniq_r)
    M = M_l + M_r
    mass_l = 1 - M_l / len(X_l)
    mass_r = 1 - M_r / len(X_r)
    bwcheck = None
    if mass_l >= 0.1 or mass_r >= 0.1:
        bwcheck = 10

    c_bw = C_c * BWp * N ** (-1.0 / 5.0)
    if M < N:
        c_bw = C_c * BWp * M ** (-1.0 / 5.0)

    x_min = np.min(X_all)
    x_max = np.max(X_all)
    if bwrestrict:
        bw_max = max(abs(c - x_min), abs(c - x_max))
        c_bw = min(c_bw, bw_max)

    if bwcheck is not None:
        bwcheck_l = min(bwcheck, M_l)
        bwcheck_r = min(bwcheck, M_r)
        bw_min_l = np.abs(X_uniq_l - c)[bwcheck_l - 1] + 1e-8
        bw_min_r = np.abs(X_uniq_r - c)[bwcheck_r - 1] + 1e-8
        c_bw = max(c_bw, bw_min_l, bw_min_r)

    range_l = np.abs(np.max(X_l) - np.min(X_l))
    range_r = np.abs(np.max(X_r) - np.min(X_r))

    # Step 1: pilot d_bw (for bias bandwidth)
    C_d_l = _rdrobust_bw(Y_l, X_l, c, q + 1, q + 1, q + 2, c_bw, range_l, 0,
                         vce, nnmatch, kernel, covs_l, covs_drop_coll)
    C_d_r = _rdrobust_bw(Y_r, X_r, c, q + 1, q + 1, q + 2, c_bw, range_r, 0,
                         vce, nnmatch, kernel, covs_r, covs_drop_coll)

    V_d_l, B_d_l, R_d_l, rate_d = C_d_l
    V_d_r, B_d_r, R_d_r, _ = C_d_r

    d_bw = ((V_d_l + V_d_r) / (B_d_r - B_d_l) ** 2) ** rate_d
    if bwrestrict:
        d_bw = min(d_bw, bw_max)

    # Step 2: b_bw
    C_b_l = _rdrobust_bw(Y_l, X_l, c, q, p + 1, q + 1, c_bw, d_bw, scaleregul,
                         vce, nnmatch, kernel, covs_l, covs_drop_coll)
    C_b_r = _rdrobust_bw(Y_r, X_r, c, q, p + 1, q + 1, c_bw, d_bw, scaleregul,
                         vce, nnmatch, kernel, covs_r, covs_drop_coll)

    V_b_l, B_b_l, R_b_l, rate_b = C_b_l
    V_b_r, B_b_r, R_b_r, _ = C_b_r

    denom_b = (B_b_r - B_b_l) ** 2 + scaleregul * (R_b_r + R_b_l)
    b_bw = ((V_b_l + V_b_r) / denom_b) ** rate_b
    if bwrestrict:
        b_bw = min(b_bw, bw_max)

    # Step 3: h_bw
    C_h_l = _rdrobust_bw(Y_l, X_l, c, p, deriv, q, c_bw, b_bw, scaleregul,
                         vce, nnmatch, kernel, covs_l, covs_drop_coll)
    C_h_r = _rdrobust_bw(Y_r, X_r, c, p, deriv, q, c_bw, b_bw, scaleregul,
                         vce, nnmatch, kernel, covs_r, covs_drop_coll)

    V_h_l, B_h_l, R_h_l, rate_h = C_h_l
    V_h_r, B_h_r, R_h_r, _ = C_h_r

    denom_h = (B_h_r - B_h_l) ** 2 + scaleregul * (R_h_r + R_h_l)
    h_bw = ((V_h_l + V_h_r) / denom_h) ** rate_h
    if bwrestrict:
        h_bw = min(h_bw, bw_max)

    return h_bw, b_bw


class RDRobust:
    """
    Sharp Regression Discontinuity local polynomial estimator.

    Parameters
    ----------
    data : pd.DataFrame
    y : str
        Outcome variable.
    x : str
        Running (forcing) variable.
    c : float, default 0.0
        Cutoff.
    h : float or tuple[float, float] or None
        Main bandwidth(s). If scalar, used on both sides.
        If None and bwselect is also None, an error is raised.
    b : float or tuple[float, float] or None
        Bias bandwidth(s). Defaults to h if None.
    p : int, default 1
        Polynomial order for point estimation.
    q : int, default 2
        Polynomial order for bias correction.
    deriv : int, default 0
        Derivative order (only 0 supported in this subset).
    kernel : str, default "triangular"
    vce : str, default "nn"
        Variance estimator: "nn" or "hc0".
    nnmatch : int, default 3
        Minimum neighbors for nn VCE.
    level : int, default 95
        Confidence level.
    bwselect : str or None
        Bandwidth selector. Supported: "mserd". If h is provided,
        bwselect is ignored.
    covs : list[str] or str or None
        Covariate variable name(s) for covariate-adjusted RD.
    covs_drop : bool, default True
        Drop collinear covariates.
    scaleregul : float, default 1
        Regularization term scaling for bandwidth selectors.
    """

    def __init__(
        self,
        data,
        y: str,
        x: str,
        c: float = 0.0,
        h: float | tuple[float, float] | None = None,
        b: float | tuple[float, float] | None = None,
        p: int = 1,
        q: int = 2,
        deriv: int = 0,
        kernel: str = "triangular",
        vce: str = "nn",
        nnmatch: int = 3,
        level: int = 95,
        bwselect: str | None = None,
        covs: list[str] | str | None = None,
        covs_drop: bool = True,
        scaleregul: float = 1.0,
    ):
        self.data = data.copy()
        self.y_var = y
        self.x_var = x
        self.c = float(c)
        self.p = int(p)
        self.q = int(q)
        self.deriv = int(deriv)
        self.kernel = kernel
        self.vce = vce.lower()
        self.nnmatch = int(nnmatch)
        self.level = float(level)
        self.bwselect = bwselect.lower() if bwselect is not None else None
        self.covs = covs
        self.covs_drop = bool(covs_drop)
        self.scaleregul = float(scaleregul)

        if self.deriv != 0:
            raise NotImplementedError("Only deriv=0 (sharp RD) is supported in this subset.")
        if self.p < 0 or self.q <= self.p:
            raise ValueError("Require 0 <= p < q.")
        if self.vce not in ("nn", "hc0"):
            raise NotImplementedError("Only vce='nn' and vce='hc0' are supported in this subset.")
        if self.bwselect is not None and self.bwselect not in ("mserd", "cerrd"):
            raise NotImplementedError(
                f"bwselect='{self.bwselect}' is not supported. Use 'mserd' or provide h explicitly."
            )
        if self.bwselect == "cerrd":
            raise NotImplementedError("bwselect='cerrd' is not yet implemented.")

        # Bandwidth parsing (may be None if bwselect is used)
        if h is not None:
            if np.isscalar(h):
                self.h_l = self.h_r = float(h)
            else:
                self.h_l, self.h_r = float(h[0]), float(h[1])
            if b is None:
                self.b_l, self.b_r = self.h_l, self.h_r
            elif np.isscalar(b):
                self.b_l = self.b_r = float(b)
            else:
                self.b_l, self.b_r = float(b[0]), float(b[1])
            if min(self.h_l, self.h_r, self.b_l, self.b_r) <= 0:
                raise ValueError("Bandwidths must be positive.")
        else:
            self.h_l = self.h_r = None
            self.b_l = self.b_r = None
            if self.bwselect is None:
                raise ValueError("Either h or bwselect must be provided.")

    def fit(self) -> ResultSchema:
        # Covariate extraction and missing-value handling
        cov_names = []
        if self.covs is not None:
            if isinstance(self.covs, str):
                cov_names = [self.covs]
            else:
                cov_names = list(self.covs)
            cols = [self.y_var, self.x_var] + cov_names
        else:
            cols = [self.y_var, self.x_var]

        df = self.data[cols].copy()
        df = df.dropna()
        y = df[self.y_var].to_numpy(dtype=float)
        x = df[self.x_var].to_numpy(dtype=float)
        if cov_names:
            covs_all = df[cov_names].to_numpy(dtype=float)
        else:
            covs_all = None

        n_input = len(self.data)
        nobs = len(y)

        if self.c <= np.min(x) or self.c >= np.max(x):
            raise ValueError("Cutoff c must lie strictly within the range of the running variable.")

        # Sort by running variable
        order = np.argsort(x, kind="stable")
        x = x[order]
        y = y[order]
        if covs_all is not None:
            covs_all = covs_all[order, :]

        left_mask = x < self.c
        right_mask = ~left_mask

        X_l = x[left_mask]
        X_r = x[right_mask]
        Y_l = y[left_mask]
        Y_r = y[right_mask]

        N_l = len(X_l)
        N_r = len(Y_r)

        if N_l < self.p + 1 or N_r < self.p + 1:
            raise ValueError("Not enough observations on at least one side of the cutoff for the chosen polynomial order.")

        if covs_all is not None:
            covs_l = covs_all[left_mask, :]
            covs_r = covs_all[right_mask, :]
        else:
            covs_l = covs_r = None

        # Automatic bandwidth selection
        if self.h_l is None:
            h_bw, b_bw = _rdbwselect_mserd(
                Y_l, X_l, Y_r, X_r, self.c, self.p, self.q, self.deriv,
                self.kernel, self.vce, self.nnmatch,
                covs_l, covs_r, self.covs_drop, self.scaleregul,
            )
            self.h_l = self.h_r = h_bw
            self.b_l = self.b_r = b_bw

        # Kernel weights
        w_h_l = _kernel_weight(X_l, self.c, self.h_l, self.kernel)
        w_h_r = _kernel_weight(X_r, self.c, self.h_r, self.kernel)
        w_b_l = _kernel_weight(X_l, self.c, self.b_l, self.kernel)
        w_b_r = _kernel_weight(X_r, self.c, self.b_r, self.kernel)

        N_h_l = int(np.sum(w_h_l > 0))
        N_h_r = int(np.sum(w_h_r > 0))
        N_b_l = int(np.sum(w_b_l > 0))
        N_b_r = int(np.sum(w_b_r > 0))

        ind_l = w_b_l > 0
        ind_r = w_b_r > 0
        if self.h_l > self.b_l:
            ind_l = w_h_l > 0
        if self.h_r > self.b_r:
            ind_r = w_h_r > 0

        eX_l = X_l[ind_l]
        eX_r = X_r[ind_r]
        eY_l = Y_l[ind_l]
        eY_r = Y_r[ind_r]
        W_h_l = w_h_l[ind_l]
        W_h_r = w_h_r[ind_r]
        W_b_l = w_b_l[ind_l]
        W_b_r = w_b_r[ind_r]

        if covs_all is not None:
            eZ_l = covs_l[ind_l, :]
            eZ_r = covs_r[ind_r, :]
        else:
            eZ_l = eZ_r = None

        eN_l = len(eX_l)
        eN_r = len(eX_r)

        # Design matrices
        R_q_l = np.zeros((eN_l, self.q + 1), dtype=float)
        R_q_r = np.zeros((eN_r, self.q + 1), dtype=float)
        for j in range(self.q + 1):
            R_q_l[:, j] = (eX_l - self.c) ** j
            R_q_r[:, j] = (eX_r - self.c) ** j
        R_p_l = R_q_l[:, : self.p + 1]
        R_p_r = R_q_r[:, : self.p + 1]

        # Multi-column WLS when covs exist
        if eZ_l is not None:
            D_l = np.column_stack((eY_l, eZ_l))
            D_r = np.column_stack((eY_r, eZ_r))
        else:
            D_l = eY_l[:, None]
            D_r = eY_r[:, None]

        beta_p_l, invG_p_l = _wls_poly(D_l, eX_l, self.c, W_h_l, self.p)
        beta_p_r, invG_p_r = _wls_poly(D_r, eX_r, self.c, W_h_r, self.p)
        beta_q_l, invG_q_l = _wls_poly(D_l, eX_l, self.c, W_b_l, self.q)
        beta_q_r, invG_q_r = _wls_poly(D_r, eX_r, self.c, W_b_r, self.q)

        # s vector (covariate-adjustment weights)
        if eZ_l is not None:
            dZ = eZ_l.shape[1]
            U_l = (R_p_l * W_h_l[:, None]).T @ D_l
            U_r = (R_p_r * W_h_r[:, None]).T @ D_r
            ZWD_l = (eZ_l * W_h_l[:, None]).T @ D_l
            ZWD_r = (eZ_r * W_h_r[:, None]).T @ D_r
            colsZ = np.arange(1, 1 + dZ)
            UiGU_l = U_l[:, colsZ].T @ (invG_p_l @ U_l)
            UiGU_r = U_r[:, colsZ].T @ (invG_p_r @ U_r)
            ZWZ_l = ZWD_l[:, colsZ] - UiGU_l[:, colsZ]
            ZWZ_r = ZWD_r[:, colsZ] - UiGU_r[:, colsZ]
            ZWY_l = ZWD_l[:, 0] - UiGU_l[:, 0]
            ZWY_r = ZWD_r[:, 0] - UiGU_r[:, 0]
            ZWZ = ZWZ_r + ZWZ_l
            ZWY = ZWY_r + ZWY_l
            if self.covs_drop:
                gamma = np.linalg.pinv(ZWZ) @ ZWY
            else:
                try:
                    L = linalg.cholesky(ZWZ, lower=True)
                    gamma = linalg.solve_triangular(L, ZWY, lower=True)
                    gamma = linalg.solve_triangular(L.T, gamma, lower=False)
                except linalg.LinAlgError:
                    gamma = np.linalg.pinv(ZWZ) @ ZWY
            s = np.append(1.0, -gamma)
        else:
            s = np.array([1.0])
            dZ = 0

        # Bias-correction design Q_q
        u_l = (eX_l - self.c) / self.h_l
        u_r = (eX_r - self.c) / self.h_r
        L_l = (R_p_l * W_h_l[:, None]).T @ (u_l ** (self.p + 1))
        L_r = (R_p_r * W_h_r[:, None]).T @ (u_r ** (self.p + 1))
        e_p1 = np.zeros(self.q + 1, dtype=float)
        e_p1[self.p + 1] = 1.0

        Q_q_l = (
            (R_p_l * W_h_l[:, None]).T
            - (self.h_l ** (self.p + 1)) * np.outer(L_l, e_p1) @ ((invG_q_l @ R_q_l.T) * W_b_l[None, :])
        ).T
        Q_q_r = (
            (R_p_r * W_h_r[:, None]).T
            - (self.h_r ** (self.p + 1)) * np.outer(L_r, e_p1) @ ((invG_q_r @ R_q_r.T) * W_b_r[None, :])
        ).T

        beta_bc_l = invG_p_l @ (Q_q_l.T @ D_l)
        beta_bc_r = invG_p_r @ (Q_q_r.T @ D_r)

        # Point estimates
        deriv = self.deriv
        scalepar = 1.0
        if eZ_l is None:
            tau_cl = scalepar * math.factorial(deriv) * (beta_p_r[deriv, 0] - beta_p_l[deriv, 0])
            tau_bc = scalepar * math.factorial(deriv) * (beta_bc_r[deriv, 0] - beta_bc_l[deriv, 0])
            tau_cl_l = scalepar * math.factorial(deriv) * beta_p_l[deriv, 0]
            tau_cl_r = scalepar * math.factorial(deriv) * beta_p_r[deriv, 0]
            tau_bc_l = scalepar * math.factorial(deriv) * beta_bc_l[deriv, 0]
            tau_bc_r = scalepar * math.factorial(deriv) * beta_bc_r[deriv, 0]
        else:
            tau_cl = float(np.matmul(scalepar * s.T, beta_p_r[deriv, :] - beta_p_l[deriv, :]))
            tau_bc = float(np.matmul(scalepar * s.T, beta_bc_r[deriv, :] - beta_bc_l[deriv, :]))
            tau_cl_l = float(np.matmul(scalepar * s.T, beta_p_l[deriv, :]))
            tau_cl_r = float(np.matmul(scalepar * s.T, beta_p_r[deriv, :]))
            tau_bc_l = float(np.matmul(scalepar * s.T, beta_bc_l[deriv, :]))
            tau_bc_r = float(np.matmul(scalepar * s.T, beta_bc_r[deriv, :]))

        bias_l = tau_cl_l - tau_bc_l
        bias_r = tau_cl_r - tau_bc_r

        # Variance estimation
        d = len(s) - 1
        if self.vce == "nn":
            res_h_l = _nn_residuals(eX_l, eY_l, self.nnmatch)[:, None]
            res_h_r = _nn_residuals(eX_r, eY_r, self.nnmatch)[:, None]
            if eZ_l is not None:
                res_Z_l = np.zeros((eN_l, dZ), dtype=float)
                res_Z_r = np.zeros((eN_r, dZ), dtype=float)
                for i in range(dZ):
                    res_Z_l[:, i] = _nn_residuals(eX_l, eZ_l[:, i], self.nnmatch)
                    res_Z_r[:, i] = _nn_residuals(eX_r, eZ_r[:, i], self.nnmatch)
                res_h_l = np.column_stack((res_h_l, res_Z_l))
                res_h_r = np.column_stack((res_h_r, res_Z_r))
            res_b_l = res_h_l
            res_b_r = res_h_r
        else:
            pred_h_l = R_p_l @ beta_p_l
            pred_h_r = R_p_r @ beta_p_r
            pred_b_l = R_q_l @ beta_q_l
            pred_b_r = R_q_r @ beta_q_r
            res_h_l = (eY_l - pred_h_l[:, 0])[:, None]
            res_h_r = (eY_r - pred_h_r[:, 0])[:, None]
            res_b_l = (eY_l - pred_b_l[:, 0])[:, None]
            res_b_r = (eY_r - pred_b_r[:, 0])[:, None]
            if eZ_l is not None:
                res_h_l = np.column_stack((res_h_l, eZ_l - pred_h_l[:, 1:]))
                res_h_r = np.column_stack((res_h_r, eZ_r - pred_h_r[:, 1:]))
                res_b_l = np.column_stack((res_b_l, eZ_l - pred_b_l[:, 1:]))
                res_b_r = np.column_stack((res_b_r, eZ_r - pred_b_r[:, 1:]))

        # VCE with multi-dimensional residuals when covs exist
        if d == 0:
            V_cl_l = _vce_hc0(invG_p_l, R_p_l, W_h_l, res_h_l[:, 0])
            V_cl_r = _vce_hc0(invG_p_r, R_p_r, W_h_r, res_h_r[:, 0])
            ones_l = np.ones_like(W_h_l)
            ones_r = np.ones_like(W_h_r)
            V_rb_l = _vce_hc0(invG_p_l, Q_q_l, ones_l, res_b_l[:, 0])
            V_rb_r = _vce_hc0(invG_p_r, Q_q_r, ones_r, res_b_r[:, 0])
        else:
            RX_l = R_p_l * W_h_l[:, None]
            RX_r = R_p_r * W_h_r[:, None]
            M_cl_l = _rdrobust_vce_multi(s, RX_l, res_h_l)
            M_cl_r = _rdrobust_vce_multi(s, RX_r, res_h_r)
            V_cl_l = invG_p_l @ M_cl_l @ invG_p_l
            V_cl_r = invG_p_r @ M_cl_r @ invG_p_r
            M_rb_l = _rdrobust_vce_multi(s, Q_q_l, res_b_l)
            M_rb_r = _rdrobust_vce_multi(s, Q_q_r, res_b_r)
            V_rb_l = invG_p_l @ M_rb_l @ invG_p_l
            V_rb_r = invG_p_r @ M_rb_r @ invG_p_r

        V_tau_cl = (scalepar ** 2) * (math.factorial(deriv) ** 2) * (V_cl_l[deriv, deriv] + V_cl_r[deriv, deriv])
        V_tau_rb = (scalepar ** 2) * (math.factorial(deriv) ** 2) * (V_rb_l[deriv, deriv] + V_rb_r[deriv, deriv])
        se_tau_cl = math.sqrt(V_tau_cl)
        se_tau_rb = math.sqrt(V_tau_rb)

        # Inference
        quant = -stats.norm.ppf(abs((1 - self.level / 100) / 2))

        methods = ["Conventional", "Bias-Corrected", "Robust"]
        coefs = [tau_cl, tau_bc, tau_bc]
        ses = [se_tau_cl, se_tau_cl, se_tau_rb]

        coefficients = []
        for name, beta, se in zip(methods, coefs, ses):
            t_stat = beta / se if se > 0 else np.nan
            pv = 2.0 * stats.norm.cdf(-abs(t_stat)) if se > 0 else np.nan
            ci_low = beta - quant * se
            ci_high = beta + quant * se
            coefficients.append(
                CoefficientRow(
                    name=name,
                    beta=beta,
                    std_err=se,
                    t_stat=t_stat,
                    p_value=pv,
                    ci_low=ci_low,
                    ci_high=ci_high,
                )
            )

        result = ResultSchema(
            model=ModelInfo(
                command="rdrobust",
                estimator_family="rd",
                vcetype=self.vce,
                has_constant=True,
            ),
            sample=SampleInfo(
                nobs=nobs,
                n_input_rows=n_input,
            ),
            fit=FitInfo(
                df_model=float(self.p + 1),
                df_resid=float(nobs - 2 * (self.p + 1)),
            ),
            coefficients=coefficients,
            variance=VarianceInfo(
                row_names=["RD_Estimate"],
                values=[[V_tau_rb]],
            ),
            diagnostics=DiagnosticsInfo(
                warnings=[],
            ),
            provenance=ProvenanceInfo(
                source="python",
                stata_version_target="17",
                stata_command="rdrobust",
            ),
        )

        result._rd_extras = {
            "N_l": N_l,
            "N_r": N_r,
            "N_h_l": N_h_l,
            "N_h_r": N_h_r,
            "N_b_l": N_b_l,
            "N_b_r": N_b_r,
            "c": self.c,
            "p": self.p,
            "q": self.q,
            "h_l": self.h_l,
            "h_r": self.h_r,
            "b_l": self.b_l,
            "b_r": self.b_r,
            "tau_cl": tau_cl,
            "tau_bc": tau_bc,
            "se_tau_cl": se_tau_cl,
            "se_tau_rb": se_tau_rb,
            "tau_cl_l": tau_cl_l,
            "tau_cl_r": tau_cl_r,
            "tau_bc_l": tau_bc_l,
            "tau_bc_r": tau_bc_r,
            "bias_l": bias_l,
            "bias_r": bias_r,
            "kernel": self.kernel,
            "vce": self.vce,
            "level": self.level,
        }

        return result
