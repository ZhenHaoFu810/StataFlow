* ===========================================================================
* Test suite for PPMLHDFE.ADO
* ===========================================================================
* Note: this must be run within the -test- folder (type -pwd-)

// --------------------------------------------------------------------------
// Prepare for tests
// --------------------------------------------------------------------------

	* Clear environment
	set trace off
	set more off
	discard
	pr drop _all
	log close _all
	cap cls
	mata: mata clear

	* Reinstall
	cap ado uninstall ppmlhdfe
	cd ../src
	do ppmlhdfe.ado // check for compile-time errors and unused vars
	cd ../test

	loc dir `c(pwd)'
	loc dir : subinstr loc dir "test" "src"
	di as text "DIR: `dir'"
	net install ppmlhdfe , from("`dir'")


// --------------------------------------------------------------------------
// Simple scripts (on well-behaved datasets)
// --------------------------------------------------------------------------

	run utility // tries to run "ppmlhdfe, version"
	run simple
	run offset
	run exposure

	run stats

	run fweight
	run pweight
	run no_regressors
	run factor_and_time
	run savefe
	run savefe_advanced


// --------------------------------------------------------------------------
// Regression tests on issues previously encountered
// --------------------------------------------------------------------------

	run problem1
	run problem2
	run problem3
	run problem4
	run problem5
	run problem6


// --------------------------------------------------------------------------
// Additional regression tests against ppml and other packages
// --------------------------------------------------------------------------

	run collinear1
	run collinear2
	run collinear3
	run collinear4
	run collinear5
	*run collinear6 // This fails due to the SEs
	run collinear7


// --------------------------------------------------------------------------
// Other difficult problems (unclassified)
// --------------------------------------------------------------------------

	run large_y
	
	run hard1
	run hard2
	run hard3
	run hard4
	run hard5

	run problem_mus18_1
	run allzero // y is always zero, should fail gracefully
	run slopes1
	run slopes2
	run slopes3
	run slopes4
	run skew


// --------------------------------------------------------------------------
// Test ReLU separation algorithm
// --------------------------------------------------------------------------
	run validate_tagsep
	run relu_extra

// --------------------------------------------------------------------------
// Test linear programming (simplex) code
// --------------------------------------------------------------------------

	run simplex_internal
	

// --------------------------------------------------------------------------
// Test postestimation
// --------------------------------------------------------------------------
	run predict
	run predict_sample_bug // bugfix
	run margins
	


// --------------------------------------------------------------------------
// Success!
// --------------------------------------------------------------------------

	di as text "No errors found!"
	clear
	set linesize 150
	forval i = 1/4 {
		di as text "{dup 120:*}"
	}
	cap storedresults drop benchmark
	clear all
	exit
