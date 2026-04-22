clear all
set more off

* Use absolute path for the data file
cd "D:\OneDrive - SAIF\PhD3\StataFlow"
use "research/vendor/stata_community/rdrobust/rdrobust-master/stata/rdrobust_senate.dta", clear

* Generate a synthetic covariate correlated with margin
set seed 42
gen z = 0.5 * margin + rnormal(0, 0.3)

* 1. Default bwselect (mserd) without covs
rdrobust vote margin, c(0)
display "tau_cl = " e(tau_cl)
display "tau_bc = " e(tau_bc)
display "se_tau_cl = " e(se_tau_cl)
display "se_tau_rb = " e(se_tau_rb)
display "h_l = " e(h_l)
display "h_r = " e(h_r)
display "b_l = " e(b_l)
display "b_r = " e(b_r)

* 2. bwselect=mserd explicitly
rdrobust vote margin, c(0) bwselect(mserd)
display "tau_cl_mserd = " e(tau_cl)
display "tau_bc_mserd = " e(tau_bc)
display "se_tau_cl_mserd = " e(se_tau_cl)
display "se_tau_rb_mserd = " e(se_tau_rb)

* 3. With covs and explicit h
rdrobust vote margin, c(0) h(15) covs(z)
display "tau_cl_covsh = " e(tau_cl)
display "tau_bc_covsh = " e(tau_bc)
display "se_tau_cl_covsh = " e(se_tau_cl)
display "se_tau_rb_covsh = " e(se_tau_rb)

* 4. With covs and default bwselect
rdrobust vote margin, c(0) covs(z)
display "tau_cl_covs = " e(tau_cl)
display "tau_bc_covs = " e(tau_bc)
display "se_tau_cl_covs = " e(se_tau_cl)
display "se_tau_rb_covs = " e(se_tau_rb)
display "h_l_covs = " e(h_l)
display "h_r_covs = " e(h_r)
