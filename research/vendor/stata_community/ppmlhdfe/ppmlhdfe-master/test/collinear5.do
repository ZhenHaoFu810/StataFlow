noi cscript "ppmlhdfe: check case where x2 is always zero" adofile ppmlhdfe
set linesize 150

/* Ensure that a simple collinearity case is correctly dropped

- ppml, glm_ml fail
- poisson, glm_irls ok

- glm_ml fails b/c of a ridge, so the LogL is the same for several values of x1
- not sure why ppml fails, but with the -technique(bfgs)- option it works (and only with that one)
*/

drawnorm x1, n(1000) seed(101010) double clear
generate double u = rpoisson(1)
generate y = exp(1+10*x1)*u
generate double x2 = 0


* Comparison list
	loc include_list ///
		scalar: N ll /// chi2 p ???
		matrix: trim_b trim_V ///
		macros: wexp wtype


* [TEST]

	* 1. Run benchmark
	poisson y x1 x2, robust
	trim_cons 1
	storedresults save benchmark e()

	* 2. Run ppmlhdfe
	ppmlhdfe y x1 x2, noa sep(simplex)
	gen sample = e(sample)
	assert sample == 1
	assert e(N_hdfe)==1
	assert e(df_m)==1
	assert inrange(e(ic), 1, 1000)

	trim_cons 1
	storedresults compare benchmark e(), tol(1e-8) include(`include_list')

exit

* Let's see how other commands perform:

ppmlhdfe y x1 x2, noa
glm y x1 x2, robust family(poisson) link(log) iter(50) ml // fails
glm y x1 x2, robust family(poisson) link(log) iter(50) irls // ok!
poisson y x1 x2, vce(robust) iter(50) // ok!
cap noi ppml y x1 x2, iter(50) // fails
ppml y x1 x2, technique(bfgs) // ok
