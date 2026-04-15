noi cscript "ppmlhdfe with offset()" adofile ppmlhdfe
set linesize 150

* Dataset
	sysuse auto
	gen int idx = _n
	gen byte c = 1
	bys turn: gen t = _n
	xtset turn t
	sort turn t idx
	*clonevar y = price


* Comparison list
	loc list_poisson ///
		scalar: N converged ll /// chi2 p ???
		matrix: trim_b trim_V ///
		macros: wexp wtype

	loc list_xtpoisson ///
		scalar: N converged df_m rank /// ll
		matrix: trim_b trim_V ///
		macros: wexp wtype


* [TEST] No absorb
	loc lhs price
	loc rhs weight gear length

	* 1. Run benchmark
	poisson `lhs' `rhs', vce(robust) offset(mpg) tol(1e-12) nrtol(1e-12)
	notrim
 	storedresults save benchmark e()

	* 2. Run ppmlhdfe
	ppmlhdfe `lhs' `rhs', offset(mpg) tol(1e-15) v(-1) noa maxiter(100)
	notrim
	storedresults compare benchmark e(), tol(1e-9) include(`list_poisson')
	assert inrange(e(ic), 1, 1000)
	storedresults drop benchmark


* [TEST] No absorb and frequency weights
* Problem: it seems that there are some accuracy issues in this example
* First, -poisson- is not as accurate as glm
* Second, glm+ml often has convergence issues
* Third, ppmlhdfe seems to have some accuracy issues

	gen double W = foreign + 1

	* 2. Run ppmlhdfe
	ppmlhdfe price weight gear length [fw=W], offset(mpg) //  maxiter(100) v(1) standardize_data(1) // use_exact_solver(1)  v(-1) // min_ok(10) 
	notrim
 	storedresults save ppmlhdfe e()
	assert inrange(e(ic), 1, 1000)

	* 1. Run benchmark
	glm price weight gear length [fw=W], offset(mpg) fam(poi) vce(robust) ml ltol(1e-10) nrtol(1e-10) iterate(20) // might fail to converge!!!
	if (e(converged)) {
		notrim
		storedresults compare ppmlhdfe e(), tol(1e-8) include(scalar: N converged ll macros: wexp wtype)
		storedresults compare ppmlhdfe e(), tol(1e-7) include(matrix: trim_b) // See email to Tom+Paulo 30Jul2019
		storedresults compare ppmlhdfe e(), tol(1e-3) include(matrix: trim_V) // See email to Tom+Paulo 30Jul2019
	}

	glm price weight gear length [fw=W], offset(mpg) fam(poi) vce(robust) ltol(1e-10) irls
	notrim
	storedresults compare ppmlhdfe e(), tol(1e-8) include(scalar: N macros: wexp wtype)
	storedresults compare ppmlhdfe e(), tol(1e-7) include(matrix: trim_b) // See email to Tom+Paulo 30Jul2019
	storedresults compare ppmlhdfe e(), tol(1e-3) include(matrix: trim_V) // See email to Tom+Paulo 30Jul2019

	poisson price weight gear length [fw=W], vce(robust) offset(mpg) tol(1e-12) nrtol(1e-12)
	notrim
	storedresults compare ppmlhdfe e(), tol(1e-8) include(scalar: N macros: wexp wtype)
	storedresults compare ppmlhdfe e(), tol(1e-8) include(matrix: trim_b) // See email to Tom+Paulo 30Jul2019
	storedresults compare ppmlhdfe e(), tol(1e-3) include(matrix: trim_V) // See email to Tom+Paulo 30Jul2019

	storedresults drop ppmlhdfe


* [TEST] As above but min_ok(#) > 1 to check convergence
	* 2. Run ppmlhdfe
	ppmlhdfe price weight gear length [fw=W], offset(mpg) min_ok(5) maxiter(100)
	notrim
 	storedresults save ppmlhdfe e()
	assert inrange(e(ic), 1, 1000)

	* 1. Run benchmark
	glm price weight gear length [fw=W], offset(mpg) fam(poi) vce(robust) ml ltol(1e-10) nrtol(1e-10) iterate(20) // might fail to converge!!!
	if (e(converged)) {
		notrim
		storedresults compare ppmlhdfe e(), tol(1e-8) include(scalar: N converged ll macros: wexp wtype)
		storedresults compare ppmlhdfe e(), tol(1e-8) include(matrix: trim_b) // See email to Tom+Paulo 30Jul2019
		storedresults compare ppmlhdfe e(), tol(1e-8) include(matrix: trim_V) // See email to Tom+Paulo 30Jul2019
	}

	glm price weight gear length [fw=W], offset(mpg) fam(poi) vce(robust) ltol(1e-10) irls
	notrim
	storedresults compare ppmlhdfe e(), tol(1e-8) include(scalar: N macros: wexp wtype)
	storedresults compare ppmlhdfe e(), tol(1e-8) include(matrix: trim_b) // See email to Tom+Paulo 30Jul2019
	storedresults compare ppmlhdfe e(), tol(1e-8) include(matrix: trim_V) // See email to Tom+Paulo 30Jul2019

	poisson price weight gear length [fw=W], vce(robust) offset(mpg) tol(1e-12) nrtol(1e-12)
	notrim
	storedresults compare ppmlhdfe e(), tol(1e-8) include(scalar: N macros: wexp wtype)
	storedresults compare ppmlhdfe e(), tol(1e-8) include(matrix: trim_b) // See email to Tom+Paulo 30Jul2019
	storedresults compare ppmlhdfe e(), tol(1e-8) include(matrix: trim_V) // See email to Tom+Paulo 30Jul2019

	storedresults drop ppmlhdfe


* [TEST] Absorb turn
	loc lhs price
	loc rhs weight gear length
	local K : list sizeof rhs
	loc absvars turn

	* 1. Run benchmark
	poisson `lhs' `rhs' i.`absvars', offset(mpg) vce(robust) tol(1e-10)
	trim_cons `K'
 	storedresults save benchmark e()

	* 2. Run ppmlhdfe
	ppmlhdfe `lhs' `rhs', absorb(`absvars') offset(mpg) tol(1e-10) keepsingletons v(1) // v(-1)
	trim_cons
	storedresults compare benchmark e(), tol(1e-8) include(`list_poisson')
	assert inrange(e(ic), 1, 1000)

exit
