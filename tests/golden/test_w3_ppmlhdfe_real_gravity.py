"""
Golden test: w3_ppmlhdfe_real_gravity - PPMLHDFE on CA county murders panel.

Real-data validation using Wooldridge countymurders dataset (California subset).
County fixed effects + year fixed effects.
"""

import re
import pytest
import pandas as pd
from pathlib import Path
from stataflow import PPMLHDFE
from stataflow.stata_runner import StataRunner
from tests.golden.test_utils import (
    PROJECT_STATA_OUTPUT,
    PROJECT_STATA_CASES,
    tolerance_close,
)


def _load_data():
    """Load California subset of countymurders dataset."""
    df = pd.read_csv(Path("research/data/public/gravity/countymurders_ca.csv"))
    return df


def _parse_stata_log(log_content: str) -> dict:
    """Parse Stata ppmlhdfe log output."""
    result = {}

    e_patterns = {
        'nobs': r'E_N=([\d]+)',
        'df_model': r'E_DF_M=([\d]+)',
        'df_a': r'E_DF_A=([\d]+)',
        'll': r'E_LL=(-?[\d.]+)',
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

    for name in ['density', 'perc1019', 'perc2029', 'percblack', 'percmale', 'rpcincmaint', 'rpcpersinc', 'rpcunemins', '_cons']:
        if name in b_matches and name in se_matches:
            coefficients.append({
                'name': name,
                'beta': float(b_matches[name]),
                'std_err': float(se_matches[name]),
            })

    result['coefficients'] = coefficients
    return result


def _run_stata_ppmlhdfe(data: pd.DataFrame) -> dict:
    """Run Stata ppmlhdfe for CA county murders test."""
    dta_file = PROJECT_STATA_CASES / "w3_ppmlhdfe_real_gravity_data.dta"
    data.to_stata(str(dta_file), write_index=False)

    do_template = f'''
clear all
set more off

use "{dta_file}", clear

ppmlhdfe murders density perc1019 perc2029 percblack percmale rpcincmaint rpcpersinc rpcunemins, absorb(countyid year) vce(ols)

display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_DF_A=" e(df_a)
display "E_LL=" e(ll)

display "B_density=" _b[density]
display "SE_density=" _se[density]
display "B_perc1019=" _b[perc1019]
display "SE_perc1019=" _se[perc1019]
display "B_perc2029=" _b[perc2029]
display "SE_perc2029=" _se[perc2029]
display "B_percblack=" _b[percblack]
display "SE_percblack=" _se[percblack]
display "B_percmale=" _b[percmale]
display "SE_percmale=" _se[percmale]
display "B_rpcincmaint=" _b[rpcincmaint]
display "SE_rpcincmaint=" _se[rpcincmaint]
display "B_rpcpersinc=" _b[rpcpersinc]
display "SE_rpcpersinc=" _se[rpcpersinc]
display "B_rpcunemins=" _b[rpcunemins]
display "SE_rpcunemins=" _se[rpcunemins]
display "B__cons=" _b[_cons]
display "SE__cons=" _se[_cons]

display "Stata ppmlhdfe real gravity completed successfully"
'''
    runner = StataRunner()
    result = runner.run_do_file(do_template, output_dir=str(PROJECT_STATA_OUTPUT))

    if result.exit_code != 0:
        raise RuntimeError(f"Stata failed: {result.error_message}")
    if not result.output_content:
        raise RuntimeError("Stata produced no output")

    return _parse_stata_log(result.output_content)


class TestW3PpmlhdfeRealGravity:
    """Golden test for w3_ppmlhdfe_real_gravity."""

    @pytest.fixture(scope="class")
    def test_data(self):
        return _load_data()

    @pytest.fixture(scope="class")
    def python_result(self, test_data):
        model = PPMLHDFE(
            data=test_data,
            y="murders",
            x=["density", "perc1019", "perc2029", "percblack", "percmale", "rpcincmaint", "rpcpersinc", "rpcunemins"],
            absorb=["countyid", "year"],
            add_constant=True,
        )
        return model.fit(vce="robust")

    @pytest.fixture(scope="class")
    def stata_result(self, test_data):
        return _run_stata_ppmlhdfe(test_data)

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

    def test_df_a(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result.fit.df_a, stata_result.get("df_a"), name="df_a"
        )
        assert passed, msg

    def test_ll(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result.fit.ll, stata_result.get("ll"), name="ll", rtol=1e-6, atol=1e-6
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
                py_coef.p_value, expected_p, name=f"p_value[{py_coef.name}]", rtol=1e-4, atol=1e-4
            )
            assert passed, msg
            passed, msg = tolerance_close(
                py_coef.ci_low, expected_ci_low, name=f"ci_low[{py_coef.name}]", rtol=1e-5, atol=1e-6
            )
            assert passed, msg
            passed, msg = tolerance_close(
                py_coef.ci_high, expected_ci_high, name=f"ci_high[{py_coef.name}]", rtol=1e-5, atol=1e-6
            )
            assert passed, msg

    def test_absorb_vars(self, python_result):
        assert python_result.model.absorb_vars == ["countyid", "year"]
