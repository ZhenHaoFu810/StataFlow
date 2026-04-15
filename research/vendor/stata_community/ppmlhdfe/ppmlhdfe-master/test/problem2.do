noi cscript "ppmlhdfe: test against prob2 dataset" adofile ppmlhdfe
set linesize 150

/* DATASET: same as Paulo's prob2.dta

Why is this dataset is tricky?
Because we can create a new variable that perfectly separates one case of y==0

. gen double z = (j==2) + (j==3) + (i==1) - x1 - x2
. list y z

Solution: drop x2 (or x1?) and observation #5
*/

clear
input float(y x1 x2 i j)
2 0 0 2 1
1 0 1 2 3
2 0 1 2 2
1 1 0 2 2
0 1 0 1 2
1 2 0 1 3
1 0 0 2 1
2 1 0 2 3
0 1 0 2 2
end

gen double z = (j==2) + (j==3) + (i==1) - x1 - x2
tab z y // z takes two values when y==0, but it's always 0 when y>0
list y z
list y x1 i j if _n!=5

gen index = _n
ppmlhdfe y x1 x2, a(i j) v(1)
gen sample = e(sample)
list index if sample

gen byte I1 = (i==2)
gen byte I2 = (i==2)
gen byte J1 = (j==1)
gen byte J2 = (j==2)
gen byte J3 = (j==3)

* Let's see how each command performs:

ppmlhdfe y x1 x2, a(i j)
poisson y x1 J* if !inlist(_n, 5, 6) , robust nocons // poisson requires babysitting to get the right regressors
ppml y x1 x2 I* J*
glm y x1 x2 I* J* , fam(poi)
glm y x1 x2 I* J* , fam(poi) irls

* Now let's run the test

* Comparison list
	loc list_poisson ///
		scalar: N converged ll /// chi2 p ???
		matrix: trim_b trim_V ///
		macros: wexp wtype

	loc list_xtpoisson ///
		scalar: N converged df_m rank /// ll
		matrix: trim_b trim_V ///
		macros: wexp wtype


* [TEST]

	* 1. Run benchmark
	poisson y x1 J* if !inlist(_n, 5, 6) , robust nocons
	drop I* J*
	trim_cons 1
	storedresults save benchmark e()

	* 2. Run ppmlhdfe
	ppmlhdfe y x1 x2, a(i j)
	trim_cons 1
	storedresults compare benchmark e(), tol(1e-8) include(`list_poisson')
	assert inrange(e(ic), 1, 1000)

exit
