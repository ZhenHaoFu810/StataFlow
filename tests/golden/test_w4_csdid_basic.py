"""Golden dual-run test: CSDID basic synthetic case."""

import numpy as np
import pandas as pd
from pathlib import Path
import pytest

from statapy import CSDID
from statapy.stata_runner import StataRunner
from tests.golden.test_utils import (
    PROJECT_ROOT,
    PROJECT_STATA_OUTPUT,
    PROJECT_STATA_CASES,
    parse_stata_log,
    tolerance_close,
)


def test_csdid_basic_synthetic():
    """Synthetic staggered adoption panel: 500 units x 11 years."""
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

    df = pd.DataFrame({"id": ids, "year": years, "first_treat": first_treat, "treat": treat, "y": y})

    dta_file = PROJECT_STATA_CASES / "w4_csdid_basic_data.dta"
    dta_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_stata(str(dta_file), write_index=False)

    do_content = f"""
clear all
set more off

use "{dta_file}", clear

csdid y, ivar(id) time(year) gvar(first_treat) method(reg)

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
display "E_N_CLUST=" e(N_clust)
display "CSDID_OK"
"""

    runner = StataRunner()
    stata_result = runner.run_do_file(do_content, output_dir=str(PROJECT_STATA_OUTPUT), timeout=300)
    assert stata_result.exit_code == 0, f"Stata failed: {stata_result.error_message}"

    parsed = parse_stata_log(stata_result.output_content)

    # Run Python CSDID
    py_res = CSDID(data=df, y="y", id="id", time="year", first_treat="first_treat").fit(method="reg", vce="cluster", cluster="id")
    py_event = py_res.estat_event()

    # Compare nobs (csdid does not store e(N_clust) by default)
    assert parsed.get("nobs") == pytest.approx(py_res.nobs, abs=1)

    # Extract only event-study coefficients (Pre_avg, Post_avg, Tm*, Tp*)
    event_names = {"pre_avg", "post_avg"} | {f"tm{i}" for i in range(1, 10)} | {f"tp{i}" for i in range(0, 10)}
    stata_coefs = {}
    for c in parsed["coefficients"]:
        name_lower = c["name"].lower()
        if name_lower in event_names:
            stata_coefs[name_lower] = c

    for key in py_event.params:
        stata_name = key.lower()
        assert stata_name in stata_coefs, f"Missing Stata coefficient: {key}"
        stata_beta = float(stata_coefs[stata_name]["beta"])
        stata_se = float(stata_coefs[stata_name]["std_err"])
        py_beta = py_event.params[key]
        py_se = py_event.bse[key]

        passed_b, msg_b = tolerance_close(py_beta, stata_beta, rtol=1e-5, atol=1e-7, name=f"{key}_beta")
        passed_se, msg_se = tolerance_close(py_se, stata_se, rtol=5e-3, atol=1e-5, name=f"{key}_se")

        assert passed_b, msg_b
        assert passed_se, msg_se
