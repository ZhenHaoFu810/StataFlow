"""OOS validation runner for GLM family (logit, probit, poisson, ppmlhdfe).

Datasets:
- vote1 (new OOS binary data)
- smoke (new OOS binary/count data)
- fertil1 (new OOS count/panel data)
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
from statapy.compat.stata import logit, poisson, ppmlhdfe, probit


def _load_vote1() -> pd.DataFrame:
    return pd.read_csv(PROJECT_ROOT / "research/data/public/binary/oos/vote1.csv")


def _load_smoke() -> pd.DataFrame:
    return pd.read_csv(PROJECT_ROOT / "research/data/public/binary/oos/smoke.csv")


def _load_fertil1() -> pd.DataFrame:
    return pd.read_csv(PROJECT_ROOT / "research/data/public/count/oos/fertil1.csv")


def run_oos_logit_vote1() -> dict:
    case = OOSCase(
        case_id="oos_logit_vote1",
        family="glm",
        command="logit",
        dataset_key="vote1",
        dataset_path="research/data/public/binary/oos/vote1.csv",
        stata_command="logit democA lexpendA lexpendB prtystrA",
        python_callable="statapy.compat.stata.logit",
        python_kwargs={"y": "democA", "x": ["lexpendA", "lexpendB", "prtystrA"], "vce": "ols"},
        description="Binary logit on congressional election data (incumbent party win).",
    )

    data = _load_vote1()
    dta_file = STATA_CASES / "oos_vote1.dta"
    data.to_stata(str(dta_file), write_index=False)

    do = f"""
clear all
set more off
use "{dta_file}", clear
logit democA lexpendA lexpendB prtystrA

display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_LL=" e(ll)
display "E_CHI2=" e(chi2)

display "COEF lexpendA " _b[lexpendA] " " _se[lexpendA]
display "COEF lexpendB " _b[lexpendB] " " _se[lexpendB]
display "COEF prtystrA " _b[prtystrA] " " _se[prtystrA]
display "COEF _cons " _b[_cons] " " _se[_cons]
"""
    st_result = run_stata_and_parse(do)
    py_result = logit(data, **case.python_kwargs)

    field_map = {
        "nobs": ("sample.nobs", "nobs", 1e-6, 1e-8),
        "df_model": ("fit.df_model", "df_model", 1e-6, 1e-8),
        "ll": ("fit.ll", "ll", 1e-6, 1e-8),
        "chi2": ("fit.f_stat", "chi2", 1e-6, 1e-8),
    }
    report = compare_case(py_result, st_result, case, field_map)
    write_case_report(report)
    return report


def run_oos_probit_vote1() -> dict:
    case = OOSCase(
        case_id="oos_probit_vote1",
        family="glm",
        command="probit",
        dataset_key="vote1",
        dataset_path="research/data/public/binary/oos/vote1.csv",
        stata_command="probit democA lexpendA lexpendB prtystrA",
        python_callable="statapy.compat.stata.probit",
        python_kwargs={"y": "democA", "x": ["lexpendA", "lexpendB", "prtystrA"], "vce": "ols"},
        description="Binary probit on congressional election data.",
    )

    data = _load_vote1()
    dta_file = STATA_CASES / "oos_vote1.dta"
    data.to_stata(str(dta_file), write_index=False)

    do = f"""
clear all
set more off
use "{dta_file}", clear
probit democA lexpendA lexpendB prtystrA

display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_LL=" e(ll)
display "E_CHI2=" e(chi2)

display "COEF lexpendA " _b[lexpendA] " " _se[lexpendA]
display "COEF lexpendB " _b[lexpendB] " " _se[lexpendB]
display "COEF prtystrA " _b[prtystrA] " " _se[prtystrA]
display "COEF _cons " _b[_cons] " " _se[_cons]
"""
    st_result = run_stata_and_parse(do)
    py_result = probit(data, **case.python_kwargs)

    field_map = {
        "nobs": ("sample.nobs", "nobs", 1e-6, 1e-8),
        "df_model": ("fit.df_model", "df_model", 1e-6, 1e-8),
        "ll": ("fit.ll", "ll", 1e-6, 1e-8),
        "chi2": ("fit.f_stat", "chi2", 1e-6, 1e-8),
    }
    report = compare_case(py_result, st_result, case, field_map)
    write_case_report(report)
    return report


def run_oos_poisson_fertil1() -> dict:
    case = OOSCase(
        case_id="oos_poisson_fertil1",
        family="glm",
        command="poisson",
        dataset_key="fertil1",
        dataset_path="research/data/public/count/oos/fertil1.csv",
        stata_command="poisson kids educ age agesq black",
        python_callable="statapy.compat.stata.poisson",
        python_kwargs={
            "y": "kids",
            "x": ["educ", "age", "agesq", "black"],
            "vce": "ols",
        },
        description="Count-model Poisson on fertility panel (cross-sectional use of year-pooled data).",
    )

    data = _load_fertil1()
    dta_file = STATA_CASES / "oos_fertil1.dta"
    data.to_stata(str(dta_file), write_index=False)

    do = f"""
clear all
set more off
use "{dta_file}", clear
poisson kids educ age agesq black

display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_LL=" e(ll)
display "E_CHI2=" e(chi2)

display "COEF educ " _b[educ] " " _se[educ]
display "COEF age " _b[age] " " _se[age]
display "COEF agesq " _b[agesq] " " _se[agesq]
display "COEF black " _b[black] " " _se[black]
display "COEF _cons " _b[_cons] " " _se[_cons]
"""
    st_result = run_stata_and_parse(do)
    py_result = poisson(data, **case.python_kwargs)

    field_map = {
        "nobs": ("sample.nobs", "nobs", 1e-6, 1e-8),
        "df_model": ("fit.df_model", "df_model", 1e-6, 1e-8),
        "ll": ("fit.ll", "ll", 1e-6, 1e-8),
        "chi2": ("fit.f_stat", "chi2", 1e-6, 1e-8),
    }
    report = compare_case(py_result, st_result, case, field_map)
    write_case_report(report)
    return report


def run_oos_ppmlhdfe_fertil1() -> dict:
    """Stress case: zero-heavy count panel with year FE."""
    case = OOSCase(
        case_id="oos_ppmlhdfe_fertil1",
        family="glm",
        command="ppmlhdfe",
        dataset_key="fertil1",
        dataset_path="research/data/public/count/oos/fertil1.csv",
        stata_command="ppmlhdfe kids educ age agesq black, absorb(year) vce(robust)",
        python_callable="statapy.compat.stata.ppmlhdfe",
        python_kwargs={
            "y": "kids",
            "x": ["educ", "age", "agesq", "black"],
            "absorb": ["year"],
            "vce": "robust",
        },
        description="PPML-HDFE on fertility count data with year fixed effects.",
    )

    data = _load_fertil1()
    dta_file = STATA_CASES / "oos_fertil1.dta"
    data.to_stata(str(dta_file), write_index=False)

    do = f"""
clear all
set more off
use "{dta_file}", clear
ppmlhdfe kids educ age agesq black, absorb(year)

display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_DF_A=" e(df_a)
display "E_LL=" e(ll)

display "COEF educ " _b[educ] " " _se[educ]
display "COEF age " _b[age] " " _se[age]
display "COEF agesq " _b[agesq] " " _se[agesq]
display "COEF black " _b[black] " " _se[black]
"""
    st_result = run_stata_and_parse(do)
    py_result = ppmlhdfe(data, **case.python_kwargs)

    field_map = {
        "nobs": ("sample.nobs", "nobs", 1e-6, 1e-8),
        "df_model": ("fit.df_model", "df_model", 1e-6, 1e-8),
        "df_a": ("fit.df_a", "df_a", 1e-6, 1e-8),
        "ll": ("fit.ll", "ll", 1e-6, 1e-8),
    }
    report = compare_case(py_result, st_result, case, field_map, skip_coefs=("_cons",))
    write_case_report(report)
    return report


def run_oos_logit_smoke_factor() -> dict:
    """Stress case: logit with factor-variable interaction."""
    case = OOSCase(
        case_id="oos_logit_smoke_factor",
        family="glm",
        command="logit",
        dataset_key="smoke",
        dataset_path="research/data/public/binary/oos/smoke.csv",
        stata_command="logit smoker educ age i.white##c.income",
        python_callable="statapy.compat.stata.logit",
        python_kwargs={"y": "smoker", "x": ["educ", "age", "i.white##c.income"], "vce": "ols"},
        description="Logit with categorical-continuous full interaction on smoking data (smoker = cigs > 0).",
    )

    data = _load_smoke()
    data["smoker"] = (data["cigs"] > 0).astype(int)
    dta_file = STATA_CASES / "oos_smoke.dta"
    data.to_stata(str(dta_file), write_index=False)

    do = f"""
clear all
set more off
use "{dta_file}", clear
logit smoker educ age i.white##c.income

display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_LL=" e(ll)
display "E_CHI2=" e(chi2)

display "COEF educ " _b[educ] " " _se[educ]
display "COEF age " _b[age] " " _se[age]
display "COEF 1.white " _b[1.white] " " _se[1.white]
display "COEF income " _b[income] " " _se[income]
display "COEF 1.white#c.income " _b[1.white#c.income] " " _se[1.white#c.income]
display "COEF _cons " _b[_cons] " " _se[_cons]
"""
    st_result = run_stata_and_parse(do)
    py_result = logit(data, **case.python_kwargs)

    field_map = {
        "nobs": ("sample.nobs", "nobs", 1e-6, 1e-8),
        "df_model": ("fit.df_model", "df_model", 1e-6, 1e-8),
        "ll": ("fit.ll", "ll", 1e-6, 1e-8),
        "chi2": ("fit.f_stat", "chi2", 1e-6, 1e-8),
    }
    report = compare_case(py_result, st_result, case, field_map)
    write_case_report(report)
    return report


if __name__ == "__main__":
    reports = []
    for fn in [
        run_oos_logit_vote1,
        run_oos_probit_vote1,
        run_oos_poisson_fertil1,
        run_oos_ppmlhdfe_fertil1,
        run_oos_logit_smoke_factor,
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
    write_family_summary("glm", reports)
    print("GLM family OOS complete.")
