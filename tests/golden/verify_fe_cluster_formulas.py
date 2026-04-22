"""
Verify FE + cluster formulas.
"""

import sys
import tempfile
import numpy as np
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tests.golden.test_utils import run_stata_ols, StataRunner

TEMP_DIR = Path(tempfile.mkdtemp(prefix="stataflow_fe_clust_verify_"))


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
    k = 2  # x1, x2
    
    # Stata values
    stata_rmse = 0.91289182
    stata_sigma_e = 1.0526183
    stata_rss = 97.504463
    stata_F = 195.39913
    stata_df_m = 1
    stata_df_r = 29
    
    print("=== Stata FE + cluster Values ===")
    print(f"N = {n}")
    print(f"G = {G}")
    print(f"k = {k}")
    print(f"RSS = {stata_rss}")
    print(f"RMSE = {stata_rmse}")
    print(f"sigma_e = {stata_sigma_e}")
    print(f"F = {stata_F}")
    print(f"df_m = {stata_df_m}")
    print(f"df_r = {stata_df_r}")
    print()
    
    # Check RMSE formula
    print("=== RMSE candidates ===")
    candidates = {
        "sqrt(RSS/(N-G-k))": np.sqrt(stata_rss / (n - G - k)),
        "sqrt(RSS/(N-1))": np.sqrt(stata_rss / (n - 1)),
        "sqrt(RSS/N)": np.sqrt(stata_rss / n),
        "sqrt(RSS/(G-1))": np.sqrt(stata_rss / (G - 1)),
        "sigma_e": stata_sigma_e,
    }
    for name, val in candidates.items():
        diff = abs(val - stata_rmse)
        print(f"  {name:25s} = {val:.8f} (diff={diff:.2e})")
    
    # From Stata output: sigma_e = 1.0526183
    # RMSE = 0.91289182
    # Check: is RMSE from different df?
    # RMSE^2 * df = RSS
    implied_df = stata_rss / (stata_rmse ** 2)
    print(f"\nImplied df from RMSE: RSS/RMSE^2 = {implied_df:.4f}")
    print(f"  N-1 = {n-1}")
    print(f"  N-G = {n-G}")
    print(f"  N-G-k = {n-G-k}")
    print(f"  G-1 = {G-1}")
    
    # Wait! Maybe Stata reports sqrt(RSS/(N-1)) for FE cluster?
    # Or maybe it's the within-transformation adjusted RSS?
    
    # Let me compute within RSS manually
    y = data['y'].values
    X = data[['x1', 'x2']].values
    entity_id = data['entity_id'].values
    
    # Within transformation
    df_temp = data.copy()
    df_temp['_y'] = y
    df_temp['_x1'] = X[:, 0]
    df_temp['_x2'] = X[:, 1]
    
    entity_means = df_temp.groupby('entity_id').transform('mean')
    y_w = y - entity_means['_y'].values
    X_w = np.column_stack([
        X[:, 0] - entity_means['_x1'].values,
        X[:, 1] - entity_means['_x2'].values,
    ])
    
    # OLS on within
    beta = np.linalg.solve(X_w.T @ X_w, X_w.T @ y_w)
    residuals_w = y_w - X_w @ beta
    rss_within = np.sum(residuals_w ** 2)
    
    print(f"\n=== Python Within Calculation ===")
    print(f"RSS (within) = {rss_within:.8f}")
    print(f"Stata RSS = {stata_rss:.8f}")
    print(f"Diff = {abs(rss_within - stata_rss):.2e}")
    
    # Now for cluster SE, the RMSE might use different formula
    # In Stata xtreg, fe vce(cluster), RMSE is sigma_e from the within regression
    # sigma_e = sqrt(RSS / (N - G - k))
    sigma_e_check = np.sqrt(rss_within / (n - G - k))
    print(f"\nsigma_e = sqrt(RSS/(N-G-k)) = {sigma_e_check:.8f}")
    print(f"Stata sigma_e = {stata_sigma_e:.8f}")
    
    # But RMSE reported is different...
    # Actually, let me check if Stata uses sqrt(RSS / (N - 1)) for display
    rmse_display = np.sqrt(rss_within / (n - 1))
    print(f"\nRMSE display (N-1) = {rmse_display:.8f}")
    print(f"Stata RMSE = {stata_rmse:.8f}")


if __name__ == "__main__":
    main()
