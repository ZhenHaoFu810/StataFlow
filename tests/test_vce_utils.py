"""Tests for shared VCE and collinearity utilities."""

import numpy as np

from stataflow.estimators._vce_utils import (
    compute_cluster_meat,
    compute_multiway_cluster_vce,
    detect_collinear_columns,
    fix_psd,
    fix_psd_reghdfe,
)


def test_detect_collinear_columns_keeps_late_independent_column_when_wide():
    """Wide designs should keep later columns if they add rank."""
    eye = np.eye(5)
    X = np.column_stack([
        eye[:, 0],
        eye[:, 1],
        eye[:, 2],
        eye[:, 3],
        eye[:, 0] + eye[:, 1],
        eye[:, 4],
        eye[:, 2] + eye[:, 3],
    ])
    names = [f"x{i}" for i in range(X.shape[1])]

    X_indep, dropped, kept = detect_collinear_columns(X, names)

    assert kept == [0, 1, 2, 3, 5]
    assert dropped == ["x4", "x6"]
    assert np.linalg.matrix_rank(X_indep) == np.linalg.matrix_rank(X)


def test_detect_collinear_columns_uses_scale_aware_pivoting():
    """Near-collinear small-scale columns should yield to stable large pivots."""
    rng = np.random.default_rng(20260613)
    x1 = rng.normal(size=50)
    x2 = (x1 + rng.normal(scale=1e-7, size=50)) * 1e6
    X = np.column_stack([x1, x2, np.ones(50)])

    X_indep, dropped, kept = detect_collinear_columns(
        X, ["x1", "x2", "_cons"]
    )

    assert kept == [1, 2]
    assert dropped == ["x1"]
    assert X_indep.shape == (50, 2)


def test_detect_collinear_columns_preserves_constant_across_extreme_scales():
    """The scale-aware path must not discard Stata's intercept."""
    rng = np.random.default_rng(2026061204)
    x1 = rng.normal(size=250)
    x2 = (x1 + rng.normal(scale=1e-7, size=250)) * 1e6
    X = np.column_stack([x1, x2, np.ones(250)])

    X_indep, dropped, kept = detect_collinear_columns(
        X, ["x1", "x2", "_cons"]
    )

    assert kept == [1, 2]
    assert dropped == ["x1"]
    assert X_indep.shape == (250, 2)


def test_fix_psd_reghdfe_without_constant_does_not_treat_last_slope_as_constant():
    """No-constant reported VCE should apply a generic PSD fix to all slopes."""
    mat = np.array([
        [1.0, 0.0, 1.4],
        [0.0, 1.0, 0.0],
        [1.4, 0.0, 1.0],
    ])

    fixed = fix_psd_reghdfe(mat, constant_index=None)

    eigvals = np.linalg.eigvalsh(fixed)
    assert np.min(eigvals) >= -1e-12
    assert not np.allclose(fixed[:2, :2], mat[:2, :2])


def test_fix_psd_reghdfe_restores_slope_block_after_full_matrix_fix():
    """Reghdfe fixes the full VCE, then restores the slope block."""
    mat = np.array([
        [1.0, 0.0, 1.4],
        [0.0, 1.0, 0.0],
        [1.4, 0.0, 1.0],
    ])

    fixed = fix_psd_reghdfe(mat.copy(), constant_index=2)

    assert np.allclose(fixed[:2, :2], mat[:2, :2])
    assert not np.isclose(fixed[2, 2], mat[2, 2])
    assert fixed[2, 2] >= 0.0


def test_fix_psd_reghdfe_preserves_slope_block_when_constant_variance_is_negative():
    """A negative _cons variance is corrected without changing valid slopes."""
    mat = np.array([
        [0.01500439, -0.00227936, -0.00201321],
        [-0.00227936, 0.00781007, 0.00166196],
        [-0.00201321, 0.00166196, -0.00560264],
    ])

    fixed = fix_psd_reghdfe(mat.copy(), constant_index=2)

    assert np.allclose(fixed[:2, :2], mat[:2, :2])
    assert fixed[2, 2] >= 0.0


def test_fix_psd_reghdfe_applies_fix_on_standardized_scale():
    """PSD correction must occur before coefficients are returned to original units."""
    mat = np.array([
        [1.0, 0.0, 1.4],
        [0.0, 1.0, 0.0],
        [1.4, 0.0, 1.0],
    ])
    scales = np.array([2.0, 0.5, 4.0])

    fixed = fix_psd_reghdfe(mat, constant_index=2, coefficient_scales=scales)
    standardized = mat * np.outer(scales, scales)
    expected = fix_psd_reghdfe(standardized, constant_index=2)
    expected /= np.outer(scales, scales)

    assert np.allclose(fixed, expected)


def test_fix_psd_reghdfe_standardizes_models_without_constant():
    """No-constant models still require PSD correction on standardized inputs."""
    mat = np.array([
        [1.0, 1.4],
        [1.4, 1.0],
    ])
    scales = np.array([3.0, 0.5])

    fixed = fix_psd_reghdfe(
        mat,
        constant_index=None,
        coefficient_scales=scales,
    )
    expected = fix_psd(mat * np.outer(scales, scales))
    expected /= np.outer(scales, scales)

    assert np.allclose(fixed, expected)


def test_multiway_cluster_interaction_avoids_separator_collision():
    """2-way cluster interaction must not merge distinct pairs when values contain '__'."""
    from stataflow.estimators._vce_utils import compute_cluster_meat

    rng = np.random.default_rng(42)
    n = 100
    k = 3
    X = rng.normal(size=(n, k))
    residuals = rng.normal(size=n)

    # cluster1 has 'a__b', cluster2 has 'c'
    # Another row has 'a' in cluster1 and 'b__c' in cluster2
    # Old string-based interaction would produce 'a__b__c' for both
    c1 = np.array(['a__b'] * 50 + ['a'] * 50)
    c2 = np.array(['c'] * 50 + ['b__c'] * 50)

    # Build interaction the same way compute_multiway_cluster_vce does
    seen = {}
    interaction = np.empty(len(c1), dtype=int)
    idx = 0
    for i, (a, b) in enumerate(zip(c1, c2)):
        key = (a, b)
        if key not in seen:
            seen[key] = idx
            idx += 1
        interaction[i] = seen[key]

    meat, G = compute_cluster_meat(X, residuals, interaction)
    # There are exactly 2 distinct pairs: ('a__b','c') and ('a','b__c')
    assert G == 2, f"Expected 2 interaction clusters, got {G}"

    # Old string approach would have produced 'a__b__c' for both pairs
    old_interaction = np.array([f"{a}__{b}" for a, b in zip(c1, c2)])
    old_meat, old_G = compute_cluster_meat(X, residuals, old_interaction)
    # This demonstrates the bug: old approach sees only 1 cluster
    assert old_G == 1, f"Old approach should show 1 merged cluster, got {old_G}"


def test_multiway_cluster_vce_falls_back_when_one_dimension_has_too_few_clusters():
    """Two-way cluster should fall back to the richer one-way dimension when G<3."""
    X = np.array([
        [1.0, 0.0],
        [1.0, 1.0],
        [1.0, 2.0],
        [1.0, 3.0],
        [1.0, 4.0],
        [1.0, 5.0],
    ])
    residuals = np.array([1.0, -1.0, 0.5, -0.5, 0.75, -0.75])
    M_inv = np.linalg.inv(X.T @ X)
    c1 = np.array([0, 0, 1, 1, 2, 2])
    c2 = np.array([0, 0, 0, 1, 1, 1])  # only 2 clusters -> fallback

    cov_2way, cluster_count = compute_multiway_cluster_vce(
        X, residuals, M_inv, [c1, c2], k_eff=2, n=len(residuals)
    )
    meat_1way, cluster_count_1way = compute_cluster_meat(X, residuals, c1)
    n_adj = (len(residuals) - 1) / (len(residuals) - 2)
    g_adj = cluster_count_1way / (cluster_count_1way - 1)
    cov_1way = n_adj * g_adj * M_inv @ meat_1way @ M_inv

    assert cluster_count == 3
    assert cluster_count_1way == 3
    assert np.allclose(cov_2way, cov_1way)
