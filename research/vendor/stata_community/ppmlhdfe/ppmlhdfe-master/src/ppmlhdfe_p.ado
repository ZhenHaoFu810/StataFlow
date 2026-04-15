program define ppmlhdfe_p

	* Also see:
	* - viewsource glim_p.ado
	* - viewsource glim_l03.ado
	* - viewsource glim_v3.ado

	* Sanity checks
	_assert "`e(cmd)'" == "ppmlhdfe"
	_assert "`e(depvar)'" != ""

	* Intersect -scores-
	cap syntax anything [if] [in], SCORES
	loc was_score = !c(rc)
	if (`was_score') {
		* Call _score_spec to get newvarname; discard type
		* - This resolves wildcards that -margins- sends to predict (e.g. var* -> var1)
		_score_spec `anything', score
		loc 0 `s(varlist)' `if' `in' , scores
	}


	syntax newvarname [if] [in] [, ///
		XB XBD D Mu Eta STDP ///
		Anscombe Cooksd DEViance Hat Likelihood Pearson Response Scores Working]

	* Default option is MU
	loc nondefault `xb' `d' `xbd' `eta' `stdp' `anscombe' `cooksd' `deviance' `hat' `likelihood' `pearson' `response' `scores' `working'

	* Ensure there is only one option
	opts_exclusive "`mu' `nondefault'"

	loc opt `mu' `nondefault'
	loc y `e(depvar)'
	loc ifin `"`in' `if'"' // put -in- first so we can add an -if- clause later in some cases

	* Default option is mu
	if ("`opt'" == "") {
		di as text "(option mu assumed; predicted mean of depvar)"
		loc opt "mu"
	}

	** * Currently implemented options
	** _assert inlist("`opt'", "xb", "d", "xbd", "eta", "mu"), msg("option `opt' not implemented yet!")

	* All options except -xb- require the vector of fixed effects
	if ("`opt'" != "xb") & ("`e(absvars)'" != "_cons") {
		_assert `"`e(d)'"' != "", msg("predict `opt' requires the -d- option of ppmlhdfe")
		conf double var `e(d)', exact
	}

	if inlist("`opt'", "xb", "stdp") {
		PredictXB `varlist' `ifin', `opt'
		exit
	}

	if ("`opt'" == "d") {
		gen double `varlist' = `e(d)' `ifin'
		la var `varlist' "d[`e(absvars)']"
		exit
	}
	

	* Compute ETA = XBD
	PredictXB `varlist' `ifin', xb
	if ("`e(absvars)'" != "_cons") {
		qui replace `varlist' = `varlist' + `e(d)' `ifin'
		la var `varlist' "Linear prediction: xb + d[`e(absvars)']"
	}
	else {
		* only include "if" when -if- is empty (we can't test against -ifin- because -in- can exist)
		loc if_literal = cond(`"`if'"'=="", "if", "&")
		qui replace `varlist' = . `ifin' `if_literal' mi(`e(d)') 
		la var `varlist' "Linear prediction: xb"
	}

	* Exit if ETA
	if inlist("`opt'", "xbd", "eta") {
		exit
	}

	* Exit if MU
	if ("`opt'" == "mu") {
		qui replace `varlist' = exp(`varlist') `ifin' // mu = g^-1(eta) = exp(eta)
		la var `varlist' "Predicted mean of `y'"
		exit
	}

	* Compute MU for later
	tempvar mu
	gen double `mu' = exp(`varlist') `ifin'

	* From now on, we need -y- to exist
	conf var `y', exact

	* Deviance = 2 { Σ[μ] - Σ[y] + (y>0) * Σ[y log(y/μ)]
	if ("`opt'" == "deviance") {
		qui replace `varlist' = 2 * cond(`y' > 0, `mu' -`y' + `y' * ln(`y' / `mu'), `mu') `ifin'
		la var `varlist' "deviance residual"
		exit
	}

	* Response = y - μ
	if ("`opt'" == "response") {
		qui replace `varlist' = `y' - `mu' `ifin'
		la var `varlist' "response residual"
		exit
	}

	* Pearson residuals = (y - μ) / sqrt(μ)
	if ("`opt'" == "pearson") {
		qui replace `varlist' = (`y' - `mu') / sqrt(`mu') `ifin'
		la var `varlist' "Pearson residual"
		exit
	}

	* Anscombe residuals
	if ("`opt'" == "anscombe") {
		qui replace `varlist' = 1.5 * (`y' ^ (2/3) -`mu' ^ (2/3)) / `mu'^(1/6) `ifin'
		la var `varlist' "Anscombe residual"
		exit
	}

	* Score residuals = y - μ
	if ("`opt'" == "scores") {
		qui replace `varlist' = `y' - `mu' `ifin'
		la var `varlist' "score residual"
		exit
	}

	* Working residuals = .. y - μ
	if ("`opt'" == "working") {
		qui replace `varlist' = (`y' - `mu') / `mu' `ifin'
		la var `varlist' "working residual"
		exit
	}

	_assert 0, msg("option not implemented: `opt'") rc(198)


end


program PredictXB
	syntax newvarname [if] [in], [*]
	cap matrix list e(b) // if there are no regressors, _predict fails
	if (c(rc)) {
		gen double `varlist' = 0 `if' `in'
	}
	else {
		_predict double `varlist' `if' `in', `options'
	}
end
