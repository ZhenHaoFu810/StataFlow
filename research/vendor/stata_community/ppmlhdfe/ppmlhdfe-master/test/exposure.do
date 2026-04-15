noi cscript "ppmlhdfe with exposure()" adofile ppmlhdfe
set linesize 150

* Dataset
	sysuse auto
	gen int idx = _n
	gen byte c = 1
	sort turn, stable
	by turn: gen t = _n
	xtset turn t
	sort turn t idx, stable
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
	loc absvars c

	* 1. Run benchmark
	poisson `lhs' `rhs', vce(robust) exposure(head) tol(1e-12) nrtol(1e-14)
	notrim
 	storedresults save benchmark e()

	* 2. Run ppmlhdfe
	ppmlhdfe `lhs' `rhs', noa exposure(head) tol(1e-12)
	notrim
	storedresults compare benchmark e(), tol(1e-9) include(`list_poisson')
	assert inrange(e(ic), 1, 1000)


* [TEST] Absorb turn
	loc lhs price
	loc rhs weight gear length
	local K : list sizeof rhs
	loc absvars turn

	* 1. Run benchmark
	poisson `lhs' `rhs' i.`absvars', exposure(head) vce(robust) tol(1e-10)
	trim_cons `K'
 	storedresults save benchmark e()

	* 2. Run ppmlhdfe
	ppmlhdfe `lhs' `rhs', absorb(`absvars') exposure(head) tol(1e-10) keepsingletons v(-1)
	trim_cons
	storedresults compare benchmark e(), tol(1e-8) include(`list_poisson')
	assert inrange(e(ic), 1, 1000)

exit
