* ===========================================================================
* Test -predict- after ppmlhdfe
* ===========================================================================


// --------------------------------------------------------------------------
// Setup
// --------------------------------------------------------------------------
	noi cscript "ppmlhdfe postestimation: predict" adofile ppmlhdfe
	set linesize 150
	*ppmlhdfe, reload
	*pr drop _all

	sysuse auto, clear


// --------------------------------------------------------------------------
// Verify that we can save -d- (the sum of the fixed effects)
// --------------------------------------------------------------------------

	ppmlhdfe price weight, a(turn) d(d)
	ppmlhdfe price weight, a(turn) d
	assert d == _ppmlhdfe_d
	drop d _ppmlhdfe_d


// --------------------------------------------------------------------------
// predict, xb
// --------------------------------------------------------------------------
	
	*poisson price weight length, tol(1e-10)
	glm price weight length, fam(poi) vce(robust) ltol(1e-10)
	predict double xb_bench, xb

	ppmlhdfe price weight length, noa
	predict double xb, xb
	su xb*
	assert abs(xb_bench - xb) < 1e-8
	drop xb xb_bench

	predict xb1 in 1, xb
	assert mi(xb1) if _n > 1
	drop xb1


// --------------------------------------------------------------------------
// options "d", "xbd", "eta"
// --------------------------------------------------------------------------
	
	* Without FEs, d==0
	ppmlhdfe price weight length gear, noa d
	assert abs(_ppmlhdfe_d) < 1e-6
	ppmlhdfe price weight length gear, noa d min_ok(2)
	assert abs(_ppmlhdfe_d) < 1e-10

	* Ensure that -d- must be saved
	drop _*
	ppmlhdfe price weight length gear, a(turn)
	predict xb, xb // ok
	cap noi predict d, d // error
	assert c(rc)
	drop xb d

	* Ensure that xb+d=xbd
	ppmlhdfe price weight length gear, a(turn trunk) d tol(1e-12)
	predict xb, xb
	predict d, d
	predict xbd, xbd
	assert abs(xbd - xb - d) < 1e-12 if e(sample)
	assert mi(xbd) & mi(d) if !e(sample)

	* Ensure that eta=xbd
	predict eta, eta
	assert eta == xbd
	drop xb xbd d

	* Ensure that GLM and PPMLHDFE agree on eta
	gen byte sample = e(sample)
	glm price weight length gear i.turn i.trunk , fam(poi) ltol(1e-12)
	predict double eta_bench, eta
	assert abs(eta - eta_bench) < 1e-6 if sample // glm predicts -eta- even outside the sample
	drop eta* sample _*

	* Ensure that GLM and PPMLHDFE agree on eta on full sample w/out FEs
	ppmlhdfe price weight length gear turn foreign, noa
	set trace off
	predict eta, eta
	predict xb, xb
	glm price weight length gear turn foreign, vce(rob) fam(poi) ltol(1e-12)
	predict double eta_bench, eta
	predict double xb_bench, xb
	assert abs(eta - eta_bench) < 1e-9
	assert abs(xb - xb_bench) < 1e-9


// --------------------------------------------------------------------------
// MU
// --------------------------------------------------------------------------
	
	sysuse auto, clear

	ppmlhdfe price weight length gear, a(turn trunk) d tol(1e-12) keepsing
	predict mu, mu

	glm price weight length gear i.turn i.trunk , fam(poi) ltol(1e-12)
	predict double mu_bench, mu
	assert reldif(mu, mu_bench) < 1e-6 // less precision due to exp() transformation
	drop mu* _*


// --------------------------------------------------------------------------
// Additional options
// --------------------------------------------------------------------------
	loc opts eta mu response pearson anscombe score working

	glm price weight length gear i.turn i.trunk , fam(poi) ltol(1e-12)
	foreach opt of local opts {
		predict double `opt'_bench, `opt'
	}

	* TEST WITHOUT STANDARDIZING Y,X
	ppmlhdfe price weight length gear, a(turn trunk) d tol(1e-12) keepsing standardize_data(0) min_ok(2)

	foreach opt of local opts {
		*di as text "- Computing option <`opt'>"
		predict `opt', `opt'

		di as text "- Testing option <`opt'>"

		* Normalize by depvar if not standardized...
		if inlist("`opt'", "response", "score") {
			gen double delta = (`opt' - `opt'_bench) / (0.1 + price)
			su delta
			assert abs(delta) < 1e-7
			drop delta
		}
		else {
			assert reldif(`opt', `opt'_bench) < 1e-7
		}
		drop `opt'
	}

	* TEST STANDARDIZING Y,X (way less accuracy! why?)
	ppmlhdfe price weight length gear, a(turn trunk) d tol(1e-12) keepsing min_ok(2)

	foreach opt of local opts {
		*di as text "- Computing option <`opt'>"
		predict `opt', `opt'

		di as text "- Testing option <`opt'>"

		* Normalize by depvar if not standardized...
		if inlist("`opt'", "response", "score") {
			gen double delta = (`opt' - `opt'_bench) / (0.1 + price)
			assert abs(delta) < 1e-6
			drop delta
		}
		else {
			assert reldif(`opt', `opt'_bench) < 1e-6
		}
		drop `opt'
	}

exit
