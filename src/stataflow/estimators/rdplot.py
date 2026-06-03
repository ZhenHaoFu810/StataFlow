"""
RD Plot companion command for Regression Discontinuity visualization.

Implements IMSE-optimal bin selection and local polynomial fit overlay,
returning data suitable for plotting (no rendering).

Based on Calonico, Cattaneo, and Titiunik (2015, JASA).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from stataflow.estimators.rdrobust import _kernel_weight, _wls_poly


def _global_poly_fit(x, y, k=4):
    """Global polynomial fit of order k with fallback to k-1, k-2."""
    n = len(x)
    for order in [k, 3, 2]:
        if order > n - 1:
            continue
        R = np.zeros((n, order + 1), dtype=float)
        for j in range(order + 1):
            R[:, j] = x ** j
        try:
            gram = R.T @ R
            inv_gram = np.linalg.pinv(gram)
            gamma = inv_gram @ (R.T @ y)
            gamma2 = inv_gram @ (R.T @ (y ** 2))
            return gamma, gamma2, order
        except Exception:
            continue
    raise ValueError("Global polynomial fit failed for all orders.")


def _compute_bins_esmv(x, y, c, side="left"):
    """
    Compute IMSE-optimal evenly-spaced bin count using spacings-based
    bias and mimicking variance estimators (esmv).
    """
    n = len(x)
    if n < 5:
        return 1

    gamma, gamma2, k = _global_poly_fit(x, y)

    # Evaluate derivatives and fitted values
    R = np.zeros((n, k + 1), dtype=float)
    for j in range(k + 1):
        R[:, j] = x ** j
    mu = R @ gamma
    mu2 = R @ gamma2
    var_y = np.var(y, ddof=1) if n > 1 else 1.0

    # Derivative for bias: use first derivative of fitted polynomial
    dR = np.zeros((n, k + 1), dtype=float)
    for j in range(1, k + 1):
        dR[:, j] = j * x ** (j - 1)
    mu1 = dR @ gamma

    if side == "left":
        x_min, x_max = np.min(x), c
    else:
        x_min, x_max = c, np.max(x)
    range_x = x_max - x_min
    if range_x <= 0:
        return 1

    # Evenly spaced grid for spacings
    n_grid = max(n, 100)
    x_grid = np.linspace(x_min, x_max, n_grid)
    dx = range_x / (n_grid - 1)

    # Evaluate mu1 on grid
    dR_grid = np.zeros((n_grid, k + 1), dtype=float)
    for j in range(1, k + 1):
        dR_grid[:, j] = j * x_grid ** (j - 1)
    mu1_grid = dR_grid @ gamma

    # Bias estimator for ES
    B = ((range_x ** 2) / (12 * n_grid)) * np.sum(mu1_grid ** 2) * dx

    # Variance estimator (spacings-based)
    sort_idx = np.argsort(x)
    x_s = x[sort_idx]
    y_s = y[sort_idx]
    dx_i = np.diff(x_s)
    dy_i = np.diff(y_s)
    valid = dx_i > 0
    if valid.sum() == 0:
        V = 1.0
    else:
        V = (0.5 / range_x) * np.sum(dx_i[valid] * (dy_i[valid] ** 2))

    if V <= 0:
        V = 1e-10

    # MV adjustment
    J_mv = max(1, int(np.ceil((var_y / V) * (n / (np.log(n) ** 2)))))
    J_dw = max(1, int(np.ceil(((2 * B / V) * n) ** (1.0 / 3))))

    # esmv = min of the two
    return min(J_mv, J_dw)


def _compute_bins_qsmv(x, y, c, side="left"):
    """
    Compute IMSE-optimal quantile-spaced bin count using spacings-based
    bias and mimicking variance estimators (qsmv).
    """
    n = len(x)
    if n < 5:
        return 1

    gamma, gamma2, k = _global_poly_fit(x, y)

    dR = np.zeros((n, k + 1), dtype=float)
    for j in range(1, k + 1):
        dR[:, j] = j * x ** (j - 1)
    mu1 = dR @ gamma

    var_y = np.var(y, ddof=1) if n > 1 else 1.0

    if side == "left":
        x_min, x_max = np.min(x), c
    else:
        x_min, x_max = c, np.max(x)
    range_x = x_max - x_min
    if range_x <= 0:
        return 1

    sort_idx = np.argsort(x)
    x_s = x[sort_idx]
    y_s = y[sort_idx]
    dx_i = np.diff(x_s)
    dy_i = np.diff(y_s)
    valid = dx_i > 0

    # Bias for QS
    if valid.sum() == 0:
        B = 1.0
    else:
        B = (n ** 2 / (24 * n)) * np.sum(dx_i[valid] ** 2 * mu1[sort_idx][:-1][valid] ** 2)

    # Variance for QS
    if valid.sum() == 0:
        V = 1.0
    else:
        V = (1.0 / (2 * n)) * np.sum(dy_i[valid] ** 2)

    if V <= 0:
        V = 1e-10

    J_mv = max(1, int(np.ceil((var_y / V) * (n / (np.log(n) ** 2)))))
    J_dw = max(1, int(np.ceil(((2 * B / V) * n) ** (1.0 / 3))))

    return min(J_mv, J_dw)


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
            if self.binselect.startswith("es"):
                J_l = _compute_bins_esmv(x_l, y_l, self.c, side="left")
                J_r = _compute_bins_esmv(x_r, y_r, self.c, side="right")
            elif self.binselect.startswith("qs"):
                J_l = _compute_bins_qsmv(x_l, y_l, self.c, side="left")
                J_r = _compute_bins_qsmv(x_r, y_r, self.c, side="right")
            else:
                raise ValueError(f"Unsupported binselect: {self.binselect}")

        J_l = max(1, J_l)
        J_r = max(1, J_r)

        # Construct bins
        if self.binselect.startswith("es"):
            edges_l = _evenly_spaced_bins(np.min(x_l) if N_l > 0 else self.c - 1, self.c, J_l)
            edges_r = _evenly_spaced_bins(self.c, np.max(x_r) if N_r > 0 else self.c + 1, J_r)
        else:
            edges_l = _quantile_spaced_bins(x_l, J_l) if N_l > 0 else np.array([self.c - 1, self.c])
            edges_r = _quantile_spaced_bins(x_r, J_r) if N_r > 0 else np.array([self.c, self.c + 1])

        # Local polynomial fit
        nplot = 500
        x_plot_l = np.linspace(self.c - self.h_l, self.c, nplot)
        x_plot_r = np.linspace(self.c, self.c + self.h_r, nplot)

        # Covariate adjustment for fit
        gamma_cov = None
        if Z is not None:
            # FWL: regress y on Z within bandwidth, partial out
            # Simplified: use global OLS of y on Z
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
