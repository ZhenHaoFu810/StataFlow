"""M06 PPMLHDFE real-data dual-run audit tests (R1-R2).

Each test loads a classic Stata example dataset in Stata 17, runs ppmlhdfe,
exports the data, and then replicates the specification in Python.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from stataflow.estimators import PPMLHDFE

from .m06_audit_utils import (
    PROJECT_ROOT,
    STATA_OUTPUT,
    STATA_CASES,
    M06_EVIDENCE,
    StataRunner,
    _clean_stata_log,
    parse_ppmlhdfe_log,
    compare_python_to_stata,
    save_evidence,
)


def _webuse_do_template(
    webuse_name: str,
    command: str,
    coef_names: list[str],
    extra_setup: str = "",
) -> str:
    """Build a .do script that loads a Stata webuse dataset and runs ppmlhdfe."""
    csv_path = (STATA_OUTPUT / f"{webuse_name}_exported.csv").as_posix()
    scalar_block = """
display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_DF_A=" e(df_a)
display "E_LL=" e(ll)
display "E_DEVIANCE=" e(deviance)
display "E_R2_P=" e(r2_p)
display "E_CHI2=" e(chi2)
capture display "E_DF_R=" e(df_r)
if _rc==0 {
    display "E_DF_R=" e(df_r)
}
else {
    display "E_DF_R=."
}
capture display "E_N_CLUST=" e(N_clust)
if _rc==0 {
    display "E_N_CLUST=" e(N_clust)
}
"""
    coef_block = ""
    for name in coef_names:
        safe_name = name.replace("_", "_u_") if name == "_cons" else name
        display_name = name
        coef_block += f'''capture display "COEF_{safe_name}=" _b[{display_name}]
if _rc==0 {{
    display "COEF_{safe_name}=" _b[{display_name}]
    display "SE_{safe_name}=" _se[{display_name}]
}}
else {{
    display "COEF_{safe_name}=0"
    display "SE_{safe_name}=0"
}}
'''
    vce_block = "\nmatrix V = e(V)\n"
    for i, name_i in enumerate(coef_names):
        for j, name_j in enumerate(coef_names):
            safe_i = name_i.replace("_", "_u_") if name_i == "_cons" else name_i
            safe_j = name_j.replace("_", "_u_") if name_j == "_cons" else name_j
            vce_block += f'''display "VCE_{safe_i}_{safe_j}=" V[{i+1},{j+1}]\n'''

    return f'''clear all
set more off
webuse {webuse_name}, clear
{extra_setup}
export delimited "{csv_path}", nolabel replace
{command}
{scalar_block}
{coef_block}
{vce_block}
display "DONE"
'''


def _run_stata_webuse(
    webuse_name: str,
    command: str,
    prefix: str,
    coef_names: list[str],
    extra_setup: str = "",
) -> tuple[dict, pd.DataFrame]:
    """Run Stata webuse + ppmlhdfe and return parsed results plus exported CSV."""
    runner = StataRunner()
    do_content = _webuse_do_template(webuse_name, command, coef_names, extra_setup)
    result = runner.run_do_file(do_content, output_dir=str(STATA_OUTPUT))
    log_path = STATA_OUTPUT / f"{prefix}.log"
    log_path.write_text(result.output_content or result.error_message or "", encoding="utf-8", errors="replace")

    if result.exit_code != 0:
        raise RuntimeError(f"Stata failed for {prefix}: {result.error_message}\nLog: {log_path}")

    cleaned = _clean_stata_log(result.output_content or "")
    log_path.write_text(cleaned, encoding="utf-8", errors="replace")

    parsed = parse_ppmlhdfe_log(cleaned)
    parsed["_log_path"] = str(log_path)
    parsed["_command"] = command
    parsed["_exit_code"] = result.exit_code

    csv_path = STATA_OUTPUT / f"{webuse_name}_exported.csv"
    df = pd.read_csv(csv_path)
    return parsed, df


# ---------------------------------------------------------------------------
# R1: ships accident data with exposure
# ---------------------------------------------------------------------------
def test_r1_ships_exposure():
    y_var = "accident"
    x_vars = ["co_65_69", "co_70_74", "co_75_79", "op_75_79"]
    absorb_vars = ["ship"]
    coef_names = x_vars + ["_cons"]
    command = (
        f"ppmlhdfe {y_var} {' '.join(x_vars)}, "
        f"absorb({' '.join(absorb_vars)}) exposure(service) vce(robust)"
    )

    st, df = _run_stata_webuse(
        webuse_name="ships",
        command=command,
        prefix="R1_SHIPS_EXPOSURE",
        coef_names=coef_names,
    )

    py = PPMLHDFE(
        data=df,
        y=y_var,
        x=x_vars,
        absorb=absorb_vars,
        exposure="service",
    ).fit(vce="robust")

    fields = ["nobs", "df_model", "df_a", "ll", "deviance", "pseudo_r2"]
    diffs = compare_python_to_stata(py, st, fields=fields, compare_vce=True)
    save_evidence("R1_SHIPS_EXPOSURE", py, st, diffs)
    assert diffs["passed"], "\n".join(diffs["messages"])


# ---------------------------------------------------------------------------
# R2: medpar length-of-stay with provider FE and cluster
# ---------------------------------------------------------------------------
def test_r2_medpar_provider_cluster():
    y_var = "los"
    x_vars = ["age", "white", "hmo", "died"]
    absorb_vars = ["provid"]
    cluster_var = "provid"
    coef_names = x_vars + ["_cons"]
    extra_setup = "egen provid = group(provnum)"
    command = (
        f"ppmlhdfe {y_var} {' '.join(x_vars)}, "
        f"absorb({' '.join(absorb_vars)}) vce(cluster {cluster_var})"
    )

    st, df = _run_stata_webuse(
        webuse_name="medpar",
        command=command,
        prefix="R2_MEDPAR_PROVIDER_CLUSTER",
        coef_names=coef_names,
        extra_setup=extra_setup,
    )

    if "n_clust" in st and st["n_clust"] is not None:
        st["df_resid"] = st["n_clust"] - 1

    py = PPMLHDFE(
        data=df,
        y=y_var,
        x=x_vars,
        absorb=absorb_vars,
    ).fit(vce="cluster", cluster=cluster_var)

    fields = [
        "nobs", "df_model", "df_a", "df_resid", "n_clust",
        "ll", "deviance", "pseudo_r2",
    ]
    diffs = compare_python_to_stata(py, st, fields=fields, compare_vce=True)
    save_evidence("R2_MEDPAR_PROVIDER_CLUSTER", py, st, diffs)
    assert diffs["passed"], "\n".join(diffs["messages"])
