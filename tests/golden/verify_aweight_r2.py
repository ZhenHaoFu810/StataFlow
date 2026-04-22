"""
Final aweight verification - confirm R2 and F calculation path.
"""

import sys
import numpy as np
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tests.golden.test_utils import run_stata_ols
import tempfile

TEMP_DIR = Path(tempfile.mkdtemp(prefix="stataflow_aweight_r2_"))


def main():
    np.random.seed(77777)
    n = 200
    x1 = np.random.normal(0, 1, n)
    x2 = np.random.normal(0, 1, n)
    error = np.random.normal(0, 1, n)
    y = 3 + 1.5 * x1 - 2 * x2 + error
    weights = np.abs(np.random.exponential(scale=2.0, size=n)) + 0.5
    data = pd.DataFrame({"y": y, "x1": x1, "x2": x2, "weight": weights})
    
    w = data["weight"].values
    w_norm = w * n / np.sum(w)  # normalized: sum = N
    y_arr = data["y"].values
    X = np.column_stack([data["x1"].values, data["x2"].values, np.ones(n)])
    k = 3
    
    # WLS
    sqrt_wn = np.sqrt(w_norm)
    X_wn = X * sqrt_wn[:, np.newaxis]
    y_wn = y_arr * sqrt_wn
    beta = np.linalg.solve(X_wn.T @ X_wn, X_wn.T @ y_wn)
    residuals = y_arr - X @ beta
    y_hat = X @ beta
    
    weighted_rss = np.sum(w_norm * residuals**2)
    
    # Stata values
    stata_rss = 192.78539
    stata_mss = 903.513404
    stata_tss = 1096.2988
    stata_r2 = 0.82414886
    stata_rmse = 0.98924519
    stata_f = 461.63285
    
    print("=== Understanding Stata aweight ANOVA ===")
    print(f"Stata: Model={stata_mss}, Residual={stata_rss}, Total={stata_tss}")
    print(f"Check: {stata_mss} + {stata_rss} = {stata_mss + stata_rss:.4f} (should = {stata_tss})")
    print(f"R2 = {stata_mss/stata_tss:.8f} (should = {stata_r2})")
    print(f"R2 = 1 - {stata_rss/stata_tss:.8f}")
    print()
    
    # What is Stata's TSS?
    # Option 1: sum(w_norm * (y - y_bar)^2)
    y_bar = np.mean(y_arr)
    tss_opt1 = np.sum(w_norm * (y_arr - y_bar)**2)
    
    # Option 2: sum(w * (y - y_bar_w)^2) / sum(w) * N
    y_bar_w = np.sum(w * y_arr) / np.sum(w)
    tss_opt2 = np.sum(w * (y_arr - y_bar_w)**2) / np.sum(w) * n
    
    # Option 3: unweighted TSS
    tss_opt3 = np.sum((y_arr - y_bar)**2)
    
    print("=== TSS candidates ===")
    print(f"  Option 1 (w_norm, around mean): {tss_opt1:.6f}")
    print(f"  Option 2 (w, around weighted mean, scaled): {tss_opt2:.6f}")
    print(f"  Option 3 (unweighted): {tss_opt3:.6f}")
    print(f"  Stata TSS: {stata_tss:.6f}")
    print()
    
    # Since RSS matches with normalized weights, and R2 = 1 - RSS/TSS:
    implied_tss = weighted_rss / (1 - stata_r2)
    print(f"Implied TSS from R2 formula: {implied_tss:.6f}")
    
    # And MSS = TSS - RSS
    implied_mss = implied_tss - weighted_rss
    print(f"Implied MSS: {implied_mss:.6f}")
    print(f"Stata MSS: {stata_mss:.6f}")
    print()
    
    # F-statistic
    # F = (MSS/df_model) / (RSS/df_resid)
    f_check = (implied_mss / (k-1)) / (weighted_rss / (n-k))
    print(f"F check with implied MSS: {f_check:.6f}")
    print(f"Stata F: {stata_f:.6f}")
    
    # Hmm, let me check: maybe TSS uses y_bar_w (weighted mean)
    tss_weighted_mean = np.sum(w_norm * (y_arr - y_bar_w)**2)
    mss_from_weighted_mean = tss_weighted_mean - weighted_rss
    f_weighted = (mss_from_weighted_mean / (k-1)) / (weighted_rss / (n-k))
    r2_weighted = 1 - weighted_rss / tss_weighted_mean
    
    print(f"\n=== Using weighted mean ===")
    print(f"  TSS (w_norm, around y_bar_w): {tss_weighted_mean:.6f}")
    print(f"  MSS: {mss_from_weighted_mean:.6f}")
    print(f"  R2: {r2_weighted:.8f}")
    print(f"  F: {f_weighted:.6f}")
    print(f"  Stata R2: {stata_r2}")
    print(f"  Stata F: {stata_f}")


if __name__ == "__main__":
    main()
