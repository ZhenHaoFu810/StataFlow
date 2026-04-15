noi cscript "ppmlhdfe: test against prob3 dataset" adofile ppmlhdfe
set linesize 150

/* DATASET: Risk of false positives

See: https://github.com/sergiocorreia/ppml_hdfe_demo/issues/3#issuecomment-328999264

We shouldn't drop any variable or obs.
*/

clear
input double y byte(x1 x2 x3)
        0 0 0 1
        0 0 0 1
        0 0 0 2
2.2596662 1 1 2
2.4177196 2 2 2
0.9788354 3 2 1
2.6114680 4 2 1
end

* Comparison list
	loc list_poisson ///
		scalar: N converged ll /// chi2 p ???
		matrix: trim_b trim_V ///
		macros: wexp wtype

	loc list_xtpoisson ///
		scalar: N converged df_m rank /// ll
		matrix: trim_b trim_V ///
		macros: wexp wtype


* [TEST]

	* 1. Run benchmark
	poisson y x*, robust tol(1e-12)
	trim_cons
	storedresults save benchmark e()

	* 2. Run ppmlhdfe
	ppmlhdfe y x*, noa tol(1e-12)
	gen sample = e(sample)
	assert e(N_hdfe)==1
	assert e(df_a)==1
	assert sample==1
	assert e(df_m)==3
	assert inrange(e(ic), 1, 1000)

	trim_cons
	storedresults compare benchmark e(), tol(1e-7) include(`list_poisson')

exit

* Let's see how other commands perform:

ppml y x* // drops x1 x2
poisson y x* // ok
glm y x*, fam(poisson) irls // ok
glm y x*, fam(poisson) ml // ok
