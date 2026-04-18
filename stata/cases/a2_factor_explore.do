clear all
set more off

use "D:/OneDrive - SAIF/PhD3/Stata2Python/stata/cases/a2_factor_test_data.dta", clear

// Explore factor syntax coefficient names
regress y c.x1#c.x2
matrix list e(b)
regress y c.x1##c.x2
matrix list e(b)
regress y i.g##c.x1
matrix list e(b)

reghdfe y c.x1##c.x2, absorb(firm year)
matrix list e(b)

reghdfe y i.g##c.x1, absorb(firm year)
matrix list e(b)

logit y_bin c.x1##c.x2
matrix list e(b)
