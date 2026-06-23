clear all
set more off
import delimited "D:\OneDrive - SAIF\PhD3\StataFlow\stata\cases\audit_v1_3_m04\MR01_missing_weakiv_diagnostics.csv", varnames(1) clear
which ivreg2
ivreg2 y (x = z), robust
display "E_N=" e(N)
display "E_DF_M=" e(df_m)
if e(df_r) < . {
    display "E_DF_R=" e(df_r)
}
display "E_R2=" e(r2)
display "E_R2_A=" e(r2_a)
display "E_RMSE=" e(rmse)
if e(F) < . {
    display "E_F=" e(F)
}
if e(widstat) < . {
    display "E_WIDSTAT=" e(widstat)
}
if e(j) < . {
    display "E_J=" e(j)
    display "E_J_P=" e(jp)
    display "E_J_DF=" e(jdf)
}
local coefs : colnames e(b)
local k : word count `coefs'
forvalues i = 1/`k' {
    local name : word `i' of `coefs'
    display "COEF `name' " _b[`name'] " " _se[`name']
}
