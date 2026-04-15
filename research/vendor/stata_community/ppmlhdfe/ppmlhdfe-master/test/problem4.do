noi cscript "ppmlhdfe: test against prob2 dataset" adofile ppmlhdfe
set linesize 150

/* DATASET: Risk of false negatives

See: https://github.com/sergiocorreia/ppml_hdfe_demo/issues/3#issuecomment-328999264

We should drop some vars that we aren't dropping
*/

clear
input double y byte(x1 x2 x3)
  0  2 3 4
  0 -5 0 1
  0  0 2 1
  0  0 0 3
  0 -2 0 1
  0  0 0 2
1.1  1 1 2
 .5  2 2 2
3.3  3 3 2
2.1  4 2 4
end

// z shows the perfect collinearity when y>0
gen double z = x1 - x2 - x3 + 2
li z x*

// we can also see that in the regression
reg x1 x2 x3 if y>0 // , nocons NOT SURE... we can't add a constant!

// note that even if x has ok values when y==0, resid_x will lead to complete separation of obs 1 to 5
predict resid, resid
gen split = y==0
li resid x* y, sepby(split)

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
	poisson y x1 x2 in 6/10, robust tol(1e-12)
	trim_cons
	storedresults save benchmark e()

	* 2. Run ppmlhdfe
	ppmlhdfe y x*, noa tol(1e-12) maxiter(200)
	gen sample = e(sample)
	assert e(N_hdfe)==1
	assert e(df_a)==1
	assert sample == (_n > 5)
	assert e(df_m)==2
	assert inrange(e(ic), 1, 1000)

	trim_cons 2
	storedresults compare benchmark e(), tol(1e-7) include(`list_poisson')

exit

* Let's see how other commands perform:

ppml y x* // fails to converge
ppmlhdfe y x*, noa // ok
ppmlhdfe y x*, noa olsguess  // ok
poisson y x* // fails to converge
glm y x*, fam(poisson) irls // fails to converge
glm y x*, fam(poisson) ml // fails to converge
