"""
Debug FE + cluster differences.
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

TEMP_DIR = Path(tempfile.mkdtemp(prefix="stataflow_fe_clust_debug_"))


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
    dta_file = TEMP_DIR / "p2_fe_clust_debug.dta"
    data.to_stata(str(dta_file), write_index=False)
    
    runner = StataRunner()
    
    do_full = '''
clear all
set more off
use "$DATA_FILE", clear
xtset entity_id time_id
xtreg y x1 x2, fe vce(cluster entity_id)

display "E_N=" e(N)
display "E_N_g=" e(N_g)
display "E_DF_M=" e(df_m)
display "E_DF_R=" e(df_r)
display "E_R2_W=" e(r2_w)
display "E_RMSE=" e(rmse)
display "E_F=" e(F)
display "E_N_CLUST=" e(N_clust)
display "E_RSS=" e(rss)
display "E_MSS=" e(mss)
display "E_rank=" e(rank)

matrix list e(b)
matrix list e(V)
'''.replace("$DATA_FILE", str(dta_file))
    
    result = runner.run_do_file(do_full, output_dir=str(TEMP_DIR))
    
    print("=== FULL Stata Log ===")
    print(result.output_content)
    
    print("\n=== Parsed Values ===")
    for name, pattern in [
        ('N', r'E_N=([\d.]+)'), ('N_g', r'E_N_g=([\d.]+)'),
        ('df_m', r'E_DF_M=([\d.]+)'), ('df_r', r'E_DF_R=([\d.]+)'),
        ('r2_w', r'E_R2_W=([\d.]+)'), ('rmse', r'E_RMSE=([\d.]+)'),
        ('F', r'E_F=([\d.]+)'), ('N_clust', r'E_N_clust=([\d.]+)'),
        ('rss', r'E_RSS=([\d.]+)'), ('mss', r'E_MSS=([\d.]+)'),
    ]:
        m = re.search(pattern, result.output_content)
        if m:
            val = m.group(1)
            if val.startswith('.'):
                val = '0' + val
            print(f"  {name} = {val}")


if __name__ == "__main__":
    main()
