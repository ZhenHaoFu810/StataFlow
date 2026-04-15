* ===========================================================================
* Validate separation algorithms against a set of datasets
* ===========================================================================
	loc stop_on_error 0
	loc all_ok 1

	loc prefix = cond(`stop_on_error', "", "cap noi")
	timer clear
	clear all
	pr drop _all

	* Warm-up
	sysuse auto
	reghdfe price weight, noa
	ppmlhdfe price weight, noa

	cls

	loc csv_path "../separation_datasets"
	loc files : dir "`csv_path'" files "*.csv", respectcase

	loc i 0
	foreach file of local files {
		loc ++i
		loc fn "`csv_path'/`file'"
		di as text "`fn'"
		insheet using "`fn'", clear comma names double

		cou if separated
		loc N`i' = r(N)

		loc xs
		loc ids
		cap unab  xs :  x*
		cap unab ids : id*
		loc absorb_opt = cond("`ids'"=="", "noabsorb", "absorb(`ids')")

		loc tolerances = cond("`file'" == "07.csv", "relu_zero_tol(1e-10) relu_maxiter(1000)", "")
		loc cmd `"ppmlhdfe y `xs', a(`ids') tagsep(sep_relu) r2 zvar(z) keepsing v(-1) `tolerances'"'
		di as input `"`cmd'"'

		timer on 1
		timer on 2
		`prefix' `cmd'
		loc rc`i' = c(rc)
		timer off 2
		timer off 1

		qui timer list 2
		return list
		loc T`i' = r(t2)
		timer clear 2

		if (c(rc)) continue
		return list
		loc r2 = e(r2)

		tab separated sep_relu, m
		di as text "Asserting obs."
		* We can NEVER detect false positives
		*assert separated >= sep_relu
		* We could fail to detect some cases in extreme datasets
		*`prefix' _assert separated == sep_relu | ("`file'" == "07.csv"), rc(10001) // BUGBUG !!!
		`prefix' _assert separated == sep_relu, rc(10001) // BUGBUG !!!

		loc rc`i' = c(rc)
		if (c(rc)) continue
		
		cou if separated==1
		if (r(N)) {
			di as text "Asserting R2 `=abs(`r2' - 1)'"
			`prefix' _assert abs(`r2' - 1) < 1e-3, rc(10002)
		}
		
		di as text "----"
	}

	// Can't record error messages without "capture"
	if (`stop_on_error') exit

	loc i 0
	foreach file of local files {
		loc ++i
		loc rc = `rc`i''
		if (`rc') loc all_ok 0
		loc msg = cond(`rc', "{err}Error `rc'", "{txt}Ok")
		loc T = strofreal(`T`i'', "%5.2f")
		di as text `"`file' {col 10} `msg' {col 30}`N`i'' {col 40}`T'"'
	}

	* Error legend:
	*  10001: incorrectly separated obs (does not match expected output)
	*  10002: R2 below 1.00
	*  10003: maximum iterations reached

	
timer list // 13.39 with tagsep
assert `all_ok'
exit


