"""OOS validation runner for IV family.

Datasets:
- card (new specification)
- wagepan (new specification for ivreghdfe)
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
from stataflow.compat.stata import ivregress_2sls, ivreghdfe


def _load_card() -> pd.DataFrame:
    return pd.read_csv(PROJECT_ROOT / "research/data/public/iv/card.csv")


def _load_wagepan() -> pd.DataFrame:
    return pd.read_csv(PROJECT_ROOT / "research/data/public/panel/wooldridge/wagepan.csv")


def run_oos_ivregress_card() -> dict:
    """New specification on Card data: different instruments and controls."""
    case = OOSCase(
        case_id="oos_ivregress_card",
        family="iv",
        command="ivregress 2sls",
        dataset_key="card",
        dataset_path="research/data/public/iv/card.csv",
        stata_command="ivregress 2sls lwage exper expersq smsa south (educ = nearc2 nearc4)",
        python_callable="stataflow.compat.stata.ivregress_2sls",
        python_kwargs={
            "y": "lwage",
            "x_exog": ["exper", "expersq", "smsa", "south"],
            "x_endog": ["educ"],
            "instruments": ["nearc2", "nearc4"],
            "vce": "ols",
        },
        description="Returns-to-schooling 2SLS with two instruments (nearc2 + nearc4).",
    )

    data = _load_card()
    dta_file = STATA_CASES / "oos_card.dta"
    data.to_stata(str(dta_file), write_index=False)

    do = f"""
clear all
set more off
use "{dta_file}", clear
ivregress 2sls lwage exper expersq smsa south (educ = nearc2 nearc4)

display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_DF_R=" e(df_r)
display "E_F=" e(F)

display "COEF educ " _b[educ] " " _se[educ]
display "COEF exper " _b[exper] " " _se[exper]
display "COEF expersq " _b[expersq] " " _se[expersq]
display "COEF smsa " _b[smsa] " " _se[smsa]
display "COEF south " _b[south] " " _se[south]
display "COEF _cons " _b[_cons] " " _se[_cons]
"""
    st_result = run_stata_and_parse(do)
    py_result = ivregress_2sls(data, **case.python_kwargs)

    field_map = {
        "nobs": ("sample.nobs", "nobs", 1e-6, 1e-8),
        "df_model": ("fit.df_model", "df_model", 1e-6, 1e-8),
        "df_resid": ("fit.df_resid", "df_resid", 1e-6, 1e-8),
        "f_stat": ("fit.f_stat", "f_stat", 1e-6, 1e-8),
    }
    report = compare_case(py_result, st_result, case, field_map)
    write_case_report(report)
    return report


def run_oos_ivreghdfe_wagepan() -> dict:
    """New specification on wagepan: absorbed IV with different endogenous var and instrument."""
    case = OOSCase(
        case_id="oos_ivreghdfe_wagepan",
        family="iv",
        command="ivreghdfe",
        dataset_key="wagepan",
        dataset_path="research/data/public/panel/wooldridge/wagepan.csv",
        stata_command="ivreghdfe lwage hours fin (union = married), absorb(nr year) vce(cluster nr)",
        python_callable="stataflow.compat.stata.ivreghdfe",
        python_kwargs={
            "y": "lwage",
            "x_exog": ["hours", "fin"],
            "x_endog": ["union"],
            "instruments": ["married"],
            "absorb": ["nr", "year"],
            "vce": "cluster",
            "cluster": "nr",
        },
        description="Absorbed IV on wage panel with worker and year FE, clustered at worker level. Different exogenous controls from golden test.",
    )

    data = _load_wagepan()
    dta_file = STATA_CASES / "oos_wagepan.dta"
    data.to_stata(str(dta_file), write_index=False)

    do = f"""
clear all
set more off
use "{dta_file}", clear
ivreghdfe lwage hours fin (union = married), absorb(nr year) vce(cluster nr)

display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_DF_R=" e(df_r)
display "E_DF_A=" e(df_a)
display "E_F=" e(F)
display "E_N_CLUST=" e(N_clust)

display "COEF union " _b[union] " " _se[union]
display "COEF hours " _b[hours] " " _se[hours]
display "COEF fin " _b[fin] " " _se[fin]
"""
    st_result = run_stata_and_parse(do)
    py_result = ivreghdfe(data, **case.python_kwargs)

    field_map = {
        "nobs": ("sample.nobs", "nobs", 1e-6, 1e-8),
        "df_model": ("fit.df_model", "df_model", 1e-6, 1e-8),
        "df_resid": ("fit.df_resid", "df_resid", 1e-6, 1e-8),
        "df_a": ("fit.df_a", "df_a", 1e-6, 1e-8),
        "f_stat": ("fit.f_stat", "f_stat", 1e-6, 1e-8),
    }
    report = compare_case(py_result, st_result, case, field_map)
    write_case_report(report)
    return report


if __name__ == "__main__":
    reports = []
    for fn in [run_oos_ivregress_card, run_oos_ivreghdfe_wagepan]:
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
    write_family_summary("iv", reports)
    print("IV family OOS complete.")
