"""M02 Panel/FE: two new independent real-data dual-run experiments."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.datasets as ds

sys.path.insert(0, str(Path(__file__).parent))
from audit_utils import (
    STATA_CASES,
    run_stata_do,
    python_result_to_dict,
    compare_scalars,
    compare_coefficients,
    compare_vce,
    save_evidence,
)

from stataflow import FixedEffectsOLS


def _stata_do_template(data_csv: str, cmd: str) -> str:
    return f'''clear all
set more off

import delimited "{data_csv}", varnames(1) clear

{cmd}

* Scalar fields
display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_DF_R=" e(df_r)
display "E_R2=" e(r2)
display "E_R2_A=" e(r2_a)
display "E_RMSE=" e(rmse)
display "E_F=" e(F)
local test_df = e(df_m)
if `test_df' <= 0 local test_df = colsof(e(b)) - 1
display "E_F_P=" Ftail(`test_df', e(df_r), e(F))
display "E_RSS=" e(rss)
display "E_MSS=" e(mss)
if e(N_g) < . {{
    display "E_N_G=" e(N_g)
}}
if e(N_clust) < . {{
    display "E_N_CLUST=" e(N_clust)
}}

* Coefficients and full VCE
local coefs : colnames e(b)
local k : word count `coefs'
forvalues i = 1/`k' {{
    local name : word `i' of `coefs'
    local b = _b[`name']
    local se = _se[`name']
    display "COEF `name' " %21.15e `b' " " %21.15e `se'
}}

* VCE matrix (full)
matrix V = e(V)
forvalues i = 1/`k' {{
    forvalues j = 1/`k' {{
        display "VCE " (`i'-1) " " (`j'-1) " " %21.15e V[`i',`j']
    }}
}}
'''


def experiment_r1_grunfeld_fe_cluster():
    """R1: Grunfeld panel with FE + cluster.

    Differs from old golden test_v1_xtreg_fe_real_grunfeld.py which used
    conventional VCE with two regressors.
    """
    test_id = "R1_grunfeld_fe_cluster"
    d = ds.grunfeld.load()
    df = d.data.copy()
    df = df.rename(columns={"value": "mvalue", "capital": "kstock"})
    df["firm_id"] = df["firm"].astype("category").cat.codes + 1
    df["year"] = df["year"].astype(int)

    data_csv = STATA_CASES / f"{test_id}.csv"
    df.to_csv(data_csv, index=False)

    stata_cmd = "xtset firm_id year\nxtreg invest mvalue, fe cluster(firm_id)"
    st_result = run_stata_do(_stata_do_template(str(data_csv), stata_cmd), test_id)

    py_result = FixedEffectsOLS(df, y="invest", x=["mvalue"], fe="firm_id", add_constant=True).fit(vce="cluster", cluster="firm_id")
    py_dict = python_result_to_dict(py_result)

    comparisons = []
    comparisons.extend(compare_coefficients(py_dict["coefficients"], st_result.get("coefficients", [])))
    for field in ["nobs", "df_model", "df_resid", "r2", "r2_adj", "rmse", "f_stat", "f_pvalue", "cluster_count"]:
        py_field = py_dict.get(field if field != "cluster_count" else "cluster_count")
        st_field = st_result.get("n_clust" if field == "cluster_count" else field)
        comparisons.append(compare_scalars(py_field, st_field, field))
    comparisons.extend(compare_vce(py_dict["vce"], st_result.get("vce", np.zeros((0, 0))), py_dict["vce_row_names"], [c["name"] for c in st_result.get("coefficients", [])]))

    save_evidence(test_id, py_dict, st_result, comparisons, data=df)
    return all(p for p, _ in comparisons), comparisons


def experiment_r2_grunfeld_two_way_fe():
    """R2: Grunfeld with entity and time FE (two-way within)."""
    test_id = "R2_grunfeld_two_way_fe"
    d = ds.grunfeld.load()
    df = d.data.copy()
    # Create time dummies manually for Python; Stata uses i.year
    df = df.rename(columns={"value": "mvalue", "capital": "kstock"})
    df["firm_id"] = df["firm"].astype("category").cat.codes + 1
    df["year"] = df["year"].astype(int)

    data_csv = STATA_CASES / f"{test_id}.csv"
    df.to_csv(data_csv, index=False)

    # Stata: absorb two-way FE using reghdfe or xtreg, fe with i.year
    # Use xtreg, fe with i.year (time dummies)
    stata_cmd = "xtset firm_id year\nxtreg invest mvalue i.year, fe"
    st_result = run_stata_do(_stata_do_template(str(data_csv), stata_cmd), test_id)

    # Python: absorb firm and include year dummies
    years = sorted(df["year"].unique())
    base_year = years[0]
    year_cols = [f"{int(y)}.year" for y in years[1:]]
    for y in years[1:]:
        df[f"{int(y)}.year"] = (df["year"] == y).astype(int)
    x_vars = ["mvalue"] + year_cols
    py_result = FixedEffectsOLS(df, y="invest", x=x_vars, fe="firm_id", add_constant=True).fit(vce="ols")
    py_dict = python_result_to_dict(py_result)

    comparisons = []
    comparisons.extend(compare_coefficients(py_dict["coefficients"], st_result.get("coefficients", [])))
    for field in ["nobs", "df_model", "df_resid", "r2", "r2_adj", "rmse", "f_stat", "f_pvalue"]:
        comparisons.append(compare_scalars(py_dict[field], st_result.get(field), field))

    save_evidence(test_id, py_dict, st_result, comparisons, data=df)
    return all(p for p, _ in comparisons), comparisons


def main():
    experiments = [
        experiment_r1_grunfeld_fe_cluster,
        experiment_r2_grunfeld_two_way_fe,
    ]
    summary = []
    for exp in experiments:
        print(f"\n=== Running {exp.__name__} ===")
        try:
            passed, comparisons = exp()
            fails = [m for p, m in comparisons if not p]
            print(f"Overall: {'PASS' if passed else 'FAIL'}")
            if fails:
                print("Failures:")
                for f in fails[:10]:
                    print("  ", f)
            summary.append((exp.__name__, passed, len(fails)))
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
            summary.append((exp.__name__, False, -1))

    print("\n=== Summary ===")
    for name, passed, fails in summary:
        print(f"{name}: {'PASS' if passed else 'FAIL'} (fails={fails})")


if __name__ == "__main__":
    main()
