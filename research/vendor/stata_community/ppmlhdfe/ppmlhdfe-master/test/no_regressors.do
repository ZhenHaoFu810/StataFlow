noi cscript "ppmlhdfe with no regressors" adofile ppmlhdfe
set linesize 150

* Dataset
	sysuse auto

* Comparison list
	loc include_list ///
		scalar: ll deviance /// chi2 p ???
		matrix: ///
		macros:

* [TEST] No absorb

	* 1. Run benchmark
	glm price, vce(robust) fam(poisson)
	storedresults save benchmark e()

	* 2. Run ppmlhdfe
	ppmlhdfe price, noabsorb
	storedresults compare benchmark e(), tol(1e-8) include(`include_list')
	assert inrange(e(ic), 1, 1000)


* [TEST] Absorb turn

	* 1. Run benchmark
	glm price i.turn, fam(poisson) ltol(1e-12)
	storedresults save benchmark e()

	* 2. Run ppmlhdfe
	ppmlhdfe price, a(turn) tol(1e-12) v(-1) keepsingletons
	storedresults compare benchmark e(), tol(1e-8) include(`include_list')
	assert inrange(e(ic), 1, 1000)

exit
