"""
RD-002 verification: compare rdplot automatic bin counts with Stata 17.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT))

from stataflow.compat.stata.rdplot import rdplot
from tests.golden.test_utils import StataRunner

np.random.seed(42)
n = 500
x = np.random.normal(0, 1, n)
y = 2.0 + 1.5 * x + 0.5 * x**2 + np.random.normal(0, 0.5, n)
df = pd.DataFrame({"y": y, "x": x})

DATA_FILE = PROJECT_ROOT / "stata" / "cases" / "rd002_data.dta"
df.to_stata(str(DATA_FILE), write_index=False)

# Python bin counts
res_es = rdplot(df, y="y", x="x", c=0.0, binselect="esmv")
res_qs = rdplot(df, y="y", x="x", c=0.0, binselect="qsmv")
info_es = res_es["info"]
info_qs = res_qs["info"]
print(f"Python esmv: J=({info_es['J_star_l']}, {info_es['J_star_r']}), N=({info_es['N_l']}, {info_es['N_r']})")
print(f"Python qsmv: J=({info_qs['J_star_l']}, {info_qs['J_star_r']}), N=({info_qs['N_l']}, {info_qs['N_r']})")

# Stata bin counts
runner = StataRunner()
for sel in ["esmv", "qsmv"]:
    do = f'''
clear all
set more off
use "{DATA_FILE}", clear
rdplot y x, c(0.0) binselect({sel})
display "J_l=" e(J_star_l)
display "J_r=" e(J_star_r)
display "J_IMSE_l=" e(J_IMSE_l)
display "J_IMSE_r=" e(J_IMSE_r)
display "J_MV_l=" e(J_MV_l)
display "J_MV_r=" e(J_MV_r)
display "N_l=" e(N_l)
display "N_r=" e(N_r)
display "RD002_DONE"
'''
    result = runner.run_do_file(do, output_dir=str(PROJECT_ROOT / "stata" / "output"))
    log = result.output_content or ""
    print(f"\nStata {sel} log:")
    for line in log.splitlines():
        if any(k in line for k in ["J_l=", "J_r=", "J_IMSE", "J_MV", "N_l=", "N_r="]):
            print(line)
