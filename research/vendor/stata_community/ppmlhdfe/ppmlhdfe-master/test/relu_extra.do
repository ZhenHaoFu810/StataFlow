noi cscript "ppmlhdfe: extra tests for ReLU separation function" adofile ppmlhdfe
set linesize 150


// --------------------------------------------------------------------------
// Issue reported by Luis Fonseca
// --------------------------------------------------------------------------
	use "datasets/lf_bug.dta"

	ppmlhdfe y, a(id1 id2) sep(relu)
	assert e(sample) + separated == 1
	
	ppmlhdfe y, a(id1 id2) sep(mu) // mu_tol(1e-8)
	assert e(sample) + separated == 1
	

// --------------------------------------------------------------------------
// Ill-defined dataset
// --------------------------------------------------------------------------
// This dataset has no separation but is ill-defined
// (because y is extremely close to zero)
	
* Dataset
	clear
	set obs 4
	gen double y = max(1e6*(_n-2),1e-8)
	gen double x = _n==1
	list

* Tests
	ppmlhdfe y x, sep(relu)
	assert e(N) == c(N)

	ppmlhdfe y x, sep(relu) standardize_data(0)
	assert e(N) == c(N)

	ppmlhdfe y x, sep(simplex)
	assert e(N) == c(N)

	ppmlhdfe y x, sep(mu)
	assert e(N) == c(N)


exit
