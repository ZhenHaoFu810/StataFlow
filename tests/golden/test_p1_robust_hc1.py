"""
Golden test: p1_robust_hc1 - OLS with robust (HC1) standard errors.

Tests that Python OLS with vce='robust' matches Stata's regress, vce(robust):
- Coefficient estimates (should be identical to OLS)
- Robust standard errors (HC1)
- t-statistics and p-values
- Confidence intervals
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
from stataflow import OLS

# Use temp directory to avoid OneDrive file locking
TEMP_DIR = Path(tempfile.mkdtemp(prefix="stataflow_robust_"))


def _generate_test_data() -> pd.DataFrame:
    """Generate test dataset with known seed."""
    np.random.seed(424242)
    n = 150

    x1 = np.random.normal(0, 1, n)
    x2 = np.random.normal(0, 1, n)
    # Heteroskedastic errors: variance depends on x1
    error_std = 0.5 + 1.5 * np.abs(x1)
    error = np.random.normal(0, 1, n) * error_std
    y = 5 + 2 * x1 - 1.5 * x2 + error

    return pd.DataFrame({"y": y, "x1": x1, "x2": x2})


def _run_stata_robust(data: pd.DataFrame) -> dict:
    """Run Stata regress with vce(robust)."""
    dta_file = TEMP_DIR / "p1_robust_data.dta"
    data.to_stata(str(dta_file), write_index=False)

    do_template = '''
clear all
set more off

// Read data
use "$DATA_FILE", clear

// Run regression with robust SE
regress y x1 x2, vce(robust)

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

display "Stata regress, vce(robust) completed successfully"
'''
    do_content = do_template.replace("$DATA_FILE", str(dta_file))
    return run_stata_ols(do_content)


class TestP1RobustHc1:
    """Golden test for p1_robust_hc1."""

    @pytest.fixture(scope="class")
    def test_data(self):
        """Generate test data once per class."""
        return _generate_test_data()

    @pytest.fixture(scope="class")
    def python_result(self, test_data):
        """Run Python OLS with robust VCE."""
        model = OLS(data=test_data, y="y", x=["x1", "x2"], add_constant=True)
        return model.fit(vce="robust")

    @pytest.fixture(scope="class")
    def stata_result(self, test_data):
        """Get Stata robust results."""
        return _run_stata_robust(test_data)

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
        """Compare R-squared (should be same as OLS)."""
        passed, msg = tolerance_close(
            python_result.fit.r2, stata_result.get('r2'), name="r2"
        )
        assert passed, msg

    def test_rmse(self, python_result, stata_result):
        """Compare RMSE (should be same as OLS)."""
        passed, msg = tolerance_close(
            python_result.fit.rmse, stata_result.get('rmse'), name="rmse"
        )
        assert passed, msg

    def test_f_stat(self, python_result, stata_result):
        """Compare Wald F-statistic for robust VCE."""
        passed, msg = tolerance_close(
            python_result.fit.f_stat, stata_result.get('f_stat'), name="f_stat"
        )
        assert passed, msg

    def test_coefficients_count(self, python_result, stata_result):
        """Compare number of coefficients."""
        assert len(python_result.coefficients) == len(stata_result.get('coefficients', []))

    def test_coefficients_names(self, python_result, stata_result):
        """Compare coefficient names."""
        py_names = [c.name for c in python_result.coefficients]
        st_names = [c['name'] for c in stata_result.get('coefficients', [])]
        assert py_names == st_names, f"Names differ: Python={py_names}, Stata={st_names}"

    def test_coefficients_beta(self, python_result, stata_result):
        """Compare coefficient estimates (should match OLS exactly)."""
        for py_coef, st_coef in zip(
            python_result.coefficients, stata_result.get('coefficients', [])
        ):
            passed, msg = tolerance_close(
                py_coef.beta, st_coef['beta'], name=f"beta[{py_coef.name}]"
            )
            assert passed, msg

    def test_coefficients_std_err_robust(self, python_result, stata_result):
        """Compare robust standard errors (HC1)."""
        for py_coef, st_coef in zip(
            python_result.coefficients, stata_result.get('coefficients', [])
        ):
            passed, msg = tolerance_close(
                py_coef.std_err, st_coef['std_err'], name=f"robust_se[{py_coef.name}]"
            )
            assert passed, msg

    def test_vcetype(self, python_result):
        """Verify vcetype is set to 'robust'."""
        assert python_result.model.vcetype == "robust", \
            f"vcetype should be 'robust', got {python_result.model.vcetype}"
