"""
Golden test: w3_poisson_real - Poisson on crime1 arrest count data.

Real-data validation using Wooldridge crime1 dataset.
"""

import re
import pytest
import pandas as pd
from pathlib import Path
from stataflow import Poisson
from stataflow.stata_runner import StataRunner
from tests.golden.test_utils import (
    PROJECT_STATA_OUTPUT,
    PROJECT_STATA_CASES,
    tolerance_close,
)


def _load_data():
    """Load crime1 dataset."""
    df = pd.read_csv(Path("research/data/public/count/crime1.csv"))
    return df


def _parse_stata_log(log_content: str) -> dict:
    """Parse Stata poisson log output."""
    result = {}

    e_patterns = {
        'nobs': r'E_N=([\d]+)',
        'df_model': r'E_DF_M=([\d]+)',
        'll': r'E_LL=(-?[\d.]+)',
        'deviance': r'E_DEV=(-?[\d.]+)',
        'chi2': r'E_CHI2=(-?[\d.]+)',
    }

    for key, pattern in e_patterns.items():
        match = re.search(pattern, log_content)
        if match:
            val_str = match.group(1)
            if val_str == '.' or val_str == '-.':
                continue
            if val_str.startswith('.'):
                val_str = '0' + val_str
            result[key] = float(val_str)

    coefficients = []
    b_matches = {k.lower(): v for k, v in re.findall(r'B_(\w+)=(-?[\d.]+)', log_content)}
    se_matches = {k.lower(): v for k, v in re.findall(r'SE_(\w+)=(-?[\d.]+)', log_content)}

    for name in ['pcnv', 'avgsen', 'tottime', 'ptime86', 'qemp86', 'inc86', 'black', 'hispan', 'born60', '_cons']:
        if name in b_matches and name in se_matches:
            coefficients.append({
                'name': name,
                'beta': float(b_matches[name]),
                'std_err': float(se_matches[name]),
            })

    result['coefficients'] = coefficients
    return result


def _run_stata_poisson(data: pd.DataFrame) -> dict:
    """Run Stata poisson for crime1 test."""
    dta_file = PROJECT_STATA_CASES / "w3_poisson_real_data.dta"
    data.to_stata(str(dta_file), write_index=False)

    do_template = f'''
clear all
set more off

use "{dta_file}", clear

* Run poisson for LR chi2 and ll
poisson narr86 pcnv avgsen tottime ptime86 qemp86 inc86 black hispan born60

display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_LL=" e(ll)
display "E_CHI2=" e(chi2)

display "B_pcnv=" _b[pcnv]
display "SE_pcnv=" _se[pcnv]
display "B_avgsen=" _b[avgsen]
display "SE_avgsen=" _se[avgsen]
display "B_tottime=" _b[tottime]
display "SE_tottime=" _se[tottime]
display "B_ptime86=" _b[ptime86]
display "SE_ptime86=" _se[ptime86]
display "B_qemp86=" _b[qemp86]
display "SE_qemp86=" _se[qemp86]
display "B_inc86=" _b[inc86]
display "SE_inc86=" _se[inc86]
display "B_black=" _b[black]
display "SE_black=" _se[black]
display "B_hispan=" _b[hispan]
display "SE_hispan=" _se[hispan]
display "B_born60=" _b[born60]
display "SE_born60=" _se[born60]
display "B__cons=" _b[_cons]
display "SE__cons=" _se[_cons]

* Run glm to get deviance (poisson does not store e(deviance))
glm narr86 pcnv avgsen tottime ptime86 qemp86 inc86 black hispan born60, family(poisson) link(log)
display "E_DEV=" e(deviance)

display "Stata poisson real completed successfully"
'''
    runner = StataRunner()
    result = runner.run_do_file(do_template, output_dir=str(PROJECT_STATA_OUTPUT))

    if result.exit_code != 0:
        raise RuntimeError(f"Stata failed: {result.error_message}")
    if not result.output_content:
        raise RuntimeError("Stata produced no output")

    return _parse_stata_log(result.output_content)


class TestW3PoissonReal:
    """Golden test for w3_poisson_real."""

    @pytest.fixture(scope="class")
    def test_data(self):
        return _load_data()

    @pytest.fixture(scope="class")
    def python_result(self, test_data):
        model = Poisson(
            data=test_data,
            y="narr86",
            x=["pcnv", "avgsen", "tottime", "ptime86", "qemp86", "inc86", "black", "hispan", "born60"],
            add_constant=True,
        )
        return model.fit(vce="ols")

    @pytest.fixture(scope="class")
    def stata_result(self, test_data):
        return _run_stata_poisson(test_data)

    def test_nobs(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result.sample.nobs, stata_result.get("nobs"), name="nobs"
        )
        assert passed, msg

    def test_df_model(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result.fit.df_model, stata_result.get("df_model"), name="df_model"
        )
        assert passed, msg

    def test_ll(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result.fit.ll, stata_result.get("ll"), name="ll", rtol=1e-6, atol=1e-6
        )
        assert passed, msg

    def test_deviance(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result.fit.deviance, stata_result.get("deviance"), name="deviance", rtol=1e-6, atol=1e-6
        )
        assert passed, msg

    def test_chi2(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result.fit.f_stat, stata_result.get("chi2"), name="chi2", rtol=1e-6, atol=1e-6
        )
        assert passed, msg

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
