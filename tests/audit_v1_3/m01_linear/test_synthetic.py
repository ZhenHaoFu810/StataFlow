"""M01 Linear: six new independent synthetic dual-run experiments.

Each experiment uses a fresh DGP, fresh random seed, and fresh Stata .do file.
No reuse of existing golden tests.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Allow importing audit_utils from same directory
sys.path.insert(0, str(Path(__file__).parent))
from audit_utils import (
    STATA_CASES,
    EVIDENCE,
    run_stata_do,
    python_result_to_dict,
    compare_scalars,
    compare_coefficients,
    compare_vce,
    save_evidence,
)

from stataflow import OLS
from stataflow.compat.stata import regress


def _stata_do_template(data_csv: str, cmd: str) -> str:
    """Return a Stata .do template that outputs parseable fields."""
    return f'''clear all
set more off

import delimited "{data_csv}", clear

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
* Multi-way cluster counts (Stata stores in e(N_clustvar) if available)
cap display "E_N_CLUST1=" e(N_clustvar)[1,1]
cap display "E_N_CLUST2=" e(N_clustvar)[1,2]

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


def experiment_s1_hand_computable():
    """S1: Hand-computable small sample (n=6)."""
    test_id = "S1_hand_computable"
    rng = np.random.default_rng(20260612)
    n = 6
    x = np.array([-2.0, -1.0, 0.0, 1.0, 2.0, 3.0])
    eps = rng.normal(scale=0.5, size=n)
    y = 2.0 + 3.0 * x + eps
    df = pd.DataFrame({"y": y, "x": x})

    data_csv = STATA_CASES / f"{test_id}.csv"
    df.to_csv(data_csv, index=False)

    stata_cmd = "regress y x"
    st_result = run_stata_do(_stata_do_template(str(data_csv), stata_cmd), test_id)

    py_result = OLS(df, y="y", x=["x"], add_constant=True).fit(vce="ols")
    py_dict = python_result_to_dict(py_result)

    comparisons = []
    comparisons.extend(compare_coefficients(py_dict["coefficients"], st_result.get("coefficients", [])))
    for field in ["nobs", "df_model", "df_resid", "r2", "r2_adj", "rmse", "f_stat", "f_pvalue", "rss", "tss"]:
        comparisons.append(compare_scalars(py_dict[field], st_result.get(field), field))
    comparisons.extend(compare_vce(py_dict["vce"], st_result.get("vce", np.zeros((0, 0))), py_dict["vce_row_names"], [c["name"] for c in st_result.get("coefficients", [])]))

    save_evidence(test_id, py_dict, st_result, comparisons, data=df)
    return all(p for p, _ in comparisons), comparisons


def experiment_s2_heteroskedastic():
    """S2: Known heteroskedastic DGP, robust VCE."""
    test_id = "S2_heteroskedastic"
    rng = np.random.default_rng(2026061201)
    n = 500
    x = rng.normal(size=n)
    sigma = 1.0 + 2.0 * np.abs(x)
    eps = rng.normal(scale=sigma)
    y = 1.0 + 2.0 * x + eps
    df = pd.DataFrame({"y": y, "x": x})

    data_csv = STATA_CASES / f"{test_id}.csv"
    df.to_csv(data_csv, index=False)

    stata_cmd = "regress y x, robust"
    st_result = run_stata_do(_stata_do_template(str(data_csv), stata_cmd), test_id)

    py_result = OLS(df, y="y", x=["x"], add_constant=True).fit(vce="robust")
    py_dict = python_result_to_dict(py_result)

    comparisons = []
    comparisons.extend(compare_coefficients(py_dict["coefficients"], st_result.get("coefficients", [])))
    for field in ["nobs", "df_model", "df_resid", "r2", "r2_adj", "rmse", "f_stat", "f_pvalue"]:
        comparisons.append(compare_scalars(py_dict[field], st_result.get(field), field))
    comparisons.extend(compare_vce(py_dict["vce"], st_result.get("vce", np.zeros((0, 0))), py_dict["vce_row_names"], [c["name"] for c in st_result.get("coefficients", [])]))

    save_evidence(test_id, py_dict, st_result, comparisons, data=df)
    return all(p for p, _ in comparisons), comparisons


def experiment_s3_imbalanced_cluster():
    """S3: Highly imbalanced cluster sizes."""
    test_id = "S3_imbalanced_cluster"
    rng = np.random.default_rng(2026061202)
    n = 400
    # 19 singleton clusters + 1 large cluster
    g = np.array([i for i in range(19)] + [19] * (n - 19))
    x = rng.normal(size=n)
    y = 1.0 + 2.0 * x + rng.normal(scale=1.0, size=n)
    df = pd.DataFrame({"y": y, "x": x, "g": g})

    data_csv = STATA_CASES / f"{test_id}.csv"
    df.to_csv(data_csv, index=False)

    stata_cmd = "regress y x, cluster(g)"
    st_result = run_stata_do(_stata_do_template(str(data_csv), stata_cmd), test_id)

    py_result = OLS(df, y="y", x=["x"], add_constant=True).fit(vce="cluster", cluster="g")
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


def experiment_s4_aweight_missing():
    """S4: aweight with missing values."""
    test_id = "S4_aweight_missing"
    rng = np.random.default_rng(2026061203)
    n = 300
    x = rng.normal(size=n)
    y = 1.0 + 2.0 * x + rng.normal(scale=0.8, size=n)
    w = rng.uniform(0.5, 3.0, size=n)
    # Set some weights to missing (should be dropped)
    w[rng.choice(n, size=20, replace=False)] = np.nan
    df = pd.DataFrame({"y": y, "x": x, "w": w})

    data_csv = STATA_CASES / f"{test_id}.csv"
    df.to_csv(data_csv, index=False)

    stata_cmd = "regress y x [aweight=w]"
    st_result = run_stata_do(_stata_do_template(str(data_csv), stata_cmd), test_id)

    py_result = OLS(df, y="y", x=["x"], add_constant=True, weights=df["w"].values, weight_type="aweight").fit(vce="ols")
    py_dict = python_result_to_dict(py_result)

    comparisons = []
    comparisons.extend(compare_coefficients(py_dict["coefficients"], st_result.get("coefficients", [])))
    for field in ["nobs", "df_model", "df_resid", "r2", "r2_adj", "rmse", "f_stat", "f_pvalue", "rss", "tss"]:
        comparisons.append(compare_scalars(py_dict[field], st_result.get(field), field))
    comparisons.extend(compare_vce(py_dict["vce"], st_result.get("vce", np.zeros((0, 0))), py_dict["vce_row_names"], [c["name"] for c in st_result.get("coefficients", [])]))

    save_evidence(test_id, py_dict, st_result, comparisons, data=df)
    return all(p for p, _ in comparisons), comparisons


def experiment_s4b_aweight_zero():
    """S4b: aweight with zero values (Stata drops, Python raises)."""
    test_id = "S4b_aweight_zero"
    rng = np.random.default_rng(2026061206)
    n = 100
    x = rng.normal(size=n)
    y = 1.0 + 2.0 * x + rng.normal(scale=0.8, size=n)
    w = rng.uniform(0.5, 3.0, size=n)
    w[rng.choice(n, size=10, replace=False)] = 0.0
    df = pd.DataFrame({"y": y, "x": x, "w": w})

    data_csv = STATA_CASES / f"{test_id}.csv"
    df.to_csv(data_csv, index=False)

    stata_cmd = "regress y x [aweight=w]"
    st_result = run_stata_do(_stata_do_template(str(data_csv), stata_cmd), test_id)

    try:
        py_result = OLS(df, y="y", x=["x"], add_constant=True, weights=df["w"].values, weight_type="aweight").fit(vce="ols")
        py_dict = python_result_to_dict(py_result)
        # If Python succeeds, compare
        comparisons = []
        comparisons.extend(compare_coefficients(py_dict["coefficients"], st_result.get("coefficients", [])))
        for field in ["nobs", "df_model", "df_resid", "r2", "r2_adj", "rmse", "f_stat", "f_pvalue", "rss", "tss"]:
            comparisons.append(compare_scalars(py_dict[field], st_result.get(field), field))
        comparisons.extend(compare_vce(py_dict["vce"], st_result.get("vce", np.zeros((0, 0))), py_dict["vce_row_names"], [c["name"] for c in st_result.get("coefficients", [])]))
        save_evidence(test_id, py_dict, st_result, comparisons, data=df)
        return all(p for p, _ in comparisons), comparisons
    except Exception as e:
        # Python fails; Stata succeeds -> this is a finding
        py_dict = {"error": str(e)}
        comparisons = [(False, f"Python raised {type(e).__name__}: {e}; Stata completed with nobs={st_result.get('nobs')}")]
        save_evidence(test_id, py_dict, st_result, comparisons, data=df)
        return False, comparisons


def experiment_s5_near_collinearity():
    """S5: Near-collinear regressors with extreme scaling."""
    test_id = "S5_near_collinearity"
    rng = np.random.default_rng(2026061204)
    n = 250
    x1 = rng.normal(size=n)
    x2 = x1 + rng.normal(scale=1e-7, size=n)
    x2_scaled = x2 * 1e6
    y = 1.0 + 2.0 * x1 + 3.0 * x2 + rng.normal(scale=0.5, size=n)
    df = pd.DataFrame({"y": y, "x1": x1, "x2": x2_scaled})

    data_csv = STATA_CASES / f"{test_id}.csv"
    df.to_csv(data_csv, index=False)

    stata_cmd = "regress y x1 x2"
    st_result = run_stata_do(_stata_do_template(str(data_csv), stata_cmd), test_id)

    py_result = OLS(df, y="y", x=["x1", "x2"], add_constant=True).fit(vce="ols")
    py_dict = python_result_to_dict(py_result)

    comparisons = []
    comparisons.extend(compare_coefficients(py_dict["coefficients"], st_result.get("coefficients", [])))
    for field in ["nobs", "df_model", "df_resid", "r2", "r2_adj", "rmse", "f_stat", "f_pvalue"]:
        comparisons.append(compare_scalars(py_dict[field], st_result.get(field), field))
    comparisons.extend(compare_vce(py_dict["vce"], st_result.get("vce", np.zeros((0, 0))), py_dict["vce_row_names"], [c["name"] for c in st_result.get("coefficients", [])]))

    save_evidence(test_id, py_dict, st_result, comparisons, data=df)
    return all(p for p, _ in comparisons), comparisons


def experiment_s6_factor_missing_changes_base():
    """S6: Factor interaction where missing values change effective base level."""
    test_id = "S6_factor_missing_changes_base"
    rng = np.random.default_rng(2026061205)
    n = 400
    g = rng.integers(1, 5, size=n).astype(int)
    x = rng.normal(size=n)
    y = 1.0 + 2.0 * x + np.where(g == 2, 5.0, 0.0) + np.where(g == 3, -3.0, 0.0) + rng.normal(scale=1.0, size=n)

    # Make all observations with g==1 have missing x, so g==1 drops out of estimation sample
    x[g == 1] = np.nan
    df = pd.DataFrame({"y": y, "x": x, "g": g})

    data_csv = STATA_CASES / f"{test_id}.csv"
    df.to_csv(data_csv, index=False)

    # Stata factor syntax
    stata_cmd = "regress y i.g##c.x"
    st_result = run_stata_do(_stata_do_template(str(data_csv), stata_cmd), test_id)

    # Python wrapper
    py_result = regress(df, y="y", x=["i.g##c.x"], vce="ols")
    py_dict = python_result_to_dict(py_result)

    comparisons = []
    comparisons.extend(compare_coefficients(py_dict["coefficients"], st_result.get("coefficients", [])))
    for field in ["nobs", "df_model", "df_resid", "r2", "r2_adj", "rmse", "f_stat", "f_pvalue"]:
        comparisons.append(compare_scalars(py_dict[field], st_result.get(field), field))
    comparisons.extend(compare_vce(py_dict["vce"], st_result.get("vce", np.zeros((0, 0))), py_dict["vce_row_names"], [c["name"] for c in st_result.get("coefficients", [])]))

    save_evidence(test_id, py_dict, st_result, comparisons, data=df)
    return all(p for p, _ in comparisons), comparisons


def experiment_s7_two_way_cluster_balanced():
    """S7: Balanced two-way clustering with moderate group counts.

    DGP: n=600, 30 firms x 20 years, outcome with firm-level and year-level shocks.
    Purpose: isolate two-way cluster VCE discrepancy from small-G effects.
    """
    test_id = "S7_two_way_cluster_balanced"
    rng = np.random.default_rng(2026061207)
    n_firms = 30
    n_years = 20
    n = n_firms * n_years
    firm = np.repeat(np.arange(n_firms), n_years)
    year = np.tile(np.arange(n_years), n_firms)
    x = rng.normal(size=n)
    # Firm and year shocks
    firm_fe = np.repeat(rng.normal(scale=0.5, size=n_firms), n_years)
    year_fe = np.tile(rng.normal(scale=0.5, size=n_years), n_firms)
    y = 1.0 + 2.0 * x + firm_fe + year_fe + rng.normal(scale=0.5, size=n)
    df = pd.DataFrame({"y": y, "x": x, "firm": firm, "year": year})

    data_csv = STATA_CASES / f"{test_id}.csv"
    df.to_csv(data_csv, index=False)

    stata_cmd = "regress y x, vce(cluster firm year)"
    st_result = run_stata_do(_stata_do_template(str(data_csv), stata_cmd), test_id)

    py_result = OLS(df, y="y", x=["x"], add_constant=True).fit(vce="cluster", cluster=["firm", "year"])
    py_dict = python_result_to_dict(py_result)

    comparisons = []
    comparisons.extend(compare_coefficients(py_dict["coefficients"], st_result.get("coefficients", [])))
    for field in ["nobs", "df_model", "df_resid", "r2", "r2_adj", "rmse", "f_stat", "f_pvalue"]:
        comparisons.append(compare_scalars(py_dict[field], st_result.get(field), field))
    comparisons.extend(compare_vce(py_dict["vce"], st_result.get("vce", np.zeros((0, 0))), py_dict["vce_row_names"], [c["name"] for c in st_result.get("coefficients", [])]))

    save_evidence(test_id, py_dict, st_result, comparisons, data=df)
    return all(p for p, _ in comparisons), comparisons


def main():
    experiments = [
        experiment_s1_hand_computable,
        experiment_s2_heteroskedastic,
        experiment_s3_imbalanced_cluster,
        experiment_s4_aweight_missing,
        experiment_s4b_aweight_zero,
        experiment_s5_near_collinearity,
        experiment_s6_factor_missing_changes_base,
        experiment_s7_two_way_cluster_balanced,
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
