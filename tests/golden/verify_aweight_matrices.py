"""
Deep investigation of Stata aweight - extract e(b) and e(V) matrices directly.
"""

import sys
import tempfile
import numpy as np
import pandas as pd
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tests.golden.test_utils import run_stata_ols

TEMP_DIR = Path(tempfile.mkdtemp(prefix="statapy_aweight_deep_"))


def generate_test_data() -> pd.DataFrame:
    np.random.seed(77777)
    n = 200
    x1 = np.random.normal(0, 1, n)
    x2 = np.random.normal(0, 1, n)
    error = np.random.normal(0, 1, n)
    y = 3 + 1.5 * x1 - 2 * x2 + error
    weights = np.abs(np.random.exponential(scale=2.0, size=n)) + 0.5
    return pd.DataFrame({"y": y, "x1": x1, "x2": x2, "weight": weights})


def parse_matrix(text, matrix_name):
    """Parse Stata matrix output."""
    pattern = rf'{matrix_name}\[.*?\]'
    match = re.search(pattern, text)
    if not match:
        return None
    
    # Extract rows after the matrix header
    lines = text[match.end():].split('\n')
    rows = []
    for line in lines:
        # Match lines with numbers
        nums = re.findall(r'[-+]?\d*\.\d+|\d+', line)
        if nums:
            rows.append([float(x) for x in nums])
        elif rows and line.strip() == '':
            break
    
    if rows:
        return np.array(rows)
    return None


def main():
    data = generate_test_data()
    w = data["weight"].values
    n = len(data)

    dta_file = TEMP_DIR / "p2_aweight_deep.dta"
    data.to_stata(str(dta_file), write_index=False)

    # Get FULL Stata output including matrices
    do_content = '''
clear all
set more off
use "$DATA_FILE", clear
regress y x1 x2 [aweight=weight]

display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_DF_R=" e(df_r)
display "E_R2=" e(r2)
display "E_R2_A=" e(r2_a)
display "E_RMSE=" e(rmse)
display "E_F=" e(F)
display "E_RSS=" e(rss)
display "E_MSS=" e(mss)

// Show matrices
matrix list e(b)
matrix list e(V)
'''.replace("$DATA_FILE", str(dta_file))

    from tests.golden.test_utils import StataRunner
    runner = StataRunner()
    result = runner.run_do_file(do_content, output_dir=str(TEMP_DIR))

    print("=== FULL Stata Log ===")
    print(result.output_content)
    
    # Parse matrices
    e_b = parse_matrix(result.output_content, 'e(b)')
    e_V = parse_matrix(result.output_content, 'e(V)')
    
    print(f"\n=== Parsed Results ===")
    print(f"e(b) = {e_b}")
    print(f"e(V) = \n{e_V}")
    
    # Now let's understand the exact formula
    # Stata aweight: V = sigma2 * (X'WX)^{-1}
    # where sigma2 = sum(w*e^2) / (N - k) normalized somehow
    
    y = data["y"].values
    X_raw = np.column_stack([data["x1"].values, data["x2"].values, np.ones(n)])
    k = X_raw.shape[1]
    
    sqrt_w = np.sqrt(w)
    X_w = X_raw * sqrt_w[:, np.newaxis]
    y_w = y * sqrt_w
    XtWX = X_w.T @ X_w
    beta_wls = np.linalg.solve(XtWX, X_w.T @ y_w)
    residuals = y - X_raw @ beta_wls
    
    # e(V) from Stata
    if e_V is not None and e_V.shape[0] >= k:
        # e(V) is (k+1)x(k+1) with constant last
        # Extract top-left kxk
        stata_V = e_V[:k, :k]
        print(f"\n=== Stata e(V) (top {k}x{k}) ===")
        print(stata_V)
        
        # Try: sigma2 = e(rss) / e(N_subp) 
        # Or: sigma2 such that V = sigma2 * (X'WX)^{-1}
        XtWX_inv = np.linalg.inv(XtWX)
        implied_sigma2 = np.zeros(k)
        for i in range(k):
            implied_sigma2[i] = stata_V[i, i] / XtWX_inv[i, i]
        print(f"\nImplied sigma2 from diagonal: {implied_sigma2}")
        
        # Try different normalizations
        weighted_rss = np.sum(w * residuals**2)
        sum_w = np.sum(w)
        
        print(f"\n=== Possible sigma2 values ===")
        print(f"  sum(w*e^2) = {weighted_rss:.15f}")
        print(f"  sum(w) = {sum_w:.15f}")
        print(f"  N = {n}")
        print(f"  k = {k}")
        print(f"  sum(w*e^2) / (N-k) = {weighted_rss / (n - k):.15f}")
        print(f"  sum(w*e^2) / (sum(w)-k) = {weighted_rss / (sum_w - k):.15f}")
        print(f"  sum(w*e^2) / sum(w) = {weighted_rss / sum_w:.15f}")
        
        # What sigma2 reproduces Stata V exactly?
        # V_stata = sigma2 * (X'WX)^{-1}
        # sigma2 = V_stata / (X'WX)^{-1} (element-wise for diagonal)
        target_sigma2 = implied_sigma2[0]
        print(f"\n  Target sigma2 (from V[0,0]): {target_sigma2:.15f}")
        
        # Check: is it sum(w*e^2) / something?
        ratio = weighted_rss / target_sigma2
        print(f"  sum(w*e^2) / target_sigma2 = {ratio:.15f}")
        print(f"  This should be: N-k={n-k}, sum(w)-k={sum_w-k}, or sum(w)={sum_w}")


if __name__ == "__main__":
    main()
