"""
Shared VCE utilities for cluster-robust inference and PSD fix.

Used by AbsorbingOLS, IVAbsorbingOLS, and PPMLHDFE.
Centralized per ADR-0004 to avoid code duplication.
"""

import numpy as np


def compute_cluster_meat(
    X: np.ndarray, residuals: np.ndarray, cluster_arr: np.ndarray,
) -> tuple[np.ndarray, int]:
    """Compute cluster-robust meat matrix for a single cluster dimension.

    Returns (meat, n_clusters).
    """
    k = X.shape[1]
    unique_clusters = np.unique(cluster_arr)
    meat = np.zeros((k, k))
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


def fix_psd_reghdfe(mat: np.ndarray) -> np.ndarray:
    """
    Reghdfe-style PSD fix on the reported VCV matrix.

    Truncates negative eigenvalues, then restores the slope submatrix
    from the original (preserving slope SEs exactly). This matches
    reghdfe_fix_psd in Regression.mata. Governed by ADR-0004.

    Assumes _cons is the last row/col of the matrix.
    """
    k = mat.shape[0]
    if k <= 1:
        return fix_psd(mat)

    index = list(range(k - 1))
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
        meat, G = compute_cluster_meat(X, residuals, ca)
        meats.append(meat)
        Gs.append(G)

    interaction = np.array([
        f"{a}__{b}" for a, b in zip(cluster_arrs[0], cluster_arrs[1])
    ])
    meat_12, G_12 = compute_cluster_meat(X, residuals, interaction)

    omega_meat = meats[0] + meats[1] - meat_12

    if small_sample_adjust:
        n_adj = (n - 1) / (n - k_eff) if n > k_eff else 1.0
    else:
        n_adj = 1.0

    G_min = min(Gs[0], Gs[1], G_12)
    g_adj = G_min / (G_min - 1) if G_min > 1 else 1.0

    cov_full = n_adj * g_adj * M_inv @ omega_meat @ M_inv
    return cov_full, G_min
