"""M02 Panel/FE: seven new independent synthetic dual-run experiments."""

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

from stataflow import FixedEffectsOLS
from stataflow.compat.stata import xtreg_fe


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


def experiment_s1_hand_computable_panel():
    """S1: Hand-computable small panel (3 entities x 4 periods)."""
    test_id = "S1_hand_computable_panel"
    rng = np.random.default_rng(2026061208)
    n_entity = 3
    n_time = 4
    n = n_entity * n_time
    entity = np.repeat(np.arange(n_entity), n_time)
    time = np.tile(np.arange(n_time), n_entity)
    x = np.linspace(-1, 1, n) + rng.normal(scale=0.05, size=n)
    alpha = np.array([5.0, -3.0, 1.0])
    y = alpha[entity] + 2.0 * x + rng.normal(scale=0.1, size=n)
    df = pd.DataFrame({"y": y, "x": x, "entity": entity, "time": time})

    data_csv = STATA_CASES / f"{test_id}.csv"
    df.to_csv(data_csv, index=False)

    stata_cmd = "xtset entity time\nxtreg y x, fe"
    st_result = run_stata_do(_stata_do_template(str(data_csv), stata_cmd), test_id)

    py_result = FixedEffectsOLS(df, y="y", x=["x"], fe="entity", add_constant=True).fit(vce="ols")
    py_dict = python_result_to_dict(py_result)

    comparisons = []
    comparisons.extend(compare_coefficients(py_dict["coefficients"], st_result.get("coefficients", [])))
    for field in ["nobs", "df_model", "df_resid", "r2", "r2_adj", "rmse", "f_stat", "f_pvalue", "rss", "tss"]:
        comparisons.append(compare_scalars(py_dict[field], st_result.get(field), field))
    comparisons.extend(compare_vce(py_dict["vce"], st_result.get("vce", np.zeros((0, 0))), py_dict["vce_row_names"], [c["name"] for c in st_result.get("coefficients", [])]))

    save_evidence(test_id, py_dict, st_result, comparisons, data=df)
    return all(p for p, _ in comparisons), comparisons


def experiment_s2_random_panel_ols():
    """S2: Random panel conventional FE VCE."""
    test_id = "S2_random_panel_ols"
    rng = np.random.default_rng(2026061209)
    n_entity = 50
    n_time = 10
    n = n_entity * n_time
    entity = np.repeat(np.arange(n_entity), n_time)
    x = rng.normal(size=n)
    alpha = np.repeat(rng.normal(scale=2.0, size=n_entity), n_time)
    y = alpha + 1.5 * x + rng.normal(scale=1.0, size=n)
    df = pd.DataFrame({"y": y, "x": x, "entity": entity})

    data_csv = STATA_CASES / f"{test_id}.csv"
    df.to_csv(data_csv, index=False)

    stata_cmd = "xtset entity\nxtreg y x, fe"
    st_result = run_stata_do(_stata_do_template(str(data_csv), stata_cmd), test_id)

    py_result = FixedEffectsOLS(df, y="y", x=["x"], fe="entity", add_constant=True).fit(vce="ols")
    py_dict = python_result_to_dict(py_result)

    comparisons = []
    comparisons.extend(compare_coefficients(py_dict["coefficients"], st_result.get("coefficients", [])))
    for field in ["nobs", "df_model", "df_resid", "r2", "r2_adj", "rmse", "f_stat", "f_pvalue", "rss", "tss"]:
        comparisons.append(compare_scalars(py_dict[field], st_result.get(field), field))
    comparisons.extend(compare_vce(py_dict["vce"], st_result.get("vce", np.zeros((0, 0))), py_dict["vce_row_names"], [c["name"] for c in st_result.get("coefficients", [])]))

    save_evidence(test_id, py_dict, st_result, comparisons, data=df)
    return all(p for p, _ in comparisons), comparisons


def experiment_s3_entity_invariant_dropped():
    """S3: Entity-invariant regressor should be dropped."""
    test_id = "S3_entity_invariant_dropped"
    rng = np.random.default_rng(2026061210)
    n_entity = 30
    n_time = 8
    n = n_entity * n_time
    entity = np.repeat(np.arange(n_entity), n_time)
    z = np.repeat(rng.normal(size=n_entity), n_time)  # entity-invariant
    x = rng.normal(size=n)
    alpha = np.repeat(rng.normal(scale=1.0, size=n_entity), n_time)
    y = alpha + 2.0 * x + 0.5 * z + rng.normal(scale=0.5, size=n)
    df = pd.DataFrame({"y": y, "x": x, "z": z, "entity": entity})

    data_csv = STATA_CASES / f"{test_id}.csv"
    df.to_csv(data_csv, index=False)

    stata_cmd = "xtset entity\nxtreg y x z, fe"
    st_result = run_stata_do(_stata_do_template(str(data_csv), stata_cmd), test_id)

    try:
        py_result = FixedEffectsOLS(df, y="y", x=["x", "z"], fe="entity", add_constant=True).fit(vce="ols")
        py_dict = python_result_to_dict(py_result)

        comparisons = []
        comparisons.extend(compare_coefficients(py_dict["coefficients"], st_result.get("coefficients", [])))
        for field in ["nobs", "df_model", "df_resid", "r2", "r2_adj", "rmse", "f_stat", "f_pvalue"]:
            comparisons.append(compare_scalars(py_dict[field], st_result.get(field), field))
        comparisons.extend(compare_vce(py_dict["vce"], st_result.get("vce", np.zeros((0, 0))), py_dict["vce_row_names"], [c["name"] for c in st_result.get("coefficients", [])]))

        save_evidence(test_id, py_dict, st_result, comparisons, data=df)
        return all(p for p, _ in comparisons), comparisons
    except Exception as e:
        py_dict = {"error": str(e)}
        comparisons = [(False, f"Python raised {type(e).__name__}: {e}; Stata completed with nobs={st_result.get('nobs')}")]
        save_evidence(test_id, py_dict, st_result, comparisons, data=df)
        return False, comparisons


def experiment_s4_unbalanced_singleton():
    """S4: Unbalanced panel with singleton entity."""
    test_id = "S4_unbalanced_singleton"
    rng = np.random.default_rng(2026061211)
    n_entity = 40
    # Most entities have 5-10 periods, one entity has only 1 observation
    counts = rng.integers(5, 11, size=n_entity - 1)
    counts = np.append(counts, 1)
    entity = np.repeat(np.arange(n_entity), counts)
    n = len(entity)
    x = rng.normal(size=n)
    alpha = np.repeat(rng.normal(scale=2.0, size=n_entity), counts)
    y = alpha + 1.5 * x + rng.normal(scale=1.0, size=n)
    time = np.concatenate([np.arange(c) for c in counts])
    df = pd.DataFrame({"y": y, "x": x, "entity": entity, "time": time})

    data_csv = STATA_CASES / f"{test_id}.csv"
    df.to_csv(data_csv, index=False)

    stata_cmd = "xtset entity time\nxtreg y x, fe"
    st_result = run_stata_do(_stata_do_template(str(data_csv), stata_cmd), test_id)

    py_result = FixedEffectsOLS(df, y="y", x=["x"], fe="entity", add_constant=True).fit(vce="ols")
    py_dict = python_result_to_dict(py_result)

    comparisons = []
    comparisons.extend(compare_coefficients(py_dict["coefficients"], st_result.get("coefficients", [])))
    for field in ["nobs", "df_model", "df_resid", "r2", "r2_adj", "rmse", "f_stat", "f_pvalue", "rss", "tss"]:
        comparisons.append(compare_scalars(py_dict[field], st_result.get(field), field))
    comparisons.extend(compare_vce(py_dict["vce"], st_result.get("vce", np.zeros((0, 0))), py_dict["vce_row_names"], [c["name"] for c in st_result.get("coefficients", [])]))

    save_evidence(test_id, py_dict, st_result, comparisons, data=df)
    return all(p for p, _ in comparisons), comparisons


def experiment_s5_fe_cluster_different_id():
    """S5: FE with cluster different from panel id."""
    test_id = "S5_fe_cluster_different_id"
    rng = np.random.default_rng(2026061212)
    n_entity = 40
    n_time = 6
    n = n_entity * n_time
    entity = np.repeat(np.arange(n_entity), n_time)
    # cluster group: each group contains 4 entities
    cluster = np.repeat(np.arange(n_entity // 4), n_time * 4)
    x = rng.normal(size=n)
    alpha = np.repeat(rng.normal(scale=2.0, size=n_entity), n_time)
    y = alpha + 1.5 * x + rng.normal(scale=1.0, size=n)
    df = pd.DataFrame({"y": y, "x": x, "entity": entity, "cluster": cluster})

    data_csv = STATA_CASES / f"{test_id}.csv"
    df.to_csv(data_csv, index=False)

    stata_cmd = "xtset entity\nxtreg y x, fe cluster(cluster)"
    st_result = run_stata_do(_stata_do_template(str(data_csv), stata_cmd), test_id)

    py_result = FixedEffectsOLS(df, y="y", x=["x"], fe="entity", add_constant=True).fit(vce="cluster", cluster="cluster")
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


def experiment_s6_wrapper_default_constant():
    """S6: xtreg_fe wrapper default constant=False vs Stata xtreg, fe always reports _cons."""
    test_id = "S6_wrapper_default_constant"
    rng = np.random.default_rng(2026061213)
    n_entity = 30
    n_time = 8
    n = n_entity * n_time
    entity = np.repeat(np.arange(n_entity), n_time)
    x = rng.normal(size=n)
    alpha = np.repeat(rng.normal(scale=2.0, size=n_entity), n_time)
    y = alpha + 1.5 * x + rng.normal(scale=1.0, size=n)
    df = pd.DataFrame({"y": y, "x": x, "entity": entity})

    data_csv = STATA_CASES / f"{test_id}.csv"
    df.to_csv(data_csv, index=False)

    # Stata xtreg, fe always reports _cons
    stata_cmd = "xtset entity\nxtreg y x, fe"
    st_result = run_stata_do(_stata_do_template(str(data_csv), stata_cmd), test_id)

    # Python wrapper default constant=False
    from stataflow.compat.stata import xtreg_fe
    py_result_default = xtreg_fe(df, y="y", x=["x"], fe="entity")
    py_dict_default = python_result_to_dict(py_result_default)

    comparisons = []
    py_has_cons = any(c["name"] == "_cons" for c in py_dict_default["coefficients"])
    st_has_cons = any(c["name"] == "_cons" for c in st_result.get("coefficients", []))
    comparisons.append((py_has_cons == st_has_cons, f"_cons presence: Python={py_has_cons}, Stata={st_has_cons}"))

    save_evidence(test_id, py_dict_default, st_result, comparisons, data=df)
    return all(p for p, _ in comparisons), comparisons


def experiment_s7_near_collinear_within():
    """S7: Near-collinear within regressors."""
    test_id = "S7_near_collinear_within"
    rng = np.random.default_rng(2026061214)
    n_entity = 30
    n_time = 10
    n = n_entity * n_time
    entity = np.repeat(np.arange(n_entity), n_time)
    base = np.repeat(rng.normal(scale=2.0, size=n_entity), n_time)
    x1 = rng.normal(size=n)
    x2 = x1 + rng.normal(scale=1e-7, size=n)
    y = base + 2.0 * x1 + 3.0 * x2 + rng.normal(scale=0.5, size=n)
    df = pd.DataFrame({"y": y, "x1": x1, "x2": x2, "entity": entity})

    data_csv = STATA_CASES / f"{test_id}.csv"
    df.to_csv(data_csv, index=False)

    stata_cmd = "xtset entity\nxtreg y x1 x2, fe"
    st_result = run_stata_do(_stata_do_template(str(data_csv), stata_cmd), test_id)

    py_result = FixedEffectsOLS(df, y="y", x=["x1", "x2"], fe="entity", add_constant=True).fit(vce="ols")
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
        experiment_s1_hand_computable_panel,
        experiment_s2_random_panel_ols,
        experiment_s3_entity_invariant_dropped,
        experiment_s4_unbalanced_singleton,
        experiment_s5_fe_cluster_different_id,
        experiment_s6_wrapper_default_constant,
        experiment_s7_near_collinear_within,
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
