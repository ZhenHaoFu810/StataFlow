clear all
set more off
webuse ships, clear
ppmlhdfe accident service, absorb(ship) exposure(service) vce(robust)
matrix V = e(V)
matrix list V
display "V11=" V[1,1]
display "V12=" V[1,2]
display "V22=" V[2,2]
