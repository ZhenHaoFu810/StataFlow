*! version 2.3.4 11jan2025
*! Authors: Sergio Correia, Paulo Guimarães, Thomas Zylkin
*! URL: https://github.com/sergiocorreia/ppmlhdfe

program ppmlhdfe, eclass
	if replay() {
		syntax, [*] [SIMPLEX(string) ANSwer(string)]

		if (`"`simplex'"'!="") {
			// Undocumented; internal for debugging
			di as text "Testing simplex..."
			if (`"`answer'"'=="") loc answer "."
			mata: debug_simplex((`simplex'), (`answer'))
		}
		else if inlist("`options'", "version", "reload") {
			`=strproper("`options'")'
		}
		else {
			Replay `0'
		}
	}
	else {
		Cleanup 0
		ms_get_version ftools, min_version("2.45.0")
		ms_get_version reghdfe, min_version("6.0.2")
		cap noi Estimate `0'
		Cleanup `c(rc)'
	}
end


program Cleanup
	args rc
	// BUGBUG Remove most of this and add GLM object
	// cap mata: mata drop HDFE // Main HDFE object
	// cap mata: mata drop hdfe_*
	// cap drop __temp_ppmlhdfe_resid__
	// cap matrix drop ppmlhdfe_statsmatrix
	cap mata: mata drop glm
	if (`rc') exit `rc'
end


program Version
	* Github install paths
	loc reghdfe_github "https://github.com/sergiocorreia/reghdfe/raw/master/src/"
	loc ftools_github "https://github.com/sergiocorreia/ftools/raw/master/src/"

	loc reqs ftools reghdfe
	if (c(version)<13) loc reqs `reqs' boottest
	loc rc 0

	which ppmlhdfe
	di as text _n "Required packages installed?"

	foreach req of local reqs {
		cap findfile `req'.ado
		
		if (c(rc)) {
			loc rc = c(rc)
			di as text "{lalign 10:- {res:`req'}}" as error "not installed" _c
			di as text "    {stata ssc install `req':install from SSC}" _c
			di as text `"    {stata `"net install `req', from(`"``req'_github'"')"':install from Github}"'
		}
		else {
			ms_get_version `req'
			di as text "{lalign 10:- {res:`req'}} yes; version: `package_version'"
		}
	}

	error `rc'
	ftools, check // compile
	ms_get_version ftools, min_version("2.45.0")
	ms_get_version reghdfe, min_version("6.0.2")
end


program Reload
	reghdfe, reload

	* Update -ppmlhdfe-
	di as text _n  _n "{bf:ppmlhdfe: updating self}"
	di as text "{hline 64}"
	cap ado uninstall ppmlhdfe
	net install ppmlhdfe, from("C:/Git/ppmlhdfe/src")
	di as text "{hline 64}"
	di as text _n "{bf:Note:} You need to run {stata program drop _all} now."
end


program Replay, rclass
	syntax [, * eform  noHEADer noTABLE]
	if (`"`e(cmd)'"' != "ppmlhdfe") error 301
	_get_diopts options, `options'

	* Maybe disable calling the inner functions if !c(noisily)

	if ("`header'" == "") ppmlhdfe_header // _coef_table_header // reghdfe_header
	*di as text "Log pseudolikelihood = " as res e(ll)
	if ("`table'" == "") _coef_table, `options' `eform' // ereturn display, `options'
	
	return add // adds r(level), r(table), etc. to ereturn (before the footnote deletes them)
	if ("`e(absvars)'" != "") reghdfe_footnote
end


program Estimate, eclass

	ereturn clear
	syntax varlist(fv ts numeric) [if] [in] [pw fw/] , ///
	[   	/// -----------------
			/// GLM Options
			/// -----------------
		VCE(string) CLuster(string) 		///
		EXPosure(varname) OFFset(varname)	/// include offset==log(exposure) w/coef of 1
		EForm IRr 							/// Report incidence-rate ratios exp(b_i), i.e. eform
			/// -----------------
			/// IRLS Options
			/// -----------------
		GUESS(string) 						/// How to define initial conditions (default, ols, etc.)
		TOLerance(real 1e-8) 				/// IRLS Tolerance
		MAXITerations(integer 10000) 		/// Maximum number of iterations
		SEParation(string) 					/// Techniques used to check for complete separation
		D(name) D2							/// Save residuals (default name is: _reghdfe_resid)
			/// -----------------
			/// HDFE options
			/// -----------------
		Absorb(string) NOAbsorb 			/// Mutually exclusive
		ITOLerance(real -1)					/// Target tolerance used internally by -reghdfe-; known internally as -target_inner_tol-
			/// -----------------
			/// Advanced options
			/// -----------------
		TIMEit 								/// (Disabled)
		Verbose(integer 0) 					///
		noLog								/// Hide iteration log
			/// -----------------
			/// Secret -tagsep- options (to find and fix separation with ReLU algorithm)
			/// -----------------
		TAGSEP(name)						/// Indicator variable for separated observations
		ZVARname(name)						/// Save certificate of separation
		R2									/// Run regression against certificate of separation (to show that R2=1)
			/// -----------------
			/// Undocumented options
			/// -----------------
		/// There are three types of options beyond those above:
		/// a) Display options parsed by -_get_diopts-
		/// b) -reghdfe- options: accel() transform() prune pool() dof() groupvar() rre() keepsingletons
		/// c) Advanced options that correspond to properties of the GLM Mata class: accel_start, standardize_data, use_exact_solver, etc.
	] [*]


// --------------------------------------------------------------------------
// Validate options
// --------------------------------------------------------------------------
	
	_get_diopts diopts options, `options' // store display options in `diopts', keep the rest in `options'
	_assert ("`exposure'" != "") + ("`offset'" != "") < 2, msg("only one of offset() or exposure() can be specified") rc(198)
	
	if (inlist("`guess'", "", "default")) loc guess simple
	if !inlist("`guess'", "simple", "ols") {
		loc guess = subinstr("`guess'", "var ", "variable ", 1)
		_assert strpos("`guess'", "variable "), msg(`"guess() invalid; valid initial value options are "simple", "ols", and "variable <varname>""')
		gettoken guess guessvar : guess
		cap confirm numeric var `guessvar'
		loc rc = c(rc)
		assert inlist(`rc', 0, 111)
		_assert (!`rc'), msg("guess(variable `guessvar') invalid; variable must exist and be numeric")
	}
	
	if ("`irr'" != "") loc eform "eform" // Synonym for eform
	
	loc timeit = ("`timeit'"!="")

	loc all_separation_techniques "fe relu simplex mu"
	loc separation = subinstr(`"`separation'"', "ir", "relu", 1)
	if inlist("`separation'", "", "def", "default", "standard", "auto", "on") loc separation "fe simplex relu" // "fe simplex mu"
	if inlist("`separation'", "all", "full") loc separation "`all_separation_techniques'"
	if inlist("`separation'", "no", "off", "none") loc separation
	_assert "`: list separation - all_separation_techniques'" == "", msg(`"separation(`separation') not allowed"')
	if (`verbose'>1) di as text _n "- Techniques used for detecting and fixing separation: {res}`separation'"

	* Allow cluster(vars) as a shortcut for vce(cluster vars)
	if ("`cluster'"!="") {
		_assert ("`vce'"==""), msg("only one of cluster() and vce() can be specified") rc(198)
		loc vce cluster `cluster'
	}

	* Save sum of FEs ("d")
	if ("`d2'" != "") {
		_assert ("`d'" == ""), msg("d() syntax error")
		cap drop _ppmlhdfe_d // destructive!
		loc d _ppmlhdfe_d
	}
	else if ("`d'"!="") {
		conf new var `d'
	}


// --------------------------------------------------------------------------
// Parse all options except absorb()
// --------------------------------------------------------------------------

	* Split varlist into <depvar> and <indepvars>
	ms_parse_varlist `varlist'
	if (`verbose' > 0) {
		di as text _n "## Parsing varlist: {res}`varlist'"
		return list
	}
	loc depvar `r(depvar)'
	loc indepvars `r(indepvars)'
	loc fe_format "`r(fe_format)'"
	loc basevars `r(basevars)'

	* Parse Weights (weight type saved in `weight'; weight var in `exp')
	if ("`weight'"!="") {
	        unab exp : `exp', min(1) max(1) // simple weights only
	}

	* Parse VCE
	ms_parse_vce, vce(`vce') weighttype(`weight')
	if (`verbose' > 0) {
		di as text _n "## Parsing vce({res}`vce'{txt})"
		sreturn list
	}
	local vcetype `s(vcetype)'
	if ("`vcetype'"=="unadjusted") local vcetype "robust" // PPML uses robust SEs
	local clustervars `s(clustervars)' // e.g. "exporter#importer"
	local base_clustervars `s(base_clustervars)' // e.g. "exporter importer"

	* Set sample
	loc varlist `depvar' `indepvars' `base_clustervars'
	marksample touse, strok // based on varlist + cluster + offset + if + in + weight

	* Parse offset/exposure (after touse is created)
	loc offvar `exposure'`offset'
	if ("`exposure'" != "") {
		_assert (`exposure' > 0) | !(`touse'), msg("exposure() must be greater than zero") rc(459)
		tempvar offset
		qui gen double `offset' = ln(`exposure')
		loc offvar "ln(`offvar')"
	}
	markout `touse' `offset'
	la var `touse' "touse"


// --------------------------------------------------------------------------
// Mata: Construct and call GLM()
// --------------------------------------------------------------------------
* If separation includes -fe- we will drop observations where depvar is always zero within a fixed effect group (e.g. if y==0 for a given individual)
* Ths is accomplished through a hack: we use [iw=depvar] which gets special treatment within HDFE()

	if (`verbose'>1) di as text _n "{bf:- Parsing absorb() and creating HDFE object:}"
	loc options `options' precondition // -precondition- stores the LSMR preconditioner (the weighting method used by ReLU uses it)
	ms_add_comma, cmd(`absorb') opt(`options') loc(absorb) // Pass remaining options to reghdfe

	mata: glm = GLM()
	mata: glm.depvar = "`depvar'"
	mata: glm.indepvars = "`indepvars'" // Don't run -ms_expand_varlist- yet!
	mata: glm.offsetvar = "`offset'"
	mata: glm.touse = "`touse'"
	mata: glm.absorb = "`absorb'"
	mata: glm.weight_type = "`weight'"
	mata: glm.weight_var = "`exp'"
	mata: glm.separation = tokens("`separation'") // fe relu simplex mu
	mata: glm.initial_guess_method = "`guess'"
	mata: glm.initial_guessvar = "`guessvar'"
	if (`verbose') mata: glm.verbose = `verbose'
	if ("`log'" == "nolog") mata: glm.log = 0
	mata: glm.vcetype = "`vcetype'"
	mata: glm.clustervars = "`clustervars'"
	mata: glm.base_clustervars = "`base_clustervars'"
	mata: glm.tolerance = `tolerance'
	if (`itolerance' > 0) mata: glm.target_inner_tol = `itolerance'
	mata: glm.maxiter = `maxiterations'

	// We'll intersect tagsep.ado functionality
	if ("`tagsep'" != "") {
		di as text "{bf: (identifying separated observations instead of running regressions)}"
		mata: glm.separation = "relu" // Override
		mata: glm.relu_sepvarname = "`tagsep'"
		mata: glm.relu_zvarname = "`zvarname'"
		mata: glm.relu_report_r2 = "`r2'" != ""
	}

	mata: glm.validate_parameters()
	mata: glm.init_fixed_effects()
	mata: glm.init_variables()
	* Intercept error when there are no obs. left; provide helpful message
	cap noi mata: glm.init_separation()
	loc rc = c(rc)
	if (`rc'==2001) {
		di as text "Insufficient observations after dropping separated obs."
		di as text `"To view the "direction of recession" (Geyer 2009), type e.g.:"'
		di as text ". ppmlhdfe ..., absorb(...) tagsep(sep) zvar(z) r2"
	}
	if (`rc') exit `rc'
	if ("`tagsep'" != "") {
		format %1.0f `tagsep'
		format %10.2g `zvarname'
		exit
	}

	tempname b V N rank df_r ll ll_0 deviance chi2
	mata: glm.solve("`b'", "`V'", "`N'", "`rank'", "`df_r'", "`ll'", "`ll_0'", "`deviance'", "`chi2'", "`d'")


// -----------------------------------------------------------------------
// Validate and post results
// -----------------------------------------------------------------------

	mata: assert_msg(glm.HDFE.weight_type == "`weight'", "wrong value of HDFE.weight_type")
	mata: assert_msg(glm.HDFE.weight_var == "`exp'", "wrong value of HDFE.weight_var")
	mata: st_local("indepvars", glm.HDFE.fullindepvars)

	* Post results
	if ("`indepvars'" != "") {
		// matrix list `b'
		//if (1) loc indepvars `indepvars' _cons // BUGBUG: only enable this if cons is enabled
		matrix colnames `b' = `indepvars'
		matrix colnames `V' = `indepvars'
		matrix rownames `V' = `indepvars'
		_ms_findomitted `b' `V'
		ereturn post `b' `V', esample(`touse') buildfvinfo depname(`depvar')
	}
	else {
		ereturn post, esample(`touse') buildfvinfo depname(`depvar')
	}

	// Note: the PDF manual for "return" explains how to fill this.

	ereturn scalar N       = `N'
	ereturn scalar rank    = `rank'
	//ereturn scalar df_r    = `df_r'
	ereturn scalar df    = `df_r' // GLM doesn't save it as df_r but as df
	ereturn local  cmd     "ppmlhdfe"
	mata: glm.HDFE.post()
	mata: st_numscalar("e(num_separated)", glm.num_separated)
	mata: st_numscalar("e(N_full)", st_numscalar("e(N)") + glm.HDFE.num_singletons + glm.num_separated) // After HDFE.post()
	_assert "`e(depvar)'" != ""
	
	ereturn scalar ll = `ll' // run this after HDFE.post(), which also writes ll
	ereturn scalar deviance = `deviance'
	ereturn scalar ll_0 = `ll_0'
	ereturn scalar r2_p = 1 - `ll' / `ll_0'
	ereturn scalar chi2 = `chi2' // Wald test

	ereturn scalar converged = 1
	ereturn scalar ic = `ic'
	ereturn scalar ic2 = `ic2' // number of partialling-out subiterations

	ereturn local chi2type "Wald"
	ereturn local title "HDFE {help ppmlhdfe##description:PPML} regression"
	ereturn local cmdline "ppmlhdfe `0'"
	ereturn local offset  "`offvar'"
	ereturn local predict "ppmlhdfe_p"
	ereturn local separation "`separation'"

	ereturn local marginsnotok "stdp Anscombe Cooksd Deviance Hat Likelihood Pearson Response Score Working ADJusted STAndardized STUdentized MODified" // do we need this???
	ereturn local marginsok "default"

	if ("`e(absvars)'" == "_cons") {
		ereturn local title "PPML regression"
		ereturn local title2
	}

	if ("`d'" != "") ereturn local d "`d'"

	// HDFE.post() added scalars that we need to delete (e.g. r2)
	// To do, we need to set them as empty e() locals
	ereturn local tss = ""
	ereturn local tss_within = ""
	ereturn local mss = ""
	ereturn local r2 = ""
	ereturn local r2_a = ""
	ereturn local r2_a_within = ""
	ereturn local r2_within = ""
	ereturn local report_constant = ""
	ereturn local sumweights = ""
	ereturn local F = ""

	* Display tables
	Replay, `diopts' `eform'


end


findfile "ppmlhdfe.mata"
include "`r(fn)'"

exit

/*
Poisson Equations:
- Log Likelihood: 	log f(y) = y log(μ) - μ - log(y!)
					log f(y) = y η - exp(η) - log(y!) ; where exp(η)==μ
- Estimating eqns:	X'y = X'μ
- FOC:				X'(y-μ) = 0  (akin to X'e=0 in OLS)
- Deviance:			D = 2 Σ[ y log(y/μ) - (y - μ)]
- Generalized Pearson χ2: Σ (y - μ) ^ 2 / μ

- Constant only model: "c" = b[_cons] = log(mean(y))
- LL0: Σ[ y c - exp(c) - log(y!)]

IRLS Equations (see McCullagh & Nelder - GLM, 1989, page 55):
- Linear predictor: η = xβ
- Conditional mean: μ = exp(η) (i.e. log link function)
- Working depvar: 	z = η + (y - μ) / μ ; when μ -> 0 and y = 0, z = η-1
  (i.e. a linearization of log(y) evaluated at μ)
- Weights: 			w = μ
  (i.e. the relative variance of z and y: w = [ Var(z|x) / Var(y|x) ] ^ -0.5

*/
