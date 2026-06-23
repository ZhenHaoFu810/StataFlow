"""Minimal reproductions of M03 HDFE confirmed findings."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from audit_utils import run_stata_do, python_result_to_dict, save_evidence

from stataflow import AbsorbingOLS
from stataflow.estimators._absorb_spec import AbsorbSpec


STATA_CASES = Path(__file__).parent.parent.parent.parent / "stata" / "cases" / "audit_v1_3_m03"
STATA_CASES.mkdir(parents=True, exist_ok=True)


def _do_template(data_csv: str, cmd: str) -> str:
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
display "E_DF_A=" e(df_a)
if e(N_clust) < . {{
    display "E_N_CLUST=" e(N_clust)
}}
local coefs : colnames e(b)
local k : word count `coefs'
forvalues i = 1/`k' {{
    local name : word `i' of `coefs'
    display "COEF `name' " _b[`name'] " " _se[`name']
}}
'''


def repro_001_nested_fe_cluster():
    """M03-HDFE-001: FE nested in cluster not detected."""
    test_id = "MR01_nested_fe_cluster"
    rng = np.random.default_rng(303)
    n_firm = 24
    n_time = 4
    n = n_firm * n_time
    firm = np.repeat(np.arange(1, n_firm + 1), n_time)
    year = np.tile(np.arange(1, n_time + 1), n_firm)
    industry = (firm - 1) // 4 + 1
    alpha = rng.normal(0, 1, n_firm)[firm - 1]
    eta = rng.normal(0, 1, 6)[industry - 1]
    x = rng.normal(0, 1, n) + 0.2 * eta
    y = 1.0 + 1.5 * x + alpha + eta + rng.normal(0, 0.5, n)
    df = pd.DataFrame({"firm": firm, "year": year, "industry": industry, "y": y, "x": x})
    csv = STATA_CASES / f"{test_id}.csv"
    df.to_csv(csv, index=False)

    st = run_stata_do(_do_template(str(csv), "reghdfe y x, absorb(firm year) vce(cluster industry)"), test_id)
    py = python_result_to_dict(AbsorbingOLS(df, y="y", x=["x"], absorb=["firm", "year"], add_constant=True, drop_singletons=True).fit(vce="cluster", cluster="industry"))
    msg = f"Stata df_a={st.get('df_a')} n_clust={st.get('n_clust')}; Python df_a={py.get('df_a')} cluster_count={py.get('cluster_count')}"
    print(f"\nM03-HDFE-001: {msg}")
    save_evidence(test_id, py, st, [(False, msg)], data=df)


def repro_002_slope_absorption():
    """M03-HDFE-002: slope absorption df_a and VCE mismatch."""
    test_id = "MR02_slope_absorption"
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

    st = run_stata_do(_do_template(str(csv), "reghdfe y x, absorb(firm##c.year) vce(cluster firm)"), test_id)
    py = python_result_to_dict(AbsorbingOLS(df, y="y", x=["x"], absorb=[AbsorbSpec(var="firm", slopes=["year"], has_intercept=True)], add_constant=True, drop_singletons=True).fit(vce="cluster", cluster="firm"))
    st_x = next((c for c in st.get("coefficients", []) if c["name"] == "x"), {})
    py_x = next((c for c in py.get("coefficients", []) if c["name"] == "x"), {})
    msg = (
        f"Stata df_a={st.get('df_a')} x_beta={st_x.get('beta')} x_se={st_x.get('std_err')}; "
        f"Python df_a={py.get('df_a')} x_beta={py_x.get('beta')} x_se={py_x.get('std_err')}"
    )
    print(f"\nM03-HDFE-002: {msg}")
    save_evidence(test_id, py, st, [(False, msg)], data=df)


def repro_003_disconnected_graph():
    """M03-HDFE-003: disconnected FE graph leads to perfect fit / missing r2_adj."""
    test_id = "MR03_disconnected_graph"
    rng = np.random.default_rng(404)
    rows = []
    for f in [1, 2, 3, 4]:
        years_for_f = [(f % 4) + 1, ((f + 1) % 4) + 1]
        for t in years_for_f:
            rows.append({"firm": f, "year": t})
    df = pd.DataFrame(rows)
    df["x"] = rng.normal(0, 1, len(df))
    alpha = {1: 1.0, 2: 2.0, 3: -1.0, 4: -2.0}
    gamma = {1: 0.5, 2: -0.5, 3: 0.3, 4: -0.3}
    df["y"] = 1.0 + 2.0 * df["x"] + df["firm"].map(alpha) + df["year"].map(gamma) + rng.normal(0, 0.1, len(df))
    csv = STATA_CASES / f"{test_id}.csv"
    df.to_csv(csv, index=False)

    st = run_stata_do(_do_template(str(csv), "reghdfe y x, absorb(firm year) vce(ols)"), test_id)
    py = python_result_to_dict(AbsorbingOLS(df, y="y", x=["x"], absorb=["firm", "year"], add_constant=True, drop_singletons=True).fit(vce="ols"))
    msg = f"Stata df_r={st.get('df_resid')} r2_adj={st.get('r2_adj')}; Python df_r={py.get('df_resid')} r2_adj={py.get('r2_adj')}"
    print(f"\nM03-HDFE-003: {msg}")
    save_evidence(test_id, py, st, [(False, msg)], data=df)


if __name__ == "__main__":
    repro_001_nested_fe_cluster()
    repro_002_slope_absorption()
    repro_003_disconnected_graph()
