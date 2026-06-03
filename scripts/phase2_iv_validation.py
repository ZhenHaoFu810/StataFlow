"""
Phase 2 IV/GMM dual-run validation script.
Runs Python and Stata 17 side-by-side on Card dataset.
Writes results and comparison reports.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from stataflow.compat.stata.iv import ivregress_2sls, ivreghdfe
from stataflow.stata_runner import StataRunner

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "stata" / "output" / "phase2"
REPORT_DIR = PROJECT_ROOT / "docs" / "audit" / "revalidation-v1.1" / "phase2-evidence"
DATA_PATH = PROJECT_ROOT / "research" / "data" / "public" / "iv" / "card.csv"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

# Load data
df = pd.read_csv(DATA_PATH)

# Add pseudo FE variable for ivreghdfe testing
df["age_group"] = (df["age"] // 5).astype(int)

# ============================================================================
# Python runs
# ============================================================================

def run_python_scenarios():
    results = {}

    # Scenario 1: ivregress 2sls, vce(ols)
    print("Running Python scenario 1: ivregress_2sls vce=ols")
    r = ivregress_2sls(
        df, y="lwage", x_exog=["exper", "expersq", "black", "south", "smsa"],
        x_endog=["educ"], instruments=["nearc4"], vce="ols"
    )
    results["py_ivregress_ols"] = extract_result(r)

    # Scenario 2: ivregress 2sls, vce(robust)
    print("Running Python scenario 2: ivregress_2sls vce=robust")
    r = ivregress_2sls(
        df, y="lwage", x_exog=["exper", "expersq", "black", "south", "smsa"],
        x_endog=["educ"], instruments=["nearc4"], vce="robust"
    )
    results["py_ivregress_robust"] = extract_result(r)

    # Scenario 3: ivregress 2sls, vce(cluster age)
    print("Running Python scenario 3: ivregress_2sls vce=cluster age")
    r = ivregress_2sls(
        df, y="lwage", x_exog=["exper", "expersq", "black", "south", "smsa"],
        x_endog=["educ"], instruments=["nearc4"], vce="cluster", cluster="age"
    )
    results["py_ivregress_cluster_age"] = extract_result(r)

    # Scenario 4: ivregress 2sls, vce(cluster south)
    print("Running Python scenario 4: ivregress_2sls vce=cluster south")
    r = ivregress_2sls(
        df, y="lwage", x_exog=["exper", "expersq", "black", "south", "smsa"],
        x_endog=["educ"], instruments=["nearc4"], vce="cluster", cluster="south"
    )
    results["py_ivregress_cluster_south"] = extract_result(r)

    # Scenario 5: ivreghdfe with pseudo FE, cluster
    print("Running Python scenario 5: ivreghdfe absorb(age_group) cluster(age_group)")
    try:
        r = ivreghdfe(
            df, y="lwage", x_exog=["exper", "expersq", "black", "south", "smsa"],
            x_endog=["educ"], instruments=["nearc4"],
            absorb="age_group", vce="cluster", cluster="age_group",
            first=True
        )
        results["py_ivreghdfe_cluster"] = extract_result(r, include_first=True)
    except Exception as e:
        print(f"  FAILED: {e}")
        results["py_ivreghdfe_cluster"] = {"error": str(e)}

    # Scenario 6: ivreghdfe 2-way cluster
    print("Running Python scenario 6: ivreghdfe 2-way cluster")
    try:
        r = ivreghdfe(
            df, y="lwage", x_exog=["exper", "expersq", "black", "south", "smsa"],
            x_endog=["educ"], instruments=["nearc4"],
            absorb="age_group", vce="cluster", cluster=["age_group", "south"],
            first=True
        )
        results["py_ivreghdfe_2way"] = extract_result(r, include_first=True)
    except Exception as e:
        print(f"  FAILED: {e}")
        results["py_ivreghdfe_2way"] = {"error": str(e)}

    return results


def extract_result(r, include_first=False):
    d = {
        "nobs": r.sample.nobs,
        "df_model": r.fit.df_model,
        "df_resid": r.fit.df_resid,
        "rmse": r.fit.rmse,
        "r2": r.fit.r2,
        "r2_adj": r.fit.r2_adj,
        "f_stat": r.fit.f_stat,
        "f_pvalue": r.fit.f_pvalue,
        "coefficients": [
            {
                "name": c.name,
                "beta": c.beta,
                "std_err": c.std_err,
                "t_stat": c.t_stat,
                "p_value": c.p_value,
            }
            for c in r.coefficients
        ],
    }
    if hasattr(r, "idstat"):
        d["weakiv"] = {
            "idstat": getattr(r, "idstat", None),
            "iddf": getattr(r, "iddf", None),
            "idp": getattr(r, "idp", None),
            "widstat": getattr(r, "widstat", None),
            "sy_10pct": getattr(r, "sy_10pct", None),
            "sy_15pct": getattr(r, "sy_15pct", None),
            "sy_20pct": getattr(r, "sy_20pct", None),
            "sy_25pct": getattr(r, "sy_25pct", None),
        }
    if include_first and hasattr(r, "first_stage"):
        d["first_stage"] = r.first_stage
    return d


# ============================================================================
# Stata runs
# ============================================================================

STATA_IVREGRESS_OLS_DO = r"""
clear all
set more off
import delimited "D:/OneDrive - SAIF/PhD3/StataFlow/research/data/public/iv/card.csv", clear

* Stata ivregress 2sls conventional VCE is default (no vce option) or vce(unadjusted)
ivregress 2sls lwage (educ = nearc4) exper expersq black south smsa

display "===SCENARIO==="
display "ivregress_ols"
display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_DF_R=" e(df_r)
display "E_RMSE=" e(rmse)
display "E_R2=" e(r2)
display "E_R2_A=" e(r2_a)

foreach var in educ exper expersq black south smsa _cons {
    display "B_`var'=" _b[`var']
    display "SE_`var'=" _se[`var']
    display "T_`var'=" (_b[`var']/_se[`var'])
}
"""

STATA_IVREGRESS_ROBUST_DO = r"""
clear all
set more off
import delimited "D:/OneDrive - SAIF/PhD3/StataFlow/research/data/public/iv/card.csv", clear

ivregress 2sls lwage (educ = nearc4) exper expersq black south smsa, vce(robust)

display "===SCENARIO==="
display "ivregress_robust"
display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_DF_R=" e(df_r)
display "E_RMSE=" e(rmse)
display "E_R2=" e(r2)
display "E_R2_A=" e(r2_a)

foreach var in educ exper expersq black south smsa _cons {
    display "B_`var'=" _b[`var']
    display "SE_`var'=" _se[`var']
    display "Z_`var'=" (_b[`var']/_se[`var'])
}
"""

STATA_IVREGRESS_CLUSTER_AGE_DO = r"""
clear all
set more off
import delimited "D:/OneDrive - SAIF/PhD3/StataFlow/research/data/public/iv/card.csv", clear

ivregress 2sls lwage (educ = nearc4) exper expersq black south smsa, vce(cluster age)

display "===SCENARIO==="
display "ivregress_cluster_age"
display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_DF_R=" e(df_r)
display "E_N_CLUST=" e(N_clust)
display "E_RMSE=" e(rmse)
display "E_R2=" e(r2)
display "E_R2_A=" e(r2_a)

foreach var in educ exper expersq black south smsa _cons {
    display "B_`var'=" _b[`var']
    display "SE_`var'=" _se[`var']
    display "Z_`var'=" (_b[`var']/_se[`var'])
}
"""

STATA_IVREGRESS_CLUSTER_SOUTH_DO = r"""
clear all
set more off
import delimited "D:/OneDrive - SAIF/PhD3/StataFlow/research/data/public/iv/card.csv", clear

ivregress 2sls lwage (educ = nearc4) exper expersq black south smsa, vce(cluster south)

display "===SCENARIO==="
display "ivregress_cluster_south"
display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_DF_R=" e(df_r)
display "E_N_CLUST=" e(N_clust)
display "E_RMSE=" e(rmse)
display "E_R2=" e(r2)
display "E_R2_A=" e(r2_a)

foreach var in educ exper expersq black south smsa _cons {
    display "B_`var'=" _b[`var']
    display "SE_`var'=" _se[`var']
    display "Z_`var'=" (_b[`var']/_se[`var'])
}
"""

STATA_IVREGRESS_FIRST_OLS_DO = r"""
clear all
set more off
import delimited "D:/OneDrive - SAIF/PhD3/StataFlow/research/data/public/iv/card.csv", clear

ivregress 2sls lwage (educ = nearc4) exper expersq black south smsa, first

display "===SCENARIO==="
display "ivregress_first_ols"
display "E_N=" e(N)

* First-stage results are in the log; we parse manually
"""

STATA_IVREGRESS_FIRST_ROBUST_DO = r"""
clear all
set more off
import delimited "D:/OneDrive - SAIF/PhD3/StataFlow/research/data/public/iv/card.csv", clear

ivregress 2sls lwage (educ = nearc4) exper expersq black south smsa, vce(robust) first

display "===SCENARIO==="
display "ivregress_first_robust"
"""

STATA_IVREGRESS_FIRST_CLUSTER_DO = r"""
clear all
set more off
import delimited "D:/OneDrive - SAIF/PhD3/StataFlow/research/data/public/iv/card.csv", clear

ivregress 2sls lwage (educ = nearc4) exper expersq black south smsa, vce(cluster age) first

display "===SCENARIO==="
display "ivregress_first_cluster"
"""

STATA_IVREGHDFE_CLUSTER_DO = r"""
clear all
set more off
import delimited "D:/OneDrive - SAIF/PhD3/StataFlow/research/data/public/iv/card.csv", clear

gen age_group = floor(age/5)

ivreghdfe lwage (educ = nearc4) exper expersq black south smsa, absorb(age_group) cluster(age_group) first

display "===SCENARIO==="
display "ivreghdfe_cluster"
display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_DF_R=" e(df_r)
display "E_DF_A=" e(df_a)
display "E_N_CLUST=" e(N_clust)
display "E_RMSE=" e(rmse)
display "E_R2=" e(r2)
display "E_R2_A=" e(r2_a)

matrix b = e(b)
matrix V = e(V)
local vars : colfullnames b
local k = colsof(b)
forvalues i = 1/`k' {
    local vname : word `i' of `vars'
    local beta = b[1,`i']
    local se = sqrt(V[`i',`i'])
    display "B_`vname'=" `beta'
    display "SE_`vname'=" `se'
    display "T_`vname'=" (`beta'/`se')
}
"""

STATA_IVREGHDFE_2WAY_DO = r"""
clear all
set more off
import delimited "D:/OneDrive - SAIF/PhD3/StataFlow/research/data/public/iv/card.csv", clear

gen age_group = floor(age/5)

ivreghdfe lwage (educ = nearc4) exper expersq black south smsa, absorb(age_group) vce(cluster age_group south) first

display "===SCENARIO==="
display "ivreghdfe_2way"
display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_DF_R=" e(df_r)
display "E_DF_A=" e(df_a)
display "E_N_CLUST=" e(N_clust)
display "E_RMSE=" e(rmse)
display "E_R2=" e(r2)
display "E_R2_A=" e(r2_a)

matrix b = e(b)
matrix V = e(V)
local vars : colfullnames b
local k = colsof(b)
forvalues i = 1/`k' {
    local vname : word `i' of `vars'
    local beta = b[1,`i']
    local se = sqrt(V[`i',`i'])
    display "B_`vname'=" `beta'
    display "SE_`vname'=" `se'
    display "T_`vname'=" (`beta'/`se')
}
"""


def run_stata_scenario(name: str, do_content: str) -> dict:
    print(f"Running Stata scenario: {name}")
    runner = StataRunner()
    result = runner.run_do_file(do_content, output_dir=str(OUTPUT_DIR), timeout=120)

    # Save log content for inspection
    log_path = OUTPUT_DIR / f"stata_{name}.log"
    if result.log_file and os.path.exists(result.log_file):
        with open(result.log_file, "r", encoding="utf-8", errors="replace") as f:
            log_content = f.read()
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(log_content)
    else:
        log_content = ""

    if result.exit_code != 0:
        print(f"  Stata failed with exit code {result.exit_code}")
        return {"error": f"exit_code={result.exit_code}", "log": log_content}

    return parse_stata_log(log_content)


def parse_stata_log(log_content: str) -> dict:
    """Parse Stata log for our display output format."""
    result = {"coefficients": []}

    # Find scenario name
    m = re.search(r'===SCENARIO===\s+([\w_]+)', log_content)
    if m:
        result["scenario"] = m.group(1)

    # Parse E_ values
    e_patterns = {
        'nobs': r'E_N=([\d]+)',
        'df_model': r'E_DF_M=([\d]+)',
        'df_resid': r'E_DF_R=([\d]+)',
        'df_a': r'E_DF_A=([\d]+)',
        'r2': r'E_R2=([\d.eE+-]+)',
        'r2_adj': r'E_R2_A=([\d.eE+-]+)',
        'rmse': r'E_RMSE=([\d.eE+-]+)',
        'n_clust': r'E_N_CLUST=([\d]+)',
    }
    for key, pattern in e_patterns.items():
        m = re.search(pattern, log_content)
        if m:
            val_str = m.group(1)
            if val_str.startswith('.'):
                val_str = '0' + val_str
            try:
                result[key] = float(val_str)
            except ValueError:
                pass

    # Parse coefficients (handle optional equation prefix like "lwage:educ")
    b_matches = {}
    for k, v in re.findall(r'B_([\w:]+)=(-?[\d.eE+-]+)', log_content):
        name = k.split(':')[-1].lower()
        b_matches[name] = float(v)
    se_matches = {}
    for k, v in re.findall(r'SE_([\w:]+)=(-?[\d.eE+-]+)', log_content):
        name = k.split(':')[-1].lower()
        se_matches[name] = float(v)
    t_matches = {}
    for k, v in re.findall(r'T_([\w:]+)=(-?[\d.eE+-]+)', log_content):
        name = k.split(':')[-1].lower()
        t_matches[name] = float(v)
    z_matches = {}
    for k, v in re.findall(r'Z_([\w:]+)=(-?[\d.eE+-]+)', log_content):
        name = k.split(':')[-1].lower()
        z_matches[name] = float(v)

    all_names = set(b_matches.keys()) & set(se_matches.keys())
    order = ['educ', 'exper', 'expersq', 'black', 'south', 'smsa', '_cons']
    for name in sorted(all_names, key=lambda x: order.index(x) if x in order else 999):
        coef = {"name": name, "beta": b_matches[name], "std_err": se_matches[name]}
        if name in t_matches:
            coef["t_stat"] = t_matches[name]
        if name in z_matches:
            coef["z_stat"] = z_matches[name]
        result["coefficients"].append(coef)

    # Parse first-stage F statistics from ivreghdfe / ivregress first output
    fs_f = re.search(r'F test of excluded instruments:\s+F\(\s*\d+,\s*\d+\)\s*=\s*([\d.]+)', log_content)
    if fs_f:
        result["first_stage_f"] = float(fs_f.group(1))
    fs_p = re.search(r'Prob > F\s*=\s*([\d.]+)', log_content)
    if fs_p:
        result["first_stage_p"] = float(fs_p.group(1))

    # Parse weak instrument stats
    weak_f = re.search(r'Kleibergen-Paap Wald rk F statistic\s+([\d.]+)', log_content)
    if weak_f:
        result["weakiv_kp_f"] = float(weak_f.group(1))
    cd_f = re.search(r'Cragg-Donald Wald F statistic\s+([\d.]+)', log_content)
    if cd_f:
        result["weakiv_cd_f"] = float(cd_f.group(1))

    return result


# ============================================================================
# Comparison
# ============================================================================

def tolerance_close(a, b, rtol=1e-6, atol=1e-8):
    if a is None or b is None:
        return a == b, f"Python={a}, Stata={b}"
    diff = abs(a - b)
    rel_diff = diff / (abs(b) + 1e-15)
    passed = diff < atol or rel_diff < rtol
    return passed, f"Python={a:.10f}, Stata={b:.10f}, abs_diff={diff:.2e}, rel_diff={rel_diff:.2e}"


def compare_scenario(py_res, st_res, scenario_name):
    lines = []
    lines.append(f"\n## {scenario_name}")
    lines.append("")

    if "error" in py_res or "error" in st_res:
        lines.append(f"**SKIPPED/FAILURE** — Python error: {py_res.get('error', 'None')}, Stata error: {st_res.get('error', 'None')}")
        return "\n".join(lines)

    # Compare coefficients
    lines.append("### Coefficients")
    lines.append("| var | Python beta | Stata beta | beta diff | Python SE | Stata SE | SE diff | stat diff | status |")
    lines.append("|-----|-------------|------------|-----------|-----------|----------|---------|-----------|--------|")

    py_coefs = {c["name"]: c for c in py_res["coefficients"]}
    st_coefs = {c["name"]: c for c in st_res["coefficients"]}

    all_names = set(py_coefs.keys()) | set(st_coefs.keys())
    for name in sorted(all_names, key=lambda x: ['educ', 'exper', 'expersq', 'black', 'south', 'smsa', '_cons'].index(x) if x in ['educ', 'exper', 'expersq', 'black', 'south', 'smsa', '_cons'] else 999):
        py_c = py_coefs.get(name, {})
        st_c = st_coefs.get(name, {})

        py_beta = py_c.get("beta")
        st_beta = st_c.get("beta")
        beta_pass, beta_msg = tolerance_close(py_beta, st_beta)

        py_se = py_c.get("std_err")
        st_se = st_c.get("std_err")
        se_pass, se_msg = tolerance_close(py_se, st_se)

        # Compare t/z stat
        py_stat = py_c.get("t_stat")
        st_stat = st_c.get("t_stat") or st_c.get("z_stat")
        stat_pass, stat_msg = tolerance_close(py_stat, st_stat)

        status = "PASS" if (beta_pass and se_pass and stat_pass) else "FAIL"

        def fmt(val, fmt_spec=".6f"):
            if val is None:
                return "-"
            return f"{val:{fmt_spec}}"

        def diff_fmt(a, b):
            if a is not None and b is not None:
                return f"{abs(a-b):.2e}"
            return "-"

        lines.append(
            f"| {name} | {fmt(py_beta)} | {fmt(st_beta)} | "
            f"{diff_fmt(py_beta, st_beta)} | "
            f"{fmt(py_se)} | {fmt(st_se)} | "
            f"{diff_fmt(py_se, st_se)} | "
            f"{diff_fmt(py_stat, st_stat)} | {status} |"
        )

    # Compare fit stats
    lines.append("\n### Fit Statistics")
    for key in ["nobs", "df_model", "df_resid", "rmse", "r2", "r2_adj"]:
        py_v = py_res.get(key)
        st_v = st_res.get(key)
        if py_v is not None or st_v is not None:
            p, msg = tolerance_close(py_v, st_v)
            status = "PASS" if p else "FAIL"
            lines.append(f"- **{key}**: {msg} → {status}")

    return "\n".join(lines)


# ============================================================================
# Main
# ============================================================================

def main():
    print("=" * 60)
    print("Phase 2 IV Validation — Python vs Stata 17")
    print("=" * 60)

    # Run Python
    py_results = run_python_scenarios()

    # Run Stata
    stata_results = {}
    stata_results["st_ivregress_ols"] = run_stata_scenario("ivregress_ols", STATA_IVREGRESS_OLS_DO)
    stata_results["st_ivregress_robust"] = run_stata_scenario("ivregress_robust", STATA_IVREGRESS_ROBUST_DO)
    stata_results["st_ivregress_cluster_age"] = run_stata_scenario("ivregress_cluster_age", STATA_IVREGRESS_CLUSTER_AGE_DO)
    stata_results["st_ivregress_cluster_south"] = run_stata_scenario("ivregress_cluster_south", STATA_IVREGRESS_CLUSTER_SOUTH_DO)
    stata_results["st_ivregress_first_ols"] = run_stata_scenario("ivregress_first_ols", STATA_IVREGRESS_FIRST_OLS_DO)
    stata_results["st_ivregress_first_robust"] = run_stata_scenario("ivregress_first_robust", STATA_IVREGRESS_FIRST_ROBUST_DO)
    stata_results["st_ivregress_first_cluster"] = run_stata_scenario("ivregress_first_cluster", STATA_IVREGRESS_FIRST_CLUSTER_DO)
    stata_results["st_ivreghdfe_cluster"] = run_stata_scenario("ivreghdfe_cluster", STATA_IVREGHDFE_CLUSTER_DO)
    stata_results["st_ivreghdfe_2way"] = run_stata_scenario("ivreghdfe_2way", STATA_IVREGHDFE_2WAY_DO)

    # Save raw results
    with open(OUTPUT_DIR / "phase2_iv_python_results.json", "w", encoding="utf-8") as f:
        json.dump(py_results, f, indent=2, default=str)
    with open(OUTPUT_DIR / "phase2_iv_stata_results.json", "w", encoding="utf-8") as f:
        json.dump(stata_results, f, indent=2, default=str)

    # Generate report
    report_lines = []
    report_lines.append("# Phase 2 IV/GMM Dual-Run Validation Report")
    report_lines.append("")
    report_lines.append(f"**Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"**Dataset**: Card IV dataset ({len(df)} obs)")
    report_lines.append("")
    report_lines.append("## Known Issues Under Test")
    report_lines.append("- IV-01: ivreghdfe GMM2S cluster VCE main/fallback path inconsistency")
    report_lines.append("- IV-02: fix_psd_reghdfe wrong _cons assumption")
    report_lines.append("- IV-03: ivregress 2sls uses z-statistics everywhere (vce(ols) should be t)")
    report_lines.append("- IV-04: X/Z independent collinearity detection causes column set mismatch")
    report_lines.append("- IV-05: Multi-endogenous weakiv not implemented")
    report_lines.append("")

    report_lines.append(compare_scenario(py_results["py_ivregress_ols"], stata_results["st_ivregress_ols"], "1. ivregress 2sls — vce(ols)"))
    report_lines.append(compare_scenario(py_results["py_ivregress_robust"], stata_results["st_ivregress_robust"], "2. ivregress 2sls — vce(robust)"))
    report_lines.append(compare_scenario(py_results["py_ivregress_cluster_age"], stata_results["st_ivregress_cluster_age"], "3. ivregress 2sls — vce(cluster age)"))
    report_lines.append(compare_scenario(py_results["py_ivregress_cluster_south"], stata_results["st_ivregress_cluster_south"], "4. ivregress 2sls — vce(cluster south)"))
    report_lines.append(compare_scenario(py_results["py_ivreghdfe_cluster"], stata_results["st_ivreghdfe_cluster"], "5. ivreghdfe — absorb(age_group) cluster(age_group)"))
    report_lines.append(compare_scenario(py_results["py_ivreghdfe_2way"], stata_results["st_ivreghdfe_2way"], "6. ivreghdfe — 2-way cluster"))

    report_lines.append("\n## First-Stage F Statistics")
    report_lines.append("See Stata logs for first-stage output parsing.")
    report_lines.append("")
    report_lines.append("## Summary")
    report_lines.append("See detailed tables above. Any FAIL rows indicate deviations > 1e-6 rtol.")
    report_lines.append("")

    report_text = "\n".join(report_lines)
    with open(REPORT_DIR / "VAL-IV.md", "w", encoding="utf-8") as f:
        f.write(report_text)

    print("\n" + "=" * 60)
    print("Validation complete. Report written to:")
    print(f"  {REPORT_DIR / 'VAL-IV.md'}")
    print("Raw results:")
    print(f"  {OUTPUT_DIR / 'phase2_iv_python_results.json'}")
    print(f"  {OUTPUT_DIR / 'phase2_iv_stata_results.json'}")


if __name__ == "__main__":
    main()
