noi cscript "ppmlhdfe - slopes" adofile ppmlhdfe
set linesize 150

loc include_list ///
	matrix: /// trim_b trim_V
	macros: wexp wtype ///
	scalar: ll rmse converged deviance rss N 


// --------------------------------------------------------------------------
// Create test dataset
// --------------------------------------------------------------------------
	
	clear
	input byte(index id1 id2 x z) double y
	1 1 1 0 -1  3369071263
	2 1 1 0  2  2535746605
	3 1 1 1 15 15241548895
	4 1 2 0 11        1040
	5 1 2 0 13         166
	6 1 2 0 15    21682500
	7 1 3 0 -1           0
	8 1 3 0  7      764800
	end
	format %16.0fc y


// --------------------------------------------------------------------------
// Explanation
// --------------------------------------------------------------------------
* 1) Within id2==3, the constant and -z- can separate obs #7:
* 	 gen double sep = 7 * (id2==3) - (id2==3) * z
* 2) Then, after dropping #7, note that
*	 a) (id2==3) becomes a singleton group (so we should drop obs #8)
*    b) The R2 in OLS becomes 1, but only b/c some values are very high

	li id2 y x z, sepby(id2)


// --------------------------------------------------------------------------
// Tests
// --------------------------------------------------------------------------

* [TEST 1 - Keep singletons (obs #8)]

	* Benchmark
	ppmlhdfe y x ibn.id1 ibn.id2##c.z, noa tol(1e-10)
	storedresults save benchmark e()

	* Test
	ppmlhdfe y x, absorb(id1 id2##c.z) maxiter(100) tol(1e-10) keepsing
	storedresults compare benchmark e(), tol(1e-8) include(`include_list')


* [TEST 2 - Drop singletons]

	* Benchmark
	ppmlhdfe y x ibn.id1 ibn.id2##c.z if _n<8, noa tol(1e-10)
	storedresults save benchmark e()

	* Test
	ppmlhdfe y x, absorb(id1 id2##c.z) maxiter(100) tol(1e-10)
	storedresults compare benchmark e(), tol(1e-8) include(`include_list')


storedresults drop benchmark
exit
