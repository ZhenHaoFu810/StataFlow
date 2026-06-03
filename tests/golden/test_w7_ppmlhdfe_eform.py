"""
Golden test: w7_ppmlhdfe_eform - PPMLHDFE with eform (exponentiated coefficients).

Verifies that Python PPMLHDFE with eform=True correctly computes:
- exp(beta) coefficients (incidence rate ratios)
- Delta-method SEs: SE_exp = exp(beta) * SE_raw

Strategy: Run Stata without eform to get raw estimates, compute expected
eform values via delta method, compare against Python eform output.
(Stata _b[] returns raw values even with eform display option.)
"""

import pytest
import numpy as np
import pandas as pd
from scipy.stats import norm
from tests.golden.test_utils import (
    PROJECT_STATA_OUTPUT,
    PROJECT_STATA_CASES,
    StataRunner,
    tolerance_close,
    parse_stata_log_with_precise_coefs,
)
from stataflow.estimators.ppmlhdfe import PPMLHDFE


def _generate_test_data() -> pd.DataFrame:
    np.random.seed(76543)
    n_entities = 40
    n_periods = 5
    n = n_entities * n_periods
    entity_id = np.repeat(np.arange(n_entities), n_periods)
    time_id = np.tile(np.arange(n_periods), n_entities)
    x1 = np.random.normal(0, 1, n)
    x2 = np.random.normal(0, 1, n)
    alpha_e = np.repeat(np.random.normal(0, 0.5, n_entities), n_periods)
    gamma_t = np.tile(np.random.normal(0, 0.3, n_periods), n_entities)
    eta = alpha_e + gamma_t + 0.8 * x1 - 0.5 * x2
    y = np.random.poisson(np.exp(eta))
    return pd.DataFrame({
        "y": y, "x1": x1, "x2": x2,
        "entity_id": entity_id, "time_id": time_id,
    })


def _run_stata_raw(data: pd.DataFrame) -> dict:
    """Run Stata ppmlhdfe WITHOUT eform to get raw estimates."""
    dta_file = PROJECT_STATA_CASES / "w7_ppmlhdfe_eform_data.dta"
    data.to_stata(str(dta_file), write_index=False)

    do_template = f'''
clear all
set more off
use "{dta_file}", clear
ppmlhdfe y x1 x2, absorb(entity_id time_id)
display "E_N=" e(N)
display "B_X1=" _b[x1]
display "B_X2=" _b[x2]
display "B__CONS=" _b[_cons]
display "SE_X1=" _se[x1]
display "SE_X2=" _se[x2]
display "SE__CONS=" _se[_cons]
display "Stata ppmlhdfe raw completed successfully"
'''
    runner = StataRunner()
    result = runner.run_do_file(do_template, output_dir=str(PROJECT_STATA_OUTPUT))
    if result.exit_code != 0:
        raise RuntimeError(f"Stata failed: {result.error_message}")
    if not result.output_content:
        raise RuntimeError("Stata produced no output")
    return parse_stata_log_with_precise_coefs(result.output_content)


class TestW7PpmlhdfeEform:
    """Golden test: ppmlhdfe eform vs delta-method from Stata raw."""

    @pytest.fixture(scope="class")
    def test_data(self):
        return _generate_test_data()

    @pytest.fixture(scope="class")
    def python_eform_result(self, test_data):
        model = PPMLHDFE(
            data=test_data, y="y", x=["x1", "x2"],
            absorb=["entity_id", "time_id"],
        )
        return model.fit(vce="robust", eform=True)

    @pytest.fixture(scope="class")
    def stata_raw_result(self, test_data):
        return _run_stata_raw(test_data)

    def test_base_estimates_match(self, test_data):
        """Verify Python and Stata produce same raw (non-eform) estimates."""
        model = PPMLHDFE(
            data=test_data, y="y", x=["x1", "x2"],
            absorb=["entity_id", "time_id"],
        )
        r = model.fit(vce="robust")
        st = _run_stata_raw(test_data)
        for py_coef, st_coef in zip(r.coefficients, st.get('coefficients', [])):
            passed, msg = tolerance_close(py_coef.beta, st_coef['beta'], name=f"raw_beta[{py_coef.name}]")
            assert passed, msg
            passed, msg = tolerance_close(py_coef.std_err, st_coef['std_err'], name=f"raw_se[{py_coef.name}]")
            assert passed, msg

    def test_eform_beta_is_exp_of_raw(self, python_eform_result, stata_raw_result):
        """eform beta = exp(raw beta)."""
        for py_coef, st_coef in zip(
            python_eform_result.coefficients, stata_raw_result.get('coefficients', [])
        ):
            expected = np.exp(st_coef['beta'])
            passed, msg = tolerance_close(py_coef.beta, expected, name=f"eform_beta[{py_coef.name}]")
            assert passed, msg

    def test_eform_se_is_delta_method(self, python_eform_result, stata_raw_result):
        """eform SE = exp(raw beta) * raw SE (delta method)."""
        for py_coef, st_coef in zip(
            python_eform_result.coefficients, stata_raw_result.get('coefficients', [])
        ):
            expected_se = np.exp(st_coef['beta']) * st_coef['std_err']
            passed, msg = tolerance_close(py_coef.std_err, expected_se, name=f"eform_se[{py_coef.name}]")
            assert passed, msg

    def test_eform_z_and_p_values_use_raw_scale(self, python_eform_result, stata_raw_result):
        """Stata eform displays transformed beta/SE but tests raw beta = 0."""
        for py_coef, st_coef in zip(
            python_eform_result.coefficients, stata_raw_result.get('coefficients', [])
        ):
            expected_z = st_coef['beta'] / st_coef['std_err']
            expected_p = 2 * (1 - norm.cdf(abs(expected_z)))
            passed, msg = tolerance_close(py_coef.t_stat, expected_z, name=f"eform_z[{py_coef.name}]")
            assert passed, msg
            passed, msg = tolerance_close(py_coef.p_value, expected_p, name=f"eform_p[{py_coef.name}]", rtol=1e-6)
            assert passed, msg
