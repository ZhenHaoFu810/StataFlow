"""
Golden test: w3_probit_robust - Probit regression with robust VCE.

Tests probit robust sandwich VCE with correct probit score,
verifying coefficient estimates and robust standard errors align with Stata.
"""

import re
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from stataflow import Probit
from stataflow.stata_runner import StataRunner
from tests.golden.test_utils import (
    PROJECT_STATA_OUTPUT,
    PROJECT_STATA_CASES,
    tolerance_close,
)


def _generate_test_data() -> pd.DataFrame:
    """Generate basic probit test dataset with known seed."""
    np.random.seed(54321)
    n = 200
    x1 = np.random.normal(0, 1, n)
    x2 = np.random.normal(0, 1, n)
    eta = 0.5 + 0.8 * x1 - 0.6 * x2
    from scipy.stats import norm
    p = norm.cdf(eta)
    y = (np.random.rand(n) < p).astype(float)
    return pd.DataFrame({"y": y, "x1": x1, "x2": x2})


def _parse_stata_log(log_content: str) -> dict:
    """Parse Stata probit log output."""
    result = {}

    coefficients = []
    b_matches = {k.lower(): v for k, v in re.findall(r'B_(\w+)=(-?[\d.]+)', log_content)}
    se_matches = {k.lower(): v for k, v in re.findall(r'SE_(\w+)=(-?[\d.]+)', log_content)}

    for name in ['x1', 'x2', '_cons']:
        if name in b_matches and name in se_matches:
            coefficients.append({
                'name': name,
                'beta': float(b_matches[name]),
                'std_err': float(se_matches[name]),
            })

    result['coefficients'] = coefficients
    return result


def _run_stata_probit(data: pd.DataFrame) -> dict:
    """Run Stata probit with robust VCE."""
    dta_file = PROJECT_STATA_CASES / "w3_probit_robust_data.dta"
    data.to_stata(str(dta_file), write_index=False)

    do_template = f'''
clear all
set more off

use "{dta_file}", clear

probit y x1 x2, vce(robust)

display "B_x1=" _b[x1]
display "SE_x1=" _se[x1]
display "B_x2=" _b[x2]
display "SE_x2=" _se[x2]
display "B__cons=" _b[_cons]
display "SE__cons=" _se[_cons]

display "Stata probit robust completed successfully"
'''
    runner = StataRunner()
    result = runner.run_do_file(do_template, output_dir=str(PROJECT_STATA_OUTPUT))

    if result.exit_code != 0:
        raise RuntimeError(f"Stata failed: {result.error_message}")
    if not result.output_content:
        raise RuntimeError("Stata produced no output")

    return _parse_stata_log(result.output_content)


class TestW3ProbitRobust:
    """Golden test for w3_probit_robust."""

    @pytest.fixture(scope="class")
    def test_data(self):
        return _generate_test_data()

    @pytest.fixture(scope="class")
    def python_result(self, test_data):
        model = Probit(data=test_data, y="y", x=["x1", "x2"], add_constant=True)
        return model.fit(vce="robust")

    @pytest.fixture(scope="class")
    def stata_result(self, test_data):
        return _run_stata_probit(test_data)

    def test_coefficients_count(self, python_result, stata_result):
        assert len(python_result.coefficients) == len(stata_result.get("coefficients", []))

    def test_coefficients_names(self, python_result, stata_result):
        py_names = [c.name for c in python_result.coefficients]
        st_names = [c["name"] for c in stata_result.get("coefficients", [])]
        assert py_names == st_names, f"Names differ: Python={py_names}, Stata={st_names}"

    def test_coefficients_beta(self, python_result, stata_result):
        for py_coef, st_coef in zip(
            python_result.coefficients, stata_result.get("coefficients", [])
        ):
            passed, msg = tolerance_close(
                py_coef.beta, st_coef["beta"], name=f"beta[{py_coef.name}]"
            )
            assert passed, msg

    def test_coefficients_std_err(self, python_result, stata_result):
        for py_coef, st_coef in zip(
            python_result.coefficients, stata_result.get("coefficients", [])
        ):
            passed, msg = tolerance_close(
                py_coef.std_err, st_coef["std_err"], name=f"std_err[{py_coef.name}]"
            )
            assert passed, msg
