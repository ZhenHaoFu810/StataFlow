* Wave 12 Performance Benchmark — Stata 17 reghdfe
* NOTE: This file must be run from the `stata/cases/` directory.
* Output: timing, coefficients, standard errors

clear all
set more off
set matsize 11000

* Create output directory if needed
cap mkdir "../../tests/benchmarks/results"

* ---------------------------------------------------------------------------
* Dataset A: single high-dimensional FE (1M obs, 10K levels)
* ---------------------------------------------------------------------------
display "=== Dataset A: single FE ==="
use "../../tests/benchmarks/data/benchmark_a_single_fe.dta", clear

* Explicitly drop missings to align with Python sample screening
egen miss_a = rowmiss(y x1 x2 firm_id)
drop if miss_a > 0
drop miss_a

timer clear
timer on 1
reghdfe y x1 x2, absorb(firm_id) vce(cluster firm_id)
timer off 1

timer list 1
matrix b_a = e(b)
matrix V_a = e(V)
local r2_a = e(r2)
local N_a = e(N)
local rank_a = e(rank)

log using "../../tests/benchmarks/results/stata_benchmark_a.log", text replace
matrix list b_a
matrix list V_a
display "R2: `r2_a'"
display "N: `N_a'"
display "Rank: `rank_a'"
log close

* ---------------------------------------------------------------------------
* Dataset B: two-way FE (1M obs, 5K + 200 levels)
* ---------------------------------------------------------------------------
display "=== Dataset B: two-way FE ==="
use "../../tests/benchmarks/data/benchmark_b_two_way_fe.dta", clear

* Explicitly drop missings to align with Python sample screening
egen miss_b = rowmiss(y x1 x2 firm_id year_id)
drop if miss_b > 0
drop miss_b

timer clear
timer on 1
reghdfe y x1 x2, absorb(firm_id year_id) vce(cluster firm_id)
timer off 1

timer list 1
matrix b_b = e(b)
matrix V_b = e(V)
local r2_b = e(r2)
local N_b = e(N)
local rank_b = e(rank)

log using "../../tests/benchmarks/results/stata_benchmark_b.log", text replace
matrix list b_b
matrix list V_b
display "R2: `r2_b'"
display "N: `N_b'"
display "Rank: `rank_b'"
log close

* ---------------------------------------------------------------------------
* Dataset C: unbalanced panel + cluster (2M obs, 20K + 5K levels)
* ---------------------------------------------------------------------------
display "=== Dataset C: unbalanced + cluster ==="
use "../../tests/benchmarks/data/benchmark_c_unbalanced_cluster.dta", clear

* Explicitly drop missings to align with Python sample screening
egen miss_c = rowmiss(y x1 x2 worker_id firm_id cluster_id)
drop if miss_c > 0
drop miss_c

timer clear
timer on 1
reghdfe y x1 x2, absorb(worker_id firm_id) vce(cluster cluster_id)
timer off 1

timer list 1
matrix b_c = e(b)
matrix V_c = e(V)
local r2_c = e(r2)
local N_c = e(N)
local rank_c = e(rank)

log using "../../tests/benchmarks/results/stata_benchmark_c.log", text replace
matrix list b_c
matrix list V_c
display "R2: `r2_c'"
display "N: `N_c'"
display "Rank: `rank_c'"
log close

display "=== All benchmarks complete ==="
