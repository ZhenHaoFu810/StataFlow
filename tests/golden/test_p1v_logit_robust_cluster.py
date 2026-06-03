"""
P1 verification: Logit robust + cluster VCE correction factors.

Validates VCE-P1-3a/c: does Stata logit apply HC1 correction for robust VCE?
Does cluster VCE use (N-1)/(N-k) * G/(G-1)?
"""

import pytest
import numpy as np
import pandas as pd
from tests.golden.test_utils import (
    PROJECT_STATA_OUTPUT, PROJECT_STATA_CASES, StataRunner,
    tolerance_close, parse_stata_log_with_precise_coefs,
)
from stataflow import Logit


def _generate_test_data() -> pd.DataFrame:
    np.random.seed(34567)
    n = 200
    G = 20
    x1 = np.random.normal(0, 1, n)
    x2 = np.random.normal(0, 1, n)
    group = np.random.randint(0, G, n)
    eta = 0.5 * x1 + 0.8 * x2 + np.random.normal(0, 0.3, n)
    prob = 1 / (1 + np.exp(-eta))
    y = (np.random.random(n) < prob).astype(int)
    return pd.DataFrame({"y": y, "x1": x1, "x2": x2, "group": group})


def _run_stata_robust(data: pd.DataFrame) -> dict:
    dta_file = PROJECT_STATA_CASES / "p1v_logit_robust_data.dta"
    data.to_stata(str(dta_file), write_index=False)
    do_template = f'''
clear all
set more off
use "{dta_file}", clear
logit y x1 x2, vce(robust)
display "E_N=" e(N)
display "B_X1=" _b[x1]
display "B_X2=" _b[x2]
display "SE_X1=" _se[x1]
display "SE_X2=" _se[x2]
display "P1V_LOGIT_ROBUST completed"
'''
    runner = StataRunner()
    result = runner.run_do_file(do_template, output_dir=str(PROJECT_STATA_OUTPUT))
    if result.exit_code != 0:
        raise RuntimeError(f"Stata failed: {result.error_message}")
    return parse_stata_log_with_precise_coefs(result.output_content, coef_names=['x1', 'x2'])


def _run_stata_cluster(data: pd.DataFrame) -> dict:
    dta_file = PROJECT_STATA_CASES / "p1v_logit_cluster_data.dta"
    data.to_stata(str(dta_file), write_index=False)
    do_template = f'''
clear all
set more off
use "{dta_file}", clear
logit y x1 x2, vce(cluster group)
display "E_N=" e(N)
display "B_X1=" _b[x1]
display "B_X2=" _b[x2]
display "SE_X1=" _se[x1]
display "SE_X2=" _se[x2]
display "P1V_LOGIT_CLUSTER completed"
'''
    runner = StataRunner()
    result = runner.run_do_file(do_template, output_dir=str(PROJECT_STATA_OUTPUT))
    if result.exit_code != 0:
        raise RuntimeError(f"Stata failed: {result.error_message}")
    return parse_stata_log_with_precise_coefs(result.output_content, coef_names=['x1', 'x2'])


class TestP1VLogitRobust:
    @pytest.fixture(scope="class")
    def test_data(self):
        return _generate_test_data()

    @pytest.fixture(scope="class")
    def python_result(self, test_data):
        model = Logit(data=test_data, y="y", x=["x1", "x2"])
        return model.fit(vce="robust")

    @pytest.fixture(scope="class")
    def stata_result(self, test_data):
        return _run_stata_robust(test_data)

    def test_coefficients_beta(self, python_result, stata_result):
        for py_coef, st_coef in zip(python_result.coefficients, stata_result.get('coefficients', [])):
            passed, msg = tolerance_close(py_coef.beta, st_coef['beta'], name=f"beta[{py_coef.name}]")
            assert passed, msg

    def test_coefficients_std_err(self, python_result, stata_result):
        for py_coef, st_coef in zip(python_result.coefficients, stata_result.get('coefficients', [])):
            passed, msg = tolerance_close(py_coef.std_err, st_coef['std_err'],
                                          name=f"std_err[{py_coef.name}]", rtol=1e-4)
            assert passed, msg


class TestP1VLogitCluster:
    @pytest.fixture(scope="class")
    def test_data(self):
        return _generate_test_data()

    @pytest.fixture(scope="class")
    def python_result(self, test_data):
        model = Logit(data=test_data, y="y", x=["x1", "x2"])
        return model.fit(vce="cluster", cluster="group")

    @pytest.fixture(scope="class")
    def stata_result(self, test_data):
        return _run_stata_cluster(test_data)

    def test_coefficients_beta(self, python_result, stata_result):
        for py_coef, st_coef in zip(python_result.coefficients, stata_result.get('coefficients', [])):
            passed, msg = tolerance_close(py_coef.beta, st_coef['beta'], name=f"beta[{py_coef.name}]")
            assert passed, msg

    def test_coefficients_std_err(self, python_result, stata_result):
        for py_coef, st_coef in zip(python_result.coefficients, stata_result.get('coefficients', [])):
            passed, msg = tolerance_close(py_coef.std_err, st_coef['std_err'],
                                          name=f"std_err[{py_coef.name}]", rtol=1e-4)
            assert passed, msg
