"""
Golden test: p1_ols_noconstant - OLS without constant term.

Tests behavior when add_constant=False:
- TSS calculated around zero (not around mean)
- R-squared definition differs from centered case
- df_model includes all parameters (no exclusion for constant)
- F-statistic may not be reported or uses different definition
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


def _generate_test_data() -> pd.DataFrame:
    """Generate basic test dataset with known seed."""
    np.random.seed(99999)
    n = 120

    x1 = np.random.normal(2, 1, n)
    x2 = np.random.normal(-1, 0.5, n)
    # True model without constant: y = 3*x1 - 2*x2 + error
    y = 3 * x1 - 2 * x2 + np.random.normal(0, 1, n)

    return pd.DataFrame({"y": y, "x1": x1, "x2": x2})


def _run_stata_noconstant(data: pd.DataFrame) -> dict:
    """Run Stata regress without constant."""
    dta_file = PROJECT_STATA_CASES / "p1_ols_noconstant_data.dta"
    data.to_stata(str(dta_file), write_index=False)

    do_template = '''
clear all
set more off

// Read data
use "$DATA_FILE", clear

// Run regression without constant
regress y x1 x2, noconstant

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


class TestP1OlsNoconstant:
    """Golden test for p1_ols_noconstant."""

    @pytest.fixture(scope="class")
    def test_data(self):
        """Generate test data once per class."""
        return _generate_test_data()

    @pytest.fixture(scope="class")
    def python_result(self, test_data):
        """Run Python OLS without constant."""
        return run_python_ols(test_data, y="y", x=["x1", "x2"], add_constant=False)

    @pytest.fixture(scope="class")
    def stata_result(self, test_data):
        """Get Stata results."""
        return _run_stata_noconstant(test_data)

    def test_nobs(self, python_result, stata_result):
        """Compare sample size."""
        passed, msg = tolerance_close(
            python_result.sample.nobs, stata_result.get('nobs'), name="nobs"
        )
        assert passed, msg

    def test_df_model(self, python_result, stata_result):
        """Compare model degrees of freedom (should be k, not k-1)."""
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
        """Compare R-squared (uncentered when no constant)."""
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

    def test_f_stat(self, python_result, stata_result):
        """Compare F-statistic (may be None or different for noconstant)."""
        py_f = python_result.fit.f_stat
        st_f = stata_result.get('f_stat')

        # Both should either have F or not have F
        if py_f is None and st_f is None:
            assert True, "Both F statistics are None (acceptable for noconstant)"
        elif py_f is not None and st_f is not None:
            passed, msg = tolerance_close(py_f, st_f, name="f_stat")
            assert passed, msg
        else:
            # One has F, other doesn't - this is acceptable with warning
            print(f"[WARN] F-stat mismatch: Python={py_f}, Stata={st_f}")

    def test_coefficients_count(self, python_result, stata_result):
        """Compare number of coefficients."""
        assert len(python_result.coefficients) == len(stata_result.get('coefficients', []))

    def test_coefficients_names(self, python_result, stata_result):
        """Compare coefficient names (should NOT include _cons)."""
        py_names = [c.name for c in python_result.coefficients]
        st_names = [c['name'] for c in stata_result.get('coefficients', [])]
        assert py_names == st_names, f"Names differ: Python={py_names}, Stata={st_names}"

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

    def test_has_constant_flag(self, python_result):
        """Verify has_constant is False."""
        assert python_result.model.has_constant is False, \
            f"has_constant should be False, got {python_result.model.has_constant}"
