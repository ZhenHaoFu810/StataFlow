"""M01 Linear: three metamorphic/property tests.

Each property is verified in both Python and Stata, or against a theoretical
prediction derived from both.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

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


def property_p1_row_order_invariance():
    """P1: Random row reordering should not change estimates.

    Property: for a fixed dataset, permuting rows leaves coefficients,
    VCE, and fit statistics unchanged (up to floating-point noise).
    """
    test_id = "P1_row_order_invariance"
    rng = np.random.default_rng(2026061301)
    n = 200
    x1 = rng.normal(size=n)
    x2 = rng.normal(size=n)
    y = 1.0 + 2.0 * x1 - 1.5 * x2 + rng.normal(scale=0.5, size=n)
    df = pd.DataFrame({"y": y, "x1": x1, "x2": x2})

    # Reordered version
    perm = rng.permutation(n)
    df_perm = df.iloc[perm].reset_index(drop=True)

    data_csv = STATA_CASES / f"{test_id}.csv"
    df.to_csv(data_csv, index=False)
    data_csv_perm = STATA_CASES / f"{test_id}_perm.csv"
    df_perm.to_csv(data_csv_perm, index=False)

    cmd = "regress y x1 x2, robust"
    st_base = run_stata_do(_stata_do_template(str(data_csv), cmd), f"{test_id}_base")
    st_perm = run_stata_do(_stata_do_template(str(data_csv_perm), cmd), f"{test_id}_perm")

    py_base = regress(df, y="y", x=["x1", "x2"], vce="robust")
    py_perm = regress(df_perm, y="y", x=["x1", "x2"], vce="robust")
    py_base_dict = python_result_to_dict(py_base)
    py_perm_dict = python_result_to_dict(py_perm)

    comparisons = []
    # Compare Stata base vs perm
    comparisons.extend(compare_coefficients(
        [{"name": c["name"], "beta": c["beta"], "std_err": c["std_err"]} for c in st_base.get("coefficients", [])],
        st_perm.get("coefficients", [])
    ))
    # Compare Python base vs perm
    comparisons.extend(compare_coefficients(py_base_dict["coefficients"], py_perm_dict["coefficients"]))

    save_evidence(test_id, py_base_dict, st_base, comparisons, data=df)
    return all(p for p, _ in comparisons), comparisons


def property_p2_irrelevant_column():
    """P2: Adding an irrelevant column (with missing values) should not change results.

    Property: a variable not included in the regression, even if it contains
    missing values, should not affect the estimation sample or estimates.
    """
    test_id = "P2_irrelevant_column"
    rng = np.random.default_rng(2026061302)
    n = 200
    x = rng.normal(size=n)
    y = 1.0 + 2.0 * x + rng.normal(scale=0.5, size=n)
    df = pd.DataFrame({"y": y, "x": x})
    df_with_z = df.copy()
    df_with_z["z"] = np.nan  # irrelevant, all missing

    data_csv = STATA_CASES / f"{test_id}.csv"
    df.to_csv(data_csv, index=False)
    data_csv_z = STATA_CASES / f"{test_id}_z.csv"
    df_with_z.to_csv(data_csv_z, index=False)

    cmd = "regress y x"
    st_base = run_stata_do(_stata_do_template(str(data_csv), cmd), f"{test_id}_base")
    st_z = run_stata_do(_stata_do_template(str(data_csv_z), cmd), f"{test_id}_z")

    py_base = regress(df, y="y", x=["x"])
    py_z = regress(df_with_z, y="y", x=["x"])
    py_base_dict = python_result_to_dict(py_base)
    py_z_dict = python_result_to_dict(py_z)

    comparisons = []
    comparisons.extend(compare_coefficients(st_base.get("coefficients", []), st_z.get("coefficients", [])))
    comparisons.extend(compare_coefficients(py_base_dict["coefficients"], py_z_dict["coefficients"]))
    comparisons.append(compare_scalars(py_base_dict["nobs"], py_z_dict["nobs"], "python_nobs"))
    comparisons.append(compare_scalars(st_base.get("nobs"), st_z.get("nobs"), "stata_nobs"))

    save_evidence(test_id, py_base_dict, st_base, comparisons, data=df)
    return all(p for p, _ in comparisons), comparisons


def property_p3_scale_transformation():
    """P3: Scaling a regressor by 10 scales its coefficient and SE by 1/10.

    Property: multiplying x by 10 should leave the constant unchanged and
    divide the coefficient and standard error of x by 10.
    """
    test_id = "P3_scale_transformation"
    rng = np.random.default_rng(2026061303)
    n = 200
    x = rng.normal(size=n)
    y = 1.0 + 2.0 * x + rng.normal(scale=0.5, size=n)
    df = pd.DataFrame({"y": y, "x": x})
    df_scaled = df.copy()
    df_scaled["x10"] = df_scaled["x"] * 10.0

    data_csv = STATA_CASES / f"{test_id}.csv"
    df.to_csv(data_csv, index=False)
    data_csv_scaled = STATA_CASES / f"{test_id}_scaled.csv"
    df_scaled.to_csv(data_csv_scaled, index=False)

    cmd_base = "regress y x"
    cmd_scaled = "regress y x10"
    st_base = run_stata_do(_stata_do_template(str(data_csv), cmd_base), f"{test_id}_base")
    st_scaled = run_stata_do(_stata_do_template(str(data_csv_scaled), cmd_scaled), f"{test_id}_scaled")

    py_base = regress(df, y="y", x=["x"])
    py_scaled = regress(df_scaled, y="y", x=["x10"])
    py_base_dict = python_result_to_dict(py_base)
    py_scaled_dict = python_result_to_dict(py_scaled)

    comparisons = []

    # Stata: x10 beta should be x beta / 10
    st_base_x = next(c for c in st_base["coefficients"] if c["name"] == "x")
    st_scaled_x10 = next(c for c in st_scaled["coefficients"] if c["name"] == "x10")
    comparisons.append(compare_scalars(st_scaled_x10["beta"], st_base_x["beta"] / 10.0, "stata_x10_beta_scale"))
    comparisons.append(compare_scalars(st_scaled_x10["std_err"], st_base_x["std_err"] / 10.0, "stata_x10_se_scale"))

    # Python: same
    py_base_x = next(c for c in py_base_dict["coefficients"] if c["name"] == "x")
    py_scaled_x10 = next(c for c in py_scaled_dict["coefficients"] if c["name"] == "x10")
    comparisons.append(compare_scalars(py_scaled_x10["beta"], py_base_x["beta"] / 10.0, "python_x10_beta_scale"))
    comparisons.append(compare_scalars(py_scaled_x10["std_err"], py_base_x["std_err"] / 10.0, "python_x10_se_scale"))

    save_evidence(test_id, py_base_dict, st_base, comparisons, data=df)
    return all(p for p, _ in comparisons), comparisons


def main():
    tests = [
        property_p1_row_order_invariance,
        property_p2_irrelevant_column,
        property_p3_scale_transformation,
    ]
    summary = []
    for t in tests:
        print(f"\n=== Running {t.__name__} ===")
        try:
            passed, comparisons = t()
            fails = [m for p, m in comparisons if not p]
            print(f"Overall: {'PASS' if passed else 'FAIL'}")
            if fails:
                print("Failures:")
                for f in fails[:10]:
                    print("  ", f)
            summary.append((t.__name__, passed, len(fails)))
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
            summary.append((t.__name__, False, -1))

    print("\n=== Summary ===")
    for name, passed, fails in summary:
        print(f"{name}: {'PASS' if passed else 'FAIL'} (fails={fails})")


if __name__ == "__main__":
    main()
