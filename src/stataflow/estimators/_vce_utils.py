"""
Shared VCE utilities for cluster-robust inference and PSD fix.

Used by AbsorbingOLS, IVAbsorbingOLS, and PPMLHDFE.
Centralized per ADR-0004 to avoid code duplication.
"""

import warnings

import numpy as np
from typing import Optional


def compute_cluster_meat(
    X: np.ndarray, residuals: np.ndarray, cluster_arr: np.ndarray,
    weights: Optional[np.ndarray] = None,
) -> tuple[np.ndarray, int]:
    """Compute cluster-robust meat matrix for a single cluster dimension.

    If ``weights`` is provided, each observation's score contribution is
    multiplied by ``sqrt(weights)``, matching the aweight convention used
    in Stata's cluster-robust sandwich.

    Returns (meat, n_clusters).
    """
    k = X.shape[1]
    unique_clusters = np.unique(cluster_arr)
    meat = np.zeros((k, k))
    if weights is not None:
        sqrt_w = np.sqrt(weights)
        r_w = residuals * sqrt_w
        for g in unique_clusters:
            mask = cluster_arr == g
            score_g = X[mask].T @ r_w[mask]
            meat += np.outer(score_g, score_g)
    else:
        for g in unique_clusters:
            mask = cluster_arr == g
            score_g = X[mask].T @ residuals[mask]
            meat += np.outer(score_g, score_g)
    return meat, len(unique_clusters)


def fix_psd(mat: np.ndarray) -> np.ndarray:
    """Fix non-PSD matrix by eigenvalue truncation (set negative eigenvalues to 0)."""
    eigvals, eigvecs = np.linalg.eigh(mat)
    eigvals = np.maximum(eigvals, 0.0)
    return eigvecs @ np.diag(eigvals) @ eigvecs.T


def fix_psd_reghdfe(
    mat: np.ndarray,
    constant_index: int | None = -1,
    coefficient_scales: Optional[np.ndarray] = None,
) -> np.ndarray:
    """Apply reghdfe's Cameron-Gelbach-Miller PSD correction.

    Reghdfe truncates negative eigenvalues of the full reported VCE.  When a
    constant is present, it then restores the slope block after applying the
    same correction to that block if necessary.  Consequently, the constant
    variance and constant-slope covariances may change while valid slope
    standard errors remain unchanged.

    By default ``_cons`` is assumed to be the last row and column. Pass
    ``constant_index=None`` when the matrix has no reported constant.
    ``coefficient_scales`` reproduces reghdfe's standardize-before-fix order:
    original coefficients equal standardized coefficients divided by these
    scales.
    """
    k = mat.shape[0]
    mat = np.asarray(mat, dtype=float)
    scales = None
    if coefficient_scales is not None:
        scales = np.asarray(coefficient_scales, dtype=float)
        if scales.shape != (k,) or np.any(scales <= 0):
            raise ValueError("coefficient_scales must contain one positive value per coefficient")
        mat = mat * np.outer(scales, scales)

    if k <= 1 or constant_index is None:
        fixed = fix_psd(mat)
        return fixed if scales is None else fixed / np.outer(scales, scales)

    mat = 0.5 * (mat + mat.T)

    if constant_index < 0:
        constant_index = k + constant_index
    if constant_index < 0 or constant_index >= k:
        raise ValueError("constant_index is out of bounds for covariance matrix")

    index = [i for i in range(k) if i != constant_index]
    slope_block = mat[np.ix_(index, index)]

    if np.min(np.linalg.eigvalsh(mat)) >= 0:
        return mat if scales is None else mat / np.outer(scales, scales)

    fixed = fix_psd(mat)
    if slope_block.size:
        if np.min(np.linalg.eigvalsh(slope_block)) < 0:
            slope_block = fix_psd(slope_block)
        fixed[np.ix_(index, index)] = slope_block
    fixed = 0.5 * (fixed + fixed.T)
    return fixed if scales is None else fixed / np.outer(scales, scales)


def compute_multiway_cluster_vce(
    X: np.ndarray,
    residuals: np.ndarray,
    M_inv: np.ndarray,
    cluster_arrs: list[np.ndarray],
    k_eff: int,
    n: int,
    small_sample_adjust: bool = True,
    weights: Optional[np.ndarray] = None,
) -> tuple[np.ndarray, int]:
    """
    Compute 2-way cluster-robust VCE using Cameron-Gelbach-Miller inclusion-exclusion.

    Omega = M_1 + M_2 - M_12 (inclusion-exclusion principle).
    Small-sample adjustment: (N-1)/(N-k_eff) * G_min/(G_min-1).

    Parameters
    ----------
    X : ndarray
        Design matrix for the sandwich (X_full for reghdfe, X_proj for iv).
    residuals : ndarray
        Residual vector.
    M_inv : ndarray
        Inverse of X'X (for reghdfe) or projection-inverse (for iv).
    cluster_arrs : list[ndarray]
        Two cluster variable vectors.
    k_eff : int
        Effective number of parameters for small-sample adjustment.
    n : int
        Number of observations.
    small_sample_adjust : bool
        If True, apply (n-1)/(n-k_eff) adjustment. PPMLHDFE sets False.
    weights : ndarray, optional
        Prior weights (aweight). If provided, scores are weighted by sqrt(weights).

    Returns
    -------
    cov_full : ndarray
        Full VCV matrix.
    cluster_count : int
        Minimum number of clusters across dimensions.
    """
    meats = []
    Gs = []
    for ca in cluster_arrs:
        meat, G = compute_cluster_meat(X, residuals, ca, weights=weights)
        meats.append(meat)
        Gs.append(G)

    # Safe interaction encoding using integer labels to avoid separator
    # collision (e.g. cluster values that naturally contain "__").
    seen = {}
    interaction = np.empty(len(cluster_arrs[0]), dtype=int)
    idx = 0
    for i, (a, b) in enumerate(zip(cluster_arrs[0], cluster_arrs[1])):
        key = (a, b)
        if key not in seen:
            seen[key] = idx
            idx += 1
        interaction[i] = seen[key]
    meat_12, G_12 = compute_cluster_meat(X, residuals, interaction, weights=weights)

    omega_meat = meats[0] + meats[1] - meat_12

    # NEW-IV-04: with only 1-2 clusters in one dimension, Stata's HDFE IV
    # path warns that the moment-condition covariance is not full rank and
    # effectively falls back to the richer one-way cluster dimension.
    if min(Gs) < 3:
        small_g = min(Gs)
        fallback_idx = int(np.argmax(Gs))
        omega_meat = meats[fallback_idx]
        Gs = [Gs[fallback_idx], Gs[fallback_idx]]
        warnings.warn(
            "2-way cluster covariance matrix of moment conditions is not of full rank "
            f"because one cluster dimension has fewer than 3 clusters (G={small_g}). "
            "Falling back to the richer one-way cluster dimension.",
            RuntimeWarning,
            stacklevel=2,
        )

    if small_sample_adjust:
        n_adj = (n - 1) / (n - k_eff) if n > k_eff else 1.0
    else:
        n_adj = 1.0

    # Use min(G1, G2) for small-sample df (aligns with Stata/ivreghdfe)
    G_min = min(Gs[0], Gs[1])
    g_adj = G_min / (G_min - 1) if G_min > 1 else 1.0

    cov_full = n_adj * g_adj * M_inv @ omega_meat @ M_inv
    return cov_full, G_min


def detect_collinear_columns(
    X: np.ndarray, names: list[str], tol: float = 1e-6,
) -> tuple[np.ndarray, list[str], list[int]]:
    """Detect and drop exact or numerically unstable collinear columns.

    Returns (X_indep, dropped_names, kept_indices).
    Used by all estimators for pre-OLS collinearity screening (ADR-0004).
    """
    if X.shape[1] <= 1:
        return X, [], list(range(X.shape[1]))

    rank = np.linalg.matrix_rank(X)
    if rank == X.shape[1]:
        # NumPy's default rank threshold is too permissive for Stata-style
        # regression screening under extreme column scaling.  Use pivoted QR
        # only for this numerically full-rank case so exact dependencies retain
        # the established input-order selection below.
        from scipy.linalg import qr

        _, r, pivots = qr(X, mode="economic", pivoting=True)
        diagonal = np.abs(np.diag(r))
        if diagonal.size == 0:
            return X, [], list(range(X.shape[1]))
        numerical_rank = int(np.sum(diagonal > tol * diagonal.max()))
        if numerical_rank == X.shape[1]:
            return X, [], list(range(X.shape[1]))

        norms = np.linalg.norm(X, axis=0)
        positive_norms = norms[norms > 0]
        scale_ratio = (
            float(positive_norms.max() / positive_norms.min())
            if positive_norms.size
            else 1.0
        )
        if scale_ratio > 1e4:
            # Compare column directions after normalizing their scales.  Keep
            # the intercept as a mandatory basis vector, then prefer larger
            # original-scale regressors when two directions are numerically
            # indistinguishable.  This reproduces Stata's omission choice
            # without allowing a large regressor to suppress `_cons`.
            mandatory = [i for i, name in enumerate(names) if name == "_cons"]
            candidates = sorted(
                (i for i in range(X.shape[1]) if i not in mandatory),
                key=lambda i: (-norms[i], i),
            )
            independent = list(mandatory)
            current_rank = len(independent)
            for i in candidates:
                if norms[i] == 0:
                    continue
                trial = independent + [i]
                trial_norms = norms[trial]
                scaled = X[:, trial] / trial_norms
                trial_rank = np.linalg.matrix_rank(scaled, tol=tol)
                if trial_rank > current_rank:
                    independent.append(i)
                    current_rank = trial_rank
            independent.sort()
        else:
            independent = []
            for i in range(X.shape[1]):
                candidate = independent + [i]
                _, candidate_r = np.linalg.qr(X[:, candidate], mode="reduced")
                candidate_diag = np.abs(np.diag(candidate_r))
                candidate_rank = int(
                    np.sum(candidate_diag > tol * candidate_diag.max())
                )
                if candidate_rank > len(independent):
                    independent.append(i)
        dropped = [names[i] for i in range(X.shape[1]) if i not in independent]
        return X[:, independent], dropped, independent

    independent = []
    dropped = []
    current_rank = 0
    for i in range(X.shape[1]):
        candidate_cols = independent + [i]
        candidate_rank = np.linalg.matrix_rank(X[:, candidate_cols], tol=tol)
        if candidate_rank > current_rank:
            independent.append(i)
            current_rank = candidate_rank
        else:
            dropped.append(names[i])
    return X[:, independent], dropped, independent
