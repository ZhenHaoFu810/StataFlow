"""
C1.1 CAPM/FF3 real-data golden test.

Fama-French 3-factor: SMB ~ Mkt-RF + HML
Tests OLS, robust (HC1), and cluster (by year) VCE on real financial data.
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from tests.golden.test_utils import (
    PROJECT_STATA_OUTPUT, PROJECT_STATA_CASES, StataRunner,
    tolerance_close, parse_stata_log_with_precise_coefs,
)
from stataflow import OLS

PROJECT_ROOT = Path(__file__).parent.parent.parent
FF3_CLEAN = PROJECT_ROOT / "research" / "experiments" / "c1_1_capm_ff3" / "ff3_clean.csv"


def _load_data():
    df = pd.read_csv(FF3_CLEAN)
    return df.dropna(subset=["Mkt-RF", "SMB", "HML", "year"])


def _run_stata(data: pd.DataFrame, vce_spec: str) -> dict:
    dta_file = PROJECT_STATA_CASES / f"c1_1_capm_ff3_{vce_spec}_data.dta"
    data.to_stata(str(dta_file), write_index=False)

    if vce_spec == "ols":
        vce_line = ""
    elif vce_spec == "robust":
        vce_line = ", vce(robust)"
    else:
        vce_line = ", vce(cluster year)"

    do_template = f'''
clear all
set more off
use "{dta_file}", clear
regress SMB Mkt-RF HML{vce_line}
display "E_N=" e(N)
display "B_MktRF=" _b["Mkt-RF"]
display "B_HML=" _b[HML]
display "B__CONS=" _b[_cons]
display "SE_MktRF=" _se["Mkt-RF"]
display "SE_HML=" _se[HML]
display "SE__CONS=" _se[_cons]
display "C1_1_CAPM_{vce_spec.upper()} completed"
'''
    runner = StataRunner()
    result = runner.run_do_file(do_template, output_dir=str(PROJECT_STATA_OUTPUT))
    if result.exit_code != 0:
        raise RuntimeError(f"Stata failed ({vce_spec}): {result.error_message}")
    return parse_stata_log_with_precise_coefs(
        result.output_content, coef_names=["Mkt-RF", "HML", "_cons"]
    )


class TestC11CAPMOLS:
    @pytest.fixture(scope="class")
    def data(self):
        return _load_data()

    @pytest.fixture(scope="class")
    def python(self, data):
        m = OLS(data=data, y="SMB", x=["Mkt-RF", "HML"], add_constant=True)
        return m.fit(vce="ols")

    @pytest.fixture(scope="class")
    def stata(self, data):
        return _run_stata(data, "ols")

    def test_beta(self, python, stata):
        for pc, sc in zip(python.coefficients, stata["coefficients"]):
            passed, msg = tolerance_close(pc.beta, sc["beta"], name=f"beta[{pc.name}]")
            assert passed, msg

    def test_std_err(self, python, stata):
        for pc, sc in zip(python.coefficients, stata["coefficients"]):
            passed, msg = tolerance_close(pc.std_err, sc["std_err"], name=f"se[{pc.name}]")
            assert passed, msg


class TestC11CAPMRobust:
    @pytest.fixture(scope="class")
    def data(self):
        return _load_data()

    @pytest.fixture(scope="class")
    def python(self, data):
        m = OLS(data=data, y="SMB", x=["Mkt-RF", "HML"], add_constant=True)
        return m.fit(vce="robust")

    @pytest.fixture(scope="class")
    def stata(self, data):
        return _run_stata(data, "robust")

    def test_beta(self, python, stata):
        for pc, sc in zip(python.coefficients, stata["coefficients"]):
            passed, msg = tolerance_close(pc.beta, sc["beta"], name=f"beta[{pc.name}]")
            assert passed, msg

    def test_std_err(self, python, stata):
        for pc, sc in zip(python.coefficients, stata["coefficients"]):
            passed, msg = tolerance_close(pc.std_err, sc["std_err"], name=f"se[{pc.name}]")
            assert passed, msg


class TestC11CAPMCluster:
    @pytest.fixture(scope="class")
    def data(self):
        return _load_data()

    @pytest.fixture(scope="class")
    def python(self, data):
        m = OLS(data=data, y="SMB", x=["Mkt-RF", "HML"], add_constant=True)
        return m.fit(vce="cluster", cluster="year")

    @pytest.fixture(scope="class")
    def stata(self, data):
        return _run_stata(data, "cluster")

    def test_beta(self, python, stata):
        for pc, sc in zip(python.coefficients, stata["coefficients"]):
            passed, msg = tolerance_close(pc.beta, sc["beta"], name=f"beta[{pc.name}]")
            assert passed, msg

    def test_std_err(self, python, stata):
        for pc, sc in zip(python.coefficients, stata["coefficients"]):
            passed, msg = tolerance_close(pc.std_err, sc["std_err"], name=f"se[{pc.name}]")
            assert passed, msg
