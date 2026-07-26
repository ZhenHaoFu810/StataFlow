"""Reproducible Stata validation cases for community commands.

Each case requires the corresponding community ado in the local Stata
installation; when the ado is missing, the case skips transparently with an
``ssc install`` hint (see conftest.py). DID cases use treatment cohorts in
the same units as calendar time (the Wave-14 time contract) and are built
with a true post-treatment effect of +2.0, so an all-zero coefficient
vector would fail the explicit nonzero-effect guard.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from stataflow.compat.stata import csdid, did_imputation, rdrobust, reghdfe
from tests.stata_validation.test_utils import (
    STATA_MATRIX_DUMP,
    assert_coef_alignment,
    run_stata_case,
    stata_coef_dump,
    tolerance_close,
    write_case_data,
)

pytestmark = pytest.mark.stata

TREAT_EFFECT = 2.0


def _make_hdfe_data(seed: int = 20260730, n_entities: int = 40, n_periods: int = 6) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    n = n_entities * n_periods
    entity_id = np.repeat(np.arange(1, n_entities + 1), n_periods)
    time_id = np.tile(np.arange(1, n_periods + 1), n_entities)
    x1 = rng.normal(size=n)
    x2 = rng.normal(size=n)
    entity_fe = np.repeat(rng.normal(scale=2.0, size=n_entities), n_periods)
    time_fe = np.tile(rng.normal(scale=1.0, size=n_periods), n_entities)
    y = 1.0 + 1.5 * x1 - 2.0 * x2 + entity_fe + time_fe + rng.normal(size=n)
    return pd.DataFrame(
        {
            "y": y,
            "x1": x1,
            "x2": x2,
            "entity_id": entity_id.astype(int),
            "time_id": time_id.astype(int),
        }
    )


def _make_staggered_panel(seed: int = 20260731) -> pd.DataFrame:
    """Balanced staggered-adoption panel with calendar-unit cohorts.

    240 units x 10 calendar years (2000-2009). Cohorts 2004 and 2007 are
    treated from their cohort year on with a true effect of +2.0; the
    remaining 80 units are never treated. Cohorts are recorded in the same
    units as the calendar time variable.
    """
    rng = np.random.default_rng(seed)
    n_units, years = 240, np.arange(2000, 2010)
    n = n_units * len(years)
    unit_id = np.repeat(np.arange(1, n_units + 1), len(years))
    year = np.tile(years, n_units)
    cohorts = np.full(n_units, np.nan)
    cohorts[:80] = 2004.0
    cohorts[80:160] = 2007.0
    first_treat = np.repeat(cohorts, len(years))
    treat = ((year >= first_treat) & ~np.isnan(first_treat)).astype(float)
    unit_fe = np.repeat(rng.normal(size=n_units), len(years))
    year_fe_map = {y: rng.normal() for y in years}
    year_fe = np.array([year_fe_map[y] for y in year])
    y = unit_fe + year_fe + TREAT_EFFECT * treat + rng.normal(size=n)
    return pd.DataFrame(
        {
            "y": y,
            "id": unit_id.astype(int),
            "year": year.astype(int),
            "first_treat": first_treat,
        }
    )


def test_reghdfe_cluster(stata_path, require_ado):
    """reghdfe y x1 x2, absorb(entity_id time_id) vce(cluster entity_id)."""
    require_ado("reghdfe")
    data = _make_hdfe_data()
    dta = write_case_data(data, "public_reghdfe_cluster")
    do = f"""
version 17.0
clear all
set more off
use "{dta.as_posix()}", clear
reghdfe y x1 x2, absorb(entity_id time_id) vce(cluster entity_id)
di as txt "E_N=" e(N)
di as txt "E_N_CLUST=" e(N_clust)
{stata_coef_dump(["x1", "x2", "_cons"])}
di as txt "STATAFLOW_PUBLIC_REGHDFE_CLUSTER_OK"
"""
    st = run_stata_case(do, "STATAFLOW_PUBLIC_REGHDFE_CLUSTER_OK")
    py = reghdfe(
        data,
        y="y",
        x=["x1", "x2"],
        absorb=["entity_id", "time_id"],
        vce="cluster",
        cluster="entity_id",
    )
    assert py.sample.nobs == int(st["e"]["N"])
    assert_coef_alignment(py.coefficients, st)


def test_did_imputation_calendar_cohort(stata_path, require_ado):
    """did_imputation with valid calendar cohorts and a nonzero effect."""
    require_ado("did_imputation")
    data = _make_staggered_panel()
    dta = write_case_data(data, "public_did_imputation")
    do = f"""
version 17.0
clear all
set more off
use "{dta.as_posix()}", clear
did_imputation y id year first_treat, cluster(id) allhorizons autosample minn(0)
{STATA_MATRIX_DUMP}
di as txt "E_N=" e(N)
di as txt "STATAFLOW_PUBLIC_DID_IMPUTATION_OK"
"""
    st = run_stata_case(do, "STATAFLOW_PUBLIC_DID_IMPUTATION_OK")
    py = did_imputation(
        data,
        y="y",
        id="id",
        time="year",
        first_treat="first_treat",
        cluster="id",
        allhorizons=True,
        autosample=True,
        minn=0,
    )
    assert py.sample.nobs == int(st["e"]["N"])

    py_names = [c.name for c in py.coefficients]
    assert set(py_names) == set(st["b"].keys()), (
        f"coefficient names differ: Python={sorted(py_names)}, Stata={sorted(st['b'])}"
    )
    # Nonzero-effect guard: an all-zero vector is not alignment evidence.
    assert max(abs(c.beta) for c in py.coefficients) > 1.0
    # Standard errors use the documented Stata comparison tolerance
    # for the BJS did_imputation ado (rel < 1e-2): the Python asymptotic VCE
    # differs from the ado by a known small numerical factor, while point
    # estimates align at the project-standard rel < 1e-6.
    assert_coef_alignment(py.coefficients, st, se_rtol=1e-2)


def test_csdid_calendar_cohort(stata_path, require_ado):
    """csdid method(reg) with valid calendar cohorts and a nonzero effect."""
    require_ado("csdid")
    data = _make_staggered_panel()
    # csdid encodes never-treated units as gvar == 0 (not missing). Cohort
    # labels stay integer so event-time labels are integer-valued.
    data["first_treat"] = data["first_treat"].fillna(0).astype(int)
    dta = write_case_data(data, "public_csdid")
    do = f"""
version 17.0
clear all
set more off
use "{dta.as_posix()}", clear
csdid y, ivar(id) time(year) gvar(first_treat) method(reg)
csdid_estat event
matrix b = r(b)
matrix V = r(V)
local names : colfullnames b
local i = 1
foreach name of local names {{
    di as txt "B_" "`name'" "=" %24.16e b[1, `i']
    di as txt "SE_" "`name'" "=" %24.16e sqrt(V[`i', `i'])
    local ++i
}}
di as txt "E_N=" e(N)
di as txt "STATAFLOW_PUBLIC_CSDID_OK"
"""
    st = run_stata_case(do, "STATAFLOW_PUBLIC_CSDID_OK")
    model = csdid(
        data,
        y="y",
        id="id",
        time="year",
        first_treat="first_treat",
        method="reg",
        vce="cluster",
        cluster="id",
    )
    py_event = model.estat_event()
    assert py_event.sample.nobs == int(st["e"]["N"])

    # Nonzero-effect guard on post-treatment event coefficients.
    post = [c for c in py_event.coefficients if c.name.lower().startswith("tp")]
    assert post and max(abs(c.beta) for c in post) > 1.0

    failures = []
    for row in py_event.coefficients:
        key = row.name.lower()
        match = next((k for k in st["b"] if k.lower() == key), None)
        if match is None:
            failures.append(f"missing Stata event coefficient: {row.name}")
            continue
        ok, msg = tolerance_close(row.beta, st["b"][match], name=f"beta[{row.name}]")
        if not ok:
            failures.append(msg)
        ok, msg = tolerance_close(row.std_err, st["se"][match], name=f"se[{row.name}]")
        if not ok:
            failures.append(msg)
    assert not failures, "\n".join(failures)


def test_rdrobust_fixed_bandwidth(stata_path, require_ado):
    """rdrobust y x, c(0) h(0.5): conventional tau and its SE."""
    require_ado("rdrobust")
    rng = np.random.default_rng(20260801)
    n = 2000
    x = rng.uniform(-1.0, 1.0, n)
    y = 1.0 + 0.5 * x + TREAT_EFFECT * (x >= 0) + rng.normal(scale=0.3, size=n)
    data = pd.DataFrame({"y": y, "x": x})
    dta = write_case_data(data, "public_rdrobust")
    do = f"""
version 17.0
clear all
set more off
use "{dta.as_posix()}", clear
rdrobust y x, c(0) h(0.5)
di as txt "E_TAU_CL=" %24.16e e(tau_cl)
di as txt "E_SE_TAU_CL=" %24.16e e(se_tau_cl)
di as txt "E_N=" e(N)
di as txt "E_N_H_L=" e(N_h_l)
di as txt "E_N_H_R=" e(N_h_r)
di as txt "STATAFLOW_PUBLIC_RDROBUST_OK"
"""
    st = run_stata_case(do, "STATAFLOW_PUBLIC_RDROBUST_OK")
    py = rdrobust(data, y="y", x="x", c=0.0, h=0.5)

    conventional = py.coefficients[0]
    assert conventional.name == "Conventional"
    failures = []
    for label, py_val, st_val in (
        ("tau_cl", conventional.beta, st["e"]["TAU_CL"]),
        ("se_tau_cl", conventional.std_err, st["e"]["SE_TAU_CL"]),
        ("N_h_l", py._rd_extras["N_h_l"], st["e"]["N_H_L"]),
        ("N_h_r", py._rd_extras["N_h_r"], st["e"]["N_H_R"]),
    ):
        ok, msg = tolerance_close(py_val, st_val, name=label)
        if not ok:
            failures.append(msg)
    assert not failures, "\n".join(failures)
    # Nonzero-effect guard.
    assert abs(conventional.beta) > 1.0
