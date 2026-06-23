"""Shared utilities for the M09 postestimation modular audit v1.3.

Provides:
- Project path resolution and evidence directories
- Stata 17 batch execution via StataRunner
- Log cleaning and scalar parsing
- Field-level comparison helpers
- Evidence persistence
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
M09_EVIDENCE = (
    PROJECT_ROOT
    / "docs"
    / "audit"
    / "modular-revalidation-v1.3"
    / "M09-postestimation"
    / "evidence"
)
STATA_CASES = PROJECT_ROOT / "stata" / "cases" / "audit_v1_3_m09"
STATA_OUTPUT = PROJECT_ROOT / "stata" / "output" / "audit_v1_3_m09"

for _p in [M09_EVIDENCE, STATA_CASES, STATA_OUTPUT]:
    _p.mkdir(parents=True, exist_ok=True)


def _clean_stata_log(raw_log: str) -> str:
    """Remove Stata banner so the output is printable and parseable."""
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
    """Stata displays numbers <1 as '.123'; add leading zero for float parsing."""
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
    """Return a reproducible hash of a DataFrame."""
    return hashlib.sha256(
        pd.util.hash_pandas_object(df, index=True).values.tobytes()
    ).hexdigest()[:16]


def _build_options(**opts: Any) -> str:
    """Build a Stata options string from keyword arguments."""
    parts = []
    for key, val in opts.items():
        if val is None or val is False:
            continue
        if val is True:
            parts.append(key)
        elif isinstance(val, (list, tuple)):
            parts.append(f"{key}({' '.join(str(v) for v in val)})")
        else:
            parts.append(f"{key}({val})")
    return " ".join(parts)


def run_stata_do(
    df: pd.DataFrame,
    prefix: str,
    do_content: str,
    timeout: int = 300,
) -> dict[str, Any]:
    """Save df to DTA, run Stata, parse scalar display lines, and return results.

    Parameters
    ----------
    df : pd.DataFrame
        Data to write to the Stata .dta file.
    prefix : str
        Base name for the .dta, .do, and .log files.
    do_content : str
        Full Stata do-file content. A literal ``{dta}`` will be replaced by the
        path to the generated .dta file.
    timeout : int
        Stata execution timeout in seconds.

    Returns
    -------
    dict with keys ``exit_code``, ``log_path``, ``dta_path``, ``cleaned_log``,
    and ``scalars`` (dict of parsed ``KEY=value`` display lines).
    """
    dta_path = STATA_CASES / f"{prefix}.dta"
    df.to_stata(str(dta_path), write_index=False)

    dta_posix = str(dta_path).replace("\\", "/")
    do_content = do_content.replace("{dta}", dta_posix)

    runner = StataRunner()
    result = runner.run_do_file(do_content, output_dir=str(STATA_OUTPUT), timeout=timeout)

    log_path = STATA_OUTPUT / f"{prefix}.log"
    cleaned_log = _clean_stata_log(result.output_content or result.error_message or "")
    log_path.write_text(cleaned_log, encoding="utf-8", errors="replace")

    if result.exit_code != 0:
        raise RuntimeError(
            f"Stata failed for {prefix}: {result.error_message}\nLog: {log_path}"
        )

    scalars = {}
    for line in cleaned_log.splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("."):
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip()
            if key and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
                fval = _to_float(val)
                if fval is not None:
                    scalars[key] = fval

    return {
        "exit_code": result.exit_code,
        "log_path": str(log_path),
        "dta_path": str(dta_path),
        "cleaned_log": cleaned_log,
        "scalars": scalars,
    }


def parse_stata_scalars(log_content: str, patterns: dict[str, str]) -> dict[str, Optional[float]]:
    """Parse selected scalar display lines from a Stata log.

    Parameters
    ----------
    log_content : str
        Cleaned Stata log.
    patterns : dict
        Mapping from output key to regex pattern with one capture group.

    Returns
    -------
    dict of parsed floats (None if missing).
    """
    out: dict[str, Optional[float]] = {}
    for key, pat in patterns.items():
        m = re.search(pat, log_content, re.MULTILINE)
        out[key] = _to_float(m.group(1)) if m else None
    return out


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


def compare_series_stats(
    py_arr: np.ndarray,
    st_mean: Optional[float],
    st_sd: Optional[float],
    name: str = "series",
    rtol: float = 1e-5,
    atol: float = 1e-6,
) -> dict[str, Any]:
    """Compare summary statistics of a Python array to Stata summary scalars."""
    py_arr = np.asarray(py_arr, dtype=float)
    py_mean = float(np.mean(py_arr))
    py_sd = float(np.std(py_arr, ddof=1))
    diffs: dict[str, Any] = {"passed": True, "messages": [], "field_results": {}}

    def _record(n: str, passed: bool, msg: str) -> None:
        diffs["field_results"][n] = {"passed": passed, "message": msg}
        if not passed:
            diffs["passed"] = False
        diffs["messages"].append(msg)

    passed, msg = tolerance_close(py_mean, st_mean, rtol, atol, name=f"{name}.mean")
    _record(f"{name}.mean", passed, msg)
    passed, msg = tolerance_close(py_sd, st_sd, rtol, atol, name=f"{name}.sd")
    _record(f"{name}.sd", passed, msg)
    return diffs


def save_evidence(prefix: str, payload: dict[str, Any]) -> Path:
    """Persist comparison evidence as JSON under the module evidence tree."""
    if prefix.startswith("S"):
        evidence_dir = M09_EVIDENCE / "synthetic" / prefix
    elif prefix.startswith("P"):
        evidence_dir = M09_EVIDENCE / "property" / prefix
    else:
        evidence_dir = M09_EVIDENCE / "real-data" / prefix
    evidence_dir.mkdir(parents=True, exist_ok=True)

    path = evidence_dir / f"{prefix}_evidence.json"
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return path


def linear_predict_do(
    model_cmd: str,
    predict_types: list[str],
    prefix: str,
    n_list: int = 5,
) -> str:
    """Build a Stata .do script that runs a model and several predict types.

    Outputs scalars ``P_<TYPE>_MEAN``, ``P_<TYPE>_SD``, and ``P_<TYPE>_<i>``
    for the first ``n_list`` observations.
    """
    lines = [
        "clear all",
        "set more off",
        'use "{dta}", clear',
        model_cmd,
    ]
    for ptype in predict_types:
        var = f"py_{ptype}"
        safe = ptype.replace("_", "")
        lines.append(f"predict {var}, {ptype}")
        lines.append(f"quietly summarize {var}")
        lines.append(f'display "P_{safe}_MEAN=" r(mean)')
        lines.append(f'display "P_{safe}_SD=" r(sd)')
        lines.append(f'display "P_{safe}_SUM=" r(sum)')
        lines.append(f'display "P_{safe}_N=" r(N)')
        for i in range(1, n_list + 1):
            lines.append(f'display "P_{safe}_{i}=" {var}[{i}]')
    lines.append(f'display "M09_OK_{prefix}"')
    return "\n".join(lines)


def margins_do(
    model_cmd: str,
    variables: list[str],
    atmeans: bool = False,
) -> str:
    """Build a Stata .do script that reports margins dydx for each variable.

    Outputs scalars ``M_<var>`` and ``SE_<var>`` for the marginal effect and
    its standard error.
    """
    lines = [
        "clear all",
        "set more off",
        'use "{dta}", clear',
        model_cmd,
    ]
    for var in variables:
        opt = "dydx(%s)" % var
        if atmeans:
            opt += " atmeans"
        lines.append(f"quietly margins, {opt}")
        lines.append(f'display "M_{var}=" r(b)[1,1]')
        lines.append(f'display "SE_{var}=" sqrt(r(V)[1,1])')
    lines.append(f'display "M09_MARGINS_OK"')
    return "\n".join(lines)


def estat_summarize_do(
    model_cmd: str,
    variables: list[str],
) -> str:
    """Build a Stata .do script that reports estimation-sample summaries.

    Outputs scalars ``SUM_<var>_{N,MEAN,SD,MIN,MAX}``.
    """
    lines = [
        "clear all",
        "set more off",
        'use "{dta}", clear',
        model_cmd,
    ]
    for var in variables:
        lines.append(f"quietly summarize {var} if e(sample)")
        lines.append(f'display "SUM_{var}_N=" r(N)')
        lines.append(f'display "SUM_{var}_MEAN=" r(mean)')
        lines.append(f'display "SUM_{var}_SD=" r(sd)')
        lines.append(f'display "SUM_{var}_MIN=" r(min)')
        lines.append(f'display "SUM_{var}_MAX=" r(max)')
    lines.append(f'display "M09_ESTAT_OK"')
    return "\n".join(lines)


def estat_ic_do(model_cmd: str) -> str:
    """Build a Stata .do script that reports information criteria.

    Outputs scalars ``IC_N``, ``IC_LL``, ``IC_K``, ``IC_AIC``, ``IC_BIC``.
    """
    lines = [
        "clear all",
        "set more off",
        'use "{dta}", clear',
        model_cmd,
        "estat ic",
        "matrix s = r(S)",
        'display "IC_N=" s[1,1]',
        'display "IC_LL=" s[1,3]',
        'display "IC_K=" s[1,4]',
        'display "IC_AIC=" s[1,5]',
        'display "IC_BIC=" s[1,6]',
        'display "M09_IC_OK"',
    ]
    return "\n".join(lines)


def py_result_to_dict(py_result: ResultSchema | Any) -> dict[str, Any]:
    """Serialize a ResultSchema (or plain dict) for evidence JSON."""
    if isinstance(py_result, ResultSchema):
        return py_result.to_dict()
    if hasattr(py_result, "__dict__"):
        return vars(py_result)
    return py_result if isinstance(py_result, dict) else {"repr": str(py_result)}
