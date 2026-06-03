"""
Shared VCE utilities for cluster-robust inference and PSD fix.

Used by AbsorbingOLS, IVAbsorbingOLS, and PPMLHDFE.
Centralized per ADR-0004 to avoid code duplication.
"""

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


def fix_psd_reghdfe(mat: np.ndarray, constant_index: int | None = -1) -> np.ndarray:
    """
    Reghdfe-style PSD fix on the reported VCV matrix.

    Truncates negative eigenvalues, then restores the slope submatrix
    from the original (preserving slope SEs exactly). This matches
    reghdfe_fix_psd in Regression.mata. Governed by ADR-0004.

    By default assumes _cons is the last row/col of the matrix. Pass
    ``constant_index=None`` when the reported matrix has no constant row.
    """
    k = mat.shape[0]
    if k <= 1:
        return fix_psd(mat)
    if constant_index is None:
        return fix_psd(mat)

    if constant_index < 0:
        constant_index = k + constant_index
    if constant_index < 0 or constant_index >= k:
        raise ValueError("constant_index is out of bounds for covariance matrix")

    index = [i for i in range(k) if i != constant_index]
    V_backup = mat[np.ix_(index, index)].copy()

    eigvals, eigvecs = np.linalg.eigh(mat)
    if np.min(eigvals) < 0:
        eigvals = np.maximum(eigvals, 0.0)
        mat = eigvecs @ np.diag(eigvals) @ eigvecs.T
        mat[np.ix_(index, index)] = V_backup
    return mat


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

    if small_sample_adjust:
        n_adj = (n - 1) / (n - k_eff) if n > k_eff else 1.0
    else:
        n_adj = 1.0

    G_min = min(Gs[0], Gs[1], G_12)
    g_adj = G_min / (G_min - 1) if G_min > 1 else 1.0

    cov_full = n_adj * g_adj * M_inv @ omega_meat @ M_inv
    return cov_full, G_min


def detect_collinear_columns(
    X: np.ndarray, names: list[str], tol: float = 1e-10,
) -> tuple[np.ndarray, list[str], list[int]]:
    """Detect and drop collinear columns by rank-increment screening.

    Returns (X_indep, dropped_names, kept_indices).
    Used by all estimators for pre-OLS collinearity screening (ADR-0004).
    """
    if X.shape[1] <= 1:
        return X, [], list(range(X.shape[1]))

    rank = np.linalg.matrix_rank(X)
    if rank == X.shape[1]:
        return X, [], list(range(X.shape[1]))

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
