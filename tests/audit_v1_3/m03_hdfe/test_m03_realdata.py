"""M03 HDFE: two new independent real-data dual-run experiments."""

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

from stataflow import AbsorbingOLS


def _stata_do_template(data_csv: str, cmd: str) -> str:
    return f'''clear all
set more off
import delimited "{data_csv}", varnames(1) clear
which reghdfe
{cmd}
display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_DF_R=" e(df_r)
display "E_R2=" e(r2)
display "E_R2_A=" e(r2_a)
display "E_RMSE=" e(rmse)
display "E_F=" e(F)
display "E_F_P=" Ftail(e(df_m), e(df_r), e(F))
display "E_RSS=" e(rss)
display "E_MSS=" e(mss)
display "E_DF_A=" e(df_a)
if e(N_clust) < . {{
    display "E_N_CLUST=" e(N_clust)
}}
if e(num_singletons) < . {{
    display "E_N_SINGLETONS=" e(num_singletons)
}}
local coefs : colnames e(b)
local k : word count `coefs'
forvalues i = 1/`k' {{
    local name : word `i' of `coefs'
    display "COEF `name' " %21.15e _b[`name'] " " %21.15e _se[`name']
}}
matrix V = e(V)
forvalues i = 1/`k' {{
    forvalues j = 1/`k' {{
        display "VCE " (`i'-1) " " (`j'-1) " " %21.15e V[`i',`j']
    }}
}}
'''


def experiment_r1_grunfeld_2fe_cluster():
    """R1: Grunfeld with firm and year FE + cluster."""
    test_id = "R1_grunfeld_2fe_cluster"
    d = ds.grunfeld.load()
    df = d.data.copy()
    df = df.rename(columns={"value": "mvalue", "capital": "kstock"})
    df["firm_id"] = df["firm"].astype("category").cat.codes + 1
    df["year"] = df["year"].astype(int)

    data_csv = STATA_CASES / f"{test_id}.csv"
    df.to_csv(data_csv, index=False)

    stata_cmd = "reghdfe invest mvalue, absorb(firm_id year) vce(cluster firm_id)"
    st_result = run_stata_do(_stata_do_template(str(data_csv), stata_cmd), test_id)

    py_result = AbsorbingOLS(df, y="invest", x=["mvalue"], absorb=["firm_id", "year"], add_constant=True, drop_singletons=True).fit(vce="cluster", cluster="firm_id")
    py_dict = python_result_to_dict(py_result)

    comparisons = []
    comparisons.extend(compare_coefficients(py_dict["coefficients"], st_result.get("coefficients", [])))
    for field in ["nobs", "df_model", "df_resid", "df_a", "r2", "r2_adj", "rmse", "f_stat", "f_pvalue", "cluster_count"]:
        py_field = py_dict.get("cluster_count" if field == "cluster_count" else field)
        st_field = st_result.get("n_clust" if field == "cluster_count" else field)
        comparisons.append(compare_scalars(py_field, st_field, field))
    comparisons.extend(compare_vce(py_dict["vce"], st_result.get("vce", np.zeros((0, 0))), py_dict["vce_row_names"], [c["name"] for c in st_result.get("coefficients", [])]))

    save_evidence(test_id, py_dict, st_result, comparisons, data=df)
    return all(p for p, _ in comparisons), comparisons


def experiment_r2_grunfeld_slope():
    """R2: Grunfeld with firm intercept + firm-specific time slope."""
    test_id = "R2_grunfeld_slope"
    d = ds.grunfeld.load()
    df = d.data.copy()
    df = df.rename(columns={"value": "mvalue", "capital": "kstock"})
    df["firm_id"] = df["firm"].astype("category").cat.codes + 1
    df["year"] = df["year"].astype(int)

    data_csv = STATA_CASES / f"{test_id}.csv"
    df.to_csv(data_csv, index=False)

    stata_cmd = "reghdfe invest mvalue, absorb(firm_id##c.year) vce(cluster firm_id)"
    st_result = run_stata_do(_stata_do_template(str(data_csv), stata_cmd), test_id)

    from stataflow.estimators._absorb_spec import AbsorbSpec
    py_result = AbsorbingOLS(df, y="invest", x=["mvalue"], absorb=[AbsorbSpec(var="firm_id", slopes=["year"], has_intercept=True)], add_constant=True, drop_singletons=True).fit(vce="cluster", cluster="firm_id")
    py_dict = python_result_to_dict(py_result)

    comparisons = []
    comparisons.extend(compare_coefficients(py_dict["coefficients"], st_result.get("coefficients", [])))
    for field in ["nobs", "df_model", "df_resid", "df_a", "r2", "r2_adj", "rmse", "f_stat", "f_pvalue", "cluster_count"]:
        py_field = py_dict.get("cluster_count" if field == "cluster_count" else field)
        st_field = st_result.get("n_clust" if field == "cluster_count" else field)
        comparisons.append(compare_scalars(py_field, st_field, field))
    comparisons.extend(compare_vce(py_dict["vce"], st_result.get("vce", np.zeros((0, 0))), py_dict["vce_row_names"], [c["name"] for c in st_result.get("coefficients", [])]))

    save_evidence(test_id, py_dict, st_result, comparisons, data=df)
    return all(p for p, _ in comparisons), comparisons


def main():
    experiments = [
        experiment_r1_grunfeld_2fe_cluster,
        experiment_r2_grunfeld_slope,
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
