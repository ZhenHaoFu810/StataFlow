clear all
sysuse auto
reghdfe price weight [aweight = mpg], a(turn) // coef = 4.320956
ivreg2 price weight i.turn [aweight = mpg], partial(i.turn) small // coef = 4.320956
ivreghdfe price weight i.turn [aweight = mpg] // coef = 4.320956

noi cscript "ivreghdfe: ensure weights are used (issue #48)" adofile ivreghdfe

* Dataset
	sysuse auto
	
	local included_e ///
		matrix: b ///

* [TEST]

	* 1. Run benchmark
	reghdfe price weight [aweight = mpg], a(turn) nocons // coef = 4.320956
	storedresults save benchmark e()
	
	* 2. Run ivreghdfe
	ivreghdfe price weight [aweight = mpg], a(turn) // coef = 4.367747
	storedresults compare benchmark e(), tol(1e-12) include(`included_e')

	* Done!

storedresults drop benchmark
exit
