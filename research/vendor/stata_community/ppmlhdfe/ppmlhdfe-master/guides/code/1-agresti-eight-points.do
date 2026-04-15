* ===========================================================================
* Didactic eight-point dataset from Section 6.5.1 of Agresti (2013)
* ===========================================================================
* Showcases complete separation
* Source: Categorical Data Analysis 3E (Agresti 2012) - Figure 6.5 - Section 6.5.1 - Page 234
* Suggested by R1 :)

     include common.do


// --------------------------------------------------------------------------
// Create data
// --------------------------------------------------------------------------
     set obs 8
     gen x = 10 * _n + 10 * (_n > 4)
     gen y = x > 50

     tw (scatter y x, msize(medlarge)), xlabel(10(10)90) ylabel(0(1)1) scheme(stcolor) ysize(8) xsize(12) title("Eight point dataset (Agresti 2013 Section 6.5.1)")
     graph export "../figures/agresti-eight.png", width(1200) replace


// --------------------------------------------------------------------------
// Replicate results
// --------------------------------------------------------------------------

     * Notice that Logit aborts:
     cap noi logit y x
     // outcome = x > 40 predicts data perfectly

     * Reshape Long->Wide so we can estimate the Logit with Poisson
     reshape_logit y x

     * Notice how all obs are dropped due to separation
     cap noi ppmlhdfe y x c, absorb(i) vce(cluster i) // insufficient obs after dropping the 8

     * We can replicate Geyer's direction of recession to show the asymptotic values of the estimates ("directions of recession")
     ppmlhdfe y x c, absorb(i) vce(cluster i) tagsep(sep) zvar(z) r2
     * We obtain b_x = -0.25 * \infty ; b_c = 1.25 * \infty (equivalent to Kosmidis 2017: scale by *5 to obtain -1; 5)

     * We can still recover LR test of X as pointed by Agresti (2012)
     * Full model is perfectly predicted; so log likelihood is just -sum(y)
     su y
     loc ll1 = -r(sum)
     di `ll1'
     * Reduced model is estimated by dropping X
     noi ppmlhdfe y c, absorb(i) vce(cluster i)
     loc ll0 = e(ll)
     di `ll0'

     loc lr = 2 * (`ll1' - `ll0')
     loc pvalue = chi2tail(1, `lr')
     di "PValue=`pvalue'; LR=`lr'"

exit
