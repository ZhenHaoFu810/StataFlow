* ===========================================================================
* Endometrial data from Agresti (2015) - Section 5.7.1 - Page 186
* ===========================================================================
* Note:
* > The endometrial data set was first analyzed in Heinze and
* > Schemper (2002), and was originally provided by Dr
* > E. Asseryanis from the Medical University of Vienna.
*
* See also:
* 	https://rdrr.io/cran/brglm2/man/endometrial.html
*
* Variables:
* NV: neovasculization with coding 0 for absent and 1 for present
* PI: pulsality index of arteria uterina
* EH: endometrium height
* HG histology grade with coding 0 for low grade and 1 for high grade
*
* R Code:
* endometrialML <- glm(HG ~ NV + PI + EH, data = endometrial, family = binomial("probit"))



     include common.do


// --------------------------------------------------------------------------
// Download data
// --------------------------------------------------------------------------
*     loc url "https://www.dropbox.com/s/6ttu8pt7i0apesc/endometrial.csv?dl=1"
*     loc fn "$input/endometrial.dta"
*     cap conf file "`fn'"
*     if (c(rc)) {
*          *copy "`url'" "`fn'"
*          import delimited "`url'", clear
*          drop v1
*          compress
*          rename HG y
*          rename NV x1
*          rename PI x2
*          rename EH x3
*          save "`fn'", replace
*     }


// --------------------------------------------------------------------------
// Import data
// --------------------------------------------------------------------------
     loc source_fn "$input/endometrial.dat"
     loc fn "$data/endometrial.dta"
     cap conf file "`fn'"
     if (c(rc)) {
          import delimited "`source_fn'", delimiter(space, collapse) varnames(1) case(upper) asdouble colrange(2:5) clear
          compress
          rename HG y
          rename NV x1
          rename PI x2
          rename EH x3
          save "`fn'", replace
     }


// --------------------------------------------------------------------------
// Load data and create variables
// --------------------------------------------------------------------------
     use "`fn'", clear

     * note that ppmlhdfe does not flag any separated observations. 
     * This is not a bug because this is a *binary choice* model, which has different conditions for separation.
     * ppmlhdfe y x1 x2 x3, sep(ir)


     * the regular logit command catches that nv = 1 only when hg = 1. Note this is an easy case.
     tab y x1
     logit y x1 x2 x3, robust

    * Reshape data so we can apply trick
    * This follows the procedure in the appendix (p. 42):
    *  - create an alternate version of each observation
    *  - if the original y is 0, its alternate version is 1, and vice versa
    *  - all x's for alternate observations equal to 0
    *  - include fixed effects for ID

    reshape_logit y x*

    * Idem
    ppmlhdfe y x* c, absorb(i) vce(cluster i)
    di e(num_separated)
    di e(num_singletons)

    * Task is best suited for simplex because of no FEs. ReLu-only also works but with more iterations
    ppmlhdfe y x* c, absorb(i) vce(cluster i) sep(relu) relu_maxiter(200)
    
    * Certificate of separation
    ppmlhdfe y x1 x2 x3 c, a(i) tagsep(sep) zvar(z) r2 relu_maxiter(200)

    * Code below is just to present a prettier output:
    matrix b = e(b)
    mata: vars = st_matrixcolstripe("b")
    mata: directions = round(st_matrix("b"), 0.001)'
    mata: idx = selectindex(directions)
    mata: (vars, strofreal(directions))[idx, .]


exit

	* Equivalent...
	logit y x1 x2 x3, robust
	glm y x1 x2 x3, robust family(binomial) link(logit) tol(1e-12) ml
	glm y x1 x2 x3, robust family(binomial) link(logit) irls
