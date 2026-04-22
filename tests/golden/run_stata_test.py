"""
Run Stata directly and capture results.

This script generates data, runs Stata, and saves results for comparison.
"""

import os
import tempfile
import numpy as np
import pandas as pd
from pathlib import Path
from stataflow.stata_runner import StataRunner

# Generate data
np.random.seed(12345)
n = 100
x1 = np.random.normal(0, 1, n)
x2 = np.random.normal(0, 1, n)
y = 1 + 2 * x1 + 3 * x2 + np.random.normal(0, 1, n)

df = pd.DataFrame({"y": y, "x1": x1, "x2": x2})

# Save to temp directory (no spaces in path)
temp_dir = Path(tempfile.mkdtemp(prefix="stataflow_"))
dta_path = temp_dir / "data.dta"
json_path = temp_dir / "stata_results.json"

print(f"Temp dir: {temp_dir}")
print(f"Saving data to: {dta_path}")

df.to_stata(str(dta_path), write_index=False)

# Build .do file
do_content = f'''
clear all
set more off

// Read data
use "{dta_path}", clear

// Run regression  
regress y x1 x2

// Export results to JSON
matrix b = e(b)
matrix V = e(V)

tempname fh
file open `fh' using "{json_path}", write replace

file write `fh' "{{" _n
file write `fh' "  \\"nobs\\": " %10.0f e(N) "," _n
file write `fh' "  \\"df_model\\": " %10.0f e(df_m) "," _n
file write `fh' "  \\"df_resid\\": " %10.0f e(df_r) "," _n
file write `fh' "  \\"r2\\": " %18.10f e(r2) "," _n
file write `fh' "  \\"rmse\\": " %18.10f e(rmse)" _n
file write `fh' "}}" _n

file close `fh'

display "DONE: Results saved to {json_path}"
'''

print("\nRunning Stata...")
runner = StataRunner()
print(f"Stata executable: {runner.resolved_stata_path}")

result = runner.run_do_file(do_content)

print(f"\nExit code: {result.exit_code}")
print(f"Log file: {result.log_file}")
print(f"Error: {result.error_message}")

if result.log_file and os.path.exists(result.log_file):
    with open(result.log_file, 'r', encoding='utf-8', errors='replace') as f:
        log = f.read()
        print(f"\nLog file content ({len(log)} chars):")
        print(log[-500:] if len(log) > 500 else log)

if json_path.exists():
    print(f"\n鉁?Stata JSON created at: {json_path}")
    with open(json_path, 'r') as f:
        print(f.read())
else:
    print(f"\n鉁?Stata JSON NOT found at: {json_path}")
