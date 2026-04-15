"""
Investigate how Stata computes _cons SE in xtreg, fe vce(cluster).
Use LSDV regression to verify the exact formula.
"""

import sys
import tempfile
import numpy as np
import pandas as pd
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tests.golden.test_utils import run_stata_ols, StataRunner

TEMP_DIR = Path(tempfile.mkdtemp(prefix="statapy_fe_cons_se_"))


def generate_test_data() -> pd.DataFrame:
    np.random.seed(66666)
    n_entities = 30
    n_periods = 4
    n = n_entities * n_periods
    
    entity_id = np.repeat(np.arange(n_entities), n_periods)
    time_id = np.tile(np.arange(n_periods), n_entities)
    x1 = np.random.normal(0, 1, n)
    x2 = np.random.normal(0, 1, n)
    entity_fe = np.repeat(np.random.normal(0, 2, n_entities), n_periods)
    error = np.random.normal(0, 1, n)
    y = 1 + 1.5 * x1 - 2 * x2 + entity_fe + error
    
    return pd.DataFrame({
        "y": y, "x1": x1, "x2": x2,
        "entity_id": entity_id, "time_id": time_id,
    })


def main():
    data = generate_test_data()
    n = len(data)
    G = data['entity_id'].nunique()
    
    # Save data
    dta_file = TEMP_DIR / "p2_fe_cons_se.dta"
    data.to_stata(str(dta_file), write_index=False)
    
    runner = StataRunner()
    
    # Test 1: xtreg, fe vce(cluster)
    print("=== Test 1: xtreg, fe vce(cluster entity_id) ===")
    do_xtreg = '''
clear all
set more off
use "$DATA_FILE", clear
xtset entity_id time_id
xtreg y x1 x2, fe vce(cluster entity_id)
display "E_N=" e(N)
display "E_RMSE=" e(rmse)
matrix list e(b)
matrix list e(V)
'''.replace("$DATA_FILE", str(dta_file))
    
    result_xtreg = runner.run_do_file(do_xtreg, output_dir=str(TEMP_DIR))
    print(result_xtreg.output_content[result_xtreg.output_content.find('xtreg'):result_xtreg.output_content.find('end of do-file')][:2000])
    
    # Test 2: LSDV with regress and cluster
    print("\n=== Test 2: LSDV regress y x1 x2 i.entity_id, vce(cluster entity_id) ===")
    do_lsdv = '''
clear all
set more off
use "$DATA_FILE", clear
regress y x1 x2 ib0.entity_id, vce(cluster entity_id)
display "E_N=" e(N)
display "E_RMSE=" e(rmse)
matrix list e(b)
matrix list e(V)
'''.replace("$DATA_FILE", str(dta_file))
    
    result_lsdv = runner.run_do_file(do_lsdv, output_dir=str(TEMP_DIR))
    
    # Extract _cons SE from LSDV
    # In LSDV, the constant is the FE for entity 0
    # We need to compute the grand mean of all FEs
    # grand_mean = mean(alpha_i) = cons + mean(dummy_coef_i) for i=1..G-1
    
    # Actually, let's just get the V matrix and compute Var(mean(alpha_i))
    # This is complex because we need the full covariance including dummies
    
    # Test 3: Get the alpha_i and their covariance
    print("\n=== Test 3: Compute alpha_i and Var(mean(alpha_i)) ===")
    
    # Python computation
    y = data['y'].values
    x1 = data['x1'].values
    x2 = data['x2'].values
    entity_id = data['entity_id'].values
    
    # Within transformation
    df_temp = data.copy()
    df_temp['_y'] = y
    df_temp['_x1'] = x1
    df_temp['_x2'] = x2
    entity_means = df_temp.groupby('entity_id').transform('mean')
    y_w = y - entity_means['_y'].values
    X_w = np.column_stack([x1 - entity_means['_x1'].values, x2 - entity_means['_x2'].values])
    
    beta = np.linalg.solve(X_w.T @ X_w, X_w.T @ y_w)
    residuals_w = y_w - X_w @ beta
    rss = np.sum(residuals_w ** 2)
    
    # Compute entity fixed effects
    entity_means_y = entity_means['_y'].values[:G]
    entity_means_x1 = entity_means['_x1'].values[:G]
    entity_means_x2 = entity_means['_x2'].values[:G]
    alpha = entity_means_y - entity_means_x1 * beta[0] - entity_means_x2 * beta[1]
    grand_mean = np.mean(alpha)
    
    print(f"beta = {beta}")
    print(f"alpha (entity effects) = {alpha}")
    print(f"grand_mean = {grand_mean}")
    
    # Now compute Var(grand_mean) using cluster-robust approach
    # alpha_i = y_bar_i - x_bar_i' * beta
    # grand_mean = (1/G) * sum_i alpha_i
    # Var(grand_mean) = (1/G^2) * sum_i sum_j Cov(alpha_i, alpha_j)
    
    # Using the influence function approach for cluster-robust SE
    # For FE model, the SE of grand_mean requires the full variance-covariance
    
    # Alternative: Use the formula from the LSDV regression
    # The cluster-robust VCE for LSDV is:
    # V_CR = (N-1)/(N-k-G) * G/(G-1) * (X'X)^{-1} * Omega * (X'X)^{-1}
    # where Omega = sum_g (X_g' e_g) (X_g' e_g)'
    
    # For the grand mean, we need Var((1/G) * sum_i alpha_i)
    # = (1/G^2) * 1' * V_alpha * 1
    # where V_alpha is the covariance matrix of alpha_i
    
    # The relationship between alpha and the LSDV coefficients:
    # alpha = M * theta_LSDV
    # where theta_LSDV = (beta_1, ..., beta_k, alpha_1, ..., alpha_G)
    # and M maps LSDV coefs to alpha_i
    
    # Actually, in the LSDV with all G dummies and no cons:
    # alpha_i IS the coefficient on dummy_i
    # So Var(mean(alpha)) = (1/G^2) * 1' * V_dummies * 1
    
    # Let me try a different approach:
    # The influence function for alpha_i is:
    # IF_i = (1/T_i) * sum_t (y_it - x_it' * beta - alpha_i)
    #      = (1/T_i) * sum_t e_it  (but these are the within residuals, which sum to 0 within each entity)
    
    # This is getting complex. Let me try the direct LSDV approach.
    
    print("\n=== Trying direct LSDV with Python ===")
    
    # Build full LSDV design matrix (entity dummies, no constant)
    D = np.zeros((n, G))
    for g in range(G):
        D[entity_id == g, g] = 1
    
    X_full = np.column_stack([x1, x2, D])
    k_full = X_full.shape[1]  # k + G
    
    # OLS
    beta_full = np.linalg.solve(X_full.T @ X_full, X_full.T @ y)
    residuals_full = y - X_full @ beta_full
    
    print(f"LSDV beta = {beta_full[:2]}")
    print(f"LSDV alpha = {beta_full[2:]}")
    print(f"Grand mean = {np.mean(beta_full[2:]):.8f}")
    
    # Cluster-robust VCE
    XtX_full = X_full.T @ X_full
    XtX_inv_full = np.linalg.inv(XtX_full)
    
    meat_full = np.zeros((k_full, k_full))
    for g in range(G):
        mask_g = entity_id == g
        X_g = X_full[mask_g]
        e_g = residuals_full[mask_g]
        Xe_g = X_g.T @ e_g
        meat_full += np.outer(Xe_g, Xe_g)
    
    # Correction: (N-1)/(N-k_full) * G/(G-1)
    n_adj = (n - 1) / (n - k_full)
    g_adj = G / (G - 1)
    V_CR_full = n_adj * g_adj * XtX_inv_full @ meat_full @ XtX_inv_full
    
    # Extract covariance of dummies (alpha)
    V_alpha = V_CR_full[2:, 2:]
    grand_mean = np.mean(beta_full[2:])
    
    # Var(grand_mean) = (1/G^2) * 1' * V_alpha * 1
    ones_G = np.ones(G)
    var_grand_mean = (1 / G**2) * ones_G @ V_alpha @ ones_G
    se_grand_mean = np.sqrt(var_grand_mean)
    
    print(f"\nLSDV cluster-robust SE of grand mean: {se_grand_mean:.8f}")
    print(f"Stata _cons SE from xtreg: 0.0247851")
    
    # What if we use different correction?
    # Try: (N-1)/(N-k-1) * G/(G-1)  (the FE cluster correction we found earlier)
    n_adj_fe = (n - 1) / (n - 2 - 1)  # (N-1)/(N-k_slopes-1)
    V_CR_fe = n_adj_fe * g_adj * XtX_inv_full @ meat_full @ XtX_inv_full
    V_alpha_fe = V_CR_fe[2:, 2:]
    var_grand_mean_fe = (1 / G**2) * ones_G @ V_alpha_fe @ ones_G
    se_grand_mean_fe = np.sqrt(var_grand_mean_fe)
    print(f"\nWith (N-1)/(N-k-1) * G/(G-1): SE = {se_grand_mean_fe:.8f}")
    
    # Try no correction at all
    V_raw = XtX_inv_full @ meat_full @ XtX_inv_full
    V_alpha_raw = V_raw[2:, 2:]
    var_grand_mean_raw = (1 / G**2) * ones_G @ V_alpha_raw @ ones_G
    se_grand_mean_raw = np.sqrt(var_grand_mean_raw)
    print(f"With no correction: SE = {se_grand_mean_raw:.8f}")


if __name__ == "__main__":
    main()
