noi cscript "ppmlhdfe: test against prob1 dataset" adofile ppmlhdfe
set linesize 150

/* DATASET: same as Paulo's prob1.dta

Why this dataset is tricky?
  1) Initially we don't drop any singletons
  2) Then we drop x2, together with 4 obs (#5 #8 #14 #15)
  3) That leaves only one obs (#7) where i==5 (a singleton)
     so we will drop it after updating the HDFE object
*/

clear
input float(y x1 x2 i j)
2 0 0 2 1
0 0 0 4 2
0 0 0 1 1
1 1 0 4 3
0 0 1 2 2
0 0 0 2 2
1 0 0 5 4
0 1 2 2 3
1 0 0 1 1
0 0 0 2 2
0 2 0 1 3
0 0 0 1 3
0 1 0 2 2
0 0 1 5 2
0 0 1 2 4
0 0 0 1 2
0 0 0 1 1
2 0 0 1 2
end

//gen double idx = _n
//set obs 20
//replace idx = 0 if idx==.
//sort idx
//drop idx
//set obs 21

cou if x2 > 0
cou if x2 < 0
cou if x2 > 0 & y > 0

cou if i==5 & x2==0

* Comparison list
	loc include_list ///
		scalar: N ll /// chi2 p ???
		matrix: trim_b trim_V ///
		macros: wexp wtype


* [TEST 1 - Keepsingletons]
	loc lhs y
	loc rhs x1 x2
	loc absvars i j

	* 1. Run benchmark
	tab i, gen(D1_)
	tab j, gen(D2_)
	//ppml `lhs' D* `rhs' if !inlist(_n, 5, 8, 14, 15), tol(1e-10)
	glm `lhs' `rhs' D* if !inlist(_n, 5, 8, 14, 15), fam(poisson) ml tol(1e-12) ltol(1e-12) robust // irls
	drop D*
	trim_cons 2
	storedresults save benchmark e()

	* 2. Run ppmlhdfe
	ppmlhdfe `lhs' `rhs', absorb(`absvars') tol(1e-10) keepsing sep(mu) // v(1)
	trim_cons
	storedresults compare benchmark e(), tol(1e-8) include(`include_list')
	assert inrange(e(ic), 1, 1000)
	storedresults drop benchmark


* [TEST 2 - Drop singletons]
	loc lhs y
	loc rhs x1 x2
	loc absvars i j

	* 1. Run benchmark
	tab i, gen(D1_)
	tab j, gen(D2_)
	// ppml `lhs' `rhs' D* if !inlist(_n, 5, 7, 8, 14, 15), tol(1e-10)
	glm `lhs' `rhs' D* if !inlist(_n, 5, 7, 8, 14, 15), fam(poisson) ml tol(1e-12) ltol(1e-12) robust // irls
	drop D*
	trim_cons 2
	storedresults save benchmark e()

	* 2. Run ppmlhdfe
	ppmlhdfe `lhs' `rhs', absorb(`absvars') tol(1e-10) v(1)
	trim_cons
	storedresults compare benchmark e(), tol(1e-8) include(`include_list')
	assert inrange(e(ic), 1, 1000)
	storedresults drop benchmark


exit


ppmlhdfe y x1 if !inlist(_n, 5, 8, 14, 15), absorb(i j) tol(1e-10) v(1)
