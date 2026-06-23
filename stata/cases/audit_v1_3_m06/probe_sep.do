clear all
set more off
set seed 20260616
set obs 60
gen entity_id = ceil(_n/4)
gen x1 = rnormal()
gen x2 = rnormal()
* 3 entities all y=0
bysort entity_id: gen n = _n
replace x1 = 0 if entity_id <= 3
replace x2 = 0 if entity_id <= 3
gen eta = 0.5*x1 - 0.3*x2 + ((entity_id>3)*rnormal()*0.2)
gen y = rpoisson(exp(eta))
replace y = 0 if entity_id <= 3
* default separation
ppmlhdfe y x1 x2, absorb(entity_id) vce(robust)
display "DEFAULT_N=" e(N)
display "DEFAULT_DF_A=" e(df_a)
* no separation
ppmlhdfe y x1 x2, absorb(entity_id) vce(robust) separation(none)
display "NONE_N=" e(N)
display "NONE_DF_A=" e(df_a)
