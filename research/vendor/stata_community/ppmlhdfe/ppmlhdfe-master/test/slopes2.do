noi cscript "ppmlhdfe - slopes" adofile ppmlhdfe
set linesize 150

loc include_list ///
	scalar: N ll rmse converged deviance rss  ///
	matrix: /// trim_b trim_V
	macros: wexp wtype

clear
input double(id1 y) byte(x z c)
1   67793.6092504498 0 -1 1
1              68774 0  0 1
2 29460066.818006903 1 -1 1
2  40370377.65078497 1 10 1
3  4215.552981376648 0  7 1
3  4288.904005765915 0 15 1
4  483882.9337809086 0  7 1
4 306164.57000368834 0  8 1
5 29557.571687340736 0  6 1
5  170794.3896008134 0 12 1
6 1963894.9483253956 0  6 1
6 3364687.2930059433 0 12 1
end

li, sepby(id1)

reghdfe x, absorb(id1##c.z c) maxiter(100)
assert e(rmse) <= 1e-12
assert e(r2)==1

* Benchmark
ppmlhdfe y ibn.id1##c.z, noa tol(1e-12)
storedresults save benchmark e()

* Test
ppmlhdfe y x, absorb(id1##c.z c) maxiter(100) tol(1e-12)
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

