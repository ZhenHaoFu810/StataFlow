noi cscript "ppmlhdfe: simplest call" adofile ppmlhdfe
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
		matrix: trim_b trim_V ///
		macros: wexp wtype ///
		scalar: N converged ll ll_0 r2_p // deviance  // chi2

	loc list_glm_ml ///
		matrix: trim_b trim_V ///
		macros: wexp wtype ///
		scalar: N converged ll deviance // ll_0 r2_p // chi2

	loc list_glm_irls ///
		matrix: trim_b trim_V ///
		macros: wexp wtype ///
		scalar: N deviance // ll_0 r2_p converged ll chi2


* [TEST] No absorb
	ppmlhdfe price weight length gear , noa
	notrim
	assert e(df_r) == .
	assert e(r2) == .
	storedresults save answer e()

	poisson price weight length gear, vce(rob)
	notrim
	assert e(df_r) == .
	assert e(r2) == .
	storedresults compare answer e(), tol(1e-8) include(`list_poisson' chi2)

	glm price weight length gear, vce(rob) fam(poi) ml
	notrim
	assert e(df_r) == .
	assert e(r2) == .
	storedresults compare answer e(), tol(1e-8) include(`list_glm_ml' chi2)

	glm price weight length gear, vce(rob) fam(poi) irls
	notrim
	assert e(df_r) == .
	assert e(r2) == .
	storedresults compare answer e(), tol(1e-8) include(`list_glm_irls')



* [TEST] Absorb
	ppmlhdfe price weight length gear , a(turn) keepsing
	loc chi2 = e(chi2)
	trim_cons
	assert e(df_r) == .
	assert e(r2) == .
	storedresults save answer e()

	poisson price weight length gear i.turn, vce(rob)
	trim_cons 3
	assert e(df_r) == .
	assert e(r2) == .
	storedresults compare answer e(), tol(1e-8) include(`list_poisson')
	test weight length gear
	assert abs(`chi2' - r(chi2)) < 1e-6

	glm price weight length gear i.turn, vce(rob) fam(poi) ml
	trim_cons 3
	assert e(df_r) == .
	assert e(r2) == .
	storedresults compare answer e(), tol(1e-8) include(`list_glm_ml')
	test weight length gear
	assert abs(`chi2' - r(chi2)) < 1e-6

	glm price weight length gear i.turn, vce(rob) fam(poi) irls
	trim_cons 3
	assert e(df_r) == .
	assert e(r2) == .
	storedresults compare answer e(), tol(1e-8) include(`list_glm_irls')
	test weight length gear
	assert abs(`chi2' - r(chi2)) < 1e-6


storedresults drop answer
exit
