clear all
set more off

import delimited "D:\OneDrive - SAIF\PhD3\StataFlow\stata\cases\audit_v1_3_m02\S1_hand_computable_panel.csv", varnames(1) clear

xtset entity time
xtreg y x, fe

* Scalar fields
display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_DF_R=" e(df_r)
display "E_R2=" e(r2)
display "E_R2_A=" e(r2_a)
display "E_RMSE=" e(rmse)
display "E_F=" e(F)
local test_df = e(df_m)
if `test_df' <= 0 local test_df = colsof(e(b)) - 1
display "E_F_P=" Ftail(`test_df', e(df_r), e(F))
display "E_RSS=" e(rss)
display "E_MSS=" e(mss)
if e(N_g) < . {
    display "E_N_G=" e(N_g)
}
if e(N_clust) < . {
    display "E_N_CLUST=" e(N_clust)
}

* Coefficients and full VCE
local coefs : colnames e(b)
local k : word count `coefs'
forvalues i = 1/`k' {
    local name : word `i' of `coefs'
    local b = _b[`name']
    local se = _se[`name']
    display "COEF `name' " %21.15e `b' " " %21.15e `se'
}

* VCE matrix (full)
matrix V = e(V)
forvalues i = 1/`k' {
    forvalues j = 1/`k' {
        display "VCE " (`i'-1) " " (`j'-1) " " %21.15e V[`i',`j']
    }
}
