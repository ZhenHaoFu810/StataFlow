"""
Golden test: w3_probit_basic - Basic probit regression test.

Tests basic probit functionality with constant term, verifying:
- Coefficient estimates
- Standard errors
- Log-likelihood (ll)
- Pseudo R-squared
- LR chi2
- Degrees of freedom
"""

import re
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from statapy import Probit
from statapy.stata_runner import StataRunner
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

    e_patterns = {
        'nobs': r'E_N=([\d]+)',
        'df_model': r'E_DF_M=([\d]+)',
        'll': r'E_LL=(-?[\d.]+)',
        'pseudo_r2': r'E_R2_P=(-?[\d.]+)',
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
    """Run Stata probit for basic test."""
    dta_file = PROJECT_STATA_CASES / "w3_probit_basic_data.dta"
    data.to_stata(str(dta_file), write_index=False)

    do_template = f'''
clear all
set more off

use "{dta_file}", clear

probit y x1 x2

display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_LL=" e(ll)
display "E_R2_P=" e(r2_p)
display "E_CHI2=" e(chi2)

display "B_x1=" _b[x1]
display "SE_x1=" _se[x1]
display "B_x2=" _b[x2]
display "SE_x2=" _se[x2]
display "B__cons=" _b[_cons]
display "SE__cons=" _se[_cons]

display "Stata probit completed successfully"
'''
    runner = StataRunner()
    result = runner.run_do_file(do_template, output_dir=str(PROJECT_STATA_OUTPUT))

    if result.exit_code != 0:
        raise RuntimeError(f"Stata failed: {result.error_message}")
    if not result.output_content:
        raise RuntimeError("Stata produced no output")

    return _parse_stata_log(result.output_content)


class TestW3ProbitBasic:
    """Golden test for w3_probit_basic."""

    @pytest.fixture(scope="class")
    def test_data(self):
        return _generate_test_data()

    @pytest.fixture(scope="class")
    def python_result(self, test_data):
        model = Probit(data=test_data, y="y", x=["x1", "x2"], add_constant=True)
        return model.fit(vce="ols")

    @pytest.fixture(scope="class")
    def stata_result(self, test_data):
        return _run_stata_probit(test_data)

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

    def test_pseudo_r2(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result.fit.pseudo_r2, stata_result.get("pseudo_r2"), name="pseudo_r2", rtol=1e-6, atol=1e-6
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

    def test_p_values_and_ci_use_z_distribution(self, python_result, stata_result):
        from scipy.stats import norm
        for py_coef, st_coef in zip(
            python_result.coefficients, stata_result.get("coefficients", [])
        ):
            z_stat = st_coef["beta"] / st_coef["std_err"]
            expected_p = 2 * (1 - norm.cdf(abs(z_stat)))
            expected_ci_low = st_coef["beta"] - norm.ppf(0.975) * st_coef["std_err"]
            expected_ci_high = st_coef["beta"] + norm.ppf(0.975) * st_coef["std_err"]
            passed, msg = tolerance_close(
                py_coef.p_value, expected_p, name=f"p_value[{py_coef.name}]"
            )
            assert passed, msg
            passed, msg = tolerance_close(
                py_coef.ci_low, expected_ci_low, name=f"ci_low[{py_coef.name}]"
            )
            assert passed, msg
            passed, msg = tolerance_close(
                py_coef.ci_high, expected_ci_high, name=f"ci_high[{py_coef.name}]"
            )
            assert passed, msg
