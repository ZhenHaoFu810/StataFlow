clear all
set more off
set seed 20260618
set obs 150
gen entity_id = ceil(_n/10)
gen x1 = rnormal()
gen x2 = rnormal()
gen off = rnormal()*0.1
gen eta = 0.4*x1 - 0.2*x2 + off + ((entity_id)*0.1)
gen y = rpoisson(exp(eta))
gen w = runiform()*2+0.5
ppmlhdfe y x1 x2 [aweight=w], absorb(entity_id) offset(off) vce(robust)
display "W_N=" e(N)
display "B_X1=" _b[x1]
display "B_X2=" _b[x2]
display "B__CONS=" _b[_cons]
