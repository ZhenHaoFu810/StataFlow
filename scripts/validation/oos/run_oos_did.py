"""OOS validation runner for DID / Event Study family.

Datasets:
- jtrain (new OOS staggered-adoption panel, already prepared)
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.validation.oos.common import (
    OOSCase,
    STATA_CASES,
    compare_case,
    run_stata_and_parse,
    write_case_report,
    write_family_summary,
)
from stataflow.compat.stata import csdid, did_imputation, eventstudyinteract


def _load_jtrain() -> pd.DataFrame:
    return pd.read_stata(PROJECT_ROOT / "research/data/public/did/jtrain_prepared.dta")


def run_oos_did_imputation_jtrain() -> dict:
    case = OOSCase(
        case_id="oos_did_imputation_jtrain",
        family="did",
        command="did_imputation",
        dataset_key="jtrain",
        dataset_path="research/data/public/did/jtrain_prepared.dta",
        stata_command="did_imputation lhrsemp fcode year first_treat, allhorizons autosample cluster(fcode)",
        python_callable="stataflow.compat.stata.did_imputation",
        python_kwargs={
            "data": None,
            "y": "lhrsemp",
            "id": "fcode",
            "time": "year",
            "first_treat": "first_treat",
            "allhorizons": True,
            "autosample": True,
            "cluster": "fcode",
        },
        description="BJS DID imputation on JTRAIN staggered-adoption panel (firm-level job training).",
        notes="JTRAIN has only 3 time periods (1987-1989), which is insufficient for Stata did_imputation to impute FE for all cohorts. Stata drops to 122 obs and suppresses most coefficients. Python is more lenient. This case documents the behavior difference on short panels.",
    )

    data = _load_jtrain()
    dta_file = STATA_CASES / "oos_jtrain.dta"
    data.to_stata(str(dta_file), write_index=False)

    do = f"""
clear all
set more off
use "{dta_file}", clear
did_imputation lhrsemp fcode year first_treat, allhorizons autosample cluster(fcode)

matrix b = e(b)
local names : colfullnames b
foreach name of local names {{
    display "COEF `name' " _b["`name'"] " " _se["`name'"]
}}

display "E_N=" e(N)
"""
    st_result = run_stata_and_parse(do)
    py_result = did_imputation(
        data, y="lhrsemp", id="fcode", time="year", first_treat="first_treat",
        allhorizons=True, autosample=True, cluster="fcode",
    )

    field_map = {
        "nobs": ("sample.nobs", "nobs", 1e-6, 1e-8),
    }
    report = compare_case(py_result, st_result, case, field_map, coef_rtol=1e-4, coef_atol=1e-6)
    write_case_report(report)
    return report


def run_oos_eventstudyinteract_jtrain() -> dict:
    case = OOSCase(
        case_id="oos_eventstudyinteract_jtrain",
        family="did",
        command="eventstudyinteract",
        dataset_key="jtrain",
        dataset_path="research/data/public/did/jtrain_prepared.dta",
        stata_command="eventstudyinteract lhrsemp Dm2 D0 Dp1, cohort(first_treat) control_cohort(never_treated) absorb(fcode year) vce(cluster fcode)",
        python_callable="stataflow.compat.stata.eventstudyinteract",
        python_kwargs={
            "data": None,
            "y": "lhrsemp",
            "time": "year",
            "first_treat": "first_treat",
            "cohort": "first_treat",
            "control_cohort": "never_treated",
            "absorb": ["fcode", "year"],
            "vce": "cluster",
            "cluster": "fcode",
            "horizons": [-2, -1, 0, 1],
            "omit": -1,
        },
        description="Sun-Abraham IW estimator on JTRAIN panel with firm and year FE.",
    )

    data = _load_jtrain()
    # Create never-treated indicator for control cohort
    data["never_treated"] = (data["first_treat"] == 0).astype(int)
    # Pre-generate event dummies for Stata (Python wrapper also creates these internally)
    rel_time = data["year"] - data["first_treat"]
    rel_time = rel_time.where(data["first_treat"] > 0, -1000)
    data["Dm2"] = (rel_time == -2).astype(float)
    data["D0"] = (rel_time == 0).astype(float)
    data["Dp1"] = (rel_time == 1).astype(float)
    dta_file = STATA_CASES / "oos_jtrain.dta"
    data.to_stata(str(dta_file), write_index=False)

    do = f"""
clear all
set more off
use "{dta_file}", clear
eventstudyinteract lhrsemp Dm2 D0 Dp1, cohort(first_treat) control_cohort(never_treated) absorb(fcode year) vce(cluster fcode)

matrix b_iw = e(b_iw)
matrix V_iw = e(V_iw)
local names : colfullnames b_iw
local i = 1
foreach name of local names {{
    display "COEF `name' " b_iw[1, `i'] " " sqrt(V_iw[`i', `i'])
    local ++i
}}

display "E_N=" e(N)
"""
    st_result = run_stata_and_parse(do)
    py_result = eventstudyinteract(
        data, y="lhrsemp", time="year", first_treat="first_treat",
        cohort="first_treat", control_cohort="never_treated", absorb=["fcode", "year"],
        vce="cluster", cluster="fcode", horizons=[-2, -1, 0, 1], omit=-1,
    )

    field_map = {
        "nobs": ("sample.nobs", "nobs", 0.05, 1e-8),
    }
    report = compare_case(py_result, st_result, case, field_map, coef_rtol=2e-3, coef_atol=1e-5)
    write_case_report(report)
    return report


def run_oos_csdid_jtrain() -> dict:
    case = OOSCase(
        case_id="oos_csdid_jtrain",
        family="did",
        command="csdid",
        dataset_key="jtrain",
        dataset_path="research/data/public/did/jtrain_prepared.dta",
        stata_command="csdid lhrsemp, ivar(fcode) time(year) gvar(first_treat) method(reg)",
        python_callable="stataflow.compat.stata.csdid",
        python_kwargs={
            "data": None,
            "y": "lhrsemp",
            "id": "fcode",
            "time": "year",
            "first_treat": "first_treat",
            "method": "reg",
        },
        description="Callaway-Sant'Anna ATT(g,t) on JTRAIN panel with never-treated control group.",
    )

    data = _load_jtrain()
    dta_file = STATA_CASES / "oos_jtrain.dta"
    data.to_stata(str(dta_file), write_index=False)

    do = f"""
clear all
set more off
use "{dta_file}", clear
csdid lhrsemp, ivar(fcode) time(year) gvar(first_treat) method(reg)

csdid_estat event

capture matrix b = r(b)
if _rc != 0 {{
    matrix b = e(b)
}}
capture matrix V = r(V)
if _rc != 0 {{
    matrix V = e(V)
}}
local names : colfullnames b
local i = 1
foreach name of local names {{
    display "COEF `name' " b[1, `i'] " " sqrt(V[`i', `i'])
    local ++i
}}

display "E_N=" e(N)
"""
    st_result = run_stata_and_parse(do)
    py_result = csdid(
        data, y="lhrsemp", id="fcode", time="year", first_treat="first_treat",
        method="reg",
    )

    field_map = {
        "nobs": ("sample.nobs", "nobs", 0.05, 1e-8),
    }
    report = compare_case(py_result, st_result, case, field_map, coef_rtol=0.1, coef_atol=1e-4)
    write_case_report(report)
    return report


if __name__ == "__main__":
    reports = []
    for fn in [
        run_oos_did_imputation_jtrain,
        run_oos_eventstudyinteract_jtrain,
        run_oos_csdid_jtrain,
    ]:
        print(f"Running {fn.__name__} ...")
        try:
            reports.append(fn())
        except Exception as exc:
            print(f"ERROR in {fn.__name__}: {exc}")
            reports.append({
                "case_id": fn.__name__.replace("run_", ""),
                "command": "unknown",
                "dataset_key": "unknown",
                "status": "blocked",
                "error": str(exc),
            })
    write_family_summary("did", reports)
    print("DID family OOS complete.")
