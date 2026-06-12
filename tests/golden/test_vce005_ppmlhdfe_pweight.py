"""VCE-005 golden test: weighted PPMLHDFE robust/cluster sandwich weight order.

Stata `ppmlhdfe [pweight=w], absorb(...) vce(robust/cluster)` uses score
proportional to w * (y - mu) * x. This test verifies Python (aweight) matches
Stata (pweight) after the VCE-005 fix switched from sqrt(w)*x*e to w*x*e.
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from tests.golden.test_utils import (
    PROJECT_STATA_OUTPUT, PROJECT_STATA_CASES, StataRunner,
    tolerance_close, parse_stata_log_with_precise_coefs,
)
from stataflow.compat.stata import ppmlhdfe


def _generate_data() -> pd.DataFrame:
    np.random.seed(55558)
    n = 400
    x1 = np.random.normal(0, 1, n)
    x2 = np.random.normal(0, 1, n)
    fe1 = np.random.randint(0, 10, size=n)
    fe2 = np.random.randint(0, 5, size=n)
    g = np.random.randint(0, 15, size=n)
    eta = 0.3 + 0.5 * x1 - 0.4 * x2 + fe1 * 0.05 + fe2 * 0.03
    mu = np.exp(eta)
    y = np.random.poisson(mu)
    weights = np.abs(np.random.exponential(scale=1.5, size=n)) + 0.5
    return pd.DataFrame({"y": y, "x1": x1, "x2": x2, "fe1": fe1, "fe2": fe2, "g": g, "w": weights})


def _run_stata(data: pd.DataFrame, vce: str) -> dict:
    dta_file = PROJECT_STATA_CASES / f"vce005_ppmlhdfe_{vce}_data.dta"
    data.to_stata(str(dta_file), write_index=False)
    cmd = f"ppmlhdfe y x1 x2 [pweight=w], absorb(fe1 fe2) vce({vce})"
    do_template = f'''
clear all
set more off
use "{dta_file}", clear
{cmd}
display "E_N=" e(N)
display "B_X1=" _b[x1]
display "B_X2=" _b[x2]
display "SE_X1=" _se[x1]
display "SE_X2=" _se[x2]
display "VCE005_PPMLHDFE_{vce.upper()} completed"
'''
    runner = StataRunner()
    result = runner.run_do_file(do_template, output_dir=str(PROJECT_STATA_OUTPUT))
    if result.exit_code != 0:
        raise RuntimeError(f"Stata failed: {result.error_message}")
    return parse_stata_log_with_precise_coefs(result.output_content, coef_names=["x1", "x2"])


class TestVCE005PPMLHDFEPweightRobust:
    @pytest.fixture(scope="class")
    def data(self):
        return _generate_data()

    @pytest.fixture(scope="class")
    def python_result(self, data):
        return ppmlhdfe(data, y="y", x=["x1", "x2"], absorb=["fe1", "fe2"], aweight="w", vce="robust")

    @pytest.fixture(scope="class")
    def stata_result(self, data):
        return _run_stata(data, "robust")

    def test_coefficients_beta(self, python_result, stata_result):
        for py_coef in python_result.coefficients:
            if py_coef.name not in ("x1", "x2"):
                continue
            st = next(c for c in stata_result["coefficients"] if c["name"] == py_coef.name)
            passed, msg = tolerance_close(py_coef.beta, st["beta"], name=f"beta[{py_coef.name}]")
            assert passed, msg

    def test_coefficients_std_err(self, python_result, stata_result):
        for py_coef in python_result.coefficients:
            if py_coef.name not in ("x1", "x2"):
                continue
            st = next(c for c in stata_result["coefficients"] if c["name"] == py_coef.name)
            passed, msg = tolerance_close(
                py_coef.std_err, st["std_err"], name=f"std_err[{py_coef.name}]"
            )
            assert passed, msg


class TestVCE005PPMLHDFEPweightCluster:
    @pytest.fixture(scope="class")
    def data(self):
        return _generate_data()

    @pytest.fixture(scope="class")
    def python_result(self, data):
        return ppmlhdfe(
            data, y="y", x=["x1", "x2"], absorb=["fe1", "fe2"], aweight="w", vce="cluster", cluster="g"
        )

    @pytest.fixture(scope="class")
    def stata_result(self, data):
        return _run_stata(data, "cluster g")

    def test_coefficients_beta(self, python_result, stata_result):
        for py_coef in python_result.coefficients:
            if py_coef.name not in ("x1", "x2"):
                continue
            st = next(c for c in stata_result["coefficients"] if c["name"] == py_coef.name)
            passed, msg = tolerance_close(py_coef.beta, st["beta"], name=f"beta[{py_coef.name}]")
            assert passed, msg

    def test_coefficients_std_err(self, python_result, stata_result):
        for py_coef in python_result.coefficients:
            if py_coef.name not in ("x1", "x2"):
                continue
            st = next(c for c in stata_result["coefficients"] if c["name"] == py_coef.name)
            passed, msg = tolerance_close(
                py_coef.std_err, st["std_err"], name=f"std_err[{py_coef.name}]"
            )
            assert passed, msg
