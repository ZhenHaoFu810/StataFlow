noi cscript "ppmlhdfe: x1 and x2 are _almost_ collinear" adofile ppmlhdfe
set linesize 150

/* Here, only ppmlhdfe and poi2hdfe work correctly */

drawnorm u e x1, n(1000) seed(101010) double clear
generate double x2 = (x1+e/18000)
generate double y = exp(1+x1+x2+u)


* Comparison list
	loc include_list ///
		scalar: N /// chi2 p ???
		matrix: trim_b trim_V ///
		macros: wexp wtype


* [TEST]

	* 1. Run benchmark
	gen byte c1 = 1
	gen byte c2 = 1
	poi2hdfe y x1 x2, id1(c1) id2(c2) tol1(1e-10) tol2(1e-8) // slow
	notrim `=997/998' // there are not really two FEs; fix the DOF
	matrix list e(trim_b)
	storedresults save benchmark e()

	* 2. Run ppmlhdfe
	ppmlhdfe y x1 x2, noa tol(1e-12)
	gen sample = e(sample)
	assert sample == 1
	assert e(N_hdfe)==1
	*assert e(N_hdfe)==2
	assert e(df_m)==2
	assert inrange(e(ic), 1, 1000)

	notrim
	matrix list e(trim_b)
	// not an exact match..
	storedresults compare benchmark e(), tol(1e-6) include(`include_list')

exit

* Let's see how other commands perform:

ppmlhdfe y x1 x2, noa // works?
poisson y x1 x2, vce(robust) iter(50) // fails
poisson y x1 x2, vce(robust) difficult iter(50) // fails
glm y x1 x2, robust family(poisson) iter(50) irls // kinda correct betas, no SEs
glm y x1 x2, robust family(poisson) iter(50) ml // fails
ppml y x1 x2, technique(bfgs) // fails

* This workaround works:
gen double z2 = x2 - x1
ppmlhdfe y x1 z2, noa
