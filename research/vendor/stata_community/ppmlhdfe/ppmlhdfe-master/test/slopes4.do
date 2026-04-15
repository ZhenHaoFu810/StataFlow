noi cscript "ppmlhdfe - slopes #4" adofile ppmlhdfe
set linesize 150

loc include_list ///
	matrix: /// trim_b trim_V
	macros: wexp wtype ///
	scalar: ll rmse converged deviance rss N 


// --------------------------------------------------------------------------
// Create test dataset
// --------------------------------------------------------------------------
	
	clear
	input long y byte(x z i j)
	      0 0 -1  1  1
	   5211 0 -1  1  4
	  10498 0  2  2  4
	   1310 0  2  2  5
	    189 0  3  3  2
	      0 0  3  3  6
	   1468 0  6  4  5
	     34 0  6  4  7
	  12000 0  7  5  3
	   1036 0  7  5  5
	      0 0  8  6  3
	   1247 0  8  6  7
	    460 0  9  7  1
	     70 0  9  7  7
	     28 0 14  8  2
	      4 0 14  8  3
	     17 0 14  8  6
	      0 0 15  9  1
	      8 0 15  9  6
	 203886 0  3 10  8
	3840369 1  3 10  9
	3961747 1  8 11  9
	 710771 0  8 11 10
	 810565 0 13 12  8
	 249014 0 13 12 10
	 819845 0 16 13  8
	5589636 1 16 13  9
	end
	format %12.0fc y


// --------------------------------------------------------------------------
// Explanation
// --------------------------------------------------------------------------

/*
	gen sep1 = (3 * (i==1) - 2 * (j==4) + (j==4) * z) / 3
	gen sep2 = (i==3) - (14/11) * (j==2) + (1/11) * (j==2) * z
	gen sep3 = (j==1) * z - 9 * (j==1)
	replace sep3 = (sep3 + 10 * sep1) / 6
	gen sep4 = (j==3) * z + 7 * (inlist(j, 2, 6) - (j==3) - inlist(i, 3, 8, 9))
	replace sep4 = sep4 + 7 * sep3

	egen double sep = rowtotal(sep*)
	drop sep?
	
	assert (sep == 0) if y > 0
	assert (sep >= 0) if y == 0

	li i j y x z sep, sepby(i)
	*/

	gen byte sample = (y > 0) // All y==0 obs are separated


// --------------------------------------------------------------------------
// Tests
// --------------------------------------------------------------------------

* [TEST 1 - Keep singletons (obs #8)]
/*
	* Benchmark
	ppmlhdfe y x ibn.i ibn.j##c.z, noa tol(1e-10) maxiter(100) 
	gen byte bench_sample = e(sample)
	assert sample == bench_sample 
	storedresults save benchmark e()

	* Test
	ppmlhdfe y x, absorb(i j##c.z) maxiter(400) tol(1e-10) keepsing mu_tol(1e-6)
	gen byte test_sample = e(sample)
	assert test_sample == bench_sample 
	storedresults compare benchmark e(), tol(1e-8) include(`include_list')

storedresults drop benchmark
exit

*/

