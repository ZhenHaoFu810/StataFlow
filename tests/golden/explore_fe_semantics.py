"""
Explore Stata xtreg, fe semantics for FixedEffectsOLS implementation.
"""

import sys
import tempfile
import numpy as np
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tests.golden.test_utils import run_stata_ols, StataRunner

TEMP_DIR = Path(tempfile.mkdtemp(prefix="statapy_fe_explore_"))


def generate_panel_data() -> pd.DataFrame:
    """Generate balanced panel data with known seed."""
    np.random.seed(55555)
    n_entities = 20
    n_periods = 5
    n = n_entities * n_periods

    # Entity and time identifiers
    entity_id = np.repeat(np.arange(n_entities), n_periods)
    time_id = np.tile(np.arange(n_periods), n_entities)

    # Time-varying regressors
    x1 = np.random.normal(0, 1, n)
    x2 = np.random.normal(0, 1, n)

    # Entity fixed effects (heterogeneous intercepts)
    entity_fe = np.repeat(np.random.normal(0, 2, n_entities), n_periods)

    # Idiosyncratic error
    error = np.random.normal(0, 1, n)

    # True model: y = 1 + 1.5*x1 - 2*x2 + entity_fe + error
    y = 1 + 1.5 * x1 - 2 * x2 + entity_fe + error

    return pd.DataFrame({
        "y": y,
        "x1": x1,
        "x2": x2,
        "entity_id": entity_id,
        "time_id": time_id,
    })


def main():
    data = generate_panel_data()
    print("=== Panel Data Summary ===")
    print(f"Total observations: {len(data)}")
    print(f"Entities: {data['entity_id'].nunique()}")
    print(f"Periods: {data['time_id'].nunique()}")
    print()

    # Save data
    dta_file = TEMP_DIR / "p2_fe_explore.dta"
    data.to_stata(str(dta_file), write_index=False)

    # === Test 1: xtreg, fe ===
    print("=== Running Stata: xtreg y x1 x2, fe ===")
    do_fe = '''
clear all
set more off
use "$DATA_FILE", clear

// Set panel structure
xtset entity_id time_id

// Run fixed effects regression
xtreg y x1 x2, fe

// Output e() values
display "E_N=" e(N)
display "E_N_G=" e(N_g)
display "E_DF_M=" e(df_m)
display "E_DF_R=" e(df_r)
display "E_R2_W=" e(r2_w)
display "E_R2_B=" e(r2_b)
display "E_R2_O=" e(r2_o)
display "E_RMSE=" e(rmse)
display "E_F=" e(F)
display "E_SIGMA_U=" e(sigma_u)
display "E_SIGMA_E=" e(sigma_e)
display "E_RSS=" e(rss)

matrix list e(b)
matrix list e(V)
'''.replace("$DATA_FILE", str(dta_file))

    runner = StataRunner()
    result_fe = runner.run_do_file(do_fe, output_dir=str(TEMP_DIR))
    
    import re
    print("=== xtreg, fe Results ===")
    for pattern_name, pattern in [
        ('E_N=', r'E_N=([\d.]+)'),
        ('E_N_g=', r'E_N_g=([\d.]+)'),
        ('E_DF_M=', r'E_DF_M=([\d.]+)'),
        ('E_DF_R=', r'E_DF_R=([\d.]+)'),
        ('E_R2_W=', r'E_R2_W=([\d.]+)'),
        ('E_RMSE=', r'E_RMSE=([\d.]+)'),
        ('E_F=', r'E_F=([\d.]+)'),
        ('E_SIGMA_U=', r'E_SIGMA_U=([\d.]+)'),
        ('E_SIGMA_E=', r'E_SIGMA_E=([\d.]+)'),
        ('E_RSS=', r'E_RSS=([\d.]+)'),
    ]:
        m = re.search(pattern, result_fe.output_content)
        if m:
            val = m.group(1)
            if val.startswith('.'):
                val = '0' + val
            print(f"  {pattern_name} {val}")
    
    # Extract coefficients
    print("\nCoefficients:")
    coef_section = False
    for line in result_fe.output_content.split('\n'):
        if '-------------+----------------------------------------------------------------' in line:
            coef_section = True
            continue
        if coef_section and line.strip() == '':
            coef_section = False
        if coef_section:
            coef_pattern = r'^\s+(\w+)\s+\|\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s+([\d.]+)'
            match = re.match(coef_pattern, line)
            if match:
                name = match.group(1)
                beta = float(match.group(2))
                std_err = float(match.group(3))
                print(f"  {name}: beta={beta:.15f}, se={std_err:.15f}")

    print("\n" + "="*60)
    
    # === Test 2: xtreg, fe vce(cluster entity_id) ===
    print("\n=== Running Stata: xtreg y x1 x2, fe vce(cluster entity_id) ===")
    do_fe_cluster = '''
clear all
set more off
use "$DATA_FILE", clear

xtset entity_id time_id

xtreg y x1 x2, fe vce(cluster entity_id)

display "E_N=" e(N)
display "E_N_G=" e(N_g)
display "E_DF_M=" e(df_m)
display "E_DF_R=" e(df_r)
display "E_R2_W=" e(r2_w)
display "E_RMSE=" e(rmse)
display "E_F=" e(F)
display "E_N_CLUST=" e(N_clust)

matrix list e(b)
matrix list e(V)
'''.replace("$DATA_FILE", str(dta_file))

    result_fe_clust = runner.run_do_file(do_fe_cluster, output_dir=str(TEMP_DIR))
    
    print("=== xtreg, fe vce(cluster) Results ===")
    for pattern_name, pattern in [
        ('E_N=', r'E_N=([\d.]+)'),
        ('E_N_g=', r'E_N_g=([\d.]+)'),
        ('E_DF_M=', r'E_DF_M=([\d.]+)'),
        ('E_DF_R=', r'E_DF_R=([\d.]+)'),
        ('E_R2_W=', r'E_R2_W=([\d.]+)'),
        ('E_RMSE=', r'E_RMSE=([\d.]+)'),
        ('E_F=', r'E_F=([\d.]+)'),
        ('E_N_clust=', r'E_N_clust=([\d.]+)'),
    ]:
        m = re.search(pattern, result_fe_clust.output_content)
        if m:
            val = m.group(1)
            if val.startswith('.'):
                val = '0' + val
            print(f"  {pattern_name} {val}")
    
    print("\nCoefficients:")
    coef_section = False
    for line in result_fe_clust.output_content.split('\n'):
        if '-------------+----------------------------------------------------------------' in line:
            coef_section = True
            continue
        if coef_section and line.strip() == '':
            coef_section = False
        if coef_section:
            coef_pattern = r'^\s+(\w+)\s+\|\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s+([\d.]+)'
            match = re.match(coef_pattern, line)
            if match:
                name = match.group(1)
                beta = float(match.group(2))
                std_err = float(match.group(3))
                print(f"  {name}: beta={beta:.15f}, se={std_err:.15f}")


if __name__ == "__main__":
    main()
