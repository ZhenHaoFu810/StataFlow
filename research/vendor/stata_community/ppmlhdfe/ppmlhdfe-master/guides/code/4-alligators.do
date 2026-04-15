* ===========================================================================
* Multinomial-Poisson Equivalence - Alligators - Agresti (2002, Table 7.4)
* ===========================================================================

	use "../input/alligators.dta", clear
	keep foodchoice size lake freq
	tab foodchoice

	* https://cran.r-project.org/web/packages/brglm2/vignettes/multinomial.html
	* Let’s scale the frequencies in alligators by 3 in order to get a sparser data set
	replace freq = round(freq/3)

	* Benchmark
	mlogit foodchoice ib2.size ib4.lake [fw=freq]
	mlogit foodchoice ib2.size ib4.lake [fw=freq], tol(1e-12)
	* e(ll) =  -80.95651491050657

// --------------------------------------------------------------------------
// No weights (we expand them first)
// --------------------------------------------------------------------------
	* Transform the data
	drop if freq==0
	tab freq
	expand freq
	drop freq

	*mdesc foodchoice size lake
	loc y foodchoice
	gen long obs = _n
	tab `y', nol
	su `y', mean
	loc k = r(max)
	expand `k'
	bys obs: gen byte category = _n // Each of the three categories
	bys obs: gen byte y = `y'==category // New dummy outcome variables
	la val category foodchoice

	* Simplex only drops some separated observations; we use ReLu to drop the rest
	ppmlhdfe y ib1.category##(ib2.size ib4.lake), a(obs) nocons relu_maxiter(1000)
	assert e(N)==310
	assert e(num_separated) == 35

	* Certificate of separation
	* Notice how we use i. instead of ib*. to make sure Stata doesn't drop any categories
	ppmlhdfe y i.category##(i.size i.lake), a(obs) nocons sep(relu) tagsep(sep) zvar(z) r2 relu_zero_tol(1e-10) relu_maxiter(1000) relu_strict(1)
	assert e(r2) > 0.9999


// --------------------------------------------------------------------------
// With frequency weights
// --------------------------------------------------------------------------
	use "../input/alligators.dta", clear
	replace freq = round(freq/3)

	loc y foodchoice
	gen long obs = _n
	tab `y', nol
	su `y', mean
	loc k = r(max)
	expand `k'
	bys obs: gen byte category = _n // Each of the three categories
	bys obs: gen byte y = `y'==category // New dummy outcome variables
	la val category foodchoice
	
	* Simplex only drops some separated observations; we use ReLu to drop the rest
	ppmlhdfe y ib1.category##(ib2.size ib4.lake) [fw=freq], a(obs) nocons
	assert e(N)==310
	* assert e(num_separated) == 35 // TODO: return weighted counts in this case

	*ppmlhdfe y ib1.category##(ib2.size ib4.lake) [fw=freq], a(obs) nocons sep(relu) tagsep(sep) zvar(z) r2 relu_zero_tol(1e-10) relu_maxiter(1000) relu_strict(1)
	ppmlhdfe y i.category##(i.size i.lake) [fw=freq], a(obs) nocons sep(relu) tagsep(sep) zvar(z) r2 relu_zero_tol(1e-10) relu_maxiter(1000) relu_strict(1)
	assert e(r2) > 0.9999

exit
