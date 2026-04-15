noi cscript "ppmlhdfe: test against example from JMC Santos Silva & Silvana Tenreyro" adofile ppmlhdfe
set linesize 150

/* Source: 
- Example in page 3 of http://personal.lse.ac.uk/tenreyro/poisson.pdf

What's going on:
- X2 perfectly predicts when Y==0
- That means that we want to assign a beta of -inf
- So the iteration never converges
*/


drawnorm x1, n(1000) seed(101010) double clear
generate double u = rpoisson(1)
generate y = exp(1+10*x1)*u
generate double x2 = (y==0)


* Comparison list
	loc include_list ///
		scalar: N ll /// chi2 p ???
		matrix: trim_b trim_V ///
		macros: wexp wtype



* [TEST]

	* 0. Other variants that should give the same result
	poisson y x1 if y > 0, robust iter(20)
	di %10.2fc  -e(ll) - 1349028900000

	ppmlhdfe y x1 if y > 0
	di %10.2fc  -e(ll) - 1349028900000
	
	ppmlhdfe y x1 if y > 0, standardize_data(0)
	di %10.2fc  -e(ll) - 1349028900000

	ppmlhdfe y x1 x2, standardize_data(0)
	di %10.2fc  -e(ll) - 1349028900000
	
	* 1. Run benchmark
	glm y x1 if y > 0, fam(poi) link(log) robust iter(20) // e(ll) = -1349028940661
	di %10.2fc  -e(ll) - 1349028900000

	trim_cons 1
	storedresults save benchmark e()

	* 2. Run ppmlhdfe
	ppmlhdfe y x1 x2, noa maxiter(100) min_ok(1) // e(ll) = -1349028910515
	di %10.2fc  -e(ll) - 1349028900000
	gen sample = e(sample)
	assert sample == (y>0)
	assert e(N_hdfe)==1
	assert e(df_m)==1
	assert inrange(e(ic), 1, 1000)

	trim_cons 1
	storedresults compare benchmark e(), tol(1e-8) include(`include_list')

exit

* Let's see how other commands perform:

ppmlhdfe y x1 x2, noa
glm y x1 x2, robust family(poisson) link(log) ml // converges to incorrect  beta2
glm y x1 x2, robust family(poisson) link(log) irls // converges to incorrect  beta2
poisson y x1 x2, vce(robust) // fails
ppml y x1 x2 // fails
