"""Common utilities for M07 DID / Event Study modular audit v1.3.

Provides:
- Project path resolution
- Stata 17 batch execution for did_imputation / csdid / eventstudyinteract
- Log parsing (B_/SE_/E_ lines, event-study coefficients)
- Field-level comparison against Python ResultSchema
- Evidence saving
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
from stataflow.results.result import ResultSchema

PROJECT_ROOT = Path(__file__).resolve().parents[3]
M07_EVIDENCE = (
    PROJECT_ROOT
    / "docs"
    / "audit"
    / "modular-revalidation-v1.3"
    / "M07-did-event-study"
    / "evidence"
)
STATA_CASES = PROJECT_ROOT / "stata" / "cases" / "audit_v1_3_m07"
STATA_OUTPUT = PROJECT_ROOT / "stata" / "output" / "audit_v1_3_m07"

for _p in [M07_EVIDENCE, STATA_CASES, STATA_OUTPUT]:
    _p.mkdir(parents=True, exist_ok=True)


def _clean_stata_log(raw_log: str) -> str:
    """Remove Stata banner so output is printable and parseable."""
    lines = raw_log.splitlines()
    for i, line in enumerate(lines):
        if line.strip().startswith(". do "):
            return "\n".join(lines[i:])
    cleaned = []
    for line in lines:
        if (
            "Copyright" in line
            or "StataCorp" in line
            or "___  ____" in line
            or " Statistics and Data Science" in line
        ):
            continue
        cleaned.append(line)
    return "\n".join(cleaned)


def _add_leading_zero(val_str: str) -> str:
    """Stata displays numbers <1 as '.123'; add leading zero."""
    val_str = val_str.strip()
    if val_str in (".", "-."):
        return "nan"
    if val_str.startswith("."):
        return "0" + val_str
    if val_str.startswith("-."):
        return "-0" + val_str[1:]
    return val_str


def _to_float(val_str: str) -> Optional[float]:
    try:
        return float(_add_leading_zero(val_str))
    except ValueError:
        return None


def data_hash(df: pd.DataFrame) -> str:
    """Return a quick hash of the data for reproducibility records."""
    return hashlib.sha256(
        pd.util.hash_pandas_object(df, index=True).values.tobytes()
    ).hexdigest()[:16]


def did_imputation_stata_do(
    dta_path: str | Path,
    y: str,
    unit: str,
    time: str,
    first_treat: str,
    options: str = "",
) -> str:
    """Build a Stata .do script for did_imputation with B_/SE_/E_ extraction."""
    dta_path = str(dta_path).replace("\\", "/")
    options = options.strip()
    opts_line = f", {options}" if options else ""
    return f'''clear all
set more off
use "{dta_path}", clear
did_imputation {y} {unit} {time} {first_treat}{opts_line}
matrix b = e(b)
matrix V = e(V)
local names : colfullnames b
local i = 1
foreach name of local names {{
    display "B_`name'=" b[1, `i']
    display "SE_`name'=" sqrt(V[`i', `i'])
    local ++i
}}
display "E_N=" e(N)
display "E_N_CLUST=" e(N_clust)
display "M07_DIDIMP_OK"
'''


def csdid_stata_do(
    dta_path: str | Path,
    y: str,
    unit: str,
    time: str,
    first_treat: str,
    options: str = "",
    agg: str = "event",
) -> str:
    """Build a Stata .do script for csdid + csdid_estat event."""
    dta_path = str(dta_path).replace("\\", "/")
    options = options.strip()
    opts_line = f", {options}" if options else ""
    return f'''clear all
set more off
use "{dta_path}", clear
csdid {y}, ivar({unit}) time({time}) gvar({first_treat}) {options}
csdid_estat {agg}
matrix b = e(b)
matrix V = e(V)
local names : colfullnames b
local i = 1
foreach name of local names {{
    display "B_`name'=" b[1, `i']
    display "SE_`name'=" sqrt(V[`i', `i'])
    local ++i
}}
display "E_N=" e(N)
display "E_N_CLUST=" e(N_clust)
display "M07_CSDID_OK"
'''


def eventstudyinteract_stata_do(
    dta_path: str | Path,
    y: str,
    dummies: list[str],
    cohort: str,
    control_cohort: str,
    absorb: list[str],
    cluster: str,
) -> str:
    """Build a Stata .do script for eventstudyinteract."""
    dta_path = str(dta_path).replace("\\", "/")
    dummies_str = " ".join(dummies)
    absorb_str = " ".join(absorb)
    return f'''clear all
set more off
use "{dta_path}", clear
eventstudyinteract {y} {dummies_str}, cohort({cohort}) control_cohort({control_cohort}) absorb({absorb_str}) vce(cluster {cluster})
matrix b = e(b_iw)
matrix V = e(V_iw)
local names : colfullnames b
local i = 1
foreach name of local names {{
    display "B_`name'=" b[1, `i']
    display "SE_`name'=" sqrt(V[`i', `i'])
    local ++i
}}
display "E_N=" e(N)
display "E_N_CLUST=" e(N_clust)
display "M07_ESI_OK"
'''


def run_stata_did(
    df: pd.DataFrame,
    prefix: str,
    do_content: str,
) -> dict[str, Any]:
    """Save df to DTA, run Stata, parse and return structured results."""
    dta_path = STATA_CASES / f"{prefix}.dta"
    df.to_stata(str(dta_path), write_index=False)

    # Substitute DTA placeholder
    dta_posix = str(dta_path).replace("\\", "/")
    do_content = do_content.replace("{dta}", dta_posix)

    runner = StataRunner()
    result = runner.run_do_file(do_content, output_dir=str(STATA_OUTPUT), timeout=300)
    log_path = STATA_OUTPUT / f"{prefix}.log"
    log_path.write_text(
        result.output_content or result.error_message or "",
        encoding="utf-8",
        errors="replace",
    )

    if result.exit_code != 0:
        raise RuntimeError(
            f"Stata failed for {prefix}: {result.error_message}\nLog: {log_path}"
        )

    cleaned_log = _clean_stata_log(result.output_content or "")
    log_path.write_text(cleaned_log, encoding="utf-8", errors="replace")

    parsed = parse_did_log(cleaned_log)
    parsed["_log_path"] = str(log_path)
    parsed["_dta_path"] = str(dta_path)
    parsed["_exit_code"] = result.exit_code
    return parsed


def parse_did_log(log_content: str) -> dict[str, Any]:
    """Parse Stata log content with B_name=/SE_name=/E_N=/E_N_CLUST= lines."""
    out: dict[str, Any] = {}

    scalar_patterns = {
        "nobs": r"E_N=([\d.]+)",
        "n_clust": r"E_N_CLUST=([\d.]+)",
    }
    for key, pat in scalar_patterns.items():
        m = re.search(pat, log_content)
        if m:
            val = _to_float(m.group(1))
            if val is not None:
                out[key] = val

    coef_beta: dict[str, float] = {}
    coef_se: dict[str, float] = {}
    for m in re.finditer(r'^B_(\S+)=(-?[\d.eE+]+)', log_content, re.MULTILINE):
        name, val = m.group(1), _to_float(m.group(2))
        if val is not None:
            coef_beta[name] = val
    for m in re.finditer(r'^SE_(\S+)=(-?[\d.eE+]+)', log_content, re.MULTILINE):
        name, val = m.group(1), _to_float(m.group(2))
        if val is not None:
            coef_se[name] = val

    coefficients: list[dict[str, Any]] = []
    for name in coef_beta:
        beta = coef_beta[name]
        se = coef_se.get(name, 0.0)
        z = beta / se if se > 0 else float("nan")
        from scipy.stats import norm

        p = 2 * (1 - norm.cdf(abs(z))) if se > 0 else float("nan")
        coefficients.append(
            {
                "name": name,
                "beta": beta,
                "std_err": se,
                "z_stat": z,
                "p_value": p,
            }
        )
    # Prefer displayed coefficient table when present (csdid_estat event,
    # eventstudyinteract, etc.), because e(b) may hold group-time ATT instead.
    table_coefs = _parse_coef_table(log_content)
    if table_coefs:
        out["coefficients"] = table_coefs
    else:
        out["coefficients"] = coefficients

    out["_raw_log"] = log_content
    return out


def _parse_coef_table(log_content: str) -> list[dict[str, Any]]:
    """Parse Stata coefficient table delimited by ------+------."""
    lines = log_content.splitlines()
    coef_pattern = re.compile(
        r'^\s+([A-Za-z_][A-Za-z0-9_:]*)\s+\|\s+(-?\d*\.?\d+)\s+(-?\d*\.?\d+)'
    )
    coefficients: list[dict[str, Any]] = []
    in_table = False
    for line in lines:
        if '-------------+----------------------------------------------------------------' in line:
            in_table = True
            continue
        if in_table and line.strip() == '':
            in_table = False
            continue
        if in_table:
            m = coef_pattern.match(line)
            if m:
                beta = float(m.group(2))
                se = float(m.group(3))
                z = beta / se if se > 0 else float("nan")
                from scipy.stats import norm
                p = 2 * (1 - norm.cdf(abs(z))) if se > 0 else float("nan")
                coefficients.append({
                    "name": m.group(1),
                    "beta": beta,
                    "std_err": se,
                    "z_stat": z,
                    "p_value": p,
                })
    return coefficients


def tolerance_close(
    a: Optional[float],
    b: Optional[float],
    rtol: float = 1e-5,
    atol: float = 1e-6,
    name: str = "value",
) -> tuple[bool, str]:
    """Compare two scalars with relative/absolute tolerance."""
    a_nan = a is None or (isinstance(a, float) and np.isnan(a))
    b_nan = b is None or (isinstance(b, float) and np.isnan(b))
    if a_nan and b_nan:
        return True, f"{name}: Python={a}, Stata={b} (both missing) PASS"
    if a is None or b is None:
        return False, f"{name}: Python={a}, Stata={b} FAIL"
    if not (np.isfinite(a) and np.isfinite(b)):
        return np.isnan(a) and np.isnan(b), f"{name}: Python={a}, Stata={b}"
    diff = abs(a - b)
    denom = max(abs(b), 1e-15)
    rel = diff / denom
    passed = diff < atol or rel < rtol
    msg = (
        f"{name}: Python={a:.12g}, Stata={b:.12g}, abs={diff:.2e}, rel={rel:.2e} "
        f"{'PASS' if passed else 'FAIL'}"
    )
    return passed, msg


def compare_python_to_stata(
    py_result: ResultSchema,
    st_result: dict[str, Any],
    fields: Optional[list[str]] = None,
    compare_sample_mask: bool = True,
) -> dict[str, Any]:
    """Field-level comparison. Returns dict with pass/fail and messages."""
    if fields is None:
        fields = ["nobs", "n_clust"]

    diffs: dict[str, Any] = {
        "passed": True,
        "messages": [],
        "field_results": {},
    }

    def _record(name: str, passed: bool, msg: str) -> None:
        diffs["field_results"][name] = {"passed": passed, "message": msg}
        if not passed:
            diffs["passed"] = False
        diffs["messages"].append(msg)

    for field in fields:
        py_val = None
        if field == "nobs":
            py_val = float(py_result.sample.nobs)
        elif field == "n_clust":
            py_val = py_result.diagnostics.cluster_count
            if py_val is None and hasattr(py_result, "n_clust"):
                py_val = getattr(py_result, "n_clust", None)
        elif field == "df_model":
            py_val = py_result.fit.df_model
        elif field == "df_resid":
            py_val = py_result.fit.df_resid
        st_val = st_result.get(field)
        if py_val is None and st_val is None:
            continue
        passed, msg = tolerance_close(py_val, st_val, name=field)
        _record(field, passed, msg)

    # Coefficients
    st_coefs = {c["name"]: c for c in st_result.get("coefficients", [])}
    for py_coef in py_result.coefficients:
        name = py_coef.name
        st_coef = st_coefs.get(name)
        if st_coef is None:
            _record(f"coef_missing_{name}", False, f"Stata missing coefficient {name}")
            continue
        for metric in ["beta", "std_err", "t_stat", "p_value"]:
            py_val = getattr(py_coef, metric)
            st_val = st_coef.get(metric if metric != "std_err" else "std_err")
            if metric == "t_stat":
                st_val = st_coef.get("z_stat")
            # SE drives t/z; use tolerances that accommodate small VCE dof
            # differences (typically <2%) while still flagging real algorithmic
            # deviations (e.g. wrong control groups or sample selection).
            if metric == "std_err":
                rtol, atol = 2e-2, 1e-6
            elif metric in ("t_stat", "z_stat"):
                rtol, atol = 2e-2, 1e-6
            elif metric == "p_value":
                rtol, atol = 5e-2, 1e-6
            else:
                rtol, atol = 1e-5, 1e-6
            passed, msg = tolerance_close(
                py_val,
                st_val,
                name=f"{name}.{metric}",
                rtol=rtol,
                atol=atol,
            )
            _record(f"{name}.{metric}", passed, msg)

    # Sample mask
    if compare_sample_mask:
        py_mask = py_result.sample.sample_mask
        passed = len(py_mask) == py_result.sample.n_input_rows
        _record(
            "sample_mask_length",
            passed,
            f"sample_mask length: Python={len(py_mask)}, n_input_rows={py_result.sample.n_input_rows} {'PASS' if passed else 'FAIL'}",
        )
        if py_mask:
            passed = sum(py_mask) == py_result.sample.nobs
            _record(
                "sample_mask_sum",
                passed,
                f"sample_mask sum: Python={sum(py_mask)}, nobs={py_result.sample.nobs} {'PASS' if passed else 'FAIL'}",
            )

    return diffs


def save_evidence(
    prefix: str,
    py_result: ResultSchema,
    st_result: dict[str, Any],
    diffs: dict[str, Any],
) -> Path:
    """Persist comparison evidence as JSON."""
    if prefix.startswith("S"):
        evidence_dir = M07_EVIDENCE / "synthetic" / prefix
    elif prefix.startswith("P"):
        evidence_dir = M07_EVIDENCE / "property" / prefix
    else:
        evidence_dir = M07_EVIDENCE / "real-data" / prefix
    evidence_dir.mkdir(parents=True, exist_ok=True)

    py_dict = py_result.to_dict() if hasattr(py_result, "to_dict") else {}
    st_result_copy = {
        k: v for k, v in st_result.items() if not k.startswith(("_raw_log",))
    }

    payload = {
        "prefix": prefix,
        "python": py_dict,
        "stata": st_result_copy,
        "diffs": diffs,
    }
    path = evidence_dir / f"{prefix}_evidence.json"
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return path
