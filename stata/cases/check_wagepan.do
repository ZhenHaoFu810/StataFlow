clear all
set more off
import delimited "D:/OneDrive - SAIF/PhD3/Stata2Python/research/data/public/panel/wooldridge/wagepan.csv", clear
areg lwage educ exper expersq union, absorb(nr)

display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_DF_R=" e(df_r)
display "E_DF_A=" e(df_a)
display "E_R2=" e(r2)
display "E_R2_A=" e(r2_a)
display "E_RMSE=" e(rmse)
display "E_F=" e(F)

matrix list e(b)

exit
