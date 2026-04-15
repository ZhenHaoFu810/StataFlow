noi cscript "ppmlhdfe - extreme case test" adofile ppmlhdfe
set linesize 150

loc include_list ///
	scalar: N ll ///
	matrix: /// trim_b trim_V
	macros: wexp wtype


clear
input byte(y id1 id2)
0 1 1
1 1 1
0 2 1
0 2 2
1 2 2
end

* A combination of ID2 and ID1 perfectly separates Y (obs #3)
*gen double z = id1 - id2
gen double z = (id2==1) - (id1==1)
li y z if y==0
li y z if y>0

loc include ///
	scalar: converged ll deviance /// chi2 p ???

* Benchmark
poisson y i.id1 i.id2 if _n!=3 , tol(1e-12)
storedresults save benchmark e()

* NOT WORKING!
* * A) PRUNE
* ppmlhdfe y, a(id1 id2, maxiter(100) prune) maxiter(100) // sep(none)
* storedresults save prune e()
* storedresults compare benchmark e(), tol(1e-8) include(`include_list')



* B) As FEs
ppmlhdfe y, a(id1 id2, maxiter(3000)) maxiter(100)
storedresults compare benchmark e(), tol(1e-8) include(`include_list')


* C) As regressors
ppmlhdfe y ibn.id1 ibn.id2, noa maxiter(100)
storedresults compare benchmark e(), tol(1e-8) include(`include_list')

* C) LSMR
ppmlhdfe y, a(id1 id2, maxiter(100) accel(lsmr)) maxiter(100) sep(mu)
storedresults compare benchmark e(), tol(1e-8) include(`include_list')

exit

// Another benchmark
// glm y ibn.id1 ibn.id2, vce(robust) fam(poisson) irls

