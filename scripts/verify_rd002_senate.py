"""
RD-002 Senate real-data verification: compare rdplot automatic bin counts
with Stata 17.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT))

from stataflow.compat.stata.rdplot import rdplot
from tests.golden.test_utils import StataRunner

DATA_FILE = PROJECT_ROOT / "research" / "data" / "public" / "rdrobust_senate_with_z.dta"

df = pd.read_stata(str(DATA_FILE))
print(f"Loaded {len(df)} observations")

for sel in ["esmv", "qsmv"]:
    res = rdplot(df, y="margin", x="vote", c=50.0, binselect=sel)
    info = res["info"]
    print(f"Python {sel}: J=({info['J_star_l']}, {info['J_star_r']}), N=({info['N_l']}, {info['N_r']})")

runner = StataRunner()
for sel in ["esmv", "qsmv"]:
    do = f'''
clear all
set more off
use "{DATA_FILE}", clear
which rdplot
rdplot margin vote, c(50.0) binselect({sel}) stdvars
display "J_l=" e(J_star_l)
display "J_r=" e(J_star_r)
display "N_l=" e(N_l)
display "N_r=" e(N_r)
display "RD002_SENATE_DONE"
'''
    result = runner.run_do_file(do, output_dir=str(PROJECT_ROOT / "stata" / "output"))
    log = result.output_content or ""
    print(f"\nStata {sel} log:")
    for line in log.splitlines():
        if any(k in line for k in ["J_l=", "J_r=", "N_l=", "N_r="]):
            print(line)
