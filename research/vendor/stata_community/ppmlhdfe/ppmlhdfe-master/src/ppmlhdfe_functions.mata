* ===========================================================================
* Ancillary functions
* ===========================================================================

mata:



// --------------------------------------------------------------------------
// Extrapolate on the series of log(eps) to predict the need for an exact solver on next iter
// --------------------------------------------------------------------------
// 0=Exact 1=Fast/Accelerated
`Boolean' predict_eps(`Vector' eps_history, `Real' eps)
{
	`Integer'		size, pos
	`Matrix'		rhs, next_rhs
	`Real'			forecast
	`Boolean'		abort_prediction

	size = rows(eps_history)
	pos = nonmissing(eps_history)

	// If there are not enough numbers, just fill history and return
	abort_prediction = pos + 1 < size

	if (pos < size) {
		eps_history[pos + 1] = log(eps)
	}
	else {
		eps_history = eps_history[2::size] \ log(eps)
	}
	if (abort_prediction) return(.)

	rhs = 1::size
	rhs = rhs, rhs :^ 2, rhs :^ 3
	next_rhs = (size + 1)
	next_rhs = next_rhs, next_rhs :^ 2, next_rhs :^ 3
	forecast = next_rhs * qrsolve(rhs, eps_history)
	// printf("Predicted EPS: %8.1e\n", exp(forecast))
	return(exp(forecast))
}


// --------------------------------------------------------------------------
// Least squares QR solver in two steps (that allows reusing the transform)
// --------------------------------------------------------------------------

`Void' qrsolve_part1(`Matrix' X,
                     `Vector' w,
                     `Matrix' H,
                     `Vector' tau,
                     `Matrix' R,
                     `Vector' p)
{
	`Integer'		rank
	H = .
	if (!cols(X)) return
	_hqrdp(H = X :* sqrt(w), tau=., R=., p=.) // Xb = y -> QRp'b = y
}


`Matrix' qrsolve_part2(`Matrix' y,
                       `Vector' w,
                       `Matrix' H,
                       `Matrix' tau,
                       `Matrix' R,
                       `RowVector' p,
                     | `Real'   tol)
{
	`Matrix'		ans
	`Integer'		rank

	if (H == .) return(J(0, 1, .))

	ans = hqrdmultq1t(H, tau, y :* sqrt(w)) // Compute Q1'y (so we now have Rp'b = Q1'y)
	rank = _solveupper(R, ans, tol) // Obtain p'b = inv(R) Q1'y
	ans = ans[invorder(p), .] // Obtain b
	return(ans)
}


// --------------------------------------------------------------------------
// Solve least-squares with equality constraints using weighting method
// --------------------------------------------------------------------------

`Vector' solve_lse(`FixedEffects'	HDFE,
                   `Variable'		y,
                   `Variables'		x,
                   `Variable'		ytilde,
                   `Variables'		xtilde,
                   `Vector' 		unconstrained_sample,
                   `Vector' 		constrained_sample,
                   `Variable'		accelerated_sample,
                   `Real'			acceleration_value,
                   `Variable'		resid,
                   `Real'			epsilon,
                   `Real'			iteration_count,
                   `Boolean'		verbose)
{
	`Integer' 				N, M, K, iter, maxiter
	`Integer'				norm_unconstrained, norm_constrained, M1, M2
	`Vector'				b, b_delta
	`Variable'				w, z // , ytilde
	//`Variables'			xtilde
	`Real'					yy
	`String'				backup_accel

	`Matrix' 				H, R, tau
	`RowVector' 			p

	// Use LSMR here because it works better for ill-conditioned matrices
	assert(HDFE.always_run_lsmr_preconditioner == 1)
	backup_accel = HDFE.acceleration
	// HDFE.acceleration = "lsmr"

	maxiter = 0
	N = rows(y)
	K = cols(x)
	norm_unconstrained = norm(x[unconstrained_sample, .], 1)
	norm_constrained = norm(x[constrained_sample, .], 1)

	// Rule of thumb from Van Loan (1985) page 11 (860)
	M1 = ceil(epsilon(1) ^ (-1/2))
	
	// Conservative criterion from Stewart (1997) page 5 (965), eq 3.8
	// Does not seem to work well in practice (!)
	//M2 = norm_unconstrained / norm_constrained / epsilon(1)

	//M2 = min((M2, 1e12))
	//M1, ., M2, M1/M2
	//M = max((M1, M2))

	M = M1 // Override!

	// Implied tolerance
	yy = cross(y, y)
	epsilon = yy / M * max((norm_unconstrained / norm_constrained, 1)) ^ 2
	epsilon = max((epsilon ^ (1+0.5*maxiter), 1e-8)) // It should be 1+maxiter but we are playing safe
	
	w = create_mask(N, M, unconstrained_sample, 1)
	if (rows(accelerated_sample)) update_mask(w, accelerated_sample, acceleration_value)

	assert(N == rows(x))

	// Update weights and solve weighted least squares
	HDFE.load_weights("aweight", "<placeholder>", w, 0) // Type, Var, Weight, Verbose
	HDFE._partial_out(ytilde, 0, 0, 0, 1) // Don't standardize vars; flush aux vectors
	if (K) {
		HDFE._partial_out(xtilde, 0, 0, 0, 1) // Don't standardize vars; flush aux vectors
	}
	else {
		xtilde = J(N, 0, .) 
	}

	//b = qrsolve_manual(xtilde, ytilde, w)
	qrsolve_part1(xtilde, w, H=., tau=., R=., p=.)
	b = qrsolve_part2(ytilde, w, H, tau, R, p)
	resid = ytilde - xtilde * b

	// Refinements
	for (iter=1; iter<=maxiter; iter++) {
		update_mask(z=resid, unconstrained_sample, 0)
		HDFE._partial_out(ytilde=z, 0, 0, 0, 1)
		b_delta = qrsolve_part2(ytilde, w, H, tau, R, p)
		resid = resid - (z - ytilde) - (xtilde * b_delta)
		b =  b + b_delta
	}

	HDFE.acceleration = backup_accel
	iteration_count = HDFE.iteration_count
	return(b)
}
	

// --------------------------------------------------------------------------
// Trim data given a list of separated obs. that will be removed
// --------------------------------------------------------------------------

`Variable' trim_separated_obs(`FixedEffects' HDFE,
						      `Variable' y,
						      `Variables' x,
						      `String' weight_type,
						      `String' weight_var,
						      `Variable' true_w,
						      `Vector' separated_obs,
						      `Boolean' verbose)
{

	`Integer'				n, k, backup_verbose, num_singletons, new_singletons
	`Vector'				tmp_sample, backup_sample
	`Variables'				tmp_mask
	`Variable' 				ok_obs_mask // Mask (0/1) of obs separated or potentially separated

	assert(rows(separated_obs)) // else, don't call it!

	n = rows(x)
	k = cols(x)
	ok_obs_mask = create_mask(n, 1, separated_obs, 0)
	separated_obs = . // Discarded

	// Sanity checks
	assert(rows(y) == n)
	assert(HDFE.N == n)
	assert(rows(HDFE.sample) == n)
	assert_in(rows(true_w) , (1, n))
	assert(cols(HDFE.indepvars) == k)

	// Construct new HDFE object based on reduced sample
	tmp_sample = selectindex(ok_obs_mask)
	HDFE.sample = HDFE.sample[tmp_sample]
	backup_sample = HDFE.sample
	HDFE.save_touse() // varname, replace (BUGBUG: need to set touse=1)
	HDFE.weight_var = weight_var
	HDFE.weight_type = weight_type
	backup_verbose = HDFE.verbose
	HDFE.verbose = verbose // Set higher verbose level, to see dropped singletons

	num_singletons = HDFE.num_singletons
	HDFE = HDFE.reload(0)
	new_singletons = HDFE.num_singletons
	HDFE.num_singletons = num_singletons + new_singletons

	HDFE.verbose = backup_verbose

	// Adjust obs in case more singletons were detected
	assert(rows(backup_sample) >= rows(HDFE.sample))
	if (new_singletons) {
		assert(rows(backup_sample) > rows(HDFE.sample))
		tmp_mask = create_mask(st_nobs(), 0, HDFE.sample, 1)
		// Tricky line: observations of -ok_obs_mask- that are now dropped
		tmp_sample = select(selectindex(ok_obs_mask), !tmp_mask[backup_sample])
		update_mask(ok_obs_mask, tmp_sample, 0)
		tmp_sample = selectindex(ok_obs_mask)
	}
	backup_sample = tmp_mask = .

	// Update data
	y = y[tmp_sample]
	x = x[tmp_sample, .]
	if (weight_var != "") true_w = true_w[tmp_sample]

	// Return so other vectors can be updated (mu, offset, etc.)
	return(tmp_sample)
}


// --------------------------------------------------------------------------
// Tag and remove collinear variables
// --------------------------------------------------------------------------
	
`Void' remove_collinears(`FixedEffects'	HDFE,
	 					 `Real'			tolerance,
	 					 `Variables'	x,
	 					 `Integer'		k,
	 					 `RowVector'	stdev_x,
	 					 `String'		weight_type,
	 					 `String'		weight_var,
	 					 `Variable'		true_w,
	 					 `Integer'		verbose)
{
	`RowVector'				ok_vars, collinear_vars
	`StringRowVector' 		tmp_names
	`Variables'				data
	`Real'					backup_tolerance
	`String'				backup_weight_type, backup_weight_var
	`Variable'				backup_weight
	`Integer'				num_collinear

	if (!k) return
	if (verbose > 0) printf("{txt} $$ - Finding separated variables\n")
	assert(rows(stdev_x)==1)

	// 1) Partial out regressors
	// a) Backup weights and tol
	backup_tolerance = HDFE.tolerance
	backup_weight_type = HDFE.weight_type
	backup_weight_var = HDFE.weight_var
	backup_weight = HDFE.weight
	// b) Update weights and tol
	HDFE.load_weights(weight_type, weight_var, true_w, verbose) // Before, HDFE.weight was just -depvar-!
	HDFE.tolerance = tolerance
	// c) Partial out
	(void) --HDFE.verbose
	HDFE._partial_out(data=x, 0, 0, 0, 1) // don't save tss, don't standardize vars, no depvar, flush
	(void) ++HDFE.verbose
	// d) Restore weights and tol
	HDFE.load_weights(backup_weight_type, backup_weight_var, backup_weight, verbose)
	HDFE.tolerance = backup_tolerance
	backup_weight = .

	num_collinear = select_not_collinear(data, true_w, ok_vars=.)
	if (!num_collinear) return
	collinear_vars = selectindex(create_mask(k, 1, ok_vars', 0))' // Collinear variables
	if (verbose > -1) {
		tmp_names = invtokens(HDFE.indepvars[collinear_vars])
		printf("{txt}note: %g variable%s omitted because of collinearity: {res}%s{txt}\n", num_collinear, num_collinear > 1 ? "s" : "", tmp_names)
	}

	x = x[., ok_vars]
	stdev_x = stdev_x[ok_vars]

	// Update HDFE omitted vars
	HDFE.not_basevar[selectindex(HDFE.not_basevar)[collinear_vars]] = J(1, cols(collinear_vars), 0)
	assert_msg(cols(HDFE.not_basevar) == cols(tokens(HDFE.fullindepvars)), "Wrong size of not_basevar")
	HDFE.indepvars = tokens(HDFE.fullindepvars)[selectindex(HDFE.not_basevar)] // is there any problem of doing it this way?
	HDFE.varlist = HDFE.varlist[1], HDFE.indepvars
	assert(rows(HDFE.indepvars) == 1)

	// Update K (used by caller code)
	k = cols(x)
	assert(k == sum(HDFE.not_basevar))
}


//`RowVector' flag_collinears(`Variables' x, `Variable' w)
`Integer' select_not_collinear(`Variables' x, `Variable' w, `RowVector' ok_vars)
{
	`Matrix'				xx
	`Integer'				num_collinear

	assert(ok_vars == .)
	xx = quadcross(x, w, x)
	// Compute inv(xx); see -reghdfe_rmcoll- for some nuances
	(void) reghdfe_rmcoll(strofreal(1..cols(x)), xx, ok_vars)
	num_collinear = cols(xx) - cols(ok_vars)
	return(num_collinear) // We also update and return -ok_vars-
}


// --------------------------------------------------------------------------
// Independent functions
// --------------------------------------------------------------------------

// Fast (but less accurate) LS solver (used within the IRLS iteration)
`Vector' fastsolve(`Variables' data, `Variable' w)
{
	`Integer'		k
	`Matrix'		xyxy
	k = cols(data)
	xyxy = cross(data, w, data)
	return(qrsolve(xyxy[2..k, 2..k], xyxy[2..k, 1]))
}


// Replace mu = max(mu, 5e-2 y, 1e-3)
`Void' censor_mu(`Variable' mu, `Variable' y, `Boolean' verbose)
{
	`Vector' censor_values, censor_index
	censor_values = rowmax((5e-2 * y, J(rows(y), 1, 1e-3)))
	censor_index = selectindex(mu :< censor_values)
	if (rows(censor_index) & (verbose > 2)) printf("{txt} @@ %g initial values of mu are too low; tweaking them\n", rows(censor_index))
	mu[censor_index] = censor_values[censor_index]
}


// Equivalent to "y = max(y, x)" with x scalar
`Void' _vector_scalar_max(`Variable' y, `Real' x)
{
	`Vector' censor_index
	censor_index = selectindex(y :< x)
	if (rows(censor_index)) y[censor_index] = J(rows(censor_index), 1, x)
}

	

// Add back rows/cols of b and V to account for omitted variables
void add_base_variables(
	`FixedEffects'	S,
	`Vector'		b,
	`Matrix'		V)
{
	`Integer'		k
	`Vector'		idx
	`Vector'		temp_b
	`Matrix'		temp_V

	if (S.not_basevar == J(1, 0, .)) return
	if (S.verbose > 1) printf("\n{txt}@@ Adding base variables to varlist\n")
	k = cols(S.not_basevar)
	assert_msg(cols(S.not_basevar) == k, "cols(S.not_basevar) == k")
	idx = selectindex(S.not_basevar)
	swap(b, temp_b)
	swap(V, temp_V)
	b = J(k, 1, 0)
	V = J(k, k, 0)
	b[idx, 1] = temp_b
	V[idx, idx] = temp_V
}

	
end
