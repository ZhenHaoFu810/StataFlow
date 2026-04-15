"""
Final verification: Stata aweight e(rss) is UNWEIGHTED sum of e^2.
"""

import sys
import tempfile
import numpy as np
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tests.golden.test_utils import run_stata_ols

TEMP_DIR = Path(tempfile.mkdtemp(prefix="statapy_aweight_final_"))


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

    dta_file = TEMP_DIR / "p2_aweight_final.dta"
    data.to_stata(str(dta_file), write_index=False)

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
'''.replace("$DATA_FILE", str(dta_file))

    stata = run_stata_ols(do_content)

    # Python WLS
    y = data["y"].values
    X = np.column_stack([data["x1"].values, data["x2"].values, np.ones(n)])
    k = 3

    sqrt_w = np.sqrt(w)
    X_w = X * sqrt_w[:, np.newaxis]
    y_w = y * sqrt_w
    beta = np.linalg.solve(X_w.T @ X_w, X_w.T @ y_w)
    residuals = y - X @ beta

    # Key insight: Stata aweight reports UNWEIGHTED statistics for RSS/MSS/R2
    unweighted_rss = np.sum(residuals**2)
    unweighted_mss = np.sum((X @ beta - np.mean(y))**2)  # around mean for R2
    unweighted_tss = np.sum((y - np.mean(y))**2)

    print("=== Stata vs Python Comparison ===")
    print(f"Stata e(rss) = {stata['rss']:.15f}")
    print(f"Python sum(e^2) = {unweighted_rss:.15f}")
    print(f"Diff = {abs(stata['rss'] - unweighted_rss):.2e}")
    print()
    print(f"Stata e(mss) = {stata.get('mss'):.15f}")
    print(f"Python unweighted MSS = {unweighted_mss:.15f}")
    print()
    print(f"Stata R2 = {stata['r2']:.15f}")
    print(f"Python unweighted R2 = {1 - unweighted_rss/unweighted_tss:.15f}")
    print()
    print(f"Stata RMSE = {stata['rmse']:.15f}")
    print(f"Python sqrt(sum(e^2)/(N-k)) = {np.sqrt(unweighted_rss/(n-k)):.15f}")
    print()
    print(f"Stata F = {stata['f_stat']:.15f}")
    f_python = (unweighted_mss/(k-1)) / (unweighted_rss/(n-k))
    print(f"Python F (unweighted) = {f_python:.15f}")

    # Now verify covariance matrix
    # Stata aweight: V = (sum(w*e^2)/(N-k)) * (X'WX)^{-1}
    weighted_rss = np.sum(w * residuals**2)
    sigma2 = weighted_rss / (n - k)
    cov = sigma2 * np.linalg.inv(X_w.T @ X_w)
    se = np.sqrt(np.diag(cov))

    print(f"\n=== Coefficient SE comparison ===")
    print(f"Stata coefficients from log:")
    print(f"  x1: se=0.0776809")
    print(f"  x2: se=0.0721680")
    print(f"  _cons: se=0.0701017")
    print(f"\nPython aweight SE:")
    print(f"  x1: se={se[0]:.15f}")
    print(f"  x2: se={se[1]:.15f}")
    print(f"  _cons: se={se[2]:.15f}")

    print(f"\n=== Summary of Stata aweight semantics ===")
    print(f"Point estimates: WLS beta = (X'WX)^(-1) X'Wy")
    print(f"Covariance: V = sigma2 * (X'WX)^(-1)")
    print(f"  where sigma2 = sum(w*e^2) / (N - k)")
    print(f"Reported statistics (RSS, MSS, R2, RMSE, F):")
    print(f"  Use UNWEIGHTED quantities (sum of e^2, not sum of w*e^2)")
    print(f"  RMSE = sqrt(sum(e^2) / (N-k))")
    print(f"  R2 = 1 - sum(e^2) / TSS")
    print(f"  F = (MSS/df_model) / (RSS/df_resid) [all unweighted]")


if __name__ == "__main__":
    main()
