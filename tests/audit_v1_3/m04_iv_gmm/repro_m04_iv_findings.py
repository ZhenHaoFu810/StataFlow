"""Minimal reproductions of M04 IV/GMM confirmed findings."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from audit_utils import run_stata_do, python_result_to_dict, save_evidence

from stataflow import IV2SLS, IVAbsorbingOLS


STATA_CASES = Path(__file__).parent.parent.parent.parent / "stata" / "cases" / "audit_v1_3_m04"
STATA_CASES.mkdir(parents=True, exist_ok=True)


def _do_ivreg2(data_csv: str, cmd: str, test_id: str) -> dict:
    do = f'''clear all
set more off
import delimited "{data_csv}", varnames(1) clear
which ivreg2
{cmd}
display "E_N=" e(N)
display "E_DF_M=" e(df_m)
if e(df_r) < . {{
    display "E_DF_R=" e(df_r)
}}
display "E_R2=" e(r2)
display "E_R2_A=" e(r2_a)
display "E_RMSE=" e(rmse)
if e(F) < . {{
    display "E_F=" e(F)
}}
if e(widstat) < . {{
    display "E_WIDSTAT=" e(widstat)
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
'''
    return run_stata_do(do, test_id)


def repro_001_missing_weakiv_diagnostics():
    """M04-IV-001: IVAbsorbingOLS/IV2SLS do not expose weak-IV widstat."""
    test_id = "MR01_missing_weakiv_diagnostics"
    rng = np.random.default_rng(303)
    n = 200
    z = rng.normal(0, 1, n)
    u = rng.normal(0, 1, n)
    x = 0.05 * z + u + rng.normal(0, 0.5, n)
    y = 1.0 + 1.0 * x + u + rng.normal(0, 0.5, n)
    df = pd.DataFrame({"y": y, "x": x, "z": z})
    csv = STATA_CASES / f"{test_id}.csv"
    df.to_csv(csv, index=False)

    st = _do_ivreg2(str(csv), "ivreg2 y (x = z), robust", test_id)
    df["__one"] = 1
    py = python_result_to_dict(IVAbsorbingOLS(df, y="y", x_exog=[], x_endog=["x"], instruments=["z"], absorb="__one", add_constant=True, drop_singletons=False).fit(vce="robust"))
    msg = f"Stata widstat={st.get('widstat')}; Python widstat={py.get('widstat')}"
    print(f"\nM04-IV-001: {msg}")
    save_evidence(test_id, py, st, [(False, msg)], data=df)


def repro_002_liml_vce_mismatch():
    """M04-IV-002: LIML standard errors and fit stats differ from Stata."""
    test_id = "MR02_liml_vce_mismatch"
    rng = np.random.default_rng(606)
    n = 120
    z1 = rng.normal(0, 1, n)
    z2 = rng.normal(0, 1, n)
    u = rng.normal(0, 1, n)
    x = 0.3 * z1 + 0.3 * z2 + u + rng.normal(0, 0.5, n)
    y = 1.0 + 1.0 * x + u + rng.normal(0, 0.5, n)
    df = pd.DataFrame({"y": y, "x": x, "z1": z1, "z2": z2})
    csv = STATA_CASES / f"{test_id}.csv"
    df.to_csv(csv, index=False)

    st = _do_ivreg2(str(csv), "ivreg2 y (x = z1 z2), liml", test_id)
    df["__one"] = 1
    py = python_result_to_dict(IVAbsorbingOLS(df, y="y", x_exog=[], x_endog=["x"], instruments=["z1", "z2"], absorb="__one", add_constant=True, drop_singletons=False).fit(vce="ols", estimator="liml"))
    st_x = next((c for c in st.get("coefficients", []) if c["name"] == "x"), {})
    py_x = next((c for c in py.get("coefficients", []) if c["name"] == "x"), {})
    msg = (
        f"Stata x_beta={st_x.get('beta')} x_se={st_x.get('std_err')} rmse={st.get('rmse')} f={st.get('f_stat')}; "
        f"Python x_beta={py_x.get('beta')} x_se={py_x.get('std_err')} rmse={py.get('rmse')} f={py.get('f_stat')}"
    )
    print(f"\nM04-IV-002: {msg}")
    save_evidence(test_id, py, st, [(False, msg)], data=df)


def repro_003_constant_absorb_no_cons():
    """M04-IV-003: IVAbsorbingOLS with constant-only absorb omits _cons."""
    test_id = "MR03_constant_absorb_no_cons"
    rng = np.random.default_rng(707)
    n = 100
    z = rng.normal(0, 1, n)
    u = rng.normal(0, 1, n)
    x = 0.5 * z + u + rng.normal(0, 0.5, n)
    y = 1.0 + 1.0 * x + u + rng.normal(0, 0.5, n)
    df = pd.DataFrame({"y": y, "x": x, "z": z})
    csv = STATA_CASES / f"{test_id}.csv"
    df.to_csv(csv, index=False)

    st = _do_ivreg2(str(csv), "ivreg2 y (x = z), robust", test_id)
    df["__one"] = 1
    py = python_result_to_dict(IVAbsorbingOLS(df, y="y", x_exog=[], x_endog=["x"], instruments=["z"], absorb="__one", add_constant=True, drop_singletons=False).fit(vce="robust"))
    st_names = [c["name"] for c in st.get("coefficients", [])]
    py_names = [c["name"] for c in py.get("coefficients", [])]
    msg = f"Stata coefficients: {st_names}; Python coefficients: {py_names}"
    print(f"\nM04-IV-003: {msg}")
    save_evidence(test_id, py, st, [(False, msg)], data=df)


if __name__ == "__main__":
    repro_001_missing_weakiv_diagnostics()
    repro_002_liml_vce_mismatch()
    repro_003_constant_absorb_no_cons()
