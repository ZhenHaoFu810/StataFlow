noi cscript "ppmlhdfe: test against example from JMC Santos Silva & Silvana Tenreyro" adofile ppmlhdfe
set linesize 150

/* Source: 
- Second example from page 3 of http://personal.lse.ac.uk/tenreyro/poisson.pdf

What's going on:
- X2 perfectly predicts when Y==0
- That means that we want to assign a beta of -inf
- So the iteration converges spuriously
*/

drawnorm x1, n(1000) seed(101010) double clear
generate double y = rpoisson(1)
generate double x2 = (y==0)


* Comparison list
	loc include_list ///
		scalar: N ll /// chi2 p ???
		matrix: trim_b trim_V ///
		macros: wexp wtype


* [TEST]

	* 1. Run benchmark
	*poisson y x1 if y > 0, robust
	ppml y x1 x2
	trim_cons 1
	storedresults save benchmark e()

	* 2. Run ppmlhdfe
	ppmlhdfe y x1 x2, noa
	gen sample = e(sample)
	assert sample == (y>0)
	assert e(N_hdfe)==1
	assert e(df_m)==1
	assert inrange(e(ic), 1, 1000)

	trim_cons 1
	storedresults compare benchmark e(), tol(1e-8) include(`include_list')

exit

* Let's see how other commands perform:

ppmlhdfe y x1 x2, noa // ok
glm y x1 x2, robust family(poisson) link(log) ml // b1 ok; b2 converges to incorrect ans
glm y x1 x2, robust family(poisson) link(log) irls // b1 ok; b2 converges to incorrect ans
poisson y x1 x2, vce(robust) tol(1e-10) // b1 kinda ok; b2 converges to incorrect ans
ppml y x1 x2 // ok
