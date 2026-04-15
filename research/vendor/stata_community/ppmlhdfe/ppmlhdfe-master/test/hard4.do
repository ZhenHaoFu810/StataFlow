noi cscript "ppmlhdfe - hard case where initial attempt shouldn't work" adofile ppmlhdfe
set linesize 150

/* Diagnostic:
- All Xs are the same over y>0, so we could replicate x1 with any linear comb. of x2, x3, x4
- Only some combinations will lead to a positive (or negative) residual on y==0
- There's no easy way of finding these
*/

clear
input byte(y x1 x2 x3 x4)
0  5 11  2  2
0  5  2 11  2
0  5  2  2 11
0  0 -1 -1 -1
1  5  5  5  5
2  4  4  4  4
3  3  3  3  3
4  2  2  2  2
5  1  1  1  1
end

gen double z = (x2 + x3 + x4) / 3
reg x1 z if y > 0 // beta = 1
gen double e = x1 - z // predict double e, resid
su e if y == 0, d
list

ppmlhdfe y    x2 x3 x4, noa tol(1e-10) // v(1) // OK
*ppmlhdfe y x1 x2 x3 x4, noa tol(1e-10) maxiter(50) v(1) // sep(extra) // FAILS TO CONVERGE


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
