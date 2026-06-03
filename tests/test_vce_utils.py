"""Tests for shared VCE and collinearity utilities."""

import numpy as np

from stataflow.estimators._vce_utils import detect_collinear_columns, fix_psd_reghdfe


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
