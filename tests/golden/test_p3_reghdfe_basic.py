"""
Golden test: p3_reghdfe_basic - reghdfe with 1 FE (synthetic).

Tests that Python AbsorbingOLS with absorb=[var] matches Stata's reghdfe:
- Coefficient estimates
- Standard errors
- R-squared, Adjusted R-squared
- F-statistic, RMSE
- Degrees of freedom (including df_a)
"""

import pytest
import numpy as np
import pandas as pd
from tests.golden.test_utils import (
    PROJECT_STATA_OUTPUT,
    PROJECT_STATA_CASES,
    StataRunner,
    tolerance_close,
    parse_stata_log_with_precise_coefs,
)
from stataflow import AbsorbingOLS


def _generate_test_data() -> pd.DataFrame:
    """Generate test dataset with known seed."""
    np.random.seed(88888)
    n_entities = 15
    n_per_entity = 10
    n = n_entities * n_per_entity

    entity_id = np.repeat(np.arange(n_entities), n_per_entity)
    x1 = np.random.normal(0, 1, n)
    x2 = np.random.normal(0, 1, n)
    entity_fe = np.repeat(np.random.normal(0, 2, n_entities), n_per_entity)
    error = np.random.normal(0, 1, n)
    y = 1 + 1.5 * x1 - 2 * x2 + entity_fe + error

    return pd.DataFrame({
        "y": y,
        "x1": x1,
        "x2": x2,
        "entity_id": entity_id,
    })


def _run_stata_reghdfe(data: pd.DataFrame) -> dict:
    """Run Stata reghdfe for basic test."""
    dta_file = PROJECT_STATA_CASES / "p3_reghdfe_basic_data.dta"
    data.to_stata(str(dta_file), write_index=False)

    do_template = f'''
clear all
set more off

// Read data
use "{dta_file}", clear

// Run reghdfe
reghdfe y x1 x2, absorb(entity_id) keepsingletons

// Output precise e() values for parsing
display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_DF_R=" e(df_r)
display "E_DF_A=" e(df_a)
display "E_R2=" e(r2)
display "E_R2_A=" e(r2_a)
display "E_RMSE=" e(rmse)
display "E_F=" e(F)

// Output precise coefficients and standard errors
display "B_X1=" _b[x1]
display "B_X2=" _b[x2]
display "B__CONS=" _b[_cons]

display "SE_X1=" _se[x1]
display "SE_X2=" _se[x2]
display "SE__CONS=" _se[_cons]

display "Stata reghdfe basic completed successfully"
'''
    runner = StataRunner()
    result = runner.run_do_file(do_template, output_dir=str(PROJECT_STATA_OUTPUT))

    if result.exit_code != 0:
        raise RuntimeError(f"Stata failed: {result.error_message}")
    if not result.output_content:
        raise RuntimeError("Stata produced no output")

    return parse_stata_log_with_precise_coefs(result.output_content)


class TestP3ReghdfeBasic:
    """Golden test for p3_reghdfe_basic."""

    @pytest.fixture(scope="class")
    def test_data(self):
        """Generate test data once per class."""
        return _generate_test_data()

    @pytest.fixture(scope="class")
    def python_result(self, test_data):
        """Run Python AbsorbingOLS in reghdfe mode."""
        model = AbsorbingOLS(
            data=test_data,
            y="y",
            x=["x1", "x2"],
            absorb=["entity_id"],
            add_constant=True,
        )
        return model.fit(vce="ols")

    @pytest.fixture(scope="class")
    def stata_result(self, test_data):
        """Get Stata reghdfe results."""
        return _run_stata_reghdfe(test_data)

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

    def test_df_a(self, python_result, stata_result):
        """Compare absorbed degrees of freedom."""
        passed, msg = tolerance_close(
            python_result.fit.df_a, stata_result.get('df_a'), name="df_a"
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

    def test_r2_adj(self, python_result, stata_result):
        """Compare Adjusted R-squared."""
        passed, msg = tolerance_close(
            python_result.fit.r2_adj, stata_result.get('r2_adj'), name="r2_adj"
        )
        assert passed, msg

    def test_rmse(self, python_result, stata_result):
        """Compare RMSE."""
        passed, msg = tolerance_close(
            python_result.fit.rmse, stata_result.get('rmse'), name="rmse"
        )
        assert passed, msg

    def test_f_stat(self, python_result, stata_result):
        """Compare F-statistic."""
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

    def test_absorb_vars(self, python_result):
        """Verify absorb variables are recorded."""
        assert python_result.model.absorb_vars == ["entity_id"]
