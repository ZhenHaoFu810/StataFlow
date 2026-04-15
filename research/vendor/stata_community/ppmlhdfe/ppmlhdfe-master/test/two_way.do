noi cscript "ppmlhdfe with two FEs" adofile ppmlhdfe
set linesize 150


* Dataset
	sysuse auto
	gen int idx = _n
	gen byte c = 1
	bys turn: gen t = _n
	xtset turn t
	sort turn t idx


* Comparison list
	loc list_poisson ///
		scalar: N converged ll /// chi2 p ???
		matrix: trim_b trim_V ///
		macros: wexp wtype

	loc list_xtpoisson ///
		scalar: N converged df_m rank /// ll
		matrix: trim_b trim_V ///
		macros: wexp wtype


* [TEST] Robust SEs
	
	loc lhs price
	loc rhs weight gear length
	local K : list sizeof rhs
	loc absvars turn trunk

	* 1. Run benchmark
	poisson `lhs' `rhs' i.(`absvars'), vce(robust) tol(1e-12) nrtol(1e-12)
	trim_cons `K'
	storedresults save benchmark e()

	* 2. Run ppmlhdfe
	ppmlhdfe `lhs' `rhs', absorb(`absvars') vce(robust) keepsingletons tol(1e-12)
	notrim
	storedresults compare benchmark e(), tol(1e-8) include(`list_poisson')

exit

* [TEST] Absorb turn; clustered SEs
	
	loc lhs price
	loc rhs weight gear length
	local K : list sizeof rhs
	loc absvars turn

	* 1. Run benchmark
	poisson `lhs' `rhs' i.`absvars', vce(cluster `absvars')
	trim_cons `K'
	storedresults save benchmark e()

	* 2. Run ppmlhdfe
	ppmlhdfe `lhs' `rhs', absorb(`absvars') vce(cluster `absvars') keepsingletons tol(1e-12)
	notrim
	storedresults compare benchmark e(), tol(1e-12) include(`list_poisson')


* [TEST] Absorb turn; clustered SEs against xtpoisson

	loc lhs price
	loc rhs weight gear length
	loc absvars turn

	*poisson `lhs' `rhs' i.`absvars' if !inlist(turn, 31, 32, 39, 51), vce(robust)
	*xi: ppml `lhs' `rhs' i.`absvars' if !inlist(turn, 31, 32, 39, 51)
	*glm `lhs' `rhs' i.`absvars' if !inlist(turn, 31, 32, 39, 51), fam(poisson) vce(robust)

	* 1. Run benchmark
	xtpoisson `lhs' `rhs' if !inlist(turn, 31, 32, 39, 51), fe vce(robust) tol(1e-12) nrtol(1e-12) // vce(robust) is actually vce(cluster turn)
	di e(N_g)
	loc ratio = e(N_g) / (e(N_g)-1)
	notrim `ratio'
	storedresults save benchmark e()

	* 2. Run ppmlhdfe
	ppmlhdfe `lhs' `rhs', absorb(`absvars') vce(cluster turn) tol(1e-12)
	notrim
	storedresults compare benchmark e(), tol(1e-9) include(`list_xtpoisson')

exit
