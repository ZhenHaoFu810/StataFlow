"""Shared helpers for out-of-sample validation runners.

These runners are independent from the development-time golden test suite.
They load new public datasets, execute Stata 17 and Python, compare field-level
results, and write structured evidence artifacts.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from stataflow.stata_runner import StataRunner

STATA_OUTPUT = PROJECT_ROOT / "stata" / "output"
STATA_CASES = PROJECT_ROOT / "stata" / "cases"
RESULTS_DIR = PROJECT_ROOT / "research" / "results" / "validation" / "oos"

STATA_OUTPUT.mkdir(parents=True, exist_ok=True)
STATA_CASES.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class OOSCase:
    case_id: str
    family: str
    command: str
    dataset_key: str
    dataset_path: str
    stata_command: str
    python_callable: str
    python_kwargs: dict[str, Any]
    description: str
    status: str = "pending"
    notes: str = ""
    fields: dict[str, Any] = field(default_factory=dict)
    coefficients: list[dict[str, Any]] = field(default_factory=list)


def run_stata_and_parse(do_content: str, output_dir: str | Path = None) -> dict:
    """Run a Stata do-file and parse standard e() + COEF lines."""
    runner = StataRunner()
    if output_dir is None:
        output_dir = str(STATA_OUTPUT)
    result = runner.run_do_file(do_content, output_dir=str(output_dir))
    if result.exit_code != 0:
        raise RuntimeError(f"Stata failed: {result.error_message}")
    if not result.output_content:
        raise RuntimeError("Stata produced no output")
    return _parse_stata_log(result.output_content)


def _parse_stata_log(log_content: str) -> dict:
    """Parse Stata log with e() values and COEF lines."""
    parsed: dict[str, Any] = {}

    e_patterns = {
        "nobs": r"E_N=([\d]+)",
        "n_g": r"E_N_g=([\d]+)",
        "df_model": r"E_DF_M=([\d]+)",
        "df_resid": r"E_DF_R=([\d]+)",
        "df_a": r"E_DF_A=([\d]+)",
        "r2": r"E_R2=([\d.]+)",
        "r2_w": r"E_R2_W=([\d.]+)",
        "r2_adj": r"E_R2_A=([\d.]+)",
        "rmse": r"E_RMSE=([\d.]+)",
        "f_stat": r"E_F=([\d.]+)",
        "ll": r"E_LL=([-\d.]+)",
        "chi2": r"E_CHI2=([\d.]+)",
        "n_clust": r"E_N_CLUST=([\d]+)",
    }

    for key, pattern in e_patterns.items():
        match = re.search(pattern, log_content)
        if match:
            val_str = match.group(1)
            if val_str in (".", "-."):
                continue
            if val_str.startswith("."):
                val_str = "0" + val_str
            parsed[key] = float(val_str)

    # Coefficients from COEF lines (preferred for factor syntax)
    coef_pattern = r"^COEF\s+(.+?)\s+(-?[\d.]+(?:e[+-]?\d+)?)\s+(-?[\d.]+(?:e[+-]?\d+)?)$"
    coefficients = []
    for line in log_content.splitlines():
        m = re.match(coef_pattern, line.strip())
        if m:
            coefficients.append({
                "name": m.group(1).strip(),
                "beta": float(m.group(2)),
                "std_err": float(m.group(3)),
            })

    if coefficients:
        parsed["coefficients"] = coefficients
    else:
        # Fallback to B_ / SE_ lines
        b_matches = {k.lower(): v for k, v in re.findall(r"B_(\w+)=(-?[\d.]+)", log_content)}
        se_matches = {k.lower(): v for k, v in re.findall(r"SE_(\w+)=(-?[\d.]+)", log_content)}
        coefficients = []
        for name in set(b_matches.keys()) & set(se_matches.keys()):
            coefficients.append({
                "name": name,
                "beta": float(b_matches[name]),
                "std_err": float(se_matches[name]),
            })
        if coefficients:
            parsed["coefficients"] = coefficients

    return parsed


def tolerance_close(a: float | None, b: float | None, rtol: float = 1e-6, atol: float = 1e-8, name: str = "value") -> tuple[bool, str]:
    if a is None or b is None:
        return a == b, f"{name}: Python={a}, Stata={b}"
    diff = abs(a - b)
    rel_diff = diff / (abs(b) + 1e-15)
    passed = diff < atol or rel_diff < rtol
    msg = f"{name}: Python={a:.15f}, Stata={b:.15f}, abs_diff={diff:.2e}, rel_diff={rel_diff:.2e}, {'PASS' if passed else 'FAIL'}"
    return passed, msg


def compare_case(
    py_result: Any,
    st_result: dict,
    case: OOSCase,
    field_map: dict[str, tuple[str, str, float, float]],
    skip_coefs: tuple[str, ...] = (),
    coef_rtol: float = 1e-6,
    coef_atol: float = 1e-8,
) -> dict:
    """Compare Python and Stata results for a case.

    field_map: dict of field_name -> (python_accessor, stata_key, rtol, atol)
    """
    report = {
        "case_id": case.case_id,
        "command": case.command,
        "dataset_key": case.dataset_key,
        "status": "pending",
        "field_checks": [],
        "coefficient_checks": [],
        "notes": case.notes,
    }

    all_passed = True

    for field_name, (py_accessor, st_key, rtol, atol) in field_map.items():
        py_val = _resolve_accessor(py_result, py_accessor)
        st_val = st_result.get(st_key)
        passed, msg = tolerance_close(py_val, st_val, rtol=rtol, atol=atol, name=field_name)
        report["field_checks"].append({
            "field": field_name,
            "python": py_val,
            "stata": st_val,
            "passed": passed,
            "message": msg,
        })
        if not passed:
            all_passed = False

    # Compare coefficients
    py_coefs = {c.name: c for c in py_result.coefficients}
    st_coefs = {c["name"]: c for c in st_result.get("coefficients", [])}

    for name in py_coefs:
        if name in skip_coefs:
            continue
        if name not in st_coefs:
            report["coefficient_checks"].append({
                "name": name,
                "passed": False,
                "message": f"Coefficient '{name}' in Python but not in Stata",
            })
            all_passed = False
            continue
        py_beta = py_coefs[name].beta
        st_beta = st_coefs[name]["beta"]
        passed_beta, msg_beta = tolerance_close(py_beta, st_beta, rtol=coef_rtol, atol=coef_atol, name=f"beta[{name}]")

        py_se = py_coefs[name].std_err
        st_se = st_coefs[name]["std_err"]
        passed_se, msg_se = tolerance_close(py_se, st_se, rtol=coef_rtol, atol=coef_atol, name=f"se[{name}]")

        report["coefficient_checks"].append({
            "name": name,
            "beta_passed": passed_beta,
            "beta_message": msg_beta,
            "se_passed": passed_se,
            "se_message": msg_se,
        })
        if not (passed_beta and passed_se):
            all_passed = False

    for name in st_coefs:
        if name in skip_coefs:
            continue
        if name not in py_coefs:
            report["coefficient_checks"].append({
                "name": name,
                "passed": False,
                "message": f"Coefficient '{name}' in Stata but not in Python",
            })
            all_passed = False

    report["status"] = "passed" if all_passed else "blocked"
    return report


def _resolve_accessor(obj: Any, accessor: str) -> Any:
    """Resolve a dotted accessor string like 'sample.nobs' or 'fit.df_model'."""
    parts = accessor.split(".")
    val = obj
    for part in parts:
        val = getattr(val, part, None)
        if val is None:
            return None
    return val


def _convert_for_json(obj: Any) -> Any:
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, dict):
        return {k: _convert_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_convert_for_json(v) for v in obj]
    return obj


def write_case_report(report: dict, output_dir: Path = None) -> Path:
    if output_dir is None:
        output_dir = RESULTS_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{report['case_id']}.json"
    path.write_text(json.dumps(_convert_for_json(report), indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def write_family_summary(family: str, reports: list[dict], output_dir: Path = None) -> Path:
    if output_dir is None:
        output_dir = RESULTS_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    passed = sum(1 for r in reports if r["status"] == "passed")
    blocked = sum(1 for r in reports if r["status"] == "blocked")

    summary = {
        "family": family,
        "cases": len(reports),
        "passed": passed,
        "blocked": blocked,
        "reports": reports,
    }

    path = output_dir / f"{family}_summary.json"
    path.write_text(json.dumps(_convert_for_json(summary), indent=2, ensure_ascii=False), encoding="utf-8")

    # Markdown render
    md_lines = [
        f"# OOS Validation Summary: {family}",
        "",
        f"- Cases: {len(reports)}",
        f"- Passed: {passed}",
        f"- Blocked: {blocked}",
        "",
        "## Case Results",
        "",
        "| case_id | command | dataset | status |",
        "| --- | --- | --- | --- |",
    ]
    for r in reports:
        md_lines.append(f"| {r['case_id']} | `{r['command']}` | {r['dataset_key']} | {r['status']} |")

    md_lines.extend(["", "## Detail"])
    for r in reports:
        md_lines.extend([
            "",
            f"### {r['case_id']}",
            "",
            f"- Command: `{r['command']}`",
            f"- Dataset: {r['dataset_key']}",
            f"- Status: **{r['status']}**",
        ])
        if r.get("notes"):
            md_lines.append(f"- Notes: {r['notes']}")
        failed_fields = [c for c in r.get("field_checks", []) if not c["passed"]]
        failed_coefs = [c for c in r.get("coefficient_checks", []) if not c.get("passed", True)]
        if failed_fields:
            md_lines.append("- Failed fields:")
            for f in failed_fields:
                md_lines.append(f"  - {f['message']}")
        if failed_coefs:
            md_lines.append("- Failed coefficients:")
            for c in failed_coefs:
                md_lines.append(f"  - {c.get('message', c.get('name'))}")

    md_path = output_dir / f"{family}_summary.md"
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    return path
