"""
Golden test: p2_aweight_missing_weight - aweight with missing weight values.

Tests that when weight has missing values, the corresponding observations
are dropped, matching Stata's behavior with [aweight=...].
"""

import tempfile
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from tests.golden.test_utils import (
    PROJECT_STATA_OUTPUT,
    run_stata_ols,
    tolerance_close,
)
from statapy import OLS

# Use temp directory to avoid OneDrive file locking
TEMP_DIR = Path(tempfile.mkdtemp(prefix="statapy_aweight_missing_"))


def _generate_test_data() -> pd.DataFrame:
    """Generate test dataset with some missing weights."""
    np.random.seed(88888)
    n = 150

    x1 = np.random.normal(0, 1, n)
    x2 = np.random.normal(0, 1, n)
    error = np.random.normal(0, 1, n)
    y = 2 + 1.5 * x1 - 1 * x2 + error

    # Weights with some missing values (NaN)
    weights = np.abs(np.random.exponential(scale=2.0, size=n)) + 0.5
    # Set 20 weights to NaN
    nan_idx = np.random.choice(n, size=20, replace=False)
    weights_with_nan = weights.copy()
    weights_with_nan[nan_idx] = np.nan

    return pd.DataFrame({
        "y": y,
        "x1": x1,
        "x2": x2,
        "weight": weights_with_nan,
    })


def _run_stata_aweight_missing(data: pd.DataFrame) -> dict:
    """Run Stata regress with [aweight=weight] where weight has missing values."""
    dta_file = TEMP_DIR / "p2_aweight_missing_data.dta"
    data.to_stata(str(dta_file), write_index=False)

    do_template = '''
clear all
set more off

// Read data
use "$DATA_FILE", clear

// Run regression with analytical weights (Stata will drop obs with missing weights)
regress y x1 x2 [aweight=weight]

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

display "Stata regress y x1 x2 [aweight=weight] with missing weights completed"
'''
    do_content = do_template.replace("$DATA_FILE", str(dta_file))
    return run_stata_ols(do_content)


class TestP2AweightMissingWeight:
    """Golden test for aweight with missing weight values."""

    @pytest.fixture(scope="class")
    def test_data(self):
        """Generate test data once per class."""
        return _generate_test_data()

    @pytest.fixture(scope="class")
    def python_result(self, test_data):
        """Run Python OLS with aweight and missing weights."""
        model = OLS(
            data=test_data,
            y="y",
            x=["x1", "x2"],
            add_constant=True,
            weights=test_data["weight"],
            weight_type="aweight",
        )
        return model.fit(vce="ols")

    @pytest.fixture(scope="class")
    def stata_result(self, test_data):
        """Get Stata aweight results with missing weights."""
        return _run_stata_aweight_missing(test_data)

    def test_nobs_after_drop(self, python_result, stata_result):
        """Compare sample size after dropping missing weights."""
        passed, msg = tolerance_close(
            python_result.sample.nobs, stata_result.get('nobs'), name="nobs_after_drop"
        )
        assert passed, msg

    def test_n_input_rows(self, python_result, test_data):
        """Verify original row count is preserved."""
        assert python_result.sample.n_input_rows == len(test_data)

    def test_sample_mask_dropped_count(self, python_result, test_data):
        """Check that dropped count matches NaN weights."""
        n_kept = sum(python_result.sample.sample_mask)
        n_dropped = len(test_data) - n_kept
        n_nan = test_data["weight"].isna().sum()
        assert n_dropped == n_nan, f"Dropped {n_dropped} but expected {n_nan} NaN weights"

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

    def test_rmse(self, python_result, stata_result):
        """Compare RMSE."""
        passed, msg = tolerance_close(
            python_result.fit.rmse, stata_result.get('rmse'), name="rmse"
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
                py_coef.std_err, st_coef['std_err'], name=f"se[{py_coef.name}]"
            )
            assert passed, msg
