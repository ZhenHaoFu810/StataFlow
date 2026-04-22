"""
Golden test: w2_ivregress_real_card - IV2SLS on Card returns-to-schooling data.

Tests that Python IV2SLS matches Stata's ivregress 2sls on real data:
- Coefficient estimates
- Standard errors
- R-squared, Adjusted R-squared
- F-statistic, RMSE
- Degrees of freedom
"""

import re
import pytest
import pandas as pd
from pathlib import Path
from tests.golden.test_utils import (
    PROJECT_STATA_OUTPUT,
    tolerance_close,
)
from stataflow import IV2SLS
from stataflow.stata_runner import StataRunner

PROJECT_ROOT = Path(__file__).parent.parent.parent
CARD_CSV = PROJECT_ROOT / "research" / "data" / "public" / "iv" / "card.csv"


def _load_test_data() -> pd.DataFrame:
    """Load Card dataset."""
    return pd.read_csv(str(CARD_CSV))


def _parse_stata_log_with_precise_coefs(log_content: str) -> dict:
    """Parse Stata log with precise _b[] and _se[] outputs."""
    result = {}

    e_patterns = {
        'nobs': r'E_N=([\d]+)',
        'df_model': r'E_DF_M=([\d]+)',
        'df_resid': r'E_DF_R=([\d]+)',
        'r2': r'E_R2=([\d.]+)',
        'r2_adj': r'E_R2_A=([\d.]+)',
        'rmse': r'E_RMSE=([\d.]+)',
        'f_stat': r'E_F=([\d.]+)',
    }

    for key, pattern in e_patterns.items():
        match = re.search(pattern, log_content)
        if match:
            val_str = match.group(1)
            if val_str == '.' or val_str == '-.':
                continue  # Stata missing value
            if val_str.startswith('.'):
                val_str = '0' + val_str
            result[key] = float(val_str)

    coefficients = []
    b_pattern = r'B_(\w+)=(-?[\d.]+)'
    se_pattern = r'SE_(\w+)=(-?[\d.]+)'

    b_matches = {k.lower(): v for k, v in re.findall(b_pattern, log_content)}
    se_matches = {k.lower(): v for k, v in re.findall(se_pattern, log_content)}

    for name in ['educ', 'exper', 'expersq', 'black', 'south', 'smsa', 'smsa66',
                 'reg661', 'reg662', 'reg663', 'reg664', 'reg665', 'reg666', 'reg667', 'reg668', '_cons']:
        if name in b_matches and name in se_matches:
            beta = float(b_matches[name])
            if name != '_cons' and abs(beta) < 1e-15:
                continue  # Skip omitted coefficient
            coefficients.append({
                'name': name,
                'beta': beta,
                'std_err': float(se_matches[name]),
            })

    result['coefficients'] = coefficients
    return result


def _run_stata_ivregress() -> dict:
    """Run Stata ivregress 2sls on Card data."""
    do_template = f'''
clear all
set more off

// Read data
import delimited "{CARD_CSV}", clear

// Run ivregress 2sls
ivregress 2sls lwage exper expersq black south smsa reg661-reg668 smsa66 (educ = nearc4)

// Output precise e() values for parsing
display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_DF_R=" e(df_r)
display "E_R2=" e(r2)
display "E_R2_A=" e(r2_a)
display "E_RMSE=" e(rmse)
display "E_F=" e(F)

// Output precise coefficients and standard errors
display "B_EDUC=" _b[educ]
display "SE_EDUC=" _se[educ]
display "B_EXPER=" _b[exper]
display "SE_EXPER=" _se[exper]
display "B_EXPERSQ=" _b[expersq]
display "SE_EXPERSQ=" _se[expersq]
display "B_BLACK=" _b[black]
display "SE_BLACK=" _se[black]
display "B_SOUTH=" _b[south]
display "SE_SOUTH=" _se[south]
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
display "B__CONS=" _b[_cons]
display "SE__CONS=" _se[_cons]

display "Stata ivregress 2sls on Card completed successfully"
'''
    runner = StataRunner()
    result = runner.run_do_file(do_template, output_dir=str(PROJECT_STATA_OUTPUT))

    if result.exit_code != 0:
        raise RuntimeError(f"Stata failed: {result.error_message}")
    if not result.output_content:
        raise RuntimeError("Stata produced no output")

    return _parse_stata_log_with_precise_coefs(result.output_content)


class TestW2IvregressRealCard:
    """Golden test for w2_ivregress_real_card (Card data)."""

    @pytest.fixture(scope="class")
    def test_data(self):
        return _load_test_data()

    @pytest.fixture(scope="class")
    def python_result(self, test_data):
        x_exog = ["exper", "expersq", "black", "south", "smsa", "smsa66",
                  "reg661", "reg662", "reg663", "reg664", "reg665", "reg666", "reg667", "reg668"]
        model = IV2SLS(
            data=test_data,
            y="lwage",
            x_exog=x_exog,
            x_endog=["educ"],
            instruments=["nearc4"],
            add_constant=True,
        )
        return model.fit(vce="ols")

    @pytest.fixture(scope="class")
    def stata_result(self):
        return _run_stata_ivregress()

    def test_nobs(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result.sample.nobs, stata_result.get('nobs'), name="nobs"
        )
        assert passed, msg

    def test_df_model(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result.fit.df_model, stata_result.get('df_model'), name="df_model"
        )
        assert passed, msg

    def test_df_resid(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result.fit.df_resid, stata_result.get('df_resid'), name="df_resid"
        )
        assert passed, msg

    def test_r2(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result.fit.r2, stata_result.get('r2'), name="r2"
        )
        assert passed, msg

    def test_r2_adj(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result.fit.r2_adj, stata_result.get('r2_adj'), name="r2_adj"
        )
        assert passed, msg

    def test_rmse(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result.fit.rmse, stata_result.get('rmse'), name="rmse"
        )
        assert passed, msg

    def test_f_stat(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result.fit.f_stat, stata_result.get('f_stat'), name="f_stat"
        )
        assert passed, msg

    def test_coefficients_count(self, python_result, stata_result):
        assert len(python_result.coefficients) == len(stata_result.get('coefficients', []))

    def test_coefficients_names(self, python_result, stata_result):
        py_names = [c.name for c in python_result.coefficients]
        st_names = [c['name'] for c in stata_result.get('coefficients', [])]
        assert py_names == st_names, f"Names differ: Python={py_names}, Stata={st_names}"

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
