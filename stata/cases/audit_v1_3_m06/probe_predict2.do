clear all
set more off
webuse ships, clear
ppmlhdfe accident co_65_69 co_70_74 co_75_79 op_75_79, absorb(ship) exposure(service) vce(robust) d
capture drop __mu
predict double __mu, mu
summarize __mu
capture drop __r
predict double __r, r
summarize __r
capture drop __pearson
predict double __pearson, pearson
summarize __pearson
capture drop __dev
predict double __dev, deviance
summarize __dev
