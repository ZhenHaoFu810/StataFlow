"""
Golden test: w4_eventstudyinteract_basic - Basic eventstudyinteract test.

Tests eventstudyinteract functionality with staggered adoption data, verifying:
- Event time coefficients
- Standard errors
"""

import re
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from stataflow import EventStudyInteract
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

    ids = np.repeat(np.arange(1, n_units + 1), n_periods)
    years = np.tile(np.arange(2001, 2001 + n_periods), n_units)

    unit_cohorts = np.zeros(n_units, dtype=int)
    unit_cohorts[:150] = 2004
    unit_cohorts[150:300] = 2006
    unit_cohorts[300:] = 2007
    first_treat = np.repeat(unit_cohorts, n_periods)

    treat = ((years >= first_treat) & (first_treat > 0)).astype(int)

    fe_i = np.repeat(np.random.normal(0, 1, n_units), n_periods)
    unique_years = np.unique(years)
    year_fe_map = {y: np.random.normal(0, 1) for y in unique_years}
    fe_t = np.array([year_fe_map[y] for y in years])

    y = fe_i + fe_t + 1.5 * treat + np.random.normal(0, 1, len(ids))

    df = pd.DataFrame({
        "id": ids,
        "year": years,
        "first_treat": first_treat,
        "treat": treat,
        "y": y,
    })

    # Create relative time indicators
    df["rel_time"] = df["year"] - df["first_treat"]
    df.loc[df["first_treat"] <= 0, "rel_time"] = np.nan

    # Generate dummy variables for each relative time period (-3 to +3)
    for h in range(1, 4):
        df[f"Dm{h}"] = ((df["rel_time"] == -h) & (df["first_treat"] > 0)).astype(float)
        df.loc[df["first_treat"] <= 0, f"Dm{h}"] = 0.0
        df[f"Dp{h}"] = ((df["rel_time"] == h) & (df["first_treat"] > 0)).astype(float)
        df.loc[df["first_treat"] <= 0, f"Dp{h}"] = 0.0

    df["D0"] = ((df["rel_time"] == 0) & (df["first_treat"] > 0)).astype(float)
    df.loc[df["first_treat"] <= 0, "D0"] = 0.0

    # Control cohort indicator
    df["never_treated"] = (df["first_treat"] == 0).astype(int)

    return df


def _parse_stata_log(log_content: str) -> dict:
    """Parse Stata eventstudyinteract log output."""
    result = {}
    coefficients = []

    # eventstudyinteract do-file prints B_name= and SE_name= lines
    b_matches = {m.group(1): float(m.group(2)) for m in re.finditer(r'B_(D[m,p]?\d+)=(-?[\d.]+)', log_content)}
    se_matches = {m.group(1): float(m.group(2)) for m in re.finditer(r'SE_(D[m,p]?\d+)=(-?[\d.]+)', log_content)}

    for name in b_matches:
        coefficients.append({
            'name': name,
            'beta': b_matches[name],
            'std_err': se_matches.get(name, 0.0),
        })

    if not coefficients:
        # Fallback to table pattern
        table_pattern = r'\|\s*(D[m,p]?\d+)\s*\|\s*(-?\d+\.?\d*)\s+(-?\d+\.?\d*)\s+(-?\d+\.?\d*)\s+([\d.]+)\s+(-?\d+\.?\d*)\s+(-?\d+\.?\d*)\s*\|'
        table_matches = re.findall(table_pattern, log_content)
        for name, beta, se, z, pval, ci_low, ci_high in table_matches:
            coefficients.append({
                'name': name,
                'beta': float(beta),
                'std_err': float(se),
            })

    result['coefficients'] = coefficients
    return result


def _run_stata_eventstudyinteract(data: pd.DataFrame) -> dict:
    """Run Stata eventstudyinteract for basic test."""
    dta_file = PROJECT_STATA_CASES / "w4_eventstudyinteract_basic_data.dta"
    data.to_stata(str(dta_file), write_index=False)

    do_template = f'''
clear all
set more off

use "{dta_file}", clear

eventstudyinteract y Dm3 Dm2 D0 Dp1 Dp2 Dp3, cohort(first_treat) control_cohort(never_treated) absorb(id year) vce(cluster id)

matrix b_iw = e(b_iw)
matrix V_iw = e(V_iw)
local names : colfullnames b_iw
local i = 1
foreach name of local names {{
    display "B_`name'=" b_iw[1, `i']
    display "SE_`name'=" sqrt(V_iw[`i', `i'])
    local ++i
}}

display "ES_OK"
'''
    runner = StataRunner()
    result = runner.run_do_file(do_template, output_dir=str(PROJECT_STATA_OUTPUT))

    if result.exit_code != 0:
        raise RuntimeError(f"Stata failed: {result.error_message}")
    if not result.output_content:
        raise RuntimeError("Stata produced no output")

    return _parse_stata_log(result.output_content)


class TestW4EventStudyInteractBasic:
    """Golden test for w4_eventstudyinteract_basic."""

    @pytest.fixture(scope="class")
    def test_data(self):
        return _generate_test_data()

    @pytest.fixture(scope="class")
    def python_result(self, test_data):
        event_dummies = ["Dm3", "Dm2", "D0", "Dp1", "Dp2", "Dp3"]
        model = EventStudyInteract(
            data=test_data,
            y="y",
            event_dummies=event_dummies,
            cohort="first_treat",
            control_cohort="never_treated",
            absorb=["id", "year"],
        )
        return model.fit(vce="cluster", cluster="id")

    @pytest.fixture(scope="class")
    def stata_result(self, test_data):
        return _run_stata_eventstudyinteract(test_data)

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
            if st_coef.get("std_err", 0) == 0:
                continue
            passed, msg = tolerance_close(
                py_coef.std_err, st_coef["std_err"], name=f"std_err[{py_coef.name}]",
                rtol=1e-4, atol=1e-6,
            )
            assert passed, msg
