import pytest
from pathlib import Path
from statapy.stata_runner import StataRunner

PROJECT_STATA_OUTPUT = Path(__file__).parent.parent.parent / "stata" / "output"

def test_run_did_imputation_jtrain_hrsemp():
    data_file = Path("research/data/public/did/jtrain_prepared.dta").resolve()
    runner = StataRunner()
    do = f"""
clear all
set more off
use "{data_file}", clear
did_imputation hrsemp fcode year first_treat, allhorizons cluster(fcode) autosample minn(0)
display "E_N=" e(N)
matrix list e(b)
local names : colfullnames e(b)
foreach name of local names {{
    display "B_`name'=" _b["`name'"]
    display "SE_`name'=" _se["`name'"]
}}
display "DID_IMP_OK"
"""
    result = runner.run_do_file(do, output_dir=str(PROJECT_STATA_OUTPUT), timeout=120)
    log_path = PROJECT_STATA_OUTPUT / "realdata_did_imputation_jtrain_hrsemp.log"
    if result.log_file and Path(result.log_file).exists():
        with open(result.log_file, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(content)
    assert result.exit_code == 0, f"Stata failed: {result.error_message}"
