noi cscript "ppmlhdfe - extreme case test" adofile ppmlhdfe
set linesize 150

* Comparison list
loc include ///
	scalar: converged deviance // ll  (can't include logl due to different number of obs.)


clear
set obs 100
set seed 12345
gen int id1 = ceil(_n/3)
gen int id2 = ceil(cond(_n==1,_N,_n-1)/3)
gen int y = runiform() < 0.1
li in 1/5
li in `=c(N)-5'/l

// ??
//ppmlhdfe y, a(id1 id2, prune)

ppmlhdfe y, a(id1 id2)
storedresults save editmu e()

*ppmlhdfe y, a(id1 id2, prune) // converges slowly
*poisson y i.id1 i.id2, vce(robust) // doesn't work
* glm doesn't work due to a Stata bug

ppmlhdfe y ibn.id1 i.id2, noa
storedresults compare editmu e(), tol(1e-8) include(`include')


exit




loc include ///
	scalar: converged ll deviance /// chi2 p ???


// Not working???
//ppmlhdfe y, a(id1 id2, maxiter(100) prune) maxiter(100)
//loc n_prune = e(N)
//storedresults save prune e()
//di e(deviance)

ppmlhdfe y, a(id1 id2, maxiter(100)) maxiter(100) editmu
loc n_editmu = e(N)
storedresults save editmu e()
di e(deviance)


ppmlhdfe y ibn.id1 ibn.id2, noa maxiter(100)
di e(deviance)

//assert e(N) == `n_prune' - 1
//storedresults compare prune e(), tol(1e-8) include(`include')

assert e(N) == `n_editmu' - 1
storedresults compare editmu e(), tol(1e-8) include(`include')

assert inrange(e(ic), 1, 1000)

// Another benchmark
glm y ibn.id1 ibn.id2, vce(robust) fam(poisson) irls


// --------------------------------------------------------------------------
// Case 2
// --------------------------------------------------------------------------
