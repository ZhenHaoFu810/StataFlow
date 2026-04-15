******************************************************************************** 
** RDROBUST Stata Package
** Do-file for Empirical Illustration 
** Authors: Sebastian Calonico, Matias D. Cattaneo, Max H. Farrell and Rocio Titiunik 
********************************************************************************
** hlp2winpdf, cdn(rdrobust) replace
** hlp2winpdf, cdn(rdbwselect) replace
** hlp2winpdf, cdn(rdplot) replace
********************************************************************************
** net install rdrobust, from(https://raw.githubusercontent.com/rdpackages/rdrobust/master/stata) replace
********************************************************************************
clear all
set more off
set linesize 80
mata: mata mlib index

********************************************************************************
** Summary Stats
********************************************************************************
use rdrobust_senate.dta, clear
sum vote margin class termshouse termssenate population, sep(2)

********************************************************************************
** rdplot with confidence intervals
********************************************************************************
rdplot vote margin, binselect(es) ci(95) ///
       graph_options(title("RD Plot: U.S. Senate Election Data") ///
                     ytitle(Vote Share in Election at time t+1) ///
                     xtitle(Vote Share in Election at time t) ///
                     graphregion(color(white)))

**************************************************************************
** rdplot with MSE-optimal choice
**************************************************************************
rdplot vote margin, binselect(es) ///
       graph_options(title(RD Plot - Senate Elections Data) ///
                           ytitle(Vote Share in Election at time t+1) ///
                           xtitle(Vote Share in Election at time t))

**************************************************************************
** rdplot with QS partitioning and mimicking variance choice
**************************************************************************
rdplot vote margin, binselect(qsmv)  ///
		graph_options(title(RD Plot - Senate Elections Data) ///
                      ytitle(Vote Share in Election at time t+1) ///
                      xtitle(Vote Share in Election at time t))

**************************************************************************
** rdrobust
**************************************************************************
rdrobust vote margin

**************************************************************************
** rdrobust with all estimates
**************************************************************************
rdrobust vote margin, all

**************************************************************************
** rdbwselect with all estimates
**************************************************************************
rdbwselect vote margin, all
					 
********************************************************************************
** rdrobust backward compatibility
********************************************************************************
rdrobust vote margin, h(16.79369) b(27.43745)

********************************************************************************
** rdplot to show rdrobust estimate
********************************************************************************
qui rdrobust vote margin
rdplot vote margin if -e(h_l)<= margin & margin <= e(h_r), ///
       binselect(esmv) kernel(triangular) h(`e(h_l)' `e(h_r)') p(1) ///
       graph_options(title("RD Plot: U.S. Senate Election Data") ///
                     ytitle(Vote Share in Election at time t+2) ///
                     xtitle(Vote Share in Election at time t) ///
                     graphregion(color(white)))

********************************************************************************
** rdrobust with covariates within the same window (i.e., using same bandwidths)
********************************************************************************
qui rdrobust vote margin
local len = `e(ci_r_rb)' - `e(ci_l_rb)'
rdrobust vote margin, covs(class termshouse termssenate) ///
         h(`e(h_l)' `e(h_r)') b(`e(b_l)' `e(b_r)')
display "CI length change: " round(((`e(ci_r_rb)'-`e(ci_l_rb)')/`len'-1)*100,.01) "%"

********************************************************************************
** rdrobust with covariates with data-driven optimal bandwidths
********************************************************************************
qui rdrobust vote margin
local len = `e(ci_r_rb)' - `e(ci_l_rb)'
rdrobust vote margin, covs(class termshouse termssenate)
display "CI length change: " round(((`e(ci_r_rb)'-`e(ci_l_rb)')/`len'-1)*100,.01) "%"

********************************************************************************
** rdrobust with useless covariate
********************************************************************************
qui rdrobust vote margin
local len = `e(ci_r_rb)' - `e(ci_l_rb)'
rdrobust vote margin, covs(population)
display "CI length change: " round(((`e(ci_r_rb)'-`e(ci_l_rb)')/`len'-1)*100,.01) "%"

********************************************************************************
** rdrobust check covariate "balanced"
********************************************************************************
local covs "class termshouse termssenate population"
local num: list sizeof covs
mat balance = J(`num',2,.)
local row = 1
foreach z in `covs' {
    qui rdrobust `z' margin
	mat balance[`row',1] = round(e(tau_cl),.001)
	mat balance[`row',2] = round(e(pv_rb),.001)
	local ++row
}
mat rownames balance = `covs'
mat colnames balance = "RD Effect" "Robust p-val"
mat lis balance

********************************************************************************
** rdrobust with clustering
********************************************************************************
rdrobust vote margin, vce(nncluster state)

********************************************************************************
** rdrobust with clustering and covariates, and different bandwidth
********************************************************************************
rdrobust vote margin, covs(class termshouse termssenate) ///
                      bwselect(msetwo) vce(nncluster state) 

********************************************************************************
** rdbwselect with all estimates
********************************************************************************
rdbwselect vote margin, all

********************************************************************************
** Other examples
********************************************************************************
rdrobust vote margin, kernel(uniform) vce(cluster state)

rdrobust vote margin, bwselect(certwo) vce(hc3)

rdrobust vote margin, h(12 15) b(18 20)

rdrobust vote margin, covs(class) bwselect(cerrd) scaleregul(0) rho(1)

rdbwselect vote margin, kernel(uniform) vce(cluster state) all

rdbwselect vote margin, covs(class) bwselect(msetwo) vce(hc2) all



