"""Shared utilities for the M10 Shared Infrastructure audit.

These helpers are isolated from product code and may only be used to generate
Stata evidence, parse logs, and compare Python/Stata results for the audit.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd

from stataflow.stata_runner import StataRunner

PROJECT_ROOT = Path(__file__).parents[3]
STATA_OUTPUT_DIR = PROJECT_ROOT / "stata" / "output" / "m10_audit"
EVIDENCE_DIR = (
    PROJECT_ROOT
    / "docs"
    / "audit"
    / "modular-revalidation-v1.3"
    / "M10-shared-infrastructure"
    / "evidence"
)


def _ensure_dirs() -> None:
    STATA_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    (EVIDENCE_DIR / "synthetic").mkdir(parents=True, exist_ok=True)
    (EVIDENCE_DIR / "real-data").mkdir(parents=True, exist_ok=True)
    (EVIDENCE_DIR / "property").mkdir(parents=True, exist_ok=True)
    (EVIDENCE_DIR / "minimal-reproductions").mkdir(parents=True, exist_ok=True)


def hash_dataframe(df: pd.DataFrame) -> str:
    """Return a stable SHA-256 hash of a DataFrame's bytes."""
    return hashlib.sha256(pd.util.hash_pandas_object(df).values.tobytes()).hexdigest()


def save_evidence_json(
    evidence: dict[str, Any],
    category: str,
    test_id: str,
) -> Path:
    """Save structured evidence to the module evidence directory."""
    _ensure_dirs()
    path = EVIDENCE_DIR / category / f"{test_id}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2, default=str)
    return path


def build_regression_do(
    stata_cmd: str,
    *,
    scalars: bool = True,
    coefficients: bool = True,
    vce_matrix: bool = True,
    sample_dta: Optional[str] = None,
) -> str:
    """Build a Stata do-file fragment that runs *stata_cmd* and emits key-value fields.

    The generated log can be parsed by :func:`parse_stata_log_fields`.  Optionally
    saves the ``e(sample)`` indicator to a Stata .dta file whose basename is
    *sample_dta*.
    """
    lines = [
        "version 17",
        "set more off",
        "set logtype text",
        stata_cmd,
        "",
    ]

    if scalars:
        scalar_specs = [
            ("nobs", "N"),
            ("df_model", "df_m"),
            ("df_resid", "df_r"),
            ("r2", "r2"),
            ("r2_adj", "r2_a"),
            ("rmse", "rmse"),
            ("f_stat", "F"),
            ("f_pvalue", "fp"),
            ("n_clust", "N_clust"),
            ("mss", "mss"),
            ("rss", "rss"),
            ("tss", "tss"),
        ]
        for key, expr in scalar_specs:
            lines.append(f'display "E_{key.upper()}=" e({expr})')

    if coefficients:
        lines.extend([
            "local cnames : colnames e(b)",
            'foreach n of local cnames {',
            '  display "B[" "`n\'" "]=" _b[`n\']',
            '  display "SE[" "`n\'" "]=" _se[`n\']',
            '}',
            "",
        ])

    if vce_matrix:
        lines.extend([
            "matrix __V = e(V)",
            "local rnames : rownames e(V)",
            "local i = 1",
            'foreach r of local rnames {',
            "  local j = 1",
            '  foreach c of local rnames {',
            '    display "V[" "`r\'" "," "`c\'" "]=" __V[`i\',`j\']',
            "    local j = `j' + 1",
            "  }",
            "  local i = `i' + 1",
            '}',
            "",
        ])

    if sample_dta is not None:
        sample_path = (STATA_OUTPUT_DIR / sample_dta).with_suffix(".dta")
        lines.extend([
            "gen byte __sample = e(sample)",
            f'save "{sample_path}" , replace',
        ])

    return "\n".join(lines)


def run_stata_do(
    df: pd.DataFrame,
    prefix: str,
    do_content: str,
    timeout: int = 120,
) -> tuple[str, Path]:
    """Save *df* as a Stata .dta and execute *do_content*.

    Returns the log text and the path to the saved .dta file.
    """
    _ensure_dirs()
    dta_path = STATA_OUTPUT_DIR / f"{prefix}.dta"
    do_path = STATA_OUTPUT_DIR / f"{prefix}.do"
    log_path = STATA_OUTPUT_DIR / f"{prefix}.log"

    df.to_stata(str(dta_path), write_index=False)

    full_do = [
        "version 17",
        "set more off",
        f'use "{dta_path}" , clear',
        do_content,
    ]

    runner = StataRunner()
    result = runner.run_do_file(
        do_content="\n".join(full_do),
        output_dir=str(STATA_OUTPUT_DIR),
        timeout=timeout,
    )
    log_text = result.output_content or ""
    if result.exit_code != 0:
        raise RuntimeError(
            f"Stata execution failed for {prefix}: exit_code={result.exit_code}\n"
            f"{result.error_message}\n{log_text[:2000]}"
        )
    return log_text, dta_path


def parse_stata_log_fields(log_text: str) -> dict[str, Any]:
    """Parse key-value fields emitted by :func:`build_regression_do`."""
    out: dict[str, Any] = {"scalars": {}, "coefficients": {}, "vce": {}}

    scalar_pattern = re.compile(r"E_([A-Z0-9_]+)\s*=\s*([-\d.eE]+)")
    for m in scalar_pattern.finditer(log_text):
        key = m.group(1).lower()
        val = m.group(2)
        if val in (".", "-."):
            continue
        if val.startswith("."):
            val = "0" + val
        try:
            out["scalars"][key] = float(val)
        except ValueError:
            out["scalars"][key] = val

    coef_pattern = re.compile(r"([BS]E?)\[(.+?)\]\s*=\s*([-\d.eE]+)")
    for m in coef_pattern.finditer(log_text):
        kind = m.group(1)
        name = m.group(2).strip()
        val = m.group(3)
        if val.startswith("."):
            val = "0" + val
        if name not in out["coefficients"]:
            out["coefficients"][name] = {}
        field = "beta" if kind == "B" else "std_err"
        out["coefficients"][name][field] = float(val)

    vce_pattern = re.compile(r"V\[(.+?),(.+?)\]\s*=\s*([-\d.eE]+)")
    for m in vce_pattern.finditer(log_text):
        row = m.group(1).strip()
        col = m.group(2).strip()
        val = m.group(3)
        if val.startswith("."):
            val = "0" + val
        out["vce"][(row, col)] = float(val)

    return out


def tolerance_close(
    a: float,
    b: float,
    rtol: float = 1e-6,
    atol: float = 1e-8,
    name: str = "value",
) -> tuple[bool, str]:
    """Return (ok, message) comparing two scalars."""
    if a is None or b is None:
        return False, f"{name}: one value is None (a={a}, b={b})"
    if np.isnan(a) and np.isnan(b):
        return True, f"{name}: both NaN"
    diff = abs(a - b)
    denom = max(abs(b), 1e-12)
    rel = diff / denom
    ok = diff <= atol or rel <= rtol
    msg = (
        f"{name}: Python={a}, Stata={b}, abs={diff:.2e}, "
        f"rel={rel:.2e} {'PASS' if ok else 'FAIL'}"
    )
    return ok, msg


def compare_dict_of_scalars(
    py: dict[str, float],
    st: dict[str, float],
    keys: list[str],
    rtol: float = 1e-6,
    atol: float = 1e-8,
) -> dict[str, Any]:
    """Compare a subset of scalar fields and return pass/fail report."""
    messages: list[str] = []
    all_ok = True
    for key in keys:
        ok, msg = tolerance_close(
            py.get(key), st.get(key), rtol=rtol, atol=atol, name=key
        )
        messages.append(msg)
        if not ok:
            all_ok = False
    return {"passed": all_ok, "messages": messages}


def extract_python_result(result) -> dict[str, Any]:
    """Convert a Python :class:`ResultSchema` into a comparable flat dict."""
    py: dict[str, Any] = {
        "nobs": result.sample.nobs,
        "n_input_rows": result.sample.n_input_rows,
        "df_model": result.fit.df_model,
        "df_resid": result.fit.df_resid,
        "df_a": result.fit.df_a,
        "r2": result.fit.r2,
        "r2_adj": result.fit.r2_adj,
        "rmse": result.fit.rmse,
        "f_stat": result.fit.f_stat,
        "f_pvalue": result.fit.f_pvalue,
        "rss": result.fit.rss,
        "tss": result.fit.tss,
        "mss": result.fit.mss,
        "n_clust": result.diagnostics.cluster_count,
        "coef_names": [c.name for c in result.coefficients],
        "active_coef_names": [c.name for c in result.coefficients if not c.is_omitted],
        "coefficients": {
            c.name: {"beta": c.beta, "std_err": c.std_err}
            for c in result.coefficients
        },
        "sample_mask": list(result.sample.sample_mask),
    }
    v = result.variance
    py["vce"] = {
        (r, c): v.values[i][j]
        for i, r in enumerate(v.row_names)
        for j, c in enumerate(v.row_names)
    }
    return py


def _is_stata_omitted_or_base(coef_name: str) -> bool:
    """Return True for Stata base/omitted coefficient rows like 0b.g or o.x1."""
    return bool(re.search(r"(^|#)(o\.\d+|\d+b\.|o\.)[^#]*", coef_name))


def compare_coefficients(
    py: dict[str, Any],
    st: dict[str, Any],
    rtol: float = 1e-6,
    atol: float = 1e-8,
) -> dict[str, Any]:
    """Compare coefficient betas and standard errors."""
    messages: list[str] = []
    all_ok = True
    py_coef = py["coefficients"]
    st_coef = st["coefficients"]

    active_st_names = [n for n in st_coef if not _is_stata_omitted_or_base(n)]

    active_py_names = py.get("active_coef_names", py["coef_names"])
    if active_py_names != active_st_names:
        py_set, st_set = set(active_py_names), set(active_st_names)
        messages.append(
            f"coef_names/order: Python(active)={active_py_names}, Stata(active)={active_st_names} "
            f"(sets equal={py_set == st_set})"
        )
        if py_set != st_set:
            all_ok = False
    else:
        messages.append(
            f"coef_names/order: Python(active)={active_py_names}, Stata={active_st_names} PASS"
        )

    for name in py["coef_names"]:
        if name not in st_coef:
            all_ok = False
            messages.append(f"coef {name}: missing in Stata")
            continue
        for field in ("beta", "std_err"):
            ok, msg = tolerance_close(
                py_coef[name][field],
                st_coef[name][field],
                rtol=rtol,
                atol=atol,
                name=f"{name}.{field}",
            )
            messages.append(msg)
            if not ok:
                all_ok = False

    return {"passed": all_ok, "messages": messages}


def compare_vce(
    py: dict[str, Any],
    st: dict[str, Any],
    rtol: float = 1e-6,
    atol: float = 1e-8,
) -> dict[str, Any]:
    """Compare full variance-covariance matrices by coefficient names."""
    messages: list[str] = []
    all_ok = True
    py_v = py["vce"]
    st_v = st["vce"]
    names = py["coef_names"]

    for i, row in enumerate(names):
        for j, col in enumerate(names):
            key = (row, col)
            if key not in st_v:
                all_ok = False
                messages.append(f"VCE[{row},{col}]: missing in Stata")
                continue
            ok, msg = tolerance_close(
                py_v[key],
                st_v[key],
                rtol=rtol,
                atol=atol,
                name=f"VCE[{row},{col}]",
            )
            messages.append(msg)
            if not ok:
                all_ok = False

    return {"passed": all_ok, "messages": messages}
