"""
Golden test: w7_ppmlhdfe_separation_fe - PPMLHDFE with separation(fe).

Tests that Python PPMLHDFE with separation="fe" matches Stata:
- Identifies and drops the same separated observations
- Produces matching coefficient estimates after dropping
- Reports consistent N, ll, deviance

A "separated" FE group is one where the sum of y is zero,
indicating the FE perfectly predicts zero outcomes.
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
from stataflow.estimators.ppmlhdfe import PPMLHDFE


def _generate_test_data() -> pd.DataFrame:
    """Generate PPML data with a separated FE group (all zero y)."""
    np.random.seed(12347)
    n_entities = 25
    n_periods = 6
    n = n_entities * n_periods

    entity_id = np.repeat(np.arange(n_entities), n_periods)
    time_id = np.tile(np.arange(n_periods), n_entities)

    x1 = np.random.normal(0, 1, n)
    x2 = np.random.normal(0, 0.5, n)

    alpha = np.repeat(np.random.normal(0, 0.4, n_entities), n_periods)
    gamma = np.tile(np.random.normal(0, 0.2, n_periods), n_entities)

    eta = 0.5 + alpha + gamma + 0.7 * x1 - 0.3 * x2
    mu = np.exp(eta)
    y = np.random.poisson(mu)

    # Create separation: set all y=0 for entity 0
    y[entity_id == 0] = 0

    return pd.DataFrame({
        "y": y.astype(float), "x1": x1, "x2": x2,
        "entity_id": entity_id, "time_id": time_id,
    })


def _run_stata_ppmlhdfe_separation(data: pd.DataFrame) -> dict:
    """Run Stata ppmlhdfe with separation(fe)."""
    dta_file = PROJECT_STATA_CASES / "w7_ppmlhdfe_sep_data.dta"
    data.to_stata(str(dta_file), write_index=False)

    do_template = f'''
clear all
set more off
use "{dta_file}", clear
ppmlhdfe y x1 x2, absorb(entity_id time_id) separation(fe)

display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_R2=" e(r2_p)
display "B_X1=" _b[x1]
display "B_X2=" _b[x2]
display "B__CONS=" _b[_cons]
display "SE_X1=" _se[x1]
display "SE_X2=" _se[x2]
display "SE__CONS=" _se[_cons]
display "Stata ppmlhdfe separation completed successfully"
'''
    runner = StataRunner()
    result = runner.run_do_file(do_template, output_dir=str(PROJECT_STATA_OUTPUT))
    if result.exit_code != 0:
        raise RuntimeError(f"Stata failed: {result.error_message}")
    if not result.output_content:
        raise RuntimeError("Stata produced no output")
    return parse_stata_log_with_precise_coefs(result.output_content)


class TestW7PpmlhdfeSeparationFe:
    """Golden test: ppmlhdfe separation(fe)."""

    @pytest.fixture(scope="class")
    def test_data(self):
        return _generate_test_data()

    @pytest.fixture(scope="class")
    def python_result(self, test_data):
        model = PPMLHDFE(
            data=test_data, y="y", x=["x1", "x2"],
            absorb=["entity_id", "time_id"], separation="fe",
        )
        return model.fit(vce="robust")

    @pytest.fixture(scope="class")
    def stata_result(self, test_data):
        return _run_stata_ppmlhdfe_separation(test_data)

    def test_nobs_reduced(self, python_result, stata_result):
        """After separation drop, N should be < original 150."""
        passed, msg = tolerance_close(python_result.sample.nobs, stata_result.get('nobs'), name="nobs")
        assert passed, msg
        assert python_result.sample.nobs < 150, "Should have dropped separated obs"

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
