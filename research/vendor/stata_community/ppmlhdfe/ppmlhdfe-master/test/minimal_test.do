cls
* Install and test that it runs (not that it is correct)
clear all
reghdfe, reload
*cap ado uninstall ftools
*net install ftools, from("C:/git/ftools/src")


cap ado uninstall ppmlhdfe
net install ppmlhdfe, from("C:/Git/ppml_hdfe_demo/src")
pr drop _all



sysuse auto, clear
ppmlhdfe price weight length, a(turn foreign)
estat ic
*ereturn list
exit


insheet using "separation_datasets/07.csv", clear comma names double
ppmlhdfe y x1 x2, a(turn)
// fe simplex relu mu
*ppmlhdfe y x1 x2, noa sep(relu) v(0) tagsep(sep_relu) zvar(z) r2

ppmlhdfe y x1 x2, a(id1 id2) sep(relu) v(0) tagsep(sep_relu) zvar(z) r2
//gen sep_relu = !e(sample)
tab sep_relu separated


exit











exit

sysuse auto
sort turn
replace price = 0 in 1/20

cls
*ppmlhdfe, version
*exit

reghdfe price weight length, a(turn)
keep if e(sample)

set trace off
ppmlhdfe price weight length, a(turn) guess(ols) mu_tol(1e-6) accel_start(7) v(1) septol(is_)
