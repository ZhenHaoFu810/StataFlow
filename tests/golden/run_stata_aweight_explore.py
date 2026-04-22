"""
Standalone script to run Stata aweight test and inspect results.
Used to understand aweight semantics before implementation.
"""

import sys
import tempfile
import numpy as np
import pandas as pd
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tests.golden.test_utils import run_stata_ols, parse_stata_log

TEMP_DIR = Path(tempfile.mkdtemp(prefix="stataflow_aweight_explore_"))


def generate_test_data() -> pd.DataFrame:
    """Generate test dataset with known seed."""
    np.random.seed(77777)
    n = 200

    x1 = np.random.normal(0, 1, n)
    x2 = np.random.normal(0, 1, n)
    error = np.random.normal(0, 1, n)

    # True model: y = 3 + 1.5*x1 - 2*x2 + error
    y = 3 + 1.5 * x1 - 2 * x2 + error

    # Non-integer, positive weights
    weights = np.abs(np.random.exponential(scale=2.0, size=n)) + 0.5

    return pd.DataFrame({
        "y": y,
        "x1": x1,
        "x2": x2,
        "weight": weights,
    })


def main():
    data = generate_test_data()
    print("=== Test Data Summary ===")
    print(f"n = {len(data)}")
    print(f"weight: min={data['weight'].min():.4f}, max={data['weight'].max():.4f}, mean={data['weight'].mean():.4f}")
    print(f"sum(weight) = {data['weight'].sum():.4f}")
    print()

    # Run Stata with aweight
    dta_file = TEMP_DIR / "p2_aweight_explore.dta"
    data.to_stata(str(dta_file), write_index=False)

    do_template = '''
clear all
set more off

// Read data
use "$DATA_FILE", clear

// Run regression with analytical weights
regress y x1 x2 [aweight=weight]

// Output precise e() values for parsing
display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_DF_R=" e(df_r)
display "E_R2=" e(r2)
display "E_R2_A=" e(r2_a)
display "E_RMSE=" e(rmse)
display "E_F=" e(F)
display "E_F_P=" e(F_p)
display "E_RSS=" e(rss)
display "E_MSS=" e(mss)

// Show coefficients
matrix list e(b)
matrix list e(V)

display "Stata regress y x1 x2 [aweight=weight] completed successfully"
'''
    do_content = do_template.replace("$DATA_FILE", str(dta_file))

    print("=== Running Stata with aweight ===")
    result = run_stata_ols(do_content)

    print("=== Stata Results ===")
    print(f"nobs     = {result.get('nobs')}")
    print(f"df_model = {result.get('df_model')}")
    print(f"df_resid = {result.get('df_resid')}")
    print(f"r2       = {result.get('r2'):.15f}")
    print(f"r2_adj   = {result.get('r2_adj'):.15f}")
    print(f"rmse     = {result.get('rmse'):.15f}")
    print(f"f_stat   = {result.get('f_stat'):.15f}")
    print(f"rss      = {result.get('rss'):.15f}")
    print(f"mss      = {result.get('mss')}")
    print()
    print("Coefficients:")
    for coef in result.get('coefficients', []):
        print(f"  {coef['name']}: beta={coef['beta']:.15f}, se={coef['std_err']:.15f}")

    # Also run unweighted for comparison
    print("\n=== Running Stata WITHOUT weights (for comparison) ===")
    do_unweighted = '''
clear all
set more off

use "$DATA_FILE", clear

regress y x1 x2

display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_DF_R=" e(df_r)
display "E_R2=" e(r2)
display "E_RMSE=" e(rmse)
display "E_F=" e(F)
display "E_RSS=" e(rss)
'''
    do_unweighted = do_unweighted.replace("$DATA_FILE", str(dta_file))
    result_unweighted = run_stata_ols(do_unweighted)

    print("Unweighted results:")
    print(f"nobs     = {result_unweighted.get('nobs')}")
    print(f"df_model = {result_unweighted.get('df_model')}")
    print(f"df_resid = {result_unweighted.get('df_resid')}")
    print(f"r2       = {result_unweighted.get('r2'):.15f}")
    print(f"rmse     = {result_unweighted.get('rmse'):.15f}")
    print(f"f_stat   = {result_unweighted.get('f_stat'):.15f}")
    print(f"rss      = {result_unweighted.get('rss'):.15f}")
    print("Coefficients:")
    for coef in result_unweighted.get('coefficients', []):
        print(f"  {coef['name']}: beta={coef['beta']:.15f}, se={coef['std_err']:.15f}")


if __name__ == "__main__":
    main()
