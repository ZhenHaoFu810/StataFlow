"""
Golden test: p3_areg_real_panel - areg on real panel data (wagepan).

Tests that Python AbsorbingOLS matches Stata's areg on Wooldridge wagepan:
- Coefficient estimates
- Standard errors
- R-squared, Adjusted R-squared
- F-statistic, RMSE
- Degrees of freedom (including df_a)
"""

import re
import pytest
import pandas as pd
from pathlib import Path
from tests.golden.test_utils import (
    PROJECT_STATA_OUTPUT,
    tolerance_close,
)
from stataflow import AbsorbingOLS
from stataflow.stata_runner import StataRunner

PROJECT_ROOT = Path(__file__).parent.parent.parent
WAGEPAN_CSV = PROJECT_ROOT / "research" / "data" / "public" / "panel" / "wooldridge" / "wagepan.csv"


def _load_test_data() -> pd.DataFrame:
    """Load wagepan dataset."""
    return pd.read_csv(str(WAGEPAN_CSV))


def _parse_stata_log_with_precise_coefs(log_content: str) -> dict:
    """Parse Stata log with precise _b[] and _se[] outputs."""
    result = {}

    # Parse precise e() values
    e_patterns = {
        'nobs': r'E_N=([\d]+)',
        'df_model': r'E_DF_M=([\d]+)',
        'df_resid': r'E_DF_R=([\d]+)',
        'df_a': r'E_DF_A=([\d]+)',
        'r2': r'E_R2=([\d.]+)',
        'r2_adj': r'E_R2_A=([\d.]+)',
        'rmse': r'E_RMSE=([\d.]+)',
        'f_stat': r'E_F=([\d.]+)',
    }

    for key, pattern in e_patterns.items():
        match = re.search(pattern, log_content)
        if match:
            val_str = match.group(1)
            if val_str.startswith('.'):
                val_str = '0' + val_str
            result[key] = float(val_str)

    # Parse precise coefficients from _b[var] and _se[var] displays
    coefficients = []
    b_pattern = r'B_(\w+)=(-?[\d.]+)'
    se_pattern = r'SE_(\w+)=(-?[\d.]+)'

    b_matches = {k.lower(): v for k, v in re.findall(b_pattern, log_content)}
    se_matches = {k.lower(): v for k, v in re.findall(se_pattern, log_content)}

    for name in ['educ', 'exper', 'expersq', 'union', '_cons']:
        if name in b_matches and name in se_matches:
            beta = float(b_matches[name])
            std_err = float(se_matches[name])
            if name == 'educ' and abs(beta) < 1e-15:
                continue  # Skip omitted coefficient
            coefficients.append({
                'name': name,
                'beta': beta,
                'std_err': std_err,
            })

    result['coefficients'] = coefficients
    return result


def _run_stata_areg() -> dict:
    """Run Stata areg on wagepan."""
    do_template = f'''
clear all
set more off

// Read data
import delimited "{WAGEPAN_CSV}", clear

// Run areg
areg lwage educ exper expersq union, absorb(nr)

// Output precise e() values for parsing
display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_DF_R=" e(df_r)
display "E_DF_A=" e(df_a)
display "E_R2=" e(r2)
display "E_R2_A=" e(r2_a)
display "E_RMSE=" e(rmse)
display "E_F=" e(F)

// Output precise coefficients and standard errors
display "B_EDUC=" _b[educ]
display "B_EXPER=" _b[exper]
display "B_EXPERSQ=" _b[expersq]
display "B_UNION=" _b[union]
display "B__CONS=" _b[_cons]

display "SE_EDUC=" _se[educ]
display "SE_EXPER=" _se[exper]
display "SE_EXPERSQ=" _se[expersq]
display "SE_UNION=" _se[union]
display "SE__CONS=" _se[_cons]

display "Stata areg on wagepan completed successfully"
'''
    runner = StataRunner()
    result = runner.run_do_file(do_template, output_dir=str(PROJECT_STATA_OUTPUT))

    if result.exit_code != 0:
        raise RuntimeError(f"Stata failed: {result.error_message}")
    if not result.output_content:
        raise RuntimeError("Stata produced no output")

    return _parse_stata_log_with_precise_coefs(result.output_content)


class TestP3AregRealPanel:
    """Golden test for p3_areg_real_panel (wagepan)."""

    @pytest.fixture(scope="class")
    def test_data(self):
        """Load test data once per class."""
        return _load_test_data()

    @pytest.fixture(scope="class")
    def python_result(self, test_data):
        """Run Python AbsorbingOLS."""
        model = AbsorbingOLS(
            data=test_data,
            y="lwage",
            x=["educ", "exper", "expersq", "union"],
            absorb="nr",
            add_constant=True,
        )
        return model.fit(vce="ols")

    @pytest.fixture(scope="class")
    def stata_result(self):
        """Get Stata areg results."""
        return _run_stata_areg()

    def test_nobs(self, python_result, stata_result):
        """Compare sample size."""
        passed, msg = tolerance_close(
            python_result.sample.nobs, stata_result.get('nobs'), name="nobs"
        )
        assert passed, msg

    def test_df_model(self, python_result, stata_result):
        """Compare model degrees of freedom."""
        passed, msg = tolerance_close(
            python_result.fit.df_model, stata_result.get('df_model'), name="df_model"
        )
        assert passed, msg

    def test_df_a(self, python_result, stata_result):
        """Compare absorbed degrees of freedom."""
        passed, msg = tolerance_close(
            python_result.fit.df_a, stata_result.get('df_a'), name="df_a"
        )
        assert passed, msg

    def test_df_resid(self, python_result, stata_result):
        """Compare residual degrees of freedom."""
        passed, msg = tolerance_close(
            python_result.fit.df_resid, stata_result.get('df_resid'), name="df_resid"
        )
        assert passed, msg

    def test_r2(self, python_result, stata_result):
        """Compare R-squared."""
        passed, msg = tolerance_close(
            python_result.fit.r2, stata_result.get('r2'), name="r2"
        )
        assert passed, msg

    def test_r2_adj(self, python_result, stata_result):
        """Compare Adjusted R-squared."""
        passed, msg = tolerance_close(
            python_result.fit.r2_adj, stata_result.get('r2_adj'), name="r2_adj"
        )
        assert passed, msg

    def test_rmse(self, python_result, stata_result):
        """Compare RMSE."""
        passed, msg = tolerance_close(
            python_result.fit.rmse, stata_result.get('rmse'), name="rmse"
        )
        assert passed, msg

    def test_f_stat(self, python_result, stata_result):
        """Compare F-statistic."""
        passed, msg = tolerance_close(
            python_result.fit.f_stat, stata_result.get('f_stat'), name="f_stat"
        )
        assert passed, msg

    def test_coefficients_count(self, python_result, stata_result):
        """Compare number of coefficients."""
        assert len(python_result.coefficients) == len(stata_result.get('coefficients', []))

    def test_coefficients_names(self, python_result, stata_result):
        """Compare coefficient names."""
        py_names = [c.name for c in python_result.coefficients]
        st_names = [c['name'] for c in stata_result.get('coefficients', [])]
        assert py_names == st_names, f"Names differ: Python={py_names}, Stata={st_names}"

    def test_coefficients_beta(self, python_result, stata_result):
        """Compare coefficient estimates."""
        for py_coef, st_coef in zip(
            python_result.coefficients, stata_result.get('coefficients', [])
        ):
            passed, msg = tolerance_close(
                py_coef.beta, st_coef['beta'], name=f"beta[{py_coef.name}]"
            )
            assert passed, msg

    def test_coefficients_std_err(self, python_result, stata_result):
        """Compare standard errors."""
        for py_coef, st_coef in zip(
            python_result.coefficients, stata_result.get('coefficients', [])
        ):
            passed, msg = tolerance_close(
                py_coef.std_err, st_coef['std_err'], name=f"std_err[{py_coef.name}]"
            )
            assert passed, msg

    def test_absorb_var(self, python_result):
        """Verify absorb variable is recorded."""
        assert python_result.model.absorb_var == "nr"
