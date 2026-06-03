"""Run Wave 12 performance benchmarks: Stata vs Python LSDV."""
import json
import os
import sys
import time
import traceback

import numpy as np
import pandas as pd

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.stataflow.stata_runner.runner import StataRunner
from stataflow.compat.stata import reghdfe

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)


def build_stata_do(dataset_path, fe_vars, cluster_var, out_prefix):
    """Build Stata do-file content for a single benchmark."""
    # Normalize path for Stata (backslashes)
    stata_path = dataset_path.replace("/", "\\")
    result_file = os.path.join(RESULTS_DIR, f"stata_{out_prefix}_results.txt").replace("/", "\\")
    log_file = os.path.join(RESULTS_DIR, f"stata_{out_prefix}_log.txt").replace("/", "\\")

    do = f"""
clear all
set more off

use "{stata_path}", clear

timer clear
timer on 1
reghdfe y x1 x2, absorb({fe_vars}) vce(cluster {cluster_var})
timer off 1

// Save timing
log using "{log_file}", text replace
timer list 1
log close

// Save coefficients and SEs
matrix b = e(b)
matrix V = e(V)
local r2 = e(r2)
local N = e(N)
local rank = e(rank)
local df_r = e(df_r)

file open out using "{result_file}", write replace text
file write out "coef_x1:" (_b[x1]) _n
file write out "coef_x2:" (_b[x2]) _n
file write out "se_x1:" (_se[x1]) _n
file write out "se_x2:" (_se[x2]) _n
file write out "r2:" (`r2') _n
file write out "N:" (`N') _n
file write out "rank:" (`rank') _n
file write out "df_r:" (`df_r') _n
file close out
"""
    return do


def run_stata_benchmark(name, dataset_path, fe_vars, cluster_var):
    """Run a single Stata benchmark."""
    print(f"\n=== Stata benchmark: {name} ===")
    do_content = build_stata_do(dataset_path, fe_vars, cluster_var, name)

    runner = StataRunner()
    start = time.time()
    result = runner.run_do_file(do_content, timeout=600)
    elapsed = time.time() - start

    # Parse timing from log
    timer_time = None
    if result.output_content:
        for line in result.output_content.splitlines():
            if line.strip().startswith("1:"):
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        timer_time = float(parts[1])
                    except ValueError:
                        pass

    # Parse results file
    result_file = os.path.join(RESULTS_DIR, f"stata_{name}_results.txt")
    results = {}
    if os.path.exists(result_file):
        with open(result_file, "r") as f:
            for line in f:
                if ":" in line:
                    key, val = line.strip().split(":", 1)
                    try:
                        results[key] = float(val)
                    except ValueError:
                        results[key] = val

    results["total_time"] = elapsed
    results["timer_time"] = timer_time
    results["exit_code"] = result.exit_code

    print(f"  Total time: {elapsed:.2f}s")
    print(f"  Timer time: {timer_time:.2f}s" if timer_time else "  Timer time: N/A")
    print(f"  Coef x1: {results.get('coef_x1')}")
    print(f"  SE x1: {results.get('se_x1')}")
    return results


def run_python_benchmark(name, dataset_path, absorb, cluster):
    """Run a single Python LSDV benchmark."""
    print(f"\n=== Python benchmark: {name} ===")
    df = pd.read_stata(dataset_path)

    # Drop missings like Stata does
    absorb_vars = [v.strip() for v in absorb.replace(",", " ").split()]
    df = df.dropna(subset=["y", "x1", "x2"] + absorb_vars)

    start = time.time()
    try:
        result = reghdfe(
            df,
            y="y",
            x=["x1", "x2"],
            absorb=absorb,
            vce="cluster",
            cluster=cluster,
        )
        elapsed = time.time() - start

        # Extract results
        coefs = {c.name: c.value for c in result.coefficients}
        ses = {c.name: c.std_error for c in result.coefficients}

        results = {
            "coef_x1": coefs.get("x1"),
            "coef_x2": coefs.get("x2"),
            "se_x1": ses.get("x1"),
            "se_x2": ses.get("x2"),
            "r2": getattr(result, "r2", None),
            "N": getattr(result, "nobs", None),
            "total_time": elapsed,
            "success": True,
        }
        print(f"  Total time: {elapsed:.2f}s")
        print(f"  Coef x1: {results['coef_x1']}")
        print(f"  SE x1: {results['se_x1']}")
    except Exception as e:
        elapsed = time.time() - start
        results = {
            "total_time": elapsed,
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
        }
        print(f"  FAILED after {elapsed:.2f}s: {type(e).__name__}: {e}")
        traceback.print_exc()

    return results


def compare_results(stata_res, py_res):
    """Compare Stata and Python results."""
    comparison = {}
    for key in ["coef_x1", "coef_x2", "se_x1", "se_x2"]:
        s = stata_res.get(key)
        p = py_res.get(key)
        if s is not None and p is not None and s != 0:
            rel_diff = abs(s - p) / abs(s)
            comparison[key] = {"stata": s, "python": p, "rel_diff": rel_diff}
        else:
            comparison[key] = {"stata": s, "python": p, "rel_diff": None}
    return comparison


def main():
    benchmarks = [
        {
            "name": "a_single_fe",
            "path": os.path.join(DATA_DIR, "benchmark_a_single_fe.dta"),
            "fe_vars": "firm_id",
            "cluster": "firm_id",
            "absorb": "firm_id",
        },
        {
            "name": "b_two_way_fe",
            "path": os.path.join(DATA_DIR, "benchmark_b_two_way_fe.dta"),
            "fe_vars": "firm_id year_id",
            "cluster": "firm_id",
            "absorb": "firm_id year_id",
        },
        {
            "name": "c_unbalanced_cluster",
            "path": os.path.join(DATA_DIR, "benchmark_c_unbalanced_cluster.dta"),
            "fe_vars": "worker_id firm_id",
            "cluster": "cluster_id",
            "absorb": "worker_id firm_id",
        },
    ]

    all_results = {}

    for bench in benchmarks:
        name = bench["name"]
        print("\n" + "=" * 60)
        print(f"Benchmark: {name}")
        print("=" * 60)

        # Stata
        stata_res = run_stata_benchmark(
            name, bench["path"], bench["fe_vars"], bench["cluster"]
        )

        # Python
        py_res = run_python_benchmark(
            name, bench["path"], bench["absorb"], bench["cluster"]
        )

        # Compare
        comparison = compare_results(stata_res, py_res)

        all_results[name] = {
            "stata": stata_res,
            "python": py_res,
            "comparison": comparison,
        }

        # Save per-benchmark results
        with open(os.path.join(RESULTS_DIR, f"{name}_results.json"), "w") as f:
            json.dump(all_results[name], f, indent=2, default=str)

    # Save combined results
    with open(os.path.join(RESULTS_DIR, "all_results.json"), "w") as f:
        json.dump(all_results, f, indent=2, default=str)

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for name, res in all_results.items():
        s_time = res["stata"].get("timer_time") or res["stata"].get("total_time")
        p_time = res["python"].get("total_time")
        p_ok = res["python"].get("success", False)
        print(f"\n{name}:")
        print(f"  Stata time: {s_time:.2f}s")
        print(f"  Python time: {p_time:.2f}s" if p_time else "  Python time: N/A")
        print(f"  Python success: {p_ok}")
        for key, comp in res["comparison"].items():
            rd = comp.get("rel_diff")
            if rd is not None:
                print(f"  {key} rel_diff: {rd:.6f}")


if __name__ == "__main__":
    main()
