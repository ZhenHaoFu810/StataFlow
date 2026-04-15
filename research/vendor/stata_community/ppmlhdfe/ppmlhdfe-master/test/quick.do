clear all
set trace off
set more off
cap ado uninstall ppmlhdfe
net install ppmlhdfe , from("C:/Git/ppml_hdfe_demo/src")
discard
pr drop _all
cls

// --------------------------------------------------------------------------
// Create dataset
// --------------------------------------------------------------------------
	
set obs 15
gen byte y = clip(_n -10, 0, .)
gen byte z1 = _n
gen byte z2 = z1 + inlist(_n, 3, 4)
gen byte z3 =  (_n==1)
gen byte z4 = -(_n==2)

set seed 123456
gen double x1 = rnormal()
gen double x2 = x1 + 10 * inlist(_n, 2, 5, 6) - 20 * (_n == 7)
gen double x3 = x1 + 10 * (_n == 7) - 5 * (_n == 6)
gen double x4 = x1 + 10 * (_n == 10) - 12 * (_n == 9)

gen double x5 = 10 * (_n == 10) - 12 * (_n == 9)

// --------------------------------------------------------------------------
// Explanation
// --------------------------------------------------------------------------
/* 
gen byte is_sep = 0

* (A) z2-z1 separates observations #3 and #4
gen double delta = z2 - z1
assert delta == 0 if y
assert delta >= 0 if !y
replace is_sep = 1 if (delta > 0 & !y)
list is_sep y delta z1 z2 if !y & delta > 0
drop delta

* (B) z3 separates #1 and z4 separates #2
assert !z3 if y
assert !z4 if y
assert z3>=0 if !y
assert z4<=0 if !y
replace is_sep = 1 if !y & (z3>0 | z4<0)
li is_sep y z3 z4 if !y & (z3 | z4)

* (C) X1, X2 and X3 separate obs #2 and #5
gen double delta = (x2-x1) + 2 * (x3-x1)
assert !delta if y
assert delta>=0 if !y
replace is_sep = 1 if delta>0 & !y
li is_sep y delta
drop delta

* (D) x5 is collinear with {x1, x2}
gen double delta = x1 - x4 + x5
li delta
drop delta

poisson y z1 z2 z3 z4 x1 x2 x3 x4 if !is_sep
glm y z1 z2 z3 z4 x1 x2 x3 x4 if !is_sep, fam(poisson) irls
glm y z1 z2 z3 z4 x1 x2 x3 x4 if !is_sep, fam(poisson) ml
exit
*/

// --------------------------------------------------------------------------
// Benchmark
// --------------------------------------------------------------------------

ppmlhdfe y z1 z2 z3 z4 x1 x2 x3 x4, noa v(0) simplexmaxiter(10)
	

exit

asd
list y delta z1 z2 if delta * (y>0) | (delta!=0)*(y==0) 



asd

*ppmlhdfe y x5, noa v(1) simplextol(1e-10)



exit

clear
input byte(y x1 x2 x3 x4 x5)
0  0  0  0  0 1
0  0  0  0  0 2
0  5 11  2  2 0
0  5  2 11  2 0 
0  5  2  2 11 0
0  0 -1 -1 -1 0
1  5  5  5  5 0
2  4  4  4  4 0
3  3  3  3  3 0
4  2  2  2  2 0
5  1  1  1  1 0
end

gen double z = (x2 + x3 + x4) / 3
reg x1 z if y > 0 // beta = 1
gen double e = x1 - z // predict double e, resid
su e if y == 0, d
list

ppmlhdfe y x1 x2 x3 x4 x5, noa tol(1e-10) 


exit
