clear all
set more off
import delimited "D:\OneDrive - SAIF\PhD3\StataFlow\research\data\public\panel\wooldridge\wagepan.csv", clear
reghdfe lwage educ exper expersq union, absorb(nr year) vce(cluster nr)
display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_DF_R=" e(df_r)
display "E_DF_A=" e(df_a)
display "E_R2=" e(r2)
display "E_R2_A=" e(r2_a)
display "E_RMSE=" e(rmse)
display "E_F=" e(F)
display "E_N_CLUST=" e(N_clust)
display "B_EDUC=" _b[educ]
display "B_EXPER=" _b[exper]
display "B_EXPERSQ=" _b[expersq]
display "B_UNION=" _b[union]
display "B__CONS=" _b[_cons]
display "SE_EDUC=" _se[educ]
display "SE_EXPER=" _se[exper]
display "SE_EXPERSQ=" _se[expersq]
display "SE_UNION=" _se[union]
display "SE__CONS=" _se[_cons]
