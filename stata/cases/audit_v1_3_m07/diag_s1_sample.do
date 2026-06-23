clear all
set more off
use "D:/OneDrive - SAIF/PhD3/StataFlow/stata/cases/audit_v1_3_m07/S1_DIDIMP_BASIC.dta", clear
did_imputation y id time first_treat, cluster(id) autosample minn(0)
gen _stata_sample = e(sample)
tab _stata_sample first_treat
save "D:/OneDrive - SAIF/PhD3/StataFlow/stata/output/audit_v1_3_m07/S1_DIDIMP_BASIC_sample.dta", replace
