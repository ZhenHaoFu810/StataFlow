"""
P1 verification: PPMLHDFE robust VCE correction factor.

Validates VCE-P1-2: does PPMLHDFE robust VCE use n/(n-1) correction,
consistent with Stata's ppmlhdfe, vce(robust)?
"""

import pytest
import numpy as np
import pandas as pd
from tests.golden.test_utils import (
    PROJECT_STATA_OUTPUT, PROJECT_STATA_CASES, StataRunner,
    tolerance_close, parse_stata_log_with_precise_coefs,
)
from stataflow import PPMLHDFE


def _generate_test_data() -> pd.DataFrame:
    np.random.seed(23456)
    n = 100
    x1 = np.random.normal(0, 0.5, n)
    x2 = np.random.normal(0, 0.5, n)
    firm_id = np.random.randint(0, 10, n)
    eta = 0.3 * x1 + 0.5 * x2 + np.random.normal(0, 0.1, n)
    y = np.random.poisson(np.exp(eta))
    return pd.DataFrame({"y": y, "x1": x1, "x2": x2, "firm_id": firm_id})


def _run_stata(data: pd.DataFrame) -> dict:
    dta_file = PROJECT_STATA_CASES / "p1v_ppmlhdfe_robust_data.dta"
    data.to_stata(str(dta_file), write_index=False)
    do_template = f'''
clear all
set more off
use "{dta_file}", clear
ppmlhdfe y x1 x2, absorb(firm_id) vce(robust)
display "E_N=" e(N)
display "B_X1=" _b[x1]
display "B_X2=" _b[x2]
display "SE_X1=" _se[x1]
display "SE_X2=" _se[x2]
display "P1V_PPML_ROBUST completed"
'''
    runner = StataRunner()
    result = runner.run_do_file(do_template, output_dir=str(PROJECT_STATA_OUTPUT))
    if result.exit_code != 0:
        raise RuntimeError(f"Stata failed: {result.error_message}")
    return parse_stata_log_with_precise_coefs(result.output_content, coef_names=['x1', 'x2'])


class TestP1VPPMLHDFERobust:
    @pytest.fixture(scope="class")
    def test_data(self):
        return _generate_test_data()

    @pytest.fixture(scope="class")
    def python_result(self, test_data):
        model = PPMLHDFE(data=test_data, y="y", x=["x1", "x2"], absorb=["firm_id"])
        return model.fit(vce="robust")

    @pytest.fixture(scope="class")
    def stata_result(self, test_data):
        return _run_stata(test_data)

    def test_coefficients_beta(self, python_result, stata_result):
        for py_coef, st_coef in zip(python_result.coefficients, stata_result.get('coefficients', [])):
            passed, msg = tolerance_close(py_coef.beta, st_coef['beta'], name=f"beta[{py_coef.name}]")
            assert passed, msg

    def test_coefficients_std_err(self, python_result, stata_result):
        for py_coef, st_coef in zip(python_result.coefficients, stata_result.get('coefficients', [])):
            passed, msg = tolerance_close(py_coef.std_err, st_coef['std_err'],
                                          name=f"std_err[{py_coef.name}]", rtol=1e-4)
            assert passed, msg
