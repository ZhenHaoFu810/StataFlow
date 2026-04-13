"""
Golden test: p1_ols_missing_drop - OLS with missing values.

Tests that missing values are properly handled:
- Observations with any missing values in y or x should be dropped
- sample_mask should correctly reflect which observations were retained
- n_input_rows should show original row count before screening
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


def _generate_test_data_with_missing() -> pd.DataFrame:
    """Generate dataset with known missing values."""
    np.random.seed(11111)
    n = 150

    x1 = np.random.normal(0, 1, n)
    x2 = np.random.normal(0, 1, n)
    y = 5 + 2 * x1 + 3 * x2 + np.random.normal(0, 1, n)

    df = pd.DataFrame({"y": y, "x1": x1, "x2": x2})

    # Introduce missing values at known positions
    # Row 10: missing y
    df.loc[10, 'y'] = np.nan
    # Row 25: missing x1
    df.loc[25, 'x1'] = np.nan
    # Row 50: missing x2
    df.loc[50, 'x2'] = np.nan
    # Row 75: missing y and x1
    df.loc[75, 'y'] = np.nan
    df.loc[75, 'x1'] = np.nan

    return df


def _run_stata_missing(data: pd.DataFrame) -> dict:
    """Run Stata regress for missing value test."""
    dta_file = PROJECT_STATA_CASES / "p1_ols_missing_data.dta"
    data.to_stata(str(dta_file), write_index=False)

    do_template = '''
clear all
set more off

// Read data
use "$DATA_FILE", clear

// Run regression (Stata automatically drops observations with missing values)
regress y x1 x2

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


class TestP1OlsMissingDrop:
    """Golden test for p1_ols_missing_drop."""

    @pytest.fixture(scope="class")
    def test_data(self):
        """Generate test data with missing values once per class."""
        return _generate_test_data_with_missing()

    @pytest.fixture(scope="class")
    def python_result(self, test_data):
        """Run Python OLS."""
        return run_python_ols(test_data, y="y", x=["x1", "x2"], add_constant=True)

    @pytest.fixture(scope="class")
    def stata_result(self, test_data):
        """Get Stata results."""
        return _run_stata_missing(test_data)

    def test_nobs_after_drop(self, python_result, stata_result):
        """Compare sample size after dropping missing."""
        passed, msg = tolerance_close(
            python_result.sample.nobs, stata_result.get('nobs'), name="nobs_after_drop"
        )
        assert passed, msg

    def test_n_input_rows(self, python_result):
        """Verify n_input_rows shows original count."""
        assert python_result.sample.n_input_rows == 150, \
            f"n_input_rows should be 150, got {python_result.sample.n_input_rows}"

    def test_sample_mask_length(self, python_result):
        """Verify sample_mask has correct length."""
        assert len(python_result.sample.sample_mask) == 150, \
            f"sample_mask length should be 150, got {len(python_result.sample.sample_mask)}"

    def test_sample_mask_true_count(self, python_result):
        """Verify sample_mask has correct number of True values."""
        true_count = sum(python_result.sample.sample_mask)
        # Should have dropped 5 rows (10, 25, 50, 75 - but 75 has 2 missing, so 4 unique rows)
        # Actually rows 10, 25, 50, 75 = 4 rows dropped
        assert true_count == 146, \
            f"sample_mask should have 146 True values, got {true_count}"

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

    def test_coefficients_beta(self, python_result, stata_result):
        """Compare coefficient estimates."""
        for py_coef, st_coef in zip(
            python_result.coefficients, stata_result.get('coefficients', [])
        ):
            passed, msg = tolerance_close(
                py_coef.beta, st_coef['beta'], name=f"beta[{py_coef.name}]"
            )
            assert passed, msg

    def test_coefficients_std_err(self, python_result, stata_result):
        """Compare standard errors."""
        for py_coef, st_coef in zip(
            python_result.coefficients, stata_result.get('coefficients', [])
        ):
            passed, msg = tolerance_close(
                py_coef.std_err, st_coef['std_err'], name=f"std_err[{py_coef.name}]"
            )
            assert passed, msg
