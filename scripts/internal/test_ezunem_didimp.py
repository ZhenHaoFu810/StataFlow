from statapy.stata_runner import StataRunner
from pathlib import Path

DATA_FILE = Path("research/data/public/did/ezunem_prepared.dta").resolve()
runner = StataRunner()

do = f"""
clear all
set more off
use "{DATA_FILE}", clear
did_imputation uclms city year first_treat, horizons(0/2) cluster(city) minn(0)
display "E_N=" e(N)
matrix list e(b)
local names : colfullnames e(b)
foreach name of local names {{
    display "B_`name'=" _b["`name'"]
    display "SE_`name'=" _se["`name'"]
}}
display "OK"
"""

result = runner.run_do_file(do, output_dir='stata/output', timeout=120)
print(f"exit={result.exit_code}")
if result.log_file and Path(result.log_file).exists():
    with open(result.log_file, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    print(content[-3000:])
else:
    print("No log file")
    print("output:", result.output_content)
    print("error:", result.error_message)
