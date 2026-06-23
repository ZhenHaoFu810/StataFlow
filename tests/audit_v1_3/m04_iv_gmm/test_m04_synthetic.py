"""M04 IV/GMM: synthetic dual-run experiments."""

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

from stataflow import IV2SLS, IVAbsorbingOLS


def _stata_do_template_ivregress(data_csv: str, cmd: str) -> str:
    return f'''clear all
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
display "E_RSS=" e(rss)
display "E_MSS=" e(mss)
if e(N_clust) < . {{
    display "E_N_CLUST=" e(N_clust)
}}
local coefs : colnames e(b)
local k : word count `coefs'
forvalues i = 1/`k' {{
    local name : word `i' of `coefs'
    display "COEF `name' " _b[`name'] " " _se[`name']
}}
matrix V = e(V)
forvalues i = 1/`k' {{
    forvalues j = 1/`k' {{
        display "VCE " (`i'-1) " " (`j'-1) " " V[`i',`j']
    }}
}}
'''


def _stata_do_template_ivreghdfe(data_csv: str, cmd: str) -> str:
    return f'''clear all
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
display "E_RSS=" e(rss)
display "E_MSS=" e(mss)
display "E_DF_A=" e(df_a)
if e(N_clust) < . {{
    display "E_N_CLUST=" e(N_clust)
}}
if e(widstat) < . {{
    display "E_WIDSTAT=" e(widstat)
}}
if e(idstat) < . {{
    display "E_IDSTAT=" e(idstat)
}}
if e(j) < . {{
    display "E_J=" e(j)
    display "E_J_P=" e(jp)
    display "E_J_DF=" e(jdf)
}}
local coefs : colnames e(b)
local k : word count `coefs'
forvalues i = 1/`k' {{
    local name : word `i' of `coefs'
    display "COEF `name' " _b[`name'] " " _se[`name']
}}
matrix V = e(V)
forvalues i = 1/`k' {{
    forvalues j = 1/`k' {{
        display "VCE " (`i'-1) " " (`j'-1) " " V[`i',`j']
    }}
}}
'''


def _stata_do_template_ivreg2(data_csv: str, cmd: str) -> str:
    return f'''clear all
set more off
import delimited "{data_csv}", varnames(1) clear
which ivreg2
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
if e(widstat) < . {{
    display "E_WIDSTAT=" e(widstat)
}}
if e(idstat) < . {{
    display "E_IDSTAT=" e(idstat)
}}
if e(j) < . {{
    display "E_J=" e(j)
    display "E_J_P=" e(jp)
    display "E_J_DF=" e(jdf)
}}
local coefs : colnames e(b)
local k : word count `coefs'
forvalues i = 1/`k' {{
    local name : word `i' of `coefs'
    display "COEF `name' " _b[`name'] " " _se[`name']
}}
matrix V = e(V)
forvalues i = 1/`k' {{
    forvalues j = 1/`k' {{
        display "VCE " (`i'-1) " " (`j'-1) " " V[`i',`j']
    }}
}}
'''


def experiment_s1_hand_computable_2sls():
    """S1: hand-computable 2SLS small sample."""
    test_id = "S1_hand_computable_2sls"
    rng = np.random.default_rng(1001)
    n = 20
    z = rng.normal(0, 1, n)
    u = rng.normal(0, 0.5, n)
    x = 0.5 * z + u + rng.normal(0, 0.5, n)  # endogenous
    y = 1.0 + 2.0 * x + u + rng.normal(0, 0.3, n)
    df = pd.DataFrame({"y": y, "x": x, "z": z})

    csv = STATA_CASES / f"{test_id}.csv"
    df.to_csv(csv, index=False)

    st_result = run_stata_do(_stata_do_template_ivregress(str(csv), "ivregress 2sls y (x = z), robust"), test_id)
    py_result = IV2SLS(df, y="y", x_exog=[], x_endog=["x"], instruments=["z"], add_constant=True).fit(vce="robust")
    py_dict = python_result_to_dict(py_result)

    comparisons = []
    comparisons.extend(compare_coefficients(py_dict["coefficients"], st_result.get("coefficients", [])))
    for field in ["nobs", "df_model", "df_resid", "r2", "r2_adj", "rmse", "f_stat", "f_pvalue"]:
        comparisons.append(compare_scalars(py_dict[field], st_result.get(field), field))
    comparisons.extend(compare_vce(py_dict["vce"], st_result.get("vce", np.zeros((0, 0))), py_dict["vce_row_names"], [c["name"] for c in st_result.get("coefficients", [])]))

    save_evidence(test_id, py_dict, st_result, comparisons, data=df)
    return all(p for p, _ in comparisons), comparisons


def experiment_s2_random_2sls_cluster():
    """S2: random 2SLS with one exog and cluster."""
    test_id = "S2_random_2sls_cluster"
    rng = np.random.default_rng(2002)
    n = 120
    g = np.repeat(np.arange(1, 21), 6)
    z = rng.normal(0, 1, n)
    w = rng.normal(0, 1, n)
    u = rng.normal(0, 1, n) + 0.5 * rng.normal(0, 1, 20)[g - 1]
    x = 0.4 * z + 0.2 * w + u + rng.normal(0, 0.5, n)
    y = 1.0 + 0.8 * w + 1.5 * x + u + rng.normal(0, 0.5, n)
    df = pd.DataFrame({"y": y, "x": x, "w": w, "z": z, "g": g})

    csv = STATA_CASES / f"{test_id}.csv"
    df.to_csv(csv, index=False)

    st_result = run_stata_do(_stata_do_template_ivregress(str(csv), "ivregress 2sls y w (x = z), cluster(g)"), test_id)
    py_result = IV2SLS(df, y="y", x_exog=["w"], x_endog=["x"], instruments=["z"], add_constant=True).fit(vce="cluster", cluster="g")
    py_dict = python_result_to_dict(py_result)

    comparisons = []
    comparisons.extend(compare_coefficients(py_dict["coefficients"], st_result.get("coefficients", [])))
    for field in ["nobs", "df_model", "df_resid", "r2", "r2_adj", "rmse", "f_stat", "f_pvalue", "cluster_count"]:
        py_field = py_dict.get("cluster_count" if field == "cluster_count" else field)
        st_field = st_result.get("n_clust" if field == "cluster_count" else field)
        comparisons.append(compare_scalars(py_field, st_field, field))
    comparisons.extend(compare_vce(py_dict["vce"], st_result.get("vce", np.zeros((0, 0))), py_dict["vce_row_names"], [c["name"] for c in st_result.get("coefficients", [])]))

    save_evidence(test_id, py_dict, st_result, comparisons, data=df)
    return all(p for p, _ in comparisons), comparisons


def experiment_s3_weak_iv():
    """S3: weak instrument design, check widstat."""
    test_id = "S3_weak_iv"
    rng = np.random.default_rng(3003)
    n = 200
    z = rng.normal(0, 1, n)
    u = rng.normal(0, 1, n)
    x = 0.05 * z + u + rng.normal(0, 0.5, n)  # very weak first stage
    y = 1.0 + 1.0 * x + u + rng.normal(0, 0.5, n)
    df = pd.DataFrame({"y": y, "x": x, "z": z})

    csv = STATA_CASES / f"{test_id}.csv"
    df.to_csv(csv, index=False)

    st_result = run_stata_do(_stata_do_template_ivreg2(str(csv), "ivreg2 y (x = z), robust"), test_id)
    df["__one"] = 1
    py_result = IVAbsorbingOLS(df, y="y", x_exog=[], x_endog=["x"], instruments=["z"], absorb="__one", add_constant=True, drop_singletons=False).fit(vce="robust")
    py_dict = python_result_to_dict(py_result)

    comparisons = []
    comparisons.extend(compare_coefficients(py_dict["coefficients"], st_result.get("coefficients", [])))
    # ivreg2 does not post e(df_r), so its derived F p-value is unavailable.
    for field in ["nobs", "df_model", "r2", "r2_adj", "rmse", "f_stat", "widstat"]:
        comparisons.append(compare_scalars(py_dict.get(field), st_result.get(field), field))
    comparisons.extend(compare_vce(py_dict["vce"], st_result.get("vce", np.zeros((0, 0))), py_dict["vce_row_names"], [c["name"] for c in st_result.get("coefficients", [])]))

    save_evidence(test_id, py_dict, st_result, comparisons, data=df)
    return all(p for p, _ in comparisons), comparisons


def experiment_s4_overidentification():
    """S4: overidentified model, check Hansen J."""
    test_id = "S4_overidentification"
    rng = np.random.default_rng(4004)
    n = 150
    z1 = rng.normal(0, 1, n)
    z2 = rng.normal(0, 1, n)
    w = rng.normal(0, 1, n)
    u = rng.normal(0, 1, n)
    x = 0.5 * z1 + 0.4 * z2 + 0.2 * w + u + rng.normal(0, 0.5, n)
    y = 1.0 + 0.7 * w + 1.2 * x + u + rng.normal(0, 0.5, n)
    df = pd.DataFrame({"y": y, "x": x, "w": w, "z1": z1, "z2": z2})

    csv = STATA_CASES / f"{test_id}.csv"
    df.to_csv(csv, index=False)

    st_result = run_stata_do(_stata_do_template_ivregress(str(csv), "ivregress 2sls y w (x = z1 z2), robust"), test_id)
    py_result = IV2SLS(df, y="y", x_exog=["w"], x_endog=["x"], instruments=["z1", "z2"], add_constant=True).fit(vce="robust")
    py_dict = python_result_to_dict(py_result)

    comparisons = []
    comparisons.extend(compare_coefficients(py_dict["coefficients"], st_result.get("coefficients", [])))
    for field in ["nobs", "df_model", "df_resid", "r2", "r2_adj", "rmse", "f_stat", "f_pvalue", "j_stat", "j_pvalue", "j_df"]:
        comparisons.append(compare_scalars(py_dict.get(field), st_result.get(field), field))
    comparisons.extend(compare_vce(py_dict["vce"], st_result.get("vce", np.zeros((0, 0))), py_dict["vce_row_names"], [c["name"] for c in st_result.get("coefficients", [])]))

    save_evidence(test_id, py_dict, st_result, comparisons, data=df)
    return all(p for p, _ in comparisons), comparisons


def experiment_s5_ivreghdfe_2fe_cluster():
    """S5: ivreghdfe with 2 FEs and cluster."""
    test_id = "S5_ivreghdfe_2fe_cluster"
    rng = np.random.default_rng(5005)
    n_firm = 30
    n_time = 5
    n = n_firm * n_time
    firm = np.repeat(np.arange(1, n_firm + 1), n_time)
    year = np.tile(np.arange(1, n_time + 1), n_firm)
    alpha = rng.normal(0, 1, n_firm)[firm - 1]
    gamma = rng.normal(0, 0.5, n_time)[year - 1]
    z = rng.normal(0, 1, n)
    u = rng.normal(0, 0.5, n)
    x = 0.5 * z + u + rng.normal(0, 0.3, n)
    y = 1.0 + 1.5 * x + alpha + gamma + u + rng.normal(0, 0.3, n)
    df = pd.DataFrame({"firm": firm, "year": year, "y": y, "x": x, "z": z})

    csv = STATA_CASES / f"{test_id}.csv"
    df.to_csv(csv, index=False)

    st_result = run_stata_do(_stata_do_template_ivreghdfe(str(csv), "ivreghdfe y (x = z), absorb(firm year) cluster(firm)"), test_id)
    py_result = IVAbsorbingOLS(df, y="y", x_exog=[], x_endog=["x"], instruments=["z"], absorb=["firm", "year"], add_constant=True, drop_singletons=True).fit(vce="cluster", cluster="firm")
    py_dict = python_result_to_dict(py_result)

    comparisons = []
    comparisons.extend(compare_coefficients(py_dict["coefficients"], st_result.get("coefficients", [])))
    for field in ["nobs", "df_model", "df_resid", "df_a", "r2", "r2_adj", "rmse", "f_stat", "f_pvalue", "cluster_count", "widstat"]:
        py_field = py_dict.get("cluster_count" if field == "cluster_count" else field)
        st_field = st_result.get("n_clust" if field == "cluster_count" else field)
        comparisons.append(compare_scalars(py_field, st_field, field))
    comparisons.extend(compare_vce(py_dict["vce"], st_result.get("vce", np.zeros((0, 0))), py_dict["vce_row_names"], [c["name"] for c in st_result.get("coefficients", [])]))

    save_evidence(test_id, py_dict, st_result, comparisons, data=df)
    return all(p for p, _ in comparisons), comparisons


def experiment_s6_liml():
    """S6: LIML vs 2SLS."""
    test_id = "S6_liml"
    rng = np.random.default_rng(6006)
    n = 120
    z1 = rng.normal(0, 1, n)
    z2 = rng.normal(0, 1, n)
    u = rng.normal(0, 1, n)
    x = 0.3 * z1 + 0.3 * z2 + u + rng.normal(0, 0.5, n)
    y = 1.0 + 1.0 * x + u + rng.normal(0, 0.5, n)
    df = pd.DataFrame({"y": y, "x": x, "z1": z1, "z2": z2})

    csv = STATA_CASES / f"{test_id}.csv"
    df.to_csv(csv, index=False)

    st_result = run_stata_do(_stata_do_template_ivreg2(str(csv), "ivreg2 y (x = z1 z2), liml"), test_id)
    df["__one"] = 1
    py_result = IVAbsorbingOLS(df, y="y", x_exog=[], x_endog=["x"], instruments=["z1", "z2"], absorb="__one", add_constant=True, drop_singletons=False).fit(vce="ols", estimator="liml")
    py_dict = python_result_to_dict(py_result)

    comparisons = []
    comparisons.extend(compare_coefficients(py_dict["coefficients"], st_result.get("coefficients", [])))
    # ivreg2 does not post e(df_r), so its derived F p-value is unavailable.
    for field in ["nobs", "df_model", "r2", "r2_adj", "rmse", "f_stat"]:
        comparisons.append(compare_scalars(py_dict[field], st_result.get(field), field))
    comparisons.extend(compare_vce(py_dict["vce"], st_result.get("vce", np.zeros((0, 0))), py_dict["vce_row_names"], [c["name"] for c in st_result.get("coefficients", [])]))

    save_evidence(test_id, py_dict, st_result, comparisons, data=df)
    return all(p for p, _ in comparisons), comparisons


def main():
    experiments = [
        experiment_s1_hand_computable_2sls,
        experiment_s2_random_2sls_cluster,
        experiment_s3_weak_iv,
        experiment_s4_overidentification,
        experiment_s5_ivreghdfe_2fe_cluster,
        experiment_s6_liml,
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
