*set linesize 150
*cap ado uninstall ppmlhdfe
*net install ppmlhdfe, from(C:\Git\ppml_hdfe_demo\src)
*discard
*clear all
*pr drop _all
*cls

noi cscript "ppmlhdfe: simplest call" adofile ppmlhdfe
set linesize 150


* Dataset
	sysuse auto
	gen byte c = 1


* Comparison list
	loc list_poisson ///
		scalar: N converged ll /// chi2 p ???
		matrix: trim_b trim_V ///
		macros: wexp wtype


* [TEST] Trivial case with pweights of 1 (should match case w/out weights)

	loc lhs price
	loc rhs weight gear length

	* 1. Run benchmark
	poisson `lhs' `rhs' [pw=c], vce(robust)
	notrim
	storedresults save benchmark e()

	* 2. Run ppmlhdfe
	ppmlhdfe `lhs' `rhs' [pw=c], noabsorb // accel_skip(0)
	notrim
	storedresults compare benchmark e(), tol(1e-8) include(`list_poisson')
	assert inrange(e(ic), 1, 1000)


* [TEST] pweight with noabsorb
	loc lhs price
	loc rhs weight gear length

	* 1. Run benchmark
	poisson `lhs' `rhs' [pw=displacement], vce(robust)
	notrim
	storedresults save benchmark e()

	* 2. Run ppmlhdfe
	ppmlhdfe `lhs' `rhs' [pw=disp], noabsorb // accel_skip(0)
	notrim
	storedresults compare benchmark e(), tol(1e-8) include(`list_poisson')
	assert inrange(e(ic), 1, 1000)


* [TEST] pweight with noabsorb and clustered SEs
	loc lhs price
	loc rhs weight gear length

	* 1. Run benchmark
	poisson `lhs' `rhs' [pw=displacement], vce(cluster turn)
	notrim
	storedresults save benchmark e()

	* 2. Run ppmlhdfe
	ppmlhdfe `lhs' `rhs' [pw=disp], noabsorb vce(cluster turn)
	notrim
	storedresults compare benchmark e(), tol(1e-8) include(`list_poisson')
	assert inrange(e(ic), 1, 1000)


* [TEST] pweight absorbing turn
	loc lhs price
	loc rhs weight gear length

	* 1. Run benchmark
	poisson `lhs' `rhs' i.turn [pw=displacement], vce(robust)
	trim_cons 3
	storedresults save benchmark e()

	* 2. Run ppmlhdfe
	ppmlhdfe `lhs' `rhs' [pw=disp], a(turn) keepsing v(-1)
	trim_cons
	storedresults compare benchmark e(), tol(1e-8) include(`list_poisson')
	assert inrange(e(ic), 1, 1000)


exit
