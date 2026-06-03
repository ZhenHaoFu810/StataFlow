clear all
set more off

use "D:\OneDrive - SAIF\PhD3\StataFlow\research\data\public\did\ezunem_prepared.dta", clear

csdid uclms c1 c2 c3, ivar(city) time(year) gvar(first_treat) method(drimp)

csdid_estat event

matrix b = e(b)
matrix V = e(V)
local names : colfullnames b
local i = 1
foreach name of local names {
    display "B_`name'=" b[1, `i']
    display "SE_`name'=" sqrt(V[`i', `i'])
    local ++i
}

display "E_N=" e(N)
display "CSDID_DR_EZUNEM_OK"
