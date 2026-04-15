* ===========================================================================
* Detect separation through iterative least squares with equalities (LSE) applied on ReLU outcome
* ===========================================================================

mata:

`Integer' relu_fix_separation(`FixedEffects'	HDFE,
							  `Variables'		y,
							  `Variables'		x,
							  `Integer'			k,
							  `RowVector'		stdev_x,
							  `Variable'		true_w,
							  `String'			weight_type,
							  `String'			weight_var,
							  `Real'			target_inner_tol,
							  `Real'			tol,
							  `Real'			zero_tol,
							  `Integer'			maxiter,
							  `Varname'			sepname,
							  `Varname'			zname,
							  `Boolean'			debug,
							  `Boolean'			report_r2,
							  `Vector'			non_separated_obs,
							  `Boolean'			strict,
							  `Boolean'			accelerate,
							  `Boolean'			verbose)
{
	// Note: currently ignoring weights (weight_type, weight_var) as the algorithm does not care about them

	 // , num_drop, num_collinear
	`Integer'				n, num_boundary, iter, num_sep, v, col, backup_verbose, total_iter, ic
	`Real'					delta, uu, backup_tol, regtol, epsilon
	`Real'					ee, ee_cumulative, ee_boundary
	`Variable'				is_boundary, u, w, resid, xbd
	`Vector'				boundary_sample, interior_sample, idx, separated_obs, b
	`String'				end_of_table, table_row

	`Boolean'				convergence_is_stuck
	`Integer'				num_candidates, num_candidates1, num_candidates2
	`Real'					progress_ratio, progress_ratio1, progress_ratio2
	`Variable'				xbd_prev1, xbd_prev2
	`Vector'				accelerated_sample
	`Real'					acceleration_value
	`Real'					threshold

	`Vector'				utilde, u_last
	`Matrix'				xtilde

	// 1. Validate and initialize parameters
	v = sepname != "" ? max((verbose, 1)) : verbose // tagsep.ado mode will always have verbose>0
	assert(non_separated_obs==.) // We'll return info here
	regtol = tol ^ 2
	assert_msg(0 < tol & tol < 1, "tol outside limits")
	if (regtol < 1e-13) regtol = 1e-13 // We can't get too close to machine epsilon; 1e-13 or 1e-12 is about the max reghdfe can do

	// 2. Initialize variables
	n = rows(y)
	u = is_boundary = !y
	boundary_sample = selectindex(is_boundary)
	interior_sample = selectindex(!is_boundary)
	num_boundary = rows(boundary_sample)
	separated_obs = J(0, 1, .)
	accelerated_sample = J(0, 1, .)
	acceleration_value = 1 // Weight given to accelerated obs (obs where y==0 and xbd<0 for a few iterations)

	convergence_is_stuck = 0
	xbd = xbd_prev1 = xbd_prev2 = .

	if (v > 0) printf("{txt}\n $$ Starting -relu- separation test on {res}%g{txt} suspect obs.\n", num_boundary)
	if (v > 0) printf("{txt} $$ Parameters: regtol ={res}%2.0e{txt}  tol ={res}%2.0e{txt}  maxiter ={res}%3.0fc{txt}\n", regtol, tol, maxiter)
	
	if (!num_boundary) {
		if (v > 0) printf("{txt} $$ No boundary observations; exiting\n")
		relu_post_results(HDFE, sepname, zname, debug, report_r2, separated_obs, J(n, 1, 0), v)
		return(0)
	}
	
	backup_verbose = HDFE.verbose
	backup_tol = HDFE.tolerance
	HDFE.verbose = verbose - 1
	HDFE.tolerance = regtol

	uu = quadcross(u, u)
	num_sep = 0
	total_iter = 0 // Total iteration count (within HDFE)

	u_last = .

	if (v > 0) printf(" {txt}{c TLC}{hline 5}{c TT}{hline 11}{c TT}{hline 11}{c TT}{hline 7}{c TT}{hline 11}{c TT}{hline 15}{c TT}{hline 14}{c TRC}\n")
	if (v > 0) printf(" {txt}{c |}  i  {c |}    u'u    {c |}    e'e    {c |}  LB %% {c |}   min(e)  {c |}    Epsilon    {c |} # Candidates {c |}\n")
	if (v > 0) printf(" {txt}{c LT}{hline 5}{c +}{hline 11}{c +}{hline 11}{c +}{hline 7}{c +}{hline 11}{c +}{hline 15}{c +}{hline 14}{c RT}\n")
	end_of_table = " {txt}{c BLC}{hline 5}{c BT}{hline 11}{c BT}{hline 11}{c BT}{hline 7}{c BT}{hline 11}{c BT}{hline 15}{c BT}{hline 14}{c BRC}\n"

	for (iter=1; iter<=maxiter; iter++) {

		swap(xbd_prev2, xbd_prev1) 	// xbd_prev2 = xbd_prev1
		swap(xbd_prev1, xbd)		// xbd_prev1 = xbd

		if (iter == 1) {
			utilde = u
			xtilde = x
		}
		else {
			utilde = u + utilde - u_last
			// xtilde = xtilde
		}
		u_last = u

		// Weights
		b = solve_lse(HDFE, u, x, utilde, xtilde, boundary_sample, interior_sample,
		              accelerated_sample, acceleration_value,
		              resid=., epsilon=., ic=., verbose)
		total_iter = total_iter + ic
		delta = epsilon + tol
		xbd = u - resid

		uu = quadcross(u, u)
		ee = quadcross(resid, resid)

		if (v > 0 & iter == 1) {
			ee_cumulative = 0
			ee_boundary = uu
		}
		else {
			ee_cumulative = ee_cumulative + ee
		}


		// Output iteration output
		num_candidates = sum(xbd[boundary_sample]:>delta)
		ee_cumulative = ee_cumulative + ee
		progress_ratio = 100 * ee_cumulative / ee_boundary

		// Update criteria for stuck convergence
		// if (!convergence_is_stuck) convergence_is_stuck = accelerate & (iter> 3) & (progress_ratio < progress_ratio1 + 0.5) & (progress_ratio1 < progress_ratio2 + 0.5) & (num_candidates == num_candidates2)
		if (!convergence_is_stuck) convergence_is_stuck = accelerate & (iter> 3) & (progress_ratio - progress_ratio2 < 1.0) & (num_candidates == num_candidates2)
		accelerated_sample = convergence_is_stuck ? selectindex(!y :& (xbd_prev2 :< 1.01 * xbd_prev1) :& (xbd_prev1 :< 1.01 * xbd) :& (xbd :< (-0.1 * delta)  )) : J(0, 1, .)
		acceleration_value = convergence_is_stuck & rows(accelerated_sample) ? min((256, 4 * acceleration_value)) : 1
		// Question: once we turn acceleration on for a given obs, should we leave it on forever?

		if (v > 0) {
			col = 0
			table_row = sprintf("{txt} {c |} %3.0f {c |}", iter)
			//table_row = table_row + sprintf(" {col %2.0f}{c |}", subiter ? sprintf("%3.0f", subiter) : "", col = col + 14)
			table_row = table_row + sprintf("%10.6f {col %2.0f}{c |}", uu, col = col + 12)
			table_row = table_row + sprintf("%10.6f {col %2.0f}{c |}", ee, col = col + 12)
			table_row = table_row + sprintf(" %5.1f {col %2.0f}{c |}", progress_ratio, col = col + 8)
			table_row = table_row + sprintf("%10.6f {col %2.0f}{c |}", min(resid), col = col + 12)
			table_row = table_row + sprintf("%14.8f {col %2.0f}{c |}", delta, col = col + 16)
			table_row = table_row + sprintf("%12.0fc {col %2.0f}{c |}", num_candidates, col = col + 23)
			if (convergence_is_stuck & rows(accelerated_sample)) table_row = table_row + sprintf(" Accelerating %f obs (w=%f)", rows(accelerated_sample), acceleration_value)
			printf(table_row + "\n")
			//mm_matlist(xbd[1..10]', "%6.4f", 0, "", "")
			//accelerated_sample'
		}

		//mm_matlist((y, J(rows(y), 1, .), u, xbd, resid, is_ignored))
		// Update stuck-related variables
		progress_ratio2 = progress_ratio1
		progress_ratio1 = progress_ratio
		num_candidates2 = num_candidates1
		num_candidates1 = num_candidates
		progress_ratio = num_candidates = .

		// Update xbd -> 0 when y>0
		update_mask(xbd, interior_sample, 0)

		// Update xbd -> 0 when y=0 and xbd is within tolerance of zero
		// (the "0.1" is because I need to be more strict below zero, to avoid false positives)
		idx = select(boundary_sample, inrange(xbd[boundary_sample], -0.1 * delta, delta)) // Do I need to change the 0.1 to e.g. 0.5?
		//idx = select(boundary_sample, abs(xbd[boundary_sample]) :<= delta) // Do I need to change the 0.1 to e.g. 0.5?
		if (length(idx)) update_mask(xbd, idx, 0)

		// Declare separation if xbd>=0 when y==0 (of course, at this point xbd=0 when y>0)
		if (all(xbd[boundary_sample] :>= 0)) {
			num_sep = sum(xbd[boundary_sample] :> 0)
			if (v > 0) printf(end_of_table)
			if (v > 0) printf("{txt} $$ Stopping (no negative predicted values); separation found in {res}%f{txt} observations (%g iterations and %g subiterations)\n", num_sep, iter, total_iter)
			break
		}
		
		// Declare separation if there are no negative residuals
		// - This is due to the normal equations: X'e=0
		// - Since z=xγ>0, then z'e=0. When e_i>0 this is only possible if z_i=0 i.e. there is no more separated obs. left to uncover
		//   (there might be separated obs. when e_i=0; see the proof for more details on why this works)
		// - This case is particularly useful in accelerating convergence when there is *no separation*, see "example_negative_residuals.do"
		
		_edittozerotol(resid, zero_tol) // Maybe we want to link this value with tol? so this is e.g. tol/100 ?
		threshold = 0 // delta might be better, due to numerical errors
		if (min(resid[boundary_sample]) >= threshold) {
			idx = select(boundary_sample, resid[boundary_sample] :> delta)
			if (length(idx)) update_mask(xbd, idx, 0)
			num_sep = sum(xbd[boundary_sample] :> 0)
			if (v > 0) printf(end_of_table)
			printf("{txt} $$ Stopping (no negative residuals); separation found in {res}%f{txt} observations (%g iterations and %g subiterations)\n", num_sep, iter, total_iter)
			break
		}

		if (iter == maxiter) {
			if (v > 0) printf(end_of_table)
			if (strict) {
				assert_msg(0, "separation via ReLU algorithm: maximum number of iterations reached; aborting", 9010, 0)
			}
			else {
				printf("{err}(ReLU separation check: maximum number of iterations reached; aborting)\n")
				return(0)
			}
		}

		// Apply ReLU function
		u[boundary_sample] = rowmax((xbd[boundary_sample], J(num_boundary, 1, 0) ))

	} // End for-loop

	HDFE.verbose = backup_verbose
	HDFE.tolerance = backup_tol

	if (!num_sep) {
		if (v > 0) printf("{txt} $$ - No separation found; stopping (%g iterations and %g subiterations)\n", iter, total_iter)
		relu_post_results(HDFE, sepname, zname, debug, report_r2, separated_obs, J(n, 1, 0), v)
		return(num_sep)
	}

	if (verbose > -1) printf(`"{txt}(ReLU method dropped %g {browse "http://scorreia.com/research/separation.pdf":separated observation%s} in %g iterations)\n"', num_sep, num_sep > 1 ? "s" : "", iter)
	separated_obs = select(boundary_sample, xbd[boundary_sample] :> 0)
	relu_post_results(HDFE, sepname, zname, debug, report_r2, separated_obs, xbd, v) // Do this BEFORE trimming the data!
	if (report_r2) return(num_sep) // exit early if we are just printing the certificate of separation

	non_separated_obs = trim_separated_obs(HDFE, y, x, weight_type, weight_var, true_w, separated_obs, verbose)
	remove_collinears(HDFE, target_inner_tol, x, k, stdev_x, weight_type, weight_var, true_w, verbose)
	return(num_sep) // Also returns ok_obs_mask and ok_var_mask
}


`Void' relu_post_results(`FixedEffects'	HDFE,
						 `Varname'		sepname,
						 `Varname'		zname,
						 `Boolean'		debug,
						 `Boolean'		report_r2,
						 `Vector'		separated_obs,
						 `Variable'		z,
						 `Boolean'		verbose)
{
	`Variable'				is_separated
	`Boolean'				var_exists
	`Integer'				idx
	`String'				cmd

	if (sepname == "") return
	is_separated = create_mask(HDFE.N, 0, separated_obs, 1)
	var_exists = !missing(_st_varindex(sepname))
	if (var_exists) st_dropvar(sepname) // Drop the variable if already exists; dangerous but this is a secret feature anyways
	idx = st_addvar("byte", sepname)
	st_store(HDFE.sample, idx, is_separated)
	st_varlabel(idx, "[ppmlhdfe: ReLU] Obs. is separated")
	if (verbose > 0) printf("{txt} $$ - Saved separated observations in {res}%s\n", sepname)

	if (zname == "") return
	var_exists = !missing(_st_varindex(zname))
	if (var_exists) st_dropvar(zname)
	idx = st_addvar("double", zname)
	prettify_z(z)
	st_store(HDFE.sample, idx, z)
	st_varlabel(idx, "[ppmlhdfe: ReLU] Certificate of separation")
	if (verbose > 0) printf("{txt} $$ - Saved certificate of separation in {res}%s\n", zname)

	if (!report_r2 | !rows(separated_obs)) return
	cmd = HDFE.absvars == "" ? "noabsorb" : sprintf("absorb(%s)", invtokens(HDFE.absvars))
	cmd = sprintf("reghdfe %s %s, %s", zname, invtokens(HDFE.indepvars), cmd)
	printf("\n{inp}{hline 32} o {hline 32}\n")
	printf("{bf:Verifying certificate of separation:}\n")
	printf("{inp}{bf:. %s}\n", cmd)
	stata(cmd)
	printf("{inp}{hline 32} o {hline 32}\n\n")
}


`Void' prettify_z(`Vector' z)
{
	`Factor'				F
	`Vector'				zz
	`Integer'				i
	`Real'					rescale_factor

	// Find out the -mode- of z[z>0] and rescale by that
	zz = round(1e6 * select(z, z :> 0))
	if (!rows(zz)) return
	
	F = _factor(zz, 1, 0, "", 0, 1)
	maxindex(F.counts, 1, i=., .)
	rescale_factor = (1e6 / zz[i[1]])
	if (0.01 <= rescale_factor & rescale_factor <= 100) {
		z = z * rescale_factor
	}
}

end


/* Algorithm:

1) Define a working depvar u = (y == 0)
2) Solve LSE problem through method of weighting
	(i.e. run a weighted regression on u, with very high weights when y>0)
3) Update -u- with ReLU function
	(i.e. "predict uhat", and then "replace u = max(uhat, 0)")
4) Stop if there is no solution to LSE or if uhat>=0

References:

Method of weighting and least-squares with equality constraints:
- https://link.springer.com/article/10.1007/BF02510363
- https://www.jstor.org/stable/2157402

 */
