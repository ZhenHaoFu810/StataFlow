* ===========================================================================
* Install ppmlhdfe from local Git folder
* ===========================================================================
	

// --------------------------------------------------------------------------
// Setup
// --------------------------------------------------------------------------

	set trace off
	set varabbrev on
	log close _all
	clear all
	discard
	cls
	pr drop _all


// --------------------------------------------------------------------------
// Install ppmlhdfe
// --------------------------------------------------------------------------

	cap ado uninstall ppmlhdfe

	* Reinstall
	* Note: "net install" requires hardcoded paths so we do a workaround
	mata: st_local("path", pathresolve(pwd(), "../src"))
	mata: assert(direxists("`path'"))
	net install ppmlhdfe , from("`path'")


// --------------------------------------------------------------------------
// Quick test to see if it works
// --------------------------------------------------------------------------

	set trace off
	sysuse auto, clear
	
	which reghdfe
	reghdfe price, a(foreign)

	which ppmlhdfe
	**ppmlhdfe price, a(foreign)

	reghdfe price weight, a(turn)
	keep if e(sample)

	ppmlhdfe price weight, a(turn) d
	predict mu, mu
	drop if mi(mu)

	ppmlhdfe price weight, a(turn) guess(simple)
	ppmlhdfe price weight, a(turn) guess(ols)
	ppmlhdfe price weight, a(turn) guess(var mu)
	ppmlhdfe price weight, a(turn) guess(var mu) use_exact_partial(1) use_exact_solver(1) start_inner_tol(1e-8) standardize_data(0)

	ppmlhdfe price weight, a(turn) guess(var mu) use_exact_partial(1) use_exact_solver(1) start_inner_tol(1e-8)
	ppmlhdfe price weight, a(turn) guess(var mu) standardize_data(0)

exit

	ppmlhdfe price weight, a(turn) guess(var mu) use_exact_partial(1) use_exact_solver(1) tolerance(1e-10) itolerance(1e-10) start_inner_tol(1e-10) standardize_data(0)

exit
	gen c1 = 1
	gen c2 = 0
	gen c3 = .
	ppmlhdfe price weight, a(turn) guess(var c1)
	ppmlhdfe price weight, a(turn) guess(var c2)
	cap noi ppmlhdfe price weight, a(turn) guess(var c3)
	assert c(rc)

	ppmlhdfe price weight, a(turn) guess(var mu) d // ??

exit


cls

	glm price i.foreign, family(poisson) link(log) tol(1e-12) ltol(1e-12) nrtol(1e-12)
	predict mu1, mu


	gen byte one =1
	ppmlhdfe price [fw=one],  a(FE=foreign) d(d) use_exact_partial(1) use_exact_solver(1) itol(1e-15) tol(1e-15) start_inner_tol(1e-12) standardize_data(0)
	predict mu2, mu

	_predict double xb
	gen xbd = d + xb
	gen mu3 = exp(xbd)

	su mu*
exit

	su FE
	di r(max) - r(min)
	tab d



	predict mu, mu
	di log(r(mean))

	poisson price i.foreign


	exit

cls

clear all
sysuse auto, clear
poisson price weight i.foreign i.turn
ppmlhdfe price weight, absorb(FE1=foreign FE2=turn) d(sumFE) tol(1e-14) keepsing


exit
