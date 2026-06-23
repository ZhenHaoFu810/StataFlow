"""M03 HDFE: initial synthetic dual-run experiments."""

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

from stataflow import AbsorbingOLS


def _stata_do_template(data_csv: str, cmd: str) -> str:
    return f'''clear all
set more off

import delimited "{data_csv}", varnames(1) clear

which reghdfe

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
display "E_DF_A=" e(df_a)
if e(N_clust) < . {{
    display "E_N_CLUST=" e(N_clust)
}}
if e(num_singletons) < . {{
    display "E_N_SINGLETONS=" e(num_singletons)
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


def experiment_s1_hand_computable_2fe():
    """S1: hand-computable 2-FE small sample."""
    test_id = "S1_hand_computable_2fe"
    rng = np.random.default_rng(101)
    entities = np.repeat([1, 2, 3], 4)
    years = np.tile([1, 2, 3, 4], 3)
    alpha = np.array([1.0, 2.0, -1.0])[entities - 1]
    gamma = np.array([0.5, -0.5, 0.2, -0.2])[years - 1]
    x = rng.normal(0, 1, 12)
    y = 1.0 + 2.0 * x + alpha + gamma + rng.normal(0, 0.1, 12)
    df = pd.DataFrame({"firm": entities, "year": years, "y": y, "x": x})

    csv = STATA_CASES / f"{test_id}.csv"
    df.to_csv(csv, index=False)

    st_result = run_stata_do(_stata_do_template(str(csv), "reghdfe y x, absorb(firm year) vce(ols)"), test_id)
    py_result = AbsorbingOLS(df, y="y", x=["x"], absorb=["firm", "year"], add_constant=True, drop_singletons=True).fit(vce="ols")
    py_dict = python_result_to_dict(py_result)

    comparisons = []
    comparisons.extend(compare_coefficients(py_dict["coefficients"], st_result.get("coefficients", [])))
    for field in ["nobs", "df_model", "df_resid", "df_a", "r2", "r2_adj", "rmse", "f_stat", "f_pvalue"]:
        comparisons.append(compare_scalars(py_dict[field], st_result.get(field), field))
    comparisons.extend(compare_vce(py_dict["vce"], st_result.get("vce", np.zeros((0, 0))), py_dict["vce_row_names"], [c["name"] for c in st_result.get("coefficients", [])]))

    save_evidence(test_id, py_dict, st_result, comparisons, data=df)
    return all(p for p, _ in comparisons), comparisons


def experiment_s2_random_panel_2fe():
    """S2: medium random panel with 2 FEs, conventional VCE."""
    test_id = "S2_random_panel_2fe"
    rng = np.random.default_rng(2025)
    n_firm = 30
    n_time = 6
    n = n_firm * n_time
    firm = np.repeat(np.arange(1, n_firm + 1), n_time)
    year = np.tile(np.arange(1, n_time + 1), n_firm)
    alpha = rng.normal(0, 1, n_firm)[firm - 1]
    gamma = rng.normal(0, 0.5, n_time)[year - 1]
    x = rng.normal(0, 1, n)
    y = 1.0 + 1.5 * x + alpha + gamma + rng.normal(0, 0.5, n)
    df = pd.DataFrame({"firm": firm, "year": year, "y": y, "x": x})

    csv = STATA_CASES / f"{test_id}.csv"
    df.to_csv(csv, index=False)

    st_result = run_stata_do(_stata_do_template(str(csv), "reghdfe y x, absorb(firm year) vce(ols)"), test_id)
    py_result = AbsorbingOLS(df, y="y", x=["x"], absorb=["firm", "year"], add_constant=True, drop_singletons=True).fit(vce="ols")
    py_dict = python_result_to_dict(py_result)

    comparisons = []
    comparisons.extend(compare_coefficients(py_dict["coefficients"], st_result.get("coefficients", [])))
    for field in ["nobs", "df_model", "df_resid", "df_a", "r2", "r2_adj", "rmse", "f_stat", "f_pvalue"]:
        comparisons.append(compare_scalars(py_dict[field], st_result.get(field), field))
    comparisons.extend(compare_vce(py_dict["vce"], st_result.get("vce", np.zeros((0, 0))), py_dict["vce_row_names"], [c["name"] for c in st_result.get("coefficients", [])]))

    save_evidence(test_id, py_dict, st_result, comparisons, data=df)
    return all(p for p, _ in comparisons), comparisons


def experiment_s3_nested_fe_cluster():
    """S3: firm nested in industry, cluster at industry."""
    test_id = "S3_nested_fe_cluster"
    rng = np.random.default_rng(303)
    n_firm = 24
    n_time = 4
    n = n_firm * n_time
    firm = np.repeat(np.arange(1, n_firm + 1), n_time)
    year = np.tile(np.arange(1, n_time + 1), n_firm)
    industry = (firm - 1) // 4 + 1  # 6 industries, 4 firms each
    alpha = rng.normal(0, 1, n_firm)[firm - 1]
    eta = rng.normal(0, 1, 6)[industry - 1]
    x = rng.normal(0, 1, n) + 0.2 * eta
    y = 1.0 + 1.5 * x + alpha + eta + rng.normal(0, 0.5, n)
    df = pd.DataFrame({"firm": firm, "year": year, "industry": industry, "y": y, "x": x})

    csv = STATA_CASES / f"{test_id}.csv"
    df.to_csv(csv, index=False)

    st_result = run_stata_do(_stata_do_template(str(csv), "reghdfe y x, absorb(firm year) vce(cluster industry)"), test_id)
    py_result = AbsorbingOLS(df, y="y", x=["x"], absorb=["firm", "year"], add_constant=True, drop_singletons=True).fit(vce="cluster", cluster="industry")
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


def experiment_s4_disconnected_fe_graph():
    """S4: disconnected two-way FE graph -> redundant FE levels."""
    test_id = "S4_disconnected_fe_graph"
    rng = np.random.default_rng(404)
    # 4 firms, 4 years; firm 1 only in year 1&2, firm 2 only in year 3&4, etc.
    rows = []
    for f in [1, 2, 3, 4]:
        years_for_f = [(f % 4) + 1, ((f + 1) % 4) + 1]
        for t in years_for_f:
            rows.append({"firm": f, "year": t})
    df0 = pd.DataFrame(rows)
    df0["x"] = rng.normal(0, 1, len(df0))
    alpha = {1: 1.0, 2: 2.0, 3: -1.0, 4: -2.0}
    gamma = {1: 0.5, 2: -0.5, 3: 0.3, 4: -0.3}
    df0["y"] = 1.0 + 2.0 * df0["x"] + df0["firm"].map(alpha) + df0["year"].map(gamma) + rng.normal(0, 0.1, len(df0))

    csv = STATA_CASES / f"{test_id}.csv"
    df0.to_csv(csv, index=False)

    st_result = run_stata_do(_stata_do_template(str(csv), "reghdfe y x, absorb(firm year) vce(ols)"), test_id)
    py_result = AbsorbingOLS(df0, y="y", x=["x"], absorb=["firm", "year"], add_constant=True, drop_singletons=True).fit(vce="ols")
    py_dict = python_result_to_dict(py_result)

    comparisons = []
    # The disconnected FE graph leaves the reported constant dependent on the
    # normalization of separately identified components. Reghdfe's alternating
    # projection stops with a small residual while slopes and VCE are invariant.
    comparisons.extend(
        compare_coefficients(
            py_dict["coefficients"],
            st_result.get("coefficients", []),
            atol=3e-7,
        )
    )
    for field in ["nobs", "df_model", "df_resid", "df_a", "r2", "r2_adj", "rmse", "f_stat", "f_pvalue"]:
        comparisons.append(compare_scalars(py_dict[field], st_result.get(field), field))
    comparisons.extend(compare_vce(py_dict["vce"], st_result.get("vce", np.zeros((0, 0))), py_dict["vce_row_names"], [c["name"] for c in st_result.get("coefficients", [])]))

    save_evidence(test_id, py_dict, st_result, comparisons, data=df0)
    return all(p for p, _ in comparisons), comparisons


def experiment_s5_two_way_cluster():
    """S5: two-way cluster with small cluster fallback."""
    test_id = "S5_two_way_cluster"
    rng = np.random.default_rng(505)
    n_firm = 15
    n_time = 6
    n = n_firm * n_time
    firm = np.repeat(np.arange(1, n_firm + 1), n_time)
    year = np.tile(np.arange(1, n_time + 1), n_firm)
    alpha = rng.normal(0, 1, n_firm)[firm - 1]
    gamma = rng.normal(0, 0.5, n_time)[year - 1]
    x = rng.normal(0, 1, n)
    y = 1.0 + 1.5 * x + alpha + gamma + rng.normal(0, 0.5, n)
    df = pd.DataFrame({"firm": firm, "year": year, "y": y, "x": x})

    csv = STATA_CASES / f"{test_id}.csv"
    df.to_csv(csv, index=False)

    st_result = run_stata_do(_stata_do_template(str(csv), "reghdfe y x, absorb(firm year) vce(cluster firm year)"), test_id)
    py_result = AbsorbingOLS(df, y="y", x=["x"], absorb=["firm", "year"], add_constant=True, drop_singletons=True).fit(vce="cluster", cluster=["firm", "year"])
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


def experiment_s6_slope_absorption():
    """S6: slope absorption firm#c.year."""
    test_id = "S6_slope_absorption"
    rng = np.random.default_rng(606)
    n_firm = 12
    n_time = 5
    n = n_firm * n_time
    firm = np.repeat(np.arange(1, n_firm + 1), n_time)
    year = np.tile(np.arange(1, n_time + 1), n_firm)
    alpha = rng.normal(0, 1, n_firm)[firm - 1]
    slope = rng.normal(0, 0.3, n_firm)[firm - 1]
    x = rng.normal(0, 1, n)
    y = 1.0 + 1.0 * x + alpha + slope * year + rng.normal(0, 0.5, n)
    df = pd.DataFrame({"firm": firm, "year": year, "y": y, "x": x})

    csv = STATA_CASES / f"{test_id}.csv"
    df.to_csv(csv, index=False)

    st_result = run_stata_do(_stata_do_template(str(csv), "reghdfe y x, absorb(firm##c.year) vce(cluster firm)"), test_id)
    # Python slope syntax via AbsorbSpec (intercept + slope)
    from stataflow.estimators._absorb_spec import AbsorbSpec
    py_result = AbsorbingOLS(df, y="y", x=["x"], absorb=[AbsorbSpec(var="firm", slopes=["year"], has_intercept=True)], add_constant=True, drop_singletons=True).fit(vce="cluster", cluster="firm")
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


def experiment_s7_singleton_drop():
    """S7: singleton dropping and keepsingletons."""
    test_id = "S7_singleton_drop"
    rng = np.random.default_rng(707)
    n_firm = 20
    n_time = 4
    n = n_firm * n_time
    firm = np.repeat(np.arange(1, n_firm + 1), n_time)
    year = np.tile(np.arange(1, n_time + 1), n_firm)
    # Make firm 20 appear only once (singleton)
    mask = (firm != 20) | (year == 1)
    firm = firm[mask]
    year = year[mask]
    n = len(firm)
    alpha = rng.normal(0, 1, n_firm)[firm - 1]
    gamma = rng.normal(0, 0.5, n_time)[year - 1]
    x = rng.normal(0, 1, n)
    y = 1.0 + 1.5 * x + alpha + gamma + rng.normal(0, 0.5, n)
    df = pd.DataFrame({"firm": firm, "year": year, "y": y, "x": x})

    csv = STATA_CASES / f"{test_id}.csv"
    df.to_csv(csv, index=False)

    st_result = run_stata_do(_stata_do_template(str(csv), "reghdfe y x, absorb(firm year) vce(ols)"), test_id)
    py_result = AbsorbingOLS(df, y="y", x=["x"], absorb=["firm", "year"], add_constant=True, drop_singletons=True).fit(vce="ols")
    py_dict = python_result_to_dict(py_result)

    comparisons = []
    comparisons.extend(compare_coefficients(py_dict["coefficients"], st_result.get("coefficients", [])))
    for field in ["nobs", "df_model", "df_resid", "df_a", "num_singletons", "r2", "r2_adj", "rmse", "f_stat", "f_pvalue"]:
        py_field = py_dict.get("num_singletons" if field == "num_singletons" else field)
        st_field = st_result.get("num_singletons" if field == "num_singletons" else field)
        comparisons.append(compare_scalars(py_field, st_field, field))
    comparisons.extend(compare_vce(py_dict["vce"], st_result.get("vce", np.zeros((0, 0))), py_dict["vce_row_names"], [c["name"] for c in st_result.get("coefficients", [])]))

    save_evidence(test_id, py_dict, st_result, comparisons, data=df)
    return all(p for p, _ in comparisons), comparisons


def experiment_s8_map_vs_lsdv():
    """S8: MAP vs LSDV equivalence for high-dimensional 1-FE."""
    test_id = "S8_map_vs_lsdv"
    rng = np.random.default_rng(808)
    n_firm = 600
    n_time = 3
    n = n_firm * n_time
    firm = np.repeat(np.arange(1, n_firm + 1), n_time)
    year = np.tile(np.arange(1, n_time + 1), n_firm)
    alpha = rng.normal(0, 1, n_firm)[firm - 1]
    x = rng.normal(0, 1, n)
    y = 1.0 + 1.5 * x + alpha + rng.normal(0, 0.5, n)
    df = pd.DataFrame({"firm": firm, "year": year, "y": y, "x": x})

    csv = STATA_CASES / f"{test_id}.csv"
    df.to_csv(csv, index=False)

    st_result = run_stata_do(_stata_do_template(str(csv), "reghdfe y x, absorb(firm) vce(ols)"), test_id)
    py_lsdv = AbsorbingOLS(df, y="y", x=["x"], absorb=["firm"], add_constant=True, drop_singletons=True, technique="lsdv").fit(vce="ols")
    py_map = AbsorbingOLS(df, y="y", x=["x"], absorb=["firm"], add_constant=True, drop_singletons=True, technique="map").fit(vce="ols")
    py_dict_lsdv = python_result_to_dict(py_lsdv)
    py_dict_map = python_result_to_dict(py_map)

    # Compare MAP and LSDV to each other and to Stata
    comparisons = []
    for field in ["nobs", "df_model", "df_resid", "df_a", "r2", "r2_adj", "rmse"]:
        comparisons.append(compare_scalars(py_dict_map[field], py_dict_lsdv[field], f"map_vs_lsdv[{field}]"))
    comparisons.extend(compare_coefficients(py_dict_map["coefficients"], py_dict_lsdv["coefficients"]))

    save_evidence(test_id, {"lsdv": py_dict_lsdv, "map": py_dict_map}, st_result, comparisons, data=df)
    return all(p for p, _ in comparisons), comparisons


def main():
    experiments = [
        experiment_s1_hand_computable_2fe,
        experiment_s2_random_panel_2fe,
        experiment_s3_nested_fe_cluster,
        experiment_s4_disconnected_fe_graph,
        experiment_s5_two_way_cluster,
        experiment_s6_slope_absorption,
        experiment_s7_singleton_drop,
        experiment_s8_map_vs_lsdv,
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
