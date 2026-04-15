noi cscript "ppmlhdfe: test against collinear.dta" adofile ppmlhdfe
set linesize 150

/* DATASET: Tom or Paulo's?
- z is perfectly predicted by the FEs when y > 0
- ppml.ado gives the correct answer, but poisson and glm fail
*/

use "datasets/collinear", clear

* Comparison list
	loc include_list ///
		scalar: N ll /// chi2 p ???
		matrix: trim_b trim_V ///
		macros: wexp wtype


* [TEST]

	* 1. Run benchmark
	xi: ppml y x z i.im i.ex
	drop _I*
	trim_cons 1
	storedresults save benchmark e()

	* 2. Run ppmlhdfe
	ppmlhdfe y x z, a(im ex)
	gen sample = e(sample)
	assert sample == (z!=1)
	assert e(N_hdfe)==2
	assert e(df_m)==1
	assert inrange(e(ic), 1, 1000)

	trim_cons 1
	storedresults compare benchmark e(), tol(1e-8) include(`include_list')

exit

* Let's see how other commands perform:

xi: ppml y x z i.im i.ex
ppmlhdfe y x z, a(im ex)
poisson y x z i.im i.ex, robust
glm y x z i.im i.ex, robust family(poisson) link(log) irls
glm y x z i.im i.ex, robust family(poisson) link(log) ml
