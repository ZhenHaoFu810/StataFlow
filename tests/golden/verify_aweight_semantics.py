"""
Verify Python aweight implementation against Stata results.
Test different approaches to match Stata's aweight semantics.
"""

import sys
import tempfile
import numpy as np
import pandas as pd
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tests.golden.test_utils import run_stata_ols
from statapy import OLS

TEMP_DIR = Path(tempfile.mkdtemp(prefix="statapy_aweight_verify_"))


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

    # Run Stata with aweight
    dta_file = TEMP_DIR / "p2_aweight_verify.dta"
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
display "E_F_P=" e(F_p)
display "E_RSS=" e(rss)
display "E_MSS=" e(mss)
display "E_N_weight=" e(N_subp)
'''.replace("$DATA_FILE", str(dta_file))

    stata_result = run_stata_ols(do_content)

    print("=== Stata aweight Results ===")
    print(f"nobs     = {stata_result.get('nobs')}")
    print(f"df_model = {stata_result.get('df_model')}")
    print(f"df_resid = {stata_result.get('df_resid')}")
    print(f"r2       = {stata_result.get('r2'):.15f}")
    print(f"r2_adj   = {stata_result.get('r2_adj'):.15f}")
    print(f"rmse     = {stata_result.get('rmse'):.15f}")
    print(f"f_stat   = {stata_result.get('f_stat'):.15f}")
    print(f"rss      = {stata_result.get('rss'):.15f}")
    print(f"mss      = {stata_result.get('mss')}")
    print(f"N_weight = {stata_result.get('n_weight')}")  # e(N_subp) for aweight
    print()
    print("Stata coefficients:")
    for coef in stata_result.get('coefficients', []):
        print(f"  {coef['name']}: beta={coef['beta']:.15f}, se={coef['std_err']:.15f}")

    # === Python numerical experiments ===
    y = data["y"].values
    X_raw = np.column_stack([data["x1"].values, data["x2"].values, np.ones(n)])
    coef_names = ["x1", "x2", "_cons"]
    k = X_raw.shape[1]  # 3

    print("\n=== Python Experiments ===")

    # Approach 1: Standard WLS with sqrt(w) transformation
    # beta = (X'WX)^{-1} X'Wy
    sqrt_w = np.sqrt(w)
    X_w = X_raw * sqrt_w[:, np.newaxis]
    y_w = y * sqrt_w

    XtWX = X_w.T @ X_w
    XtWy = X_w.T @ y_w
    beta_wls = np.linalg.solve(XtWX, XtWy)

    print("\nApproach 1: Standard WLS (sqrt(w) transformation)")
    print(f"beta = {beta_wls}")

    residuals = y - X_raw @ beta_wls

    # Stata aweight: sigma2 = sum(w * e^2) / (N - k)
    # Note: uses N not sum(w) in denominator
    weighted_rss = np.sum(w * residuals**2)
    sigma2_aweight = weighted_rss / (n - k)

    print(f"weighted RSS = sum(w*e^2) = {weighted_rss:.15f}")
    print(f"sigma2 = weighted_RSS / (N-k) = {sigma2_aweight:.15f}")
    print(f"rmse = sqrt(sigma2) = {np.sqrt(sigma2_aweight):.15f}")
    print(f"Stata rmse = {stata_result.get('rmse'):.15f}")

    # Covariance: sigma2 * (X'WX)^{-1}
    cov_aweight = sigma2_aweight * np.linalg.inv(XtWX)
    se_aweight = np.sqrt(np.diag(cov_aweight))

    print(f"\nPython aweight SE (sigma2 = sum(w*e^2)/(N-k)):")
    for name, b, se in zip(coef_names, beta_wls, se_aweight):
        print(f"  {name}: beta={b:.15f}, se={se:.15f}")

    # Compare with Stata
    print(f"\nComparison with Stata:")
    for i, coef in enumerate(stata_result.get('coefficients', [])):
        py_beta = beta_wls[i]
        py_se = se_aweight[i]
        st_beta = coef['beta']
        st_se = coef['std_err']
        print(f"  {coef['name']}:")
        print(f"    beta: py={py_beta:.15f}, st={st_beta:.15f}, diff={abs(py_beta - st_beta):.2e}")
        print(f"    se:   py={py_se:.15f}, st={st_se:.15f}, diff={abs(py_se - st_se):.2e}")

    # R2 calculation
    # Weighted TSS: sum(w * (y - y_bar_w)^2) where y_bar_w is weighted mean
    y_bar_w = np.sum(w * y) / np.sum(w)
    weighted_tss = np.sum(w * (y - y_bar_w)**2)
    r2_weighted = 1 - weighted_rss / weighted_tss

    print(f"\nR2 comparison:")
    print(f"  Python weighted R2 = {r2_weighted:.15f}")
    print(f"  Stata R2           = {stata_result.get('r2'):.15f}")

    # Adjusted R2
    r2_adj_python = 1 - (1 - r2_weighted) * (n - 1) / (n - k)
    print(f"  Python adj R2 = {r2_adj_python:.15f}")
    print(f"  Stata adj R2  = {stata_result.get('r2_adj'):.15f}")

    # F-statistic
    weighted_mss = weighted_tss - weighted_rss
    f_stat = (weighted_mss / (k - 1)) / (weighted_rss / (n - k))
    from scipy.stats import f as f_dist
    f_pvalue = 1 - f_dist.cdf(f_stat, dfn=k-1, dfd=n-k)
    print(f"\nF-statistic comparison:")
    print(f"  Python F = {f_stat:.15f}")
    print(f"  Stata F  = {stata_result.get('f_stat'):.15f}")


if __name__ == "__main__":
    main()
