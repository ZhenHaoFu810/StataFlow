"""
Golden test: w9_csdid_dr_basic - CSDID with method(drimp) on synthetic data.

Tests CSDID doubly-robust estimation with covariates on synthetic staggered
adoption data, verifying event-study coefficients align with Stata 17.
"""

import re
import numpy as np
import pandas as pd
from pathlib import Path
import pytest

from stataflow import CSDID
from stataflow.stata_runner import StataRunner
from tests.golden.test_utils import (
    PROJECT_ROOT,
    PROJECT_STATA_OUTPUT,
    PROJECT_STATA_CASES,
    parse_stata_log,
    tolerance_close,
)


def test_csdid_dr_basic_synthetic():
    """Synthetic staggered adoption panel with covariates: 500 units x 11 years."""
    np.random.seed(12345)
    n_units = 500
    n_periods = 11
    ids = np.repeat(np.arange(1, n_units + 1), n_periods)
    years = np.tile(np.arange(2001, 2001 + n_periods), n_units)
    unit_cohorts = np.zeros(n_units, dtype=int)
    unit_cohorts[:100] = 0  # never-treated
    unit_cohorts[100:250] = 2004
    unit_cohorts[250:400] = 2006
    unit_cohorts[400:] = 2007
    first_treat = np.repeat(unit_cohorts, n_periods)
    treat = ((years >= first_treat) & (first_treat > 0)).astype(int)
    fe_i = np.repeat(np.random.normal(0, 1, n_units), n_periods)
    unique_years = np.unique(years)
    year_fe_map = {y: np.random.normal(0, 1) for y in unique_years}
    fe_t = np.array([year_fe_map[y] for y in years])

    # Covariates
    x1 = np.random.normal(0, 1, len(ids))
    x2 = np.random.normal(0, 1, len(ids))

    # Outcome with covariate effects
    y = fe_i + fe_t + 0.3 * x1 - 0.2 * x2 + 1.5 * treat + np.random.normal(0, 1, len(ids))

    df = pd.DataFrame({
        "id": ids, "year": years, "first_treat": first_treat,
        "treat": treat, "x1": x1, "x2": x2, "y": y,
    })

    dta_file = PROJECT_STATA_CASES / "w9_csdid_dr_basic_data.dta"
    dta_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_stata(str(dta_file), write_index=False)

    do_content = f"""
clear all
set more off

use "{dta_file}", clear

csdid y x1 x2, ivar(id) time(year) gvar(first_treat) method(drimp)

csdid_estat event

matrix b = e(b)
matrix V = e(V)
local names : colfullnames b
local i = 1
foreach name of local names {{
    display "B_`name'=" b[1, `i']
    display "SE_`name'=" sqrt(V[`i', `i'])
    local ++i
}}

display "E_N=" e(N)
display "CSDID_DR_OK"
"""

    runner = StataRunner()
    stata_result = runner.run_do_file(
        do_content, output_dir=str(PROJECT_STATA_OUTPUT), timeout=300
    )
    assert stata_result.exit_code == 0, f"Stata failed: {stata_result.error_message}"

    # Parse event-study coefficients from the log table directly
    def _parse_event_study_log(log_content: str) -> dict:
        lines = log_content.splitlines()
        start_idx = None
        for i, line in enumerate(lines):
            if "Event Study:Dynamic effects" in line:
                start_idx = i
                break
        if start_idx is None:
            raise ValueError("Event Study section not found in log")
        delim_idx = None
        for i in range(start_idx, len(lines)):
            if "-------------+----------------------------------------------------------------" in lines[i]:
                delim_idx = i
                break
        if delim_idx is None:
            raise ValueError("Coefficient table delimiter not found")
        coef_pattern = re.compile(
            r'^\s+([A-Za-z_][A-Za-z0-9_]*)\s+\|\s+(-?\d*\.?\d+)\s+(-?\d*\.?\d+)'
        )
        coefficients = []
        for line in lines[delim_idx + 1:]:
            if line.strip() == '':
                break
            match = coef_pattern.match(line)
            if match:
                coefficients.append({
                    'name': match.group(1),
                    'beta': float(match.group(2)),
                    'std_err': float(match.group(3)),
                })
        nobs_match = re.search(r'E_N=(\d+)', log_content)
        nobs = int(nobs_match.group(1)) if nobs_match else None
        return {'coefficients': coefficients, 'nobs': nobs}

    parsed = _parse_event_study_log(stata_result.output_content)

    # Run Python CSDID with DR
    py_res = CSDID(
        data=df, y="y", id="id", time="year", first_treat="first_treat", xvars=["x1", "x2"]
    ).fit(method="drimp", vce="cluster", cluster="id")
    py_event = py_res.estat_event()

    # Compare nobs
    assert parsed.get("nobs") == pytest.approx(py_res.nobs, abs=1)

    # Extract only event-study coefficients (Pre_avg, Post_avg, Tm*, Tp*)
    event_names = {"pre_avg", "post_avg"} | {f"tm{i}" for i in range(1, 10)} | {f"tp{i}" for i in range(0, 10)}
    stata_coefs = {}
    for c in parsed["coefficients"]:
        name_lower = c["name"].lower()
        if name_lower in event_names:
            stata_coefs[name_lower] = c

    for coef_row in py_event.coefficients:
        key = coef_row.name
        stata_name = key.lower()
        assert stata_name in stata_coefs, f"Missing Stata coefficient: {key}"
        stata_beta = float(stata_coefs[stata_name]["beta"])
        stata_se = float(stata_coefs[stata_name]["std_err"])
        py_beta = coef_row.beta
        py_se = coef_row.std_err

        # DR method may have larger numerical differences due to PS/OR fitting.
        # Pre-treatment estimates are near zero, so use absolute tolerance.
        # Post-treatment estimates target ~1.5, so relative tolerance applies.
        is_pre = stata_name.startswith("tm") or stata_name == "pre_avg"
        if is_pre:
            b_rtol, b_atol = 1e-1, 5e-2
        else:
            b_rtol, b_atol = 5e-2, 5e-2
        passed_b, msg_b = tolerance_close(
            py_beta, stata_beta, rtol=b_rtol, atol=b_atol, name=f"{key}_beta"
        )
        passed_se, msg_se = tolerance_close(
            py_se, stata_se, rtol=1.5e-1, atol=2e-2, name=f"{key}_se"
        )

        assert passed_b, msg_b
        assert passed_se, msg_se
