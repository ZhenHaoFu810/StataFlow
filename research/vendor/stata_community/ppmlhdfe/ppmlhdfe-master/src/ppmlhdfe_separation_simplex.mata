* ===========================================================================
* Detect separation through simplex method
* ===========================================================================

mata:

// Note:
// *_sample is a list of observations (thus, a vector with values in 1..N)
// *_mask is a N*1 vector with values in {0,1}
// flagged_* is for vars/obs flagged as possibly separating (due to their y>0 behavior)


`Integer' simplex_fix_separation(`FixedEffects'	HDFE,
								 `Variables'	y,
								 `Variables'	x,
								 `Integer'		k,
								 `RowVector'	stdev_x,
								 `Variable'		true_w,
								 `String'		weight_type,
								 `String'		weight_var,
								 `Real'			tolerance,
								 `Real'			simplex_tolerance,
								 `Integer'		simplex_maxiter,
								 `Vector'		non_separated_obs,
								 `Boolean'		verbose)
{
	`Integer'				n, num_drop, num_collinear
	`Vector'				flagged_sample, b, separated_obs
	`RowVector'				flagged_vars, tmp_vars, flagged_var_mask, ok_var_mask, ok_vars, collinear_vars
	`RowVector'				all_zero, all_positive, all_negative
	`StringRowVector' 		tmp_names
	`Matrix'				ranges
	`Variable'				w, ok_obs_mask
	`Variables'				data, flagged_data, tmp_mask
	`Real'					backup_tolerance
	`Integer'				rc
	`Boolean'				simplex_flagged_separation


// --------------------------------------------------------------------------
// Prelude
// --------------------------------------------------------------------------

	if (!k) return(0)

	ok_obs_mask = (y :> 0)
	n = rows(x)
	if (verbose > 0) printf("{txt}\n $$ Starting -simplex- separation test on %g regressors and %g suspect obs.\n", k, n-sum(ok_obs_mask))
	num_drop = 0

	// Sanity checks
	assert(rows(y) == n)
	assert(HDFE.N == n)
	assert(cols(HDFE.indepvars) == k)
	assert(rows(ok_obs_mask) == n)
	assert_in(rows(true_w) , (1, n))
	assert(non_separated_obs==.) // Return info here

	// Restrict sample by updating weights (set them to zero on -excluded_sample-)
	if (verbose > 0) printf("{txt}\n $$ Restricting sample to non-suspect observations\n")
	w = ok_obs_mask :* (weight_type == "fweight" ? true_w : 1)
	HDFE.load_weights("fweight", "<placeholder>", w, verbose)
	

	// ok_obs_mask: three possible values at the end: 0 (y=0, drop), 1 (y=0, keep), 2 (y>0)
	ok_obs_mask = ok_obs_mask :+ 1 // only do this after updating weights


// --------------------------------------------------------------------------
// Partial out regressors on y>0 sample
// --------------------------------------------------------------------------
	backup_tolerance = HDFE.tolerance
	HDFE.tolerance = tolerance
	if (verbose > 0) printf("{txt} $$ - Demeaning regressors (tol=%-1.0e)\n", HDFE.tolerance)
	HDFE._partial_out(data=x, 0, 0, 0, 1)  // don't save tss, don't standardize vars, no depvar, flush
	HDFE.tolerance = backup_tolerance


// --------------------------------------------------------------------------
// Find out collinear regressors on y>0 sample
// --------------------------------------------------------------------------

	if (verbose > 0) printf("{txt} $$ - Checking for collinearity in demeaned regressors (over y > 0)\n")
	assert_msg(rows(data)==rows(w))
	num_collinear = select_not_collinear(data, w, ok_vars=.)
	if (!num_collinear) {
		if (verbose > 0) printf("{txt} $$   DONE: demeaned regressors have full rank in the (y > 0) sample\n")
		return(0)
	}
	flagged_var_mask = create_mask(k, 1, ok_vars', 0)'
	flagged_vars = selectindex(flagged_var_mask) // Collinear variables
	if (verbose > 0) {
		tmp_names = invtokens(HDFE.indepvars[flagged_vars])
		printf("{txt} $$   Demeaned regressors don't have full rank (over y > 0); %g vars flagged for possible deletion: {res}%s{txt}\n", num_collinear, tmp_names)
	}


// --------------------------------------------------------------------------
// Construct residuals of flagged regressors on y=0 sample
// --------------------------------------------------------------------------

	// No need to construct resids if there are no unflagged variables!
	flagged_sample = selectindex(ok_obs_mask :== 1) // remember that ok_obs_mask takes values (0,1,2)
	if (cols(flagged_vars) == k) {
		if (verbose > 0) printf("{txt} $$ - Note: all variables are flagged as potentially suspect\n")
		data = data[flagged_sample, .]
	}
	else {
		if (verbose > 0) printf("{txt} $$ - Computing residuals of flagged variables\n")
		// Equivalent to:
		// 1) regress x_suspect x_ok if y > 0
		// 2) predict resid if y == 0
		flagged_data = data[., flagged_vars] // Data for suspect regressors
		data = data[., selectindex(!flagged_var_mask)] // Data for other regressors

		b = qrsolve(data :* sqrt(w), flagged_data :* sqrt(w))
		data = flagged_data[flagged_sample, .] - data[flagged_sample, .] * b // Residuals
		_edittozerotol(data, epsilon(100)) // Values lower than 1e-14 will be rounded to zero
		flagged_data = b = . // save memory
	}


// --------------------------------------------------------------------------
// Test 1: inspect each residual and see if all its values have the same sign
// --------------------------------------------------------------------------

	if (verbose > 0) printf("{txt} $$ - Inspecting residuals of %g variables\n", cols(data))
	ok_var_mask = J(1, k, 1)
	ranges = colminmax(data)
	_edittozerotol(ranges, simplex_tolerance) // Allow for numerical errors (partialling out, ols, resids)
	all_zero = (ranges[1, .] :== 0) :& (ranges[2, .] :== 0)
	all_positive = ranges[1, .] :>= 0
	all_negative = ranges[2, .] :<= 0
	tmp_mask = J(rows(data), 1, 0) // mask with the obs within the flagged sample (y==0) that will be dropped

	// We can remove this part as collinearity should be checked before separation
	if (any(all_zero)) {
		tmp_vars = selectindex(all_zero)
		tmp_vars = flagged_vars[tmp_vars]
		ok_var_mask[tmp_vars] = J(1, cols(tmp_vars), 0)
		tmp_names = invtokens(HDFE.indepvars[tmp_vars])
		if (verbose > 0) printf("{txt} $$   Note: residuals of %g variables are collinear: {res}%s{txt}\n", cols(tmp_vars), tmp_names)
	}

	if (any(all_positive)) {
		tmp_vars = selectindex(all_positive)
		tmp_mask = tmp_mask :| (rowsum(edittozerotol(data[., tmp_vars], simplex_tolerance)) :> 0)
		update_mask(ok_obs_mask, select(flagged_sample, tmp_mask), 0)
		tmp_vars = flagged_vars[tmp_vars]
		ok_var_mask[tmp_vars] = J(1, cols(tmp_vars), 0)
		tmp_names = invtokens(HDFE.indepvars[tmp_vars])
		if (verbose > 0) printf("{txt} $$   Found %g separated obs.; residuals of %g vars have coef of -infinity: {res}%s{txt}\n", sum(tmp_mask), cols(tmp_vars), tmp_names)
	}

	if (any(all_negative)) {
		tmp_vars = selectindex(all_negative)
		tmp_mask = tmp_mask :| (rowsum(edittozerotol(data[., tmp_vars], simplex_tolerance)) :< 0)
		update_mask(ok_obs_mask, select(flagged_sample, tmp_mask), 0)
		tmp_vars = flagged_vars[tmp_vars]
		ok_var_mask[tmp_vars] = J(1, cols(tmp_vars), 0)
		tmp_names = invtokens(HDFE.indepvars[tmp_vars])
		// Small issue: the message below will include the obs. dropped by the previous check (>0)
		if (verbose > 0) printf("{txt} $$   Found %g separated obs.; residuals of %g vars have coef of +infinity: {res}%s{txt}\n", sum(tmp_mask), cols(tmp_vars), tmp_names)
	}

	// If we found separated obs/vars, trim the flagged data
	if (!all(ok_var_mask)) {
		data = data[selectindex(!tmp_mask), selectindex(ok_var_mask[flagged_vars])]
		flagged_var_mask = flagged_var_mask :& ok_var_mask
		flagged_vars = selectindex(flagged_var_mask)
		flagged_sample = selectindex(ok_obs_mask:==1)
	}
	else {
		if (verbose > 0) printf("{txt} $$   No variables dropped in step 1 of separation check\n")
	}

	if (cols(data) > 1) {
		// Drop collinear variables from the trimmed data
		// (else, they would be redundant AND mess up with the simplex code)
		assert(rows(data)==rows(flagged_sample))
		num_collinear = select_not_collinear(data, w[flagged_sample], ok_vars=.)
		ok_var_mask[flagged_vars] = create_mask(cols(data), 0, ok_vars', 1)'

		if (verbose > 0 & num_collinear) {
			collinear_vars = selectindex(create_mask(k, 1, ok_vars', 0))
			tmp_names = invtokens(HDFE.indepvars[collinear_vars])
			printf("{txt} $$   Found %g collinear vars after step 1 of separation check: {res}%s{txt}\n", num_collinear, tmp_names)
		}

		// Update current objects (data and flagged_vars)
		data = data[., ok_vars]
		flagged_var_mask = flagged_var_mask :& ok_var_mask
		flagged_vars = selectindex(flagged_var_mask)
	}


// --------------------------------------------------------------------------
// Test 2: Apply simplex and look for lin.comb. of the residuals that are >= or <=
// --------------------------------------------------------------------------

	// Need to call it even with 1 col, unless I repeat Test 1 until there are no more left (or if test 1 didn't detect anything)
	if ( cols(data) > 1 | (cols(data)==1 & !all(ok_var_mask)) ) {

		if (verbose > 0) {
			tmp_names = invtokens(HDFE.indepvars[flagged_vars])
			printf("{txt}\n $$ - Starting simplex method on %g obs and %g variables: {res}%s\n", rows(data), cols(data), tmp_names)
		}
		rc = simplex_flag_separated_obs(data, simplex_maxiter, tmp_mask=., verbose)
		if (rc) {
			printf("{err}simplex iteration failed:\n")
			exit(error(rc))
		}

		// tmp_mask is 1 for ok and 0 for sep
		simplex_flagged_separation = !all(tmp_mask)
		if (simplex_flagged_separation) {
			update_mask(ok_obs_mask, select(flagged_sample, !tmp_mask), 0)
		}
	}
	else {
		simplex_flagged_separation = 0
	}

	ok_obs_mask = !!ok_obs_mask // Set 1 and 2 to 1, leave 0 as it is


// --------------------------------------------------------------------------
// Epilogue: trim data
// --------------------------------------------------------------------------

	data = flagged_sample = . // save memory // flagged_var_mask = 
	assert(all(ok_obs_mask :==0 :| ok_obs_mask :==1))
	num_drop = n - sum(ok_obs_mask)

	if (num_drop == 0) {
		if (verbose > 0) printf("{txt} $$ - No separation found; stopping\n")
		ok_var_mask = J(1, k, 1)
		assert(ok_obs_mask == J(n, 1, 1))
		return(0)
	}

	if (verbose > -1) printf(`"{txt}(simplex method dropped %g {browse "http://scorreia.com/research/separation.pdf":separated observation%s})\n"', num_drop, num_drop > 1 ? "s" : "")
	separated_obs = selectindex(!ok_obs_mask)
	non_separated_obs = trim_separated_obs(HDFE, y, x, weight_type, weight_var, true_w, separated_obs, verbose)
	remove_collinears(HDFE, tolerance, x, k, stdev_x, weight_type, weight_var, true_w, verbose)
	return(num_drop) // Also returns ok_obs_mask and ok_var_mask
}


// Run modified Simplex and detect separated observations
// INPUT: Matrix of suspect residual vars on suspect observations
// Also see:
// - http://www.math.wsu.edu/faculty/dzhang/201/Guideline%20to%20Simplex%20Method.pdf

`Boolean' simplex_flag_separated_obs(
	`Variables'		X,
	`Integer'		maxiter,
	`Variable'		keep_mask,
	`Integer'		verbose)
{
	//`Vector'		coefs // Always zero in our case
	`Vector'		tmp_index
	`RowVector'		costs, c_basic, c_nonbasic, r
	`RowVector'		basic_vars, nonbasic_vars
	`Integer'		n, k, iter
	`StringRowVector' tmp_names

	`Vector'		pivot_col
	`RowVector'		scaled_pivot_row // pivot_row
	`Vector'		pivot_col_pos_list, pivot_row_pos_list
	`Integer'		pivot_col_pos, pivot_row_pos, last_pivot_row_pos
	`Integer'		entering_var, leaving_var, switch_pos
	`Real'			max_val, pivot, tmp_c
	`Boolean'		is_optimal, is_unbounded
	`RowVector'		all_zero

	// Warnings and checks
	assert(keep_mask==.)
	if (any( (abs(X) :< 1e-12) :& (abs(X) :> 0) )) {
		printf("{err}simplex warning: input has very low non-zero values; might create numerical problems\n")
	}


	// Drop columns of X if they are zero
	all_zero = colsum(abs(X)) :== 0
	if (any(all_zero)) {
		if (verbose > 3) printf("\n{txt}[Simplex Presolve] Dropping empty columns: {res}%s\n", invtokens(strofreal(selectindex(all_zero))) )
		X = X[., selectindex(!all_zero)]
		// Trivial case where X is now empty
		if (!cols(X)) {
			if (verbose > 0) printf("{txt} $$ - Simplex converged trivially: no separation\n")
			keep_mask = J(rows(X), 1, 1)
			return(0)
		}
	}
	all_zero = .

	k = cols(X)
	n = rows(X)

	// Remove the K free variables from the system (as well as K obs.)
	presolve(X, basic_vars=., nonbasic_vars=., keep_mask=., k, n, verbose)
	assert(k <= n) // we can't have this, after removing collinear Xs

	// If, after dropping collinear Xs, n=k, we have an independent system, so all obs. should be dropped!
	if (n == k) {
		if (verbose > 0) printf("{txt} $$ - Simplex converged trivially: all obs. separated\n")
		keep_mask = J(n, 1, 0)
		return(0)
	}

	// Initial costs
	c_basic = J(1, n - k, 1)
	c_nonbasic = J(1, k, 1)

	// Coefs of basic vars
	// coefs = J(n - k, 1, 0)
	
	assert_msg(n >= k)
	assert_msg(sum(keep_mask) == n - k)

	last_pivot_row_pos = .

	for (iter=1; iter<=maxiter; iter++) {
		if (verbose > 1) printf("{txt}[Simplex] Iteration {res}%g{txt}\n", iter)

		// Compute relative costs of each non-basic variable (r = c - z)
		r = c_nonbasic - c_basic * X

		// Truncate tiny values to zero; else the check "max_val < 0" might
		// fail by thinking "-1e-16" is negative instead of zero
		_edittozerotol(r, epsilon(100))
		
		// tmp_index = selectindex(c_nonbasic :== 0)
		// if (cols(tmp_index)) r[tmp_index] = J(1, cols(tmp_index), .)

		// Tableau
		if (verbose > 3 & n < 100) view_tableau(X, c_basic, c_nonbasic, n, k, basic_vars, nonbasic_vars, r)

		// With only one var there might be no possible pivots (if the basic var was already flagged) +-
		if (!nonmissing(r) & 0) {
			if (verbose > 3) printf("Simplex has only one variable; so there are no possible pivots\n")
			is_optimal = 1
		}
		else {
		
			// Compute entering variable
			// See: https://pdfs.semanticscholar.org/9f11/f1fa16c966be86da9356c0b52d367599d131.pdf
			maxindex(r, 1, pivot_col_pos_list=., .)
			//if (verbose > 3) printf("\t{txt}Multiple entering candidates: {res}%s{txt}\n", invtokens("e" :+ strofreal(nonbasic_vars[pivot_col_pos_list])'))
			_jumble(pivot_col_pos_list) // required to prevent cycling (do we need this?)
			assert_msg(rows(pivot_col_pos_list), "pivot_col_pos_list is empty")
			pivot_col_pos = pivot_col_pos_list[1]
			entering_var = nonbasic_vars[pivot_col_pos]
			max_val = r[pivot_col_pos]
			
			if (verbose > 3) {
				printf("\t{txt}Entering variable: {res}e%g{txt} has the maximum r: {res}%-5.3f\n", entering_var, max_val)
			}
			
			is_optimal = (max_val <= 0)
		}

		if (is_optimal) {
			costs = J(1, n, .)
			tmp_index = selectindex(keep_mask)
			costs[tmp_index] = c_basic
			costs[nonbasic_vars] = c_nonbasic
			_transpose(costs)

			if (verbose > 3) {
				printf("\t{txt}{bf:Simplex convergence achieved in %g iterations (r<=0):} {res}%g{txt} obs. separated\n\n", iter, n - sum(costs))
			}
			else if (verbose > 1) {
				printf("\t{txt}{bf:Simplex convergence achieved in %g iterations:} {res}%g{txt} obs. separated\n\n", iter, n - sum(costs))
			}
			else if (verbose > 0) {
				printf("{txt} $$ simplex converged in %g iterations; identified %g separated observations)\n", iter, n - sum(costs))
				//printf("{txt}(simplex converged in %g iterations)\n", iter)
			}
			//is_optimal, ., pivot_col_pos, nonbasic_vars[pivot_col_pos]
			swap(keep_mask, costs)
			return(0)
		}

		// Pivot column.
		// Here we should divide RHS column over pivot column, but RHS col is always zero
		pivot_col = X[., pivot_col_pos]
		is_unbounded = all(pivot_col :<= 0) | rows(pivot_col)==0 // all() should evaluate to True if the vector is null!

		if (is_unbounded) {
			// Set cost of entering variable to zero, as well as of
			// all basic variables with negative values in the pivot column

			// If unbounded, set costs of the entering and of all non-zero basic vars to zero
			// And continue from next iter
			tmp_index = selectindex(X[., pivot_col_pos]' :< 0)

			if (verbose > 3) {
				printf("\t{txt}{bf:Unbounded:} all cols of entering var are <=0; zeroing coefs of entering variable\n")
				if (cols(tmp_index)) {
					tmp_names = invtokens("e" :+ strofreal(basic_vars[tmp_index]))
					printf("\t\t   also zeroing %g basic vars with negative values in the pivot column: {res}%s\n", cols(tmp_index), tmp_names)
				}
			}
			else if (verbose > 1) {
				printf("\t{txt}{bf:Unbounded:} zeroing coefs of entering var and of %g basic vars\n", cols(tmp_index))
			}
			if (verbose > 3) printf("\n")
			c_basic[tmp_index] = J(1, cols(tmp_index), 0)
			c_nonbasic[pivot_col_pos] = 0
			continue
		}

		// Compute leaving variable: row with highest non-negative value
		maxindex(pivot_col, 1, pivot_row_pos_list=., .)
		_jumble(pivot_row_pos_list) // hopefully alleviate cycling
		pivot_row_pos = pivot_row_pos_list[1]
		if ((pivot_row_pos==last_pivot_row_pos) & (rows(pivot_row_pos_list)>1)) {
			pivot_row_pos = pivot_row_pos_list[2]
		}
		leaving_var = basic_vars[pivot_row_pos]

		// Compute pivot
		pivot = X[pivot_row_pos, pivot_col_pos]
		assert(0 < pivot & pivot < .)

		if (verbose > 3) printf("\t{txt}Leaving variable: {res}e%g{txt} has the minimum non-negative value: {res}%-5.3f\n", leaving_var, pivot)
		if (verbose > 1) printf("\t{txt}{bf:Pivoting:} {res}e%g{txt} is entering and {res}e%g{txt} is leaving the basis\n", entering_var, leaving_var)

		// Apply pivot
		scaled_pivot_row = X[pivot_row_pos, .] / pivot
		X = X - pivot_col * scaled_pivot_row
		X[pivot_row_pos, .] = scaled_pivot_row
		assert(X[., pivot_col_pos] == e(pivot_row_pos, n-k)')

		// Replace entering variable with leaving variable in X
		X[., pivot_col_pos] = - pivot_col / pivot
		X[pivot_row_pos, pivot_col_pos] = 1 / pivot

		// Update mask and list of basic & non-basic variables
		keep_mask[entering_var] = 1
		keep_mask[leaving_var] = 0
		
		switch_pos = selectindex(nonbasic_vars :== entering_var)
		nonbasic_vars[switch_pos] = leaving_var
		
		switch_pos = selectindex(basic_vars :== leaving_var)
		basic_vars[switch_pos] = entering_var
		
		assert(selectindex(keep_mask) == sort(basic_vars', 1))
		assert(selectindex(!keep_mask) == sort(nonbasic_vars', 1))
		
		tmp_c = c_nonbasic[pivot_col_pos]
		c_nonbasic[pivot_col_pos] = c_basic[pivot_row_pos]
		c_basic[pivot_row_pos] = tmp_c

		_edittozerotol(X, epsilon(10)) // Not sure if needed
		last_pivot_row_pos = pivot_row_pos

		if (verbose > 3) printf("{txt}\n")
	}

	return(430) // 430 = convergence not achieved
}


// PRESOLVE: remove free variables (betas); this implies two things:
// 1) one row will be dropped (b/c redundant) for each X removed
// 2) The identity matrix gets modified in three columns
// See page 13 (example 4) of Luenberg's book
`Void' presolve(
	`Matrix'		X,
	`RowVector'		basic_vars,
	`RowVector'		nonbasic_vars,
	`Variable'		keep_mask,
	`Integer' 		k,
	`Integer' 		n,
	`Integer'		verbose)
{
	`Integer'		 i, j, q
	`Real'			pivot
	`Vector'		pivot_col
	`RowVector'		pivot_row
	`RowVector'		is_dropped
	`StringVector' 	rstripe
	`StringRowVector' cstripe
	`Matrix'		A

	A = J(n, k, 0)
	nonbasic_vars = J(1, k, .)
	keep_mask = J(n, 1, 1)
	is_dropped = J(1, k, 0)

	if (verbose > 3 & n < 100) {
		cstripe = "X" :+ strofreal(1..k), "|", "e" :+ strofreal(1..n)
		rstripe = strofreal(1::n)
		printf("\n{txt}[Simplex Presolve] Input:\n")
		mm_matlist((X, J(n, 1, .), I(n)), "%g", 3, rstripe, cstripe, "Obs \ Vars")
	}

	if (verbose > 3) printf("{txt}Removing the %g free variable%s from the linear problem:\n", k, k > 1? "s" : "")
	for (j=1; j<=k; j++) {
		i = firstnm(X, j) // First non-missing row in column j of X

		// If two vars are the same, then the 2nd will be zero after the first transformation
		if (i == .) {
			if (verbose > 3) printf("{txt} - Col %g is empty; excluding\n", j)
			X[., j] = J(n, 1, 0)
			is_dropped[j] = 1
			nonbasic_vars[j] = .
			continue
		}
		
		assert(i < .)

		if (verbose > 3) printf("{txt} - Deleting col %g with basic variable %g (obs. %g will be excluded) \n", j, i, i)
		nonbasic_vars[j] = i // Row i will also be dropped!
		keep_mask[i] = 0
		
		pivot = -1 / X[i,j]
		pivot_row = pivot * X[i, .]
		pivot_col = X[., j]
	
		A[i, j] = 1
		A = A + pivot_col * pivot * A[i, .]
		X = X + pivot_col * pivot_row
		_edittozerotol(A, epsilon(100))
		_edittozerotol(X, epsilon(100))
		//X, J(n, 1, .), A
	}

	assert(!any(X))
	assert(!any(select(A, !keep_mask)))

	// without this check we might get a 0x0 matrix, and thus an error later on
	X = any(keep_mask) ? select(A, keep_mask) : J(0, 1, .) 
	A = .

	// Trim dataset for dropped vars
	if (any(is_dropped)) {
		q = sum(is_dropped)
		assert(q = missing(nonbasic_vars))
		nonbasic_vars = nonbasic_vars[selectindex(!is_dropped)]
		X = X[., selectindex(!is_dropped)]
		k = k - q
	}

	assert(rows(X) == n - k)
	assert(cols(X))
	assert_msg(cols(nonbasic_vars) == k)

	// Create list of basis vars (starts ordered, will end up jumbled)
	basic_vars = (1..n)
	basic_vars[nonbasic_vars] = J(1, cols(nonbasic_vars), 0)
	basic_vars = any(basic_vars) ? select(basic_vars, basic_vars) : J(1, 0, .)
	assert_msg(cols(basic_vars) == n - k)
	assert_msg(rows(basic_vars) == 1)

	if (verbose > 3) printf("\n\n")
}


`Integer' firstnm(`Matrix' x, `Integer' col)
{
	`Integer' i, n
	n = rows(x)
	for (i=1; i<=n; i++) {
		if (x[i, col] != 0) return(i)
	}
	return(.)
}


// Display the tableau (slow and requires -moremata-)
`Void' view_tableau(
	`Matrix'		X,
	`RowVector'		c_basic,
	`RowVector'		c_nonbasic,
	`Integer'		n,
	`Integer'		k,
	`RowVector'		basic_vars,
	`RowVector'		nonbasic_vars,
	`RowVector'		r)
{
	`RowVector'		costs, z_row
	`Matrix'		tableau, inner_tableau
	`StringVector'	rstripe
	`StringRowVector' cstripe, nonbasic_names
	`Vector'		rhs
	
	rstripe = "Obj fn coef" \ "e" :+ strofreal(basic_vars') \ "Improvement (r)"

	costs = c_basic, c_nonbasic
	rhs = J(n - k, 1, 0)

	//z_row = J(1, n, .)
	//z_row[nonbasic_vars] = r // J(1, k, 1)
	z_row = J(1, n - k, .) , r
	inner_tableau = I(n - k), X // view_eye(X, nonbasic_vars, keep_mask)
	tableau = (costs, .) \ (inner_tableau, rhs) \ (z_row, .x)
	
	cstripe = ("e" :+ strofreal(basic_vars)) , ("*e" :+ strofreal(nonbasic_vars)) , "= RHS"

	mm_matlist(tableau, "%8.3g", 3,  rstripe, cstripe, "Basic \ All")
	nonbasic_names = ("e" :+ strofreal(sort(nonbasic_vars, 1)))
	printf("\t{txt}Nonbasic vars: {res}%s{txt}\n", invtokens(nonbasic_names) )
}


`Void' debug_simplex(`Matrix' X, `Matrix' answer)
{
	`Variable' keep_mask
	//printf("\n{txt}# Simplex input:\n")
	//X
	//printf("{txt}{hline 60}\n")

	(void) simplex_flag_separated_obs(X, 20, keep_mask=., 4) // matrix, maxiter, keep_mask, verbose
	
	printf("{txt}{hline 60}\n")
	printf("{txt}# Simplex output (observations kept):\n")
	keep_mask

	if (answer != .) {
		_transpose(answer) // we recieve a row vector
		assert_msg(cols(answer)==1)
		assert_msg(rows(answer)==rows(keep_mask), "rows(answer) must be equal to rows(input)")
		if (answer != keep_mask) {
			printf("{err}Simplex gave unexpected output; expected vs actual:\n")
			answer, J(rows(answer), 1, .), keep_mask
			exit(322)
		}
		assert_msg(answer == keep_mask, "Simplex gave unexpected output", 322)
	}
	
}


end
