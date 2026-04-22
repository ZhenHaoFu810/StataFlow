* p0_min_ols_auto - Minimal OLS dual-run test
* This .do file runs regress and exports structured results to JSON

clear all
set more off

// Use temp directory to avoid OneDrive sync issues
local tempdir = c("tmpdir")
local workdir "`tempdir'\stataflow_p0"
cap mkdir "`workdir'"

// Create minimal dataset
set obs 100
set seed 12345

gen x1 = rnormal(0, 1)
gen x2 = rnormal(0, 1)
gen y = 1 + 2 * x1 + 3 * x2 + rnormal(0, 1)

// Run regression
regress y x1 x2

// Extract results from e() macros
matrix b = e(b)
matrix V = e(V)
scalar nobs = e(N)
scalar df_model = e(df_m)
scalar df_resid = e(df_r)
scalar rss = e(rss)
scalar r2 = e(r2)
scalar r2_adj = e(r2_a)
scalar rmse = e(rmse)
scalar f_stat = e(F)
scalar f_pvalue = e(F_p)

// Get coefficient names and values
local n_cols = colsof(b)

// Build JSON manually
tempname fh
local jsonfile "`workdir'\p0_min_ols_auto_stata.json"
file open `fh' using "`jsonfile'", write replace

file write `fh' "{" _n
file write `fh' "  \"model\": {" _n
file write `fh' "    \"command\": \"regress\"," _n
file write `fh' "    \"estimator_family\": \"ols\"," _n
file write `fh' "    \"vcetype\": \"ols\"," _n
file write `fh' "    \"has_constant\": true" _n
file write `fh' "  }," _n

file write `fh' "  \"sample\": {" _n
file write `fh' "    \"nobs\": " %10.0f nobs "," _n
file write `fh' "    \"df_model\": " %10.0f df_model "," _n  
file write `fh' "    \"df_resid\": " %10.0f df_resid _n
file write `fh' "  }," _n

file write `fh' "  \"fit\": {" _n
file write `fh' "    \"df_model\": " %18.10f df_model "," _n
file write `fh' "    \"df_resid\": " %18.10f df_resid "," _n
file write `fh' "    \"rss\": " %18.10f rss "," _n
file write `fh' "    \"r2\": " %18.10f r2 "," _n
file write `fh' "    \"r2_adj\": " %18.10f r2_adj "," _n
file write `fh' "    \"rmse\": " %18.10f rmse "," _n
file write `fh' "    \"f_stat\": " %18.10f f_stat "," _n
file write `fh' "    \"f_pvalue\": " %18.10f f_pvalue _n
file write `fh' "  }," _n

// Coefficients
file write `fh' "  \"coefficients\": [" _n
forvalues i = 1 / `n_cols' {
    local name : word `i' of `: coln b''
    local beta = b[1, `i']
    local se = sqrt(V[`i', `i'])
    local t = `beta' / `se'
    
    file write `fh' "    {" _n
    file write `fh' "      \"name\": \"`name'\"," _n
    file write `fh' "      \"beta\": " %18.10f `beta' "," _n
    file write `fh' "      \"std_err\": " %18.10f `se' _n
    file write `fh' "    }"
    
    if `i' < `n_cols' {
        file write `fh' ","
    }
    file write `fh' _n
}
file write `fh' "  ]," _n

// Covariance matrix
file write `fh' "  \"variance\": {" _n
file write `fh' "    \"row_names\": ["
forvalues i = 1 / `n_cols' {
    local name : word `i' of `: coln b''
    file write `fh' "\"`name'\""
    if `i' < `n_cols' {
        file write `fh' ", "
    }
}
file write `fh' "]," _n

file write `fh' "    \"values\": [" _n
forvalues i = 1 / `n_cols' {
    file write `fh' "    ["
    forvalues j = 1 / `n_cols' {
        file write `fh' %18.10f V[`i', `j']
        if `j' < `n_cols' {
            file write `fh' ", "
        }
    }
    file write `fh' "]"
    if `i' < `n_cols' {
        file write `fh' ","
    }
    file write `fh' _n
}
file write `fh' "    ]" _n
file write `fh' "  }" _n

file write `fh' "}" _n
file close `fh'

// Also save to project output directory if possible
cap copy "`jsonfile'" "stata/output/p0_min_ols_auto_stata.json", replace

display ""
display "=== Stata Results Exported ==="
display "N = " nobs
display "df_model = " df_model
display "df_resid = " df_resid
display "R2 = " r2
display "F = " f_stat
display "Results saved to: `jsonfile'"
