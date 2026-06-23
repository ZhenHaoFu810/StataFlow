"""Standalone reproduction script for M07 DID / Event Study confirmed findings.

Run with:
    python tests/audit_v1_3/m07_did_event_study/repro_m07_did_findings.py

Requires: local Stata 17 with did_imputation and csdid installed.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

import sys
_HERE = Path(__file__).resolve().parent
# Script is intended to be run from the project root.
PROJECT_ROOT = Path.cwd()
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(_HERE))

from stataflow import DIDImputation, csdid
from m07_audit_utils import (
    did_imputation_stata_do,
    csdid_stata_do,
    run_stata_did,
    M07_EVIDENCE,
)
from test_m07_synthetic import _make_panel

_MINI_DIR = M07_EVIDENCE / "minimal-reproductions"
_MINI_DIR.mkdir(parents=True, exist_ok=True)

_repro_summary: dict = {"findings": []}


def _save_mini(name: str, payload: dict) -> None:
    path = _MINI_DIR / f"{name}.json"
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    _repro_summary["findings"].append({"name": name, "path": str(path), **payload})


def finding_did_imputation_missing_never_treated():
    """M07-DID-001: Python drops missing first_treat; Stata uses them as controls."""
    print("\n=== Finding: DIDImputation missing first_treat encoding (M07-DID-001) ===")
    # No-never baseline where all units have positive first_treat
    df = _make_panel(
        seed=20260620, n_units=60, n_periods=10, cohorts=[6, 8, 10], include_never=False
    )
    # Mark the last 15 units as Stata-style never-treated (missing)
    last_units = sorted(df["id"].unique())[-15:]
    df.loc[df["id"].isin(last_units), "first_treat"] = np.nan

    prefix = "REPRO_DIDIMP_MISSING_NEVER"
    do = did_imputation_stata_do(
        "{dta}", "y", "id", "time", "first_treat",
        options="cluster(id) autosample minn(0)",
    )
    st = run_stata_did(df, prefix, do)
    py = DIDImputation(
        data=df, y="y", id="id", time="time", first_treat="first_treat"
    ).fit(cluster="id", autosample=True, minn=0)

    py_tau = py.coefficients[0]
    st_tau = next((c for c in st.get("coefficients", []) if c["name"] == "tau"), {})
    payload = {
        "python_nobs": py.sample.nobs,
        "stata_nobs": st.get("nobs"),
        "python_n_input_rows": py.sample.n_input_rows,
        "python_sum_mask": sum(py.sample.sample_mask),
        "python_tau_beta": py_tau.beta,
        "python_tau_se": py_tau.std_err,
        "stata_tau_beta": st_tau.get("beta"),
        "stata_tau_se": st_tau.get("std_err"),
    }
    for k, v in payload.items():
        print(f"{k:26} = {v}")
    _save_mini(prefix, payload)


def finding_did_imputation_zero_treated_as_treated():
    """M07-DID-004: Python treats 0 as never-treated; Stata treats 0 as treated."""
    print("\n=== Finding: DIDImputation first_treat=0 encoding (M07-DID-004) ===")
    df = _make_panel(
        seed=20260621, n_units=60, n_periods=10, cohorts=[6, 8], include_never=True
    )
    # Here the original never-treated units already have first_treat=0.
    prefix = "REPRO_DIDIMP_ZERO_NEVER"
    do = did_imputation_stata_do(
        "{dta}", "y", "id", "time", "first_treat",
        options="cluster(id) autosample minn(0)",
    )
    st = run_stata_did(df, prefix, do)
    py = DIDImputation(
        data=df, y="y", id="id", time="time", first_treat="first_treat"
    ).fit(cluster="id", autosample=True, minn=0)

    py_tau = py.coefficients[0]
    st_tau = next((c for c in st.get("coefficients", []) if c["name"] == "tau"), {})
    payload = {
        "python_nobs": py.sample.nobs,
        "stata_nobs": st.get("nobs"),
        "python_tau_beta": py_tau.beta,
        "python_tau_se": py_tau.std_err,
        "stata_tau_beta": st_tau.get("beta"),
        "stata_tau_se": st_tau.get("std_err"),
    }
    for k, v in payload.items():
        print(f"{k:26} = {v}")
    _save_mini(prefix, payload)


def finding_csdid_notyet_real_data():
    """M07-DID-003: CSDID notyet=True excludes never-treated, but Stata includes them."""
    print("\n=== Finding: CSDID notyet event aggregation on ezunem (M07-DID-003) ===")
    ez_path = PROJECT_ROOT / "research" / "data" / "public" / "did" / "ezunem_prepared.dta"
    df = pd.read_stata(ez_path)
    prefix = "REPRO_CSDID_NOTYET_REAL"
    do = csdid_stata_do(
        "{dta}",
        "uclms",
        "city",
        "year",
        "first_treat",
        options="method(reg) vce(cluster city) notyet",
        agg="event",
    )
    st = run_stata_did(df, prefix, do)
    model = csdid(
        data=df, y="uclms", id="city", time="year", first_treat="first_treat",
        method="reg", cluster="city", notyet=True,
    )
    py = model.estat_event()

    print(f"Python nobs = {py.sample.nobs}")
    print(f"Stata nobs  = {st.get('nobs')}")
    coef_rows = []
    print("Event coefficients:")
    for py_coef in py.coefficients:
        st_coef = next(
            (c for c in st.get("coefficients", []) if c["name"] == py_coef.name), {}
        )
        row = {
            "name": py_coef.name,
            "python_beta": py_coef.beta,
            "python_se": py_coef.std_err,
            "stata_beta": st_coef.get("beta"),
            "stata_se": st_coef.get("std_err"),
        }
        coef_rows.append(row)
        print(
            f"  {py_coef.name}: Python beta={py_coef.beta:.4f} SE={py_coef.std_err:.4f} | "
            f"Stata beta={st_coef.get('beta')} SE={st_coef.get('std_err')}"
        )
    _save_mini(
        prefix,
        {"python_nobs": py.sample.nobs, "stata_nobs": st.get("nobs"), "coefficients": coef_rows},
    )


if __name__ == "__main__":
    finding_did_imputation_missing_never_treated()
    finding_did_imputation_zero_treated_as_treated()
    finding_csdid_notyet_real_data()

    summary_path = _MINI_DIR / "REPRO_SUMMARY.json"
    summary_path.write_text(json.dumps(_repro_summary, indent=2, default=str), encoding="utf-8")
    print(f"\nReproduction script complete.")
    print(f"Summary: {summary_path}")
    print(f"Logs:    {PROJECT_ROOT / 'stata' / 'output' / 'audit_v1_3_m07'}")
