noi cscript "ppmlhdfe with factor and time-series variables" adofile ppmlhdfe
set linesize 150

* Dataset
	sysuse auto
	sort turn, stable // Else we could get random errors
	by turn: gen t = _n
	xtset turn t


* Comparison list
	loc include_list ///
		scalar: N converged ll /// chi2 p ???
		matrix: trim_b trim_V ///
		macros: wexp wtype
//		scalar: ll deviance /// chi2 p ???
//		matrix: ///
//		macros:


* [TEST] No absorb
	drop if mi(rep)
	set seed 123

	* 1. Run benchmark
	glm L.price i.foreign#i.rep S.L.F1.(weight gear) , vce(robust) fam(poi) tol(1e-14)
	notrim
	storedresults save benchmark e()

	* 2. Run ppmlhdfe
	ppmlhdfe L.price i.foreign#i.rep S.L.F1.(weight gear) , noa tol(1e-12)
	notrim
	storedresults compare benchmark e(), tol(1e-8) include(`include_list')
	assert inrange(e(ic), 1, 1000)


* [TEST] Absorb turn

	* 1. Run benchmark
	glm L.price i.foreign#i.rep S.L.F1.(weight gear) i.turn, vce(robust) fam(poi) tol(1e-12)
	trim_cons 12
	matrix list e(trim_b)
	storedresults save benchmark e()

	* 2. Run ppmlhdfe
	ppmlhdfe L.price i.foreign#i.rep S.L.F1.(weight gear) , a(turn) keepsing v(-1) tol(1e-12)
	trim_cons
	storedresults compare benchmark e(), tol(1e-8) include(`include_list')
	assert inrange(e(ic), 1, 1000)

exit
