* ===========================================================================
* Test -predict- after ppmlhdfe
* ===========================================================================


// --------------------------------------------------------------------------
// Setup
// --------------------------------------------------------------------------
	noi cscript "ppmlhdfe postestimation: predict bugfix" adofile ppmlhdfe
	set linesize 150
	*ppmlhdfe, reload
	*pr drop _all

	cls
	clear all
	set obs 20
	set seed 12345
	gen y=(_n > 3) * _n
	gen x1=int(rnormal(0,2))
	gen x2=x1
	replace x2=2.5 in 1
	replace x2=5 in 2
	gen x3=int(rnormal(0,2))


// --------------------------------------------------------------------------
// (prevent bug regression; fixed in 2.3.3) - prediction is missing outside of e(sample)
// --------------------------------------------------------------------------
	ppmlhdfe y x1 x2 x3, d

	ppmlhdfe y x1 x2 x3, d
	predict mu1, mu
	gen sample1 = e(sample)

	ppmlhdfe y x2 x1 x3, d
	predict mu2, mu
	gen sample2 = e(sample)

	tab sample1 sample2, m
	
	assert mi(mu1) & mi(mu2) if sample2==0
	assert abs(mu1-mu2) <= 1e-8 if sample2==1

exit
