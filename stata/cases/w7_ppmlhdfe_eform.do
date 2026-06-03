clear all
set more off

* Generate synthetic PPML data
set seed 12345
set obs 200
gen entity_id = mod(_n-1, 40) + 1
gen time_id = mod(_n-1, 5) + 1
gen x1 = rnormal(0, 1)
gen x2 = rnormal(0, 0.5)
gen fe1 = rnormal(0, 0.3)
gen fe2 = rnormal(0, 0.2)
gen eta = 0.5 + 0.6*x1 - 0.4*x2 + fe1 + fe2
gen mu = exp(eta)
gen y = rpoisson(mu)

* Run ppmlhdfe with eform
ppmlhdfe y x1 x2, absorb(entity_id time_id) eform

display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_DEV=" e(deviance)
display "E_R2=" e(r2_p)

display "B_X1=" _b[x1]
display "B_X2=" _b[x2]
display "B__CONS=" _b[_cons]

display "SE_X1=" _se[x1]
display "SE_X2=" _se[x2]
display "SE__CONS=" _se[_cons]

display "Stata ppmlhdfe eform completed successfully"
