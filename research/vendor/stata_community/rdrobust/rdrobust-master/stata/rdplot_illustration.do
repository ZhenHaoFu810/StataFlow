********************************************************************************
** RDROBUST Stata Package
** Do-file for RDPLOT Illustration
** Authors: Sebastian Calonico, Matias D. Cattaneo, Max H. Farrell and Rocio Titiunik 
********************************************************************************
** net install rdrobust, from(https://raw.githubusercontent.com/rdpackages/rdrobust/master/stata) replace
********************************************************************************
clear all

********************************************************************************
** Load data and generate RDPLOT results without output plot
********************************************************************************
use "rdrobust_senate.dta", clear
global y vote
global x margin
global c 0
su $x
global x_min = r(min)
global x_max = r(max)

rdplot $y $x, genvars hide ci(95)

********************************************************************************
** Default RDPLOT
********************************************************************************
twoway (scatter rdplot_mean_y rdplot_mean_bin, sort msize(small)  mcolor(gs10)) ///
(function `e(eq_l)', range($x_min $c) lcolor(black) sort lwidth(medthin) lpattern(solid)) ///
(function `e(eq_r)', range($c $x_max) lcolor(black) sort lwidth(medthin) lpattern(solid)), ///
xline($c, lcolor(black) lwidth(medthin)) xscale(r($x_min $x_max))  /// 
legend(pos(6) cols(2) order(1 "Sample average within bin" 2 "Polynomial fit of order 4" )) title("Regression function fit", color(gs0)) 

********************************************************************************
** RDPLOT with confidence intervals
********************************************************************************
twoway (rcap rdplot_ci_l rdplot_ci_r rdplot_mean_bin, color(gs11)) ///
(scatter rdplot_mean_y rdplot_mean_bin, sort msize(small)  mcolor(gs10)) ///
(function `e(eq_l)', range($x_min $c) lcolor(black) sort lwidth(medthin) lpattern(solid)) ///
(function `e(eq_r)', range($c $x_max) lcolor(black) sort lwidth(medthin) lpattern(solid)), ///
xline($c, lcolor(black) lwidth(medthin)) xscale(r($x_min $x_max))  /// 
legend(pos(6) cols(2) order(1 "Sample average within bin" 2 "Polynomial fit of order 4" )) title("Regression function fit", color(gs0)) 

********************************************************************************
** RDPLOT with shaded confidence intervals
********************************************************************************
twoway (rarea rdplot_ci_l rdplot_ci_r rdplot_mean_bin if rdplot_id<0, sort color(gs11)) ///
(rarea rdplot_ci_l rdplot_ci_r rdplot_mean_bin if rdplot_id>0, sort color(gs11)) ///
(scatter rdplot_mean_y rdplot_mean_bin, sort msize(small)  mcolor(gs10)) ///
(function `e(eq_l)', range($x_min $c) lcolor(black) sort lwidth(medthin) lpattern(solid)) ///
(function `e(eq_r)', range($c $x_max) lcolor(black) sort lwidth(medthin) lpattern(solid)), ///
xline($c, lcolor(black) lwidth(medthin)) xscale(r($x_min $x_max))  /// 
legend(pos(6) cols(2) order(1 "Sample average within bin" 2 "Polynomial fit of order 4" )) title("Regression function fit", color(gs0)) 

