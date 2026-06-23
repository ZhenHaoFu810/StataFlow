"""
RD Plot companion command for Regression Discontinuity visualization.

Implements IMSE-optimal bin selection and local polynomial fit overlay,
returning data suitable for plotting (no rendering).

Based on Calonico, Cattaneo, and Titiunik (2015, JASA).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.linalg import solve_triangular

from stataflow.estimators.rdrobust import _kernel_weight, _wls_poly


def _local_fwl_gamma(y, x, Z, c, h, kernel):
    """
    Estimate covariate coefficients using local WLS within bandwidth h.

    Runs weighted least squares of y on [1, Z] using kernel weights
    centered at c with bandwidth h, then returns the coefficients on Z.
    This follows the local FWL principle used in rdrobust covariate
    adjustment, avoiding the bias from global OLS when covariates have
    different relationships on either side of the cutoff.

    Parameters
    ----------
    y : np.ndarray
        Outcome variable.
    x : np.ndarray
        Running variable (used only for kernel weighting).
    Z : np.ndarray
        Covariate matrix (n x d).
    c : float
        Cutoff.
    h : float
        Bandwidth.
    kernel : str
        Kernel type.

    Returns
    -------
    np.ndarray or None
        Coefficients on Z (shape (d,)), or None if not enough observations.
    """
    w = _kernel_weight(x, c, h, kernel)
    mask = w > 0
    if mask.sum() < Z.shape[1] + 1:
        return None
    X = np.column_stack([np.ones(mask.sum()), Z[mask]])
    Xw = X * np.sqrt(w[mask, None])
    yw = y[mask] * np.sqrt(w[mask])
    beta = np.linalg.lstsq(Xw, yw, rcond=None)[0]
    return beta[1:]


def _global_poly_fit_raw(x, y, k=4):
    """OLS fit of y on raw powers [1, x, x^2, ..., x^k] with fallback."""
    n = len(x)
    for order in [k, 3, 2]:
        if order > n - 1:
            continue
        R = np.zeros((n, order + 1), dtype=float)
        for j in range(order + 1):
            R[:, j] = x ** j
        try:
            gram = R.T @ R
            # Use Cholesky inverse to match rdrobust's qrXXinv; fall back
            # to pseudo-inverse for rank-deficient designs.
            L = np.linalg.cholesky(gram)
            invL = solve_triangular(L, np.eye(order + 1), lower=True)
            inv_gram = invL.T @ invL
            gamma = inv_gram @ (R.T @ y)
            return gamma, order
        except Exception:
            try:
                inv_gram = np.linalg.pinv(gram)
                gamma = inv_gram @ (R.T @ y)
                return gamma, order
            except Exception:
                continue
    raise ValueError("Global polynomial fit failed for all orders.")


def _compute_bins_esmv(x, y, c, side, n_total):
    """
    Mimicking-variance evenly-spaced bin count.

    Follows Calonico, Cattaneo and Titiunik (2015a) and the
    rdrobust 2.2 reference implementation.
    """
    n_side = len(x)
    if n_side < 5:
        return 1

    gamma, _ = _global_poly_fit_raw(x, y, k=4)

    if side == "left":
        range_x = c - float(np.min(x))
    else:
        range_x = float(np.max(x)) - c
    if range_x <= 0:
        return 1

    k = len(gamma) - 1
    drk = np.zeros((n_side, k), dtype=float)
    for j in range(1, k + 1):
        drk[:, j - 1] = j * x ** (j - 1)
    mu1_hat = drk @ gamma[1:]

    # Spacings-based variance estimator (stable sort to match R/Stata)
    sort_idx = np.argsort(x, kind="stable")
    x_s = x[sort_idx]
    y_s = y[sort_idx]
    dxi = np.diff(x_s)
    dyi = np.diff(y_s)
    valid = dxi > 0
    if valid.sum() == 0:
        return 1

    V = (0.5 / range_x) * np.sum(dxi[valid] * (dyi[valid] ** 2))
    if V <= 0:
        V = 1e-10

    var_y = float(np.var(y, ddof=1)) if n_side > 1 else 1.0
    J_mv = int(np.ceil((var_y / V) * (n_total / (np.log(n_total) ** 2))))
    return max(1, J_mv)


def _compute_bins_qsmv(x, y, c, side, n_total):
    """
    Mimicking-variance quantile-spaced bin count.

    Follows Calonico, Cattaneo and Titiunik (2015a) and the
    rdrobust 2.2 reference implementation.
    """
    n_side = len(x)
    if n_side < 5:
        return 1

    gamma, _ = _global_poly_fit_raw(x, y, k=4)

    sort_idx = np.argsort(x, kind="stable")
    x_s = x[sort_idx]
    y_s = y[sort_idx]
    dxi = np.diff(x_s)
    dyi = np.diff(y_s)
    valid = dxi > 0
    if valid.sum() == 0:
        return 1

    x_bar = (x_s[1:] + x_s[:-1]) / 2.0
    k = len(gamma) - 1
    drk_i = np.zeros((len(x_bar), k), dtype=float)
    for j in range(1, k + 1):
        drk_i[:, j - 1] = j * x_bar ** (j - 1)
    mu1_i_hat = drk_i @ gamma[1:]

    B = (n_side ** 2 / (24.0 * n_total)) * np.sum(
        dxi[valid] ** 2 * mu1_i_hat[valid] ** 2
    )
    # Stata's qs spacings variance sums dyi^2 over all adjacent pairs,
    # including pairs with tied x (dxi==0). Do not apply the valid mask here.
    V = (1.0 / (2.0 * n_side)) * np.sum(dyi ** 2)
    if V <= 0:
        V = 1e-10

    var_y = float(np.var(y, ddof=1)) if n_side > 1 else 1.0
    J_mv = int(np.ceil((var_y / V) * (n_total / (np.log(n_total) ** 2))))
    return max(1, J_mv)


def _evenly_spaced_bins(x_min, x_max, J):
    """Return J+1 evenly spaced bin edges."""
    return np.linspace(x_min - 1e-8, x_max + 1e-8, J + 1)


def _quantile_spaced_bins(x, J):
    """Return J+1 quantile-spaced bin edges."""
    q = np.linspace(0, 1, J + 1)
    edges = np.quantile(x, q)
    edges[0] -= 1e-8
    edges[-1] += 1e-8
    return edges


def _collapse_bins(x, y, edges):
    """Collapse observations into bins, returning bin statistics."""
    bin_ids = np.digitize(x, edges) - 1
    bin_ids = np.clip(bin_ids, 0, len(edges) - 2)

    results = []
    for b in range(len(edges) - 1):
        mask = bin_ids == b
        n_b = mask.sum()
        if n_b == 0:
            continue
        x_b = x[mask]
        y_b = y[mask]
        results.append({
            "bin_id": b,
            "N": n_b,
            "x_min": float(edges[b]),
            "x_max": float(edges[b + 1]),
            "mean_x": float(np.mean(x_b)),
            "mean_y": float(np.mean(y_b)),
            "se_y": float(np.std(y_b, ddof=1) / np.sqrt(n_b)) if n_b > 1 else 0.0,
        })
    return pd.DataFrame(results)


class RDPlot:
    """RD Plot companion command."""

    def __init__(
        self,
        data,
        y: str,
        x: str,
        c: float = 0.0,
        p: int = 4,
        nbins: tuple[int, int] | int | None = None,
        binselect: str = "esmv",
        kernel: str = "uniform",
        h: float | tuple[float, float] | None = None,
        covs: list[str] | str | None = None,
    ):
        self.data = data.copy()
        self.y_var = y
        self.x_var = x
        self.c = float(c)
        self.p = int(p)
        self.nbins = nbins
        self.binselect = binselect.lower()
        self.kernel = kernel
        self.covs = covs

        if h is not None:
            if np.isscalar(h):
                self.h_l = self.h_r = float(h)
            else:
                self.h_l, self.h_r = float(h[0]), float(h[1])
        else:
            # Default: use full data range as bandwidth
            x_vals = self.data[self.x_var].to_numpy(dtype=float)
            self.h_l = float(self.c - np.min(x_vals[x_vals < self.c])) if np.any(x_vals < self.c) else 1.0
            self.h_r = float(np.max(x_vals[x_vals >= self.c]) - self.c) if np.any(x_vals >= self.c) else 1.0

    def fit(self):
        # Data extraction
        cols = [self.y_var, self.x_var]
        cov_names = []
        if self.covs is not None:
            if isinstance(self.covs, str):
                cov_names = [self.covs]
            else:
                cov_names = list(self.covs)
            cols += cov_names

        df = self.data[cols].copy()
        df = df.dropna()
        y = df[self.y_var].to_numpy(dtype=float)
        x = df[self.x_var].to_numpy(dtype=float)
        if cov_names:
            Z = df[cov_names].to_numpy(dtype=float)
        else:
            Z = None

        nobs = len(y)

        # Sort by x
        order = np.argsort(x, kind="stable")
        x = x[order]
        y = y[order]
        if Z is not None:
            Z = Z[order, :]

        left_mask = x < self.c
        right_mask = ~left_mask

        x_l = x[left_mask]
        x_r = x[right_mask]
        y_l = y[left_mask]
        y_r = y[right_mask]
        Z_l = Z[left_mask, :] if Z is not None else None
        Z_r = Z[right_mask, :] if Z is not None else None

        N_l = len(x_l)
        N_r = len(x_r)

        # Determine bin counts
        if self.nbins is not None:
            if isinstance(self.nbins, int):
                J_l = J_r = self.nbins
            else:
                J_l, J_r = self.nbins
        else:
            nobs = N_l + N_r
            if self.binselect == "esmv":
                J_l = _compute_bins_esmv(x_l, y_l, self.c, "left", nobs)
                J_r = _compute_bins_esmv(x_r, y_r, self.c, "right", nobs)
            elif self.binselect == "qsmv":
                J_l = _compute_bins_qsmv(x_l, y_l, self.c, "left", nobs)
                J_r = _compute_bins_qsmv(x_r, y_r, self.c, "right", nobs)
            else:
                raise ValueError(f"Unsupported binselect: {self.binselect}")

        J_l = max(1, J_l)
        J_r = max(1, J_r)

        # Construct bins
        if self.binselect == "esmv":
            edges_l = _evenly_spaced_bins(np.min(x_l) if N_l > 0 else self.c - 1, self.c, J_l)
            edges_r = _evenly_spaced_bins(self.c, np.max(x_r) if N_r > 0 else self.c + 1, J_r)
        elif self.binselect == "qsmv":
            edges_l = _quantile_spaced_bins(x_l, J_l) if N_l > 0 else np.array([self.c - 1, self.c])
            edges_r = _quantile_spaced_bins(x_r, J_r) if N_r > 0 else np.array([self.c, self.c + 1])
        else:
            raise ValueError(f"Unsupported binselect: {self.binselect}")

        # Local polynomial fit
        nplot = 500
        x_plot_l = np.linspace(self.c - self.h_l, self.c, nplot)
        x_plot_r = np.linspace(self.c, self.c + self.h_r, nplot)

        # Covariate adjustment for fit
        gamma_cov = None
        if Z is not None:
            # Local FWL: estimate covariate coefficients within bandwidth
            # on each side, then average. This avoids global OLS bias when
            # covariate-outcome relationships differ across the cutoff.
            gamma_l = (
                _local_fwl_gamma(y_l, x_l, Z_l, self.c, self.h_l, self.kernel)
                if N_l > 0 else None
            )
            gamma_r = (
                _local_fwl_gamma(y_r, x_r, Z_r, self.c, self.h_r, self.kernel)
                if N_r > 0 else None
            )
            if gamma_l is not None and gamma_r is not None:
                gamma_cov = 0.5 * (gamma_l + gamma_r)
            elif gamma_l is not None:
                gamma_cov = gamma_l
            elif gamma_r is not None:
                gamma_cov = gamma_r
            else:
                # Fallback to global OLS if local fails (too few obs)
                Z_centered = Z - Z.mean(axis=0)
                y_centered = y - y.mean()
                gamma_cov = np.linalg.lstsq(Z_centered, y_centered, rcond=None)[0]
            y_l_adj = y_l - Z_l @ gamma_cov
            y_r_adj = y_r - Z_r @ gamma_cov
        else:
            y_l_adj = y_l
            y_r_adj = y_r

        # Collapse (use adjusted y for consistency with fit line)
        bins_l = _collapse_bins(x_l, y_l_adj, edges_l)
        bins_r = _collapse_bins(x_r, y_r_adj, edges_r)
        bins = pd.concat([bins_l, bins_r], ignore_index=True)

        w_l = _kernel_weight(x_l, self.c, self.h_l, self.kernel)
        w_r = _kernel_weight(x_r, self.c, self.h_r, self.kernel)

        beta_l, _ = _wls_poly(y_l_adj, x_l, self.c, w_l, self.p)
        beta_r, _ = _wls_poly(y_r_adj, x_r, self.c, w_r, self.p)

        R_plot_l = np.zeros((nplot, self.p + 1), dtype=float)
        R_plot_r = np.zeros((nplot, self.p + 1), dtype=float)
        for j in range(self.p + 1):
            R_plot_l[:, j] = (x_plot_l - self.c) ** j
            R_plot_r[:, j] = (x_plot_r - self.c) ** j

        y_plot_l = R_plot_l @ beta_l
        y_plot_r = R_plot_r @ beta_r

        fit_l = pd.DataFrame({"x": x_plot_l, "y": y_plot_l, "side": "left"})
        fit_r = pd.DataFrame({"x": x_plot_r, "y": y_plot_r, "side": "right"})
        fit = pd.concat([fit_l, fit_r], ignore_index=True)

        info = {
            "N_l": N_l,
            "N_r": N_r,
            "J_star_l": J_l,
            "J_star_r": J_r,
            "c": self.c,
            "p": self.p,
            "h_l": self.h_l,
            "h_r": self.h_r,
            "binselect": self.binselect,
            "kernel": self.kernel,
        }

        return {
            "bins": bins,
            "fit": fit,
            "info": info,
        }
