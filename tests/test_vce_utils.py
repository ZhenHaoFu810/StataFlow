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
