"""
Golden test: w10_card_liml - LIML on Card returns-to-schooling data.

Tests that Python IVAbsorbingOLS with estimator='liml' matches Stata's
ivreghdfe liml on real data.
"""

import re
import pytest
import pandas as pd
from pathlib import Path
from tests.golden.test_utils import (
    PROJECT_STATA_OUTPUT,
    tolerance_close,
)
from stataflow.compat.stata import ivreghdfe

PROJECT_ROOT = Path(__file__).parent.parent.parent
CARD_CSV = PROJECT_ROOT / "research" / "data" / "public" / "iv" / "card.csv"


def _load_test_data() -> pd.DataFrame:
    """Load Card dataset."""
    return pd.read_csv(str(CARD_CSV))


def _parse_stata_log(log_content: str) -> dict:
    """Parse Stata log output."""
    result = {}

    e_patterns = {
        'nobs': r'E_N=([\d]+)',
        'df_model': r'E_DF_M=([\d]+)',
        'r2': r'E_R2=([\d.]+)',
        'rmse': r'E_RMSE=([\d.]+)',
        'f_stat': r'E_F=([\d.]+)',
        'kclass': r'E_K=([\d.]+)',
    }

    for key, pattern in e_patterns.items():
        match = re.search(pattern, log_content)
        if match:
            val_str = match.group(1)
            if val_str.startswith('.'):
                val_str = '0' + val_str
            result[key] = float(val_str)

    coefficients = []
    b_pattern = r'B_(\w+)=(-?[\d.]+)'
    se_pattern = r'SE_(\w+)=(-?[\d.]+)'

    b_matches = {k.lower(): v for k, v in re.findall(b_pattern, log_content)}
    se_matches = {k.lower(): v for k, v in re.findall(se_pattern, log_content)}

    for name in ['educ', 'exper', 'expersq', 'black', 'smsa', 'smsa66',
                 'reg661', 'reg662', 'reg663', 'reg664', 'reg665', 'reg666', 'reg667', 'reg668']:
        if name in b_matches and name in se_matches:
            coefficients.append({
                'name': name,
                'beta': float(b_matches[name]),
                'std_err': float(se_matches[name]),
            })

    result['coefficients'] = coefficients
    return result


def _run_stata() -> dict:
    """Run Stata ivreghdfe with liml on Card data."""
    do_template = f'''
clear all
set more off

import delimited "{CARD_CSV}", clear

ivreghdfe lwage exper expersq black smsa reg661-reg668 smsa66 (educ = nearc4), absorb(south) keepsingletons liml

display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_R2=" e(r2)
display "E_RMSE=" e(rmse)
display "E_F=" e(F)
display "E_K=" e(kclass)

display "B_EDUC=" _b[educ]
display "SE_EDUC=" _se[educ]
display "B_EXPER=" _b[exper]
display "SE_EXPER=" _se[exper]
display "B_EXPERSQ=" _b[expersq]
display "SE_EXPERSQ=" _se[expersq]
display "B_BLACK=" _b[black]
display "SE_BLACK=" _se[black]
display "B_SMSA=" _b[smsa]
display "SE_SMSA=" _se[smsa]
display "B_SMSA66=" _b[smsa66]
display "SE_SMSA66=" _se[smsa66]
display "B_REG661=" _b[reg661]
display "SE_REG661=" _se[reg661]
display "B_REG662=" _b[reg662]
display "SE_REG662=" _se[reg662]
display "B_REG663=" _b[reg663]
display "SE_REG663=" _se[reg663]
display "B_REG664=" _b[reg664]
display "SE_REG664=" _se[reg664]
display "B_REG665=" _b[reg665]
display "SE_REG665=" _se[reg665]
display "B_REG666=" _b[reg666]
display "SE_REG666=" _se[reg666]
display "B_REG667=" _b[reg667]
display "SE_REG667=" _se[reg667]
display "B_REG668=" _b[reg668]
display "SE_REG668=" _se[reg668]
'''
    from stataflow.stata_runner import StataRunner
    runner = StataRunner()
    result = runner.run_do_file(do_template, output_dir=str(PROJECT_STATA_OUTPUT))

    if result.exit_code != 0:
        raise RuntimeError(f"Stata failed: {result.error_message}")
    if not result.output_content:
        raise RuntimeError("Stata produced no output")

    return _parse_stata_log(result.output_content)


def _run_python(data: pd.DataFrame):
    """Run Python ivreghdfe with liml on Card data."""
    x_exog = ["exper", "expersq", "black", "smsa", "smsa66",
              "reg661", "reg662", "reg663", "reg664", "reg665", "reg666", "reg667", "reg668"]
    return ivreghdfe(
        data,
        y="lwage",
        x_exog=x_exog,
        x_endog=["educ"],
        instruments=["nearc4"],
        absorb="south",
        estimator="liml",
    )


class TestW10CardLiml:
    """Golden test for w10_card_liml."""

    @pytest.fixture(scope="class")
    def test_data(self):
        return _load_test_data()

    @pytest.fixture(scope="class")
    def python_result(self, test_data):
        return _run_python(test_data)

    @pytest.fixture(scope="class")
    def stata_result(self):
        return _run_stata()

    def test_nobs(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result.sample.nobs, stata_result.get("nobs"), name="nobs"
        )
        assert passed, msg

    def test_coefficients_beta(self, python_result, stata_result):
        py_coefs = {c.name: c.beta for c in python_result.coefficients}
        st_coefs = {c['name']: c['beta'] for c in stata_result.get('coefficients', [])}
        assert set(py_coefs.keys()) == set(st_coefs.keys())
        for name in py_coefs:
            passed, msg = tolerance_close(py_coefs[name], st_coefs[name], name=f"beta_{name}")
            assert passed, msg

    def test_coefficients_std_err(self, python_result, stata_result):
        py_coefs = {c.name: c.std_err for c in python_result.coefficients}
        st_coefs = {c['name']: c['std_err'] for c in stata_result.get('coefficients', [])}
        for name in py_coefs:
            passed, msg = tolerance_close(py_coefs[name], st_coefs[name], name=f"se_{name}")
            assert passed, msg

    def test_kclass(self, python_result, stata_result):
        py_k = getattr(python_result, 'liml_k', None)
        st_k = stata_result.get("kclass")
        assert py_k is not None
        assert st_k is not None
        passed, msg = tolerance_close(py_k, st_k, name="kclass")
        assert passed, msg
