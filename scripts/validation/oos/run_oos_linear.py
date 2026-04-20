"""OOS validation runner for Linear / FE / HDFE family.

Datasets:
- airfare (new OOS panel)
- wagepan (new specification for areg/reghdfe)
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
    STATA_OUTPUT,
    compare_case,
    run_stata_and_parse,
    write_case_report,
    write_family_summary,
)
from statapy.compat.stata import areg, reghdfe, regress, xtreg_fe


def _load_airfare() -> pd.DataFrame:
    return pd.read_csv(PROJECT_ROOT / "research/data/public/panel/oos/airfare.csv")


def _load_wagepan() -> pd.DataFrame:
    return pd.read_csv(PROJECT_ROOT / "research/data/public/panel/wooldridge/wagepan.csv")


def run_oos_regress_airfare() -> dict:
    case = OOSCase(
        case_id="oos_regress_airfare",
        family="linear",
        command="regress",
        dataset_key="airfare",
        dataset_path="research/data/public/panel/oos/airfare.csv",
        stata_command="regress lfare ldist concen y98 y99 y00",
        python_callable="statapy.compat.stata.regress",
        python_kwargs={"y": "lfare", "x": ["ldist", "concen", "y98", "y99", "y00"], "vce": "ols"},
        description="Pooled OLS on airfare panel with route distance, market concentration, and year dummies.",
    )

    data = _load_airfare()
    dta_file = STATA_CASES / "oos_airfare.dta"
    data.to_stata(str(dta_file), write_index=False)

    do = f"""
clear all
set more off
use "{dta_file}", clear
regress lfare ldist concen y98 y99 y00

display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_DF_R=" e(df_r)
display "E_R2=" e(r2)
display "E_R2_A=" e(r2_a)
display "E_RMSE=" e(rmse)
display "E_F=" e(F)

display "COEF ldist " _b[ldist] " " _se[ldist]
display "COEF concen " _b[concen] " " _se[concen]
display "COEF y98 " _b[y98] " " _se[y98]
display "COEF y99 " _b[y99] " " _se[y99]
display "COEF y00 " _b[y00] " " _se[y00]
display "COEF _cons " _b[_cons] " " _se[_cons]
"""
    st_result = run_stata_and_parse(do)
    py_result = regress(data, **case.python_kwargs)

    field_map = {
        "nobs": ("sample.nobs", "nobs", 1e-6, 1e-8),
        "df_model": ("fit.df_model", "df_model", 1e-6, 1e-8),
        "df_resid": ("fit.df_resid", "df_resid", 1e-6, 1e-8),
        "r2": ("fit.r2", "r2", 1e-6, 1e-8),
        "r2_adj": ("fit.r2_adj", "r2_adj", 1e-6, 1e-8),
        "rmse": ("fit.rmse", "rmse", 1e-6, 1e-8),
        "f_stat": ("fit.f_stat", "f_stat", 1e-6, 1e-8),
    }
    report = compare_case(py_result, st_result, case, field_map)
    write_case_report(report)
    return report


def run_oos_xtreg_fe_airfare() -> dict:
    case = OOSCase(
        case_id="oos_xtreg_fe_airfare",
        family="linear",
        command="xtreg, fe",
        dataset_key="airfare",
        dataset_path="research/data/public/panel/oos/airfare.csv",
        stata_command="xtreg lfare concen y98 y99 y00, fe",
        python_callable="statapy.compat.stata.xtreg_fe",
        python_kwargs={"y": "lfare", "x": ["concen", "y98", "y99", "y00"], "fe": "id", "vce": "ols"},
        description="Within-transformation FE on airfare panel (route FE).",
    )

    data = _load_airfare()
    dta_file = STATA_CASES / "oos_airfare.dta"
    data.to_stata(str(dta_file), write_index=False)

    do = f"""
clear all
set more off
use "{dta_file}", clear
xtset id year
xtreg lfare concen y98 y99 y00, fe

display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_DF_R=" e(df_r)
display "E_R2_W=" e(r2_w)
display "E_RMSE=" e(rmse)
display "E_F=" e(F)

display "COEF concen " _b[concen] " " _se[concen]
display "COEF y98 " _b[y98] " " _se[y98]
display "COEF y99 " _b[y99] " " _se[y99]
display "COEF y00 " _b[y00] " " _se[y00]
"""
    st_result = run_stata_and_parse(do)
    py_result = xtreg_fe(data, **case.python_kwargs)

    field_map = {
        "nobs": ("sample.nobs", "nobs", 1e-6, 1e-8),
        "df_model": ("fit.df_model", "df_model", 1e-6, 1e-8),
        "df_resid": ("fit.df_resid", "df_resid", 1e-6, 1e-8),
        "r2_w": ("fit.r2", "r2_w", 1e-6, 1e-8),
        "rmse": ("fit.rmse", "rmse", 1e-6, 1e-8),
        "f_stat": ("fit.f_stat", "f_stat", 1e-6, 1e-8),
    }
    report = compare_case(py_result, st_result, case, field_map)
    write_case_report(report)
    return report


def run_oos_areg_airfare() -> dict:
    case = OOSCase(
        case_id="oos_areg_airfare",
        family="linear",
        command="areg",
        dataset_key="airfare",
        dataset_path="research/data/public/panel/oos/airfare.csv",
        stata_command="areg lfare concen, absorb(id)",
        python_callable="statapy.compat.stata.areg",
        python_kwargs={"y": "lfare", "x": ["concen"], "absorb": "id", "vce": "ols"},
        description="Single absorbed route FE on airfare panel.",
    )

    data = _load_airfare()
    dta_file = STATA_CASES / "oos_airfare.dta"
    data.to_stata(str(dta_file), write_index=False)

    do = f"""
clear all
set more off
use "{dta_file}", clear
areg lfare concen, absorb(id)

display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_DF_R=" e(df_r)
display "E_DF_A=" e(df_a)
display "E_R2=" e(r2)
display "E_R2_A=" e(r2_a)
display "E_RMSE=" e(rmse)
display "E_F=" e(F)

display "COEF concen " _b[concen] " " _se[concen]
"""
    st_result = run_stata_and_parse(do)
    py_result = areg(data, **case.python_kwargs)

    field_map = {
        "nobs": ("sample.nobs", "nobs", 1e-6, 1e-8),
        "df_model": ("fit.df_model", "df_model", 1e-6, 1e-8),
        "df_resid": ("fit.df_resid", "df_resid", 1e-6, 1e-8),
        "df_a": ("fit.df_a", "df_a", 1e-6, 1e-8),
        "r2": ("fit.r2", "r2", 1e-6, 1e-8),
        "r2_adj": ("fit.r2_adj", "r2_adj", 1e-6, 1e-8),
        "rmse": ("fit.rmse", "rmse", 1e-6, 1e-8),
        "f_stat": ("fit.f_stat", "f_stat", 1e-6, 1e-8),
    }
    report = compare_case(py_result, st_result, case, field_map, skip_coefs=("_cons",))
    write_case_report(report)
    return report


def run_oos_reghdfe_airfare() -> dict:
    case = OOSCase(
        case_id="oos_reghdfe_airfare",
        family="linear",
        command="reghdfe",
        dataset_key="airfare",
        dataset_path="research/data/public/panel/oos/airfare.csv",
        stata_command="reghdfe lfare concen, absorb(id year) vce(cluster id)",
        python_callable="statapy.compat.stata.reghdfe",
        python_kwargs={"y": "lfare", "x": ["concen"], "absorb": ["id", "year"], "vce": "cluster", "cluster": "id"},
        description="Two-way FE (route + year) with route clustering on airfare panel.",
    )

    data = _load_airfare()
    dta_file = STATA_CASES / "oos_airfare.dta"
    data.to_stata(str(dta_file), write_index=False)

    do = f"""
clear all
set more off
use "{dta_file}", clear
reghdfe lfare concen, absorb(id year) vce(cluster id)

display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_DF_R=" e(df_r)
display "E_DF_A=" e(df_a)
display "E_R2=" e(r2)
display "E_R2_A=" e(r2_a)
display "E_RMSE=" e(rmse)
display "E_F=" e(F)
display "E_N_CLUST=" e(N_clust)

display "COEF concen " _b[concen] " " _se[concen]
"""
    st_result = run_stata_and_parse(do)
    py_result = reghdfe(data, **case.python_kwargs)

    field_map = {
        "nobs": ("sample.nobs", "nobs", 1e-6, 1e-8),
        "df_model": ("fit.df_model", "df_model", 1e-6, 1e-8),
        "df_resid": ("fit.df_resid", "df_resid", 1e-6, 1e-8),
        "df_a": ("fit.df_a", "df_a", 1e-6, 1e-8),
        "r2": ("fit.r2", "r2", 1e-6, 1e-8),
        "r2_adj": ("fit.r2_adj", "r2_adj", 1e-6, 1e-8),
        "rmse": ("fit.rmse", "rmse", 1e-6, 1e-8),
        "f_stat": ("fit.f_stat", "f_stat", 1e-6, 1e-8),
    }
    report = compare_case(py_result, st_result, case, field_map, skip_coefs=("_cons",))
    write_case_report(report)
    return report


def run_oos_reghdfe_airfare_factor() -> dict:
    """Stress case: factor-variable interaction with absorbed FE."""
    case = OOSCase(
        case_id="oos_reghdfe_airfare_factor",
        family="linear",
        command="reghdfe",
        dataset_key="airfare",
        dataset_path="research/data/public/panel/oos/airfare.csv",
        stata_command="reghdfe lfare i.year##c.ldist, absorb(id)",
        python_callable="statapy.compat.stata.reghdfe",
        python_kwargs={"y": "lfare", "x": ["i.year##c.ldist"], "absorb": "id", "vce": "ols"},
        description="Factor-variable full interaction (year dummies x distance) with route FE. Tests absorbed-FE collinearity behavior.",
    )

    data = _load_airfare()
    dta_file = STATA_CASES / "oos_airfare.dta"
    data.to_stata(str(dta_file), write_index=False)

    do = f"""
clear all
set more off
use "{dta_file}", clear
reghdfe lfare i.year##c.ldist, absorb(id)

display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_DF_R=" e(df_r)
display "E_DF_A=" e(df_a)
display "E_R2=" e(r2)
display "E_R2_A=" e(r2_a)
display "E_RMSE=" e(rmse)
display "E_F=" e(F)

display "COEF 1998.year " _b[1998.year] " " _se[1998.year]
display "COEF 1999.year " _b[1999.year] " " _se[1999.year]
display "COEF 2000.year " _b[2000.year] " " _se[2000.year]
display "COEF 1998.year#c.ldist " _b[1998.year#c.ldist] " " _se[1998.year#c.ldist]
display "COEF 1999.year#c.ldist " _b[1999.year#c.ldist] " " _se[1999.year#c.ldist]
display "COEF 2000.year#c.ldist " _b[2000.year#c.ldist] " " _se[2000.year#c.ldist]
"""
    st_result = run_stata_and_parse(do)
    py_result = reghdfe(data, **case.python_kwargs)

    field_map = {
        "nobs": ("sample.nobs", "nobs", 1e-6, 1e-8),
        "df_model": ("fit.df_model", "df_model", 1e-6, 1e-8),
        "df_resid": ("fit.df_resid", "df_resid", 1e-6, 1e-8),
        "df_a": ("fit.df_a", "df_a", 1e-6, 1e-8),
        "r2": ("fit.r2", "r2", 1e-6, 1e-8),
        "r2_adj": ("fit.r2_adj", "r2_adj", 1e-6, 1e-8),
        "rmse": ("fit.rmse", "rmse", 1e-6, 1e-8),
        "f_stat": ("fit.f_stat", "f_stat", 1e-6, 1e-8),
    }
    report = compare_case(py_result, st_result, case, field_map, skip_coefs=("_cons",))
    write_case_report(report)
    return report


if __name__ == "__main__":
    reports = []
    for fn in [
        run_oos_regress_airfare,
        run_oos_xtreg_fe_airfare,
        run_oos_areg_airfare,
        run_oos_reghdfe_airfare,
        run_oos_reghdfe_airfare_factor,
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
    write_family_summary("linear", reports)
    print("Linear family OOS complete.")
