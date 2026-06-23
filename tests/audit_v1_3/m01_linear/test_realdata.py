"""M01 Linear: two new independent real-data dual-run experiments.

Datasets are publicly available through statsmodels.
"""

from __future__ import annotations

import hashlib
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

from stataflow.compat.stata import regress


def _stata_do_template(data_csv: str, cmd: str) -> str:
    """Return a Stata .do template that outputs parseable fields."""
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
display "E_F_P=" Ftail(e(df_m), e(df_r), e(F))
display "E_RSS=" e(rss)
display "E_MSS=" e(mss)
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
    display "COEF `name' " `b' " " `se'
}}

* VCE matrix (full)
matrix V = e(V)
forvalues i = 1/`k' {{
    forvalues j = 1/`k' {{
        display "VCE " (`i'-1) " " (`j'-1) " " V[`i',`j']
    }}
}}
'''


def _df_hash(df: pd.DataFrame) -> str:
    return hashlib.sha256(pd.util.hash_pandas_object(df).values.tobytes()).hexdigest()[:16]


def experiment_r1_engel_robust():
    """R1: Engel food expenditure data, OLS + robust VCE.

    Source: statsmodels.datasets.engel (public domain / classic dataset).
    Research question: food expenditure ~ income.
    """
    test_id = "R1_engel_robust"
    d = ds.engel.load()
    df = d.data.copy()
    df = df.rename(columns={"income": "income", "foodexp": "foodexp"})

    data_csv = STATA_CASES / f"{test_id}.csv"
    df.to_csv(data_csv, index=False)

    stata_cmd = "regress foodexp income, robust"
    st_result = run_stata_do(_stata_do_template(str(data_csv), stata_cmd), test_id)

    py_result = regress(df, y="foodexp", x=["income"], vce="robust")
    py_dict = python_result_to_dict(py_result)

    comparisons = []
    comparisons.extend(compare_coefficients(py_dict["coefficients"], st_result.get("coefficients", [])))
    for field in ["nobs", "df_model", "df_resid", "r2", "r2_adj", "rmse", "f_stat", "f_pvalue", "rss", "tss"]:
        comparisons.append(compare_scalars(py_dict[field], st_result.get(field), field))
    comparisons.extend(compare_vce(py_dict["vce"], st_result.get("vce", np.zeros((0, 0))), py_dict["vce_row_names"], [c["name"] for c in st_result.get("coefficients", [])]))

    save_evidence(test_id, py_dict, st_result, comparisons, data=df)
    return all(p for p, _ in comparisons), comparisons


def experiment_r2_modechoice_two_way_cluster():
    """R2: Mode choice data with two-way clustering (individual x mode).

    Source: statsmodels.datasets.modechoice (public / transport mode choice).
    Research question: linear probability model of choice ~ trip attributes,
    clustered by individual and by travel mode.
    """
    test_id = "R2_modechoice_two_way_cluster"
    d = ds.modechoice.load()
    df = d.data.copy()

    # Ensure cluster variables are integer-coded for cleaner Stata output
    df["individual"] = df["individual"].astype(int)
    df["mode"] = df["mode"].astype("category").cat.codes.astype(int)

    # Dependent and regressors (linear probability model)
    y = "choice"
    x = ["ttme", "invc", "invt", "gc", "hinc"]

    data_csv = STATA_CASES / f"{test_id}.csv"
    df.to_csv(data_csv, index=False)

    stata_cmd = "regress choice ttme invc invt gc hinc, vce(cluster individual mode)"
    st_result = run_stata_do(_stata_do_template(str(data_csv), stata_cmd), test_id)

    py_result = regress(df, y=y, x=x, vce="cluster", cluster=["individual", "mode"])
    py_dict = python_result_to_dict(py_result)

    comparisons = []
    comparisons.extend(compare_coefficients(py_dict["coefficients"], st_result.get("coefficients", [])))
    for field in ["nobs", "df_model", "df_resid", "r2", "r2_adj", "rmse", "f_stat", "f_pvalue", "cluster_count"]:
        py_field = py_dict.get(field if field != "cluster_count" else "cluster_count")
        st_field = st_result.get("n_clust" if field == "cluster_count" else field)
        if field == "cluster_count" and st_field is None and st_result.get("df_resid") is not None:
            # Multiway regress posts min(G)-1 as e(df_r), but no scalar e(N_clust).
            st_field = st_result["df_resid"] + 1
        comparisons.append(compare_scalars(py_field, st_field, field))
    comparisons.extend(compare_vce(py_dict["vce"], st_result.get("vce", np.zeros((0, 0))), py_dict["vce_row_names"], [c["name"] for c in st_result.get("coefficients", [])]))

    save_evidence(test_id, py_dict, st_result, comparisons, data=df)
    return all(p for p, _ in comparisons), comparisons


def main():
    experiments = [
        experiment_r1_engel_robust,
        experiment_r2_modechoice_two_way_cluster,
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
