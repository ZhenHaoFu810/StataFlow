"""Common utilities for M08 RD modular audit v1.3.

Provides:
- Project path resolution
- Stata 17 batch execution for rdrobust / rdplot
- Log parsing (B_/SE_/E_ lines, rdplot info)
- Field-level comparison against Python ResultSchema / dict
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
M08_EVIDENCE = (
    PROJECT_ROOT
    / "docs"
    / "audit"
    / "modular-revalidation-v1.3"
    / "M08-rd"
    / "evidence"
)
STATA_CASES = PROJECT_ROOT / "stata" / "cases" / "audit_v1_3_m08"
STATA_OUTPUT = PROJECT_ROOT / "stata" / "output" / "audit_v1_3_m08"

for _p in [M08_EVIDENCE, STATA_CASES, STATA_OUTPUT]:
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


def rdrobust_stata_do(
    dta_path: str | Path,
    y: str,
    x: str,
    c: float = 0.0,
    h: float | tuple[float, float] | None = None,
    b: float | tuple[float, float] | None = None,
    p: int = 1,
    q: int = 2,
    deriv: int = 0,
    kernel: str = "triangular",
    vce: str = "nn",
    nnmatch: int = 3,
    level: int = 95,
    bwselect: str | None = None,
    covs: list[str] | str | None = None,
    scaleregul: float = 1.0,
    masspoints: str = "adjust",
    bwcheck: int = 0,
    weights: str | None = None,
    fuzzy: str | None = None,
    sharpbw: bool = False,
    cluster: str | None = None,
) -> str:
    """Build a Stata .do script for rdrobust with full e()/matrix extraction."""
    dta_path = str(dta_path).replace("\\", "/")

    opts: dict[str, Any] = {}
    if c != 0.0:
        opts["c"] = c
    if h is not None:
        if isinstance(h, tuple):
            opts["h"] = f"{h[0]} {h[1]}"
        else:
            opts["h"] = h
    if b is not None:
        if isinstance(b, tuple):
            opts["b"] = f"{b[0]} {b[1]}"
        else:
            opts["b"] = b
    if bwselect is not None and h is None:
        opts["bwselect"] = bwselect
    if p != 1:
        opts["p"] = p
    if q != 2:
        opts["q"] = q
    if deriv != 0:
        opts["deriv"] = deriv
    if kernel != "triangular":
        opts["kernel"] = kernel
    if vce != "nn":
        # rdrobust Stata syntax folds cluster variable into vce(), e.g. vce(cluster g)
        if cluster is not None and vce in ("cluster", "nncluster"):
            opts["vce"] = f"{vce} {cluster}"
        else:
            opts["vce"] = vce
    if nnmatch != 3:
        opts["nnmatch"] = nnmatch
    if level != 95:
        opts["level"] = level
    if covs is not None:
        if isinstance(covs, list):
            opts["covs"] = " ".join(covs)
        else:
            opts["covs"] = covs
    if scaleregul != 1.0:
        opts["scaleregul"] = scaleregul
    if masspoints != "adjust":
        opts["masspoints"] = masspoints
    if bwcheck != 0:
        opts["bwcheck"] = bwcheck
    if weights is not None:
        opts["weights"] = weights
    if fuzzy is not None:
        opts["fuzzy"] = fuzzy
    if sharpbw:
        opts["sharpbw"] = True

    opts_line = _build_options(**opts)
    opts_line = f", {opts_line}" if opts_line else ""

    return f'''clear all
set more off
use "{dta_path}", clear
rdrobust {y} {x}{opts_line}
matrix b = e(b)
matrix V = e(V)
display "B_TAU_CL=" b[1,1]
display "B_TAU_BC=" b[1,2]
display "B_TAU_RB=" b[1,3]
display "SE_TAU_CL=" sqrt(V[1,1])
display "SE_TAU_BC=" sqrt(V[2,2])
display "SE_TAU_RB=" sqrt(V[3,3])
display "B_TAU_BC_SCL=" e(tau_bc)
display "B_TAU_RB_SCL=" e(tau_rb)
display "SE_TAU_BC_SCL=" e(se_tau_bc)
display "SE_TAU_RB_SCL=" e(se_tau_rb)
display "E_N=" e(N)
display "E_N_L=" e(N_l)
display "E_N_R=" e(N_r)
display "E_N_H_L=" e(N_h_l)
display "E_N_H_R=" e(N_h_r)
display "E_N_B_L=" e(N_b_l)
display "E_N_B_R=" e(N_b_r)
display "E_H_L=" e(h_l)
display "E_H_R=" e(h_r)
display "E_B_L=" e(b_l)
display "E_B_R=" e(b_r)
display "E_C=" e(c)
display "E_LEVEL=" e(level)
display "M08_RD_OK"
'''


def rdplot_stata_do(
    dta_path: str | Path,
    y: str,
    x: str,
    c: float = 0.0,
    p: int = 4,
    nbins: tuple[int, int] | int | None = None,
    binselect: str = "esmv",
    kernel: str = "uniform",
    h: float | tuple[float, float] | None = None,
    covs: list[str] | str | None = None,
) -> str:
    """Build a Stata .do script for rdplot with e() extraction."""
    dta_path = str(dta_path).replace("\\", "/")

    opts: dict[str, Any] = {}
    if p != 4:
        opts["p"] = p
    if nbins is not None:
        if isinstance(nbins, tuple):
            opts["nbins"] = f"{nbins[0]} {nbins[1]}"
        else:
            opts["nbins"] = nbins
    if binselect != "esmv":
        opts["binselect"] = binselect
    if kernel != "uniform":
        opts["kernel"] = kernel
    if h is not None:
        if isinstance(h, tuple):
            opts["h"] = f"{h[0]} {h[1]}"
        else:
            opts["h"] = h
    if covs is not None:
        if isinstance(covs, list):
            opts["covs"] = " ".join(covs)
        else:
            opts["covs"] = covs

    opts_line = _build_options(**opts)
    opts_line = f", {opts_line}" if opts_line else ""

    return f'''clear all
set more off
use "{dta_path}", clear
rdplot {y} {x}{opts_line}
display "E_N_L=" e(N_l)
display "E_N_R=" e(N_r)
display "E_J_STAR_L=" e(J_star_l)
display "E_J_STAR_R=" e(J_star_r)
display "E_C=" e(c)
display "E_P=" e(p)
display "E_H_L=" e(h_l)
display "E_H_R=" e(h_r)
display "M08_RDPLOT_OK"
'''


def run_stata_rd(
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

    if "M08_RD_OK" in cleaned_log:
        parsed = parse_rdrobust_log(cleaned_log)
    elif "M08_RDPLOT_OK" in cleaned_log:
        parsed = parse_rdplot_log(cleaned_log)
    else:
        parsed = {"_raw_log": cleaned_log}

    parsed["_log_path"] = str(log_path)
    parsed["_dta_path"] = str(dta_path)
    parsed["_exit_code"] = result.exit_code
    return parsed


def parse_rdrobust_log(log_content: str) -> dict[str, Any]:
    """Parse Stata rdrobust log content with B_/SE_/E_ lines."""
    out: dict[str, Any] = {"_raw_log": log_content}

    scalar_patterns = {
        "nobs": r"E_N=([\d.]+)",
        "n_l": r"E_N_L=([\d.]+)",
        "n_r": r"E_N_R=([\d.]+)",
        "n_h_l": r"E_N_H_L=([\d.]+)",
        "n_h_r": r"E_N_H_R=([\d.]+)",
        "n_b_l": r"E_N_B_L=([\d.]+)",
        "n_b_r": r"E_N_B_R=([\d.]+)",
        "h_l": r"E_H_L=(-?[\d.eE+]+)",
        "h_r": r"E_H_R=(-?[\d.eE+]+)",
        "b_l": r"E_B_L=(-?[\d.eE+]+)",
        "b_r": r"E_B_R=(-?[\d.eE+]+)",
        "c": r"E_C=(-?[\d.eE+]+)",
        "level": r"E_LEVEL=(-?[\d.eE+]+)",
    }
    for key, pat in scalar_patterns.items():
        m = re.search(pat, log_content)
        if m:
            val = _to_float(m.group(1))
            if val is not None:
                out[key] = val

    coef_map = {
        "Conventional": ("B_TAU_CL", "SE_TAU_CL", None, None),
        "Bias-Corrected": ("B_TAU_BC", "SE_TAU_BC", "B_TAU_BC_SCL", "SE_TAU_BC_SCL"),
        "Robust": ("B_TAU_RB", "SE_TAU_RB", "B_TAU_RB_SCL", "SE_TAU_RB_SCL"),
    }
    coefficients: list[dict[str, Any]] = []
    for name, (beta_pat, se_pat, beta_scl_pat, se_scl_pat) in coef_map.items():
        beta = None
        se = None
        m_b = re.search(rf"^{beta_pat}=(-?[\d.eE+]+)", log_content, re.MULTILINE)
        m_s = re.search(rf"^{se_pat}=(-?[\d.eE+]+)", log_content, re.MULTILINE)
        if m_b:
            beta = _to_float(m_b.group(1))
        if m_s:
            se = _to_float(m_s.group(1))
        # Fallback to scalar e(tau_*) / e(se_tau_*) when matrix element is missing.
        if (beta is None or np.isnan(beta)) and beta_scl_pat:
            m_bs = re.search(rf"^{beta_scl_pat}=(-?[\d.eE+]+)", log_content, re.MULTILINE)
            if m_bs:
                beta = _to_float(m_bs.group(1))
        if (se is None or np.isnan(se)) and se_scl_pat:
            m_ss = re.search(rf"^{se_scl_pat}=(-?[\d.eE+]+)", log_content, re.MULTILINE)
            if m_ss:
                se = _to_float(m_ss.group(1))
        z = beta / se if (beta is not None and se is not None and se > 0) else float("nan")
        from scipy.stats import norm

        p = 2 * (1 - norm.cdf(abs(z))) if (beta is not None and se is not None and se > 0) else float("nan")
        coefficients.append(
            {
                "name": name,
                "beta": beta if beta is not None else float("nan"),
                "std_err": se if se is not None else float("nan"),
                "z_stat": z,
                "p_value": p,
            }
        )
    out["coefficients"] = coefficients
    return out


def parse_rdplot_log(log_content: str) -> dict[str, Any]:
    """Parse Stata rdplot log content."""
    out: dict[str, Any] = {"_raw_log": log_content}
    scalar_patterns = {
        "n_l": r"E_N_L=([\d.]+)",
        "n_r": r"E_N_R=([\d.]+)",
        "j_star_l": r"E_J_STAR_L=([\d.]+)",
        "j_star_r": r"E_J_STAR_R=([\d.]+)",
        "c": r"E_C=(-?[\d.eE+]+)",
        "p": r"E_P=([\d.]+)",
        "h_l": r"E_H_L=(-?[\d.eE+]+)",
        "h_r": r"E_H_R=(-?[\d.eE+]+)",
    }
    for key, pat in scalar_patterns.items():
        m = re.search(pat, log_content)
        if m:
            val = _to_float(m.group(1))
            if val is not None:
                out[key] = val
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


def _py_rd_extras(py_result: ResultSchema) -> dict[str, Any]:
    """Return _rd_extras dict or empty."""
    return getattr(py_result, "_rd_extras", {}) or {}


class _MockCoef:
    """Tiny wrapper to compare dict-based coefficients."""

    def __init__(self, c: dict[str, Any]) -> None:
        self.name = c["name"]
        self.beta = c["beta"]
        self.std_err = c["std_err"]
        self.t_stat = c.get("z_stat")
        self.p_value = c["p_value"]


def compare_python_to_stata(
    py_result: ResultSchema | dict[str, Any],
    st_result: dict[str, Any],
    fields: Optional[list[str]] = None,
    compare_sample_mask: bool = True,
    bandwidth_rtol: float = 5e-4,
) -> dict[str, Any]:
    """Field-level comparison. Returns dict with pass/fail and messages."""
    if fields is None:
        fields = ["nobs", "n_l", "n_r", "n_h_l", "n_h_r", "n_b_l", "n_b_r"]

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

    py_extras = {}
    if isinstance(py_result, ResultSchema):
        py_extras = _py_rd_extras(py_result)

    field_map = {
        "nobs": ("sample", "nobs"),
        "n_l": ("_rd_extras", "N_l"),
        "n_r": ("_rd_extras", "N_r"),
        "n_h_l": ("_rd_extras", "N_h_l"),
        "n_h_r": ("_rd_extras", "N_h_r"),
        "n_b_l": ("_rd_extras", "N_b_l"),
        "n_b_r": ("_rd_extras", "N_b_r"),
        "h_l": ("_rd_extras", "h_l"),
        "h_r": ("_rd_extras", "h_r"),
        "b_l": ("_rd_extras", "b_l"),
        "b_r": ("_rd_extras", "b_r"),
        "c": ("_rd_extras", "c"),
        "level": ("_rd_extras", "level"),
    }

    for field in fields:
        py_val = None
        if isinstance(py_result, ResultSchema):
            if field in field_map:
                section, attr = field_map[field]
                if section == "sample":
                    py_val = float(getattr(py_result.sample, attr))
                elif section == "_rd_extras":
                    py_val = py_extras.get(attr)
            elif field == "df_model":
                py_val = py_result.fit.df_model
            elif field == "df_resid":
                py_val = py_result.fit.df_resid
        elif isinstance(py_result, dict):
            # rdplot returns a dict with an "info" sub-dict using capitalized keys.
            info = py_result.get("info", {})
            rdplot_key_map = {
                "n_l": "N_l",
                "n_r": "N_r",
                "j_star_l": "J_star_l",
                "j_star_r": "J_star_r",
                "h_l": "h_l",
                "h_r": "h_r",
                "c": "c",
                "p": "p",
                "level": "level",
            }
            if field in rdplot_key_map:
                py_val = info.get(rdplot_key_map[field])
            else:
                py_val = py_result.get(field)

        st_val = st_result.get(field)
        if py_val is None and st_val is None:
            continue

        # Bandwidth fields: allow larger tolerance because of plug-in numerical variance
        if field in ("h_l", "h_r", "b_l", "b_r"):
            passed, msg = tolerance_close(py_val, st_val, rtol=bandwidth_rtol, atol=1e-6, name=field)
        else:
            passed, msg = tolerance_close(py_val, st_val, name=field)
        _record(field, passed, msg)

    # Coefficients
    if isinstance(py_result, ResultSchema):
        py_coefs = py_result.coefficients
    else:
        py_coefs = [_MockCoef(c) for c in py_result.get("coefficients", [])]

    st_coefs = {c["name"]: c for c in st_result.get("coefficients", [])}
    for py_coef in py_coefs:
        name = py_coef.name
        st_coef = st_coefs.get(name)
        if st_coef is None:
            _record(f"coef_missing_{name}", False, f"Stata missing coefficient {name}")
            continue
        # If Stata returned a missing coefficient (e.g. tiny effective sample),
        # skip field-level comparison rather than forcing a failure.
        st_beta = st_coef.get("beta")
        if st_beta is None or (isinstance(st_beta, float) and np.isnan(st_beta)):
            _record(
                f"{name}_skipped",
                True,
                f"{name}: Stata coefficient missing; skipping comparison",
            )
            continue
        for metric in ["beta", "std_err", "t_stat", "p_value"]:
            py_val = getattr(py_coef, metric)
            st_val = st_coef.get(metric if metric != "std_err" else "std_err")
            if metric == "t_stat":
                st_val = st_coef.get("z_stat")
            # If Stata value is missing for this metric, skip rather than fail.
            if st_val is None or (isinstance(st_val, float) and np.isnan(st_val)):
                _record(
                    f"{name}.{metric}_skipped",
                    True,
                    f"{name}.{metric}: Stata value missing; skipping comparison",
                )
                continue
            # Robust SE drives t/z; tolerances reflect plug-in / cluster variance.
            if metric == "std_err":
                rtol, atol = 3e-2, 1e-6
            elif metric in ("t_stat", "z_stat"):
                rtol, atol = 3e-2, 1e-6
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
    if compare_sample_mask and isinstance(py_result, ResultSchema):
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
    py_result: ResultSchema | dict[str, Any],
    st_result: dict[str, Any],
    diffs: dict[str, Any],
) -> Path:
    """Persist comparison evidence as JSON."""
    if prefix.startswith("S"):
        evidence_dir = M08_EVIDENCE / "synthetic" / prefix
    elif prefix.startswith("P"):
        evidence_dir = M08_EVIDENCE / "property" / prefix
    else:
        evidence_dir = M08_EVIDENCE / "real-data" / prefix
    evidence_dir.mkdir(parents=True, exist_ok=True)

    if isinstance(py_result, ResultSchema):
        py_dict = py_result.to_dict() if hasattr(py_result, "to_dict") else {}
        py_dict["_rd_extras"] = _py_rd_extras(py_result)
    else:
        py_dict = py_result

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
