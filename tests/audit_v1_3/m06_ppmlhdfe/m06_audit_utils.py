"""Common utilities for M06 PPMLHDFE modular audit v1.3.

Provides:
- Project path resolution
- Stata 17 batch execution for ppmlhdfe
- Log parsing (coefficients, scalars, VCE, predict summaries)
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
M06_EVIDENCE = PROJECT_ROOT / "docs" / "audit" / "modular-revalidation-v1.3" / "M06-ppmlhdfe" / "evidence"
STATA_CASES = PROJECT_ROOT / "stata" / "cases" / "audit_v1_3_m06"
STATA_OUTPUT = PROJECT_ROOT / "stata" / "output" / "audit_v1_3_m06"

for _p in [M06_EVIDENCE, STATA_CASES, STATA_OUTPUT]:
    _p.mkdir(parents=True, exist_ok=True)


def _clean_stata_log(raw_log: str) -> str:
    """Remove Stata banner/copyright lines so output is printable and parseable."""
    lines = raw_log.splitlines()
    for i, line in enumerate(lines):
        if line.strip().startswith(". do "):
            return "\n".join(lines[i:])
    # Fallback: drop known banner lines
    cleaned = []
    for line in lines:
        if "Copyright" in line or "StataCorp" in line or "___  ____" in line or " Statistics and Data Science" in line:
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


def ppmlhdfe_stata_do_template(
    data_csv: str | Path,
    command: str,
    y_var: str,
    coef_names: Optional[list[str]] = None,
    predict_types: Optional[list[str]] = None,
    include_vce: bool = True,
) -> str:
    """Return a Stata .do script that runs ppmlhdfe and emits parseable fields."""
    data_csv = str(data_csv).replace("\\", "/")

    # Build scalar extraction block
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
"""
    capture_n_clust = """
capture display "E_N_CLUST=" e(N_clust)
if _rc==0 {
    display "E_N_CLUST=" e(N_clust)
}
"""

    coef_block = ""
    if coef_names:
        for name in coef_names:
            safe_name = name.replace("_", "_u_") if name == "_cons" else name
            # For _cons, Stata name is literally _cons; for factor syntax use tokens
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

    vce_block = ""
    if include_vce and coef_names:
        vce_block += "\nmatrix V = e(V)\n"
        for i, name_i in enumerate(coef_names):
            for j, name_j in enumerate(coef_names):
                safe_i = name_i.replace("_", "_u_") if name_i == "_cons" else name_i
                safe_j = name_j.replace("_", "_u_") if name_j == "_cons" else name_j
                vce_block += f'''display "VCE_{safe_i}_{safe_j}=" V[{i+1},{j+1}]\n'''

    predict_block = ""
    if predict_types:
        for ptype in predict_types:
            # Stata predict options for ppmlhdfe
            stata_opt = ptype
            if ptype == "residuals":
                stata_opt = "r"
            elif ptype == "pearson":
                stata_opt = "pearson"
            elif ptype == "deviance":
                stata_opt = "deviance"
            elif ptype == "mu":
                stata_opt = "mu"
            elif ptype == "xb":
                stata_opt = "xb"
            predict_block += f'''\ncapture drop __pred_{ptype}
capture predict double __pred_{ptype}, {stata_opt}
if _rc==0 {{
    summarize __pred_{ptype}, detail
    display "PRED_{ptype}_MEAN=" r(mean)
    display "PRED_{ptype}_SD=" r(sd)
    display "PRED_{ptype}_MIN=" r(min)
    display "PRED_{ptype}_MAX=" r(max)
}}\n'''

    return f'''clear all
set more off
import delimited "{data_csv}", varnames(1) clear
{command}
{scalar_block}
{capture_n_clust}
{coef_block}
{vce_block}
{predict_block}
display "DONE"
'''


def run_stata_ppmlhdfe(
    df: pd.DataFrame,
    command: str,
    y_var: str,
    prefix: str,
    coef_names: Optional[list[str]] = None,
    predict_types: Optional[list[str]] = None,
    include_vce: bool = True,
) -> dict[str, Any]:
    """Save df to CSV, run Stata ppmlhdfe, parse and return structured results."""
    csv_path = STATA_CASES / f"{prefix}.csv"
    df.to_csv(csv_path, index=False)

    do_content = ppmlhdfe_stata_do_template(
        data_csv=csv_path,
        command=command,
        y_var=y_var,
        coef_names=coef_names,
        predict_types=predict_types,
        include_vce=include_vce,
    )

    runner = StataRunner()
    result = runner.run_do_file(do_content, output_dir=str(STATA_OUTPUT))
    log_path = STATA_OUTPUT / f"{prefix}.log"
    log_path.write_text(result.output_content or result.error_message or "", encoding="utf-8", errors="replace")

    if result.exit_code != 0:
        raise RuntimeError(f"Stata failed for {prefix}: {result.error_message}\nLog: {log_path}")

    cleaned_log = _clean_stata_log(result.output_content or "")
    log_path.write_text(cleaned_log, encoding="utf-8", errors="replace")

    parsed = parse_ppmlhdfe_log(cleaned_log)
    parsed["_log_path"] = str(log_path)
    parsed["_csv_path"] = str(csv_path)
    parsed["_command"] = command
    parsed["_exit_code"] = result.exit_code
    return parsed


def parse_ppmlhdfe_log(log_content: str) -> dict[str, Any]:
    """Parse Stata log content emitted by ppmlhdfe_stata_do_template."""
    out: dict[str, Any] = {}

    scalar_patterns = {
        "nobs": r"E_N=([\d.]+)",
        "df_model": r"E_DF_M=([\d.]+)",
        "df_a": r"E_DF_A=([\d.]+)",
        "df_resid": r"E_DF_R=([\d.]+|-?\.|\.)",
        "ll": r"E_LL=(-?[\d.eE+]+)",
        "deviance": r"E_DEVIANCE=(-?[\d.eE+]+)",
        "pseudo_r2": r"E_R2_P=(-?[\d.eE+]+)",
        "chi2": r"E_CHI2=(-?[\d.eE+]+)",
        "n_clust": r"E_N_CLUST=([\d.]+)",
    }
    for key, pat in scalar_patterns.items():
        m = re.search(pat, log_content)
        if m:
            val = _to_float(m.group(1))
            if val is not None:
                out[key] = val

    coefficients: list[dict[str, Any]] = []
    coef_beta: dict[str, float] = {}
    coef_se: dict[str, float] = {}
    for m in re.finditer(r'^COEF_(\S+)=(-?[\d.eE+]+)', log_content, re.MULTILINE):
        safe_name, val = m.group(1), _to_float(m.group(2))
        name = "_cons" if safe_name == "_u_cons" else safe_name
        if val is not None:
            coef_beta[name] = val
    for m in re.finditer(r'^SE_(\S+)=(-?[\d.eE+]+)', log_content, re.MULTILINE):
        safe_name, val = m.group(1), _to_float(m.group(2))
        name = "_cons" if safe_name == "_u_cons" else safe_name
        if val is not None:
            coef_se[name] = val

    for name in coef_beta:
        if name in coef_se:
            beta = coef_beta[name]
            se = coef_se[name]
            z = beta / se if se > 0 else float("nan")
            from scipy.stats import norm
            p = 2 * (1 - norm.cdf(abs(z))) if se > 0 else float("nan")
            coefficients.append({
                "name": name,
                "beta": beta,
                "std_err": se,
                "z_stat": z,
                "p_value": p,
            })
    out["coefficients"] = coefficients

    # VCE matrix
    vce_names = list(coef_beta.keys())
    vce_matrix: Optional[np.ndarray] = None
    if vce_names:
        n = len(vce_names)
        vce_matrix = np.zeros((n, n))
        for i, name_i in enumerate(vce_names):
            for j, name_j in enumerate(vce_names):
                safe_i = "_u_cons" if name_i == "_cons" else name_i
                safe_j = "_u_cons" if name_j == "_cons" else name_j
                pat = rf"^VCE_{re.escape(safe_i)}_{re.escape(safe_j)}=(-?[\d.eE+]+)"
                m = re.search(pat, log_content, re.MULTILINE)
                if m:
                    vce_matrix[i, j] = _to_float(m.group(1)) or 0.0
        out["vce_matrix"] = vce_matrix
        out["vce_names"] = vce_names

    predict: dict[str, dict[str, float]] = {}
    for ptype in ["xb", "mu", "residuals", "pearson", "deviance"]:
        number = r"-?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"
        pat = rf"PRED_{ptype}_(MEAN|SD|MIN|MAX)=({number})"
        vals = {}
        for m in re.finditer(pat, log_content):
            vals[m.group(1).lower()] = _to_float(m.group(2))
        if vals:
            predict[ptype] = vals
    out["predict"] = predict

    out["_raw_log"] = log_content
    return out


def tolerance_close(
    a: Optional[float],
    b: Optional[float],
    rtol: float = 1e-6,
    atol: float = 1e-8,
    name: str = "value",
) -> tuple[bool, str]:
    """Compare two scalars with relative/absolute tolerance."""
    if a is None or b is None:
        return a == b, f"{name}: Python={a}, Stata={b}"
    if not (np.isfinite(a) and np.isfinite(b)):
        return np.isnan(a) and np.isnan(b), f"{name}: Python={a}, Stata={b}"
    diff = abs(a - b)
    denom = max(abs(b), 1e-15)
    rel = diff / denom
    passed = diff < atol or rel < rtol
    msg = f"{name}: Python={a:.12g}, Stata={b:.12g}, abs={diff:.2e}, rel={rel:.2e} {'PASS' if passed else 'FAIL'}"
    return passed, msg


def compare_python_to_stata(
    py_result: ResultSchema,
    st_result: dict[str, Any],
    fields: Optional[list[str]] = None,
    compare_vce: bool = True,
    predict_types: Optional[list[str]] = None,
    coefficient_rtol: float = 1e-6,
    vce_rtol: float = 1e-6,
    predict_rtol: float = 1e-6,
    predict_atol: float = 1e-8,
) -> dict[str, Any]:
    """Field-level comparison. Returns dict with pass/fail and messages."""
    if fields is None:
        fields = ["nobs", "df_model", "df_a", "df_resid", "ll", "deviance", "pseudo_r2", "chi2", "n_clust"]

    diffs: dict[str, Any] = {"passed": True, "messages": [], "field_results": {}}

    def _record(name: str, passed: bool, msg: str) -> None:
        diffs["field_results"][name] = {"passed": passed, "message": msg}
        if not passed:
            diffs["passed"] = False
        diffs["messages"].append(msg)

    for field in fields:
        py_val = None
        if field == "nobs":
            py_val = float(py_result.sample.nobs)
        elif field == "df_model":
            py_val = py_result.fit.df_model
        elif field == "df_a":
            py_val = py_result.fit.df_a
        elif field == "df_resid":
            py_val = py_result.fit.df_resid
        elif field == "ll":
            py_val = py_result.fit.ll
        elif field == "deviance":
            py_val = py_result.fit.deviance
        elif field == "pseudo_r2":
            py_val = py_result.fit.pseudo_r2
        elif field == "chi2":
            # Python stores no chi2 in FitInfo currently; skip if missing
            py_val = getattr(py_result.fit, "chi2", None)
        elif field == "n_clust":
            py_val = py_result.diagnostics.cluster_count
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
            passed, msg = tolerance_close(
                py_val, st_val, rtol=coefficient_rtol, name=f"{name}.{metric}"
            )
            _record(f"{name}.{metric}", passed, msg)

    # VCE matrix
    if compare_vce and "vce_matrix" in st_result and st_result["vce_matrix"] is not None:
        vce_mat = st_result["vce_matrix"]
        st_names = st_result["vce_names"]
        py_names = list(py_result.variance.row_names)
        py_mat = np.array(py_result.variance.values)
        name_to_idx_py = {n: i for i, n in enumerate(py_names)}
        name_to_idx_st = {n: i for i, n in enumerate(st_names)}
        for name_i in py_names:
            for name_j in py_names:
                i_py = name_to_idx_py[name_i]
                j_py = name_to_idx_py[name_j]
                i_st = name_to_idx_st.get(name_i)
                j_st = name_to_idx_st.get(name_j)
                if i_st is None or j_st is None:
                    continue
                py_val = py_mat[i_py, j_py]
                st_val = vce_mat[i_st, j_st]
                passed, msg = tolerance_close(
                    py_val, st_val, rtol=vce_rtol, name=f"VCE[{name_i},{name_j}]"
                )
                _record(f"vce.{name_i}.{name_j}", passed, msg)

    # Predict summaries
    if predict_types:
        for ptype in predict_types:
            py_vals = predict_summary_python(py_result, ptype)
            st_vals = st_result.get("predict", {}).get(ptype, {})
            for stat in ["mean", "sd", "min", "max"]:
                py_val = py_vals.get(stat)
                st_val = st_vals.get(stat)
                if py_val is None and st_val is None:
                    continue
                passed, msg = tolerance_close(
                    py_val,
                    st_val,
                    rtol=predict_rtol,
                    atol=predict_atol,
                    name=f"predict.{ptype}.{stat}",
                )
                _record(f"predict.{ptype}.{stat}", passed, msg)

    return diffs


def predict_summary_python(py_result: ResultSchema, ptype: str) -> dict[str, Optional[float]]:
    """Compute summary statistics for Python predict output."""
    model = getattr(py_result, "_model", None)
    if model is None or not hasattr(model, "predict"):
        return {}
    try:
        arr = model.predict(type=ptype)
    except Exception:
        return {}
    if arr is None or len(arr) == 0:
        return {}
    return {
        "mean": float(np.mean(arr)),
        "sd": float(np.std(arr, ddof=1)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
    }


def save_evidence(prefix: str, py_result: ResultSchema, st_result: dict[str, Any], diffs: dict[str, Any]) -> Path:
    """Persist comparison evidence as JSON in the module evidence directory."""
    evidence_dir = M06_EVIDENCE / "synthetic" if prefix.startswith(("S", "P")) else M06_EVIDENCE / "real-data"
    evidence_dir = evidence_dir / prefix
    evidence_dir.mkdir(parents=True, exist_ok=True)

    py_dict = py_result.to_dict() if hasattr(py_result, "to_dict") else {}
    # Convert numpy arrays to lists for JSON
    st_result_copy = {k: v for k, v in st_result.items() if not k.startswith("_raw_log")}
    if "vce_matrix" in st_result_copy and isinstance(st_result_copy["vce_matrix"], np.ndarray):
        st_result_copy["vce_matrix"] = st_result_copy["vce_matrix"].tolist()

    payload = {
        "prefix": prefix,
        "python": py_dict,
        "stata": st_result_copy,
        "diffs": diffs,
    }
    path = evidence_dir / f"{prefix}_evidence.json"
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return path


def data_hash(df: pd.DataFrame) -> str:
    """Return a quick hash of the data for reproducibility records."""
    return hashlib.sha256(pd.util.hash_pandas_object(df, index=True).values.tobytes()).hexdigest()[:16]
