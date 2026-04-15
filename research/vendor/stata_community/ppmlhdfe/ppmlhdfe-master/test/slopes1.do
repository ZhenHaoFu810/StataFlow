noi cscript "ppmlhdfe - slopes" adofile ppmlhdfe
set linesize 150

loc include_list ///
	scalar: N ll rmse converged deviance rss  ///
	matrix: /// trim_b trim_V
	macros: wexp wtype


clear
input double trade byte(fta exporter trend c)
35412.88183544995 0  8 15 1
619124.7429669127 0  8 16 1
 645947.355868591 0 35  0 1
2113023.937040806 1 35 12 1
end

reghdfe fta, absorb(exporter##c.trend c) maxiter(10)
assert e(rmse) <= 1e-12
assert e(r2)==1

* Benchmark
ppmlhdfe trade ibn.exporter##c.trend, noa maxiter(100)
storedresults save benchmark e()

* Test
ppmlhdfe trade fta, absorb(exporter##c.trend c) noa maxiter(100)
storedresults compare benchmark e(), tol(1e-8) include(`include_list')


exit




* A combination of ID2 and ID1 perfectly separates Y (obs #3)
*gen double z = id1 - id2
gen double z = (id2==1) - (id1==1)
li y z if y==0
li y z if y>0

loc include ///
	scalar: converged ll deviance /// chi2 p ???

* Benchmark
poisson y i.id1 i.id2 if _n!=3 , tol(1e-12)


* NOT WORKING!
* * A) PRUNE
* ppmlhdfe y, a(id1 id2, maxiter(100) prune) maxiter(100) // sep(none)
* storedresults save prune e()
* storedresults compare benchmark e(), tol(1e-8) include(`include_list')



* B) As FEs
ppmlhdfe y, a(id1 id2, maxiter(1000)) maxiter(100)
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

