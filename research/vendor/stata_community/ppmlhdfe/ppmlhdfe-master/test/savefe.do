noi cscript "ppmlhdfe: save fixed effects" adofile ppmlhdfe
set linesize 150

* Dataset
sysuse auto, clear

* Comparison list
	loc include_list ///
		scalar: N ll /// chi2 p ???
		matrix: trim_b trim_V ///
		macros: wexp wtype


* [TEST]

	* 1. Run benchmark
	poisson price weight gear i.turn i.foreign, robust
	trim_cons 2
	storedresults save benchmark e()

	* 2. Run ppmlhdfe
	ppmlhdfe price weight gear, a(FE1=turn FE2=foreign) vce(robust) tol(1e-10) keepsing v(-1)
	conf var FE1 FE2

	ppmlhdfe price weight gear, a(turn foreign, savefe) vce(robust) tol(1e-10) keepsing v(-1)
	conf var __hdfe1__ __hdfe2__

	assert abs((FE1+FE2) - (__hdfe1__+__hdfe2__)) <= 1e-6

	trim_cons
	storedresults compare benchmark e(), tol(1e-8) include(`include_list')

exit
