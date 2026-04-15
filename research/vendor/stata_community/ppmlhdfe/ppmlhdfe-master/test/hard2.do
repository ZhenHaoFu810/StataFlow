noi cscript "ppmlhdfe - extreme case test" adofile ppmlhdfe
set linesize 150

* Comparison list

loc exclude_same ///
	scalar: tss mss F ll_0 r2_a_within r2_a r2_within r2 chi2



loc exclude_similar ///
	scalar: tss mss F ll_0 r2_a_within r2_a r2_within r2 ///
			rank N_hdfe N_hdfe_extended df_a df_a_initial df_a_redundant df_m ic ic2 df chi2 /// (why is df -1?) 
	macros: cmdline indepvars title title2 extended_absvars absvars ///
	matrix: b V dof_table


loc list_glm ///
	/// scalar: /// N ll converged
	matrix: /// trim_b trim_V
	macros: wexp wtype


loc list_poisson ///
	scalar: converged /// N ll
	matrix: /// trim_b trim_V
	macros: wexp wtype


clear
input byte FTA int(ikt_fe jkt_fe ijk_fe)
1 1 3 1
1 2 4 1
1 1 5 2
1 2 6 2
1 3 1 3
1 4 2 3
1 3 7 4
1 4 8 4
1 5 1 5
1 6 2 5
0 5 3 6
1 6 4 6
0 5 5 7
1 6 6 7
1 5 7 8
1 6 8 8
end


// Note the 1.00 R2!
//reghdfe FTA, absorb(ijk_fe jkt_fe ikt_fe, dofadjust(none))

ppmlhdfe FTA, absorb(ijk_fe jkt_fe ikt_fe) tol(1e-12) keepsing // v(1) 
assert e(converged) == 1
storedresults save absorb e()

* Same thing (just to ensure we dont compare missings)
ppmlhdfe FTA, absorb(ijk_fe jkt_fe ikt_fe) tol(1e-12) keepsing // v(1) 
assert e(converged) == 1
storedresults compare absorb e(), tol(1e-8) exclude(`exclude_same')

* Move absorb() to regressors
ppmlhdfe FTA ibn.ijk_fe ibn.jkt_fe ibn.ikt_fe, noa tol(1e-12) keepsing // v(1) 
assert e(converged) == 1
storedresults compare absorb e(), tol(1e-8) exclude(`exclude_similar')

storedresults drop absorb
exit

* PROBLEM: WHAT CAN WE COMPARE THIS AGAINST?
glm FTA ibn.ijk_fe i.jkt_fe i.ikt_fe, vce(robust) fam(poisson) irls ltol(1e-12)
storedresults compare absorb e(), tol(1e-8) include(`list_glm')

poisson FTA ibn.ijk_fe i.jkt_fe i.ikt_fe, vce(robust)
storedresults compare absorb e(), tol(1e-8) include(`list_poisson')

exit








// Fail
cap noi ppmlhdfe FTA, absorb(ijk_fe jkt_fe ikt_fe) maxiter(100) accel_skip(0) edit v(1)
cap noi xi: ppmlhdfe FTA i.ijk_fe i.jkt_fe i.ikt_fe, noabsorb accel_skip(0) edit

// Work? (LL=0)
xi: ppmlhdfe FTA i.ijk_fe i.jkt_fe i.ikt_fe, noabsorb accel_skip(0) sep(none) edit

set obs `=c(N)+10'
foreach var of varlist *_fe {
	replace `var' = 10 + ceil(runiform() * 2) if mi(`var')
}
replace FTA = exp(1+runiform() * 10) if mi(FTA)
ppmlhdfe FTA, absorb(ijk_fe jkt_fe ikt_fe)

exit


// TZ: try this - this works. I think for "difficult" problems you may need a tighter inner tolerance to start
ppmlhdfe FTA, absorb(ijk_fe jkt_fe ikt_fe) edit start_inner_tol(1e-4)


xi: ppmlhdfe FTA i.ijk_fe i.jkt_fe i.ikt_fe, noabsorb verbose(1) accel_skip(0) sep(none) edit


