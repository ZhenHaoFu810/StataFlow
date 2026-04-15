"""
Stata aweight deep dive - understand the exact normalization.
"""

import sys
import tempfile
import numpy as np
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tests.golden.test_utils import run_stata_ols

TEMP_DIR = Path(tempfile.mkdtemp(prefix="statapy_aweight_deep2_"))


def generate_test_data() -> pd.DataFrame:
    np.random.seed(77777)
    n = 200
    x1 = np.random.normal(0, 1, n)
    x2 = np.random.normal(0, 1, n)
    error = np.random.normal(0, 1, n)
    y = 3 + 1.5 * x1 - 2 * x2 + error
    weights = np.abs(np.random.exponential(scale=2.0, size=n)) + 0.5
    return pd.DataFrame({"y": y, "x1": x1, "x2": x2, "weight": weights})


def main():
    data = generate_test_data()
    w = data["weight"].values
    n = len(data)
    sum_w = np.sum(w)

    dta_file = TEMP_DIR / "p2_aweight_deep2.dta"
    data.to_stata(str(dta_file), write_index=False)

    # Run Stata and get FULL output
    do_content = '''
clear all
set more off
use "$DATA_FILE", clear
regress y x1 x2 [aweight=weight]

display "E_N=" e(N)
display "E_N_subp=" e(N_subp)
display "E_DF_M=" e(df_m)
display "E_DF_R=" e(df_r)
display "E_R2=" e(r2)
display "E_R2_A=" e(r2_a)
display "E_RMSE=" e(rmse)
display "E_F=" e(F)
display "E_RSS=" e(rss)
display "E_MSS=" e(mss)
display "E_rss_a=" e(rss_a)  // alternative RSS?

// Also check what predict gives
predict double e, resid
gen double e2 = e^2
gen double we2 = weight * e^2

sum e2
sum we2

display "sum(e^2) = " r(sum)
display "sum(w*e^2) = " 
'''.replace("$DATA_FILE", str(dta_file))

    from tests.golden.test_utils import StataRunner
    runner = StataRunner()
    result = runner.run_do_file(do_content, output_dir=str(TEMP_DIR))
    
    # Just print the relevant parts
    print("=== Key Stata values ===")
    log = result.output_content
    
    import re
    for pattern_name, pattern in [
        ('E_N=', r'E_N=([\d.]+)'),
        ('E_N_subp=', r'E_N_subp=([\d.]+)'),
        ('E_DF_M=', r'E_DF_M=([\d.]+)'),
        ('E_DF_R=', r'E_DF_R=([\d.]+)'),
        ('E_R2=', r'E_R2=([\d.]+)'),
        ('E_RMSE=', r'E_RMSE=([\d.]+)'),
        ('E_F=', r'E_F=([\d.]+)'),
        ('E_RSS=', r'E_RSS=([\d.]+)'),
        ('E_MSS=', r'E_MSS=([\d.]+)'),
        ('sum(e^2)', r'sum\(e\^2\)\s*=\s*([\d.]+)'),
        ('sum(w*e^2)', r'sum\(w\*e\^2\)\s*=\s*([\d.]+)'),
    ]:
        m = re.search(pattern, log)
        if m:
            val = m.group(1)
            if val.startswith('.'):
                val = '0' + val
            print(f"  {pattern_name} {val}")
    
    # Also print the sum output
    for line in log.split('\n'):
        if 'Variable' in line or 'Obs' in line or 'Mean' in line or 'sum(e' in line.lower() or 'sum(w' in line.lower():
            print(f"  {line}")

    # Python calculations with normalized weights
    print(f"\n=== Python calculations ===")
    print(f"  N = {n}")
    print(f"  sum(w) = {sum_w:.15f}")
    print(f"  mean(w) = {np.mean(w):.15f}")
    
    # Normalized weights: w* = w * N / sum(w), so sum(w*) = N
    w_norm = w * n / sum_w
    
    y = data["y"].values
    X = np.column_stack([data["x1"].values, data["x2"].values, np.ones(n)])
    k = 3
    
    # WLS with normalized weights
    sqrt_wn = np.sqrt(w_norm)
    X_wn = X * sqrt_wn[:, np.newaxis]
    y_wn = y * sqrt_wn
    beta = np.linalg.solve(X_wn.T @ X_wn, X_wn.T @ y_wn)
    residuals = y - X @ beta
    
    unweighted_rss = np.sum(residuals**2)
    weighted_rss = np.sum(w * residuals**2)
    weighted_rss_norm = np.sum(w_norm * residuals**2)
    
    print(f"\n  With ORIGINAL weights:")
    print(f"    sum(w*e^2) = {weighted_rss:.15f}")
    print(f"    sum(e^2) = {unweighted_rss:.15f}")
    
    print(f"\n  With NORMALIZED weights (sum=N):")
    print(f"    sum(w_norm*e^2) = {weighted_rss_norm:.15f}")
    print(f"    sum(w_norm*e^2)/(N-k) = {weighted_rss_norm/(n-k):.15f}")
    print(f"    RMSE = {np.sqrt(weighted_rss_norm/(n-k)):.15f}")
    
    # From Stata log: RMSE = .98924519
    # Residual MS = .978606052
    # So RMSE^2 = 0.9786... 
    stata_rmse = 0.98924519
    print(f"\n  Stata RMSE = {stata_rmse}")
    print(f"  Stata RMSE^2 = {stata_rmse**2:.15f}")
    print(f"  Matches sum(w_norm*e^2)/(N-k)? diff = {abs(stata_rmse**2 - weighted_rss_norm/(n-k)):.2e}")
    
    # Check ANOVA table values
    # Model: 903.513404, Residual: 192.785392, Total: 1096.2988
    print(f"\n  Stata ANOVA (from log):")
    print(f"    Model SS  = 903.513404")
    print(f"    Resid SS  = 192.785392")  
    print(f"    Total SS  = 1096.2988")
    print(f"    Model + Residual = {903.513404 + 192.785392:.4f}")
    
    # What are these?
    # If using normalized weights:
    y_bar = np.mean(y)
    weighted_tss_norm = np.sum(w_norm * (y - y_bar)**2)
    weighted_mss_norm = weighted_tss_norm - weighted_rss_norm
    
    print(f"\n  Python with normalized weights:")
    print(f"    Weighted TSS = {weighted_tss_norm:.15f}")
    print(f"    Weighted RSS = {weighted_rss_norm:.15f}")
    print(f"    Weighted MSS = {weighted_mss_norm:.15f}")


if __name__ == "__main__":
    main()
