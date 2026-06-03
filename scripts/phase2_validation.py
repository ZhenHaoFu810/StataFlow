"""Phase 2 Panel/FE/reghdfe dual-run validation script."""
from __future__ import annotations

import os
import sys
import traceback
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from stataflow.compat.stata.hdfe import reghdfe
from stataflow.compat.stata.linear import areg, xtreg_fe
from stataflow.estimators.absorbing_ols import AbsorbingOLS

DATA_PATH = "D:/OneDrive - SAIF/PhD3/StataFlow/research/data/public/panel/grunfeld.csv"
OUTPUT_DIR = "D:/OneDrive - SAIF/PhD3/StataFlow/stata/output/phase2"

def load_data():
    df = pd.read_csv(DATA_PATH)
    # ensure numeric types
    for col in ['firm', 'year', 'inv', 'value', 'capital']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

def fmt_coef(result):
    lines = []
    for c in result.coefficients:
        lines.append(f"  {c.name:15s}  beta={c.beta:12.6f}  se={c.std_err:12.6f}  t={c.t_stat:10.4f}  p={c.p_value:.4f}")
    return "\n".join(lines)

def fmt_fit(result):
    f = result.fit
    return (f"  N={result.sample.nobs}  df_m={f.df_model}  df_r={f.df_resid}  df_a={f.df_a}\n"
            f"  R2={f.r2:.6f}  R2_adj={f.r2_adj:.6f}  RMSE={f.rmse:.6f}\n"
            f"  F={f.f_stat}  F_p={f.f_pvalue}")

def run_case(name, py_fn, expected_error=None):
    print(f"\n{'='*60}")
    print(f"CASE: {name}")
    print(f"{'='*60}")
    try:
        result = py_fn()
        print("STATUS: SUCCESS")
        print(fmt_fit(result))
        print(fmt_coef(result))
        if expected_error:
            print("WARNING: Expected error did not occur!")
        # Check for fixed_effects
        if hasattr(result, 'fixed_effects') and result.fixed_effects is not None:
            print(f"  fixed_effects present: {list(result.fixed_effects.keys()) if isinstance(result.fixed_effects, dict) else type(result.fixed_effects)}")
        return {"status": "success", "result": result}
    except Exception as e:
        print(f"STATUS: ERROR ({type(e).__name__})")
        print(str(e))
        if expected_error:
            print("(This error was expected)")
        traceback.print_exc()
        return {"status": "error", "error": e, "traceback": traceback.format_exc()}

def main():
    df = load_data()
    results = {}

    # 1. reghdfe - basic OLS
    results["reghdfe_basic"] = run_case(
        "1. reghdfe - basic OLS",
        lambda: reghdfe(df, y='inv', x=['value', 'capital'], absorb='firm')
    )

    # 2. reghdfe - robust VCE
    results["reghdfe_robust"] = run_case(
        "2. reghdfe - robust VCE",
        lambda: reghdfe(df, y='inv', x=['value', 'capital'], absorb='firm', vce='robust')
    )

    # 3. reghdfe - cluster VCE (firm)
    results["reghdfe_cluster_firm"] = run_case(
        "3. reghdfe - cluster VCE (firm)",
        lambda: reghdfe(df, y='inv', x=['value', 'capital'], absorb='firm', vce='cluster', cluster='firm')
    )

    # 3b. reghdfe - cluster VCE (year)
    results["reghdfe_cluster_year"] = run_case(
        "3b. reghdfe - cluster VCE (year)",
        lambda: reghdfe(df, y='inv', x=['value', 'capital'], absorb='firm', vce='cluster', cluster='year')
    )

    # 4. reghdfe - 2-way FE
    results["reghdfe_2way"] = run_case(
        "4. reghdfe - 2-way FE",
        lambda: reghdfe(df, y='inv', x=['value', 'capital'], absorb=['firm', 'year'])
    )

    # 5. reghdfe - slopes
    results["reghdfe_slopes"] = run_case(
        "5. reghdfe - slopes (firm##c.year)",
        lambda: reghdfe(df, y='inv', x=['value', 'capital'], absorb='firm##c.year')
    )

    # 6. areg - basic
    results["areg_basic"] = run_case(
        "6. areg - basic",
        lambda: areg(df, y='inv', x=['value', 'capital'], absorb='firm')
    )

    # 7. xtreg_fe - basic
    results["xtreg_fe_basic"] = run_case(
        "7. xtreg_fe - basic",
        lambda: xtreg_fe(df, y='inv', x=['value', 'capital'], fe='firm')
    )

    # 8. MAP path forced (PANEL-01)
    results["map_forced"] = run_case(
        "8. MAP path forced (PANEL-01)",
        lambda: AbsorbingOLS(data=df, y='inv', x=['value', 'capital'], absorb='firm', technique='map').fit(vce='ols'),
        expected_error=False  # We want to see if it crashes
    )

    # 9. savefe
    results["reghdfe_savefe"] = run_case(
        "9. reghdfe - savefe",
        lambda: reghdfe(df, y='inv', x=['value', 'capital'], absorb='firm', savefe=True)
    )

    # Save summary to file
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(os.path.join(OUTPUT_DIR, "python_validation_summary.txt"), "w") as f:
        for k, v in results.items():
            f.write(f"\n{'='*60}\nCASE: {k}\n{'='*60}\n")
            if v["status"] == "success":
                f.write("STATUS: SUCCESS\n")
                r = v["result"]
                f.write(fmt_fit(r) + "\n")
                f.write(fmt_coef(r) + "\n")
                if hasattr(r, 'fixed_effects') and r.fixed_effects is not None:
                    f.write(f"fixed_effects: {list(r.fixed_effects.keys()) if isinstance(r.fixed_effects, dict) else type(r.fixed_effects)}\n")
            else:
                f.write(f"STATUS: ERROR ({type(v['error']).__name__})\n")
                f.write(str(v['error']) + "\n")
                f.write(v.get('traceback', '') + "\n")

    print("\n\nSummary saved to", os.path.join(OUTPUT_DIR, "python_validation_summary.txt"))

if __name__ == "__main__":
    main()
