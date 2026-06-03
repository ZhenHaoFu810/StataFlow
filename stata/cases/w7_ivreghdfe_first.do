clear all
set more off

log using "w7_ivreghdfe_first.log", replace

use "w7_ivreghdfe_first_data.dta", clear

ivreghdfe y x1 (x2 = z1 z2), absorb(entity_id) keepsingletons first

display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_DF_R=" e(df_r)
display "E_DF_A=" e(df_a)

log close
