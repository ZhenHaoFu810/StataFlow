noi cscript "ppmlhdfe: save fixed effects (sanity checks)" adofile ppmlhdfe
set linesize 150

/* Discussion
This test fails if we set min_ok(1) instead of 2.
On iteration #8, the ratio deviance/old_deviance becomes 1.000 (exactly 1)

This is NOT due to
- Transition from approximate partial-out to exact partial-out
- A low start inner tol
*/


// --------------------------------------------------------------------------
// Load data
// --------------------------------------------------------------------------
	use "./datasets/mus18data.dta", clear

	* Save FEs
	ppmlhdfe y x, a(ID1=id ID2=year) tol(1e-12) min_ok(2)
	loc b_x = _b[x]
	loc b_cons = _b[_cons]

	* [Test 1] Ensure that b[FE] is 1

	*poisson y x ID1 ID2, tol(1e-12) (poor precision...)
	*glm y x ID1 ID2, fam(poi) irls ltol(1e-12)
	glm y x ID1 ID2, fam(poi) ml

	di %20.1e abs(_b[ID1] - 1)
	di %20.1e abs(_b[ID2] - 1)

	assert abs(_b[x] - `b_x') < 1e-8
	assert abs(_b[_cons] - `b_cons') < 1e-8
	assert abs(_b[ID1] - 1) < 1e-8
	assert abs(_b[ID2] - 1) < 1e-8

	* [Test 2] Ensure that ppmlhdfe gives the same result
	ppmlhdfe y x ID1 ID2, noa

	assert abs(_b[x] - `b_x') < 1e-8
	assert abs(_b[_cons] - `b_cons') < 1e-8
	assert abs(_b[ID1] - 1) < 1e-8
	assert abs(_b[ID2] - 1) < 1e-8

	* [Test 3] Now with offset...
	gen double ID = ID1+ID2
	ppmlhdfe y x, noa offset(ID)
	assert abs(_b[x] - `b_x') < 1e-8
	assert abs(_b[_cons] - `b_cons') < 1e-8

exit
