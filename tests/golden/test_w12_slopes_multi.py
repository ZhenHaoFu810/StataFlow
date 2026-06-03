"""
Golden test: w12_slopes_multi - multi-slope absorption (synthetic).

Tests that Python reghdfe with absorb(firm_id##c.(time z)) matches Stata.
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
    N = 50
    T = 10
    n = N * T

    firm_id = np.repeat(np.arange(N), T)
    time = np.tile(np.arange(T), N)
    x = np.random.normal(0, 1, n)
    z = np.random.normal(0, 1, n)
    firm_fe = np.repeat(np.random.normal(0, 2, N), T)
    firm_slope1 = np.repeat(np.random.normal(0, 0.5, N), T)
    firm_slope2 = np.repeat(np.random.normal(0, 0.3, N), T)
    eps = np.random.normal(0, 1, n)
    y = 1 + 0.5 * x + firm_fe + firm_slope1 * time + firm_slope2 * z + eps

    return pd.DataFrame({
        "y": y,
        "x": x,
        "z": z,
        "firm_id": firm_id,
        "time": time,
    })


def _run_stata(data: pd.DataFrame) -> dict:
    """Run Stata reghdfe with multi-slope absorption."""
    dta_file = PROJECT_STATA_CASES / "w12_slopes_multi_data.dta"
    data.to_stata(str(dta_file), write_index=False)

    do_template = f'''
clear all
set more off

use "{dta_file}", clear

reghdfe y x, absorb(firm_id##c.(time z)) keepsingletons

display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_DF_R=" e(df_r)
display "E_DF_A=" e(df_a)
display "E_R2=" e(r2)
display "E_R2_A=" e(r2_a)
display "E_RMSE=" e(rmse)
display "E_F=" e(F)

display "B_X=" _b[x]
display "B__CONS=" _b[_cons]
display "SE_X=" _se[x]
display "SE__CONS=" _se[_cons]

display "Stata slopes multi completed successfully"
'''
    runner = StataRunner()
    result = runner.run_do_file(do_template, output_dir=str(PROJECT_STATA_OUTPUT))

    if result.exit_code != 0:
        raise RuntimeError(f"Stata failed: {result.error_message}")
    if not result.output_content:
        raise RuntimeError("Stata produced no output")

    return parse_stata_log_with_precise_coefs(result.output_content, coef_names=['x', '_cons'])


class TestW12SlopesMulti:
    @pytest.fixture(scope="class")
    def test_data(self):
        return _generate_test_data()

    @pytest.fixture(scope="class")
    def python_result(self, test_data):
        model = AbsorbingOLS(
            data=test_data,
            y="y",
            x=["x"],
            absorb="firm_id##c.(time z)",
            add_constant=True,
        )
        return model.fit(vce="ols")

    @pytest.fixture(scope="class")
    def stata_result(self, test_data):
        return _run_stata(test_data)

    def test_coefficients_beta(self, python_result, stata_result):
        for py_coef, st_coef in zip(
            python_result.coefficients, stata_result.get('coefficients', [])
        ):
            passed, msg = tolerance_close(
                py_coef.beta, st_coef['beta'], name=f"beta[{py_coef.name}]"
            )
            assert passed, msg

    def test_coefficients_std_err(self, python_result, stata_result):
        for py_coef, st_coef in zip(
            python_result.coefficients, stata_result.get('coefficients', [])
        ):
            passed, msg = tolerance_close(
                py_coef.std_err, st_coef['std_err'], name=f"std_err[{py_coef.name}]"
            )
            assert passed, msg
