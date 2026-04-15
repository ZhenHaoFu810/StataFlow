clear all
discard
sysuse auto

tempvar touse newtouse
gen `touse' = foreign

loc absorb turn trunk##c.gear, lorem(ipsum) // todo: allow extra options such as tol() here
loc weight_type 
loc weight_var
loc drop_singletons = 0
loc verbose = 1
loc clustervars turn#trunk


// If we load the data by hand, we need
// ms_fvstrip `vars' if `touse', expand dropomit addbn onebyone

mata:
	HDFE = fixed_effects("`absorb'", "`touse'", "`weight_type'", "`weight_var'", `drop_singletons', `verbose')

	HDFE.G // number of absvars
	HDFE.tolerance = 1e-10 // change tolerance (later we can pass these options through absorb)
	HDFE.N // number of obs.

	// We need to know clustervars to compute the absorbed degrees-of-freedom
	HDFE.options.clustervars = tokens("`clustervars'") // todo: rely on ms_parse_vce.ado
	HDFE.options.base_clustervars = tokens(subinstr("`clustervars'", "#", " ")) // todo: rely on ms_parse_vce.ado
	HDFE.options.num_clusters = length(HDFE.options.clustervars)
	
	HDFE.estimate_dof() // compute degrees-of-freedom
	HDFE.output.df_a // e(df_a)

	// Optionally update touse (might have been reduced if we dropped singletons)
	HDFE.save_touse("`newtouse'")

	y = HDFE.partial_out("price") // first option

	x = st_data(HDFE.sample, "weight length") // load data
	HDFE._partial_out(x) // second option

	beta = invsym(cross(x, x)) * cross(x, y)
	beta

	// Cleanup
	mata drop HDFE
end


* Non-Mata alternative:
reghdfe price weight length if foreign, a(turn trunk##c.gear) vce(cluster turn#trunk)


exit
