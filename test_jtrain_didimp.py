from statapy.stata_runner import StataRunner
from pathlib import Path

DATA_FILE = Path("research/data/public/did/jtrain_prepared.dta").resolve()
runner = StataRunner()

do = f"""
clear all
set more off
use "{DATA_FILE}", clear
did_imputation scrap fcode year first_treat, allhorizons cluster(fcode) autosample
display "E_N=" e(N)
display "E_N_CLUST=" e(N_clust)
matrix list e(b)
local names : colfullnames e(b)
foreach name of local names {{
    display "B_`name'=" _b["`name'"]
    display "SE_`name'=" _se["`name'"]
}}
display "OK"
"""

result = runner.run_do_file(do, output_dir='stata/output', timeout=120)
with open('stata/output/test_jtrain_didimp.log', 'w', encoding='utf-8') as f:
    f.write(f"exit={result.exit_code}\n")
    if result.log_file and Path(result.log_file).exists():
        with open(result.log_file, 'r', encoding='utf-8', errors='replace') as lf:
            f.write(lf.read())
    else:
        f.write("No log file\n")
        if result.output_content:
            f.write(result.output_content)
        if result.error_message:
            f.write(str(result.error_message.encode('utf-8', errors='replace')))
print("Done")
