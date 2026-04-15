* ===========================================================================
* Mata Code: Poisson Pseudo-Maximum Likelihood through IRLS
* ===========================================================================

// Include reghdfe (which in turn includes ftools) --------------------------
	cap findfile "reghdfe5.mata"
	if (_rc) {
	    di as error "ppmlhdfe requires the {bf:reghdfe} package (version 6 or newer), which is not installed"
	    di as error `"    - install from {stata ssc install reghdfe:SSC}"'
	    di as error `"    - install from {stata `"net install reghdfe, from("https://github.com/sergiocorreia/reghdfe/raw/master/src/")"':Github}"'
	    exit 9
	}
	include "`r(fn)'"


// Include .mata files  -----------------------------------------------------
	local GLM "class GLM scalar"
	
	findfile "ppmlhdfe_functions.mata"
	include "`r(fn)'"
	
	findfile "ppmlhdfe_separation_simplex.mata"
	include "`r(fn)'"
	
	findfile "ppmlhdfe_separation_relu.mata"
	include "`r(fn)'"


// --------------------------------------------------------------------------
// GLM Class
// --------------------------------------------------------------------------
mata:

mata set matastrict on
mata set mataoptimize on
mata set matadebug off // (on when debugging; off in production)
mata set matalnum  off // (on when debugging; off in production)


class GLM
{
	`Varname'				depvar, touse, weight_var, offsetvar
	`Varlist'				indepvars // , fullindepvars
	// `RowVector'             not_basevar (HDFE)
	`String'				absorb, weight_type
	`RowString'				separation

	`FixedEffects'			HDFE
	`Boolean'				verbose
	`Boolean'				log
	`Integer'				init_step // Used to ensure that we run the init_*() functions in the correct order

	`String'				vcetype
	`RowString'				clustervars, base_clustervars

	// Data-related variables
	`Variable'				y, offset, true_w
	`Variables'				x
	`Integer'				k
	`RowVector'				stdev_x
	`Real'					stdev_y, min_positive_y

	// Advanced estimation/solver parameters
	`String'				initial_guess_method // Method used to determine initial values of -mu-
	`String'				initial_guessvar // Variable used as initial value for -mu- ; only for guess(var ...)
	`Boolean'				standardize_data
	`Boolean'				remove_collinear_variables
	`Boolean'				use_exact_solver
	`Boolean'				use_exact_partial
	`Boolean'				use_heuristic_tol
	`Real'					tolerance, start_inner_tol, target_inner_tol, realized_tolerance
	`Integer'				iter, subiter // Iteration and subiteration counts
	`Integer'				min_ok // Minimum number of "ok" iterations before declaring convergence
	`Integer'				maxiter // Maximum number of iterations in IRLS step

	// Step-halving
	`Boolean'				use_step_halving
	`Real'					step_halving_memory
	`Iter'					max_step_halving

	// Separation-related parameters
	`Integer'				num_separated
	`Real'					mu_tol

	`Real'					simplex_tol
	`Integer'				simplex_maxiter
	
	`Real'					relu_tol
	`Real'					relu_zero_tol
	`Real'					relu_maxiter
	`Boolean'				relu_report_r2
	`String'				relu_sepvarname
	`String'				relu_zvarname
	`Boolean'				relu_debug
	`Boolean'				relu_strict
	`Boolean'				relu_accelerate

	// Methods
	`Void'					new()
	`Void'					validate_parameters()
	`Void'					init_fixed_effects()
	`Void'					init_variables()
	`Void'					init_separation()
	`Void'					solve()
	`Boolean'				inner_irls() // Returns 1 if converged else 0
}	


`Void' GLM::new()
{
	verbose = 0
	log = 1
	init_step = 0
	weight_var = weight_type = ""
	iter = subiter = 0
	// separation = J(1, 0, "")

	// Advanced estimation/solver parameters
	remove_collinear_variables = 1
	standardize_data = 1
	use_exact_solver = 0
	use_exact_partial = 0
	use_heuristic_tol = 1
	use_step_halving = 0
	step_halving_memory = 0.9
	max_step_halving = 2
	tolerance = 1e-8
	target_inner_tol = 1e-9 // Target HDFE tolerance
	start_inner_tol = 1e-4
	initial_guess_method = "simple"
	initial_guessvar = ""
	min_ok = 1 // Set to 1 or at most 2... // BUGBUG: If this is below 2, then this test will fail: savefe_advanced.do (!!)
	maxiter = 1000 // 10,000 ?

	// Separation parameters
	num_separated = 0
	separation = tokens("fe simplex relu mu")
	mu_tol = 1e-6 // Actual tolerance is this scaled by the minimum MU when y>0
	simplex_tol = 1e-12
	simplex_maxiter = 1000

	relu_tol = 1e-4
	relu_zero_tol = 1e-8
	relu_maxiter = 100
	relu_report_r2 = relu_debug = 0
	relu_zvarname = relu_sepvarname = ""
	relu_strict = 0
	relu_accelerate = 0 // 0 by default as it conflicts with the "accelerate partial" trick (by making the weights change frequently). Maybe if we make the weights more stable across iters...?
}


// --------------------------------------------------------------------------
// Validate that parameter values are not invalid
// --------------------------------------------------------------------------

`Void' GLM::validate_parameters()
{
	assert_boolean(remove_collinear_variables)
	assert_boolean(standardize_data)
	assert_boolean(use_exact_solver)
	assert_boolean(use_exact_partial)
	assert_boolean(use_heuristic_tol)

	assert_msg(0 < tolerance & tolerance <= 1, "tolerance must be a real between 0 and 1", 9001, 0)
	assert_msg(0 < start_inner_tol & start_inner_tol <= 1, "start_inner_tol must be a real between 0 and 1", 9001, 0)

	assert_in(initial_guess_method, ("simple", "ols", "variable"))
	assert_msg(min_ok >= 1, "min_ok must be a positive integer", 9001, 0)
	assert_msg(0 < maxiter)

	// Separation parameters
	assert_msg(0 < mu_tol & mu_tol < 1e-1, "mu_tol must be a real in (0, 0.1)", 9001, 0)
	assert_msg(0 < simplex_tol & simplex_tol < 1e-1, "simplex_tol must be a real in (0, 0.1)", 9001, 0)
	assert_msg(0 < simplex_maxiter, "simplex_maxiter must be a positive integer", 9001, 0)
}


// --------------------------------------------------------------------------
// Compute HDFE object
// --------------------------------------------------------------------------
`Void' GLM::init_fixed_effects()
{
	`Integer'				hdfe_verbose, num_tokens, i
	`Boolean'				check_separation
	`String'				options, key, val, cmd
	`StringRowVector'		tokens

	if (verbose > 0) printf("\n{txt}{bf:- Parsing absorb() and creating HDFE object:}\n")
	assert(++init_step == 1)
	assert_msg(depvar != "", "glm.depvar is empty")
	assert_msg(touse != "", "glm.touse is empty")
	
	// SYNTAX: fixed_effects( absvars [ , touse, weighttype, weightvar, drop_singletons, verbose])
	// Note: to set drop_singletons=0, add the "keepsingletons" option to the -absorb- string
	hdfe_verbose = verbose > 0 ? verbose - 1 : verbose
	check_separation = anyof(separation, "fe")
	HDFE = fixed_effects(absorb, touse, check_separation ? "iweight" : "", depvar, ., hdfe_verbose)
	HDFE.depvar = depvar // Otherwise, e(depvar) will be set to missing when we call HDFE.post()

	// Check for invalid suboptions within absorb()
	if (verbose > -1 & !HDFE.drop_singletons) printf("{err}warning: keeping singleton groups will keep fixed effects that cause separation\n")
	assert_msg(HDFE.residuals == "", "option {bf:residuals} not allowed", 198, 0)
	//assert_msg(st_global("s(options)") == "", sprintf("option(s) {bf:%s} not allowed",st_global("s(options)")), 198, 0)

	// Add advanced options
	options = st_global("s(options)")
	if (options != "") {
		tokens = tokens(options, " ()")
		assert_msg(!mod(cols(tokens), 4), sprintf("Invalid options: %s", options))
		num_tokens = trunc(cols(tokens) / 4)
		for (i=0; i<num_tokens; i++) {
			key = tokens[4*i+1]
			assert_msg(tokens[4*i+2] == "(")
			val = tokens[4*i+3]
			assert_msg(tokens[4*i+4] == ")")
			cmd = sprintf("cap mata: glm.%s = %s", key, val)
			stata(cmd)
			assert_msg(!st_numscalar("c(rc)"), sprintf("option {bf:%s} not allowed", key), 198, 0)
		}

		// Check that parameters are still valid
		validate_parameters()
	}

	// Update touse (might be smaller due to singletons)
	if (HDFE.drop_singletons) HDFE.save_touse()
}


// --------------------------------------------------------------------------
// Load data into Mata
// --------------------------------------------------------------------------
`Void' GLM::init_variables()
{
	if (verbose > 0) printf("\n{txt}{bf:- Loading regression variables into Mata}\n")
	assert(++init_step == 2)

	// 1) Expand factor variables in the RHS, and mark omitted variables
	stata(sprintf("ms_expand_varlist %s if %s", indepvars, touse))
	if (verbose > 0) stata("return list")
	HDFE.not_basevar = strtoreal(tokens(st_global("r(not_omitted)"))) // We want to output all coefs including the omitted ones
	indepvars = HDFE.indepvars = tokens(st_global("r(varlist)"))
	HDFE.fullindepvars = st_global("r(fullvarlist)") // tokens() ???
	HDFE.varlist = depvar, HDFE.indepvars

	// 2) Load LHS
	y = st_data(HDFE.sample, depvar)
	assert_msg(all(y :>= 0), sprintf("{err}%s must be greater than or equal to zero", depvar), 459, 0)
	
	// 3) Load RHS
	k = cols(indepvars)
	if (k) {
		_st_data_wrapper(HDFE.sample, indepvars, x=., verbose)
	}
	else {
		x = J(rows(y), 0, .)	
	}
	assert(cols(x)==k)

	// 4) Load additional variables
	offset = offsetvar != "" ? st_data(HDFE.sample, offsetvar) : J(0, 1, .)
	true_w = weight_var != "" ? st_data(HDFE.sample, weight_var) : 1

	// 5) Save memory
	// st_dropvar(HDFE.tousevar)
	// (If needed, preserve+clear the data)

	// 6) Standardize data
	if (standardize_data) {
		if (verbose > 0) printf("{txt} @@ Standardizing variables\n")
		stdev_x = reghdfe_standardize(x)
		stdev_y = reghdfe_standardize(y)
		//_edittozerotol(y, epsilon(1)) // round to zero values below macheps (2e-16) // Warning: doing this might be a bad idea, and will fail the collinear.do test
		min_positive_y = min(select(y, y:>0))
		if (verbose > -1 & min_positive_y <= 1e-6) printf("{err}warning: dependent variable takes very low values after standardizing (%g)\n", min_positive_y)
		// TODO: do we need to rescale the offset?
	}
	else {
		stdev_x = J(1, k, 1)
		stdev_y = 1
	}

	// 7) Speedup trick: Try to sort data by first FE (if not already sorted by one of the FEs)
	// Isn't it better to do this BEFORE loading all the data and creating HDFE?

	// 8) Remove collinear variables (better to do this now than to carry these variables through the separation step)
	// Note that this requires an entire partial_out() call, so it is slow
	if (remove_collinear_variables) {
		if (verbose > 0) printf("{txt} @@ Removing collinear variables\n")
		HDFE.varlist = HDFE.indepvars
		remove_collinears(HDFE, target_inner_tol, x, k, stdev_x, weight_type, weight_var, true_w, verbose) // Will modify (HDFE.not_basevar, x, k, stdev_x) accordingly, and overwrite HDFE.weights
		HDFE.varlist = depvar, HDFE.indepvars
	}
}


// --------------------------------------------------------------------------
// Detect and correct separation
// --------------------------------------------------------------------------
`Void' GLM::init_separation()
{
	`Boolean'				check_separation
	`Vector'				non_separated_obs
	`Integer'				num_drop

	assert(++init_step == 3)

	// Abort if there are no boundary observations (i.e. y > 0 always)
	if (all(y :> 0)) {
		if (verbose > 0) printf("{txt}\n $$ No boundary observations (y=0), no separation tests required.\n")
		return
	}

	// Simplex method
	check_separation = anyof(separation, "simplex") & k
	if (check_separation) {
		num_drop = simplex_fix_separation(HDFE, y, x, k, stdev_x, true_w, weight_type, weight_var, target_inner_tol, simplex_tol, simplex_maxiter, non_separated_obs=., verbose)
		if (num_drop & rows(offset)) offset = offset[non_separated_obs]
		num_separated = num_separated + num_drop
	}

	// ReLU method (also works for fixed effects and combinations of regressors and FEs)
	check_separation = anyof(separation, "relu")
	if (check_separation) {
		num_drop = relu_fix_separation(HDFE, y, x, k, stdev_x, true_w, weight_type, weight_var, target_inner_tol,
		                               relu_tol, relu_zero_tol, relu_maxiter,
		                               relu_sepvarname, relu_zvarname, relu_debug, relu_report_r2,
		                               non_separated_obs=., relu_strict, relu_accelerate, verbose)
		if (num_drop & rows(offset)) offset = offset[non_separated_obs]
		num_separated = num_separated + num_drop
	}

}


// --------------------------------------------------------------------------
// Compute estimates through IRLS
// --------------------------------------------------------------------------
`Void' GLM::solve(`String' bname,
                  `String' Vname,
                  `String' nname,
                  `String' rname,
                  `String' dfrname,
                  `String' llname,
                  `String' ll_0name,
                  `String' devname,
                  `String' chi2name,
                  `String' d_name)
{
	`Variable'				mu, eta, z, resid, d
	`Variables'				data
	`Vector'				b
	`Matrix'				V
	`Integer'				N, df_r, rank, N_sep, backup_iter
	`Boolean'				check_separation
	`Boolean'				converged
	`Real'					deviance, eps, ll, ll_0, ll_0_mu, chi2
	`Vector'				separated_obs, non_separated_obs, zero_sample


	assert(++init_step == 4)

	if (verbose > 1) printf("{txt} @@ Starting GLM::solve\n")

	// Set up tolerance (used to estimate initial values and first step of IRLS)
	HDFE.tolerance = max(( start_inner_tol , tolerance ))

	// Set weights (used when setting initial values...)
	HDFE.load_weights(weight_type, weight_var, true_w, verbose) // Before, HDFE.weight was just -depvar-!

	// Initial values for -mu- (using actual weights)
		// - Reference: Generalized Linear Models and Extensions (Hardin & Hilbe) page 31
		//	 a) "initialize the fitted values to the inverse link of the mean of the response variable"
		//   b) "set the initial fitter values to (y + y̅ ) / 2"
	// TODO: is there a better way?
	if (verbose > 0) printf("{txt} @@ Setting initial values\n")
	if (initial_guess_method == "ols") {
		if (verbose > 0) printf("\n{txt} - OLS Estimates of log(1+y) as initial values")
		HDFE._partial_out(data = (log(y :+ mean(y, HDFE.weight) :/ 100 ), x), ., 0, ., 1) // Don't standardize vars; flush aux vectors // Bugbug why divide mean by 100? to make it small?
		reghdfe_solve_ols(HDFE, data, b=., V=., N=., rank=., df_r=., mu=., ., "vce_none") // mu instead of resid, to save space
		mu = exp(log(y :+ 1) - mu)
	}
	else if (initial_guess_method == "simple") {
		mu = 0.5 * (y :+ mean(y, HDFE.weight))
	}
	else {
		mu = st_data(HDFE.sample, initial_guessvar)
		if (standardize_data) (void) reghdfe_standardize(mu)
		assert_msg(!hasmissing(mu), sprintf("{err}guess() variable cannot have missing values"))
	}

	// Run IRLS algorithm (note that -mu- is both an input and output!)
	check_separation = anyof(separation, "mu")

	converged = inner_irls(mu, eta, check_separation, data=., z=., deviance=., eps=., separated_obs=J(0, 1, .))
	assert_msg(converged, sprintf("{err}Failed to converge in %4.0f iterations (eps=%9.6e){txt}\n", maxiter, eps), 430, 0)

	// Post-IRLS check for separation
	N_sep = rows(separated_obs)
	if (N_sep) {
		assert(check_separation)
		data = . // Conserve memory
		num_separated = num_separated + N_sep

		if (verbose > -1) printf("{txt}(IRLS step detected %g separated observation%s)\n", N_sep, N_sep > 1 ? "s" : "")
		non_separated_obs = trim_separated_obs(HDFE, y, x, weight_type, weight_var, true_w, separated_obs, verbose)
		// Note that we might separate more than N_sep obs. due to possible new singletons
		mu = mu[non_separated_obs]
		eta = eta[non_separated_obs]
		z = z[non_separated_obs]
		if (rows(offset)) offset = offset[non_separated_obs]
		remove_collinears(HDFE, target_inner_tol, x, k, stdev_x, weight_type, weight_var, true_w, verbose) // Will modify (HDFE.not_basevar, x, k, stdev_x) accordingly, and overwrite HDFE.weights

		// Re-run IRLS with trimmed data
		backup_iter = iter
		converged = inner_irls(mu, eta, 0, data=., z=., deviance=., eps=., separated_obs=J(0, 1, .))
		iter = iter + backup_iter
		assert_msg(converged, sprintf("{err}Failed to converge in %4.0f iterations (eps=%9.6e){txt}\n", maxiter, eps), 430, 0)
	}

	if (verbose > -1 & log) printf("{txt}{hline 108}\n")
	if (verbose > -1 & log) printf("{txt}(legend: {res}p{txt}: exact partial-out   {res}s{txt}: exact solver   {res}h{txt}: step-halving   {res}o{txt}: epsilon below tolerance)\n")
	if (verbose > -1) printf("{txt}Converged in %g iterations and %g HDFE sub-iterations (tol =%4.0e)\n", iter, subiter, tolerance)
	st_local("ic", strofreal(iter))
	st_local("ic2", strofreal(subiter))


	// Compute results
	if (verbose > 0) printf("{txt} @@ Computing DoF\n")
	HDFE.vcetype = vcetype
	HDFE.clustervars = tokens(clustervars)
	HDFE.base_clustervars = tokens(base_clustervars)
	HDFE.num_clusters = length(HDFE.clustervars)
	HDFE.estimate_dof()

	if (verbose > 0) printf("{txt} @@ Computing final betas and standard errors\n")

	// Pseudo log likelihood
	// We use lngamma() because lnfactorial() doesn't work with non-integers
	resid = y :* stdev_y :* (eta:+ log(stdev_y)) - mu :* stdev_y - lngamma(y :* stdev_y :+ 1)
	//resid = y :* stdev_y :* (log(mu) :+ log(stdev_y)) - mu :* stdev_y - lngamma(y :* stdev_y :+ 1) // Not as accurate on extreme cases, makes collinear2.do fail
	
	zero_sample = selectindex(y :== 0)
	resid[zero_sample] = -mu[zero_sample] :* stdev_y
	ll = quadsum(resid :* true_w)
	resid = .

	// Alternative; using the fact that LL = MAX_LL - Deviance / 2
	// resid = y :* stdev_y :* (log(y) :+ log(stdev_y) - 1) - lngamma(y :* stdev_y :+ 1)
	// resid[zero_sample] = -y[zero_sample] :* stdev_y
	// ll = quadsum(resid :* true_w) - deviance / 2

	// Pseudo Log likelihood of constant-only model
	ll_0_mu = mean(y, true_w)
	resid = y :* (stdev_y * (log(ll_0_mu) + log(stdev_y))) :- (ll_0_mu * stdev_y) :- lngamma(y :* stdev_y :+ 1)
	zero_sample = selectindex(y :== 0)
	resid[zero_sample] = J(rows(zero_sample), 1, -ll_0_mu * stdev_y)
	ll_0 = quadsum(resid :* true_w)
	resid = .

	// Prepare to recover _cons
	HDFE.compute_constant = 1
	// Note: mu :* true_w == HDFE.weight
	HDFE.means = mean(log(mu), HDFE.weight) , mean(x, HDFE.weight)
	stdev_x = stdev_x, 1

	// With fweights we need to run an ad-hoc code, equivalent to aweights+fweights
	reghdfe_solve_ols(HDFE, data, b=., V=., N=., rank=., df_r=., resid=., ., "vce_asymptotic",
	                  weight_type == "fweight" ? true_w : J(0, 1, .))
	if (rows(offset)) b[rows(b)] = b[rows(b)] - mean(offset, HDFE.weight) // mu :* true_w

	// Run this before updating weights
	if (HDFE.save_any_fe | (d_name != "")) {
		//  z =  x b + d + e	(z: working depvar)
		// zz = xx b + e 		(zz: demeaned z)
		// THUS: d = z - xb - (e = zz - xx b)

		d = z - resid :- (cols(x) ? x * b[1..(rows(b)-1)] : 0)
		d = d :- mean(d, HDFE.weight)

		if (d_name != "") {
			if (HDFE.verbose > 0) printf("{txt} @@ Storing sum of fixed effects in {res}%s{txt}\n", d_name)
			//resid = resid :- log(stdev_y)
			HDFE.save_variable(d_name, d, "Sum of fixed effects")
		}

		if (HDFE.save_any_fe) {
			if (verbose > 0 & verbose < 3) printf("\n## Storing estimated fixed effects\n")
			HDFE.store_alphas(d)
		}

		// Debugging:
		// HDFE.save_variable("weight", HDFE.weight)
		// stata("su A B weight") // Not zero mean
		// stata("su A B [iw=weight]") // Zero mean
	}

	// Rescale results
	// See https://stats.stackexchange.com/questions/175349/in-a-poisson-model-what-is-the-difference-between-using-time-as-a-covariate-or
	b[rows(b)] = b[rows(b)] + log(stdev_y)
	b = b :/ stdev_x'
	V = V :/ (stdev_x' * stdev_x)
	// resid = resid :* stdev_y // BUGBUG?

	HDFE.load_weights(weight_type, weight_var, true_w, 1) // Why verbose==1? BUGBUG

	assert(cols(data) - 1 == rows(b) - HDFE.compute_constant)
	data = .

	chi2 = HDFE.F * HDFE.df_m // Wald test; based on output by reghdfe_solve_ols()

	// Add constant
	if (verbose > 1) printf("\n{txt}## Adding _cons to varlist\n")
	assert_msg(rows(HDFE.not_basevar) == 1, "rows(S.not_basevar) == 1")
	HDFE.not_basevar = HDFE.not_basevar, 1
	HDFE.fullindepvars = HDFE.fullindepvars + " _cons"
	HDFE.indepvars = HDFE.indepvars, " _cons"

	// Add base/omitted variables
	add_base_variables(HDFE, b, V)
	// Post results
	st_matrix(bname, b')
	st_matrix(Vname, V)
	st_numscalar(nname, N)
	st_numscalar(rname, rank)
	st_numscalar(dfrname, df_r)
	st_numscalar(llname, ll)
	st_numscalar(ll_0name, ll_0)
	st_numscalar(chi2name, chi2)
	st_numscalar(devname, deviance)

	// Need to save resids if saving FEs, even if temporarily
	if (HDFE.residuals == "" & HDFE.save_any_fe) {
		HDFE.residuals = "__temp_reghdfe_resid__"
	}

	// BUGBUG ! We shouldn't need to update touse!!
	//st_dropvar(HDFE.tousevar)
	//HDFE.save_touse("", 0)
	HDFE.save_touse("", 1)
}


// --------------------------------------------------------------------------
// Iteratively Re-weighted Least Squares (IRLS) 
// --------------------------------------------------------------------------

// WARNING:
// Discussion on numerical stability: very low (but positive) values of mu
// (This is related to the "collinear2.do" test)
// If our LHS has both very high and very low values, then standardizing -y- will make the very low values *extremely low*
// Then, the ratio y/mu (and thus log(..)) can be wildly inaccurate
// Example from obs. 5 of collinear2.do:
// y=134.9833527, eta= -1.23202993 ; thus mu=0.291699846, y/mu=462.7474252 and log(y/mu)=6.137181387
// However, if stdev_y=1.17511e+14 , then mu=2.22045e-14 y/mu=51.73238502 and log(y/mu)=3.946083988
// Instead, let's do y/mu=exp(log(y)-eta)=462.7474256 and log(y/mu)=log(y)-eta= 6.137181388 , which are WAY CLOSER to the correct soln (!!)
// (The cost is of course a slower computation for y/mu)

`Boolean' GLM::inner_irls(`Variable' mu, // Initial value
                          `Variable' eta, // Will be returned (to compute log-likelihood)
                          `Boolean' check_separation,
        				  `Variables' data, // Return transformed data (y,x)
        				  `Variable' z, // Return working depvar; only used when saving FEs
        				  `Real' deviance, // Return final deviance
        				  `Real' eps, // Return eps; the convergence criteria
        				  `Vector' separated_obs)
{
	`Integer'		ok, N_sep, col, num_step_halving
	`Variable'		separation_mask, z_last, irls_w, resid, old_eta
	`Vector'		zero_sample
	`Vector'		b
	`Real'			log_septol, old_deviance, delta_deviance, alt_tol, highest_inner_tol, denom_eps, min_eta, adjusted_log_septol
	`Boolean'		iter_fast_partial, iter_fast_solver, iter_step_halving
	`String'		iter_text
	`Matrix'		last_x
	`Vector'		eps_history
	`Real'			predicted_eps

	// Sanity checks
	assert(k == cols(x))
	assert(0 < step_halving_memory & step_halving_memory < 1)

	// WARNING:
	// If the initial value of MU is too close to zero, then 
	// when computing z = "eta - 1 + y / mu" we end up with a high value
	// and that eventually leads to mu=exp(eta) being infinite
	// EG: if y/mu=1e-2, exp(z) = 2e+43 (!!!)
	censor_mu(mu, y, verbose)

	// Initialize IRLS
	highest_inner_tol = max((1e-12, min((target_inner_tol, 0.1 * tolerance)) )) // This is the *actual* target tolerance; HDFE.partial_out() will never have a tolerance higher than this
	log_septol = log(mu_tol) // sep. tolerance in terms of Mu and not Eta
	eta = log(mu)
	HDFE.load_weights("aweight", "<placeholder for mu>", y, 1) // y is just a placeholder; we'll place (true_w*mu) later
	eps = deviance  = .
	ok = N_sep = iter_step_halving = num_step_halving = 0
	separation_mask = z = z_last = J(rows(eta), 1, 0)
	zero_sample = selectindex(y :== 0)
	eps_history = J(3, 1, .)

	if (verbose > 0) {
		printf("{txt} @@ Starting IRLS\n")
		printf("{txt}    Target HDFE tolerance:{res}%-9.4e{txt}\n", highest_inner_tol)
		if (verbose > 2) stata("memory")
	}

	// Iterate
	iter = 0
	while ((ok < min_ok) & (++iter <= maxiter)) {

		iter_fast_partial = !use_exact_partial & (iter > 1)
		iter_fast_solver  = !iter_step_halving & !use_exact_solver  & k & (HDFE.tolerance > tolerance * 11)
		if (use_heuristic_tol) {
			predicted_eps = predict_eps(eps_history, eps)
			iter_fast_solver = iter_fast_solver & (predicted_eps > tolerance)
		}

		// (a) Update weights: W = μ
		if (verbose > 1) printf("{txt} @@@ HDFE.update_sorted_weights()\n")
		assert_msg(!hasmissing(mu), sprintf("mu has infinite values on iteration %g; aborting", iter), 9003, 0)
		irls_w = true_w :* mu
		HDFE.update_sorted_weights(irls_w)
		HDFE.update_cvar_objects()

		// (b) Update working variable z = η + (y - μ) / μ - offset
		//							 	 = η + y/μ - 1 - offset
		// 	   Note: lim z (μ->0; y=0) = η - 1 - offset + 0/ε
		//							   = η - 1 - offset
		if (rows(offset)) {
			z = eta - offset :- 1 + y :/ mu
			// z = eta - offset :- 1 + exp(log(y) - eta) // Perhaps more accurate?
			if (check_separation) z[zero_sample] = eta[zero_sample] - offset[zero_sample] :- 1
		}
		else {
			z = eta :- 1 + y :/ mu
			// z = eta :- 1 + exp(log(y) - eta) // Perhaps more accurate?
			if (check_separation) z[zero_sample] = eta[zero_sample] :- 1
		}

		// (c) Data is (z, X)
		if (iter_fast_partial) {
			data[., 1] = data[., 1] + z - z_last
			// data[., 1] = data[., 1] - (last_x - data[., 2..cols(data)]) * b[1..k]
		}
		else {
			data = (z, x)
		}
		//last_x = data[., 2..cols(data)]

		// (d.1) Partial out data
		if (verbose > 1) printf("{txt} @@@ HDFE._partial_out()\n")
		_edittozerotol(data, min((tolerance, 1e-12)) ) // see test: hard2.do
		if (iter > 1) (void) --HDFE.verbose
		HDFE._partial_out(data, 0, 0, 0, 1) // Don't standardize vars; flush aux vectors
		if (iter > 1) (void) ++HDFE.verbose
		_edittozerotol(data, min((tolerance, 1e-12)) )
		subiter = subiter + HDFE.iteration_count
		
		// (d.2) Solve β and compute residuals
		if (verbose > 1) printf("{txt} @@@ reghdfe_solve_ols()\n")
		if (iter_fast_solver) {
			// Faster solution (~5% runtime) when still away from converging
			b = fastsolve(data, HDFE.weight)
			if (verbose > 1) b'
			resid = data * (1 \ -b)
		}
		else {
			// Good-quality estimates when close to the solution
			reghdfe_solve_ols(HDFE, data, b=., ., ., ., ., resid=., ., "vce_none")
			if (verbose > 1) b'
		}

		if (verbose > 1) printf("{txt} @@@ updating eta/mu/deviance\n")

		// (e) Update η = z - resid = xβ + d
		if (!iter_step_halving) swap(old_eta, eta) // A faster alternative to "old_eta = eta"
		if (rows(offset)) {
			eta = z - resid + offset
		}
		else {
			eta = z - resid
		}
		if (check_separation) {
			// Add min(eta + 5| y > 0) to log_septol, if that is negative
			// Essentially, this uses a more conservative tolerance if eta is also low when y>0
			// But the effect only kicks in when eta is below -5
			adjusted_log_septol = log_septol + min(( min(select(eta, y:>0)) + 5, 0 ))

			separation_mask = separation_mask :| ( (eta :<= adjusted_log_septol) :& (y :== 0) )
			separated_obs = selectindex(separation_mask)
			N_sep = rows(separated_obs)
		}

		// (f) Update μ = exp(η)
		mu = exp(eta)
		if (N_sep) mu[separated_obs] = J(N_sep, 1, 0)
		_vector_scalar_max(mu, epsilon(100)) // the result might oscillate endlessly if mu is too close to epsilon()

		// (e) Update deviance:
		//	   Dev = 2 { Σ[μ] - Σ[y] + (y>0) * Σ[y log(y/μ)]
		swap(z, z_last)
		old_deviance = deviance
		//deviance = quadsum((mu - y) :* true_w) + quadcross(y, (y :> 0) :* true_w, log(y :/ mu) )
		deviance = quadsum((mu - y) :* true_w) + quadcross(y, (y :> 0) :* true_w, log(y) - eta )
		if (2 * deviance / rows(y) < epsilon(1)) deviance = 0 // We are within macheps accuracy of zero
		deviance = 2 * edittozerotol(deviance, epsilon(1))
		if (deviance < 0) deviance = 0
		delta_deviance = old_deviance - deviance

		// Trick: since Dev>0; in the next iteration ΔDev can't be lower than Dev
		if (!missing(delta_deviance) & (deviance < 0.1 * delta_deviance)) {
			delta_deviance = deviance
			if (verbose > 0) printf("{txt}    - note: deviance is already very close to zero\n")
		}

		// Stopping criteria:
		// - It's HARD to choose a good stopping criteria
		// - Note: unless the model has no constant, sum(y) == sum(mu) at convergence
		if (iter > 1) {

			// Alternatives:
			//eps = abs(delta_deviance) / (0.1 + deviance)							// R criterion: https://github.com/SurajGupta/r-source/blob/a28e609e72ed7c47f6ddfbb86c85279a0750f0b7/src/library/stats/R/glm.R#L302
			//eps = abs(delta_deviance)												// Stata criterion: glm.ado (line 1060)
			//eps = delta_deviance / deviance 										// Julia criterion: https://github.com/JuliaStats/GLM.jl/blob/84da7f178589ebd5aa131e92be5aff8baa9a9636/src/glmfit.jl#L262
			//eps = abs(delta_deviance) / deviance 									// Modified Julia criterion: https://github.com/JuliaStats/GLM.jl/blob/84da7f178589ebd5aa131e92be5aff8baa9a9636/src/glmfit.jl#L262
			//eps = abs(delta_deviance) / (0.1  + min((deviance, old_deviance))) 	// Criterion from version 1 of ppmlhdfe.ado

			// denom_eps = max(( min((deviance, old_deviance)) , 0.1 / stdev_y ))
			denom_eps = max(( min((deviance, old_deviance)) , 0.1 ))
			eps = abs(delta_deviance) / denom_eps
			
			// Never used:
			//eps, delta_deviance, denom_eps, ., min((deviance, old_deviance)), 0.1, 0.1 / stdev_y
			//eps = mreldif(deviance, old_deviance) // maybe this is safer?
			//eps = mean(reldif(deviance, old_deviance))
			//eps = abs(delta_deviance) / (0.1 * stdev_y + min((deviance, old_deviance)))
			//eps = abs(delta_deviance) / max(( min((deviance, old_deviance)) , epsilon(100) ))

			// Declare convergence once we have enough non-accelerated iterations where eps < tol
			if (eps < tolerance) {
				if (use_heuristic_tol & HDFE.accuracy >= 0) {
					// HDFE.accuracy can be -1 with LSMR (LSMR does not update accuracy as it uses multiple tols)
					assert(HDFE.accuracy <= HDFE.tolerance)
					if (!iter_fast_solver & (HDFE.accuracy <= 1.1 * highest_inner_tol | HDFE.G==1)) {
						ok = ok + 1
					}
				}
				else {
					if (!iter_fast_solver & (HDFE.tolerance <= 1.1 * highest_inner_tol | HDFE.G==1)) {
						ok = ok + 1
					}
				}
			}
			else if (use_step_halving & (delta_deviance < 0) & (num_step_halving < max_step_halving)) {
				// Run step-halving AFTER checking for convergence
				eta = step_halving_memory * old_eta + (1 - step_halving_memory) * eta
				if (num_step_halving > 0) update_mask(eta, selectindex(eta:<-10), -10) // If the first step halving was not enough, clip very low values of eta
				mu = exp(eta)
				iter_step_halving = 1
				ok = 0
				num_step_halving = num_step_halving + 1
			}
			else {
				iter_step_halving = 0
				num_step_halving = 0
			}

		}

		// Progress report
		if (verbose > -1 & log) {
			col = 0

			iter_text = sprintf("{txt}{col %2.0f}Iteration %g:", col, iter)
			col = col + 16

			iter_text = iter_text + sprintf("{txt}{col %2.0f}deviance = {res}%-11.5e", col, deviance * stdev_y)
			col = col + 23

			iter_text = iter_text + sprintf("{col %2.0f}{txt}eps = {res}%-9.4e{txt}", col, eps)
			col = col + 16

			iter_text = iter_text + sprintf("{col %2.0f}{txt}iters = {res}%g", col, HDFE.iteration_count)
			col = col + 13

			iter_text = iter_text + sprintf("{col %2.0f}{txt}tol ={res}%5.0e", col, HDFE.tolerance)
			col = col + 14

			min_eta = min(select(eta, !separation_mask))
			iter_text = iter_text + sprintf("{col %2.0f}{txt} min(eta) = {%s}%6.2f", col, min_eta < log_septol - 1 & !check_separation ? "err" : "res", min_eta ) // Add "& verbose>0"
			col = col + 20
			
			//iter_text = iter_text + sprintf("{txt}{col %2.0f}[{txt}%s%s%s%s{txt}] ", col, iter_fast_partial ? " " : "p", iter_fast_solver ? " " : "s", iter_step_halving ? "h" : " ", ok ? "o" : " ")
			iter_text = iter_text + "  {txt}"
			iter_text = iter_text + (iter_fast_partial ? " " : "P")
			iter_text = iter_text + (iter_fast_solver  ? " " : "S")
			iter_text = iter_text + (iter_step_halving ? "H" : " ")
			iter_text = iter_text + (ok ? "O" : " ")

			col = col + 6
			if (N_sep) iter_text = iter_text + sprintf("{col %2.0f}{txt} sep.obs. = {res}%g", col = col, N_sep)
			printf(iter_text + "\n")
		}

		// If using step halving, start a new iteration after the progress report
		if (iter_step_halving) {
			deviance = old_deviance
			continue
		}
		
		if (ok >= min_ok | ok >= 1 & deviance == 0) {
			deviance = deviance * stdev_y
			return(1) // converged=1
		}

		// As IRLS starts to converge, switch to stricter tolerances when partialling out
		if (use_heuristic_tol) {
			if (eps < HDFE.tolerance) {
				// Increase HDFE tol by at least 10x.
				// Go further if IRLS is converging fast enough.
				// But don't increase beyond the user-requested tol!
				// (Note: "max((eps, epsilon(1)))" avoids missing values when eps==0)
				HDFE.tolerance = max((min((0.1 * HDFE.tolerance, alt_tol)), highest_inner_tol))
				alt_tol = 10 ^ -ceil(log10(1 / max((0.1 * eps, epsilon(1)))  ))
			}
			if (use_exact_partial & HDFE.tolerance > tolerance) HDFE.tolerance = 0.1 * tolerance // BUGBUG??

			if (inrange(tolerance, predicted_eps, eps) & inrange(HDFE.tolerance/highest_inner_tol, 1.1, 10.1) & (HDFE.accuracy/highest_inner_tol <= 10.1)) {
				HDFE.tolerance = 0.1 * HDFE.tolerance
			}

		}
		else {

			if (eps < HDFE.tolerance) {
				// Increase HDFE tol by at least 10x.
				// Go further if IRLS is converging fast enough.
				// But don't increase beyond the user-requested tol!
				// (Note: "max((eps, epsilon(1)))" avoids missing values when eps==0)
				HDFE.tolerance = max((min((0.1 * HDFE.tolerance, alt_tol)), highest_inner_tol))
				alt_tol = 10 ^ -ceil(log10(1 / max((0.1 * eps, epsilon(1)))  ))
			}
			if (use_exact_partial & HDFE.tolerance > tolerance) HDFE.tolerance = 0.1 * tolerance // BUGBUG??

		}



		
	}

	return(0) // converged=0
}

end

exit
