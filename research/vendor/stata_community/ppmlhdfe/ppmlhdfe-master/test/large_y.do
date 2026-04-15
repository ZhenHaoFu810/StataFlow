noi cscript "ppmlhdfe: y takes large values" adofile ppmlhdfe
set linesize 150

/* all work correctly */

drawnorm u x1 x2, n(1000) seed(101010) double clear
generate double y = exp(40+x1+x2+u)


* Comparison list
	loc include_list ///
		scalar: N ll /// chi2 p ???
		matrix: trim_b trim_V ///
		macros: wexp wtype


* [TEST]

	* 1. Run benchmark
	poisson y x1 x2, vce(robust)
	notrim
	storedresults save benchmark e()

	* 2. Run ppmlhdfe
	ppmlhdfe y x1 x2, noa tol(1e-10)
	gen sample = e(sample)
	assert sample == 1
	assert e(N_hdfe)==1
	assert e(df_m)==2
	assert inrange(e(ic), 1, 1000)
	notrim
	storedresults compare benchmark e(), tol(1e-8) include(`include_list')

exit

* Let's see how other commands perform:

poisson y x1 x2, vce(robust) difficult
glm y x1 x2, robust family(poisson) link(log) irls
ppml y x1 x2
ppmlhdfe y x1 x2, noa
