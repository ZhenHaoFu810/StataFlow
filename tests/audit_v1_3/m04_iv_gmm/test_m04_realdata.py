"""M04 IV/GMM: real-data dual-run experiments on Grunfeld."""

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

from stataflow import IV2SLS, IVAbsorbingOLS


def _do_ivregress(data_csv: str, cmd: str, test_id: str) -> dict:
    do = f'''clear all
set more off
import delimited "{data_csv}", varnames(1) clear
{cmd}
display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_DF_R=" e(df_r)
display "E_R2=" e(r2)
display "E_R2_A=" e(r2_a)
display "E_RMSE=" e(rmse)
display "E_F=" e(F)
display "E_F_P=" Ftail(e(df_m), e(df_r), e(F))
if e(N_clust) < . {{
    display "E_N_CLUST=" e(N_clust)
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
    return run_stata_do(do, test_id)


def _do_ivreghdfe(data_csv: str, cmd: str, test_id: str) -> dict:
    do = f'''clear all
set more off
import delimited "{data_csv}", varnames(1) clear
which ivreghdfe
{cmd}
display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_DF_R=" e(df_r)
display "E_R2=" e(r2)
display "E_R2_A=" e(r2_a)
display "E_RMSE=" e(rmse)
display "E_F=" e(F)
display "E_F_P=" Ftail(e(df_m), e(df_r), e(F))
display "E_DF_A=" e(df_a)
if e(N_clust) < . {{
    display "E_N_CLUST=" e(N_clust)
}}
if e(widstat) < . {{
    display "E_WIDSTAT=" e(widstat)
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
    return run_stata_do(do, test_id)


def experiment_r1_grunfeld_ivregress():
    """R1: Grunfeld 2SLS with ivregress."""
    test_id = "R1_grunfeld_ivregress"
    d = ds.grunfeld.load()
    df = d.data.copy()
    df = df.rename(columns={"value": "mvalue", "capital": "kstock"})
    df["firm_id"] = df["firm"].astype("category").cat.codes + 1
    df["year"] = df["year"].astype(int)

    csv = STATA_CASES / f"{test_id}.csv"
    df.to_csv(csv, index=False)

    st = _do_ivregress(str(csv), "ivregress 2sls invest (mvalue = kstock), robust", test_id)
    py = python_result_to_dict(IV2SLS(df, y="invest", x_exog=[], x_endog=["mvalue"], instruments=["kstock"], add_constant=True).fit(vce="robust"))

    comparisons = []
    comparisons.extend(compare_coefficients(py["coefficients"], st.get("coefficients", [])))
    for field in ["nobs", "df_model", "df_resid", "r2", "r2_adj", "rmse", "f_stat", "f_pvalue"]:
        comparisons.append(compare_scalars(py[field], st.get(field), field))
    comparisons.extend(compare_vce(py["vce"], st.get("vce", np.zeros((0, 0))), py["vce_row_names"], [c["name"] for c in st.get("coefficients", [])]))

    save_evidence(test_id, py, st, comparisons, data=df)
    return all(p for p, _ in comparisons), comparisons


def experiment_r2_grunfeld_ivreghdfe():
    """R2: Grunfeld ivreghdfe with firm/year FE + cluster."""
    test_id = "R2_grunfeld_ivreghdfe"
    d = ds.grunfeld.load()
    df = d.data.copy()
    df = df.rename(columns={"value": "mvalue", "capital": "kstock"})
    df["firm_id"] = df["firm"].astype("category").cat.codes + 1
    df["year"] = df["year"].astype(int)

    csv = STATA_CASES / f"{test_id}.csv"
    df.to_csv(csv, index=False)

    st = _do_ivreghdfe(str(csv), "ivreghdfe invest (mvalue = kstock), absorb(firm_id year) cluster(firm_id)", test_id)
    py = python_result_to_dict(IVAbsorbingOLS(df, y="invest", x_exog=[], x_endog=["mvalue"], instruments=["kstock"], absorb=["firm_id", "year"], add_constant=True, drop_singletons=True).fit(vce="cluster", cluster="firm_id"))

    comparisons = []
    comparisons.extend(compare_coefficients(py["coefficients"], st.get("coefficients", [])))
    for field in ["nobs", "df_model", "df_resid", "df_a", "r2", "r2_adj", "rmse", "f_stat", "f_pvalue", "cluster_count", "widstat"]:
        py_field = py.get("cluster_count" if field == "cluster_count" else field)
        st_field = st.get("n_clust" if field == "cluster_count" else field)
        comparisons.append(compare_scalars(py_field, st_field, field))
    comparisons.extend(compare_vce(py["vce"], st.get("vce", np.zeros((0, 0))), py["vce_row_names"], [c["name"] for c in st.get("coefficients", [])]))

    save_evidence(test_id, py, st, comparisons, data=df)
    return all(p for p, _ in comparisons), comparisons


def main():
    experiments = [experiment_r1_grunfeld_ivregress, experiment_r2_grunfeld_ivreghdfe]
    summary = []
    for exp in experiments:
        print(f"\n=== Running {exp.__name__} ===")
        try:
            passed, comparisons = exp()
            fails = [m for p, m in comparisons if not p]
            print(f"Overall: {'PASS' if passed else 'FAIL'}")
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
