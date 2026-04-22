"""
Investigate Stata aweight RMSE normalization.
"""

import sys
import tempfile
import numpy as np
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tests.golden.test_utils import run_stata_ols

TEMP_DIR = Path(tempfile.mkdtemp(prefix="stataflow_aweight_rmse_"))


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

    dta_file = TEMP_DIR / "p2_aweight_rmse.dta"
    data.to_stata(str(dta_file), write_index=False)

    # Get full Stata output
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
display "E_rank=" e(rank)

// Get the underlying unweighted RSS
// e(rss) in weighted regression is sum(w*e^2)
// Let's check what predict gives us
predict double resid, resid
predict double yhat, xb
gen double resid_sq = resid^2
gen double w_resid_sq = weight * resid_sq

sum resid_sq
sum w_resid_sq

display "Sum of e_i^2 = " r(sum)
display "Sum of w*e_i^2 = " r(sum)

// Check unweighted RSS
sum resid_sq, detail
display "Unweighted RSS (sum of e^2) = " r(sum)
'''.replace("$DATA_FILE", str(dta_file))

    stata_result = run_stata_ols(do_content)

    print("=== Stata Results ===")
    for key in ['nobs', 'df_model', 'df_resid', 'r2', 'r2_adj', 'rmse', 'f_stat', 'rss', 'mss', 'n_subp', 'rank']:
        val = stata_result.get(key)
        if val is not None:
            print(f"  {key} = {val:.15f}")

    print(f"\nCoefficients:")
    for coef in stata_result.get('coefficients', []):
        print(f"  {coef['name']}: beta={coef['beta']:.15f}, se={coef['std_err']:.15f}")

    # Python calculations
    y = data["y"].values
    X_raw = np.column_stack([data["x1"].values, data["x2"].values, np.ones(n)])
    k = X_raw.shape[1]

    sqrt_w = np.sqrt(w)
    X_w = X_raw * sqrt_w[:, np.newaxis]
    y_w = y * sqrt_w
    beta_wls = np.linalg.solve(X_w.T @ X_w, X_w.T @ y_w)
    residuals = y - X_raw @ beta_wls

    # Different possible RMSE definitions
    weighted_rss = np.sum(w * residuals**2)  # Stata's e(rss)
    unweighted_rss = np.sum(residuals**2)
    sum_w = np.sum(w)

    print(f"\n=== Python RSS calculations ===")
    print(f"  sum(w*e^2) [Stata e(rss)]  = {weighted_rss:.15f}")
    print(f"  sum(e^2) [unweighted RSS]   = {unweighted_rss:.15f}")
    print(f"  sum(w)                      = {sum_w:.15f}")

    # Different possible RMSE formulas
    print(f"\n=== Possible RMSE formulas ===")
    rmse_candidates = {
        "sqrt(sum(w*e^2)/(N-k))": np.sqrt(weighted_rss / (n - k)),
        "sqrt(sum(w*e^2)/(sum(w)-k))": np.sqrt(weighted_rss / (sum_w - k)),
        "sqrt(sum(e^2)/(N-k))": np.sqrt(unweighted_rss / (n - k)),
        "sqrt(sum(w*e^2)/sum(w))": np.sqrt(weighted_rss / sum_w),
        "sqrt(sum(e^2)/N)": np.sqrt(unweighted_rss / n),
        "sqrt(sum(w*e^2)/(N-k)) / mean(w)": np.sqrt(weighted_rss / (n - k)) / np.mean(w),
    }

    stata_rmse = stata_result.get('rmse')
    print(f"  Stata RMSE = {stata_rmse:.15f}")
    for formula, value in rmse_candidates.items():
        diff = abs(value - stata_rmse)
        match = "MATCH!" if diff < 1e-6 else ""
        print(f"  {formula:45s} = {value:.15f}  (diff={diff:.2e}) {match}")

    # Let's also check: maybe Stata reports unweighted RMSE
    # or uses normalized weights
    w_normalized = w * n / sum_w  # normalize to sum to N
    weighted_rss_norm = np.sum(w_normalized * residuals**2)
    rmse_norm = np.sqrt(weighted_rss_norm / (n - k))
    print(f"\n  With normalized weights (sum=w*N):")
    print(f"    sum(w_norm*e^2)/(N-k) = {weighted_rss_norm / (n - k):.15f}")
    print(f"    rmse = {rmse_norm:.15f}")


if __name__ == "__main__":
    main()
