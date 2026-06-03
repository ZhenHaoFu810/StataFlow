"""
Golden test: w7_reghdfe_savefe - reghdfe savefe FE extraction.

Tests that Python AbsorbingOLS with savefe=True correctly extracts
fixed effect estimates that are consistent with the LSDV dummy coefficients.
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
from stataflow.estimators.absorbing_ols import AbsorbingOLS


def _generate_test_data() -> pd.DataFrame:
    np.random.seed(12346)
    n_groups = 15
    n_per_group = 8
    n = n_groups * n_per_group
    fe1 = np.repeat(np.arange(n_groups), n_per_group)
    fe2 = np.tile(np.arange(n_per_group), n_groups)
    fe1_effect = np.repeat(np.random.randn(n_groups) * 1.0, n_per_group)
    fe2_effect = np.tile(np.random.randn(n_per_group) * 0.5, n_groups)
    x1 = np.random.randn(n) * 0.8
    x2 = np.random.randn(n) * 0.6
    y = 2.0 + 1.5 * x1 - 0.7 * x2 + fe1_effect + fe2_effect + np.random.randn(n) * 0.3
    return pd.DataFrame({
        "y": y, "x1": x1, "x2": x2, "fe1": fe1, "fe2": fe2,
    })


def _run_stata_reghdfe(data: pd.DataFrame) -> dict:
    dta_file = PROJECT_STATA_CASES / "w7_reghdfe_savefe_data.dta"
    data.to_stata(str(dta_file), write_index=False)
    do_template = f'''
clear all
set more off
use "{dta_file}", clear
reghdfe y x1 x2, absorb(fe1 fe2)
display "E_N=" e(N)
display "B_X1=" _b[x1]
display "B_X2=" _b[x2]
display "B__CONS=" _b[_cons]
display "SE_X1=" _se[x1]
display "SE_X2=" _se[x2]
display "SE__CONS=" _se[_cons]
display "Stata reghdfe completed successfully"
'''
    runner = StataRunner()
    result = runner.run_do_file(do_template, output_dir=str(PROJECT_STATA_OUTPUT))
    if result.exit_code != 0:
        raise RuntimeError(f"Stata failed: {result.error_message}")
    if not result.output_content:
        raise RuntimeError("Stata produced no output")
    return parse_stata_log_with_precise_coefs(result.output_content)


class TestW7ReghdfeSavefe:
    """Golden test: reghdfe savefe FE extraction."""

    @pytest.fixture(scope="class")
    def test_data(self):
        return _generate_test_data()

    @pytest.fixture(scope="class")
    def python_result(self, test_data):
        model = AbsorbingOLS(
            data=test_data, y="y", x=["x1", "x2"],
            absorb=["fe1", "fe2"],
        )
        return model.fit(vce="ols", savefe=True)

    @pytest.fixture(scope="class")
    def stata_result(self, test_data):
        return _run_stata_reghdfe(test_data)

    def test_nobs(self, python_result, stata_result):
        passed, msg = tolerance_close(python_result.sample.nobs, stata_result.get('nobs'), name="nobs")
        assert passed, msg

    def test_coefficients_beta(self, python_result, stata_result):
        for py_coef, st_coef in zip(
            python_result.coefficients, stata_result.get('coefficients', [])
        ):
            passed, msg = tolerance_close(py_coef.beta, st_coef['beta'], name=f"beta[{py_coef.name}]")
            assert passed, msg

    def test_coefficients_std_err(self, python_result, stata_result):
        for py_coef, st_coef in zip(
            python_result.coefficients, stata_result.get('coefficients', [])
        ):
            passed, msg = tolerance_close(py_coef.std_err, st_coef['std_err'], name=f"se[{py_coef.name}]")
            assert passed, msg

    def test_savefe_returns_dict(self, python_result):
        fe = python_result.fixed_effects
        assert fe is not None, "fixed_effects should not be None when savefe=True"
        assert isinstance(fe, dict), f"Expected dict, got {type(fe)}"

    def test_savefe_has_absorb_vars(self, python_result):
        fe = python_result.fixed_effects
        for var in ["fe1", "fe2"]:
            assert var in fe, f"Missing FE var: {var}"

    def test_savefe_fe_count_matches(self, test_data, python_result):
        fe = python_result.fixed_effects
        assert len(fe["fe1"]) == test_data["fe1"].nunique()
        assert len(fe["fe2"]) == test_data["fe2"].nunique()

    def test_savefe_values_are_finite(self, python_result):
        fe = python_result.fixed_effects
        for var in ["fe1", "fe2"]:
            for val in fe[var].values:
                assert np.isfinite(val), f"Non-finite FE value in {var}: {val}"
