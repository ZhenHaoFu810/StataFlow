"""Shared utilities for M01 Linear modular revalidation v1.3.

Do not import from existing golden tests; all helpers are rewritten
independently for this audit round.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd

from stataflow import OLS
from stataflow.compat.stata import regress
from stataflow.stata_runner import StataRunner

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
STATA_CASES = PROJECT_ROOT / "stata" / "cases" / "audit_v1_3_m01"
STATA_OUTPUT = PROJECT_ROOT / "stata" / "output" / "audit_v1_3_m01"
EVIDENCE = PROJECT_ROOT / "docs" / "audit" / "modular-revalidation-v1.3" / "M01-linear" / "evidence"

STATA_CASES.mkdir(parents=True, exist_ok=True)
STATA_OUTPUT.mkdir(parents=True, exist_ok=True)


def file_hash(path: Path) -> str:
    """Return SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def run_stata_do(do_content: str, do_name: str) -> dict[str, Any]:
    """Write and execute a Stata .do file, return parsed log dict."""
    do_path = STATA_CASES / f"{do_name}.do"
    do_path.write_text(do_content, encoding="utf-8")

    runner = StataRunner()
    result = runner.run_do_file(do_content, output_dir=str(STATA_OUTPUT))

    if result.exit_code != 0:
        raise RuntimeError(
            f"Stata failed for {do_name}: exit={result.exit_code}, "
            f"err={result.error_message}"
        )
    if not result.output_content:
        raise RuntimeError(f"Stata produced no output for {do_name}")

    parsed = parse_stata_log(result.output_content)
    parsed["_do_file"] = str(do_path)
    parsed["_log_hash"] = file_hash(do_path)
    parsed["_exit_code"] = result.exit_code
    return parsed


def parse_stata_log(log_content: str) -> dict[str, Any]:
    """Parse Stata log for E_ values, COEF lines, and VCE rows."""
    result: dict[str, Any] = {}

    # Scalar e() values
    e_patterns = {
        "nobs": r"E_N=([\d]+)",
        "df_model": r"E_DF_M=([\d]+)",
        "df_resid": r"E_DF_R=([\d]+)",
        "r2": r"E_R2=([\d.eE+-]+)",
        "r2_adj": r"E_R2_A=([\d.eE+-]+)",
        "rmse": r"E_RMSE=([\d.eE+-]+)",
        "f_stat": r"E_F=([\d.eE+-]+)",
        "f_pvalue": r"E_F_P=([\d.eE+-]+)",
        "rss": r"E_RSS=([\d.eE+-]+)",
        "mss": r"E_MSS=([\d.eE+-]+)",
        "n_clust": r"E_N_CLUST=([\d]+)",
    }
    for key, pattern in e_patterns.items():
        match = re.search(pattern, log_content)
        if match:
            val_str = match.group(1).strip()
            if val_str in (".", "-."):
                continue
            if val_str.startswith("."):
                val_str = "0" + val_str
            try:
                result[key] = float(val_str)
            except ValueError:
                pass

    # Derive TSS from MSS + RSS if available
    if "mss" in result and "rss" in result:
        result["tss"] = result["mss"] + result["rss"]

    # Coefficients from COEF lines: "COEF <name> <beta> <se>"
    coefficients = []
    coef_pattern = re.compile(r"^COEF\s+(.+?)\s+(-?[\d.eE+-]+)\s+(-?[\d.eE+-]+)$")
    for line in log_content.splitlines():
        m = coef_pattern.match(line.strip())
        if m:
            coefficients.append({
                "name": m.group(1).strip(),
                "beta": float(m.group(2)),
                "std_err": float(m.group(3)),
            })
    if coefficients:
        result["coefficients"] = coefficients

    # Full VCE from VCE lines: "VCE <i> <j> <value>"
    vce_rows: list[tuple[int, int, float]] = []
    vce_pattern = re.compile(r"^VCE\s+(\d+)\s+(\d+)\s+(-?[\d.eE+-]+)$")
    for line in log_content.splitlines():
        m = vce_pattern.match(line.strip())
        if m:
            vce_rows.append((int(m.group(1)), int(m.group(2)), float(m.group(3))))
    if vce_rows:
        n = max(i for i, j, v in vce_rows) + 1
        vce = np.zeros((n, n))
        for i, j, v in vce_rows:
            vce[i, j] = v
            vce[j, i] = v
        result["vce"] = vce
        result["vce_rows"] = n

    return result


def python_result_to_dict(result) -> dict[str, Any]:
    """Convert a Python ResultSchema to a comparable dict."""
    coefs = [
        {
            "name": c.name,
            "beta": c.beta,
            "std_err": c.std_err,
            "t_stat": c.t_stat,
            "p_value": c.p_value,
            "ci_low": c.ci_low,
            "ci_high": c.ci_high,
            "is_omitted": c.is_omitted,
        }
        for c in result.coefficients
    ]
    vce = np.array(result.variance.values)
    out = {
        "nobs": result.sample.nobs,
        "n_input_rows": result.sample.n_input_rows,
        "df_model": result.fit.df_model,
        "df_resid": result.fit.df_resid,
        "r2": result.fit.r2,
        "r2_adj": result.fit.r2_adj,
        "rmse": result.fit.rmse,
        "f_stat": result.fit.f_stat,
        "f_pvalue": result.fit.f_pvalue,
        "rss": result.fit.rss,
        "tss": result.fit.tss,
        "mss": result.fit.mss,
        "cluster_count": result.diagnostics.cluster_count,
        "coefficients": coefs,
        "vce": vce,
        "vce_row_names": list(result.variance.row_names),
        "sample_mask": list(result.sample.sample_mask),
        "warnings": list(result.diagnostics.warnings),
    }
    # Attach dropped-variable info if the underlying model is available.
    model = getattr(result, "_model", None)
    if model is not None and hasattr(model, "_collinear_dropped"):
        out["dropped_vars"] = list(model._collinear_dropped)
    return out


def compare_scalars(py_val, st_val, name: str, rtol: float = 1e-6, atol: float = 1e-8):
    """Return (passed, message) for scalar comparison."""
    if py_val is None and st_val is None:
        return True, f"{name}: both None -> PASS"
    if py_val is None or st_val is None:
        return False, f"{name}: Python={py_val}, Stata={st_val} -> FAIL (one missing)"
    if not np.isfinite(py_val) or not np.isfinite(st_val):
        return py_val == st_val, f"{name}: Python={py_val}, Stata={st_val} -> {'PASS' if py_val == st_val else 'FAIL'}"
    diff = abs(py_val - st_val)
    rel_diff = diff / (abs(st_val) + 1e-15)
    passed = diff < atol or rel_diff < rtol
    return passed, (
        f"{name}: Python={py_val:.15g}, Stata={st_val:.15g}, "
        f"abs_diff={diff:.2e}, rel_diff={rel_diff:.2e} -> {'PASS' if passed else 'FAIL'}"
    )


def _is_stata_omitted(name: str) -> bool:
    """Return True if Stata coefficient name indicates omitted/base variable."""
    return "b." in name or "o." in name or "co." in name


def _normalize_stata_name(name: str) -> str:
    """Remove Stata omitted/base markers for comparison.

    Examples: '2b.g' -> '2.g', 'o.x1' -> 'x1', '2b.g#co.x' -> '2.g#c.x'
    """
    import re
    # Remove b. / o. / co. markers (Stata-specific)
    name = re.sub(r"\b([bco])\.", "", name)
    return name


def _normalize_python_name(name: str) -> str:
    """Normalize Python-generated factor column names toward Stata naming.

    Examples: '3.g#c.x' -> '3.g#x'
    """
    import re
    # Remove c. prefix after # (continuous marker)
    name = re.sub(r"#c\.", "#", name)
    return name


def compare_coefficients(py_coefs: list[dict], st_coefs: list[dict], rtol: float = 1e-6, atol: float = 1e-8):
    """Compare coefficient lists and return list of (passed, message).

    Stata omitted/base coefficients are compared against Python dropped variables
    or skipped if Python also dropped them. Non-omitted coefficients are compared
    by normalized name.
    """
    results = []
    py_active = [c for c in py_coefs if not c.get("is_omitted", False)]
    st_non_omitted = [c for c in st_coefs if not _is_stata_omitted(c["name"])]
    st_omitted = [c for c in st_coefs if _is_stata_omitted(c["name"])]

    # Compare non-omitted Stata coefficients to Python coefficients by normalized name
    py_by_name = {_normalize_python_name(c["name"]): c for c in py_active}
    for sc in st_non_omitted:
        norm_name = _normalize_python_name(_normalize_stata_name(sc["name"]))
        if norm_name not in py_by_name:
            results.append((False, f"Stata non-omitted coef '{sc['name']}' (norm '{norm_name}') not found in Python"))
            continue
        pc = py_by_name[norm_name]
        for field in ["beta", "std_err"]:
            passed, msg = compare_scalars(pc[field], sc[field], f"{field}[{sc['name']}]", rtol=rtol, atol=atol)
            results.append((passed, msg))

    # Check that Python doesn't have extra unexpected non-omitted coefficients
    st_non_omitted_norms = {_normalize_python_name(_normalize_stata_name(c["name"])) for c in st_non_omitted}
    for pc in py_active:
        py_norm = _normalize_python_name(pc["name"])
        if py_norm not in st_non_omitted_norms:
            # Python has a coefficient that Stata either omitted or doesn't have
            results.append((False, f"Python coef '{pc['name']}' (norm '{py_norm}') not in Stata non-omitted set {st_non_omitted_norms}"))

    # Report omitted variables as informational (not a failure per se)
    if st_omitted:
        results.append((True, f"Stata omitted coefficients: {[c['name'] for c in st_omitted]}"))

    return results


def compare_vce(py_vce: np.ndarray, st_vce: np.ndarray, py_names: list[str], st_names: list[str], rtol: float = 1e-6, atol: float = 1e-8):
    """Compare VCE matrices, handling Stata omitted/base rows/cols.

    Only non-omitted Stata rows/cols are compared. Omitted rows/cols in Stata
    are expected to be zero/empty in Python.
    """
    if py_vce.size == 0 or st_vce.size == 0:
        return [(False, f"VCE empty: Python shape={py_vce.shape}, Stata shape={st_vce.shape}")]

    st_keep = [i for i, n in enumerate(st_names) if not _is_stata_omitted(n)]
    st_names_kept = [_normalize_python_name(_normalize_stata_name(st_names[i])) for i in st_keep]
    py_keep = [i for i, n in enumerate(py_names) if not _is_stata_omitted(n)]
    py_names_norm = [_normalize_python_name(py_names[i]) for i in py_keep]

    if set(py_names_norm) != set(st_names_kept):
        return [(False, f"VCE non-omitted names differ: Python={py_names_norm}, Stata(non-omitted)={st_names_kept}")]

    # Reorder Python VCE to match Stata kept order
    py_order = [py_keep[py_names_norm.index(n)] for n in st_names_kept]
    py_vce_kept = py_vce[np.ix_(py_order, py_order)]
    st_vce_kept = st_vce[np.ix_(st_keep, st_keep)]

    diff = np.abs(py_vce_kept - st_vce_kept)
    denom = np.abs(st_vce_kept) + 1e-15
    rel_diff = diff / denom
    max_diff = float(np.max(diff))
    max_rel = float(np.max(rel_diff))
    passed = np.all(diff < atol) or np.all(rel_diff < rtol)
    return [(passed, f"VCE(non-omitted) max_abs_diff={max_diff:.2e}, max_rel_diff={max_rel:.2e} -> {'PASS' if passed else 'FAIL'}")]


def save_evidence(test_id: str, py_dict: dict, st_dict: dict, comparisons: list[tuple[bool, str]], data: Optional[pd.DataFrame] = None):
    """Save structured evidence to the module evidence directory."""
    ev_dir = EVIDENCE / "synthetic" if test_id.startswith("S") else EVIDENCE / "real-data" if test_id.startswith("R") else EVIDENCE / "minimal-reproductions"
    ev_dir.mkdir(parents=True, exist_ok=True)

    # Save comparison report
    report_path = ev_dir / f"{test_id}_report.json"
    report = {
        "test_id": test_id,
        "python": {k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in py_dict.items()},
        "stata": {k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in st_dict.items()},
        "comparisons": [{"passed": p, "message": m} for p, m in comparisons],
    }
    report_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    # Save data if provided
    if data is not None:
        data_path = ev_dir / f"{test_id}_data.csv"
        data.to_csv(data_path, index=False)

    return report_path
