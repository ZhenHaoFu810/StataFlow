* Stata dual-run template for revalidation
* Data: <DATASET_NAME>
* Command: <STATA_COMMAND>
* Date: <DATE>

clear all
set more off

* Load data
use "<DATA_PATH>", clear

* Run command and collect results
<STATA_COMMAND>

* Output key results
display "===RESULTS==="
display "N_obs = " e(N)
display "N_clust = " e(N_clust)
display "df_m = " e(df_m)
display "df_r = " e(df_r)
display "r2 = " e(r2)
display "rmse = " e(rmse)
display "F = " e(F)

* Coefficients
matrix b = e(b)
matrix V = e(V)
matrix list b
matrix list V

* Log close
log close
