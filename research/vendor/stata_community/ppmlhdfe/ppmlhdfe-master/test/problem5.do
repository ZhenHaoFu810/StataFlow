noi cscript "ppmlhdfe: test against another prob dataset" adofile ppmlhdfe
set linesize 150

/* DATASET: Risk of false positives

See: https://github.com/sergiocorreia/ppml_hdfe_demo/issues/3#issuecomment-329200920
*/

clear
input float(y x1 x2 i j)
2 0 0 2 1
1 0 1 4 3
2 0 1 2 2
1 1 0 2 2
0 1 0 1 2
1 2 0 1 3
1 0 0 2 1
2 1 0 2 3
0 1 0 2 2
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

	gen byte smpl = (i != 4) & (_n != 5) & (i!=1) & (j != 3)
	* i==4 is singleton
	* afterwards, the other regressors can combine with x2 to separate y==0 at _n==5
	* then, i==1 and j==3 become singletons

	* 1. Run benchmark
	poisson y x1  i.i i.j if smpl, robust tol(1e-12)
	trim_cons 1
	storedresults save benchmark e()

	* 2. Run ppmlhdfe
	ppmlhdfe y x1 x2, a(i j) tol(1e-12) maxiter(20)
	assert smpl == e(sample)
	assert e(N_hdfe)==2
	assert e(df_a)==2
	assert e(df_m)==1
	assert inrange(e(ic), 1, 1000)

	trim_cons 1
	storedresults compare benchmark e(), tol(1e-7) include(`list_poisson')

exit

* Let's see how other commands perform:

ppml y x* // drops x1 x2
poisson y x* // ok
glm y x*, fam(poisson) irls // ok
glm y x*, fam(poisson) ml // ok
