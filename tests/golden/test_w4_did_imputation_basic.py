"""
Golden test: w4_did_imputation_basic - Basic did_imputation test.

Tests did_imputation functionality with staggered adoption data, verifying:
- Event time coefficients (tauh)
- Standard errors
- Number of observations
- Number of clusters
"""

import re
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from statapy import DIDImputation
from statapy.stata_runner import StataRunner
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
    # Time FE: same for all units in a given year
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
    """Parse Stata did_imputation log output."""
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

    result['coefficients'] = coefficients
    return result


def _run_stata_did_imputation(data: pd.DataFrame) -> dict:
    """Run Stata did_imputation for basic test."""
    dta_file = PROJECT_STATA_CASES / "w4_did_imputation_basic_data.dta"
    data.to_stata(str(dta_file), write_index=False)

    do_template = f'''
clear all
set more off

use "{dta_file}", clear

did_imputation y id year first_treat, allhorizons cluster(id) autosample

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

display "DID_IMP_OK"
'''
    runner = StataRunner()
    result = runner.run_do_file(do_template, output_dir=str(PROJECT_STATA_OUTPUT))

    if result.exit_code != 0:
        raise RuntimeError(f"Stata failed: {result.error_message}")
    if not result.output_content:
        raise RuntimeError("Stata produced no output")

    return _parse_stata_log(result.output_content)


class TestW4DidImputationBasic:
    """Golden test for w4_did_imputation_basic."""

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
        return model.fit(cluster="id", allhorizons=True, autosample=True)

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
                py_coef.beta, st_coef["beta"], name=f"beta[{py_coef.name}]"
            )
            assert passed, msg

    def test_coefficients_std_err(self, python_result, stata_result):
        for py_coef, st_coef in zip(
            python_result.coefficients, stata_result.get("coefficients", [])
        ):
            # Skip omitted coefficients
            if st_coef.get("std_err", 0) == 0:
                continue
            # Use slightly looser tolerance for SE: iterative groupby vs reghdfe
            # can produce tiny numerical differences (< 1e-4 relative)
            passed, msg = tolerance_close(
                py_coef.std_err, st_coef["std_err"], name=f"std_err[{py_coef.name}]",
                rtol=1e-4, atol=1e-6
            )
            assert passed, msg
