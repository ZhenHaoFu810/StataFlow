"""
Regression Discontinuity (RD) robust local polynomial estimator.

Implements a minimal but verifiable sharp RD estimation path,
aligning with Calonico, Cattaneo, and Titiunik (2014a) and
subsequent rdrobust package literature.

This is a clean re-implementation of the core algorithm
(local polynomial WLS + bias correction + robust inference)
using only NumPy/SciPy, adapted to the stataflow ResultSchema.

Supported:
- Sharp RD (deriv=0)
- p (polynomial order for point est.), q (for bias correction)
- Explicit bandwidth h, optional bias bandwidth b
- Automatic bandwidth selectors: mserd, msesum, msetwo, msecomb1, msecomb2,
  cerrd, cersum, certwo, cercomb1, cercomb2
- Covariate adjustment via covs
- Kernels: triangular, epanechnikov, uniform
- VCE: nn (nearest-neighbor), hc0

Explicitly unsupported (hard-rejected by wrapper):
- clustering
- deriv > 0 (kink designs)
"""

from __future__ import annotations

import math
import numpy as np
from scipy import linalg, stats

from stataflow.results.result import (
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
        w[inside] = (1.0 - np.abs(u[inside]))
    elif k in ("epanechnikov", "epa"):
        w[inside] = 0.75 * (1.0 - u[inside] ** 2)
    elif k in ("uniform", "uni"):
        w[inside] = 0.5
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


def _vce_hc0(inv_gram: np.ndarray, R: np.ndarray, w: np.ndarray, res: np.ndarray) -> np.ndarray:
    """Heteroskedasticity-robust plug-in residual variance (hc0)."""
    n = R.shape[0]
    M = np.zeros((R.shape[1], R.shape[1]), dtype=float)
    for i in range(n):
        ri = R[i, :] * w[i] * res[i]
        M += np.outer(ri, ri)
    return inv_gram @ M @ inv_gram


# _vce_nn is functionally identical to _vce_hc0 in this implementation
def _vce_nn(inv_gram: np.ndarray, R: np.ndarray, w: np.ndarray, res: np.ndarray) -> np.ndarray:
    """Conventional variance matrix using nearest-neighbor residuals."""
    return _vce_hc0(inv_gram, R, w, res)


def _rdrobust_vce_multi(s: np.ndarray, RX: np.ndarray, res: np.ndarray, cluster_ids: np.ndarray | None = None) -> np.ndarray:
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
    cluster_ids : np.ndarray, shape (n,) or None
        Cluster identifiers. If provided, scores are summed within cluster
        before the outer product (cluster-robust meat).
    """
    if res.ndim == 1:
        res = res[:, None]
    scores = RX * (res @ s)[:, None]  # (n, k)
    if cluster_ids is None:
        return scores.T @ scores
    meat = np.zeros((RX.shape[1], RX.shape[1]), dtype=float)
    clusters = np.unique(cluster_ids)
    for g in clusters:
        mask = cluster_ids == g
        score_g = scores[mask].sum(axis=0)
        meat += np.outer(score_g, score_g)
    n, k = RX.shape
    if len(clusters) <= 1 or n <= k:
        return meat
    scale = ((n - 1) / (n - k)) * (len(clusters) / (len(clusters) - 1))
    return scale * meat


def _rdrobust_bw(Y, X, c, o, nu, o_B, h_V, h_B, scale,
                 vce, nnmatch, kernel, covs=None, covs_drop_coll=True,
                 cluster_ids=None):
    """
    Single-side bandwidth component computation.

    Returns (V, B, R, rate) matching Mata rdrobust_bw().
    """
    w = _kernel_weight(X, c, h_V, kernel)
    ind = w > 0
    eY = Y[ind]
    eX = X[ind]
    eW = w[ind]
    eC = cluster_ids[ind] if cluster_ids is not None else None
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

    len(s) - 1

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
    M = _rdrobust_vce_multi(s, RX, res_V, eC)
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
    eC_B = cluster_ids[ind_B] if cluster_ids is not None else None
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
        M_B = _rdrobust_vce_multi(s, RX_B, res_B, eC_B)
        V_B = (invG_B @ M_B @ invG_B)[-1, -1]
        BWreg = 3 * BConst ** 2 * V_B

    beta_aux = beta_B[-1, :] if beta_B.ndim > 1 else np.array([beta_B[-1]])
    B = np.sqrt(2 * (o + 1 - nu)) * BConst * np.dot(s, beta_aux)
    V = (2 * nu + 1) * h_V ** (2 * nu + 1) * V_V
    R_term = scale * (2 * (o + 1 - nu)) * BWreg
    rate = 1.0 / (2 * o + 3)

    return V, B, R_term, rate


def _compute_pilot_bw(X_l, X_r, c, kernel, masspoints="adjust", bwcheck=0, bwrestrict=True):
    """Compute initial pilot bandwidth c_bw and related bounds.

    Returns (c_bw, bw_max, range_l, range_r, M_l, M_r, masspoints_found, effective_bwcheck).
    """
    X_all = np.concatenate([X_l, X_r])
    N = len(X_all)
    N_l = len(X_l)
    N_r = len(X_r)
    x_iq = np.quantile(X_all, 0.75) - np.quantile(X_all, 0.25)
    BWp = min(np.std(X_all, ddof=1), x_iq / 1.349)

    k = kernel.lower()
    if k in ("epanechnikov", "epa"):
        C_c = 2.34
    elif k in ("uniform", "uni"):
        C_c = 1.843
    else:
        C_c = 2.576

    X_uniq_l = np.sort(np.unique(X_l))[::-1]
    X_uniq_r = np.unique(X_r)
    M_l = len(X_uniq_l)
    M_r = len(X_uniq_r)
    M = M_l + M_r

    # Mass points detection
    mass_l = 1.0 - M_l / N_l
    mass_r = 1.0 - M_r / N_r
    masspoints_found = (mass_l >= 0.2) or (mass_r >= 0.2)

    # Pilot bandwidth: use M instead of N when masspoints="adjust"
    if masspoints == "adjust":
        c_bw = C_c * BWp * M ** (-1.0 / 5.0)
    else:
        c_bw = C_c * BWp * N ** (-1.0 / 5.0)

    x_min = np.min(X_all)
    x_max = np.max(X_all)
    bw_max = None
    if bwrestrict:
        bw_max = max(abs(c - x_min), abs(c - x_max))
        c_bw = min(c_bw, bw_max)

    # Auto bwcheck when adjusting
    effective_bwcheck = bwcheck
    if masspoints == "adjust" and masspoints_found and bwcheck == 0:
        effective_bwcheck = 10

    # bwcheck enforcement
    if effective_bwcheck > 0:
        bwcheck_l = min(effective_bwcheck, M_l)
        bwcheck_r = min(effective_bwcheck, M_r)
        if bwcheck_l > 0 and bwcheck_r > 0:
            bw_min_l = np.abs(X_uniq_l - c)[bwcheck_l - 1] + 1e-8
            bw_min_r = np.abs(X_uniq_r - c)[bwcheck_r - 1] + 1e-8
            c_bw = max(c_bw, bw_min_l, bw_min_r)

    range_l = abs(c - np.min(X_l))
    range_r = abs(c - np.max(X_r))

    return c_bw, bw_max, range_l, range_r, M_l, M_r, masspoints_found, effective_bwcheck


def _three_step_bw_rd(Y_l, X_l, Y_r, X_r, c, p, q, deriv, kernel, vce, nnmatch,
                      covs_l, covs_r, covs_drop_coll, scaleregul, c_bw, bw_max,
                      range_l, range_r, bwrestrict, cluster_l=None, cluster_r=None):
    """Three-step plug-in for MSE-RD branch (difference criterion). Returns (h, b)."""
    # Step 1: pilot d_bw
    C_d_l = _rdrobust_bw(Y_l, X_l, c, q + 1, q + 1, q + 2, c_bw, range_l, 0,
                         vce, nnmatch, kernel, covs_l, covs_drop_coll, cluster_l)
    C_d_r = _rdrobust_bw(Y_r, X_r, c, q + 1, q + 1, q + 2, c_bw, range_r, 0,
                         vce, nnmatch, kernel, covs_r, covs_drop_coll, cluster_r)
    V_d_l, B_d_l, R_d_l, rate_d = C_d_l
    V_d_r, B_d_r, R_d_r, _ = C_d_r

    d_bw = ((V_d_l + V_d_r) / (B_d_r - B_d_l) ** 2) ** rate_d
    if bwrestrict and bw_max is not None:
        d_bw = min(d_bw, bw_max)

    # Step 2: b_bw
    C_b_l = _rdrobust_bw(Y_l, X_l, c, q, p + 1, q + 1, c_bw, d_bw, scaleregul,
                         vce, nnmatch, kernel, covs_l, covs_drop_coll, cluster_l)
    C_b_r = _rdrobust_bw(Y_r, X_r, c, q, p + 1, q + 1, c_bw, d_bw, scaleregul,
                         vce, nnmatch, kernel, covs_r, covs_drop_coll, cluster_r)
    V_b_l, B_b_l, R_b_l, rate_b = C_b_l
    V_b_r, B_b_r, R_b_r, _ = C_b_r

    denom_b = (B_b_r - B_b_l) ** 2 + scaleregul * (R_b_r + R_b_l)
    b_bw = ((V_b_l + V_b_r) / denom_b) ** rate_b
    if bwrestrict and bw_max is not None:
        b_bw = min(b_bw, bw_max)

    # Step 3: h_bw
    C_h_l = _rdrobust_bw(Y_l, X_l, c, p, deriv, q, c_bw, b_bw, scaleregul,
                         vce, nnmatch, kernel, covs_l, covs_drop_coll, cluster_l)
    C_h_r = _rdrobust_bw(Y_r, X_r, c, p, deriv, q, c_bw, b_bw, scaleregul,
                         vce, nnmatch, kernel, covs_r, covs_drop_coll, cluster_r)
    V_h_l, B_h_l, R_h_l, rate_h = C_h_l
    V_h_r, B_h_r, R_h_r, _ = C_h_r

    denom_h = (B_h_r - B_h_l) ** 2 + scaleregul * (R_h_r + R_h_l)
    h_bw = ((V_h_l + V_h_r) / denom_h) ** rate_h
    if bwrestrict and bw_max is not None:
        h_bw = min(h_bw, bw_max)

    return h_bw, b_bw


def _three_step_bw_sum(Y_l, X_l, Y_r, X_r, c, p, q, deriv, kernel, vce, nnmatch,
                       covs_l, covs_r, covs_drop_coll, scaleregul, c_bw, bw_max,
                       range_l, range_r, bwrestrict, cluster_l=None, cluster_r=None):
    """Three-step plug-in for MSE-SUM branch (sum criterion). Returns (h, b)."""
    # Step 1: pilot d_bw
    C_d_l = _rdrobust_bw(Y_l, X_l, c, q + 1, q + 1, q + 2, c_bw, range_l, 0,
                         vce, nnmatch, kernel, covs_l, covs_drop_coll, cluster_l)
    C_d_r = _rdrobust_bw(Y_r, X_r, c, q + 1, q + 1, q + 2, c_bw, range_r, 0,
                         vce, nnmatch, kernel, covs_r, covs_drop_coll, cluster_r)
    V_d_l, B_d_l, R_d_l, rate_d = C_d_l
    V_d_r, B_d_r, R_d_r, _ = C_d_r

    d_bw = ((V_d_l + V_d_r) / (B_d_r + B_d_l) ** 2) ** rate_d
    if bwrestrict and bw_max is not None:
        d_bw = min(d_bw, bw_max)

    # Step 2: b_bw
    C_b_l = _rdrobust_bw(Y_l, X_l, c, q, p + 1, q + 1, c_bw, d_bw, scaleregul,
                         vce, nnmatch, kernel, covs_l, covs_drop_coll, cluster_l)
    C_b_r = _rdrobust_bw(Y_r, X_r, c, q, p + 1, q + 1, c_bw, d_bw, scaleregul,
                         vce, nnmatch, kernel, covs_r, covs_drop_coll, cluster_r)
    V_b_l, B_b_l, R_b_l, rate_b = C_b_l
    V_b_r, B_b_r, R_b_r, _ = C_b_r

    denom_b = (B_b_r + B_b_l) ** 2 + scaleregul * (R_b_r + R_b_l)
    b_bw = ((V_b_l + V_b_r) / denom_b) ** rate_b
    if bwrestrict and bw_max is not None:
        b_bw = min(b_bw, bw_max)

    # Step 3: h_bw
    C_h_l = _rdrobust_bw(Y_l, X_l, c, p, deriv, q, c_bw, b_bw, scaleregul,
                         vce, nnmatch, kernel, covs_l, covs_drop_coll, cluster_l)
    C_h_r = _rdrobust_bw(Y_r, X_r, c, p, deriv, q, c_bw, b_bw, scaleregul,
                         vce, nnmatch, kernel, covs_r, covs_drop_coll, cluster_r)
    V_h_l, B_h_l, R_h_l, rate_h = C_h_l
    V_h_r, B_h_r, R_h_r, _ = C_h_r

    denom_h = (B_h_r + B_h_l) ** 2 + scaleregul * (R_h_r + R_h_l)
    h_bw = ((V_h_l + V_h_r) / denom_h) ** rate_h
    if bwrestrict and bw_max is not None:
        h_bw = min(h_bw, bw_max)

    return h_bw, b_bw


def _three_step_bw_two(Y_l, X_l, Y_r, X_r, c, p, q, deriv, kernel, vce, nnmatch,
                       covs_l, covs_r, covs_drop_coll, scaleregul, c_bw, bw_max,
                       range_l, range_r, bwrestrict, cluster_l=None, cluster_r=None):
    """Three-step plug-in for MSE-TWO branch (per-side independent). Returns (h_l, h_r, b_l, b_r)."""
    # Step 1: pilot d_bw per side
    C_d_l = _rdrobust_bw(Y_l, X_l, c, q + 1, q + 1, q + 2, c_bw, range_l, 0,
                         vce, nnmatch, kernel, covs_l, covs_drop_coll, cluster_l)
    C_d_r = _rdrobust_bw(Y_r, X_r, c, q + 1, q + 1, q + 2, c_bw, range_r, 0,
                         vce, nnmatch, kernel, covs_r, covs_drop_coll, cluster_r)
    V_d_l, B_d_l, R_d_l, rate_d = C_d_l
    V_d_r, B_d_r, R_d_r, _ = C_d_r

    d_bw_l = (V_d_l / B_d_l ** 2) ** rate_d
    d_bw_r = (V_d_r / B_d_r ** 2) ** rate_d
    if bwrestrict:
        d_bw_l = min(d_bw_l, range_l)
        d_bw_r = min(d_bw_r, range_r)

    # Step 2: b_bw per side
    C_b_l = _rdrobust_bw(Y_l, X_l, c, q, p + 1, q + 1, c_bw, d_bw_l, scaleregul,
                         vce, nnmatch, kernel, covs_l, covs_drop_coll, cluster_l)
    C_b_r = _rdrobust_bw(Y_r, X_r, c, q, p + 1, q + 1, c_bw, d_bw_r, scaleregul,
                         vce, nnmatch, kernel, covs_r, covs_drop_coll, cluster_r)
    V_b_l, B_b_l, R_b_l, rate_b = C_b_l
    V_b_r, B_b_r, R_b_r, _ = C_b_r

    denom_b_l = B_b_l ** 2 + scaleregul * R_b_l
    denom_b_r = B_b_r ** 2 + scaleregul * R_b_r
    b_bw_l = (V_b_l / denom_b_l) ** rate_b
    b_bw_r = (V_b_r / denom_b_r) ** rate_b
    if bwrestrict:
        b_bw_l = min(b_bw_l, range_l)
        b_bw_r = min(b_bw_r, range_r)

    # Step 3: h_bw per side
    C_h_l = _rdrobust_bw(Y_l, X_l, c, p, deriv, q, c_bw, b_bw_l, scaleregul,
                         vce, nnmatch, kernel, covs_l, covs_drop_coll, cluster_l)
    C_h_r = _rdrobust_bw(Y_r, X_r, c, p, deriv, q, c_bw, b_bw_r, scaleregul,
                         vce, nnmatch, kernel, covs_r, covs_drop_coll, cluster_r)
    V_h_l, B_h_l, R_h_l, rate_h = C_h_l
    V_h_r, B_h_r, R_h_r, _ = C_h_r

    denom_h_l = B_h_l ** 2 + scaleregul * R_h_l
    denom_h_r = B_h_r ** 2 + scaleregul * R_h_r
    h_bw_l = (V_h_l / denom_h_l) ** rate_h
    h_bw_r = (V_h_r / denom_h_r) ** rate_h
    if bwrestrict:
        h_bw_l = min(h_bw_l, range_l)
        h_bw_r = min(h_bw_r, range_r)

    return h_bw_l, h_bw_r, b_bw_l, b_bw_r


def _cer_scale(N, p, g_l=0, g_r=0):
    """CER scaling factor. With clustering use (g_l+g_r) instead of N."""
    denom = (3 + p) * (3 + 2 * p)
    if g_l > 0 or g_r > 0:
        n_eff = g_l + g_r
    else:
        n_eff = N
    return n_eff ** (-p / denom)


def _rdbwselect(Y_l, X_l, Y_r, X_r, c, p, q, deriv, kernel, vce, nnmatch,
                covs_l=None, covs_r=None, covs_drop_coll=True,
                scaleregul=1, bwrestrict=True, masspoints="adjust", bwcheck=0,
                cluster_l=0, cluster_r=0, cluster_ids_l=None, cluster_ids_r=None):
    """
    Unified bandwidth selector supporting all 9 rdrobust selectors.

    Returns a dict with bandwidths for all selectors:
    {
        'mserd': (h, b),
        'msesum': (h, b),
        'msetwo': (h_l, h_r, b_l, b_r),
        'msecomb1': (h, b),
        'msecomb2': (h_l, h_r, b_l, b_r),
        'cerrd': (h, b),
        'cersum': (h, b),
        'certwo': (h_l, h_r, b_l, b_r),
        'cercomb1': (h, b),
        'cercomb2': (h_l, h_r, b_l, b_r),
    }
    For selectors returning a single h/b, h_l=h_r=h and b_l=b_r=b.
    """
    c_bw, bw_max, range_l, range_r, M_l, M_r, masspoints_found, effective_bwcheck = _compute_pilot_bw(
        X_l, X_r, c, kernel, masspoints, bwcheck, bwrestrict
    )

    # Compute all three MSE branches
    h_mserd, b_mserd = _three_step_bw_rd(
        Y_l, X_l, Y_r, X_r, c, p, q, deriv, kernel, vce, nnmatch,
        covs_l, covs_r, covs_drop_coll, scaleregul, c_bw, bw_max,
        range_l, range_r, bwrestrict, cluster_ids_l, cluster_ids_r,
    )
    h_msesum, b_msesum = _three_step_bw_sum(
        Y_l, X_l, Y_r, X_r, c, p, q, deriv, kernel, vce, nnmatch,
        covs_l, covs_r, covs_drop_coll, scaleregul, c_bw, bw_max,
        range_l, range_r, bwrestrict, cluster_ids_l, cluster_ids_r,
    )
    h_msetwo_l, h_msetwo_r, b_msetwo_l, b_msetwo_r = _three_step_bw_two(
        Y_l, X_l, Y_r, X_r, c, p, q, deriv, kernel, vce, nnmatch,
        covs_l, covs_r, covs_drop_coll, scaleregul, c_bw, bw_max,
        range_l, range_r, bwrestrict, cluster_ids_l, cluster_ids_r,
    )

    # CER scaling
    N = len(X_l) + len(X_r)
    cer_h = _cer_scale(N, p, cluster_l, cluster_r)
    cer_b = 1.0  # bias bandwidth unchanged for CER

    h_cerrd = h_mserd * cer_h
    b_cerrd = b_mserd * cer_b
    h_cersum = h_msesum * cer_h
    b_cersum = b_msesum * cer_b
    h_certwo_l = h_msetwo_l * cer_h
    h_certwo_r = h_msetwo_r * cer_h
    b_certwo_l = b_msetwo_l * cer_b
    b_certwo_r = b_msetwo_r * cer_b

    # Comb selectors
    # comb1 = min(rd, sum)
    h_msecomb1 = min(h_mserd, h_msesum)
    b_msecomb1 = min(b_mserd, b_msesum)
    h_cercomb1 = h_msecomb1 * cer_h
    b_cercomb1 = b_msecomb1 * cer_b

    # comb2 = median(rd, sum, two) per side
    def _median3(a, b, c):
        return sorted([a, b, c])[1]

    h_msecomb2_l = _median3(h_mserd, h_msesum, h_msetwo_l)
    h_msecomb2_r = _median3(h_mserd, h_msesum, h_msetwo_r)
    b_msecomb2_l = _median3(b_mserd, b_msesum, b_msetwo_l)
    b_msecomb2_r = _median3(b_mserd, b_msesum, b_msetwo_r)
    h_cercomb2_l = h_msecomb2_l * cer_h
    h_cercomb2_r = h_msecomb2_r * cer_h
    b_cercomb2_l = b_msecomb2_l * cer_b
    b_cercomb2_r = b_msecomb2_r * cer_b

    return {
        "mserd": (h_mserd, h_mserd, b_mserd, b_mserd),
        "msesum": (h_msesum, h_msesum, b_msesum, b_msesum),
        "msetwo": (h_msetwo_l, h_msetwo_r, b_msetwo_l, b_msetwo_r),
        "msecomb1": (h_msecomb1, h_msecomb1, b_msecomb1, b_msecomb1),
        "msecomb2": (h_msecomb2_l, h_msecomb2_r, b_msecomb2_l, b_msecomb2_r),
        "cerrd": (h_cerrd, h_cerrd, b_cerrd, b_cerrd),
        "cersum": (h_cersum, h_cersum, b_cersum, b_cersum),
        "certwo": (h_certwo_l, h_certwo_r, b_certwo_l, b_certwo_r),
        "cercomb1": (h_cercomb1, h_cercomb1, b_cercomb1, b_cercomb1),
        "cercomb2": (h_cercomb2_l, h_cercomb2_r, b_cercomb2_l, b_cercomb2_r),
    }


def _rdbwselect_mserd(Y_l, X_l, Y_r, X_r, c, p, q, deriv, kernel, vce, nnmatch,
                      covs_l=None, covs_r=None, covs_drop_coll=True,
                      scaleregul=1, bwrestrict=True):
    """Legacy entry point for mserd only. Returns (h, b)."""
    c_bw, bw_max, range_l, range_r, _, _, _, _ = _compute_pilot_bw(
        X_l, X_r, c, kernel, "adjust", 0, bwrestrict
    )
    return _three_step_bw_rd(
        Y_l, X_l, Y_r, X_r, c, p, q, deriv, kernel, vce, nnmatch,
        covs_l, covs_r, covs_drop_coll, scaleregul, c_bw, bw_max,
        range_l, range_r, bwrestrict,
    )


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
        Bandwidth selector. Supported: "mserd", "msesum", "msetwo",
        "msecomb1", "msecomb2", "cerrd", "cersum", "certwo",
        "cercomb1", "cercomb2". If h is provided, bwselect is ignored.
    covs : list[str] or str or None
        Covariate variable name(s) for covariate-adjusted RD.
    covs_drop : bool, default True
        Drop collinear covariates.
    scaleregul : float, default 1
        Regularization term scaling for bandwidth selectors.
    """

    # Supported bandwidth selectors (9 total)
    _VALID_BWSELECT = {
        "mserd", "msesum", "msetwo",
        "msecomb1", "msecomb2",
        "cerrd", "cersum", "certwo",
        "cercomb1", "cercomb2",
    }

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
        masspoints: str = "adjust",
        bwcheck: int = 0,
        weights: str | None = None,
        fuzzy: str | None = None,
        sharpbw: bool = False,
        cluster: str | None = None,
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
        self.bwselect = bwselect.lower() if bwselect is not None else "mserd"
        self.covs = covs
        self.covs_drop = bool(covs_drop)
        self.scaleregul = float(scaleregul)
        self.masspoints = masspoints
        self.bwcheck = int(bwcheck)
        self.weights = weights
        self.fuzzy = fuzzy
        self.sharpbw = bool(sharpbw)
        self.cluster = cluster

        if self.deriv != 0:
            raise NotImplementedError("Only deriv=0 (sharp RD) is supported in this subset.")
        if self.p < 0 or self.q <= self.p:
            raise ValueError("Require 0 <= p < q.")
        if self.vce not in ("nn", "hc0", "cluster", "nncluster"):
            raise NotImplementedError(
                "Only vce='nn', 'hc0', 'cluster', and 'nncluster' are supported in this subset."
            )
        if self.bwselect not in self._VALID_BWSELECT:
            raise NotImplementedError(
                f"bwselect='{self.bwselect}' is not supported. "
                f"Supported: {sorted(self._VALID_BWSELECT)} or provide h explicitly."
            )
        if self.cluster is not None and self.vce not in ("cluster", "nncluster"):
            raise ValueError("cluster variable requires vce='cluster' or vce='nncluster'.")
        if self.vce in ("cluster", "nncluster") and self.cluster is None:
            raise ValueError("vce='cluster' or vce='nncluster' requires a cluster variable.")

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

        if self.fuzzy is not None:
            cols.append(self.fuzzy)
        if self.weights is not None:
            cols.append(self.weights)
        if self.cluster is not None:
            cols.append(self.cluster)

        df = self.data[cols].copy()
        n_input = len(df)
        df["_stataflow_row_id"] = np.arange(n_input)
        df = df.dropna()
        y = df[self.y_var].to_numpy(dtype=float)
        x = df[self.x_var].to_numpy(dtype=float)
        if cov_names:
            covs_all = df[cov_names].to_numpy(dtype=float)
        else:
            covs_all = None

        # Fuzzy treatment variable
        T_all = None
        if self.fuzzy is not None:
            T_all = df[self.fuzzy].to_numpy(dtype=float)

        # Cluster variable
        C_all = None
        if self.cluster is not None:
            C_all = df[self.cluster].to_numpy(dtype=float)

        # Frequency weights: drop non-positive
        fw = None
        if self.weights is not None:
            fw = df[self.weights].to_numpy(dtype=float)
            valid = fw > 0
            if not valid.all():
                y = y[valid]
                x = x[valid]
                fw = fw[valid]
                df = df.iloc[valid].copy()
                if covs_all is not None:
                    covs_all = covs_all[valid, :]
                if T_all is not None:
                    T_all = T_all[valid]
                if C_all is not None:
                    C_all = C_all[valid]
            # aweight normalization: sum(w) = N after missing drop
            if fw is not None and fw.sum() > 0:
                fw = fw / fw.sum() * len(fw)

        # Build sample mask after all row-level drops.
        kept_ids = set(df["_stataflow_row_id"].values)
        sample_mask = [i in kept_ids for i in range(n_input)]
        df = df.drop(columns=["_stataflow_row_id"])

        nobs = len(y)

        if self.c <= np.min(x) or self.c >= np.max(x):
            raise ValueError("Cutoff c must lie strictly within the range of the running variable.")

        # Sort by running variable
        order = np.argsort(x, kind="stable")
        x = x[order]
        y = y[order]
        if covs_all is not None:
            covs_all = covs_all[order, :]
        if fw is not None:
            fw = fw[order]
        if T_all is not None:
            T_all = T_all[order]
        if C_all is not None:
            C_all = C_all[order]

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

        T_l = T_all[left_mask] if T_all is not None else None
        T_r = T_all[right_mask] if T_all is not None else None

        C_l = C_all[left_mask] if C_all is not None else None
        C_r = C_all[right_mask] if C_all is not None else None

        # Perfect compliance detection
        perf_comp = False
        if T_l is not None:
            if np.var(T_l) < 1e-12 or np.var(T_r) < 1e-12:
                perf_comp = True

        fw_l = fw[left_mask] if fw is not None else None
        fw_r = fw[right_mask] if fw is not None else None

        # Automatic bandwidth selection
        if self.h_l is None:
            # Fuzzy RD: use sharp bandwidth selection unless user provided h
            use_sharpbw = (self.fuzzy is not None) and (self.sharpbw or perf_comp)
            if self.fuzzy is not None and not use_sharpbw:
                raise NotImplementedError(
                    "Fuzzy RD automatic bandwidth selection without sharpbw is not yet supported. "
                    "Please provide h explicitly or set sharpbw=True."
                )
            # Full-sample cluster counts for CER scaling in bandwidth selection
            g_l_full = len(np.unique(C_l)) if C_l is not None else 0
            g_r_full = len(np.unique(C_r)) if C_r is not None else 0
            # Map vce for bandwidth selection residual basis
            vce_bw = self.vce
            if vce_bw == "cluster":
                vce_bw = "hc0"
            elif vce_bw == "nncluster":
                vce_bw = "nn"
            bw_dict = _rdbwselect(
                Y_l, X_l, Y_r, X_r, self.c, self.p, self.q, self.deriv,
                self.kernel, vce_bw, self.nnmatch,
                covs_l, covs_r, self.covs_drop, self.scaleregul,
                masspoints=self.masspoints,
                bwcheck=self.bwcheck,
                cluster_l=g_l_full,
                cluster_r=g_r_full,
                cluster_ids_l=C_l,
                cluster_ids_r=C_r,
            )
            sel = self.bwselect or "mserd"
            self.h_l, self.h_r, self.b_l, self.b_r = bw_dict[sel]
            self.h_l = float(self.h_l)
            self.h_r = float(self.h_r)
            self.b_l = float(self.b_l)
            self.b_r = float(self.b_r)

        # Kernel weights
        w_h_l = _kernel_weight(X_l, self.c, self.h_l, self.kernel)
        w_h_r = _kernel_weight(X_r, self.c, self.h_r, self.kernel)
        w_b_l = _kernel_weight(X_l, self.c, self.b_l, self.kernel)
        w_b_r = _kernel_weight(X_r, self.c, self.b_r, self.kernel)

        # Multiply by frequency weights if provided
        if fw_l is not None:
            w_h_l = w_h_l * fw_l
            w_b_l = w_b_l * fw_l
        if fw_r is not None:
            w_h_r = w_h_r * fw_r
            w_b_r = w_b_r * fw_r

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

        # Effective cluster arrays and counts (post-bandwidth restriction)
        eC_l = C_l[ind_l] if C_l is not None else None
        eC_r = C_r[ind_r] if C_r is not None else None
        has_cluster = eC_l is not None
        if has_cluster:
            if np.isnan(eC_l).any() or np.isnan(eC_r).any():
                raise ValueError("Cluster variable contains NaN in bandwidth-restricted sample.")

        # Design matrices
        R_q_l = np.zeros((eN_l, self.q + 1), dtype=float)
        R_q_r = np.zeros((eN_r, self.q + 1), dtype=float)
        for j in range(self.q + 1):
            R_q_l[:, j] = (eX_l - self.c) ** j
            R_q_r[:, j] = (eX_r - self.c) ** j
        R_p_l = R_q_l[:, : self.p + 1]
        R_p_r = R_q_r[:, : self.p + 1]

        # Multi-column WLS: construct D with [Y, T, Z] ordering
        has_fuzzy = T_l is not None
        if has_fuzzy:
            D_l = np.column_stack((eY_l, T_l[ind_l]))
            D_r = np.column_stack((eY_r, T_r[ind_r]))
            if eZ_l is not None:
                D_l = np.column_stack((D_l, eZ_l))
                D_r = np.column_stack((D_r, eZ_r))
        else:
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
        s = np.array([1.0])
        dZ = 0
        gamma_Y = None
        gamma_T = None
        if eZ_l is not None:
            dZ = eZ_l.shape[1]
            U_l = (R_p_l * W_h_l[:, None]).T @ D_l
            U_r = (R_p_r * W_h_r[:, None]).T @ D_r
            ZWD_l = (eZ_l * W_h_l[:, None]).T @ D_l
            ZWD_r = (eZ_r * W_h_r[:, None]).T @ D_r
            if has_fuzzy:
                colsZ = np.arange(2, 2 + dZ)
                ZWY_Y_l = ZWD_l[:, 0] - (U_l[:, colsZ].T @ (invG_p_l @ U_l[:, 0]))
                ZWY_Y_r = ZWD_r[:, 0] - (U_r[:, colsZ].T @ (invG_p_r @ U_r[:, 0]))
                ZWY_T_l = ZWD_l[:, 1] - (U_l[:, colsZ].T @ (invG_p_l @ U_l[:, 1]))
                ZWY_T_r = ZWD_r[:, 1] - (U_r[:, colsZ].T @ (invG_p_r @ U_r[:, 1]))
            else:
                colsZ = np.arange(1, 1 + dZ)
                ZWY_Y_l = ZWD_l[:, 0] - (U_l[:, colsZ].T @ (invG_p_l @ U_l[:, 0]))
                ZWY_Y_r = ZWD_r[:, 0] - (U_r[:, colsZ].T @ (invG_p_r @ U_r[:, 0]))
            UiGU_l = U_l[:, colsZ].T @ (invG_p_l @ U_l[:, colsZ])
            UiGU_r = U_r[:, colsZ].T @ (invG_p_r @ U_r[:, colsZ])
            ZWZ_l = ZWD_l[:, colsZ] - UiGU_l
            ZWZ_r = ZWD_r[:, colsZ] - UiGU_r
            ZWZ = ZWZ_r + ZWZ_l
            ZWY_Y = ZWY_Y_r + ZWY_Y_l
            if self.covs_drop:
                gamma_Y = np.linalg.pinv(ZWZ) @ ZWY_Y
            else:
                try:
                    L = linalg.cholesky(ZWZ, lower=True)
                    gamma_Y = linalg.solve_triangular(L, ZWY_Y, lower=True)
                    gamma_Y = linalg.solve_triangular(L.T, gamma_Y, lower=False)
                except linalg.LinAlgError:
                    gamma_Y = np.linalg.pinv(ZWZ) @ ZWY_Y
            if has_fuzzy:
                ZWY_T = ZWY_T_r + ZWY_T_l
                if self.covs_drop:
                    gamma_T = np.linalg.pinv(ZWZ) @ ZWY_T
                else:
                    try:
                        L = linalg.cholesky(ZWZ, lower=True)
                        gamma_T = linalg.solve_triangular(L, ZWY_T, lower=True)
                        gamma_T = linalg.solve_triangular(L.T, gamma_T, lower=False)
                    except linalg.LinAlgError:
                        gamma_T = np.linalg.pinv(ZWZ) @ ZWY_T
                # Full s-vectors for [Y, T, Z] multi-column D
                s_Y = np.concatenate(([1.0, 0.0], -gamma_Y))
                s_T = np.concatenate(([0.0, 1.0], -gamma_T))
            else:
                s = np.append(1.0, -gamma_Y)
        elif has_fuzzy:
            # Fuzzy without covs: s remains [1.0] for now; fuzzy s computed after tau
            pass

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
        tau_T_cl = np.nan
        tau_T_bc = np.nan
        if has_fuzzy:
            # Fuzzy RD: Wald ratio estimator
            if eZ_l is not None:
                tau_Y_cl = scalepar * math.factorial(deriv) * float(
                    np.matmul(s_Y.T, beta_p_r[deriv, :] - beta_p_l[deriv, :])
                )
                tau_Y_bc = scalepar * math.factorial(deriv) * float(
                    np.matmul(s_Y.T, beta_bc_r[deriv, :] - beta_bc_l[deriv, :])
                )
                tau_T_cl = math.factorial(deriv) * float(
                    np.matmul(s_T.T, beta_p_r[deriv, :] - beta_p_l[deriv, :])
                )
                tau_T_bc = math.factorial(deriv) * float(
                    np.matmul(s_T.T, beta_bc_r[deriv, :] - beta_bc_l[deriv, :])
                )
            else:
                tau_Y_cl = scalepar * math.factorial(deriv) * (beta_p_r[deriv, 0] - beta_p_l[deriv, 0])
                tau_Y_bc = scalepar * math.factorial(deriv) * (beta_bc_r[deriv, 0] - beta_bc_l[deriv, 0])
                tau_T_cl = math.factorial(deriv) * (beta_p_r[deriv, 1] - beta_p_l[deriv, 1])
                tau_T_bc = math.factorial(deriv) * (beta_bc_r[deriv, 1] - beta_bc_l[deriv, 1])

            tau_cl = tau_Y_cl / tau_T_cl
            # Delta-method bias correction
            B_F_Y = tau_Y_cl - tau_Y_bc
            B_F_T = tau_T_cl - tau_T_bc
            tau_bc = tau_cl - (B_F_Y / tau_T_cl - tau_Y_cl * B_F_T / (tau_T_cl ** 2))

            # Side-specific estimates are not defined for Wald ratio estimator;
            # store NaN rather than arbitrary placeholders.
            tau_cl_l = np.nan
            tau_cl_r = np.nan
            tau_bc_l = np.nan
            tau_bc_r = np.nan

            # Fuzzy s-vector for VCE
            if eZ_l is not None:
                s_vce = np.array([
                    1.0 / tau_T_cl,
                    -tau_Y_cl / (tau_T_cl ** 2),
                    *(-(1.0 / tau_T_cl) * gamma_Y + (tau_Y_cl / (tau_T_cl ** 2)) * gamma_T)
                ])
            else:
                s_vce = np.array([1.0 / tau_T_cl, -tau_Y_cl / (tau_T_cl ** 2)])
        else:
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

        if has_fuzzy:
            # Side-specific bias decomposition is not defined for the Wald ratio.
            bias_l = np.nan
            bias_r = np.nan
        else:
            bias_l = tau_cl_l - tau_bc_l
            bias_r = tau_cl_r - tau_bc_r

        # Variance estimation
        vce_s = s_vce if has_fuzzy else s
        d = len(vce_s) - 1
        vce_select = self.vce
        if vce_select == "cluster":
            vce_select = "hc0"
        elif vce_select == "nncluster":
            vce_select = "nn"
        if vce_select == "nn":
            res_h_l = _nn_residuals(eX_l, eY_l, self.nnmatch)[:, None]
            res_h_r = _nn_residuals(eX_r, eY_r, self.nnmatch)[:, None]
            if has_fuzzy:
                res_T_l = _nn_residuals(eX_l, T_l[ind_l], self.nnmatch)[:, None]
                res_T_r = _nn_residuals(eX_r, T_r[ind_r], self.nnmatch)[:, None]
                res_h_l = np.column_stack((res_h_l, res_T_l))
                res_h_r = np.column_stack((res_h_r, res_T_r))
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
            if has_fuzzy:
                res_h_l = np.column_stack((res_h_l, T_l[ind_l] - pred_h_l[:, 1]))
                res_h_r = np.column_stack((res_h_r, T_r[ind_r] - pred_h_r[:, 1]))
                res_b_l = np.column_stack((res_b_l, T_l[ind_l] - pred_b_l[:, 1]))
                res_b_r = np.column_stack((res_b_r, T_r[ind_r] - pred_b_r[:, 1]))
            if eZ_l is not None:
                offset = 2 if has_fuzzy else 1
                res_h_l = np.column_stack((res_h_l, eZ_l - pred_h_l[:, offset:]))
                res_h_r = np.column_stack((res_h_r, eZ_r - pred_h_r[:, offset:]))
                res_b_l = np.column_stack((res_b_l, eZ_l - pred_b_l[:, offset:]))
                res_b_r = np.column_stack((res_b_r, eZ_r - pred_b_r[:, offset:]))

        # VCE with multi-dimensional residuals when covs exist or fuzzy
        if d == 0 and not has_cluster:
            V_cl_l = _vce_hc0(invG_p_l, R_p_l, W_h_l, res_h_l[:, 0])
            V_cl_r = _vce_hc0(invG_p_r, R_p_r, W_h_r, res_h_r[:, 0])
            ones_l = np.ones_like(W_h_l)
            ones_r = np.ones_like(W_h_r)
            V_rb_l = _vce_hc0(invG_p_l, Q_q_l, ones_l, res_b_l[:, 0])
            V_rb_r = _vce_hc0(invG_p_r, Q_q_r, ones_r, res_b_r[:, 0])
        else:
            # Unified path: handles both covs/fuzzy and clustering
            _s = vce_s if d > 0 else np.array([1.0])
            RX_l = R_p_l * W_h_l[:, None]
            RX_r = R_p_r * W_h_r[:, None]
            M_cl_l = _rdrobust_vce_multi(_s, RX_l, res_h_l, eC_l)
            M_cl_r = _rdrobust_vce_multi(_s, RX_r, res_h_r, eC_r)
            V_cl_l = invG_p_l @ M_cl_l @ invG_p_l
            V_cl_r = invG_p_r @ M_cl_r @ invG_p_r
            M_rb_l = _rdrobust_vce_multi(_s, Q_q_l, res_b_l, eC_l)
            M_rb_r = _rdrobust_vce_multi(_s, Q_q_r, res_b_r, eC_r)
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
                sample_mask=sample_mask,
            ),
            fit=FitInfo(
                df_model=float(2 * (self.p + 1)),
                df_resid=float(nobs - 2 * (self.p + 1)),
            ),
            coefficients=coefficients,
            variance=VarianceInfo(
                row_names=[c.name for c in coefficients],
                values=[
                    [V_tau_cl, 0.0, 0.0],
                    [0.0, V_tau_cl, 0.0],
                    [0.0, 0.0, V_tau_rb],
                ],
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
            "tau_T_cl": tau_T_cl,
            "tau_T_bc": tau_T_bc,
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

        result.validate()
        return result
