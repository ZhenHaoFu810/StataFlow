clear all
set more off
import delimited "D:\OneDrive - SAIF\PhD3\StataFlow\stata\cases\audit_v1_3_m05\S5_poisson_overdispersion_ols.csv", varnames(1) clear
poisson y x1 x2
display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_K=" e(k)
display "E_DF_R=" e(df_r)
display "E_LL=" e(ll)
display "E_PSEUDO_R2=" e(r2_p)
display "E_CHI2=" e(chi2)
display "E_CHI2_P=" e(p)
capture drop __mu __dev_i
predict double __mu if e(sample)
gen double __dev_i = 0 if e(sample)
replace __dev_i = 2*(__mu) if e(sample) & y==0
replace __dev_i = 2*(y*ln(y/__mu) - (y - __mu)) if e(sample) & y>0
summarize __dev_i, meanonly
display "E_DEVIANCE=" r(sum)
if e(N_clust) < . {
    display "E_N_CLUST=" e(N_clust)
}
local coefs : colnames e(b)
local k : word count `coefs'
forvalues i = 1/`k' {
    local name : word `i' of `coefs'
    display "COEF `name' " _b[`name'] " " _se[`name']
}
matrix V = e(V)
forvalues i = 1/`k' {
    forvalues j = 1/`k' {
        display "VCE " (`i'-1) " " (`j'-1) " " V[`i',`j']
    }
}
