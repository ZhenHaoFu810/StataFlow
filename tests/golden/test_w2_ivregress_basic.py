"""
Golden test: w2_ivregress_basic - Basic 2SLS regression test.

Tests basic ivregress 2sls functionality with constant term, verifying:
- Coefficient estimates
- Standard errors
- R-squared, Adjusted R-squared
- F-statistic, RMSE
- Degrees of freedom
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from tests.golden.test_utils import (
    PROJECT_STATA_OUTPUT,
    PROJECT_STATA_CASES,
    run_stata_ivregress,
    run_python_iv2sls,
    tolerance_close,
)


def _generate_test_data() -> pd.DataFrame:
    """Generate basic IV test dataset with known seed."""
    np.random.seed(54321)
    n = 200

    z1 = np.random.normal(0, 1, n)
    z2 = np.random.normal(0, 1, n)
    x1 = np.random.normal(2, 1, n)

    # Endogenous x2 depends on z1, z2 and an unobserved error correlated with u
    v = np.random.normal(0, 1, n)
    x2 = 0.5 + 1.5 * z1 - 0.8 * z2 + 0.3 * x1 + v

    # Structural error correlated with v
    u = np.random.normal(0, 1, n) + 0.5 * v

    # True model: y = 3 + 2*x1 + 1.5*x2 + u
    y = 3 + 2 * x1 + 1.5 * x2 + u

    return pd.DataFrame({"y": y, "x1": x1, "x2": x2, "z1": z1, "z2": z2})


def _run_stata_ivregress_basic(data: pd.DataFrame) -> dict:
    """Run Stata ivregress 2sls for basic test."""
    dta_file = PROJECT_STATA_CASES / "w2_ivregress_basic_data.dta"
    data.to_stata(str(dta_file), write_index=False)

    do_template = '''
clear all
set more off

// Read data
use "$DATA_FILE", clear

// Run 2SLS
ivregress 2sls y x1 (x2 = z1 z2)

// Output precise e() values for parsing
display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_DF_R=" e(df_r)
display "E_R2=" e(r2)
display "E_R2_A=" e(r2_a)
display "E_RMSE=" e(rmse)
display "E_F=" e(F)
display "E_F_P=" e(F_p)

// Output precise coefficients
display "B_x1=" _b[x1]
display "SE_x1=" _se[x1]
display "B_x2=" _b[x2]
display "SE_x2=" _se[x2]
display "B__cons=" _b[_cons]
display "SE__cons=" _se[_cons]

display "Stata ivregress 2sls completed successfully"
'''
    do_content = do_template.replace("$DATA_FILE", str(dta_file))
    return run_stata_ivregress(do_content, coef_names=["x2", "x1", "_cons"])


class TestW2IvregressBasic:
    """Golden test for w2_ivregress_basic."""

    @pytest.fixture(scope="class")
    def test_data(self):
        """Generate test data once per class."""
        return _generate_test_data()

    @pytest.fixture(scope="class")
    def python_result(self, test_data):
        """Run Python IV2SLS."""
        return run_python_iv2sls(
            test_data,
            y="y",
            x_exog=["x1"],
            x_endog=["x2"],
            instruments=["z1", "z2"],
            add_constant=True,
            vce="ols",
        )

    @pytest.fixture(scope="class")
    def stata_result(self, test_data):
        """Get Stata results."""
        return _run_stata_ivregress_basic(test_data)

    def test_nobs(self, python_result, stata_result):
        """Compare sample size."""
        passed, msg = tolerance_close(
            python_result.sample.nobs, stata_result.get("nobs"), name="nobs"
        )
        assert passed, msg

    def test_df_model(self, python_result, stata_result):
        """Compare model degrees of freedom."""
        passed, msg = tolerance_close(
            python_result.fit.df_model, stata_result.get("df_model"), name="df_model"
        )
        assert passed, msg

    def test_df_resid(self, python_result, stata_result):
        """Compare residual degrees of freedom."""
        passed, msg = tolerance_close(
            python_result.fit.df_resid, stata_result.get("df_resid"), name="df_resid"
        )
        assert passed, msg

    def test_r2(self, python_result, stata_result):
        """Compare R-squared."""
        passed, msg = tolerance_close(
            python_result.fit.r2, stata_result.get("r2"), name="r2"
        )
        assert passed, msg

    def test_r2_adj(self, python_result, stata_result):
        """Compare Adjusted R-squared."""
        passed, msg = tolerance_close(
            python_result.fit.r2_adj, stata_result.get("r2_adj"), name="r2_adj"
        )
        assert passed, msg

    def test_rmse(self, python_result, stata_result):
        """Compare RMSE."""
        passed, msg = tolerance_close(
            python_result.fit.rmse, stata_result.get("rmse"), name="rmse"
        )
        assert passed, msg

    def test_f_stat(self, python_result, stata_result):
        """Compare F-statistic."""
        passed, msg = tolerance_close(
            python_result.fit.f_stat, stata_result.get("f_stat"), name="f_stat"
        )
        assert passed, msg

    def test_coefficients_count(self, python_result, stata_result):
        """Compare number of coefficients."""
        assert len(python_result.coefficients) == len(
            stata_result.get("coefficients", [])
        )

    def test_coefficients_names(self, python_result, stata_result):
        """Compare coefficient names."""
        py_names = [c.name for c in python_result.coefficients]
        st_names = [c["name"] for c in stata_result.get("coefficients", [])]
        assert py_names == st_names, f"Names differ: Python={py_names}, Stata={st_names}"

    def test_coefficients_beta(self, python_result, stata_result):
        """Compare coefficient estimates."""
        for py_coef, st_coef in zip(
            python_result.coefficients, stata_result.get("coefficients", [])
        ):
            passed, msg = tolerance_close(
                py_coef.beta, st_coef["beta"], name=f"beta[{py_coef.name}]"
            )
            assert passed, msg

    def test_coefficients_std_err(self, python_result, stata_result):
        """Compare standard errors."""
        for py_coef, st_coef in zip(
            python_result.coefficients, stata_result.get("coefficients", [])
        ):
            passed, msg = tolerance_close(
                py_coef.std_err, st_coef["std_err"], name=f"std_err[{py_coef.name}]"
            )
            assert passed, msg
