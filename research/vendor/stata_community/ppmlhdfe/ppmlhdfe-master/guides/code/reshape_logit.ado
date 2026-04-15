program reshape_logit
	* program is very simple; no [if], no missings allowed, no factor or timeseries, etc.
	syntax varlist
	gettoken y xs : varlist
	*mdesc `varlist' // ensure there are no missings
	tab `y'

	* Also hardcoded: variables -dupe-, -i-, and -c-
	gen long i = _n

	qui compress
	tempfile data
	qui save "`data'"
	append using "`data'", gen(dupe)

	qui replace `y' = 1 - `y' if dupe
	foreach x of varlist `xs' {
		qui replace `x' = 0 if dupe & !mi(`x')
	}
	gen byte c = !dupe // don't forget about constant
	sort i dupe
	di as text `"command:{inp} ppmlhdfe `varlist' c, absorb(i) vce(cluster i)"'
end


/*
Expand 2
for i=1 we keep y ==> cat1 is default=1
for i=2 we do 1-y ==> cat2 is default=0 (baseline?)
for i=2 (default=0) we set zero out all Xs

*/
