from stataflow.stata_runner import StataRunner
from pathlib import Path

PROJECT_STATA_OUTPUT = Path("stata/output").resolve()
PROJECT_STATA_OUTPUT.mkdir(parents=True, exist_ok=True)

DATA_FILE = Path(__file__).parent.resolve() / "research" / "data" / "public" / "did" / "ezunem_prepared.dta"

runner = StataRunner()

# 1. did_imputation
did_imp_do = f"""
clear all
set more off
use "{DATA_FILE}", clear
did_imputation uclms city year first_treat, allhorizons cluster(city) autosample
display "E_N=" e(N)
display "E_N_CLUST=" e(N_clust)
matrix list e(b)
local names : colfullnames e(b)
foreach name of local names {{
    display "B_`name'=" _b["`name'"]
    display "SE_`name'=" _se["`name'"]
}}
display "DID_IMP_OK"
"""

# 2. eventstudyinteract
es_do = f"""
clear all
set more off
use "{DATA_FILE}", clear
gen cohort = first_treat
gen rel_time = year - first_treat if first_treat > 0
replace rel_time = -1000 if first_treat == 0
tab rel_time, gen(Dm)
eventstudyinteract uclms Dm1 Dm2 Dm3 Dm4, cohort(cohort) control_cohort(never_treated) absorb(city year) cluster(city)
matrix b_iw = e(b_iw)
matrix V_iw = e(V_iw)
local names : colfullnames b_iw
local i = 1
foreach name of local names {{
    display "B_`name'=" b_iw[1, `i']
    display "SE_`name'=" sqrt(V_iw[`i', `i'])
    local ++i
}}
display "ES_OK"
"""

# 3. csdid
csdid_do = f"""
clear all
set more off
use "{DATA_FILE}", clear
csdid uclms, ivar(city) time(year) gvar(first_treat) method(reg)
csdid_estat event
matrix b = e(b)
matrix V = e(V)
local names : colfullnames b
local i = 1
foreach name of local names {{
    display "B_`name'=" b[1, `i']
    display "SE_`name'=" sqrt(V[`i', `i'])
    local ++i
}}
display "E_N=" e(N)
display "CSDID_OK"
"""

for name, do_content in [("did_imputation", did_imp_do), ("eventstudyinteract", es_do), ("csdid", csdid_do)]:
    result = runner.run_do_file(do_content, output_dir=str(PROJECT_STATA_OUTPUT), timeout=300)
    log_path = PROJECT_STATA_OUTPUT / f"realdata_{name}.log"
    if result.log_file and Path(result.log_file).exists():
        with open(result.log_file, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"{name}: wrote log to {log_path} (exit={result.exit_code})")
    else:
        err_path = PROJECT_STATA_OUTPUT / f"realdata_{name}_err.txt"
        with open(err_path, "w", encoding="utf-8") as f:
            f.write(f"No log. exit={result.exit_code}\nerr={repr(result.error_message)}\n")
        print(f"{name}: FAILED (exit={result.exit_code}, err={repr(result.error_message)})")
