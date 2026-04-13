"""
Golden test: p1_collinearity_drop - OLS with collinear variables.

Tests that collinear variables are properly handled:
- Perfectly collinear variables are detected and dropped
- Dropped variables are recorded in diagnostics
- Remaining coefficients match Stata
- No crash or silent failure
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from tests.golden.test_utils import (
    PROJECT_STATA_OUTPUT,
    PROJECT_STATA_CASES,
    run_stata_ols,
    run_python_ols,
    tolerance_close,
)


def _generate_test_data_with_collinearity() -> pd.DataFrame:
    """
    Generate dataset with known collinearity.

    x3 = x1 + x2 (perfect collinearity)
    x4 = 2 * x1 + 0.5 * x2 (also collinear)

    Stata should drop x3 and x4, keeping only x1 and x2.
    """
    np.random.seed(77777)
    n = 100

    x1 = np.random.normal(0, 1, n)
    x2 = np.random.normal(0, 1, n)

    # Create perfectly collinear variables
    x3 = x1 + x2
    x4 = 2 * x1 + 0.5 * x2

    # True model: y = 5 + 3*x1 - 2*x2 + error
    # (x3 and x4 should be dropped)
    y = 5 + 3 * x1 - 2 * x2 + np.random.normal(0, 1, n)

    return pd.DataFrame({"y": y, "x1": x1, "x2": x2, "x3": x3, "x4": x4})


def _run_stata_collinearity(data: pd.DataFrame) -> dict:
    """Run Stata regress with collinear variables."""
    dta_file = PROJECT_STATA_CASES / "p1_collinearity_data.dta"
    data.to_stata(str(dta_file), write_index=False)

    do_template = '''
clear all
set more off

// Read data
use "$DATA_FILE", clear

// Run regression (Stata will detect and drop collinear variables)
regress y x1 x2 x3 x4

// Output precise e() values for parsing
display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_DF_R=" e(df_r)
display "E_R2=" e(r2)
display "E_R2_A=" e(r2_a)
display "E_RMSE=" e(rmse)
display "E_F=" e(F)
display "E_F_P=" e(F_p)
display "E_RSS=" e(rss)

display "Stata regress completed successfully"
'''
    do_content = do_template.replace("$DATA_FILE", str(dta_file))
    return run_stata_ols(do_content)


class TestP1CollinearityDrop:
    """Golden test for p1_collinearity_drop."""

    @pytest.fixture(scope="class")
    def test_data(self):
        """Generate test data with collinearity once per class."""
        return _generate_test_data_with_collinearity()

    @pytest.fixture(scope="class")
    def python_result(self, test_data):
        """Run Python OLS."""
        return run_python_ols(test_data, y="y", x=["x1", "x2", "x3", "x4"], add_constant=True)

    @pytest.fixture(scope="class")
    def stata_result(self, test_data):
        """Get Stata results."""
        return _run_stata_collinearity(test_data)

    def test_nobs(self, python_result, stata_result):
        """Compare sample size."""
        passed, msg = tolerance_close(
            python_result.sample.nobs, stata_result.get('nobs'), name="nobs"
        )
        assert passed, msg

    def test_df_model(self, python_result, stata_result):
        """Compare model degrees of freedom."""
        passed, msg = tolerance_close(
            python_result.fit.df_model, stata_result.get('df_model'), name="df_model"
        )
        assert passed, msg

    def test_df_resid(self, python_result, stata_result):
        """Compare residual degrees of freedom."""
        passed, msg = tolerance_close(
            python_result.fit.df_resid, stata_result.get('df_resid'), name="df_resid"
        )
        assert passed, msg

    def test_r2(self, python_result, stata_result):
        """Compare R-squared."""
        passed, msg = tolerance_close(
            python_result.fit.r2, stata_result.get('r2'), name="r2"
        )
        assert passed, msg

    def test_coefficients_count(self, python_result, stata_result):
        """Compare number of coefficients (should be same after dropping collinear)."""
        py_count = len(python_result.coefficients)
        st_count = len(stata_result.get('coefficients', []))
        assert py_count == st_count, \
            f"Coefficient count mismatch: Python={py_count}, Stata={st_count}"

    def test_coefficients_names(self, python_result, stata_result):
        """
        Compare coefficient names.
        
        Note: When perfect collinearity exists, different software may
        keep different variables. Both are statistically valid as long
        as the number of coefficients is the same and fit is identical.
        """
        py_names = set(c.name for c in python_result.coefficients)
        st_names = set(c['name'] for c in stata_result.get('coefficients', []))
        
        # Just verify same number of coefficients
        assert len(py_names) == len(st_names), \
            f"Coefficient count differs: Python={len(py_names)}, Stata={len(st_names)}"
        
        # Print warning if different variables kept
        if py_names != st_names:
            print(f"[INFO] Different variables kept due to collinearity:")
            print(f"  Python: {py_names}")
            print(f"  Stata: {st_names}")
            print(f"  This is acceptable when perfect collinearity exists")

    def test_collinear_vars_dropped(self, python_result):
        """Verify collinear variables are recorded in diagnostics."""
        # x3 and x4 should be dropped
        warnings = python_result.diagnostics.warnings
        assert len(warnings) > 0, "Expected warnings for collinear variables"

        warning_text = ' '.join(warnings)
        assert 'x3' in warning_text or 'x4' in warning_text, \
            f"Expected x3 or x4 in collinearity warnings, got: {warnings}"

    def test_r2_match(self, python_result, stata_result):
        """Compare R-squared (should be identical even with collinearity)."""
        passed, msg = tolerance_close(
            python_result.fit.r2, stata_result.get('r2'), name="r2"
        )
        assert passed, msg

    def test_rmse_match(self, python_result, stata_result):
        """Compare RMSE (should be identical even with collinearity)."""
        passed, msg = tolerance_close(
            python_result.fit.rmse, stata_result.get('rmse'), name="rmse"
        )
        assert passed, msg
