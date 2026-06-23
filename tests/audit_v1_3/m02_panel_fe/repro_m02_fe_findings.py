"""Minimal reproductions of M02 Panel/FE confirmed findings.

Run with: python tests/audit_v1_3/m02_panel_fe/repro_m02_fe_findings.py

Each function isolates one deviation from Stata 17 and prints the
Python vs Stata discrepancy.  These scripts intentionally use small,
hand-verifiable data so the root cause is easy to inspect.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from audit_utils import run_stata_do, python_result_to_dict, compare_scalars

from stataflow import FixedEffectsOLS
from stataflow.compat.stata import xtreg_fe


STATA_CASES = Path(__file__).parent.parent.parent.parent / "stata" / "cases" / "audit_v1_3_m02"
STATA_CASES.mkdir(parents=True, exist_ok=True)


def _do_template(data_csv: str, cmd: str) -> str:
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
local coefs : colnames e(b)
local k : word count `coefs'
forvalues i = 1/`k' {{
    local name : word `i' of `coefs'
    display "COEF `name' " _b[`name'] " " _se[`name']
}}
'''


from audit_utils import save_evidence

def repro_001_f_pvalue_df_model():
    """M02-FE-001: FE F-statistic p-value uses wrong df_model."""
    test_id = "MR01_f_pvalue_df_model"
    df = pd.DataFrame({
        "entity": [1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3],
        "time":   [1, 2, 3, 4] * 3,
        "y": [1.0, 2.1, 3.0, 4.2, 2.0, 3.2, 4.1, 5.0, 0.5, 1.8, 2.9, 4.0],
        "x": [0.5, 1.0, 1.5, 2.0, 1.2, 1.8, 2.4, 3.0, 0.2, 0.9, 1.6, 2.5],
    })
    csv = STATA_CASES / "repro_001.csv"
    df.to_csv(csv, index=False)
    st = run_stata_do(_do_template(str(csv), "xtset entity time\nxtreg y x, fe"), test_id)
    py = python_result_to_dict(FixedEffectsOLS(df, y="y", x=["x"], fe="entity", add_constant=True).fit(vce="ols"))
    msg = (
        f"Stata e(df_m)={st['df_model']}, F p-value={st['f_pvalue']}; "
        f"Python df_model={py['df_model']}, F p-value={py['f_pvalue']}"
    )
    print(f"\nM02-FE-001: {msg}")
    save_evidence(test_id, py, st, [(False, msg)], data=df)


def repro_002_collinear_drop_crash():
    """M02-FE-002: add_constant=True + within-collinear drop crashes."""
    test_id = "MR02_collinear_drop_crash"
    df = pd.DataFrame({
        "entity": [1, 1, 1, 1, 2, 2, 2, 2],
        "y": [1.0, 2.0, 3.0, 4.0, 2.0, 3.0, 4.0, 5.0],
        "x": [1.0, 2.0, 3.0, 4.0, 2.0, 3.0, 4.0, 5.0],
        "z": [1.0, 2.0, 3.0, 4.0, 2.0, 3.0, 4.0, 5.0],
    })
    print("\nM02-FE-002: within-collinear + add_constant crash")
    try:
        FixedEffectsOLS(df, y="y", x=["x", "z"], fe="entity", add_constant=True).fit(vce="ols")
        msg = "Python completed without exception (unexpected)"
        print(f"  {msg}")
        save_evidence(test_id, {"status": "no exception"}, None, [(False, msg)], data=df)
    except Exception as exc:
        msg = f"Python raised {type(exc).__name__}: {exc}; Stata completes"
        print(f"  {msg}")
        save_evidence(test_id, {"error": str(exc)}, None, [(False, msg)], data=df)


def repro_003_unbalanced_cons():
    """M02-FE-003: _cons coefficient/SE deviates on unbalanced panel."""
    test_id = "MR03_unbalanced_cons"
    df = pd.DataFrame({
        "entity": [1, 1, 1, 1, 2, 2, 3, 3, 3],
        "time":   [1, 2, 3, 4, 1, 2, 1, 2, 3],
        "y": [1.0, 2.1, 2.9, 4.2, 2.1, 3.0, 0.4, 1.9, 3.1],
        "x": [0.5, 1.0, 1.5, 2.0, 1.1, 1.9, 0.1, 0.8, 1.7],
    })
    csv = STATA_CASES / "repro_003.csv"
    df.to_csv(csv, index=False)
    st = run_stata_do(_do_template(str(csv), "xtset entity time\nxtreg y x, fe"), test_id)
    py = python_result_to_dict(FixedEffectsOLS(df, y="y", x=["x"], fe="entity", add_constant=True).fit(vce="ols"))
    st_cons = next((c for c in st["coefficients"] if c["name"] == "_cons"), {})
    py_cons = next((c for c in py["coefficients"] if c["name"] == "_cons"), {})
    msg = (
        f"Stata _cons beta={st_cons.get('beta')} se={st_cons.get('std_err')}; "
        f"Python _cons beta={py_cons.get('beta')} se={py_cons.get('std_err')}"
    )
    print(f"\nM02-FE-003: {msg}")
    save_evidence(test_id, py, st, [(False, msg)], data=df)


def repro_004_cluster_df_model():
    """M02-FE-004: cluster FE df_model=0 vs 1 and r2_adj mismatch."""
    test_id = "MR04_cluster_df_model"
    rng = np.random.default_rng(7)
    n = 60
    df = pd.DataFrame({
        "entity": np.repeat(np.arange(1, 11), 6),
        "time": np.tile(np.arange(1, 7), 10),
        "x": rng.normal(0, 1, n),
        "y": rng.normal(0, 1, n),
    })
    csv = STATA_CASES / "repro_004.csv"
    df.to_csv(csv, index=False)
    st = run_stata_do(_do_template(str(csv), "xtset entity time\nxtreg y x, fe cluster(entity)"), test_id)
    py = python_result_to_dict(FixedEffectsOLS(df, y="y", x=["x"], fe="entity", add_constant=True).fit(vce="cluster", cluster="entity"))
    msg = f"Stata df_model={st['df_model']} r2_adj={st['r2_adj']}; Python df_model={py['df_model']} r2_adj={py['r2_adj']}"
    print(f"\nM02-FE-004: {msg}")
    save_evidence(test_id, py, st, [(False, msg)], data=df)


def repro_005_wrapper_default_constant():
    """M02-FE-005: xtreg_fe wrapper default constant=False."""
    test_id = "MR05_wrapper_default_constant"
    df = pd.DataFrame({
        "entity": [1, 1, 2, 2],
        "y": [1.0, 2.0, 2.0, 3.0],
        "x": [0.5, 1.5, 1.0, 2.0],
    })
    py = xtreg_fe(df, y="y", x=["x"], fe="entity")
    names = [c.name for c in py.coefficients]
    msg = f"Python xtreg_fe names={names}; Stata xtreg, fe always reports _cons"
    print(f"\nM02-FE-005: {msg}")
    save_evidence(test_id, {"coefficient_names": names}, None, [(False, msg)], data=df)


def repro_006_within_collinear_not_dropped():
    """M02-FE-006: near-collinear within variables not omitted."""
    test_id = "MR06_within_collinear_not_dropped"
    rng = np.random.default_rng(8)
    n = 40
    entity = np.repeat(np.arange(1, 9), 5)
    x = rng.normal(0, 1, n)
    df = pd.DataFrame({
        "entity": entity,
        "time": np.tile(np.arange(1, 6), 8),
        "y": x + rng.normal(0, 0.1, n) + rng.normal(0, 1, 8)[entity - 1],
        "x": x,
        "w": x + 1e-10 * rng.normal(0, 1, n),
    })
    csv = STATA_CASES / "repro_006.csv"
    df.to_csv(csv, index=False)
    st = run_stata_do(_do_template(str(csv), "xtset entity time\nxtreg y x w, fe"), test_id)
    py = python_result_to_dict(FixedEffectsOLS(df, y="y", x=["x", "w"], fe="entity", add_constant=True).fit(vce="ols"))
    st_names = [c["name"] for c in st["coefficients"]]
    py_names = [c["name"] for c in py["coefficients"]]
    msg = f"Stata kept={st_names}; Python kept={py_names}"
    print(f"\nM02-FE-006: {msg}")
    save_evidence(test_id, py, st, [(False, msg)], data=df)


def repro_007_entity_invariant_not_dropped():
    """M02-FE-007: entity-invariant regressor not dropped."""
    test_id = "MR07_entity_invariant_not_dropped"
    df = pd.DataFrame({
        "entity": [1, 1, 1, 2, 2, 2, 3, 3, 3],
        "y": [1.0, 2.0, 3.0, 2.0, 3.0, 4.0, 0.0, 1.0, 2.0],
        "x": [0.5, 1.0, 1.5, 1.0, 1.5, 2.0, 0.0, 0.5, 1.0],
        "z": [1.0, 1.0, 1.0, 2.0, 2.0, 2.0, 3.0, 3.0, 3.0],
    })
    print("\nM02-FE-007: entity-invariant regressor not dropped")
    try:
        py = python_result_to_dict(FixedEffectsOLS(df, y="y", x=["x", "z"], fe="entity", add_constant=True).fit(vce="ols"))
        z_coef = next((c for c in py["coefficients"] if c["name"] == "z"), {})
        msg = f"Python z coef={z_coef.get('beta')} se={z_coef.get('std_err')}; Stata drops z"
        print(f"  {msg}")
        save_evidence(test_id, py, None, [(False, msg)], data=df)
    except Exception as exc:
        msg = f"Python raised {type(exc).__name__}: {exc}; Stata drops z"
        print(f"  {msg}")
        save_evidence(test_id, {"error": str(exc)}, None, [(False, msg)], data=df)


if __name__ == "__main__":
    repro_001_f_pvalue_df_model()
    repro_002_collinear_drop_crash()
    repro_003_unbalanced_cons()
    repro_004_cluster_df_model()
    repro_005_wrapper_default_constant()
    repro_006_within_collinear_not_dropped()
    repro_007_entity_invariant_not_dropped()
