"""
Golden test: w9_di_pretrends_basic - did_imputation with pretrends.

Tests did_imputation with pretrends(3) on synthetic staggered adoption data,
verifying event time coefficients (tauh), pretrends coefficients (preh),
and standard errors align with Stata 17.
"""

import re
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from stataflow import DIDImputation
from stataflow.stata_runner import StataRunner
from tests.golden.test_utils import (
    PROJECT_STATA_OUTPUT,
    PROJECT_STATA_CASES,
    tolerance_close,
)


def _generate_test_data() -> pd.DataFrame:
    """Generate staggered adoption panel matching Stata synthetic data."""
    np.random.seed(12345)
    n_units = 500
    n_periods = 11

    # Unit identifiers
    ids = np.repeat(np.arange(1, n_units + 1), n_periods)
    # Time periods: 2001-2011
    years = np.tile(np.arange(2001, 2001 + n_periods), n_units)

    # Cohort assignment per unit
    unit_cohorts = np.zeros(n_units, dtype=int)
    unit_cohorts[:150] = 2004
    unit_cohorts[150:300] = 2006
    unit_cohorts[300:] = 2007
    first_treat = np.repeat(unit_cohorts, n_periods)

    # Treatment indicator
    treat = ((years >= first_treat) & (first_treat > 0)).astype(int)

    # Fixed effects and outcome
    fe_i = np.repeat(np.random.normal(0, 1, n_units), n_periods)
    unique_years = np.unique(years)
    year_fe_map = {y: np.random.normal(0, 1) for y in unique_years}
    fe_t = np.array([year_fe_map[y] for y in years])

    y = fe_i + fe_t + 1.5 * treat + np.random.normal(0, 1, len(ids))

    return pd.DataFrame({
        "id": ids,
        "year": years,
        "first_treat": first_treat,
        "treat": treat,
        "y": y,
    })


def _parse_stata_log(log_content: str) -> dict:
    """Parse Stata did_imputation log output with pretrends."""
    result = {}

    # Extract e(N)
    n_match = re.search(r'E_N=([\d.]+)', log_content)
    if n_match:
        result['nobs'] = float(n_match.group(1))

    # Parse B_tauX= and SE_tauX= display lines
    coefficients = []
    b_matches = re.findall(r'B_(tau\d+)=(-?[\d.]+)', log_content)
    se_matches = dict(re.findall(r'SE_(tau\d+)=(-?[\d.]+)', log_content))

    for name, beta_str in b_matches:
        beta = float(beta_str)
        se = float(se_matches.get(name, '0')) if name in se_matches else 0.0
        coefficients.append({
            'name': name,
            'beta': beta,
            'std_err': se,
        })

    # Parse pretrends coefficients (pre1, pre2, pre3)
    pre_b_matches = re.findall(r'B_(pre\d+)=(-?[\d.]+)', log_content)
    pre_se_matches = dict(re.findall(r'SE_(pre\d+)=(-?[\d.]+)', log_content))

    for name, beta_str in pre_b_matches:
        beta = float(beta_str)
        se = float(pre_se_matches.get(name, '0')) if name in pre_se_matches else 0.0
        coefficients.append({
            'name': name,
            'beta': beta,
            'std_err': se,
        })

    # Parse joint F test for pretrends
    f_match = re.search(r'PRE_F=([\d.]+)', log_content)
    p_match = re.search(r'PRE_P=([\d.]+)', log_content)
    if f_match and p_match:
        f_val = f_match.group(1)
        p_val = p_match.group(1)
        # Handle Stata missing values
        if f_val != '.':
            result['pretrend_f'] = float(f_val)
        if p_val != '.':
            result['pretrend_p'] = float(p_val)

    result['coefficients'] = coefficients
    return result


def _run_stata_did_imputation(data: pd.DataFrame) -> dict:
    """Run Stata did_imputation with pretrends."""
    dta_file = PROJECT_STATA_CASES / "w9_di_pretrends_basic_data.dta"
    data.to_stata(str(dta_file), write_index=False)

    do_template = f'''
clear all
set more off

use "{dta_file}", clear

did_imputation y id year first_treat, pretrends(3) allhorizons cluster(id) autosample

estimates store did_imp

display "E_N=" e(N)
display "E_N_CLUST=" e(N_clust)

matrix list e(b)

* Get coefficient names from e(b)
local names : colfullnames e(b)
foreach name of local names {{
    display "B_`name'=" _b["`name'"]
    display "SE_`name'=" _se["`name'"]
}}

* Test joint significance of pretrends
test pre1 pre2 pre3
display "PRE_F=" r(F)
display "PRE_P=" r(p)

display "DID_IMP_OK"
'''
    runner = StataRunner()
    result = runner.run_do_file(do_template, output_dir=str(PROJECT_STATA_OUTPUT))

    if result.exit_code != 0:
        raise RuntimeError(f"Stata failed: {result.error_message}")
    if not result.output_content:
        raise RuntimeError("Stata produced no output")

    return _parse_stata_log(result.output_content)


class TestW9DiPretrendsBasic:
    """Golden test for w9_di_pretrends_basic."""

    @pytest.fixture(scope="class")
    def test_data(self):
        return _generate_test_data()

    @pytest.fixture(scope="class")
    def python_result(self, test_data):
        model = DIDImputation(
            data=test_data,
            y="y",
            id="id",
            time="year",
            first_treat="first_treat",
        )
        return model.fit(
            cluster="id",
            allhorizons=True,
            autosample=True,
            pretrends=3,
        )

    @pytest.fixture(scope="class")
    def stata_result(self, test_data):
        return _run_stata_did_imputation(test_data)

    def test_nobs(self, python_result, stata_result):
        passed, msg = tolerance_close(
            python_result.sample.nobs, stata_result.get("nobs"), name="nobs"
        )
        assert passed, msg

    def test_coefficients_count(self, python_result, stata_result):
        py_names = [c.name for c in python_result.coefficients]
        st_names = [c["name"] for c in stata_result.get("coefficients", [])]
        assert py_names == st_names, f"Names differ: Python={py_names}, Stata={st_names}"

    def test_coefficients_beta(self, python_result, stata_result):
        for py_coef, st_coef in zip(
            python_result.coefficients, stata_result.get("coefficients", [])
        ):
            passed, msg = tolerance_close(
                py_coef.beta, st_coef["beta"], name=f"beta[{py_coef.name}]",
                rtol=1e-5, atol=1e-7,
            )
            assert passed, msg

    def test_coefficients_std_err(self, python_result, stata_result):
        for py_coef, st_coef in zip(
            python_result.coefficients, stata_result.get("coefficients", [])
        ):
            # Skip omitted coefficients
            if st_coef.get("std_err", 0) == 0:
                continue
            # Use looser tolerance for pretrends SEs (LSDV vs iterative demeaning)
            if py_coef.name.startswith("pre"):
                rtol, atol = 3e-2, 1e-3
            else:
                rtol, atol = 1e-3, 1e-6
            passed, msg = tolerance_close(
                py_coef.std_err, st_coef["std_err"], name=f"std_err[{py_coef.name}]",
                rtol=rtol, atol=atol,
            )
            assert passed, msg

    def test_pretrend_joint_pvalue(self, python_result, stata_result):
        """Compare joint test p-value for pretrends.

        Stata uses chi2 test; Python uses F test. They are asymptotically
        equivalent but differ in finite samples. We compare p-values.
        """
        st_p = stata_result.get('pretrend_p')
        if st_p is None:
            pytest.skip("Stata pretrend p-value not available")

        # Extract p-value from Python diagnostics warnings
        py_warnings = []
        if python_result.diagnostics and python_result.diagnostics.warnings:
            py_warnings = python_result.diagnostics.warnings

        py_p = None
        for w in py_warnings:
            if "Pretrend joint F-test" in w:
                # Parse "Pretrend joint F-test: F=..., p=..., df=..."
                import re
                m = re.search(r'p=([\d.]+)', w)
                if m:
                    py_p = float(m.group(1))
                break

        if py_p is None:
            pytest.skip("Python pretrend p-value not available")

        # Both tests should give the same qualitative conclusion
        # (p > 0.05 means no pretrend violation). Use loose tolerance
        # because chi2 vs F distributions differ in finite samples.
        passed, msg = tolerance_close(
            py_p, st_p, name="pretrend_joint_pvalue", rtol=5e-2, atol=1e-3
        )
        assert passed, msg
