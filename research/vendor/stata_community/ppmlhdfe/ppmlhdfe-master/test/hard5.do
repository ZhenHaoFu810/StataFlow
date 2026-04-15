noi cscript "ppmlhdfe - hard4 (simplex) plus simple case" adofile ppmlhdfe
set linesize 150

clear
input byte(y x1 x2 x3 x4 x5)
0  0  0  0  0 1
0  0  0  0  0 2
0  5 11  2  2 0
0  5  2 11  2 0 
0  5  2  2 11 0
0  0 -1 -1 -1 0
1  5  5  5  5 0
2  4  4  4  4 0
3  3  3  3  3 0
4  2  2  2  2 0
5  1  1  1  1 0
end

gen double z = (x2 + x3 + x4) / 3
reg x1 z if y > 0 // beta = 1
gen double e = x1 - z // predict double e, resid
su e if y == 0, d
list

set seed 12345
ppmlhdfe y x1 x2 x3 x4, noa tol(1e-10) simplex_maxiter(10) v(4) // v(1) // OK

ppmlhdfe y    x2 x3 x4, noa tol(1e-10) // v(1) // OK

*ppmlhdfe y x1 x2 x3 x4, noa tol(1e-10) maxiter(50) v(1) // sep(extra) // FAILS TO CONVERGE

* TODO: rewrite this as a proper cscript

exit


asd

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
// glm y ibn.id1 ibn.id2, vce(robust) fam(poisson) irls

exit
