noi cscript "ppmlhdfe - slopes #4" adofile ppmlhdfe
set linesize 150

* Comparison list
	loc list_poisson ///
		scalar: N converged /// ll (why can't we match deviance/ll ?)
		matrix: trim_b trim_V ///
		macros: wexp wtype


// --------------------------------------------------------------------------
// Load data
// --------------------------------------------------------------------------
	use "./datasets/problem6.dta", clear
	recast double y


// --------------------------------------------------------------------------
// Explanation
// --------------------------------------------------------------------------
* At some point in the iteration, the ratio y/mu gets to 1e-15 and the iteration might cycle without converging
* as a solution to that, we replace MUs too close to zero with a value close to machine accuracy (~1e-14)


// --------------------------------------------------------------------------
// Tests
// --------------------------------------------------------------------------

* Benchmark 1
	poisson y x, tol(1e-12) vce(robust)
	notrim
	storedresults save benchmark e()

* Benchmark 2 (does not converge!!!)
*	glm y x, fam(poi) ml ltol(1e-10)
*	notrim
*	storedresults compare benchmark e(), tol(1e-8) include(`list_poisson')

* Benchmark 3 (results slightly off)
*	glm y x, fam(poi) irls ltol(1e-12) vce(robust)
*	notrim
*	storedresults compare benchmark e(), tol(1e-8) include(`list_poisson')

* Test 1
	ppmlhdfe y x, noa maxit(20)
	notrim
	storedresults compare benchmark e(), tol(1e-8) include(`list_poisson')
	// WARNING: We can't match the log-likelihood!! 

* Test 2 (don't standardize data; hidden option)
	ppmlhdfe y x, noa maxit(20) standardize_data(0) v(1)
	notrim
	storedresults compare benchmark e(), tol(1e-8) include(`list_poisson')


storedresults drop benchmark
exit
