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


* [TEST 1] Trivial case with fweights of 1 (should match case w/out weights)

	loc lhs price
	loc rhs weight gear length

	* 1. Run benchmark
	poisson `lhs' `rhs' [fw=c], vce(robust)
	notrim
	storedresults save benchmark e()

	* 2. Run ppmlhdfe
	ppmlhdfe `lhs' `rhs' [fw=c], noabsorb // accel_skip(0)
	notrim
	storedresults compare benchmark e(), tol(1e-8) include(`list_poisson')
	assert inrange(e(ic), 1, 1000)


* [TEST 2] fweight with noabsorb
	loc lhs price
	loc rhs weight gear length

	* 1. Run benchmark
	poisson `lhs' `rhs' [fw=displacement], vce(robust)
	matrix list e(V), format(%16.8f)
	notrim
	storedresults save benchmark e()

	* 2. Run ppmlhdfe
	ppmlhdfe `lhs' `rhs' [fw=disp], noabsorb // accel_skip(0)
	matrix list e(V), format(%16.8f)
	notrim
	storedresults compare benchmark e(), tol(1e-8) include(`list_poisson')
	assert inrange(e(ic), 1, 1000)


* [TEST 3a] fweight with noabsorb and clustered SEs
	loc lhs price
	loc rhs weight gear length

	* 1. Run benchmark
	poisson `lhs' `rhs' [fw=displacement], vce(cluster turn)
	notrim
	storedresults save benchmark e()

	* 2. Run ppmlhdfe
	ppmlhdfe `lhs' `rhs' [fw=disp], noabsorb vce(cluster turn)
	notrim
	storedresults compare benchmark e(), tol(1e-8) include(`list_poisson')
	assert inrange(e(ic), 1, 1000)


* [TEST 3b] fweight with noabsorb and clustered SEs
	loc lhs price
	loc rhs weight gear length

	* 1. Run benchmark
	poisson `lhs' `rhs' [fw=turn], vce(cluster trunk)
	notrim
	storedresults save benchmark e()

	* 2. Run ppmlhdfe
	ppmlhdfe `lhs' `rhs' [fw=turn], noabsorb vce(cluster trunk)
	notrim
	storedresults compare benchmark e(), tol(1e-8) include(`list_poisson')
	assert inrange(e(ic), 1, 1000)


* [TEST 3c] fweight with noabsorb and clustering by _n
	loc lhs price
	loc rhs weight gear length

	* 1. Run benchmark
	gen double i = _n
	poisson `lhs' `rhs' [fw=turn], vce(cluster i)
	notrim
	storedresults save benchmark e()

	* 2. Run ppmlhdfe
	ppmlhdfe `lhs' `rhs' [fw=turn], noabsorb vce(cluster i)
	notrim
	storedresults compare benchmark e(), tol(1e-8) include(`list_poisson')
	assert inrange(e(ic), 1, 1000)


* [TEST 4] fweight absorbing turn
	loc lhs price
	loc rhs weight gear length

	* 1. Run benchmark
	poisson `lhs' `rhs' i.turn [fw=displacement], vce(robust)
	trim_cons 3
	storedresults save benchmark e()

	* 2. Run ppmlhdfe
	ppmlhdfe `lhs' `rhs' [fw=disp], a(turn) keepsing v(-1)
	trim_cons
	storedresults compare benchmark e(), tol(1e-8) include(`list_poisson')
	assert inrange(e(ic), 1, 1000)


exit
