* Not a proper cscript yet...

clear all
* cls
sysuse auto


// --------------------------------------------------------------------------
// Initial examples (no FEs)
// --------------------------------------------------------------------------
glm price c.weight#c.weight c.weight#c.gear i.foreign, fam(poi) vce(robust) ltol(1e-12)
margins
margins foreign
margins, dydx(weight) atmeans

ppmlhdfe price c.weight#c.weight c.weight#c.gear i.foreign, maxiter(100) tol(1e-12)
margins
margins foreign
margins, dydx(weight) atmeans



// --------------------------------------------------------------------------
// Examples from Jeff Pitblado (StataCorp)
// --------------------------------------------------------------------------
glm price c.weight##c.headroom, vce(robust) fam(poi) tol(1e-12)
est store bench1
margins, dydx(weight) at(headroom=(1.5(0.5)5)) post
est store bench1_marg

ppmlhdfe price c.weight##c.headroom, maxiter(100)
est store ppmlhdfe1
margins, dydx(weight) at(headroom=(1.5(0.5)5)) post
est store ppmlhdfe1_marg

* show equivalent model fits, and the same parameterization
est table bench1 ppmlhdfe1, b se stat(rmse)

* show -margins- yields the same marginal effects and SE estimates
est table bench1_marg ppmlhdfe1_marg, b se
est clear

glm price c.weight##i.foreign, vce(robust) fam(poi) tol(1e-12)
est store bench2
margins for, dydx(weight) post
est store bench2_marg

ppmlhdfe price c.weight##i.foreign, maxiter(100)
est store ppmlhdfe2
margins for, dydx(weight) post
est store ppmlhdfe2_marg

* show equivalent model fits, but a different parameterization because
* the c.weight#1.foreign coefficient was fit by -areg-, but
* c.weight#0.foreign was fit by -ppmlhdfe-
est table bench2 ppmlhdfe2, b se stat(rmse)

* show -margins- yields the same marginal effects and SE estimates
est table bench2_marg ppmlhdfe2_marg, b se
est clear


// --------------------------------------------------------------------------
// Examples from Jeff Pitblado (StataCorp) ; with FEs
// --------------------------------------------------------------------------
glm price ibn.turn c.weight##c.headroom, irls vce(robust) fam(poi) ltol(1e-14)
est store bench1
margins, dydx(weight) at(headroom=(1.5(1.0)5)) post
est store bench1_marg

ppmlhdfe price c.weight##c.headroom, a(turn) d keepsing tol(1e-12) maxiter(100)
est store ppmlhdfe1
margins, dydx(weight) at(headroom=(1.5(1.0)5)) post
est store ppmlhdfe1_marg

* show equivalent model fits, and the same parameterization
*est table bench1 ppmlhdfe1, b se stat(rmse)

* show -margins- yields the same marginal effects // NOT SE estimates
est table bench1_marg ppmlhdfe1_marg, b se
est clear

* WARNING: Not the same SEs; because of the FEs?
* (maybe "help xtlogit_postestimation##margins" and other docs can provide more info?)

exit
