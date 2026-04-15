noi cscript "ppmlhdfe: x2 is normal if y==0 and 0 if y>0" adofile ppmlhdfe
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
generate double y = exp(1+10*x1)*u
generate double x2 = (y==0)


* Comparison list
	loc include_list ///
		scalar: N ll /// chi2 p ???
		matrix: trim_b trim_V ///
		macros: wexp wtype



* Comparison list
	loc alt_include_list ///
		scalar: N ll ///
		matrix: trim_b trim_V ///
		macros: wexp wtype


* [TEST WITH X1]

	* 1. Run benchmark
	poisson y x1, robust
	trim_cons
	storedresults save benchmark e()

	* 2. Run ppmlhdfe
	* WARNING: if we detect separation via IRLS, we get a different e(N) than with poisson
	* This is because of three odd issues:
	* 1) very high stdev of y
	* 2) y has some very low numbers (e.g. 1e-8)
	* 3) a perfect correlation between x1 and y (??)
	* Thus, after standardizing, 1e-8 becomes 0,
	* and x1 is able to perfectly separate all these zeroes
	ppmlhdfe y x1, noa sep(simplex)
	gen sample = e(sample)
	assert sample == 1
	assert e(N_hdfe)==1
	assert e(df_m)==1
	assert inrange(e(ic), 1, 1000)
	trim_cons
	storedresults compare benchmark e(), tol(1e-8) include(`include_list')
	drop sample


/*
* [TEST WITH X1 AND FULL SEP]
	clonevar yy = y
	replace yy = 0 if y < 1e-4

	* 1. Run benchmark
	poisson yy x1, robust tol(1e-12)
	trim_cons
	storedresults save benchmark e()
	ppmlhdfe yy x1, noa tol(1e-12)
	gen sample = e(sample)
	//assert sample == 1 if y > 1e-6
	assert e(N_hdfe)==1
	assert e(df_m)==1
	assert inrange(e(ic), 1, 1000)
	trim_cons
	storedresults compare benchmark e(), tol(1e-8) include(`alt_include_list')
	drop sample
*/

* [TEST WITH X1 AND X2]

	* 1. Run benchmark
	poisson y x1 if y>0, robust iter(20)
	trim_cons 1
	storedresults save benchmark e()

	* 2. Run ppmlhdfe
	ppmlhdfe y x1 x2, noa
	gen sample = e(sample)
	assert sample == y > 0
	assert e(N_hdfe)==1
	assert e(df_m)==1
	assert inrange(e(ic), 1, 1000)
	trim_cons 1
	storedresults compare benchmark e(), tol(1e-8) include(`include_list')

exit

* Let's see how other commands perform:

* X1 only:
poisson y x1 x2, vce(robust) tol(1e-12) iter(50) // ok
glm y x1 x2, iter(50) robust fam(poisson) tol(1e-12) // ok
ppmlhdfe y x1 x2, noa tol(1e-12)
asd
glm y x1 x2, iter(50) robust fam(poisson) irls ltol(1e-12) // fails to converge
ppml y x1 x2, tol(1e-12) // fails to converge


* X1 and X2:

poisson y x1 x2, vce(robust) tol(1e-12) iter(50) // fails to converge
glm y x1 x2, iter(50) robust fam(poisson) tol(1e-12) // converges to wrong result
glm y x1 x2, iter(50) robust fam(poisson) irls ltol(1e-12) // converges to wrong result
ppmlhdfe y x1 x2, noa tol(1e-12) // ok
ppml y x1 x2, tol(1e-12) iter(50) // fails to converge
