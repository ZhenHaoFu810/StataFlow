clear all
set obs 10
gen x = rnormal()
gen y = 1 + 2*x + rnormal()
regress y x
display "F_P=" e(F_p)
display "P=" e(p)
