"""Phase 2 DID dual-run validation script (v2 - fixed Stata commands)."""

from __future__ import annotations

import os
import sys
import re
import json
import traceback
import time
import subprocess
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path("D:/OneDrive - SAIF/PhD3/StataFlow")
STATA_EXE = "D:/Software/Stata17/StataMP-64.exe"
DATA_PATH = PROJECT_ROOT / "research/data/public/did/ezunem_prepared.dta"
OUTPUT_DIR = PROJECT_ROOT / "stata/output/phase2"
REPORT_DIR = PROJECT_ROOT / "docs/audit/revalidation-v1.1/phase2-evidence"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(PROJECT_ROOT / "src"))

from stataflow.compat.stata.did import csdid, did_imputation, eventstudyinteract


def run_stata_do(do_content: str, output_dir: Path) -> tuple[str, str, int]:
    output_dir = output_dir.resolve()
    timestamp = int(time.time() * 1000)
    do_file = output_dir / f"run_{timestamp}.do"
    log_file = output_dir / f"run_{timestamp}.log"
    do_file.write_text(do_content, encoding="utf-8")
    cmd = f'cd /d "{output_dir}" && "{STATA_EXE}" /e do {do_file.name}'
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = 0
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True, startupinfo=startupinfo, cwd=str(output_dir))
    log_content = result.stdout
    if not log_content and log_file.exists():
        log_content = log_file.read_text(encoding="utf-8", errors="replace")
    return log_content, result.stderr, result.returncode


def parse_stata_log(text: str) -> dict:
    coeffs = []
    nobs = None
    error = None
    
    # Detect error
    err_match = re.search(r'r\((\d+)\);', text)
    if err_match:
        error = f"Stata error r({err_match.group(1)})"
    
    # csdid event table
    if "ATT by Periods Before and After treatment" in text or "Event Study:Dynamic effects" in text:
        lines = text.splitlines()
        in_table = False
        for line in lines:
            if "Event Study:Dynamic effects" in line or "ATT by Periods Before and After treatment" in line:
                in_table = True
                continue
            if in_table:
                if re.match(r"\s*[-=]+", line):
                    continue
                if line.strip() == "":
                    continue
                m = re.match(
                    r"\s*(Tm?\d+|Tp?\d+|Pre_avg|Post_avg)\s*\|\s*"
                    r"([\-\d\.]+)\s+([\-\d\.]+)\s+([\-\d\.]+)\s+([\-\d\.]+)\s+"
                    r"([\-\d\.]+)\s+([\-\d\.]+)",
                    line,
                )
                if m:
                    coeffs.append({
                        "name": m.group(1).strip(),
                        "beta": float(m.group(2)),
                        "std_err": float(m.group(3)),
                        "t_stat": float(m.group(4)),
                        "p_value": float(m.group(5)),
                        "ci_low": float(m.group(6)),
                        "ci_high": float(m.group(7)),
                    })
    
    # csdid pretrend
    if "Pretrend Test" in text or "pretrend" in text.lower():
        f_match = re.search(r"chi2\((\d+)\)\s*=\s*([\d\.]+)", text)
        p_match = re.search(r"p-value\s*=\s*([\d\.]+)", text)
        if f_match:
            coeffs.append({
                "name": "pretrend_chi2",
                "beta": float(f_match.group(2)),
                "std_err": 0.0,
                "t_stat": float(f_match.group(2)),
                "p_value": float(p_match.group(1)) if p_match else np.nan,
                "df": int(f_match.group(1)),
            })
    
    # did_imputation table
    lines = text.splitlines()
    in_table = False
    for line in lines:
        if "Coefficient" in line and "Std. err." in line:
            in_table = True
            continue
        if in_table:
            if re.match(r"\s*[-=]+", line):
                continue
            if line.strip() == "":
                continue
            m = re.match(
                r"\s*(tau\d+|tau|pre\d+|sum)\s*\|\s*"
                r"([\-\d\.]+)\s+([\-\d\.]+)\s+([\-\d\.]+)\s+([\-\d\.]+)\s+"
                r"([\-\d\.]+)\s+([\-\d\.]+)",
                line,
            )
            if m:
                coeffs.append({
                    "name": m.group(1).strip(),
                    "beta": float(m.group(2)),
                    "std_err": float(m.group(3)),
                    "t_stat": float(m.group(4)),
                    "p_value": float(m.group(5)),
                    "ci_low": float(m.group(6)),
                    "ci_high": float(m.group(7)),
                })
            elif "(omitted)" in line:
                m2 = re.match(r"\s*(tau\d+|tau|pre\d+|sum)\s*\|\s*([\-\d\.]+)?\s*\(omitted\)", line)
                if m2:
                    coeffs.append({
                        "name": m2.group(1).strip(),
                        "beta": 0.0,
                        "std_err": 0.0,
                        "t_stat": 0.0,
                        "p_value": 1.0,
                        "omitted": True,
                    })
    
    # eventstudyinteract table
    if "eventstudyinteract" in text.lower() or "IW estimates" in text:
        for line in lines:
            m = re.match(
                r"\s*(Dm\d+|Dp\d+|D0)\s*\|\s*"
                r"([\-\d\.]+)\s+([\-\d\.]+)\s+([\-\d\.]+)\s+([\-\d\.]+)\s+"
                r"([\-\d\.]+)\s+([\-\d\.]+)",
                line,
            )
            if m:
                coeffs.append({
                    "name": m.group(1).strip(),
                    "beta": float(m.group(2)),
                    "std_err": float(m.group(3)),
                    "t_stat": float(m.group(4)),
                    "p_value": float(m.group(5)),
                    "ci_low": float(m.group(6)),
                    "ci_high": float(m.group(7)),
                })
    
    n_match = re.search(r"Number\s+of\s+obs\s*=\s*(\d+)", text, re.IGNORECASE)
    if n_match:
        nobs = int(n_match.group(1))
    else:
        n_match2 = re.search(r"Observations\s*:\s*(\d+)", text, re.IGNORECASE)
        if n_match2:
            nobs = int(n_match2.group(1))
    
    return {"coefficients": coeffs, "nobs": nobs, "error": error, "raw_text": text}


def rel_diff(py_val, st_val):
    if py_val is None or st_val is None:
        return np.nan
    if np.isnan(py_val) or np.isnan(st_val):
        return np.nan
    denom = max(abs(st_val), 1e-10)
    return abs(py_val - st_val) / denom


def py_coeffs_to_dict(py_result):
    return {
        "coefficients": [
            {
                "name": c.name,
                "beta": c.beta,
                "std_err": c.std_err,
                "t_stat": c.t_stat,
                "p_value": c.p_value,
            }
            for c in py_result.coefficients
        ],
        "nobs": py_result.sample.nobs,
        "type": type(py_result).__name__,
    }


df = pd.read_stata(DATA_PATH)
results = {}

# ═══════════════════════════════════════════════════════════════════════
# 1. CSDID basic
# ═══════════════════════════════════════════════════════════════════════
print("TEST 1: CSDID basic")
try:
    py_result = csdid(df, y="uclms", id="city", time="year", first_treat="first_treat", aggtype="event")
    py_csdid_basic = py_coeffs_to_dict(py_result)
except Exception as e:
    py_csdid_basic = {"error": str(e), "traceback": traceback.format_exc()}

do_content = f'''use "{DATA_PATH}", clear\ncsdid uclms, ivar(city) time(year) gvar(first_treat) agg(event)\nestat event\n'''
log_text, stderr, rc = run_stata_do(do_content, OUTPUT_DIR)
st_csdid_basic = parse_stata_log(log_text)
st_csdid_basic["stderr"] = stderr
st_csdid_basic["returncode"] = rc
results["csdid_basic"] = {"python": py_csdid_basic, "stata": st_csdid_basic}

# ═══════════════════════════════════════════════════════════════════════
# 2. CSDID pretrend
# ═══════════════════════════════════════════════════════════════════════
print("TEST 2: CSDID pretrend")
try:
    py_result = csdid(df, y="uclms", id="city", time="year", first_treat="first_treat", aggtype="pretrend")
    py_csdid_pretrend = {
        "type": type(py_result).__name__,
        "value": py_result if isinstance(py_result, dict) else str(py_result),
    }
except Exception as e:
    py_csdid_pretrend = {"error": str(e), "traceback": traceback.format_exc()}

do_content = f'''use "{DATA_PATH}", clear\ncsdid uclms, ivar(city) time(year) gvar(first_treat)\nestat pretrend\n'''
log_text, stderr, rc = run_stata_do(do_content, OUTPUT_DIR)
st_csdid_pretrend = parse_stata_log(log_text)
st_csdid_pretrend["stderr"] = stderr
st_csdid_pretrend["returncode"] = rc
results["csdid_pretrend"] = {"python": py_csdid_pretrend, "stata": st_csdid_pretrend}

# ═══════════════════════════════════════════════════════════════════════
# 3. did_imputation basic (with autosample to match Stata requirement)
# ═══════════════════════════════════════════════════════════════════════
print("TEST 3: did_imputation basic")
try:
    py_result = did_imputation(df, y="uclms", id="city", time="year", first_treat="first_treat", autosample=True)
    py_did_basic = py_coeffs_to_dict(py_result)
except Exception as e:
    py_did_basic = {"error": str(e), "traceback": traceback.format_exc()}

do_content = f'''use "{DATA_PATH}", clear\ndid_imputation uclms city year first_treat, autosample\n'''
log_text, stderr, rc = run_stata_do(do_content, OUTPUT_DIR)
st_did_basic = parse_stata_log(log_text)
st_did_basic["stderr"] = stderr
st_did_basic["returncode"] = rc
results["did_basic"] = {"python": py_did_basic, "stata": st_did_basic}

# ═══════════════════════════════════════════════════════════════════════
# 4. did_imputation allhorizons
# ═══════════════════════════════════════════════════════════════════════
print("TEST 4: did_imputation allhorizons")
try:
    result_false = did_imputation(df, y="uclms", id="city", time="year", first_treat="first_treat", autosample=True, allhorizons=False)
    result_true = did_imputation(df, y="uclms", id="city", time="year", first_treat="first_treat", autosample=True, allhorizons=True)
    coeffs_false = {c.name: c.beta for c in result_false.coefficients}
    coeffs_true = {c.name: c.beta for c in result_true.coefficients}
    py_did_allh = {
        "allhorizons_false": py_coeffs_to_dict(result_false),
        "allhorizons_true": py_coeffs_to_dict(result_true),
        "same_coefficients": coeffs_false == coeffs_true,
        "false_keys": list(coeffs_false.keys()),
        "true_keys": list(coeffs_true.keys()),
    }
except Exception as e:
    py_did_allh = {"error": str(e), "traceback": traceback.format_exc()}

do_content = f'''use "{DATA_PATH}", clear\ndid_imputation uclms city year first_treat, autosample allhorizons\n'''
log_text, stderr, rc = run_stata_do(do_content, OUTPUT_DIR)
st_did_allh = parse_stata_log(log_text)
st_did_allh["stderr"] = stderr
st_did_allh["returncode"] = rc
results["did_allhorizons"] = {"python": py_did_allh, "stata": st_did_allh}

# ═══════════════════════════════════════════════════════════════════════
# 5. did_imputation with cluster
# ═══════════════════════════════════════════════════════════════════════
print("TEST 5: did_imputation with cluster")
try:
    py_result = did_imputation(df, y="uclms", id="city", time="year", first_treat="first_treat", autosample=True, cluster="city")
    py_did_cluster = py_coeffs_to_dict(py_result)
except Exception as e:
    py_did_cluster = {"error": str(e), "traceback": traceback.format_exc()}

do_content = f'''use "{DATA_PATH}", clear\ndid_imputation uclms city year first_treat, autosample cluster(city)\n'''
log_text, stderr, rc = run_stata_do(do_content, OUTPUT_DIR)
st_did_cluster = parse_stata_log(log_text)
st_did_cluster["stderr"] = stderr
st_did_cluster["returncode"] = rc
results["did_cluster"] = {"python": py_did_cluster, "stata": st_did_cluster}

# ═══════════════════════════════════════════════════════════════════════
# 6. eventstudyinteract basic
# ═══════════════════════════════════════════════════════════════════════
print("TEST 6: eventstudyinteract basic")
try:
    df_es = df.copy()
    df_es["cohort"] = df_es["first_treat"]
    df_es["control_cohort"] = (df_es["first_treat"] == 0).astype(int)
    df_es["rel_time"] = df_es["year"] - df_es["first_treat"]
    df_es.loc[df_es["first_treat"] == 0, "rel_time"] = -1000
    horizons = list(range(-3, 4))
    omit = -1
    event_dummies = []
    for h in horizons:
        if h == omit:
            continue
        if h < 0:
            col = f"Dm{abs(h)}"
        elif h == 0:
            col = "D0"
        else:
            col = f"Dp{h}"
        df_es[col] = (df_es["rel_time"] == h).astype(float)
        event_dummies.append(col)
    py_result = eventstudyinteract(df_es, y="uclms", cohort="cohort", control_cohort="control_cohort", absorb=["city", "year"], event_dummies=event_dummies)
    py_es_basic = py_coeffs_to_dict(py_result)
except Exception as e:
    py_es_basic = {"error": str(e), "traceback": traceback.format_exc()}

do_content = f'''use "{DATA_PATH}", clear\ngen cohort = first_treat\ngen control_cohort = first_treat == 0\ngen rel_time = year - first_treat if first_treat > 0\nforvalues h = 3(-1)1 {{\n    gen Dm`h' = (rel_time == -`h')\n}}\ngen D0 = (rel_time == 0)\nforvalues h = 1/3 {{\n    gen Dp`h' = (rel_time == `h')\n}}\neventstudyinteract uclms Dm3 Dm2 D0 Dp1 Dp2 Dp3, cohort(cohort) control_cohort(control_cohort) absorb(city year)\n'''
log_text, stderr, rc = run_stata_do(do_content, OUTPUT_DIR)
st_es_basic = parse_stata_log(log_text)
st_es_basic["stderr"] = stderr
st_es_basic["returncode"] = rc
results["eventstudyinteract_basic"] = {"python": py_es_basic, "stata": st_es_basic}

# ═══════════════════════════════════════════════════════════════════════
# 7. CSDID kwargs bug
# ═══════════════════════════════════════════════════════════════════════
print("TEST 7: CSDID kwargs bug (notyet)")
try:
    py_result = csdid(df, y="uclms", id="city", time="year", first_treat="first_treat", notyet=True)
    py_csdid_notyet = {"type": type(py_result).__name__}
except Exception as e:
    py_csdid_notyet = {"error": str(e), "traceback": traceback.format_exc()}
results["csdid_notyet"] = {"python": py_csdid_notyet, "stata": {"note": "notyet is a Stata csdid option"}}

# ═══════════════════════════════════════════════════════════════════════
# 8. CSDID unbalanced panel
# ═══════════════════════════════════════════════════════════════════════
print("TEST 8: CSDID unbalanced panel")
try:
    df_unbal = df.copy()
    np.random.seed(42)
    drop_idx = np.random.choice(df_unbal.index, size=20, replace=False)
    df_unbal.loc[drop_idx, "uclms"] = np.nan
    py_result = csdid(df_unbal, y="uclms", id="city", time="year", first_treat="first_treat", aggtype="event")
    py_csdid_unbal = {
        "coefficients": [{"name": c.name, "beta": c.beta, "std_err": c.std_err} for c in py_result.coefficients],
        "nobs": py_result.sample.nobs,
        "has_nan": any(np.isnan(c.beta) or np.isnan(c.std_err) for c in py_result.coefficients),
    }
except Exception as e:
    py_csdid_unbal = {"error": str(e), "traceback": traceback.format_exc()}
results["csdid_unbalanced"] = {"python": py_csdid_unbal, "stata": {"note": "Synthetic NaN test"}}

# Save JSON
snapshot_path = OUTPUT_DIR / "phase2_results_v2.json"
class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)
snapshot_path.write_text(json.dumps(results, indent=2, cls=NpEncoder), encoding="utf-8")
print("\nAll tests completed. Results saved to:", snapshot_path)
