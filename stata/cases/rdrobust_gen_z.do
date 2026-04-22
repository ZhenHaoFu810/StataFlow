clear all
set more off
cd "D:\OneDrive - SAIF\PhD3\StataFlow"
use "research/vendor/stata_community/rdrobust/rdrobust-master/stata/rdrobust_senate.dta", clear
set seed 42
gen z = 0.5 * margin + rnormal(0, 0.3)
save "stata/output/rdrobust_senate_with_z.dta", replace
