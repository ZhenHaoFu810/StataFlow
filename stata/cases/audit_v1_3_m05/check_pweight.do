clear all
set obs 10
gen y = mod(_n,2)
gen x = _n
gen w = _n
logit y x [pweight=w]
