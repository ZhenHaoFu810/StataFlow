set more off
clear

** Example 1
webuse ships, clear
*xtpoisson acc op_75_79 co_65_69 co_70_74 co_75_79, exp(service) irr fe nolog

ppmlhdfe acc op_75_79 co_65_69 co_70_74 co_75_79, a(ship) exp(service) irr nolog


** Example 2
ppmlhdfe acc op_75_79 co_65_69, a(ship co_70_74 co_75_79) exp(service) irr nolog


** Example 3
* same as
* ppml_panel_sg trade fta if category == "TOTAL", ex(isoexp) im(isoimp) y(year)

use http://fmwww.bc.edu/RePEc/bocode/e/EXAMPLE_TRADE_FTA_DATA if category=="TOTAL", clear
cap egen imp=group(isoimp)
cap egen exp=group(isoexp)
ppmlhdfe trade fta, a(imp#year exp#year imp#exp) cluster(imp#exp) nolog


** Example 4

use citations_example, clear
estimates clear
ppmlhdfe cit nbaut, a(issn type jel2 pubyear)
eststo
ppmlhdfe cit nbaut, a(issn#c.year type jel2 pubyear)
eststo
ppmlhdfe cit nbaut, a(issn#year type jel2 pubyear)
eststo
estfe *, labels(type "Article type FE" jel2 "JEL code FE" pubyear "Publication year FE" issn "ISSN FE" issn#c.year "Year trend by ISSN" issn#year "ISSN-Year FE")
esttab, indicate(`r(indicate_fe)', labels("Yes" "")) b(3) se(3) varwidth(25) label ///
	stat(N ll, fmt(%12.0fc %13.1fc)) se starlevels(* 0.1 ** 0.05 *** 0.01) compress
exit
