clear all
set more off

use "D:/OneDrive - SAIF/PhD3/Stata2Python/stata/cases/a2_factor_test_data.dta", clear

logit y_bin c.x1##c.x2
matrix list e(b)
