"""Phase 2 Panel/FE/reghdfe dual-run validation - final run."""
from __future__ import annotations

import os
import sys
import json
import traceback
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from stataflow.compat.stata.hdfe import reghdfe
from stataflow.compat.stata.linear import areg, xtreg_fe
from stataflow.estimators.absorbing_ols import AbsorbingOLS

DATA_PATH = "D:/OneDrive - SAIF/PhD3/StataFlow/research/data/public/panel/grunfeld.csv"
OUTPUT_DIR = "D:/OneDrive - SAIF/PhD3/StataFlow/stata/output/phase2"

def load_data():
    df = pd.read_csv(DATA_PATH)
    for col in ['firm', 'year', 'inv', 'value', 'capital']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

def extract_result(result):
    """Extract comparable fields from ResultSchema."""
    coefs = {}
    for c in result.coefficients:
        coefs[c.name] = {
            "beta": c.beta,
            "se": c.std_err,
            "t": c.t_stat,
            "p": c.p_value,
        }
    return {
        "status": "success",
        "n": result.sample.nobs,
        "df_model": result.fit.df_model,
        "df_resid": result.fit.df_resid,
        "df_a": result.fit.df_a,
        "r2": result.fit.r2,
        "r2_adj": result.fit.r2_adj,
        "rmse": result.fit.rmse,
        "f_stat": result.fit.f_stat,
        "f_pvalue": result.fit.f_pvalue,
        "coefs": coefs,
        "has_fixed_effects": hasattr(result, 'fixed_effects') and result.fixed_effects is not None,
        "fixed_effects_keys": list(result.fixed_effects.keys()) if (hasattr(result, 'fixed_effects') and result.fixed_effects is not None) else [],
    }

def run_case(name, py_fn):
    print(f"\n{'='*60}")
    print(f"CASE: {name}")
    print(f"{'='*60}")
    try:
        result = py_fn()
        info = extract_result(result)
        print("STATUS: SUCCESS")
        print(json.dumps(info, indent=2))
        return info
    except Exception as e:
        print(f"STATUS: ERROR ({type(e).__name__})")
        print(str(e))
        tb = traceback.format_exc()
        print(tb)
        return {
            "status": "error",
            "error_type": type(e).__name__,
            "error_msg": str(e),
            "traceback": tb,
        }

def main():
    df = load_data()
    results = {}

    results["1_reghdfe_basic"] = run_case("1. reghdfe - basic OLS", lambda: reghdfe(df, y='inv', x=['value', 'capital'], absorb='firm'))
    results["2_reghdfe_robust"] = run_case("2. reghdfe - robust VCE", lambda: reghdfe(df, y='inv', x=['value', 'capital'], absorb='firm', vce='robust'))
    results["3_reghdfe_cluster_firm"] = run_case("3. reghdfe - cluster VCE (firm)", lambda: reghdfe(df, y='inv', x=['value', 'capital'], absorb='firm', vce='cluster', cluster='firm'))
    results["3b_reghdfe_cluster_year"] = run_case("3b. reghdfe - cluster VCE (year)", lambda: reghdfe(df, y='inv', x=['value', 'capital'], absorb='firm', vce='cluster', cluster='year'))
    results["4_reghdfe_2way"] = run_case("4. reghdfe - 2-way FE", lambda: reghdfe(df, y='inv', x=['value', 'capital'], absorb=['firm', 'year']))
    results["5_reghdfe_slopes"] = run_case("5. reghdfe - slopes", lambda: reghdfe(df, y='inv', x=['value', 'capital'], absorb='firm##c.year'))
    results["6_areg_basic"] = run_case("6. areg - basic", lambda: areg(df, y='inv', x=['value', 'capital'], absorb='firm'))
    results["7_xtreg_fe_basic"] = run_case("7. xtreg_fe - basic", lambda: xtreg_fe(df, y='inv', x=['value', 'capital'], fe='firm'))
    results["8_map_forced"] = run_case("8. MAP path forced", lambda: AbsorbingOLS(data=df, y='inv', x=['value', 'capital'], absorb='firm', technique='map').fit(vce='ols'))
    results["9_reghdfe_savefe"] = run_case("9. reghdfe - savefe", lambda: reghdfe(df, y='inv', x=['value', 'capital'], absorb='firm', savefe=True))

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(os.path.join(OUTPUT_DIR, "python_results_final.json"), "w") as f:
        json.dump(results, f, indent=2)
    print("\n\nResults saved to", os.path.join(OUTPUT_DIR, "python_results_final.json"))

if __name__ == "__main__":
    main()
