noi cscript "ppmlhdfe - trivial case where y=0" adofile ppmlhdfe
set linesize 150

clear
set obs 10
gen byte y = 0
gen double x1 = rnormal()
gen double x2 = rnormal()

cap noi poisson y x1 x2 // error 498
cap noi glm y x1 x2, fam(poisson) ml // error 459
cap noi glm y x1 x2, fam(poisson) irls
cap noi ppmlhdfe y x1 x2, noa // v(1) // we should we giving out error 4
assert c(rc) == 2001

exit
