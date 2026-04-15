*! ivreghdfe 1.1.4  29nov2025 (bugfix for github issue #61)
*! ivreghdfe 1.1.3  04Jan2023 (bugfix for github issue #48)
*! ivreghdfe 1.1.2  29Sep2022 (bugfix for github issue #44)
*! ivreghdfe 1.1.1  14Dec2021 (experimental -margins- support)
*! ivreghdfe 1.1.0  25Feb2021
*! ivreg2 4.1.11  22Nov2019
*! authors cfb & mes
*! see end of file for version comments

*  Variable naming:
*  lhs = LHS endogenous
*  endo = X1, RHS endogenous (instrumented) = #K1
*  inexog = X2 = Z2 = included exogenous (instruments) = #K2 = #L2
*  exexog = Z1 = excluded exogenous (instruments) = #L1
*  iv = {inexog exexog} = all instruments
*  rhs = {endo inexog} = RHS regressors
*  no 0 or 1 at end of varlist means original varlist but after expansion of FV and TS vars
*  0 at the end of the name means the varlist after duplicates removed and collinearities/omitteds marked
*  1 means the same as 0 but after omitted vars dropped and extraneous FV operators "o", "b" and "n" removed.
*  0, 1 etc. also apply to _ct variables that are counts of these varlists
*  dofminus is large-sample adjustment (e.g., #fixed effects)
*  sdofminus is small-sample adjustment (e.g., #partialled-out regressors)

if c(version) < 12 & c(version) >= 9 {
* livreg2 Mata library.
* Ensure Mata library is indexed if new install.
* Not needed for Stata 12+ since ssc.ado does this when installing.
        capture mata: mata drop m_calckw()
        capture mata: mata drop m_omega()
        capture mata: mata drop ms_vcvorthog()
        capture mata: mata drop s_vkernel()
        capture mata: mata drop s_cdsy()
        mata: mata mlib index
}

*********************************************************************************
***************************** PARENT IVREG2 *************************************
****************** FORKS TO EXTERNAL IVREG2S IF CALLER < 11 *********************
*********************************************************************************

* Parent program, forks to versions as appropriate after version call
* Requires byable(onecall)
program define ivreghdfe, eclass byable(onecall) /* properties(svyj) */ sortpreserve
        local lversion 04.1.11

        ms_get_version ftools, min_version("2.49.1")
        ms_get_version reghdfe, min_version("6.12.5")

* local to store Stata version of calling program
        local caller = _caller()

* reghdfe 6 requires stata 13
        version 13

* Replay = no arguments before comma    
        if replay() {
* Call to ivreg2 will either be for version, in which case there should be no other arguments,
* or a postestimation call, in which case control should pass to main program.
                syntax [, VERsion * ]
                if "`version'"~="" & "`options'"=="" {
* Call to ivreg2 is for version
                        di in gr "`lversion'"
                        ereturn clear
                        ereturn local version `lversion'
                        exit    
                }
                else if "`version'"~="" & "`options'"~="" {
* Improper use of version option
di as err "invalid syntax - cannot combine version with other options"
                        exit 198
                }
                else {
* Postestimation call, so put `options' macro (i.e. *) back into `0' macro with preceding comma
                        local 0 `", `options'"'
                }
        }

* replay can't be combined with by
        if replay() & _by() {
di as err "invalid syntax - cannot use by with replay"
                exit 601
        }

* Handling of by. ivreg2x programs are byable(recall), so must set prefix for them.
        if _by() {
                local BY `"by `_byvars'`_byrc0':"'
        }

* If calling version is < 11, pass control to earlier version
* Note that this means calls from version 11.0 will not go to legacy version
* but will fail requirement of version 11.2 in main code.
        if `caller' < 11 {
                local ver = round(`caller')
                local ivreg2cmd ivreg2`ver'
* If replay, change e(cmd) macro to name of legacy ivreg2 before calling it, then change back
* Note by not allowed with replay; caught above so prefix not needed here.
                if replay() {
                        ereturn local cmd "`ivreg2cmd'"
                        `ivreg2cmd' `0'
                        ereturn local cmd "ivreg2"

                }
                else {
* If not replay, call legacy ivreg2 and then add macros
                        `BY' `ivreg2cmd' `0'
                        ereturn local cmd "ivreg2"
                        ereturn local ivreg2cmd "`ivreg2cmd'"
                        ereturn local version `lversion'
                        ereturn local predict ivreg2_p
                }
                exit
        }

// Version is 11 or above.
// Pass control to current estimation program ivreg211.
        if replay() {
                ivreg211 `0'
        }
// If not replay, call ivreg211 and then add macros
        else {
                // use to separate main args from options
                syntax [anything] [if] [in] [aw fw pw iw] [, * ]
                // append caller(.) to options
                `BY' ivreg211 `anything' `if' `in' [`weight' `exp'], `options' caller(`caller')
//              `BY' ivreg211 `0'
                ereturn local cmd "ivreghdfe"
                ereturn local ivreg2cmd "ivreghdfe"
                ereturn local version `lversion'
                ereturn local predict reghdfe // ivreg2_p    <- to enable -predict- and -margins-
                ereturn local cmdline ivreghdfe `0'                //  `0' rather than `*' in case of any "s in string
                if (e(N_hdfe)!=  .) ereturn local predict reghdfe_p
                cap mata: mata drop HDFE // prefix ivreg211 call with capture?
                cap mata: mata drop hdfe_residuals
        }

end
*********************************************************************************
*************************** END PARENT IVREG2 ***********************************
*********************************************************************************


********************* EXIT IF STATA VERSION < 11 ********************************

* When do file is loaded, exit here if Stata version calling program is < 11.
* Prevents loading of rest of program file (could cause earlier Statas to crash).

if c(stata_version) < 11 {
        exit
}

******************** END EXIT IF STATA VERSION < 11 *****************************


*********************************************************************************
***************** BEGIN MAIN IVREG2 ESTIMATION CODE *****************************
*********************************************************************************

* Main estimation program
program define ivreg211, eclass byable(recall) sortpreserve
        version 11.2

        local ivreg2cmd "ivreg211"                      //  actual command name
        local ivreg2name "ivreg2"                       //  name used in command line and for default naming of equations etc.

        if replay() {
                syntax [,                                                                                               ///
                                FIRST FFIRST RF SFIRST                                                  ///
                                dropfirst droprf dropsfirst                                             ///
                                Level(integer $S_level)                                                 ///
                                NOHEader NOFOoter                                                               ///
                                EForm(string) PLUS                                                              ///
                                NOOMITTED vsquish noemptycells                                  ///
                                baselevels allbaselevels                                                ///
                                VERsion                                                                                 ///
                                caller(real 0)                                                                  ///
                                ]
                if "`version'" != "" & "`first'`ffirst'`rf'`noheader'`nofooter'`dropfirst'`droprf'`eform'`plus'" != "" {
                        di as err "option version not allowed"
                        error 198
                }
                if "`version'" != "" {
                        di in gr "`lversion'"
                        ereturn clear
                        ereturn local version `lversion'
                        exit
                }
                if `"`e(cmd)'"' != "ivreghdfe"  {
                        error 301
                }
// Set display options
                local dispopt   eform(`eform') `noomitted' `vsquish' `noemptycells' `baselevels' `allbaselevels'

// On replay, set flag so saved eqns aren't dropped
                if "`e(firsteqs)'" != "" & "`dropfirst'" == "" {
                        local savefirst "savefirst"
                }
                if "`e(rfeq)'" != "" & "`droprf'" == "" {
                        local saverf "saverf"
                }
                if "`e(sfirsteq)'" != "" & "`dropsfirst'" == "" {
                        local savesfirst "savesfirst"
                }
// On replay, re-display collinearities and duplicates messages
                DispCollinDups
        }
        else {
// MAIN CODE BLOCK

// Start parsing
                syntax [anything(name=0)] [if] [in] [aw fw pw iw/] [,           ///
                                NOID NOCOLLIN                                                                           ///
                                FIRST FFIRST SAVEFIRST SAVEFPrefix(name)                        ///
                                RF SAVERF SAVERFPrefix(name)                                            ///
                                SFIRST SAVESFIRST SAVESFPrefix(name)                            ///
                                SMall NOConstant                                                                        ///
                                Robust CLuster(varlist) kiefer dkraay(integer 0)        ///
                                VCE(string) ///
                                BW(string) kernel(string) center                                        ///
                                GMM GMM2s CUE                                                                           ///
                                LIML COVIV FULLER(real 0) Kclass(real 0)                        ///
                                ORTHOG(string) ENDOGtest(string) REDundant(string)      ///
                                PARTIAL(string) FWL(string)                                                     ///
                                Absorb(string) ///
                                RESiduals(name) RESiduals2  /* if no name, residuals saved as _reghdfe_resid */ ///
                                Level(integer $S_level)                                                         ///
                                NOHEader NOFOoter NOOUTput                                                      ///
                                bvclean NOOMITTED omitted vsquish noemptycells          ///
                                baselevels allbaselevels                                                        ///
                                title(string) subtitle(string)                                          ///
                                DEPname(string) EForm(string) PLUS                                      ///
                                Tvar(varname) Ivar(varname)                                                     ///
                                B0(string) SMATRIX(string) WMATRIX(string)                      ///
                                sw psd0 psda useqr                                                                      ///
                                dofminus(integer 0) sdofminus(integer 0)                        ///
                                NOPARTIALSMALL                                                                          ///
                                fvall fvsep                                                                                     ///
                                caller(real 0)                                                                          ///
                                * ]
    
        * Allow cluster(vars) as a shortcut for vce(cluster vars)
        if ("`vce'"!="") {
            _assert ("`cluster'"==""), msg("only one of cluster() and vce() can be specified") rc(198)
            _assert ("`robust'"==""), msg("only one of robust() and vce() can be specified") rc(198)
            gettoken vce_type vce_rest : vce
            _assert inlist("`vce_type'", "cluster", "robust", "unadjusted"), msg("vce() only supports cluster, robust, and unadjusted") rc(198)

            if ("`vce_type'" == "cluster") {
                loc cluster "`vce_rest'"
                _assert ("`vce_rest'"!=""), msg("vce(cluster ...) requires variables") rc(198)
            }
            if ("`vce_type'" == "robust") {
                _assert ("`vce_rest'"==""), msg("vce(robust) does not support varnames or other options") rc(198)
                loc robust "robust"
            }
            loc vce // clear out local just to be sure (as it's used later in the code for other purposes)
        }

        if (`"`absorb'"' != "") {
                // absorb implies...
                loc small small
                loc noconstant noconstant
                loc nopartialsmall
                loc reghdfe_options `"absorb(`absorb') `options' nopartialout varlist_is_touse"' // (nopartialout implies keepmata)

                if ("`residuals2'" != "") {
                    cap drop _reghdfe_resid // destructive!
                    loc residuals _reghdfe_resid
                }
                else if ("`residuals'"!="") {
                    conf new var `residuals'
                }
        }

//  Confirm ranktest is installed (necessary component).
                checkversion_ranktest `caller'
                local ranktestcmd `r(ranktestcmd)'

// Parse after clearing any sreturn macros (can be left behind in Stata 11)
                sreturn clear
                ivparse `0',    ivreg2name(`ivreg2name')                ///  needed for some options
                                                partial(`partial')                              ///
                                                fwl(`fwl')                                              ///  legacy option
                                                orthog(`orthog')                                ///
                                                endogtest(`endogtest')                  ///
                                                redundant(`redundant')                  ///
                                                depname(`depname')                              ///
                                                `robust'                                                ///
                                                cluster(`cluster')                              ///
                                                bw(`bw')                                                ///
                                                kernel(`kernel')                                ///
                                                dkraay(`dkraay')                                ///
                                                `center'                                                ///
                                                `kiefer'                                                ///
                                                `sw'                                                    ///
                                                `noconstant'                                    ///
                                                tvar(`tvar')                                    ///
                                                ivar(`ivar')                                    ///
                                                `gmm2s'                                                 ///
                                                `gmm'                                                   ///  legacy option, produces error message
                                                `cue'                                                   ///
                                                `liml'                                                  ///
                                                fuller(`fuller')                                ///
                                                kclass(`kclass')                                ///
                                                b0(`b0')                                                ///
                                                wmatrix(`wmatrix')                              ///
                                                `noid'                                                  ///
                                                `savefirst'                                             ///
                                                savefprefix(`savefprefix')              ///
                                                `saverf'                                                ///
                                                saverfprefix(`saverfprefix')    ///
                                                `savesfirst'                                    ///
                                                savesfprefix(`savesfprefix')    ///
                                                dofminus(`dofminus')                    ///
                                                `psd0'                                                  ///
                                                `psda'                                                  ///
                                                `nocollin'                                              ///
                                                `useqr'                                                 ///
                                                `bvclean'                                               ///
                                                eform(`eform')                                  ///
                                                `noomitted'                                             ///
                                                `vsquish'                                               ///
                                                `noemptycells'                                  ///
                                                `baselevels'                                    ///
                                                `allbaselevels'

// varlists are unexpanded; may be empty
                local lhs                       `s(lhs)'
                local depname           `s(depname)'
                local endo                      `s(endo)'
                local inexog            `s(inexog)'
                local exexog            `s(exexog)'
                local partial           `s(partial)'
                local cons                      =s(cons)
                local partialcons       =s(partialcons)
                local tvar                      `s(tvar)'
                local ivar                      `s(ivar)'
                local tdelta            `s(tdelta)'
                local tsops                     =s(tsops)
                local fvops                     =s(fvops)
                local robust            `s(robust)'
                local cluster           `s(cluster)'
                local bw                        =`s(bw)'                                //  arrives as string but return now as number
                local bwopt                     `s(bwopt)'
                local kernel            `s(kernel)'                             //  also used as flag for HAC estimation
                local center            =`s(center)'                    //  arrives as string but now boolean
                local kclassopt         `s(kclassopt)'
                local fulleropt         `s(fulleropt)'
                local liml                      `s(liml)'
                local noid                      `s(noid)'                               //  can also be triggered by b0(.) option
                local useqr                     =`s(useqr)'                             //  arrives as string but now boolean; nocollin=>useqr
                local savefirst         `s(savefirst)'
                local savefprefix       `s(savefprefix)'
                local saverf            `s(saverf)'
                local saverfprefix      `s(saverfprefix)'
                local savesfirst        `s(savesfirst)'
                local savesfprefix      `s(savesfprefix)'
                local psd                       `s(psd)'                                //  triggered by psd0 or psda
                local dofmopt           `s(dofmopt)'
                local bvclean           =`s(bvclean)'                   //  arrives as string but return now as boolean
                local dispopt           `s(dispopt)'

// Can now tsset; sortpreserve will restore sort after exit
                if `tsops' | "`kernel'"~="" {
                        cap tsset                                                               //  restores sort if tsset or xtset but sort disrupted
                        if _rc>0 {
                                tsset `ivar' `tvar'
                        }
                }

***********************************************************

// Weights
// fweight and aweight accepted as is
// iweight not allowed with robust or gmm and requires a trap below when used with summarize
// pweight is equivalent to aweight + robust
// Since we subsequently work with wvar, tsrevar of weight vars in weight `exp' not needed.

                tempvar wvar
                if "`weight'" == "fweight" | "`weight'"=="aweight" {
                        local wtexp `"[`weight'=`exp']"'
                        qui gen double `wvar'=`exp'
                }
                if "`weight'" == "fweight" & "`kernel'" !="" {
                        di in red "fweights not allowed (data are -tsset-)"
                        exit 101
                }
                if "`weight'" == "fweight" & "`sw'" != "" {
                        di in red "fweights currently not supported with -sw- option"
                        exit 101
                }
                if "`weight'" == "iweight" {
                        if "`robust'`cluster'`gmm2s'`kernel'" !="" {
                                di in red "iweights not allowed with robust or gmm"
                                exit 101
                        }
                        else {
                                local wtexp `"[`weight'=`exp']"'
                                qui gen double `wvar'=`exp'
                        }
                }
                if "`weight'" == "pweight" {
                        local wtexp `"[aweight=`exp']"'
                        qui gen double `wvar'=`exp'
                        local robust "robust"
                }
                if "`weight'" == "" {
* If no weights, define neutral weight variable
                        qui gen byte `wvar'=1
                }

********************************************************************************
// markout sample
// include `tvar' to limit sample to where tvar is available, but only if TS operators used
                marksample touse
                if `tsops' {
                        markout `touse' `lhs' `inexog' `exexog' `endo' `cluster' `tvar', strok
                }
                else {
                        markout `touse' `lhs' `inexog' `exexog' `endo' `cluster', strok
                }

* Create HDFE object and update touse
if (`"`absorb'"' != "") {
    if ("`weight'" != "") loc reghdfe_weight "[`weight'=`wvar']"
	if (`"`cluster'"' != "") loc reghdfe_options `"`reghdfe_options' vce(cluster `cluster')"'
    reghdfe `touse' `reghdfe_weight', `reghdfe_options' // create HDFE object
}

********************************************************************************
// weight factor and sample size
// Every time a weight is used, must multiply by scalar wf ("weight factor")
// wf=1 for no weights, fw and iw, wf = scalar that normalizes sum to be N if aw or pw

                sum `wvar' if `touse' `wtexp', meanonly
// Weight statement
                if "`weight'" ~= "" {
di in gr "(sum of wgt is " %14.4e `r(sum_w)' ")"
                }
                if "`weight'"=="" | "`weight'"=="fweight" | "`weight'"=="iweight" {
// Effective number of observations is sum of weight variable.
// If weight is "", weight var must be column of ones and N is number of rows
                        local wf=1
                        local N=r(sum_w)
                }
                else if "`weight'"=="aweight" | "`weight'"=="pweight" {
                        local wf=r(N)/r(sum_w)
                        local N=r(N)
                }
                else {
// Should never reach here
di as err "ivreg2 error - misspecified weights"
                        exit 198
                }
                if `N'==0 {
di as err "no observations"
                        exit 2000
                }

***************************************************************
// Time-series data
// tindex used by Mata code so that ts operators work correctly

                tempvar tindex
                qui gen `tindex'=1 if `touse'
                qui replace `tindex'=sum(`tindex') if `touse'

                if `tsops' | "`kernel'"~="" {
// Report gaps in data
                        tsreport if `touse', panel
                        if `r(N_gaps)' != 0 {
di as text "Warning: time variable " as res "`tvar'" as text " has "            ///
                                as res "`r(N_gaps)'" as text " gap(s) in relevant range"
                        }
// Set local macro T and check that bw < (T-1)
                        sum `tvar' if `touse', meanonly
                        local T = r(max)-r(min) + 1
                        local T1 = `T' - 1
                        if (`bw' > (`T1'/`tdelta')) {
di as err "invalid bandwidth in option bw() - cannot exceed timespan of data"
                                exit 198
                        }
                }

// kiefer VCV = kernel(tru) bw(T) and no robust with tsset data
                if "`kiefer'" ~= "" {
                        local bw        =`T'
                }

*********** Column of ones for constant set up here **************

                if "`noconstant'"=="" {
// If macro not created, automatically omitted.
                        tempvar ones
                        qui gen byte `ones' = 1 if `touse'
                }

************* Varlists, FV varlists, duplicates *****************
// Varlists come in 4 versions, e.g., for inexog:
// (a) inexog = full list of original expanded vnames; may have duplicates
// (b) inexog0 = as with inexog with duplicates removed but RETAINING base/omitted/etc. varnames
// (c) inexog1 = as with inexog0 but WITHOUT base/omitted/etc.
// (d) fv_inexog1 = corresponding list with temp vars minus base/omitted/etc., duplicates, collinearities etc.
// Varlists (c) and (d) are definitive, i.e., have the variables actually used in the estimation.

// Create consistent expanded varlists.
// "Consistent" means base vars for FVs must be consistent
// hence default rhs=endo+inexog is expanded as one.
// fvall: overrides, endo+inexog+exexog expanded as one
// fvsep: overrides, endo, inexog and exexog expanded separately
// NB: expanding endo+inexog+exexog is dangerous because
//     fvexpand can zap a list in case of overlap
//     e.g. fvexpand mpg + i(1/4).rep78 + i5.rep78 
//             => mpg 1b.rep78 2.rep78 3.rep78 4.rep78 5.rep78
//     but fvexpand mpg + i.rep78 + i5.rep78
//                              => mpg 5.rep78

                CheckDupsCollin,                                                        ///
                                                        lhs(`lhs')                              ///
                                                        endo(`endo')                    ///
                                                        inexog(`inexog')                ///
                                                        exexog(`exexog')                ///
                                                        partial(`partial')              ///
                                                        orthog(`orthog')                ///
                                                        endogtest(`endogtest')  ///
                                                        redundant(`redundant')  ///
                                                        touse(`touse')                  ///
                                                        wvar(`wvar')                    ///
                                                        wf(`wf')                                ///
                                                        `noconstant'                    ///
                                                        `nocollin'                              ///
                                                        `fvall'                                 ///
                                                        `fvsep'

// Replace basic varlists and create "0" versions of varlists
                foreach vl in lhs endo inexog exexog partial orthog endogtest redundant {
                        local `vl'              `s(`vl')'
                        local `vl'0             `s(`vl'0)'
                }
                local dups              `s(dups)'
                local collin    `s(collin)'
                local ecollin   `s(ecollin)'

// Create "1" and fv versions of varlists
                foreach vl in lhs endo inexog exexog partial orthog endogtest redundant {
                        foreach var of local `vl'0 {                                            //  var-by-var so that fvrevar doesn't decide on base etc.
                                _ms_parse_parts `var'
                                if ~`r(omit)' {                                                                 //  create temp var only if not omitted
                                        fvrevar `var'   if `touse'
                                        local `vl'1             ``vl'1' `var'
                                        local fv_`vl'1  `fv_`vl'1' `r(varlist)'
                                }
                        }
                        local `vl'1             : list retokenize `vl'1
                        local fv_`vl'1  : list retokenize fv_`vl'1
                }

// Check that LHS expanded to a single variable
                local wrongvars_ct      : word count `lhs'
                if `wrongvars_ct' > 1 {
di as err "multiple dependent variables specified: `lhs'"
                        error 198
                }

// Check that option varlists are compatible with main varlists
// orthog()
                local wrongvars         : list orthog1 - inexog1
                local wrongvars         : list wrongvars - exexog1
                local wrongvars_ct      : word count `wrongvars'
                if `wrongvars_ct' {
di as err "Error: `wrongvars' listed in orthog() but does not appear as exogenous." 
                        error 198
                }
// endog()
                local wrongvars         : list endogtest1 - endo1
                local wrongvars_ct      : word count `wrongvars'
                if `wrongvars_ct' {
di as err "Error: `wrongvars' listed in endog() but does not appear as endogenous." 
                        error 198
                }
// redundant()
                local wrongvars         : list redundant1 - exexog1
                local wrongvars_ct      : word count `wrongvars'
                if `wrongvars_ct' {
di as err "Error: `wrongvars' listed in redundant() but does not appear as exogenous." 
                        error 198
                }

// And create allnames macros
                local allnames          `lhs' `endo' `inexog' `exexog'
                local allnames0         `lhs0' `endo0' `inexog0' `exexog0'
                local allnames1         `lhs1' `endo1' `inexog1' `exexog1'
                local fv_allnames1      `fv_lhs1' `fv_endo1' `fv_inexog1' `fv_exexog1'


// *************** Partial-out block ************** //

// `partial' has all to be partialled out except for constant
                if "`partial1'" != "" | `partialcons'==1 | "`absorb'" != "" {
                        preserve

                        *====================================================================
                        * IVREGHDFE BLOCK
                        *====================================================================
                        * Need to save resids if saving FEs, even if temporarily
                        mata: st_local("save_any_fe", strofreal(HDFE.save_any_fe))
                        if ("`residuals'" == "" & `save_any_fe') {
                                loc residuals "__temp_reghdfe_resid__"
                        }

                        if ("`residuals'" != "") {
                                tempvar sortpreserve2
                                gen double `sortpreserve2' = _n
                        }
                        *====================================================================

// Remove partial0 from inexog0.
// Remove partial1 from inexog1.
                        local inexog0           : list inexog0 - partial0
                        local inexog1           : list inexog1 - partial1
                        local fv_inexog1        : list fv_inexog1 - fv_partial1

// Check that cluster, weight, tvar or ivar variables won't be transformed
// Use allnames1 (expanded varlist)
                        if "`cluster'"~="" {
                                local pvarcheck : list cluster in allnames1
                                if `pvarcheck' {
di in r "Error: cannot use cluster variable `cluster' as dependent variable, regressor or IV"
di in r "       in combination with -partial- option." 
                                error 198
                                }
                        }
                        if "`tvar'"~="" {
                                local pvarcheck : list tvar in allnames1
                                if `pvarcheck' {
di in r "Error: cannot use time variable `tvar' as dependent variable, regressor or IV"
di in r "       in combination with -partial- option." 
                                error 198
                                }
                        }
                        if "`ivar'"~="" {
                                local pvarcheck : list ivar in allnames1
                                if `pvarcheck' {
di in r "Error: cannot use panel variable `ivar' as dependent variable, regressor or IV"
di in r "       in combination with -partial- option." 
                                error 198
                                }
                        }
                        if "`wtexp'"~="" {
                                tokenize `exp', parse("*/()+-^&|~")
                                local wvartokens `*'
                                local nwvarnames : list allnames1 - wvartokens
                                local wvarnames  : list allnames1 - nwvarnames
                                if "`wvarnames'"~="" {
di in r "Error: cannot use weight variables as dependent variable, regressor or IV"
di in r "       in combination with -partial- option." 
                                error 198
                                }
                        }
// Partial out
// But first replace everything with doubles
                        recast double `fv_lhs1' `fv_endo1' `fv_inexog1' `fv_exexog1' `fv_partial1'

if ("`absorb'" != "") {
        loc hdfe_varlist `fv_lhs1' `fv_endo1' `fv_inexog1' `fv_exexog1' `fv_partial1'
        mata: HDFE.partial_out(tokens("`hdfe_varlist'"), 0, 1) // don't save TSS; standardize inputs
        mata: st_store(HDFE.sample, tokens("`hdfe_varlist'"), HDFE.solution.data :* HDFE.solution.stdevs)
        mata: HDFE.solution.data = . // save memory
        mata: st_local("absorb_ct", strofreal(HDFE.df_a))
        assert `absorb_ct'`' != .
        if (`absorb_ct'==0) loc absorb_ct 1 // adjustment to match ivreg2 and old reghdfe (happens if absvar is nested in cluster)
        loc partial_ct 0
        loc partialcons `absorb_ct'
}

if ("`partial1'" != "" | `partialcons'==1) {
        mata: s_partial ("`fv_lhs1'",                   ///
                         "`fv_endo1'",                   ///
                         "`fv_inexog1'",                 ///
                         "`fv_exexog1'",                 ///
                         "`fv_partial1'",                ///
                         "`touse'",                              ///
                         "`weight'",                             ///
                         "`wvar'",                               ///
                         `wf',                                   ///
                         `N',                                    ///
                         `cons')
        local partial_ct : word count `partial1'
}

// Constant is partialled out, unless nocons already specified in the first place
                        capture drop `ones'
                        local ones ""
                        if "`noconstant'" == "" {
// partial_ct used for small-sample adjustment to regression F-stat
                                local partial_ct = `partial_ct' + 1
                                local noconstant "noconstant"
                                local cons 0
                        }

                        if ("`absorb'" != "") {
                        	local partial_ct = `partial_ct' + `absorb_ct'
                        }
                }
                else {
// Set count of partial vars to zero if option not used
                        local partial_ct 0
                        local partialcons 0
                }
// Add partial_ct to small dof adjustment sdofminus
                if "`nopartialsmall'"=="" {
                        local sdofminus = `sdofminus'+`partial_ct'
                }

*********************************************

                local rhs0                      `endo0' `inexog0'                               //  needed for display of omitted/base/etc.
                local rhs1                      `endo1' `inexog1'
                local insts1            `exexog1' `inexog1'
                local fv_insts1         `fv_exexog1' `fv_inexog1'
                local fv_rhs1           `fv_endo1' `fv_inexog1'
                local rhs0_ct           : word count `rhs0'                             //  needed for display of omitted/base/etc.
                local rhs1_ct           : word count `fv_rhs1'
                local iv1_ct            : word count `fv_insts1'
                local endo1_ct          : word count `fv_endo1'
                local exex1_ct          : word count `fv_exexog1'
                local endoexex1_c       : word count `fv_endo1' `fv_exexog1'
                local inexog1_ct        : word count `fv_inexog1'

// Counts modified to include constant if appropriate
                local rhs1_ct = `rhs1_ct' + `cons'
                local rhs0_ct = `rhs0_ct' + `cons'                                      //  needed for display of omitted/base/etc.
                local iv1_ct  = `iv1_ct' + `cons'

// Column/row names for matrices b, V, S, etc.
                local cnb0      `endo0' `inexog0'                               //  including omitted
                local cnb1      `endo1' `inexog1'                               //  excluding omitted
                local cnZ0      `exexog0' `inexog0'                             //  excluding omitted
                local cnZ1      `exexog1' `inexog1'                             //  excluding omitted
                if `cons' {
                        local cnb0      "`cnb0' _cons"
                        local cnb1      "`cnb1' _cons"
                        local cnZ0      "`cnZ0' _cons"
                        local cnZ1      "`cnZ1' _cons"
                }

*********************************************
// Remaining checks: variable counts, col/row names of b0, smatrix, wmatrix
                CheckMisc,                                                      ///
                                        rhs1_ct(`rhs1_ct')              ///
                                        iv1_ct(`iv1_ct')                ///
                                        bvector(`b0')                   ///
                                        smatrix(`smatrix')              ///
                                        wmatrix(`wmatrix')              ///
                                        cnb1(`cnb1')                    ///
                                        cnZ1(`cnZ1')

                if "`b0'"~="" {
                        tempname b0                                             //  so we can overwrite without changing original user matrix
                        mat `b0'                = r(b0)
                }
                if "`smatrix'"~="" {
                        tempname S0
                        mat `S0'                = r(S0)
                }
                if "`wmatrix'"~="" {
                        tempname wmatrix                                //  so we can overwrite without changing original user matrix
                        mat `wmatrix'   = r(W0)
                }
                
*************** Commonly used matrices ****************
                tempname YY yy yyc
                tempname XX X1X1 X2X2 X1Z X1Z1 XZ Xy
                tempname ZZ Z1Z1 Z2Z2 Z1Z2 Z1X2 Zy ZY Z2y Z2Y
                tempname XXinv X2X2inv ZZinv XPZXinv
                tempname rankxx rankzz condxx condzz

// use fv_ varlists
                mata: s_crossprods      ("`fv_lhs1'",                   ///
                                                        "`fv_endo1'",                   ///
                                                        "`fv_inexog1' `ones'",  ///
                                                        "`fv_exexog1'",                 ///
                                                        "`touse'",                              ///
                                                        "`weight'",                             ///
                                                        "`wvar'",                               ///
                                                        `wf',                                   ///
                                                        `N')
                mat `XX'                =r(XX)
                mat `X1X1'              =r(X1X1)
                mat `X1Z'               =r(X1Z)
                mat `ZZ'                =r(ZZ)
                mat `Z2Z2'              =r(Z2Z2)
                mat `Z1Z2'              =r(Z1Z2)
                mat `XZ'                =r(XZ)
                mat `Xy'                =r(Xy)
                mat `Zy'                =r(Zy)
                mat `YY'                =r(YY)
                scalar `yy'             =r(yy)
                scalar `yyc'    =r(yyc)
                mat `ZY'                =r(ZY)
                mat `Z2y'               =r(Z2y)
                mat `Z2Y'               =r(Z2Y)
                mat `XXinv'             =r(XXinv)
                mat `ZZinv'             =r(ZZinv)
                mat `XPZXinv'   =r(XPZXinv)
                scalar `condxx' =r(condxx)
                scalar `condzz' =r(condzz)

                scalar `rankzz' = rowsof(`ZZinv') - diag0cnt(`ZZinv')
                scalar `rankxx' = rowsof(`XXinv') - diag0cnt(`XXinv')
                local overid    = `rankzz' - `rankxx'

********** CLUSTER SETUP **********************************************

* Mata code requires data are sorted on (1) the first var cluster if there
* is only one cluster var; (2) on the 3rd and then 1st if two-way clustering,
* unless (3) two-way clustering is combined with kernel option, in which case
* the data are tsset and sorted on panel id (first cluster variable) and time
* id (second cluster variable).
* Second cluster var is optional and requires an identifier numbered 1..N_clust2,
* unless combined with kernel option, in which case it's the time variable.
* Third cluster var is the intersection of 1 and 2, unless combined with kernel
* opt, in which case it's unnecessary.
* Sorting on "cluster3 cluster1" means that in Mata, panelsetup works for
* both, since cluster1 nests cluster3.
* Note that it is possible to cluster on time but not panel, in which case
* cluster1 is time, cluster2 is empty and data are sorted on panel-time.
* Note also that if data are sorted here but happen to be tsset, will need
* to be re-tsset after estimation code concludes.


// No cluster options or only 1-way clustering
// but for Mata and other purposes, set N_clust vars =0
                local N_clust=0
                local N_clust1=0
                local N_clust2=0
                if "`cluster'"!="" {
                        local clopt "cluster(`cluster')"
                        tokenize `cluster'
                        local cluster1 "`1'"
                        local cluster2 "`2'"
                        if "`kernel'"~="" {
* kernel requires either that cluster1 is time var and cluster2 is empty
* or that cluster1 is panel var and cluster2 is time var.
* Either way, data must be tsset and sorted for panel data.
                                if "`cluster2'"~="" {
* Allow backwards order
                                        if "`cluster1'"=="`tvar'" & "`cluster2'"=="`ivar'" {
                                                local cluster1 "`2'"
                                                local cluster2 "`1'"
                                        }
                                        if "`cluster1'"~="`ivar'" | "`cluster2'"~="`tvar'" {
di as err "Error: cluster kernel-robust requires clustering on tsset panel & time vars."
di as err "       tsset panel var=`ivar'; tsset time var=`tvar'; cluster vars=`cluster1',`cluster2'"
                                                exit 198
                                        }
                                }
                                else {
                                        if "`cluster1'"~="`tvar'" {
di as err "Error: cluster kernel-robust requires clustering on tsset time variable."
di as err "       tsset time var=`tvar'; cluster var=`cluster1'"
                                                exit 198
                                        }
                                }
                        }
* Simple way to get quick count of 1st cluster variable without disrupting sort
* clusterid1 is numbered 1.._Nclust1.
                        tempvar clusterid1
                        qui egen `clusterid1'=group(`cluster1') if `touse'
                        sum `clusterid1' if `touse', meanonly
                        if "`cluster2'"=="" {
                                local N_clust=r(max)
                                local N_clust1=`N_clust'
                                if "`kernel'"=="" {
* Single level of clustering and no kernel-robust, so sort on single cluster var.
* kernel-robust already sorted via tsset.
                                        sort `cluster1'
                                }
                        }
                        else {
                                local N_clust1=r(max)
                                if "`kernel'"=="" {
                                        tempvar clusterid2 clusterid3
* New cluster id vars are numbered 1..N_clust2 and 1..N_clust3
                                        qui egen `clusterid2'=group(`cluster2') if `touse'
                                        qui egen `clusterid3'=group(`cluster1' `cluster2') if `touse'
* Two levels of clustering and no kernel-robust, so sort on cluster3/nested in/cluster1
* kernel-robust already sorted via tsset.
                                        sort `clusterid3' `cluster1'
                                        sum `clusterid2' if `touse', meanonly
                                        local N_clust2=r(max)
                                }
                                else {
* Need to create this only to count the number of clusters
                                        tempvar clusterid2
                                        qui egen `clusterid2'=group(`cluster2') if `touse'
                                        sum `clusterid2' if `touse', meanonly
                                        local N_clust2=r(max)
* Now replace with original variable
                                        local clusterid2 `cluster2'
                                }

                                local N_clust=min(`N_clust1',`N_clust2')

                        }               // end 2-way cluster block
                }               // end cluster block


************************************************************************************************

                tempname b W S V beta lambda j jp rss mss rmse sigmasq rankV rankS
                tempname arubin arubinp arubin_lin arubin_linp
                tempname r2 r2_a r2u r2c F Fp Fdf2 ivest

                tempvar resid
                qui gen double `resid'=.
                
*******************************************************************************************
* LIML
*******************************************************************************************

                if "`liml'`kclassopt'"~="" {

                        mata: s_liml(   "`ZZ'",                                                         ///
                                                        "`XX'",                                                         ///
                                                        "`XZ'",                                                         ///
                                                        "`Zy'",                                                         ///
                                                        "`Z2Z2'",                                                       ///
                                                        "`YY'",                                                         ///
                                                        "`ZY'",                                                         ///
                                                        "`Z2Y'",                                                        ///
                                                        "`Xy'",                                                         ///
                                                        "`ZZinv'",                                                      ///
                                                        "`fv_lhs1'",                                            ///
                                                        "`fv_lhs1' `fv_endo1'",                         ///
                                                        "`resid'",                                                      ///
                                                        "`fv_endo1' `fv_inexog1' `ones'",       ///
                                                        "`fv_endo1'",                                           ///
                                                        "`fv_exexog1' `fv_inexog1' `ones'",     ///
                                                        "`fv_exexog1'",                                         ///
                                                        "`fv_inexog1' `ones'",                          ///
                                                        `fuller',                                                       ///
                                                        `kclass',                                                       ///
                                                        "`coviv'",                                                      ///
                                                        "`touse'",                                                      ///
                                                        "`weight'",                                                     ///
                                                        "`wvar'",                                                       ///
                                                        `wf',                                                           ///
                                                        `N',                                                            ///
                                                        "`robust'",                                                     ///
                                                        "`clusterid1'",                                         ///
                                                        "`clusterid2'",                                         ///
                                                        "`clusterid3'",                                         ///
                                                        `bw',                                                           ///
                                                        "`kernel'",                                                     ///
                                                        "`sw'",                                                         ///
                                                        "`psd'",                                                        ///
                                                        "`ivar'",                                                       ///
                                                        "`tvar'",                                                       ///
                                                        "`tindex'",                                                     ///
                                                        `tdelta',                                                       ///
                                                        `center',                                                       ///
                                                        `dofminus',                                                     ///
                                                        `useqr')

                        mat `b'=r(beta)
                        mat `S'=r(S)
                        mat `V'=r(V)
                        scalar `lambda'=r(lambda)
                        local kclass=r(kclass)
                        scalar `j'=r(j)
                        scalar `rss'=r(rss)
                        scalar `sigmasq'=r(sigmasq)
                        scalar `rankV'=r(rankV)
                        scalar `rankS'=r(rankS)

                        scalar `arubin'=(`N'-`dofminus')*ln(`lambda')
                        scalar `arubin_lin'=(`N'-`dofminus')*(`lambda'-1)
                        
// collinearities can cause LIML to generate (spurious) OLS results
                        if "`nocollin'"~="" & `kclass'<1e-8 {
di as err "warning: k=1 in LIML estimation; results equivalent to OLS;"
di as err "         may be caused by collinearities"
                        }
                }

*******************************************************************************************
* OLS, IV and 2SGMM.  Also enter to get CUE starting values.
************************************************************************************************

                if "`liml'`kclassopt'`b0'"=="" {

* Call to s_gmm1s to do 1st-step GMM.
* If W or S supplied, calculates GMM beta and residuals
* If none of the above supplied, calculates GMM beta using default IV weighting matrix and residuals
* Block not entered if b0 is provided.

* 1-step GMM is efficient and V/J/Sargan can be returned if:
*   - estimator is IV, W is known and S can be calculated from 1st-step residuals
*   - S is provided (and W is NOT) so W=inv(S) and beta can be calculated using W
* 1-step GMM is inefficient if:
*   - non-iid VCE is requested
*   - W is provided

                        local effic1s =         (                                                                                                       ///
                                                                                "`gmm2s'`robust'`cluster'`kernel'"==""          ///
                                                                        |       ("`smatrix'"~="" & "`wmatrix'"=="")                     ///
                                                                )

// use fv_ varlists
                        mata: s_gmm1s(  "`ZZ'",                                                                 ///
                                                        "`XX'",                                                                 ///
                                                        "`XZ'",                                                                 ///
                                                        "`Zy'",                                                                 ///
                                                        "`ZZinv'",                                                              ///
                                                        "`fv_lhs1'",                                                    ///
                                                        "`resid'",                                                              ///
                                                        "`fv_endo1' `fv_inexog1' `ones'",               ///
                                                        "`fv_exexog1' `fv_inexog1' `ones'",             ///
                                                        "`touse'",                                                              ///
                                                        "`weight'",                                                             ///
                                                        "`wvar'",                                                               ///
                                                        `wf',                                                                   ///
                                                        `N',                                                                    ///
                                                        "`wmatrix'",                                                    ///
                                                        "`S0'",                                                                 ///
                                                        `dofminus',                                                             ///
                                                        `effic1s',                                                              ///
                                                        `overid',                                                               ///
                                                        `useqr')
                        mat `b'=r(beta)
                        mat `W'=r(W)

* If 1st-step is efficient, save remaining results and we're done
                        if `effic1s' {
                                mat `V'=r(V)
                                mat `S'=r(S)
                                scalar `j'=r(j)
                                scalar `rss'=r(rss)
                                scalar `sigmasq'=r(sigmasq)
                                scalar `rankV'=r(rankV)
                                scalar `rankS'=r(rankS)
                        }
                        else {
* ...we're not done - do inefficient or 2-step efficient GMM

* Pick up matrix left by s_gmm1s(.)
                                tempname QXZ_W_QZX
                                mat `QXZ_W_QZX'=r(QXZ_W_QZX)

* Block calls s_omega to get cov matrix of orthog conditions, if not supplied
                                if "`smatrix'"~="" {
                                        mat `S'=`S0'
                                }
                                else {
        
* NB: xtivreg2 calls ivreg2 with data sorted on ivar and optionally tvar.
*     Stock-Watson adjustment -sw- assumes data are sorted on ivar.  Checked at start of ivreg2.
        
* call abw code if bw() is defined and bw(auto) selected
                                        if `bw' != 0 {
                                                if `bw' == -1 {
                                                        tempvar abwtouse
                                                        gen byte `abwtouse' = (`resid' < .) 
                                                        abw `resid' `exexog1' `inexog1' `abwtouse',     /*
                                                                */      tindex(`tindex') nobs(`N') tobs(`T') noconstant kernel(`kernel')
                                                        local bw `r(abw)'
                                                        local bwopt "bw(`bw')"
                                                        local bwchoice "`r(bwchoice)'"
                                                }
                                        }
* S covariance matrix of orthogonality conditions
// use fv_ varlists
                                        mata: s_omega(  "`ZZ'",                                                                 ///
                                                                        "`resid'",                                                              ///
                                                                        "`fv_exexog1' `fv_inexog1' `ones'",             ///
                                                                        "`touse'",                                                              ///
                                                                        "`weight'",                                                             ///
                                                                        "`wvar'",                                                               ///
                                                                        `wf',                                                                   ///
                                                                        `N',                                                                    ///
                                                                        "`robust'",                                                             ///
                                                                        "`clusterid1'",                                                 ///
                                                                        "`clusterid2'",                                                 ///
                                                                        "`clusterid3'",                                                 ///
                                                                        `bw',                                                                   ///
                                                                        "`kernel'",                                                             ///
                                                                        "`sw'",                                                                 ///
                                                                        "`psd'",                                                                ///
                                                                        "`ivar'",                                                               ///
                                                                        "`tvar'",                                                               ///
                                                                        "`tindex'",                                                             ///
                                                                        `tdelta',                                                               ///
                                                                        `center',                                                               ///
                                                                        `dofminus')
                                        mat `S'=r(S)
                                }
        
* By this point: `b' has 1st-step inefficient beta
*                `resid' has resids from the above beta
*                `S' has vcv of orthog conditions using either `resid' or user-supplied `S0'
*                 `QXZ_W_QZX' was calculated in s_gmm1s(.) for use in s_iegmm(.)

* Inefficient IV.  S, W and b were already calculated above.
                                if "`gmm2s'"=="" & "`robust'`cluster'`kernel'"~="" {
                                        mata: s_iegmm(  "`ZZ'",                                                         ///
                                                                        "`XX'",                                                         ///
                                                                        "`XZ'",                                                         ///
                                                                        "`Zy'",                                                         ///
                                                                        "`QXZ_W_QZX'",                                          ///
                                                                        "`fv_lhs1'",                                            ///
                                                                        "`resid'",                                                      ///
                                                                        "`fv_endo1' `fv_inexog1' `ones'",       ///
                                                                        "`fv_exexog1' `fv_inexog1' `ones'",     ///
                                                                        "`touse'",                                                      ///
                                                                        "`weight'",                                                     ///
                                                                        "`wvar'",                                                       ///
                                                                        `wf',                                                           ///
                                                                        `N',                                                            ///
                                                                        "`W'",                                                          ///
                                                                        "`S'",                                                          ///
                                                                        "`b'",                                                          ///
                                                                        `dofminus',                                                     ///
                                                                        `overid',                                                       ///
                                                                        `useqr')
                                        }

* 2-step efficient GMM.  S calculated above, b and W will be updated.
                                if "`gmm2s'"~="" {
                                        mata: s_egmm(   "`ZZ'",                                                         ///
                                                                        "`XX'",                                                         ///
                                                                        "`XZ'",                                                         ///
                                                                        "`Zy'",                                                         ///
                                                                        "`ZZinv'",                                                      ///
                                                                        "`fv_lhs1'",                                            ///
                                                                        "`resid'",                                                      ///
                                                                        "`fv_endo1' `fv_inexog1' `ones'",       ///
                                                                        "`fv_exexog1' `fv_inexog1' `ones'",     ///
                                                                        "`touse'",                                                      ///
                                                                        "`weight'",                                                     ///
                                                                        "`wvar'",                                                       ///
                                                                        `wf',                                                           ///
                                                                        `N',                                                            ///
                                                                        "`S'",                                                          ///
                                                                        `dofminus',                                                     ///
                                                                        `overid',                                                       ///
                                                                        `useqr')
                                        mat `b'=r(beta)
                                        mat `W'=r(W)
                                }
        
                                mat `V'=r(V)
                                scalar `j'=r(j)
                                scalar `rss'=r(rss)
                                scalar `sigmasq'=r(sigmasq)
                                scalar `rankV'=r(rankV)
                                scalar `rankS'=r(rankS)
                        }
* Finished with non-CUE/LIML block
                }

***************************************************************************************
* Block for cue gmm
*******************************************************************************************
                if "`cue'`b0'" != "" {

* s_gmmcue is passed initial b from IV/2-step GMM block above
* OR user-supplied b0 for evaluation of CUE obj function at b0
                        mata: s_gmmcue( "`ZZ'",                                                         ///
                                                        "`XZ'",                                                         ///
                                                        "`fv_lhs1'",                                            ///
                                                        "`resid'",                                                      ///
                                                        "`fv_endo1' `fv_inexog1' `ones'",       ///
                                                        "`fv_exexog1' `fv_inexog1' `ones'",     ///
                                                        "`touse'",                                                      ///
                                                        "`weight'",                                                     ///
                                                        "`wvar'",                                                       ///
                                                        `wf',                                                           ///
                                                        `N',                                                            ///
                                                        "`robust'",                                                     ///
                                                        "`clusterid1'",                                         ///
                                                        "`clusterid2'",                                         ///
                                                        "`clusterid3'",                                         ///
                                                        `bw',                                                           ///
                                                        "`kernel'",                                                     ///
                                                        "`sw'",                                                         ///
                                                        "`psd'",                                                        ///
                                                        "`ivar'",                                                       ///
                                                        "`tvar'",                                                       ///
                                                        "`tindex'",                                                     ///
                                                        `tdelta',                                                       ///
                                                        "`b'",                                                          ///
                                                        "`b0'",                                                         ///
                                                        `center',                                                       ///
                                                        `dofminus',                                                     ///
                                                        `useqr')

                        mat `b'=r(beta)
                        mat `S'=r(S)
                        mat `W'=r(W)
                        mat `V'=r(V)
                        scalar `j'=r(j)
                        scalar `rss'=r(rss)
                        scalar `sigmasq'=r(sigmasq)
                        scalar `rankV'=r(rankV)
                        scalar `rankS'=r(rankS)

                }

****************************************************************
* Done with estimation blocks
****************************************************************

                mat colnames `b' = `cnb1'
                mat colnames `V' = `cnb1'
                mat rownames `V' = `cnb1'
                mat colnames `S' = `cnZ1'
                mat rownames `S' = `cnZ1'
* No W matrix for LIML or kclass
                capture mat colnames `W' = `cnZ1'
                capture mat rownames `W' = `cnZ1'

*====================================================================
* IVREGHDFE BLOCK
*====================================================================
* Store residuals if requested
if (`"`absorb'"' != "" & "`residuals'" != "") {
    mata: HDFE.solution.resid = st_data(., "`resid' `touse' `sortpreserve2'") // Load three vars: resid, sample dummy, and sort order
    mata: HDFE.solution.resid = sort(HDFE.solution.resid, 3) // sort matrix by sortorder
    mata: HDFE.solution.resid = select(HDFE.solution.resid[., 1], HDFE.solution.resid[., 2]) // keep first column, within sample
    * mata: HDFE.solution.resid = st_data(., "`resid'", "`touse'") // This would be the code if there was no preserve/sort    
}
*====================================================================


*******************************************************************************************
* RSS, counts, dofs, F-stat, small-sample corrections
*******************************************************************************************

// rankxx = rhs1_ct except if nocollin
// rankzz = iv1_ct except if nocollin
// nocollin means count may exceed rank (because of dropped vars), so rank #s foolproof
                scalar `rmse'=sqrt(`sigmasq')
                if "`noconstant'"=="" {
                        scalar `mss'=`yyc' - `rss'
                }
                else {
                        scalar `mss'=`yy' - `rss'
                }

                local Fdf1 = `rankxx' - `cons'
                local df_m = `rankxx' - `cons' + (`sdofminus'-`partialcons')

* Residual dof
                if "`cluster'"=="" {
* Use int(`N') because of non-integer N with iweights, and also because of
* possible numeric imprecision with N returned by above.
                        local df_r = int(`N') - `rankxx' - `dofminus' - `sdofminus'
                }
                else {
* To match Stata, subtract 1
                        local df_r = `N_clust' - 1
                }

* Sargan-Hansen J dof and p-value
* df=0 doesn't guarantee j=0 since can be call to get value of CUE obj fn
                local jdf = `rankzz' - `rankxx'
                if `jdf' == 0 & "`b0'"=="" {
                        scalar `j' = 0
                }
                else {
                        scalar `jp' = chiprob(`jdf',`j')
                }
                if "`liml'"~="" {
                        scalar `arubinp' = chiprob(`jdf',`arubin')
                        scalar `arubin_linp' = chiprob(`jdf',`arubin_lin')
                }

* Small sample corrections for var-cov matrix.
* If robust, the finite sample correction is N/(N-K), and with no small
* we change this to 1 (a la Davidson & MacKinnon 1993, p. 554, HC0).
* If cluster, the finite sample correction is (N-1)/(N-K)*M/(M-1), and with no small
* we change this to 1 (a la Wooldridge 2002, p. 193), where M=number of clusters.

                if "`small'" != "" {
                        if "`cluster'"=="" {
                                matrix `V'=`V'*(`N'-`dofminus')/(`N'-`rankxx'-`dofminus'-`sdofminus')
                        }
                        else {
                                matrix `V'=`V'*(`N'-1)/(`N'-`rankxx'-`sdofminus')               ///
                                                        * `N_clust'/(`N_clust'-1)
                        }
                        scalar `sigmasq'=`rss'/(`N'-`rankxx'-`dofminus'-`sdofminus')
                        scalar `rmse'=sqrt(`sigmasq')
                }

                scalar `r2u'=1-`rss'/`yy'
                scalar `r2c'=1-`rss'/`yyc'
                if "`noconstant'"=="" {
                        scalar `r2'=`r2c'
                        scalar `r2_a'=1-(1-`r2')*(`N'-1)/(`N'-`rankxx'-`dofminus'-`sdofminus')
                }
                else {
                        scalar `r2'=`r2u'
                        scalar `r2_a'=1-(1-`r2')*`N'/(`N'-`rankxx'-`dofminus'-`sdofminus')
                }
* `N' is rounded down to nearest integer if iweights are used.
* If aw, pw or fw, should already be integer but use round in case of numerical imprecision.
                local N=int(`N')

* Fstat
* To get it to match Stata's, must post separately with dofs and then do F stat by hand
*   in case weights generate non-integer obs and dofs
* Create copies so they can be posted
                tempname FB FV
                mat `FB'=`b'
                mat `FV'=`V'
                capture ereturn post `FB' `FV'
* If the cov matrix wasn't positive definite, the post fails with error code 506
                local rc = _rc
                if `rc' != 506 {
* Strip out omitted/base/etc. vars from RHS list
                        ivreg2_fvstrip `rhs1', dropomit
                        capture test `r(varlist)'
                        if "`small'" == "" {
                                if "`cluster'"=="" {
                                        capture scalar `F' = r(chi2)/`Fdf1' * `df_r'/(`N'-`dofminus')
                                }
                                else {
* sdofminus used here so that F-stat matches test stat from regression with no partial and small
                                        capture scalar `F' =    r(chi2)/`Fdf1' *                                        ///
                                                                                        (`N_clust'-1)/`N_clust' *                       ///
                                                                                        (`N'-`rankxx'-`sdofminus')/(`N'-1)
                                }
                        }
                        else {
                                capture scalar `F' = r(chi2)/`Fdf1'
                        }
                        capture scalar `Fp'=Ftail(`Fdf1',`df_r',`F')
                        capture scalar `Fdf2'=`df_r'
                }

* If j==. or vcv wasn't full rank, then vcv problems and F is meaningless
                if `j' == . | `rc'==506 {
                        scalar `F' = .
                        scalar `Fp' = .
                }

* End of counts, dofs, F-stat, small sample corrections

********************************************************************************************
* Reduced form and first stage regression options
*******************************************************************************************
* Relies on proper count of (non-collinear) IVs generated earlier.
* Note that nocons option + constant in instrument list means first-stage
* regressions are reported with nocons option.  First-stage F-stat therefore
* correctly includes the constant as an explanatory variable.

                if "`sfirst'`savesfirst'`rf'`saverf'`first'`ffirst'`savefirst'" != "" & (`endo1_ct' > 0) {

* Restore original order if changed for mata code above
                        capture tsset

                        local sdofmopt = "sdofminus(`sdofminus')"
// Need to create Stata placeholders for Mata code so that Stata time-series operators can work on them
// fres1 is Nx1
// endo1_hat is NxK1
// fsresall is Nx(K1+1) (used for full system)
                        tempname fsres1
                        qui gen double `fsres1'=.
                        local fsresall `fsres1'
                        foreach x of local fv_endo1 {
                                tempname fsres
                                qui gen double `fsres'=.
                                local fsresall "`fsresall' `fsres'"
                        }

// mata code requires sorting on cluster 3 / cluster 1 (if 2-way) or cluster 1 (if one-way)
                        if "`cluster'"!="" {
                                        sort `clusterid3' `cluster1'
                        }
                        mata: s_ffirst( "`ZZ'",                                                 ///
                                                        "`XX'",                                                 ///
                                                        "`XZ'",                                                 ///
                                                        "`ZY'",                                                 ///
                                                        "`ZZinv'",                                              ///
                                                        "`XXinv'",                                              ///
                                                        "`XPZXinv'",                                    ///
                                                        "`Z2Z2'",                                               ///
                                                        "`Z1Z2'",                                               ///
                                                        "`Z2y'",                                                ///
                                                        "`fsres1'",                                             /// Nx1
                                                        "`fsresall'",                                   /// Nx(K1+1)
                                                        "`fv_lhs1'",                                    ///
                                                        "`fv_endo1'",                                   ///
                                                        "`fv_inexog1' `ones'",                  ///
                                                        "`fv_exexog1'",                                 ///
                                                        "`touse'",                                              ///
                                                        "`weight'",                                             ///
                                                        "`wvar'",                                               ///
                                                        `wf',                                                   ///
                                                        `N',                                                    ///
                                                        `N_clust',                                              ///
                                                        "`robust'",                                             ///
                                                        "`clusterid1'",                                 ///
                                                        "`clusterid2'",                                 ///
                                                        "`clusterid3'",                                 ///
                                                        `bw',                                                   ///
                                                        "`kernel'",                                             ///
                                                        "`sw'",                                                 ///
                                                        "`psd'",                                                ///
                                                        "`ivar'",                                               ///
                                                        "`tvar'",                                               ///
                                                        "`tindex'",                                             ///
                                                        `tdelta',                                               ///
                                                        `center',                                               ///
                                                        `dofminus',                                             ///
                                                        `sdofminus')

                        tempname firstmat firstb firstv firsts
                        mat `firstmat' = r(firstmat)
                        mat rowname `firstmat' =        rmse sheapr2 pr2 F df df_r pvalue                       ///
                                                                                SWF SWFdf1 SWFdf2 SWFp SWchi2 SWchi2p SWr2      ///
                                                                                APF APFdf1 APFdf2 APFp APchi2 APchi2p APr2
                        mat colname `firstmat' = `endo1'
                        mat `firstb'    = r(b)
                        mat `firstv'    = r(V)
                        mat `firsts'    = r(S)
                        local archi2    =r(archi2)
                        local archi2p   =r(archi2p)
                        local arf               =r(arf)
                        local arfp              =r(arfp)
                        local ardf              =r(ardf)
                        local ardf_r    =r(ardf_r)
                        local sstat             =r(sstat)
                        local sstatdf   =r(sstatdf)
                        local sstatp    =r(sstatp)
                        local rmse_rf   =r(rmse_rf)
                        
* Restore original order if changed for mata code above
                        capture tsset
// System of first-stage/reduced form eqns
                        if "`sfirst'`savesfirst'" ~= "" {
                                PostFirstRF if `touse',                                 ///
                                                        bmat(`firstb')                          ///
                                                        vmat(`firstv')                          ///
                                                        smat(`firsts')                          ///
                                                        firstmat(`firstmat')            ///
                                                        lhs1(`lhs1')                            ///
                                                        endo1(`endo1')                          ///
                                                        znames0(`cnZ0')                         ///
                                                        znames1(`cnZ1')                         ///
                                                        bvclean(`bvclean')                      ///
                                                        fvops(`fvops')                          ///
                                                        partial_ct(`partial_ct')        ///
                                                        `robust'                                        ///
                                                        cluster(`cluster')                      ///
                                                        cluster1(`cluster1')            ///
                                                        cluster2(`cluster2')            ///
                                                        nc(`N_clust')                           ///
                                                        nc1(`N_clust1')                         ///
                                                        nc2(`N_clust2')                         ///
                                                        kernel(`kernel')                        ///
                                                        bw(`bw')                                        ///
                                                        ivar(`ivar')                            ///
                                                        tvar(`tvar')                            ///
                                                        obs(`N')                                        ///
                                                        iv1_ct(`iv1_ct')                        ///
                                                        cons(`cons')                            ///
                                                        partialcons(`partialcons')      ///
                                                        dofminus(`dofminus')            ///
                                                        sdofminus(`sdofminus')
                                local sfirsteq "`savesfprefix'sfirst_`lhs1'"
                                local sfirsteq : subinstr local sfirsteq "." "_"
                                capture est store `sfirsteq', title("System of first-stage/reduced form regressions")
                                if _rc > 0 {
di
di in ye "Unable to store system of first-stage reduced form regressions."
di
                                }
                        }

// RF regression
                        if "`rf'`saverf'" ~= "" {
                                PostFirstRF if `touse',                                 ///
                                                        rf                                                      /// extract RF regression as saved result
                                                        rmse_rf(`rmse_rf')                      /// provide RMSE for posting
                                                        bmat(`firstb')                          ///
                                                        vmat(`firstv')                          ///
                                                        smat(`firsts')                          ///
                                                        firstmat(`firstmat')            ///
                                                        lhs1(`lhs1')                            ///
                                                        endo1(`endo1')                          ///
                                                        znames0(`cnZ0')                         ///
                                                        znames1(`cnZ1')                         ///
                                                        bvclean(`bvclean')                      ///
                                                        fvops(`fvops')                          ///
                                                        partial_ct(`partial_ct')        ///
                                                        `robust'                                        ///
                                                        cluster(`cluster')                      ///
                                                        cluster1(`cluster1')            ///
                                                        cluster2(`cluster2')            ///
                                                        nc(`N_clust')                           ///
                                                        nc1(`N_clust1')                         ///
                                                        nc2(`N_clust2')                         ///
                                                        kernel(`kernel')                        ///
                                                        bw(`bw')                                        ///
                                                        ivar(`ivar')                            ///
                                                        tvar(`tvar')                            ///
                                                        obs(`N')                                        ///
                                                        iv1_ct(`iv1_ct')                        ///
                                                        cons(`cons')                            ///
                                                        partialcons(`partialcons')      ///
                                                        dofminus(`dofminus')            ///
                                                        sdofminus(`sdofminus')
                                local rfeq              "`saverfprefix'`lhs1'"
                                local rfeq              : subinstr local rfeq "." "_"
                                capture est store `rfeq', title("Reduced-form regression: `lhs'")
                                if _rc > 0 {
di
di in ye "Unable to store reduced form regression of `lhs1'."
di
                                }
                        }

// Individual first-stage equations
                        if "`first'`savefirst'" ~= "" {
                                foreach vn in `endo1' {
        
                                        PostFirstRF if `touse',                                 ///
                                                                first(`vn')                                     /// extract first-stage regression
                                                                bmat(`firstb')                          ///
                                                                vmat(`firstv')                          ///
                                                                smat(`firsts')                          ///
                                                                firstmat(`firstmat')            ///
                                                                lhs1(`lhs1')                            ///
                                                                endo1(`endo1')                          ///
                                                                znames0(`cnZ0')                         ///
                                                                znames1(`cnZ1')                         ///
                                                                bvclean(`bvclean')                      ///
                                                                fvops(`fvops')                          ///
                                                                partial_ct(`partial_ct')        ///
                                                                `robust'                                        ///
                                                                cluster(`cluster')                      ///
                                                                cluster1(`cluster1')            ///
                                                                cluster2(`cluster2')            ///
                                                                nc(`N_clust')                           ///
                                                                nc1(`N_clust1')                         ///
                                                                nc2(`N_clust2')                         ///
                                                                kernel(`kernel')                        ///
                                                                bw(`bw')                                        ///
                                                                ivar(`ivar')                            ///
                                                                tvar(`tvar')                            ///
                                                                obs(`N')                                        ///
                                                                iv1_ct(`iv1_ct')                        ///
                                                                cons(`cons')                            ///
                                                                partialcons(`partialcons')      ///
                                                                dofminus(`dofminus')            ///
                                                                sdofminus(`sdofminus')
                                        local eqname "`savefprefix'`vn'"
                                        local eqname : subinstr local eqname "." "_"
                                        capture est store `eqname', title("First-stage regression: `vn'")
                                        if _rc == 0 {
                                                local firsteqs "`firsteqs' `eqname'"
                                        }
                                        else {
di
di in ye "Unable to store first-stage regression of `vn'."
di
                                        }
                                }
                        }
                }
* End of RF and first-stage regression code

*******************************************************************************************
* Re-tsset if necessary
************************************************************************************************

                capture tsset

*******************************************************************************************
* orthog option: C statistic (difference of Sargan statistics)
*******************************************************************************************
* Requires j dof from above
                if "`orthog'"!="" {
                        tempname cj cstat cstatp
* Initialize cstat
                        scalar `cstat' = 0
* Remove orthog from inexog and put in endo
* Remove orthog from exexog
                        local cexexog1  : list fv_exexog1 - fv_orthog1
                        local cinexog1  : list fv_inexog1 - fv_orthog1
                        local cendo1    : list fv_inexog1 - cinexog1
                        local cendo1    `fv_endo1' `cendo1'
                        local clist_ct  : word count `orthog1'

* If robust, HAC/AC or GMM (but not LIML or IV), create optimal weighting matrix to pass to ivreg2
*   by extracting the submatrix from the full S and then inverting.
*   This guarantees the C stat will be non-negative.  See Hayashi (2000), p. 220. 
* Calculate C statistic with recursive call to ivreg2
* Collinearities may cause problems, hence -capture-.
* smatrix works generally, including homoskedastic case with Sargan stat
                        capture _estimates hold `ivest', restore
                        if _rc==1000 {
di as err "ivreg2 internal error - no room to save temporary estimation results"
di as err "Please drop one or more estimation results using -estimates drop-"
                                exit 1000
                        }
* clopt is omitted because it requires calculation of numbers of clusters, which is done
* only when S matrix is calculated
* S matrix has final varnames, but need to call ivreg2 with temp vars
* so must rename cols/rows of S
                        tempname fv_S
                        mat `fv_S'=`S'
                        if `cons' {
                                mat colnames `fv_S' = `fv_exexog1' `fv_inexog1' _cons
                                mat rownames `fv_S' = `fv_exexog1' `fv_inexog1' _cons
                        }
                        else {
                                mat colnames `fv_S' =  `fv_exexog1' `fv_inexog1'
                                mat rownames `fv_S' =  `fv_exexog1' `fv_inexog1'
                        }
                        capture `ivreg2cmd'             `fv_lhs1'                               ///
                                                                        `cinexog1'                              ///
                                                                        (`cendo1'=`cexexog1')   ///
                                                                        if `touse'                              ///
                                                                        `wtexp',                                ///
                                                                        `noconstant'                    ///
                                                                        `options'                               ///
                                                                        `small'                                 ///
                                                                        `robust'                                ///
                                                                        `gmm2s'                                 ///
                                                                        `bwopt'                                 ///
                                                                        `kernopt'                               ///
                                                                        `dofmopt'                               ///
                                                                        `sw'                                    ///
                                                                        `psd'                                   ///
                                                                        smatrix("`fv_S'")               ///
                                                                        noid                                    ///
                                                                        nocollin
                        local rc = _rc
                        if `rc' == 481 {
                                scalar `cstat' = 0
                                local cstatdf = 0
                        }
                        else {
                                scalar `cj'=e(j)
                                local cjdf=e(jdf)
                                scalar `cstat' = `j' - `cj'
                                local cstatdf  = `jdf' - `cjdf'
                        }
                        _estimates unhold `ivest'
                        scalar `cstatp'= chiprob(`cstatdf',`cstat')
* Collinearities may cause C-stat dof to differ from the number of variables in orthog()
* If so, set cstat=0
                        if `cstatdf' != `clist_ct' {
                                scalar `cstat' = 0
                        }
                }
* End of orthog block

*******************************************************************************************
* Endog option
*******************************************************************************************
* Uses recursive call with orthog
                if "`endogtest'"!="" {
                        tempname estat estatp
* Initialize estat
                        scalar `estat' = 0
* Remove endogtest vars from endo and put in inexog
                        local eendo1    : list fv_endo1 - fv_endogtest1
                        local einexog1  `fv_inexog1' `fv_endogtest1'
                        local elist_ct  : word count `endogtest1'

* Recursive call to ivreg2 using orthog option to obtain endogeneity test statistic
* Collinearities may cause problems, hence -capture-.
                        capture {
                                capture _estimates hold `ivest', restore
                                if _rc==1000 {
di as err "ivreg2 internal error - no room to save temporary estimation results"
di as err "Please drop one or more estimation results using -estimates drop-"
                                        exit 1000
                                }
                                capture `ivreg2cmd'             `fv_lhs1'                               ///
                                                                                `einexog1'                              ///
                                                                                (`eendo1'=`fv_exexog1') ///
                                                                                if `touse'                              ///
                                                                                `wtexp',                                ///
                                                                                `noconstant'                    ///
                                                                                `robust'                                ///
                                                                                `clopt'                                 ///
                                                                                `gmm2s'                                 ///
                                                                                `liml'                                  ///
                                                                                `bwopt'                                 ///
                                                                                `kernopt'                               ///
                                                                                `small'                                 ///
                                                                                `dofmopt'                               ///
                                                                                `sw'                                    ///
                                                                                `psd'                                   ///
                                                                                `options'                               ///
                                                                                orthog(`fv_endogtest1') ///
                                                                                noid                                    ///
                                                                                nocollin
                                local rc = _rc
                                if `rc' == 481 {
                                        scalar `estat' = 0
                                        local estatdf = 0
                                        }
                                else {
                                        scalar `estat'=e(cstat)
                                        local  estatdf=e(cstatdf)
                                        scalar `estatp'=e(cstatp)
                                }
                                _estimates unhold `ivest'
* Collinearities may cause endog stat dof to differ from the number of variables in endog()
* If so, set estat=0
                                if `estatdf' != `elist_ct' {
                                        scalar `estat' = 0
                                }
                        }
* End of endogeneity test block
                }

*******************************************************************************************
* Rank identification and redundancy block
*******************************************************************************************
                if `endo1_ct' > 0 & "`noid'"=="" {

// id=underidentification statistic, wid=weak identification statistic
                        tempname idrkstat widrkstat iddf idp
                        tempname ccf cdf rkf cceval cdeval cd
                        tempname idstat widstat

// UNDERIDENTIFICATION
// Anderson canon corr underidentification statistic if homo, rk stat if not
// Need only id stat for testing full rank=(#cols-1)
// ranktest can exit with error if not full rank
// May not exit with error if e.g. ranktest (x y) (x w),
// i.e. collinearity across lists, so need to catch that.
// If no collinearity, can use iv1_ct and rhs1_ct etc.
                        cap `ranktestcmd'                                                       ///
                                                                (`fv_endo1')                    ///
                                                                (`fv_exexog1')                  ///
                                                                `wtexp'                                 ///
                                                                 if `touse',                    ///
                                                                 partial(`fv_inexog1')  ///
                                                                 full                                   ///
                                                                 `noconstant'                   ///
                                                                 `robust'                               ///
                                                                 `clopt'                                ///
                                                                 `bwopt'                                ///
                                                                 `kernopt'
// Returned in e(.) macro:
                        local rkcmd `r(ranktestcmd)'

// Canonical correlations returned in r(ccorr), sorted in descending order.
// If largest = 1, collinearities so enter error block.
                        local rkerror           = _rc>0 | r(chi2)==.
                        if ~`rkerror' {
                                local rkerror   = el(r(ccorr),1,1)==1
                        }
                        if `rkerror' {
di as err "warning: -ranktest- error in calculating underidentification test statistics;"
di as err "         may be caused by collinearities"
                                scalar `idstat' = .
                                local iddf              = .
                                scalar `idp'    = .
                                scalar `cd'             = .
                                scalar `cdf'    = .
                        }
                        else {
                                if "`cluster'"=="" {
                                        scalar `idstat'=r(chi2)/r(N)*(`N'-`dofminus')
                                }
                                else {
// No dofminus adjustment needed for cluster-robust
                                        scalar `idstat'=r(chi2)
                                }
                                mat `cceval'=r(ccorr)
                                mat `cdeval' = J(1,`endo1_ct',.)
                                forval i=1/`endo1_ct' {
                                        mat `cceval'[1,`i'] = (`cceval'[1,`i'])^2
                                        mat `cdeval'[1,`i'] = `cceval'[1,`i'] / (1 - `cceval'[1,`i'])
                                }
                                local iddf = `iv1_ct' - (`rhs1_ct'-1)
                                scalar `idp' = chiprob(`iddf',`idstat')
// Cragg-Donald F statistic.
// Under homoskedasticity, Wald cd eigenvalue = cc/(1-cc) Anderson canon corr eigenvalue.
                                scalar `cd'=`cdeval'[1,`endo1_ct']
                                scalar `cdf'=`cd'*(`N'-`sdofminus'-`iv1_ct'-`dofminus')/`exex1_ct'
                        }       // end underidentification stat

// WEAK IDENTIFICATION
// Weak id statistic is Cragg-Donald F stat, rk Wald F stat if not
// ranktest exits with error if not full rank so can use iv1_ct and rhs1_ct etc.
                        if "`robust'`cluster'`kernel'"=="" {
                                scalar `widstat'=`cdf'
                        }
                        else {
// Need only test of full rank
                                cap `ranktestcmd'                                               ///
                                                                (`fv_endo1')                    ///
                                                                (`fv_exexog1')                  ///
                                                                `wtexp'                                 ///
                                                                if `touse',                             ///
                                                                partial(`fv_inexog1')   ///
                                                                full                                    ///
                                                                wald                                    ///
                                                                `noconstant'                    ///
                                                                `robust'                                ///
                                                                `clopt'                                 ///
                                                                `bwopt'                                 ///
                                                                `kernopt'
// Canonical correlations returned in r(ccorr), sorted in descending order.
// If largest = 1, collinearities so enter error block.
                                local rkerror           = _rc>0 | r(chi2)==.
                                if ~`rkerror' {
                                        local rkerror   = el(r(ccorr),1,1)==1
                                }
                                if `rkerror' {
di as err "warning: -ranktest- error in calculating weak identification test statistics;"
di as err "         may be caused by collinearities"
                                        scalar `rkf'            = .
                                        scalar `widstat'        = .
                                }
                                else {
// sdofminus used here so that F-stat matches test stat from regression with no partial
                                        if "`cluster'"=="" {
                                                scalar `rkf'=r(chi2)/r(N)*(`N'-`iv1_ct'-`sdofminus'-`dofminus')/`exex1_ct'
                                        }
                                        else {
                                                scalar `rkf' =  r(chi2)/(`N'-1) *                               ///
                                                                                (`N'-`iv1_ct'-`sdofminus') *    ///
                                                                                (`N_clust'-1)/`N_clust' /               ///
                                                                                `exex1_ct'
                                        }
                                        scalar `widstat'=`rkf'
                                }
                        }       // end weak-identification stat
                }       // end under- and weak-identification stats

* LM redundancy test
                if `endo1_ct' > 0 & "`redundant'" ~= "" & "`noid'"=="" {
* Use K-P rk statistics and LM version of test
* Statistic is the rank of the matrix of Z_1B*X_2, where Z_1B are the possibly redundant
* instruments and X_1 are the endogenous regressors; both have X_2 (exogenous regressors)
* and Z_1A (maintained excluded instruments) partialled out.  LM test of rank is
* is numerically equivalent to estimation of set of RF regressions and performing
* standard LM test of possibly redundant instruments.

                        local rexexog1          : list fv_exexog1 - fv_redundant1
                        local redlist_ct        : word count `redundant1'
* LM version requires only -nullrank- rk statistics so would not need -all- option
                        tempname rkmatrix
                        qui `ranktestcmd'                                                                               ///
                                                                (`fv_endo1')                                            ///
                                                                (`fv_redundant1')                                       ///
                                                                `wtexp'                                                         ///
                                                                if `touse',                                                     ///
                                                                partial(`fv_inexog1' `rexexog1')        ///
                                                                null                                                            ///
                                                                `noconstant'                                            ///
                                                                `robust'                                                        ///
                                                                `clopt'                                                         ///
                                                                `bwopt'                                                         ///
                                                                `kernopt'
                        mat `rkmatrix'=r(rkmatrix)
                        tempname redstat redp
* dof adjustment needed because it doesn't use the adjusted S
                        if "`cluster'"=="" {
                                scalar `redstat' = `rkmatrix'[1,1]/r(N)*(`N'-`dofminus')
                        }
                        else {
* No dofminus adjustment needed for cluster-robust
                                scalar `redstat' = `rkmatrix'[1,1]
                        }
                        local reddf = `endo1_ct'*`redlist_ct'
                        scalar `redp' = chiprob(`reddf',`redstat')
                }

* End of identification stats block

*******************************************************************************************
* Error-checking block
*******************************************************************************************

* Check if adequate number of observations
                if `N' <= `iv1_ct' {
di in r "Error: number of observations must be greater than number of instruments"
di in r "       including constant."
                        error 2001
                }

* Check if robust VCV matrix is of full rank
                if ("`gmm2s'`robust'`cluster'`kernel'" != "") & (`rankS' < `iv1_ct') {
* Robust covariance matrix not of full rank means either a singleton dummy or too few
*   clusters (in which case the indiv SEs are OK but no F stat or 2-step GMM is possible),
*   or there are too many AC/HAC-lags, or the HAC covariance estimator
*   isn't positive definite (possible with truncated and Tukey-Hanning kernels)
*   or nocollin option has been used.
* Previous versions of ivreg2 exited if 2-step GMM but beta and VCV may be OK.
* Continue but J, F, and C stat (if present) all possibly meaningless.
* Set j = missing so that problem can be reported in output.
                        scalar `j' = .
                        if "`orthog'"!="" {
                                scalar `cstat' = .
                        }
                        if "`endogtest'"!="" {
                                scalar `estat' = .
                        }
                }

* End of error-checking block

**********************************************************************************************
* Post and display results.
*******************************************************************************************

// rankV = rhs1_ct except if nocollin
// rankS = iv1_ct except if nocollin
// nocollin means count may exceed rank (because of dropped vars), so rank #s foolproof

// Add back in omitted vars from "0" varlists unless bvclean requested
// or unless there are no omitted regressors that need adding back in.
                if ~`bvclean' & (`rhs0_ct' > `rhs1_ct') {
                        AddOmitted, bmat(`b') vmat(`V') cnb0(`cnb0') cnb1(`cnb1')
                        mat `b' = r(b)
                        mat `V' = r(V)
// build fv info (base, empty, etc.) unless there was partialling out
                        if `fvops' & ~`partial_ct' {
                                local bfv "buildfvinfo"
                        }
                }

*******************************************************************************************

// restore data if preserved for partial option
                if (`partial_ct' | "`absorb'"!="") {
                        restore
                }

                if "`small'"!="" {
                        local NminusK = `N'-`rankxx'-`sdofminus'
                        capture ereturn post `b' `V', dep(`depname') obs(`N') esample(`touse') dof(`NminusK') `bfv'
                }
                else {
                        capture ereturn post `b' `V', dep(`depname') obs(`N') esample(`touse') `bfv'
                }

                local rc = _rc
                if `rc' == 504 {
di in red "Error: estimated variance-covariance matrix has missing values"
                        exit 504
                }
                if `rc' == 506 {
di in red "Error: estimated variance-covariance matrix not positive-definite"
                        exit 506
                }
                if `rc' > 0 {
di in red "Error: estimation failed - could not post estimation results"
                        exit `rc'
                }

                local mok       =1                                                                                                      //  default - margins OK
                * ivreghdfe 1.1.1: Override to enable -margins-; dangerous
                *local mok       = `mok' & ~`partial_ct'                                                         //  but not if partialling out
                *local mok       = `mok' & ~(`fvops' & `bvclean')                                        //  nor if there are FVs and the base vars are not in e(b)
                if `mok' & `endo1_ct' {                                                                                 //  margins can be used, endog regressors
                        ereturn local marginsnotok      "Residuals SCores"                              //  same as official -ivregress-
                        ereturn local marginsok         "XB default"
                }
                else if `mok' & ~`endo1_ct' {                                                                   //  margins can be used, no endog regressors
                        ereturn local marginsok         "XB default"                                    //  same as official -regress'
                }
                else {                                                                                                                  //  don't allow margins
                        ereturn local marginsnotok      "Residuals SCores XB default"
                }

// Original varlists without removed duplicates, collinears, etc.
// "0" varlists after removing duplicates and reclassifying vars, and including omitteds, FV base vars, etc.
// "1" varlists without omitted, FV base vars, and partialled-out vars
                ereturn local ecollin   `ecollin'
                ereturn local collin    `collin'
                ereturn local dups              `dups'
                ereturn local partial1  `partial1'
                ereturn local partial   `partial'
                ereturn local inexog1   `inexog1'
                ereturn local inexog0   `inexog0'
                ereturn local inexog    `inexog'
                ereturn local exexog1   `exexog1'
                ereturn local exexog0   `exexog0'
                ereturn local exexog    `exexog'
                ereturn local insts1    `exexog1' `inexog1'
                ereturn local insts0    `exexog0' `inexog0'
                ereturn local insts     `exexog' `inexog'
                ereturn local instd1    `endo1'
                ereturn local instd0    `endo0'
                ereturn local instd             `endo'
                ereturn local depvar1   `lhs1'
                ereturn local depvar0   `lhs0'
                ereturn local depvar    `lhs'

                ereturn scalar inexog_ct        =`inexog1_ct'
                ereturn scalar exexog_ct        =`exex1_ct'
                ereturn scalar endog_ct         =`endo1_ct'
                ereturn scalar partial_ct       =`partial_ct'

                if "`smatrix'" == "" {
                        ereturn matrix S `S'
                }
                else {
                        ereturn matrix S `S0'                                   //  it's a copy so original won't be zapped
                }

* No weighting matrix defined for LIML and kclass
                if "`wmatrix'"=="" & "`liml'`kclassopt'"=="" {
                        ereturn matrix W `W'
                }
                else if "`liml'`kclassopt'"=="" {
                        ereturn matrix W `wmatrix'                              //  it's a copy so original won't be zapped
                }

                if "`kernel'"!="" {
                        ereturn local kernel "`kernel'"
                        ereturn scalar bw=`bw'
                        ereturn local tvar "`tvar'"
                        if "`ivar'" ~= "" {
                                ereturn local ivar "`ivar'"
                        }
                        if "`bwchoice'" ~= "" {
                                ereturn local bwchoice "`bwchoice'"
                        }
                }

                if "`small'"!="" {
                        ereturn scalar df_r=`df_r'
                        ereturn local small "small"
                }
                if "`nopartialsmall'"=="" {
                        ereturn local partialsmall "small"
                }

                
                if "`robust'" != "" {
                        local vce "robust"
                }
                if "`cluster1'" != "" {
                        if "`cluster2'"=="" {
                                local vce "`vce' cluster"
                        }
                        else {
                                local vce "`vce' two-way cluster"
                        }
                }
                if "`kernel'" != "" {
                        if "`robust'" != "" {
                                local vce "`vce' hac"
                        }
                        else {
                                local vce "`vce' ac"
                        }
                        local vce "`vce' `kernel' bw=`bw'"
                }
                if "`sw'" != "" {
                        local vce "`vce' sw"
                }
                if "`psd'" != "" {
                        local vce "`vce' `psd'"
                }
                local vce : list clean vce
                local vce = lower("`vce'")
                ereturn local vce `vce'

                if "`cluster'"!="" {
                        ereturn scalar N_clust=`N_clust'
                        ereturn local clustvar `cluster'
                }
                if "`cluster2'"!="" {
                        ereturn scalar N_clust1=`N_clust1'
                        ereturn scalar N_clust2=`N_clust2'
                        ereturn local clustvar1 `cluster1'
                        ereturn local clustvar2 `cluster2'
                }

                if "`robust'`cluster'" != "" {
                        ereturn local vcetype "Robust"
                }

                ereturn scalar df_m=`df_m'
                ereturn scalar sdofminus=`sdofminus'
                ereturn scalar dofminus=`dofminus'
                ereturn scalar center=`center'
                ereturn scalar r2=`r2'
                ereturn scalar rmse=`rmse'
                ereturn scalar rss=`rss'
                ereturn scalar mss=`mss'
                ereturn scalar r2_a=`r2_a'
                ereturn scalar F=`F'
                ereturn scalar Fp=`Fp'
                ereturn scalar Fdf1=`Fdf1'
                ereturn scalar Fdf2=`Fdf2'
                ereturn scalar yy=`yy'
                ereturn scalar yyc=`yyc'
                ereturn scalar r2u=`r2u'
                ereturn scalar r2c=`r2c'
                ereturn scalar condzz=`condzz'
                ereturn scalar condxx=`condxx'
                ereturn scalar rankzz=`rankzz'
                ereturn scalar rankxx=`rankxx'
                ereturn scalar rankS=`rankS'
                ereturn scalar rankV=`rankV'
                ereturn scalar ll = -0.5 * (`N'*ln(2*_pi) + `N'*ln(`rss'/`N') + `N')

* Always save J.  Also save as Sargan if homoskedastic; save A-R if LIML.
                ereturn scalar j=`j'
                ereturn scalar jdf=`jdf'
                if `j' != 0 & `j' != . {
                        ereturn scalar jp=`jp'
                }
                if ("`robust'`cluster'"=="") {
                        ereturn scalar sargan=`j'
                        ereturn scalar sargandf=`jdf'
                        if `j' != 0  & `j' != . {
                                ereturn scalar sarganp=`jp'
                        }
                }
                if "`liml'"!="" {
                        ereturn scalar arubin=`arubin'
                        ereturn scalar arubin_lin=`arubin_lin'
                        if `j' != 0  & `j' != . {
                                ereturn scalar arubinp=`arubinp'
                                ereturn scalar arubin_linp=`arubin_linp'
                        }
                        ereturn scalar arubindf=`jdf'
                }

                if "`orthog'"!="" {
                        ereturn scalar cstat=`cstat'
                        if `cstat'!=0  & `cstat' != . {
                                ereturn scalar cstatp=`cstatp'
                                ereturn scalar cstatdf=`cstatdf'
                                ereturn local clist `orthog1'
                        }
                }

                if "`endogtest'"!="" {
                        ereturn scalar estat=`estat'
                        if `estat'!=0  & `estat' != . {
                                ereturn scalar estatp=`estatp'
                                ereturn scalar estatdf=`estatdf'
                                ereturn local elist `endogtest1'
                        }
                }

                if `endo1_ct' > 0 & "`noid'"=="" {
                        ereturn scalar idstat=`idstat'
                        ereturn scalar iddf=`iddf'
                        ereturn scalar idp=`idp'
                        ereturn scalar cd=`cd'
                        ereturn scalar widstat=`widstat'
                        ereturn scalar cdf=`cdf'
                        capture ereturn matrix ccev=`cceval'
                        capture ereturn matrix cdev `cdeval'
                        capture ereturn scalar rkf=`rkf'
                }

                if "`redundant'"!="" & "`noid'"=="" {
                        ereturn scalar redstat=`redstat'
                        ereturn scalar redp=`redp'
                        ereturn scalar reddf=`reddf'
                        ereturn local  redlist `redundant1'
                }

                if "`first'`ffirst'`savefirst'`sfirst'`savesfirst'" != "" & `endo1_ct'>0 {
// Capture here because firstmat may be empty if mvs encountered in 1st stage regressions
                        capture ereturn matrix first `firstmat'
                        ereturn scalar  arf=`arf'
                        ereturn scalar  arfp=`arfp'
                        ereturn scalar  archi2=`archi2'
                        ereturn scalar  archi2p=`archi2p'
                        ereturn scalar  ardf=`ardf'
                        ereturn scalar  ardf_r=`ardf_r'
                        ereturn scalar  sstat=`sstat'
                        ereturn scalar  sstatp=`sstatp'
                        ereturn scalar  sstatdf=`sstatdf'
                }
// not saved if empty
                ereturn local   firsteqs `firsteqs'
                ereturn local   rfeq `rfeq'
                ereturn local   sfirsteq `sfirsteq'

                if "`liml'"!="" {
                        ereturn local model "liml"
                        ereturn scalar kclass=`kclass'
                        ereturn scalar lambda=`lambda'
                        if `fuller' > 0 & `fuller' < . {
                                ereturn scalar fuller=`fuller'
                        }
                }
                else if "`kclassopt'" != "" {
                        ereturn local model "kclass"
                        ereturn scalar kclass=`kclass'
                }
                else if "`gmm2s'`cue'`b0'`wmatrix'"=="" {
                        if "`endo1'" == "" {
                                ereturn local model "ols"
                        }
                        else {
                                ereturn local model "iv"
                        }
                }
                else if "`cue'`b0'"~="" {
                                ereturn local model "cue"
                        }
                else if "`gmm2s'"~="" {
                        ereturn local model "gmm2s"
                }
                else if "`wmatrix'"~="" {
                                ereturn local model "gmmw"
                }
                else {
* Should never enter here
                        ereturn local model "unknown"
                }

                if "`weight'" != "" { 
                        ereturn local wexp "=`exp'"
                        ereturn local wtype `weight'
                }
                ereturn local cmd                       `ivreg2cmd'
                ereturn local ranktestcmd       `rkcmd'
                ereturn local version           `lversion'
                ereturn scalar nocollin         =("`nocollin'"~="")
                ereturn scalar partialcons      =`partialcons'
                ereturn scalar cons                     =`cons'

                ereturn local predict "`ivreg2cmd'_p"
                
                if "`e(model)'"=="gmm2s" & "`wmatrix'"=="" {
                        local title2 "2-Step GMM estimation"
                }
                else if "`e(model)'"=="gmm2s" & "`wmatrix'"~="" {
                        local title2 "2-Step GMM estimation with user-supplied first-step weighting matrix"
                }
                else if "`e(model)'"=="gmmw" {
                        local title2 "GMM estimation with user-supplied weighting matrix"
                }
                else if "`e(model)'"=="cue" & "`b0'"=="" {
                        local title2 "CUE estimation"
                }
                else if "`e(model)'"=="cue" & "`b0'"~="" {
                        local title2 "CUE evaluated at user-supplied parameter vector"
                }
                else if "`e(model)'"=="ols" {
                        local title2 "OLS estimation"
                }
                else if "`e(model)'"=="iv" {
                        local title2 "IV (2SLS) estimation"
                }
                else if "`e(model)'"=="liml" {
                        local title2 "LIML estimation"
                }
                else if "`e(model)'"=="kclass" {
                        local title2 "k-class estimation"
                }
                else {
* Should never reach here
                        local title2 "unknown estimation"
                }
                if "`e(vcetype)'" == "Robust" {
                        local hacsubtitle1 "heteroskedasticity"
                }
                if "`e(kernel)'"!="" & "`e(clustvar)'"=="" {
                        local hacsubtitle3 "autocorrelation"
                }
                if "`kiefer'"!="" {
                        local hacsubtitle3 "within-cluster autocorrelation (Kiefer)"
                }
                if "`e(clustvar)'"!="" {
                        if "`e(clustvar2)'"=="" {
                                local hacsubtitle3 "clustering on `e(clustvar)'"
                        }
                        else {
                                local hacsubtitle3 "clustering on `e(clustvar1)' and `e(clustvar2)'"
                        }
                        if "`e(kernel)'" != "" {
                                local hacsubtitle4 "and kernel-robust to common correlated disturbances (Driscoll-Kraay)"
                        }
                }
                if "`hacsubtitle1'"~="" & "`hacsubtitle3'" ~= "" {
                        local hacsubtitle2 " and "
                }
                if "`title'"=="" {
                        ereturn local title "`title1'`title2'"
                }
                else {
                        ereturn local title "`title'"
                }
                if "`subtitle'"~="" {
                        ereturn local subtitle "`subtitle'"
                }
                local hacsubtitle "`hacsubtitle1'`hacsubtitle2'`hacsubtitle3'"
                if "`b0'"~="" {
                        ereturn local hacsubtitleB "Estimates based on supplied parameter vector"
                }
                else if "`hacsubtitle'"~="" & "`gmm2s'`cue'"~="" {
                        ereturn local hacsubtitleB "Estimates efficient for arbitrary `hacsubtitle'"
                }
                else if "`wmatrix'"~="" {
                        ereturn local hacsubtitleB "Efficiency of estimates dependent on weighting matrix"
                }
                else {
                        ereturn local hacsubtitleB "Estimates efficient for homoskedasticity only"
                }
                if "`hacsubtitle'"~="" {
                        ereturn local hacsubtitleV "Statistics robust to `hacsubtitle'"
                }
                else {
                        ereturn local hacsubtitleV "Statistics consistent for homoskedasticity only"
                }
                if "`hacsubtitle4'"~="" {
                        ereturn local hacsubtitleV2 "`hacsubtitle4'"
                }
                if "`sw'"~="" {
                        ereturn local hacsubtitleV "Stock-Watson heteroskedastic-robust statistics (BETA VERSION)"
                }

                if ("`absorb'" != "") {
                    mata: HDFE.post_footnote()
                    assert e(N_hdfe) != .

                    if ("`residuals'" != "") {
                        mata: HDFE.save_variable("`residuals'", HDFE.solution.resid, "Residuals") // do we need hdfe_residuals if we have HDFE.solution.resid ?
                        mata: st_global("e(resid)", "`residuals'")
                        reghdfe, store_alphas
                    }
                }
        }

*******************************************************************************************
* Display results unless ivreg2 called just to generate stats or nooutput option

        if "`nooutput'" == "" {
        
// Display supplementary first-stage/RF results
                if "`savesfirst'`saverf'`savefirst'" != "" {
                        DispStored `"`savesfirst'"' `"`saverf'"' `"`savefirst'"'
                }
                if "`rf'" != "" {
                        local eqname "`e(rfeq)'"
                        tempname ivest
                        _estimates hold `ivest', copy
                        capture estimates restore `eqname'
                        if _rc != 0 {
di
di in ye "Unable to display stored reduced form estimation."
di
                        }
                        else {
                                DispSFirst "rf" `"`plus'"' `"`level'"' `"`nofooter'"' `"`ivreg2name'"' "`dispopt'"
                        }
                        _estimates unhold `ivest'
                }
                if "`first'" != "" {
                        DispFirst `"`ivreg2name'"'
                }
                if "`sfirst'"!="" {
                        local eqname "`e(sfirsteq)'"
                        tempname ivest
                        _estimates hold `ivest', copy
                        capture estimates restore `eqname'
                        if _rc != 0 {
di
di in ye "Unable to display stored first-stage/reduced form estimations."
di
                        }
                        else {
                                DispSFirst "sfirst" `"`plus'"' `"`level'"' `"`nofooter'"' `"`ivreg2name'"' "`dispopt'"
                        }
                        _estimates unhold `ivest'
                }
                if "`first'`ffirst'`sfirst'" != "" {
                        DispFFirst `"`ivreg2name'"'
                }

// Display main output.  Can be standard ivreg2, or first-stage-type results
                if "`e(model)'"=="first" | "`e(model)'"=="rf" | "`e(model)'"=="sfirst" {
                        DispSFirst "`e(model)'" `"`plus'"' `"`level'"' `"`nofooter'"' `"`ivreg2name'"' "`dispopt'"
                }
                else {
                        DispMain `"`noheader'"' `"`plus'"' `"`level'"' `"`nofooter'"' `"`ivreg2name'"' "`dispopt'"
                }
        }

// Drop first stage estimations unless explicitly saved or if replay
        if "`savefirst'" == "" {
                local firsteqs "`e(firsteqs)'"
                foreach eqname of local firsteqs {
                        capture estimates drop `eqname'
                }
                ereturn local firsteqs
        }
// Drop reduced form estimation unless explicitly saved or if replay
        if "`saverf'" == "" {
                local eqname "`e(rfeq)'"
                capture estimates drop `eqname'
                ereturn local rfeq
        }
// Drop first stage/reduced form estimation unless explicitly saved or if replay
        if "`savesfirst'" == "" {
                local eqname "`e(sfirsteq)'"
                capture estimates drop `eqname'
                ereturn local sfirsteq
        }

end

*******************************************************************************************
* SUBROUTINES
*******************************************************************************************

// ************* Display system of or single first-stage and/or RF estimations ************ //

program define DispSFirst, eclass
        args model plus level nofooter helpfile dispopt
        version 11.2

di
        if "`model'"=="first" {
di in gr "First-stage regression of `e(depvar)':"
        }
        else if "`model'"=="rf" {
                local strlen = length("`e(depvar)'")+25
di in gr "Reduced-form regression: `e(depvar)'"
di in smcl in gr "{hline `strlen'}"
        }
        else if "`model'"=="sfirst" {
di in gr "System of first-stage/reduced-form regressions:"
di in smcl in gr "{hline 47}"
        }

// Display coefficients etc.
// Header info
        if "`e(hacsubtitleV)'" ~= "" {
di in gr _n "`e(hacsubtitleV)'"
        }
        if "`e(hacsubtitleV2)'" ~= "" {
di in gr "`e(hacsubtitleV2)'"
        }
di in gr "Number of obs = " _col(31) in ye %8.0f e(N)
        if "`e(kernel)'"!="" {
di in gr "  kernel=`e(kernel)'; bandwidth=" `e(bw)'
                if "`e(bwchoice)'"!="" {
di in gr "  `e(bwchoice)'"
                }
di in gr "  time variable (t):  " in ye e(tvar)
                if "`e(ivar)'" != "" {
di in gr "  group variable (i): " in ye e(ivar)
                }
        }
        if "`e(clustvar)'"!="" {
                if "`e(clustvar2)'"=="" {
                        local N_clust `e(N_clust)'
                        local clustvar `e(clustvar)'
                }
                else {
                        local N_clust `e(N_clust1)'
                        local clustvar `e(clustvar1)'
                }
di in gr "Number of clusters (`clustvar') = " _col(33) in ye %6.0f `N_clust'
        }
        if "`e(clustvar2)'"!="" {
di in gr "Number of clusters (" "`e(clustvar2)'" ") = " _col(33) in ye %6.0f e(N_clust2)
        }

// Unfortunate but necessary hack here: to suppress message about cluster adjustment of
//   standard error, clear e(clustvar) and then reset it after display
        local cluster `e(clustvar)'
        ereturn local clustvar

// Display output
        ereturn display, `plus' level(`level') `dispopt'
        ereturn local clustvar `cluster'

end

// ************* Display main estimation outpout ************** //

program define DispMain, rclass
        args noheader plus level nofooter helpfile dispopt
        version 11.2
* Prepare for problem resulting from rank(S) being insufficient
* Results from insuff number of clusters, too many lags in HAC,
*   to calculate robust S matrix, HAC matrix not PD, singleton dummy,
*   and indicated by missing value for j stat
* Macro `rprob' is either 1 (problem) or 0 (no problem)
        capture local rprob ("`e(j)'"==".")

        if "`noheader'"=="" {
                if "`e(title)'" ~= "" {
di in gr _n "`e(title)'"
                        local tlen=length("`e(title)'")
di in gr "{hline `tlen'}"
                }
                if "`e(subtitle)'" ~= "" {
di in gr "`e(subtitle)'"
                }
                if "`e(model)'"=="liml" | "`e(model)'"=="kclass" {
di in gr "k               =" %7.5f `e(kclass)'
                }
                if "`e(model)'"=="liml" {
di in gr "lambda          =" %7.5f `e(lambda)'
                }
                if e(fuller) > 0 & e(fuller) < . {
di in gr "Fuller parameter=" %-5.0f `e(fuller)'
                }
                if "`e(hacsubtitleB)'" ~= "" {
di in gr _n "`e(hacsubtitleB)'" _c
                }
                if "`e(hacsubtitleV)'" ~= "" {
di in gr _n "`e(hacsubtitleV)'"
                }
                if "`e(hacsubtitleV2)'" ~= "" {
di in gr "`e(hacsubtitleV2)'"
                }
                if "`e(kernel)'"!="" {
di in gr "  kernel=`e(kernel)'; bandwidth=" `e(bw)'
                        if "`e(bwchoice)'"!="" {
di in gr "  `e(bwchoice)'"
                        }
di in gr "  time variable (t):  " in ye e(tvar)
                        if "`e(ivar)'" != "" {
di in gr "  group variable (i): " in ye e(ivar)
                        }
                }
                di
                if "`e(clustvar)'"!="" {
                        if "`e(clustvar2)'"=="" {
                                local N_clust `e(N_clust)'
                                local clustvar `e(clustvar)'
                        }
                        else {
                                local N_clust `e(N_clust1)'
                                local clustvar `e(clustvar1)'
                        }
di in gr "Number of clusters (`clustvar') = " _col(33) in ye %6.0f `N_clust' _continue
                }
di in gr _col(55) "Number of obs = " in ye %8.0f e(N)
                if "`e(clustvar2)'"!="" {
di in gr "Number of clusters (" "`e(clustvar2)'" ") = " _col(33) in ye %6.0f e(N_clust2) _continue
                }
di in gr _c _col(55) "F(" %3.0f e(Fdf1) "," %6.0f e(Fdf2) ") = "
                if e(F) < 99999 {
di in ye %8.2f e(F)
                }
                else {
di in ye %8.2e e(F)
                }
di in gr _col(55) "Prob > F      = " in ye %8.4f e(Fp)

di in gr "Total (centered) SS     = " in ye %12.0g e(yyc) _continue
di in gr _col(55) "Centered R2   = " in ye %8.4f e(r2c)
di in gr "Total (uncentered) SS   = " in ye %12.0g e(yy) _continue
di in gr _col(55) "Uncentered R2 = " in ye %8.4f e(r2u)
di in gr "Residual SS             = " in ye %12.0g e(rss) _continue
di in gr _col(55) "Root MSE      = " in ye %8.4g e(rmse)
di
        }

* Display coefficients etc.
* Unfortunate but necessary hack here: to suppress message about cluster adjustment of
*   standard error, clear e(clustvar) and then reset it after display
        local cluster `e(clustvar)'
        * ereturn local clustvar
        * ereturn display, `plus' level(`level') `dispopt'
        * ereturn local clustvar `cluster'
* Sergio: workaround but not 100% sure that it will always work as wanted
* Trick: _coef_table.ado just calls a Mata function that reads locals
    local noclustreport noclustreport // undocumented in _coef_table.ado
    mata: _coef_table()
    return add // adds r(level), r(table), etc. to ereturn (before the footnote deletes them)



* Display 1st footer with identification stats
* Footer not displayed if -nofooter- option or if pure OLS, i.e., model="ols" and Sargan-Hansen=0
        if ~("`nofooter'"~="" | (e(model)=="ols" & (e(sargan)==0 | e(j)==0))) {

* Under ID test
                if "`e(instd)'"~="" & "`e(idstat)'"~="" {
di in smcl _c "{help `helpfile'##idtest:Underidentification test}"
                        if "`e(vcetype)'`e(kernel)'"=="" {
di in gr _c " (Anderson canon. corr. LM statistic):"
                        }
                        else {
di in gr _c " (Kleibergen-Paap rk LM statistic):"
                        }
di in ye _col(71) %8.3f e(idstat)
di in gr _col(52) "Chi-sq(" in ye e(iddf) /* 
                                */  in gr ") P-val =  " in ye _col(73) %6.4f e(idp)
* IV redundancy statistic
                        if "`e(redlist)'"!="" {
di in gr "-redundant- option:"
di in smcl _c "{help `helpfile'##redtest:IV redundancy test}"
di in gr _c " (LM test of redundancy of specified instruments):"
di in ye _col(71) %8.3f e(redstat)
di in gr _col(52) "Chi-sq(" in ye e(reddf) /* 
                                */  in gr ") P-val =  " in ye _col(73) %6.4f e(redp)
di in gr "Instruments tested: " _c
                                        Disp `e(redlist)', _col(23)
                        }
di in smcl in gr "{hline 78}"
                }
* Report Cragg-Donald statistic
                if "`e(instd)'"~="" & "`e(idstat)'"~="" {
di in smcl _c "{help `helpfile'##widtest:Weak identification test}"
di in gr " (Cragg-Donald Wald F statistic):" in ye _col(71) %8.3f e(cdf)
                        if "`e(vcetype)'`e(kernel)'"~="" {
di in gr "                         (Kleibergen-Paap rk Wald F statistic):" in ye _col(71) %8.3f e(widstat)
                        }
di in gr _c "Stock-Yogo weak ID test critical values:"
                        Disp_cdsy, model(`e(model)') k2(`e(exexog_ct)') nendog(`e(endog_ct)') fuller("`e(fuller)'") col1(42) col2(73)
                        if `r(cdmissing)' {
                                di in gr _col(64) "<not available>"
                        }
                        else {
                                di in gr "Source: Stock-Yogo (2005).  Reproduced by permission."
                                if "`e(vcetype)'`e(kernel)'"~="" {
di in gr "NB: Critical values are for Cragg-Donald F statistic and i.i.d. errors."
                                }
                        }
                        di in smcl in gr "{hline 78}"
                }

* Report either (a) Sargan-Hansen-C stats, or (b) robust covariance matrix problem
* e(model)="gmmw" means user-supplied weighting matrix and Hansen J using 2nd-step resids reported
                if `rprob' == 0 {
* Display overid statistic
                        if "`e(vcetype)'" == "Robust" | "`e(model)'" == "gmmw" {
                                if "`e(instd)'" != "" {
di in smcl _c "{help `helpfile'##overidtests:Hansen J statistic}"
di in gr _c " (overidentification test of all instruments):"
                                }
                                else {
di in smcl _c "{help `helpfile'##overidtests:Hansen J statistic}"
di in gr _c " (Lagrange multiplier test of excluded instruments):"
                                }
                        }
                        else {
                                if "`e(instd)'" != "" {
di in smcl _c "{help `helpfile'##overidtests:Sargan statistic}"
di in gr _c " (overidentification test of all instruments):"
                                }
                                else {
di in smcl _c "{help `helpfile'##overidtests:Sargan statistic}"
di in gr _c " (Lagrange multiplier test of excluded instruments):"
                                }
                        }
di in ye _col(71) %8.3f e(j)
                        if e(jdf) {
di in gr _col(52) "Chi-sq(" in ye e(jdf) /* 
                                */  in gr ") P-val =  " in ye _col(73) %6.4f e(jp)
                        }
                        else {
di in gr _col(50) "(equation exactly identified)"
                        }

* Display orthog option: C statistic (difference of Sargan statistics)
                        if e(cstat) != . {
* If C-stat = 0 then warn, otherwise output
                                if e(cstat) > 0  {
di in gr "-orthog- option:"
                                        if "`e(vcetype)'" == "Robust" {
di in gr _c "Hansen J statistic (eqn. excluding suspect orthog. conditions): "
                                        }
                                        else {
di in gr _c "Sargan statistic (eqn. excluding suspect orthogonality conditions):"
                                        }
di in ye _col(71) %8.3f e(j)-e(cstat)
di in gr _col(52) "Chi-sq(" in ye e(jdf)-e(cstatdf) in gr ") P-val =  " /*
                                */ in ye _col(73) %6.4f chiprob(e(jdf)-e(cstatdf),e(j)-e(cstat))
di in smcl _c "{help `helpfile'##ctest:C statistic}"
di in gr _c " (exogeneity/orthogonality of suspect instruments): "
di in ye _col(71) %8.3f e(cstat)
di in gr _col(52) "Chi-sq(" in ye e(cstatdf) in gr ") P-val =  " /*
                                */ in ye _col(73) %6.4f e(cstatp)
di in gr "Instruments tested:  " _c
                                        Disp `e(clist)', _col(23)
                                }
                                if e(cstat) == 0 {
di in gr _n "Collinearity/identification problems in eqn. excl. suspect orthog. conditions:"
di in gr "  C statistic not calculated for -orthog- option"
                                }
                        }
                }
                else {
* Problem exists with robust VCV - notify and list possible causes
di in r "Warning: estimated covariance matrix of moment conditions not of full rank."
                        if e(j)==. {
di in r "         overidentification statistic not reported, and standard errors and"
                        }
di in r "         model tests should be interpreted with caution."
di in r "Possible causes:"
                        if e(nocollin) {
di in r "         collinearities in regressors or instruments (with -nocollin- option)"
                        }
                        if "`e(N_clust)'" != "" {
di in r "         number of clusters insufficient to calculate robust covariance matrix"
                        }
                        if "`e(kernel)'" != "" {
di in r "         covariance matrix of moment conditions not positive definite"
di in r "         covariance matrix uses too many lags"
                        }
di in r "         singleton dummy variable (dummy with one 1 and N-1 0s or vice versa)"
di in r in smcl _c "{help `helpfile'##partial:partial}"
di in r " option may address problem."
                }

* Display endog option: endogeneity test statistic
                if e(estat) != . {
* If stat = 0 then warn, otherwise output
                        if e(estat) > 0  {
di in gr "-endog- option:"
di in smcl _c "{help `helpfile'##endogtest:Endogeneity test}"
di in gr _c " of endogenous regressors: "
di in ye _col(71) %8.3f e(estat)
di in gr _col(52) "Chi-sq(" in ye e(estatdf) /* 
                        */  in gr ") P-val =  " in ye _col(73) %6.4f e(estatp)
di in gr "Regressors tested:  " _c
                                Disp `e(elist)', _col(23)
                        }
                        if e(estat) == 0 {
di in gr _n "Collinearity/identification problems in restricted equation:"
di in gr "  Endogeneity test statistic not calculated for -endog- option"
                        }
                }

                di in smcl in gr "{hline 78}"
* Display AR overid statistic if LIML and not robust
                if "`e(model)'" == "liml" & "`e(vcetype)'" ~= "Robust" & "`e(kernel)'" == "" {
                        if "`e(instd)'" != "" {
di in smcl _c "{help `helpfile'##liml:Anderson-Rubin statistic}"
di in gr _c " (overidentification test of all instruments):"
                                }
                                else {
di in smcl _c "{help `helpfile'##liml:Anderson-Rubin statistic}"
di in gr _c " (LR test of excluded instruments):"
                                }
di in ye _col(72) %7.3f e(arubin)
                        if e(arubindf) {
di in gr _col(52) "Chi-sq(" in ye e(arubindf) /* 
                                */  in gr ") P-val =  " in ye _col(73) %6.4f e(arubinp)
                        }
                        else {
di in gr _col(50) "(equation exactly identified)"
                        }
                        di in smcl in gr "{hline 78}"
                }
        }

* Display 2nd footer with variable lists
        if "`nofooter'"=="" {

* Warn about dropped instruments if any
* Can happen with nocollin option and rank(S) < cols(S)
                if colsof(e(S)) > e(rankzz) {
di in gr "Collinearities detected among instruments: " _c
di in gr colsof(e(S))-e(rankzz) " instrument(s) dropped"
                }

                if "`e(collin)'`e(dups)'" != "" | e(partial_ct) {
* If collinearities, duplicates or partial, abbreviated varlists saved with a 1 at the end
                        local one "1"
                }
                if e(endog_ct) {
                        di in gr "Instrumented:" _c
                        Disp `e(instd`one')', _col(23)
                }
                if e(inexog_ct) {
                        di in gr "Included instruments:" _c
                        Disp `e(inexog`one')', _col(23)
                }
                if e(exexog_ct) {
                        di in gr "Excluded instruments:" _c
                        Disp `e(exexog`one')', _col(23)
                }
                if e(partial_ct) {
                        if e(partialcons) {
                                local partial "`e(partial`one')' _cons"
                        }
                        else {
                                local partial "`e(partial`one')'"
                        }
di in smcl _c "{help `helpfile'##partial:Partialled-out}"
                        di in gr ":" _c
                        Disp `partial', _col(23)
                        if "`e(partialsmall)'"=="" {
di in gr _col(23) "nb: total SS, model F and R2s are after partialling-out;"
di in gr _col(23) "    any {help `helpfile'##s_small:small-sample adjustments} do not include"
di in gr _col(23) "    partialled-out variables in regressor count K"
                        }
                        else {
di in gr _col(23) "nb: total SS, model F and R2s are after partialling-out;"
di in gr _col(23) "    any {help `helpfile'##s_small:small-sample adjustments} include partialled-out"
di in gr _col(23) "    variables in regressor count K"
                        }
                }
                if "`e(dups)'" != "" {
                        di in gr "Duplicates:" _c
                        Disp `e(dups)', _col(23)
                }
                if "`e(collin)'" != "" {
                        di in gr "Dropped collinear:" _c
                        Disp `e(collin)', _col(23)
                }
                if "`e(ecollin)'" != "" {
                        di in gr "Reclassified as exog:" _c
                        Disp `e(ecollin)', _col(23)
                }
                di in smcl in gr "{hline 78}"

                if (e(N_hdfe)!=  .) reghdfe_footnote
        }
end

**************************************************************************************

// ************ Display collinearity and duplicates warning messages ************ //

program define DispCollinDups
        version 11.2
        if "`e(dups)'" != "" {
di in gr "Warning - duplicate variables detected"
di in gr "Duplicates:" _c
                Disp `e(dups)', _col(16)
        }
        if "`e(collin)'" != "" {
di in gr "Warning - collinearities detected"
di in gr "Vars dropped:" _c
                Disp `e(collin)', _col(16)
        }
end

// ************* Display all first-stage estimations ************ //

program define DispFirst
        version 11.2
        args helpfile
        tempname firstmat ivest sheapr2 pr2 F df df_r pvalue
        tempname SWF SWFdf1 SWFdf2 SWFp SWr2

        mat `firstmat'=e(first)
        if `firstmat'[1,1] == . {
di
di in ye "Unable to display first-stage estimates; macro e(first) is missing"
                exit
        }
di in gr _newline "First-stage regressions"
di in smcl in gr "{hline 23}"
di
        local endo1 : colnames(`firstmat')
        local nrvars : word count `endo1'
        local firsteqs "`e(firsteqs)'"
        local nreqs : word count `firsteqs'
        if `nreqs' < `nrvars' {
di in ye "Unable to display all first-stage regressions."
di in ye "There may be insufficient room to store results using -estimates store-,"
di in ye "or names of endogenous regressors may be too long to store the results."
di in ye "Try dropping one or more estimation results using -estimates drop-,"
di in ye "using the -savefprefix- option, or using shorter variable names."
di
        }
        local robust "`e(vcetype)'"
        local cluster "`e(clustvar)'"
        local kernel "`e(kernel)'"
        foreach eqname of local firsteqs {
                _estimates hold `ivest'
                capture estimates restore `eqname'
                if _rc != 0 {
di
di in ye "Unable to list stored estimation `eqname'."
di in ye "There may be insufficient room to store results using -estimates store-,"
di in ye "or names of endogenous regressors may be too long to store the results."
di in ye "Try dropping one or more estimation results using -estimates drop-,"
di in ye "using the -savefprefix- option, or using shorter variable names."
di
                }
                else {
                        local vn "`e(depvar)'"
                        estimates replay `eqname', noheader
                        mat `sheapr2' =`firstmat'["sheapr2","`vn'"]
                        mat `pr2'     =`firstmat'["pr2","`vn'"]
                        mat `F'       =`firstmat'["F","`vn'"]
                        mat `df'      =`firstmat'["df","`vn'"]
                        mat `df_r'    =`firstmat'["df_r","`vn'"]
                        mat `pvalue'  =`firstmat'["pvalue","`vn'"]
                        mat `SWF'     =`firstmat'["SWF","`vn'"]
                        mat `SWFdf1'  =`firstmat'["SWFdf1","`vn'"]
                        mat `SWFdf2'  =`firstmat'["SWFdf2","`vn'"]
                        mat `SWFp'    =`firstmat'["SWFp","`vn'"]
                        mat `SWr2'    =`firstmat'["SWr2","`vn'"]

di in gr "F test of excluded instruments:"
di in gr "  F(" %3.0f `df'[1,1] "," %6.0f `df_r'[1,1] ") = " in ye %8.2f `F'[1,1]
di in gr "  Prob > F      = " in ye %8.4f `pvalue'[1,1]

di in smcl "{help `helpfile'##swstats:Sanderson-Windmeijer multivariate F test of excluded instruments:}"
di in gr "  F(" %3.0f `SWFdf1'[1,1] "," %6.0f `SWFdf2'[1,1] ") = " in ye %8.2f `SWF'[1,1]
di in gr "  Prob > F      = " in ye %8.4f `SWFp'[1,1]

di
                }
                _estimates unhold `ivest'
        }
end

// ************* Display list of stored first-stage and RF estimations ************ //

program define DispStored
        args savesfirst saverf savefirst
        version 11.2

        if "`savesfirst'" != "" {
                local eqlist "`e(sfirsteq)'"
        }
        if "`saverf'" != "" {
                local eqlist "`eqlist' `e(rfeq)'"
        }
        if "`savefirst'" != "" {
                local eqlist "`eqlist' `e(firsteqs)'"
        }
        local eqlist : list retokenize eqlist

di in gr _newline "Stored estimation results"
di in smcl in gr "{hline 25}" _c
        capture estimates dir `eqlist'
        if "`eqlist'" != "" & _rc == 0 {
// Estimates exist and can be listed
                estimates dir `eqlist'
        }
        else if "`eqlist'" != "" & _rc != 0 {
di
di in ye "Unable to list stored estimations."
di
        }
end

// ************* Display summary first-stage and ID test results ************ //

program define DispFFirst
        version 11.2
        args helpfile
        tempname firstmat
        tempname sheapr2 pr2 F df df_r pvalue
        tempname SWF SWFdf1 SWFdf2 SWFp SWchi2 SWchi2p SWr2
        mat `firstmat'=e(first)
        if `firstmat'[1,1] == . {
di
di in ye "Unable to display summary of first-stage estimates; macro e(first) is missing"
                exit
        }
        local endo   : colnames(`firstmat')
        local nrvars : word count `endo'
        local robust   "`e(vcetype)'"
        local cluster  "`e(clustvar)'"
        local kernel   "`e(kernel)'"
        local efirsteqs  "`e(firsteqs)'"

        mat `df'      =`firstmat'["df",1]
        mat `df_r'    =`firstmat'["df_r",1]
        mat `SWFdf1'  =`firstmat'["SWFdf1",1]
        mat `SWFdf2'  =`firstmat'["SWFdf2",1]

di
di in gr _newline "Summary results for first-stage regressions"
di in smcl in gr "{hline 43}"
di

di _c in smcl _col(44) "{help `helpfile'##swstats:(Underid)}"
di    in smcl _col(65) "{help `helpfile'##swstats:(Weak id)}"

di _c in gr "Variable     |"
di _c in smcl _col(16) "{help `helpfile'##swstats:F}" in gr "("
di _c in ye _col(17) %3.0f `df'[1,1] in gr "," in ye %6.0f `df_r'[1,1] in gr ")  P-val"
di _c in gr _col(37) "|"
di _c in smcl _col(39) "{help `helpfile'##swstats:SW Chi-sq}" in gr "("
di _c in ye %3.0f `SWFdf1'[1,1] in gr ") P-val"
di _c in gr _col(60) "|"
di _c in smcl _col(62) "{help `helpfile'##swstats:SW F}" in gr "("
di    in ye _col(67) %3.0f `SWFdf1'[1,1] in gr "," in ye %6.0f `SWFdf2'[1,1] in gr ")"

        local i = 1
        foreach vn of local endo {
        
                mat `sheapr2' =`firstmat'["sheapr2","`vn'"]
                mat `pr2'     =`firstmat'["pr2","`vn'"]
                mat `F'       =`firstmat'["F","`vn'"]
                mat `df'      =`firstmat'["df","`vn'"]
                mat `df_r'    =`firstmat'["df_r","`vn'"]
                mat `pvalue'  =`firstmat'["pvalue","`vn'"]
                mat `SWF'     =`firstmat'["SWF","`vn'"]
                mat `SWFdf1'  =`firstmat'["SWFdf1","`vn'"]
                mat `SWFdf2'  =`firstmat'["SWFdf2","`vn'"]
                mat `SWFp'    =`firstmat'["SWFp","`vn'"]
                mat `SWchi2'  =`firstmat'["SWchi2","`vn'"]
                mat `SWchi2p' =`firstmat'["SWchi2p","`vn'"]
                mat `SWr2'    =`firstmat'["SWr2","`vn'"]

                local vnlen : length local vn
                if `vnlen' > 12 {
                        local vn : piece 1 12 of "`vn'"
                }
di _c in y %-12s "`vn'" _col(14) in gr "|" _col(18) in y %8.2f `F'[1,1]
di _c _col(28) in y %8.4f  `pvalue'[1,1]
di _c _col(37) in g "|" _col(42) in y %8.2f `SWchi2'[1,1] _col(51) in y %8.4f  `SWchi2p'[1,1]
di    _col(60) in g "|" _col(65) in y %8.2f `SWF'[1,1] 
                local i = `i' + 1
        }
di

        if "`robust'`cluster'" != "" {
                if "`cluster'" != "" {
                        local rtype "cluster-robust"
                }
                else if "`kernel'" != "" {
                        local rtype "heteroskedasticity and autocorrelation-robust"
                }
                else {
                        local rtype "heteroskedasticity-robust"
                }
        }
        else if "`kernel'" != "" {
                        local rtype "autocorrelation-robust"
        }
        if "`robust'`cluster'`kernel'" != "" {
di in gr "NB: first-stage test statistics `rtype'"
di
        }

        local k2 = `SWFdf1'[1,1]
di in gr "Stock-Yogo weak ID F test critical values for single endogenous regressor:"
        Disp_cdsy, model(`e(model)') k2(`e(exexog_ct)') nendog(1) fuller("`e(fuller)'") col1(36) col2(67)
        if `r(cdmissing)' {
                di in gr _col(64) "<not available>"
        }
        else {
                di in gr "Source: Stock-Yogo (2005).  Reproduced by permission."
                if "`e(model)'"=="iv" & "`e(vcetype)'`e(kernel)'"=="" {
di in gr "NB: Critical values are for Sanderson-Windmeijer F statistic."
                }
                else {
di in gr "NB: Critical values are for i.i.d. errors only."
                }
di
        }

* Check that SW chi-sq and F denominator are correct and = underid test dof
        if e(iddf)~=`SWFdf1'[1,1] {
di in red "Warning: Error in calculating first-stage id statistics above;"
di in red "         dof of SW statistics is " `SWFdf1'[1,1] ", should be L-(K-1)=`e(iddf)'."
        }

        tempname iddf idstat idp widstat cdf rkf
        scalar `iddf'=e(iddf)
        scalar `idstat'=e(idstat)
        scalar `idp'=e(idp)
        scalar `widstat'=e(widstat)
        scalar `cdf'=e(cdf)
        capture scalar `rkf'=e(rkf)
di in smcl "{help `helpfile'##idtest:Underidentification test}"
di in gr "Ho: matrix of reduced form coefficients has rank=K1-1 (underidentified)"
di in gr "Ha: matrix has rank=K1 (identified)"
        if "`robust'`kernel'"=="" {
di in ye "Anderson canon. corr. LM statistic" _c
        }
        else {
di in ye "Kleibergen-Paap rk LM statistic" _c
        }
di in gr _col(42) "Chi-sq(" in ye `iddf' in gr ")=" %-7.2f in ye `idstat' /*
        */ _col(61) in gr "P-val=" %6.4f in ye `idp'

di
di in smcl "{help `helpfile'##widtest:Weak identification test}"
di in gr "Ho: equation is weakly identified"
di in ye "Cragg-Donald Wald F statistic" _col(65) %8.2f `cdf'
        if "`robust'`kernel'"~="" {
di in ye "Kleibergen-Paap Wald rk F statistic"  _col(65) %8.2f `rkf'
        }
di

di in gr "Stock-Yogo weak ID test critical values for K1=`e(endog_ct)' and L1=`e(exexog_ct)':"
        Disp_cdsy, model(`e(model)') k2(`e(exexog_ct)') nendog(`e(endog_ct)') fuller("`e(fuller)'") col1(36) col2(67)
        if `r(cdmissing)' {
                di in gr _col(64) "<not available>"
        }
        else {
                di in gr "Source: Stock-Yogo (2005).  Reproduced by permission."
                if "`e(vcetype)'`e(kernel)'"~="" {
di in gr "NB: Critical values are for Cragg-Donald F statistic and i.i.d. errors."
                }
        }
di

        tempname arf arfp archi2 archi2p ardf ardf_r
        tempname sstat sstatp sstatdf
di in smcl "{help `helpfile'##wirobust:Weak-instrument-robust inference}"
di in gr "Tests of joint significance of endogenous regressors B1 in main equation"
di in gr "Ho: B1=0 and orthogonality conditions are valid"
* Needs to be small so that adjusted dof is reflected in F stat
        scalar `arf'=e(arf)
        scalar `arfp'=e(arfp)
        scalar `archi2'=e(archi2)
        scalar `archi2p'=e(archi2p)
        scalar `ardf'=e(ardf)
        scalar `ardf_r'=e(ardf_r)
        scalar `sstat'=e(sstat)
        scalar `sstatp'=e(sstatp)
        scalar `sstatdf'=e(sstatdf)
di in ye _c "Anderson-Rubin Wald test"
di in gr _col(36) "F(" in ye `ardf' in gr "," in ye `ardf_r' in gr ")=" /*
                */      _col(49) in ye %7.2f `arf'    _col(61) in gr "P-val=" in ye %6.4f `arfp'
di in ye _c "Anderson-Rubin Wald test"
di in gr _col(36) "Chi-sq(" in ye `ardf' in gr ")=" /*
                */      _col(49) in ye %7.2f `archi2' _col(61) in gr "P-val=" in ye %6.4f `archi2p'
di in ye _c "Stock-Wright LM S statistic"
di in gr _col(36) "Chi-sq(" in ye `sstatdf' in gr ")=" /*
                */      _col(49) in ye %7.2f `sstat' _col(61) in gr "P-val=" in ye %6.4f `sstatp'
di
        if "`robust'`cluster'`kernel'" != "" {
di in gr "NB: Underidentification, weak identification and weak-identification-robust"
di in gr "    test statistics `rtype'"
di
        }

        if "`cluster'" != "" & "`e(clustvar2)'"=="" {
di in gr "Number of clusters             N_clust  = " in ye %10.0f e(N_clust)
        }
        else if "`e(clustvar2)'" ~= "" {
di in gr "Number of clusters (1)         N_clust1 = " in ye %10.0f e(N_clust1)
di in gr "Number of clusters (2)         N_clust2 = " in ye %10.0f e(N_clust2)
        }
di in gr "Number of observations               N  = " in ye %10.0f e(N)
di in gr "Number of regressors                 K  = " in ye %10.0f e(rankxx)
di in gr "Number of endogenous regressors      K1 = " in ye %10.0f e(endog_ct)
di in gr "Number of instruments                L  = " in ye %10.0f e(rankzz)
di in gr "Number of excluded instruments       L1 = " in ye %10.0f e(ardf)
        if "`e(partial)'" != "" {
di in gr "Number of partialled-out regressors/IVs = " in ye %10.0f e(partial_ct)
di in gr "NB: K & L do not included partialled-out variables"
        }

end

// ************* Post first-stage and/or RF estimations ************ //

program define PostFirstRF, eclass
        version 11.2
        syntax [if]                                                     ///
                 [ ,                                                    ///
                                first(string)                   /// can be fv
                                rf                                              /// omit first(.) and rf => post system of eqns
                                rmse_rf(real 0)                 ///
                                bmat(name)                              ///
                                vmat(name)                              ///
                                smat(name)                              ///
                                firstmat(name)                  ///
                                lhs1(string)                    /// can be fv
                                endo1(string)                   ///
                                znames0(string)                 ///
                                znames1(string)                 ///
                                bvclean(integer 0)              ///
                                fvops(integer 0)                ///
                                partial_ct(integer 0)   ///
                                robust                                  ///
                                cluster(string)                 ///
                                cluster1(string)                ///
                                cluster2(string)                ///
                                nc(integer 0)                   ///
                                nc1(integer 0)                  ///
                                nc2(integer 0)                  ///
                                kernel(string)                  ///
                                bw(real 0)                              ///
                                ivar(name)                              ///
                                tvar(name)                              ///
                                obs(integer 0)                  ///
                                iv1_ct(integer 0)               ///
                                cons(integer 0)                 ///
                                partialcons(integer 0)  ///
                                dofminus(integer 0)             ///
                                sdofminus(integer 0)    ///
                        ]

// renaming/copying
        local N                 = `obs'
        local N_clust   = `nc'
        local N_clust1  = `nc1'
        local N_clust2  = `nc2'
        tempname b V S
        mat `b' = `bmat'
        mat `V' = `vmat'
        mat `S' = `smat'

        marksample touse

        mat colname `b' = `lhs1' `endo1'
        mat rowname `b' = `znames1'
        mat `b' = vec(`b')
        mat `b' = `b''
        mat colname `V' = `: colfullnames `b''
        mat rowname `V' = `: colfullnames `b''
        mat colname `S' = `: colfullnames `b''
        mat rowname `S' = `: colfullnames `b''
        
        if "`cluster'"=="" {
                matrix `V'=`V'*(`N'-`dofminus')/(`N'-`iv1_ct'-`dofminus'-`sdofminus')
        }
        else {
                matrix `V'=`V'*(`N'-1)/(`N'-`iv1_ct'-`sdofminus')               ///
                                        * `N_clust'/(`N_clust'-1)
        }

// If RF or first-stage estimation required, extract it
// also set macros for model and depvar
        if "`rf'`first'"~="" {
                if "`rf'"~="" {                                                                                 // RF
                        local vnum              = 0
                        local model             rf
                        local depvar    `lhs1'
                        local rmse              = `rmse_rf'
                }
                else {                                                                                                  // first-stage
                        local vnum              : list posof "`first'" in endo1
                        local vnum              = `vnum'
                        local model     first
                        local depvar    `first'
                        local rmse              = el(`firstmat', rownumb(`firstmat',"rmse"), colnumb(`firstmat',"`first'"))
                }
                local c0                = 1 + `vnum'*`iv1_ct'
                local c1                = (`vnum'+1)*`iv1_ct'
                mat `b'                 = `b'[1,`c0'..`c1']
                mat `V'                 = `V'[`c0'..`c1',`c0'..`c1']
                mat `S'                 = `S'[`c0'..`c1',`c0'..`c1']
                mat coleq `b'   = ""
                mat coleq `V'   = ""
                mat roweq `V'   = ""
                mat coleq `S'   = ""
                mat roweq `S'   = ""
        }
        else {
                local model             sfirst
                local eqlist    `lhs1' `endo1'
        }

// reinsert omitteds etc. unless requested not to
// eqlist empty unless first-stage/rf system
        if ~`bvclean' {
                AddOmitted, bmat(`b') vmat(`V') cnb0(`znames0') cnb1(`znames1') eqlist(`eqlist')
                mat `b' = r(b)
                mat `V' = r(V)
// build fv info (base, empty, etc.) unless there was partialling out
                if `fvops' & ~`partial_ct' {
                        local bfv "buildfvinfo"
                }
        }

        local dof       = `N' - `iv1_ct' - `dofminus' - `sdofminus'
        ereturn post `b' `V', obs(`obs') esample(`touse') dof(`dof') depname(`depvar') `bfv'

// saved RF/first-stage equation scalars
        if "`rf'`first'"~="" {
                ereturn scalar rmse = `rmse'
                ereturn scalar df_r = `dof'
                ereturn scalar df_m = `iv1_ct' - `cons' + `sdofminus' - `partialcons'
        }
        ereturn scalar k_eq     = `: word count `endo1''
        ereturn local cmd       ivreg2
        ereturn local model     `model'
        ereturn matrix S        `S'

        if "`kernel'"!="" {
                ereturn local kernel "`kernel'"
                ereturn scalar bw=`bw'
                ereturn local tvar "`tvar'"
                if "`ivar'" ~= "" {
                        ereturn local ivar "`ivar'"
                }
        }

        if "`robust'" != "" {
                local vce "robust"
        }
        if "`cluster1'" != "" {
                if "`cluster2'"=="" {
                        local vce "`vce' cluster"
                }
                else {
                        local vce "`vce' two-way cluster"
                }
        }
        if "`kernel'" != "" {
                if "`robust'" != "" {
                        local vce "`vce' hac"
                }
                else {
                        local vce "`vce' ac"
                }
                local vce "`vce' `kernel' bw=`bw'"
        }

        local vce : list clean vce
        local vce = lower("`vce'")
        ereturn local vce `vce'

        if "`cluster'"!="" {
                ereturn scalar N_clust=`N_clust'
                ereturn local clustvar `cluster'
        }
        if "`cluster2'"!="" {
                ereturn scalar N_clust1=`N_clust1'
                ereturn scalar N_clust2=`N_clust2'
                ereturn local clustvar1 `cluster1'
                ereturn local clustvar2 `cluster2'
        }

        if "`robust'`cluster'" != "" {
                ereturn local vcetype "Robust"
        }

// Assemble output titles
        if "`e(vcetype)'" == "Robust" {
                local hacsubtitle1 "heteroskedasticity"
        }
        if "`e(kernel)'"!="" & "`e(clustvar)'"=="" {
                local hacsubtitle3 "autocorrelation"
        }
        if "`kiefer'"!="" {
                local hacsubtitle3 "within-cluster autocorrelation (Kiefer)"
        }
        if "`e(clustvar)'"!="" {
                if "`e(clustvar2)'"=="" {
                        local hacsubtitle3 "clustering on `e(clustvar)'"
                }
                else {
                        local hacsubtitle3 "clustering on `e(clustvar1)' and `e(clustvar2)'"
                }
                if "`e(kernel)'" != "" {
                        local hacsubtitle4 "and kernel-robust to common correlated disturbances (Driscoll-Kraay)"
                }
        }
        if "`hacsubtitle1'"~="" & "`hacsubtitle3'" ~= "" {
                local hacsubtitle2 " and "
        }
        local hacsubtitle "`hacsubtitle1'`hacsubtitle2'`hacsubtitle3'"
        if "`hacsubtitle'"~="" {
                ereturn local hacsubtitleV "Statistics robust to `hacsubtitle'"
        }
        else {
                ereturn local hacsubtitleV "Statistics consistent for homoskedasticity only"
        }
        if "`hacsubtitle4'"~="" {
                ereturn local hacsubtitleV2 "`hacsubtitle4'"
        }
        if "`sw'"~="" {
                ereturn local hacsubtitleV "Stock-Watson heteroskedastic-robust statistics (BETA VERSION)"
        }

        if ("`absorb'" != "") {
            mata: HDFE.post_footnote()
            assert e(N_hdfe) != .
        }

end



**************************************************************************************
program define IsStop, sclass
                                /* sic, must do tests one-at-a-time, 
                                 * 0, may be very large */
        version 11.2
        if `"`0'"' == "[" {             
                sret local stop 1
                exit
        }
        if `"`0'"' == "," {
                sret local stop 1
                exit
        }
        if `"`0'"' == "if" {
                sret local stop 1
                exit
        }
* per official ivreg 5.1.3
        if substr(`"`0'"',1,3) == "if(" {
                sret local stop 1
                exit
        }
        if `"`0'"' == "in" {
                sret local stop 1
                exit
        }
        if `"`0'"' == "" {
                sret local stop 1
                exit
        }
        else    sret local stop 0
end

// ************* Display list of variables ************ //

program define Disp 
        version 11.2
        syntax [anything] [, _col(integer 15) ]
        local maxlen = 80-`_col'
        local len = 0
        local first = 1
        foreach vn in `anything' {
* Don't display if base or omitted variable
                _ms_parse_parts `vn'
                if ~`r(omit)' {
                        local vnlen             : length local vn
                        if `len'+`vnlen' > `maxlen' {
                                di
                                local first = 1
                                local len = `vnlen'
                        }
                        else {
                                local len = `len'+`vnlen'+1
                        }
                        if `first' {
                                local first = 0
                                di in gr _col(`_col') "`vn'" _c
                                }
                        else {
                                di in gr " `vn'" _c
                        }
                }
        }
* Finish with a newline
        di
end

// *********** Display Cragg-Donald/Stock-Yogo critical values etc. ******** //

program define Disp_cdsy, rclass
        version 11.2
        syntax , col1(integer) col2(integer) model(string) k2(integer) nendog(integer) [ fuller(string) ]
        local cdmissing=1
        if "`model'"=="iv" | "`model'"=="gmm2s" | "`model'"=="gmmw" {
                cdsy, type(ivbias5) k2(`k2') nendog(`nendog')
                if "`r(cv)'"~="." {
                        di in gr _col(`col1') " 5% maximal IV relative bias" in ye _col(`col2') %6.2f r(cv)
                        local cdmissing=0
                }
                cdsy, type(ivbias10) k2(`k2') nendog(`nendog')
                if "`r(cv)'"~="." {
                        di in gr _col(`col1') "10% maximal IV relative bias" in ye _col(`col2') %6.2f r(cv)
                        local cdmissing=0
                }
                cdsy, type(ivbias20) k2(`k2') nendog(`nendog')
                if "`r(cv)'"~="." {
                        di in gr _col(`col1') "20% maximal IV relative bias" in ye _col(`col2') %6.2f r(cv)
                        local cdmissing=0
                }
                cdsy, type(ivbias30) k2(`k2') nendog(`nendog')
                if "`r(cv)'"~="." {
                        di in gr _col(`col1') "30% maximal IV relative bias" in ye _col(`col2') %6.2f r(cv)
                        local cdmissing=0
                }
                cdsy, type(ivsize10) k2(`k2') nendog(`nendog')
                if "`r(cv)'"~="." {
                        di in gr _col(`col1') "10% maximal IV size" in ye _col(`col2') %6.2f r(cv)
                        local cdmissing=0
                }
                cdsy, type(ivsize15) k2(`k2') nendog(`nendog')
                if "`r(cv)'"~="." {
                        di in gr _col(`col1') "15% maximal IV size" in ye _col(`col2') %6.2f r(cv)
                        local cdmissing=0
                }
                cdsy, type(ivsize20) k2(`k2') nendog(`nendog')
                if "`r(cv)'"~="." {
                        di in gr _col(`col1') "20% maximal IV size" in ye _col(`col2') %6.2f r(cv)
                        local cdmissing=0
                }
                cdsy, type(ivsize25) k2(`k2') nendog(`nendog')
                if "`r(cv)'"~="." {
                        di in gr _col(`col1') "25% maximal IV size" in ye _col(`col2') %6.2f r(cv)
                        local cdmissing=0
                }
        }
        else if ("`model'"=="liml" & "`fuller'"=="") | "`model'"=="cue" {
                cdsy, type(limlsize10) k2(`k2') nendog(`nendog')
                if "`r(cv)'"~="." {
                        di in gr _col(`col1') "10% maximal LIML size" in ye _col(`col2') %6.2f r(cv)
                        local cdmissing=0
                }
                cdsy, type(limlsize15) k2(`k2') nendog(`nendog')
                if "`r(cv)'"~="." {
                        di in gr _col(`col1') "15% maximal LIML size" in ye _col(`col2') %6.2f r(cv)
                        local cdmissing=0
                }
                cdsy, type(limlsize20) k2(`k2') nendog(`nendog')
                if "`r(cv)'"~="." {
                        di in gr _col(`col1') "20% maximal LIML size" in ye _col(`col2') %6.2f r(cv)
                        local cdmissing=0
                }
                cdsy, type(limlsize25) k2(`k2') nendog(`nendog')
                if "`r(cv)'"~="." {
                        di in gr _col(`col1') "25% maximal LIML size" in ye _col(`col2') %6.2f r(cv)
                        local cdmissing=0
                }
        }
        else if ("`model'"=="liml" & "`fuller'"~="") {
                cdsy, type(fullrel5) k2(`k2') nendog(`nendog')
                if "`r(cv)'"~="." {
                        di in gr _col(`col1') " 5% maximal Fuller rel. bias" in ye _col(`col2') %6.2f r(cv)
                        local cdmissing=0
                }
                cdsy, type(fullrel10) k2(`k2') nendog(`nendog')
                if "`r(cv)'"~="." {
                        di in gr _col(`col1') "10% maximal Fuller rel. bias" in ye _col(`col2') %6.2f r(cv)
                        local cdmissing=0
                }
                cdsy, type(fullrel20) k2(`k2') nendog(`nendog')
                if "`r(cv)'"~="." {
                        di in gr _col(`col1') "20% maximal Fuller rel. bias" in ye _col(`col2') %6.2f r(cv)
                        local cdmissing=0
                }
                cdsy, type(fullrel30) k2(`k2') nendog(`nendog')
                if "`r(cv)'"~="." {
                        di in gr _col(`col1') "30% maximal Fuller rel. bias" in ye _col(`col2') %6.2f r(cv)
                        local cdmissing=0
                }
                cdsy, type(fullmax5) k2(`k2') nendog(`nendog')
                if "`r(cv)'"~="." {
                        di in gr _col(`col1') " 5% Fuller maximum bias" in ye _col(`col2') %6.2f r(cv)
                        local cdmissing=0
                }
                cdsy, type(fullmax10) k2(`k2') nendog(`nendog')
                if "`r(cv)'"~="." {
                        di in gr _col(`col1') "10% Fuller maximum bias" in ye _col(`col2') %6.2f r(cv)
                        local cdmissing=0
                }
                cdsy, type(fullmax20) k2(`k2') nendog(`nendog')
                if "`r(cv)'"~="." {
                        di in gr _col(`col1') "20% Fuller maximum bias" in ye _col(`col2') %6.2f r(cv)
                        local cdmissing=0
                }
                cdsy, type(fullmax30) k2(`k2') nendog(`nendog')
                if "`r(cv)'"~="." {
                        di in gr _col(`col1') "30% Fuller maximum bias" in ye _col(`col2') %6.2f r(cv)
                        local cdmissing=0
                }
                di in gr "NB: Critical values based on Fuller parameter=1"
        }       
        return scalar cdmissing =`cdmissing'
end

program define cdsy, rclass
        version 11.2
        syntax , type(string) k2(integer) nendog(integer)

* type() can be ivbias5   (k2<=100, nendog<=3)
*               ivbias10  (ditto)
*               ivbias20  (ditto)
*               ivbias30  (ditto)
*               ivsize10  (k2<=100, nendog<=2)
*               ivsize15  (ditto)
*               ivsize20  (ditto)
*               ivsize25  (ditto)
*               fullrel5  (ditto)
*               fullrel10 (ditto)
*               fullrel20 (ditto)
*               fullrel30 (ditto)
*               fullmax5  (ditto)
*               fullmax10 (ditto)
*               fullmax20 (ditto)
*               fullmax30 (ditto)
*               limlsize10 (ditto)
*               limlsize15 (ditto)
*               limlsize20 (ditto)
*               limlsize25 (ditto)

        tempname temp cv

* Initialize critical value as MV
        scalar `cv'=.

        if "`type'"=="ivbias5" {
                mata: s_cdsy("`temp'", 1)
                if `k2'<=100 & `nendog'<=3 {
                        scalar `cv'=`temp'[`k2',`nendog']
                }
        }

        if "`type'"=="ivbias10" {
                mata: s_cdsy("`temp'", 2)
                if `k2'<=100 & `nendog'<=3 {
                        scalar `cv'=`temp'[`k2',`nendog']
                }
        }

        if "`type'"=="ivbias20" {
                mata: s_cdsy("`temp'", 3)
                if `k2'<=100 & `nendog'<=3 {
                        scalar `cv'=`temp'[`k2',`nendog']
                }
        }

        if "`type'"=="ivbias30" {
                mata: s_cdsy("`temp'", 4)
                if `k2'<=100 & `nendog'<=3 {
                        scalar `cv'=`temp'[`k2',`nendog']
                }
        }


        if "`type'"=="ivsize10" {
                mata: s_cdsy("`temp'", 5)
                if `k2'<=100 & `nendog'<=2 {
                        scalar `cv'=`temp'[`k2',`nendog']
                }
        }

        if "`type'"=="ivsize15" {
                mata: s_cdsy("`temp'", 6)
                if `k2'<=100 & `nendog'<=2 {
                        scalar `cv'=`temp'[`k2',`nendog']
                }
        }

        if "`type'"=="ivsize20" {
                mata: s_cdsy("`temp'", 7)
                if `k2'<=100 & `nendog'<=2 {
                        scalar `cv'=`temp'[`k2',`nendog']
                }
        }

        if "`type'"=="ivsize25" {
                mata: s_cdsy("`temp'", 8)
                if `k2'<=100 & `nendog'<=2 {
                        scalar `cv'=`temp'[`k2',`nendog']
                }
        }
        
        if "`type'"=="fullrel5" {
                mata: s_cdsy("`temp'", 9)
                if `k2'<=100 & `nendog'<=2 {
                        scalar `cv'=`temp'[`k2',`nendog']
                }
        }
        
        if "`type'"=="fullrel10" {
                mata: s_cdsy("`temp'", 10)
                if `k2'<=100 & `nendog'<=2 {
                        scalar `cv'=`temp'[`k2',`nendog']
                }
        }
        
        if "`type'"=="fullrel20" {
                mata: s_cdsy("`temp'", 11)
                if `k2'<=100 & `nendog'<=2 {
                        scalar `cv'=`temp'[`k2',`nendog']
                }
        }

        if "`type'"=="fullrel30" {
                mata: s_cdsy("`temp'", 12)
                if `k2'<=100 & `nendog'<=2 {
                        scalar `cv'=`temp'[`k2',`nendog']
                }
        }

        if "`type'"=="fullmax5" {
                mata: s_cdsy("`temp'", 13)
                if `k2'<=100 & `nendog'<=2 {
                        scalar `cv'=`temp'[`k2',`nendog']
                }
        }
        
        if "`type'"=="fullmax10" {
                mata: s_cdsy("`temp'", 14)
                if `k2'<=100 & `nendog'<=2 {
                        scalar `cv'=`temp'[`k2',`nendog']
                }
        }
        
        if "`type'"=="fullmax20" {
                mata: s_cdsy("`temp'", 15)
                if `k2'<=100 & `nendog'<=2 {
                        scalar `cv'=`temp'[`k2',`nendog']
                }
        }

        if "`type'"=="fullmax30" {
                mata: s_cdsy("`temp'", 16)
                if `k2'<=100 & `nendog'<=2 {
                        scalar `cv'=`temp'[`k2',`nendog']
                }
        }

        if "`type'"=="limlsize10" {
                mata: s_cdsy("`temp'", 17)
                if `k2'<=100 & `nendog'<=2 {
                        scalar `cv'=`temp'[`k2',`nendog']
                }
        }

        if "`type'"=="limlsize15" {
                mata: s_cdsy("`temp'", 18)
                if `k2'<=100 & `nendog'<=2 {
                        scalar `cv'=`temp'[`k2',`nendog']
                }
        }

        if "`type'"=="limlsize20" {
                mata: s_cdsy("`temp'", 19)
                if `k2'<=100 & `nendog'<=2 {
                        scalar `cv'=`temp'[`k2',`nendog']
                }
        }

        if "`type'"=="limlsize25" {
                mata: s_cdsy("`temp'", 20)
                if `k2'<=100 & `nendog'<=2 {
                        scalar `cv'=`temp'[`k2',`nendog']
                }
        }
        return scalar cv=`cv'
end

// ***************************** Parse ivreg2 arguments **************** //

program define ivparse, sclass
        version 11.2
                syntax [anything(name=0)]                       ///
                        [ ,                                                             ///
                                ivreg2name(name)                        ///
                                partial(string)                         ///  as string because may have nonvariable in list
                                fwl(string)                                     ///  legacy option
                                orthog(varlist fv ts)           ///
                                endogtest(varlist fv ts)        ///
                                redundant(varlist fv ts)        ///
                                depname(string)                         ///
                                robust                                          ///
                                cluster(varlist fv ts)          ///
                                bw(string)                                      /// as string because may have noninteger option "auto"
                                kernel(string)                          ///
                                dkraay(integer 0)                       ///
                                sw                                                      ///
                                kiefer                                          ///
                                center                                          ///
                                NOCONSTANT                                      ///
                                tvar(varname)                           ///
                                ivar(varname)                           ///
                                gmm2s                                           ///
                                gmm                                                     ///
                                cue                                                     ///
                                liml                                            ///
                                fuller(real 0)                          ///
                                kclass(real 0)                          ///
                                b0(string)                                      ///
                                wmatrix(string)                         ///
                                NOID                                            ///
                                savefirst                                       ///
                                savefprefix(name)                       ///
                                saverf                                          ///
                                saverfprefix(name)                      ///
                                savesfirst                                      ///
                                savesfprefix(name)                      ///
                                psd0                                            ///
                                psda                                            ///
                                dofminus(integer 0)                     ///
                                NOCOLLIN                                        ///
                                useqr                                           ///
                                bvclean                                         ///
                                eform(string)                           ///
                                NOOMITTED                                       ///
                                vsquish                                         ///
                                noemptycells                            ///
                                baselevels                                      ///
                                allbaselevels                           ///
                        ]

// TS and FV opts based on option varlists
                local tsops             = ("`s(tsops)'"=="true")
                local fvops             = ("`s(fvops)'"=="true")
// useful boolean
                local cons              =("`noconstant'"=="")

                local n 0
                gettoken lhs 0 : 0, parse(" ,[") match(paren)
                IsStop `lhs'
                while `s(stop)'==0 {
                        if "`paren'"=="(" {
                                local ++n
                                if `n'>1 { 
di as err `"syntax is "(all instrumented variables = instrument variables)""'
                                        exit 198
                                }
                                gettoken p lhs : lhs, parse(" =")
                                while "`p'"!="=" {
                                        if "`p'"=="" {
di as err `"syntax is "(all instrumented variables = instrument variables)""'
di as er `"the equal sign "=" is required"'
                                                exit 198
                                        }
                                        local endo `endo' `p'
                                        gettoken p lhs : lhs, parse(" =")
                                }
                                local exexog `lhs'
                        }
                        else {
                                local inexog `inexog' `lhs'
                        }
                        gettoken lhs 0 : 0, parse(" ,[") match(paren)
                        IsStop `lhs'
                }
// lhs attached to front of inexog
                gettoken lhs inexog     : inexog
                local endo                      : list retokenize endo
                local inexog            : list retokenize inexog
                local exexog            : list retokenize exexog
// If depname not provided (default) name is lhs variable
                if "`depname'"=="" {
                        local depname `lhs'
                }

// partial, including legacy FWL option
                local partial           `partial' `fwl'
// Need to nonvars "_cons" from list if present
// Also set `partialcons' local to 0/1
// Need word option so that varnames with cons in them aren't zapped
                local partial           : subinstr local partial "_cons" "", all count(local partialcons) word
                local partial           : list retokenize partial
                if "`partial'"=="_all" {
                        local partial   `inexog'
                }
// constant always partialled out if present in regression and other inexog are being partialled out
// (incompatibilities caught in error-check section below)
                if "`partial'"~="" {
                        local partialcons       = (`cons' | `partialcons')
                }

// detect if TS or FV operators used in main varlists
// clear any extraneous sreturn macros first
                sreturn clear
                local 0                         `lhs' `inexog' `endo' `exexog' `partial'
                syntax                          varlist(fv ts)
                local tsops                     = ("`s(tsops)'"=="true") | `tsops'
                local fvops                     = ("`s(fvops)'"=="true") | `fvops'

// TS operators not allowed with cluster, ivar or tvar.  Captured in -syntax-.
                if "`tvar'" == "" {
                        local tvar              `_dta[_TStvar]'
                }
                if "`ivar'" == "" {
                        local ivar              `_dta[_TSpanel]'
                }
                if "`_dta[_TSdelta]'" == "" {
                        local tdelta    1
                }
                else {                                                                                          //  use evaluator since _dta[_TSdelta] can
                        local tdelta    = `_dta[_TSdelta]'                              //  be stored as e.g. +1.0000000000000X+000
                }

                sreturn local lhs                       `lhs'
                sreturn local depname           `depname'
                sreturn local endo                      `endo'
                sreturn local inexog            `inexog'
                sreturn local exexog            `exexog'
                sreturn local partial           `partial'
                sreturn local cons                      =`cons'
                sreturn local partialcons       =`partialcons'
                sreturn local tsops                     =`tsops'
                sreturn local fvops                     =`fvops'
                sreturn local tvar                      `tvar'
                sreturn local ivar                      `ivar'
                sreturn local tdelta            `tdelta'
                sreturn local noid                      `noid'                  //  can be overriden below
                sreturn local liml                      `liml'                  //  can be overriden below

//convert to boolean
                sreturn local useqr                     =("`useqr'" ~= "")

// Cluster and SW imply robust
                if "`cluster'`sw'"~="" {
                        local robust    "robust"
                }

// HAC estimation.

// First dkraay(bw): special case of HAC with clustering
// on time-series var in a panel + kernel-robust
                if `dkraay' {
                        if "`bw'" == "" {
                                local bw        `dkraay'
                        }
                        if "`cluster'" == "" {
                                local cluster   `tvar'
                        }
                }
// If bw is omitted, default `bw' is 0.
// bw(.) can be number or "auto" hence arrives as string, but is returned as number
// bw=-1 returned if "auto"
// If bw or kernel supplied, check/set `kernel'.
// Macro `kernel' is also used for indicating HAC in use.
// If bw or kernel not supplied, set bw=0
                if "`bw'" == "" & "`kernel'" == "" {
                        local bw        0
                }
                else {
// Check it's a valid kernel and replace with unabbreviated kernel name; check bw.
// s_vkernel is in livreg2 mlib.
                        mata: s_vkernel("`kernel'", "`bw'", "`ivar'")
                        local kernel    `r(kernel)'
                        local bw                `r(bw)'                 //  = -1 if bw(auto) option chosen
                        local tsops             = 1
                }
// kiefer = kernel(tru) bw(T) and no robust
                if "`kiefer'" ~= "" & "`kernel'" == "" {
                        local kernel "Truncated"
                }

// Done parsing VCE opts
                sreturn local bw                `bw'
                sreturn local kernel    `kernel'
                sreturn local robust    `robust'
                sreturn local cluster   `cluster'
                if `bw' {
                        sreturn local bwopt "bw(`bw')"
                        sreturn local kernopt "kernel(`kernel')"
                }
// center arrives as string but is returned as boolean
                sreturn local center    =("`center'"=="center")

// Fuller implies LIML
                if `fuller' != 0 {
                        sreturn local liml                      "liml"
                        sreturn local fulleropt         "fuller(`fuller')"
                }

                if `kclass' != 0 {
                        sreturn local kclassopt         "kclass(`kclass')"
                }

// b0 implies noid.
                if "`b0'" ~= "" {
                        sreturn local noid                      "noid"
                }

// save first, rf
                if "`savefprefix'" != "" {                                              //  savefprefix implies savefirst
                        local savefirst                         "savefirst"
                }
                else {                                                                                  //  default savefprefix is _ivreg2_
                        local savefprefix                       "_`ivreg2name'_"
                }
                sreturn local savefirst                 `savefirst'
                sreturn local savefprefix               `savefprefix'
                if "`saverfprefix'" != "" {                                             //  saverfprefix implies saverf
                        local saverf                            "saverf"
                }
                else {                                                                                  // default saverfprefix is _ivreg2_
                        local saverfprefix                      "_`ivreg2name'_"
                }
                sreturn local saverf                    `saverf'
                sreturn local saverfprefix              `saverfprefix'
                if "`savesfprefix'" != "" {                                     //  savesfprefix implies savesfirst
                        local savesfirst                        "savesfirst"
                }
                else {                                                                                  // default saverfprefix is _ivreg2_
                        local savesfprefix                      "_`ivreg2name'_"
                }
                sreturn local savesfirst                `savesfirst'
                sreturn local savesfprefix              `savesfprefix'

// Macro psd has either psd0, psda or is empty
                sreturn local psd               "`psd0'`psda'"

// dofminus
                if `dofminus' {
                        sreturn local dofmopt   dofminus(`dofminus')
                }

// display options
                local dispopt                   eform(`eform') `vsquish' `noomitted' `noemptycells' `baselevels' `allbaselevels'
// now boolean - indicates that omitted and/or base vars should NOT be added to VCV
// automatically triggered by partial
                local bvclean                   = wordcount("`bvclean'") | wordcount("`partial'") | `partialcons'
                sreturn local bvclean   `bvclean'
                sreturn local dispopt   `dispopt'

// ************ ERROR CHECKS ************* //

                if `partialcons' & ~`cons' {
di in r "Error: _cons listed in partial() but equation specifies -noconstant-." 
                        exit 198
                }
                if `partialcons' > 1 {
// Just in case of multiple _cons
di in r "Error: _cons listed more than once in partial()." 
                        exit 198
                }

// User-supplied tvar and ivar checked if consistent with tsset.
                if "`tvar'"!="`_dta[_TStvar]'" {
di as err "invalid tvar() option - data already -tsset-"
                        exit 5
                }
                if "`ivar'"!="`_dta[_TSpanel]'" {
di as err "invalid ivar() option - data already -xtset-"
                        exit 5
                }

// dkraay
                if `dkraay' {
                        if "`ivar'" == "" | "`tvar'" == "" {
di as err "invalid use of dkraay option - must use tsset panel data"
                                exit 5
                        }
                        if "`dkraay'" ~= "`bw'" {
di as err "cannot use dkraay(.) and bw(.) options together"
                                exit 198
                        }
                        if "`cluster'" ~= "`tvar'" {
di as err "invalid use of dkraay option - must cluster on `tvar' (or omit cluster option)"
                                exit 198
                        }
                }

// kiefer VCV = kernel(tru) bw(T) and no robust with tsset data
                if "`kiefer'" ~= "" {
                        if "`ivar'" == "" | "`tvar'" == "" {
di as err "invalid use of kiefer option - must use tsset panel data"
                                exit 5
                        }
                        if      "`robust'" ~= "" {
di as err "incompatible options: kiefer and robust"
                                exit 198
                        }
                        if      "`kernel'" ~= "" & "`kernel'" ~= "Truncated" {
di as err "incompatible options: kiefer and kernel(`kernel')"
                                exit 198
                        }
                        if      (`bw'~=0) {
di as err "incompatible options: kiefer and bw"
                                exit 198
                        }
                }

// sw=Stock-Watson robust SEs
                if "`sw'" ~= "" & "`cluster'" ~= "" {
di as err "Stock-Watson robust SEs not supported with -cluster- option"
                                exit 198
                }
                if "`sw'" ~= "" & "`kernel'" ~= "" {
di as err "Stock-Watson robust SEs not supported with -kernel- option"
                                exit 198
                }
                if "`sw'" ~= "" & "`ivar'"=="" {
di as err "Must -xtset- or -tsset- data or specify -ivar- with -sw- option"
                        exit 198
                }

// LIML/kclass incompatibilities
                if "`liml'`kclassopt'" != "" {
                        if "`gmm2s'`cue'" != "" {
di as err "GMM estimation not available with LIML or k-class estimators"
                        exit 198
                        }
                        if `fuller' < 0 {
di as err "invalid Fuller option"
                        exit 198
                        }
                        if "`liml'" != "" & "`kclassopt'" != "" {
di as err "cannot use liml and kclass options together"
                        exit 198
                        }
                        if `kclass' < 0 {
di as err "invalid k-class option"
                                exit 198
                                }                       
                }

                if "`gmm2s'" != "" & "`cue'" != "" {
di as err "incompatible options: 2-step efficient gmm and cue gmm"
                        exit 198
                }

                if "`gmm2s'`cue'" != "" & "`exexog'" == "" {
di as err "option `gmm2s'`cue' invalid: no excluded instruments specified"
                        exit 102
                }

// Legacy gmm option
                if "`gmm'" ~= "" {
di as err "-gmm- is no longer a supported option; use -gmm2s- with the appropriate option"
di as res "      gmm             =  gmm2s robust"
di as res "      gmm robust      =  gmm2s robust"
di as res "      gmm bw()        =  gmm2s bw()"
di as res "      gmm robust bw() =  gmm2s robust bw()"
di as res "      gmm cluster()   =  gmm2s cluster()"
                        exit 198
                }
                
// b0 incompatible options.
                if "`b0'" ~= "" & "`gmm2s'`cue'`liml'`wmatrix'" ~= "" {
di as err "incompatible options: -b0- and `gmm2s' `cue' `liml' `wmatrix'"
                        exit 198
                }
                if "`b0'" ~= "" & `kclass' ~= 0 {
di as err "incompatible options: -b0- and kclass(`kclass')"
                        exit 198
                }

                if "`psd0'"~="" & "`psda'"~="" {
di as err "cannot use psd0 and psda options together"
                        exit 198
                }
end

// *************** Check varlists for for duplicates and collinearities ***************** //

program define CheckDupsCollin, sclass
        version 11.2
                syntax                                                          ///
                        [ ,                                                             ///
                                lhs(string)                                     ///
                                endo(string)                            ///
                                inexog(string)                          ///
                                exexog(string)                          ///
                                partial(string)                         ///
                                orthog(string)                          ///
                                endogtest(string)                       ///
                                redundant(string)                       ///
                                touse(string)                           ///
                                wvar(string)                            ///
                                wf(real 0)                                      ///
                                NOCONSTANT                                      ///
                                NOCOLLIN                                        ///
                                fvall                                           ///
                                fvsep                                           ///
                        ]

                if "`fvall'`fvsep'"=="" {                               //  default, expand RHS and exexog separately
                        local rhs       `endo' `inexog'
                        foreach vl in lhs rhs exexog {
                                fvexpand ``vl'' if `touse'
                                local `vl' `r(varlist)'
                        }
                        local allvars   `rhs' `exexog'
                }
                else if "`fvall'"~="" {                                 //  expand all 3 varlists as one
                        fvexpand `lhs' if `touse'
                        local lhs               `r(varlist)'
                        fvexpand `endo' `inexog' `exexog' if `touse'
                        local allvars   `r(varlist)'
                }
                else if "`fvsep'"~="" {                                 //  expand 3 varlists separately
                        foreach vl in lhs endo inexog exexog {
                                fvexpand ``vl'' if `touse'
                                local `vl' `r(varlist)'
                        }
                        local allvars   `endo' `inexog' `exexog'
                }
                else {                                                                  //  shouldn't reach here
di as err "internal ivreg2 err: CheckDupsCollin"
                        exit 198
                }

// Create dictionary: `allvars' is list with b/n/o etc., sallvars is stripped version
// NB: lhs is not in dictionary and won't need to recreate it
                ivreg2_fvstrip `allvars'
                local sallvars  `r(varlist)'

// Create consistent expanded varlists
// (1) expand; (2) strip (since base etc. may be wrong); (3) recreate using dictionary
// NB: matchnames will return unmatched original name if not found in 2nd arg varlist
                foreach vl in endo inexog exexog partial orthog endogtest redundant {
                        fvexpand ``vl'' if `touse'
                        ivreg2_fvstrip `r(varlist)'
                        local stripped  `r(varlist)'                                                    //  create stripped version of varlist
                        matchnames "`stripped'" "`sallvars'" "`allvars'"                //  match using dictionary
                        local `vl'              `r(names)'                                                              //  new consistent varlist with correct b/n/o etc.
                }

// Check for duplicates of variables
// (1)  inexog > endo
// (2)  inexog > exexog
// (3)  endo + exexog = inexog, as if it were "perfectly predicted"
                local lhs0              `lhs'                                   //  create here
                local dupsen1   : list dups endo
                local dupsin1   : list dups inexog
                local dupsex1   : list dups exexog
                foreach vl in endo inexog exexog partial orthog endogtest redundant {
                        local `vl'0     : list uniq `vl'
                }
// Remove inexog from endo
                local dupsen2   : list endo0 & inexog0
                local endo0             : list endo0 - inexog0
// Remove inexog from exexog
                local dupsex2   : list exexog0 & inexog0
                local exexog0   : list exexog0 - inexog0
// Remove endo from exexog
                local dupsex3   : list exexog0 & endo0
                local exexog0   : list exexog0 - endo0
                local dups "`dupsen1' `dupsex1' `dupsin1' `dupsen2' `dupsex2' `dupsex3'"
                local dups              : list uniq dups

// Collinearity checks

// Need variable counts for "0" varlists
// These do NOT include the constant
                local endo0_ct          : word count `endo0'
                local inexog0_ct        : word count `inexog0'
                local rhs0_ct           : word count `inexog0' `exexog0'
                local exexog0_ct        : word count `exexog'

                if "`nocollin'" == "" {

// Needed for ivreg2_rmcollright2
                        tempvar normwt
                        qui gen double `normwt' = `wf' * `wvar' if `touse'

// Simple case: no endogenous regressors, only included and excluded exogenous
                        if `endo0_ct'==0 {
// Call ivreg2_rmcollright2 on "0" versions of inexog and exexog
// noexpand since already expanded and don't want inconsistant expansion
// newonly since don't want base vars in collinear list
                                qui ivreg2_rmcollright2 `inexog0' `exexog0' if `touse',         ///
                                                normwt(`normwt') `noconstant' noexpand newonly
// ivreg2_rmcollright2 returns fulll varlist with omitteds marked as omitted,
// so just need to separate the inexog and exexog lists
                                if `r(k_omitted)' {
                                        local collin    `collin' `r(omitted)'
                                        local inexog0   ""
                                        local exexog0   ""
                                        local nvarlist  `r(varlist)'
                                        local i                 1
                                        while `i' <= `rhs0_ct' {
                                                local nvar              : word `i' of `nvarlist'
                                                if `i' <= `inexog0_ct' {
                                                        local inexog0   `inexog0' `nvar'                //  first batch go into inexog0
                                                }
                                                else {
                                                        local exexog0   `exexog0' `nvar'                //  remainder go into exexog0
                                                }
                                                local ++i
                                        }
                                        local inexog0   : list retokenize inexog0
                                        local exexog0   : list retokenize exexog0
                                }
                        }
// Not-simple case: endogenous regressors
                        else {

// 1st pass through - remove intra-endo collinears
                                qui ivreg2_rmcollright2 `endo0' if `touse',                             ///
                                                normwt(`normwt') `noconstant' noexpand newonly
// ivreg2_rmcollright2 returns fulll varlist with omitteds marked as omitted,
// so just need to separate the inexog and exexog lists
                                if `r(k_omitted)' {
                                        local collin    `collin' `r(omitted)'
                                        local endo0             `r(varlist)'
                                }

// 2nd pass through - good enough unless endog appear as colllinear
// noexpand since already expanded and don't want inconsistent expansion
// newonly since don't want base vars in collinear list
                                qui ivreg2_rmcollright2 `inexog0' `exexog0' `endo0' if `touse',         ///
                                                normwt(`normwt') `noconstant' noexpand newonly
                                if `r(k_omitted)' {
// Check if any endo are in the collinears.
// If yes, reclassify as inexog, then
// 3rd pass through - and then proceed to process inexog and exexog as above
                                        local ecollin   `r(omitted)'
                                        local ecollin   : list ecollin - inexog0
                                        local ecollin   : list ecollin - exexog0
                                        if wordcount("`ecollin'") {
// Collinears in endo, so reclassify as inexog, redo counts and call ivreg2_rmcollright2 again
                                                local endo0                     : list endo0 - ecollin
                                                local inexog0           `ecollin' `inexog0'
                                                local inexog0           : list retokenize inexog0
                                                local endo0_ct          : word count `endo0'
                                                local inexog0_ct        : word count `inexog0'
                                                local rhs0_ct           : word count `inexog0' `exexog0'
// noexpand since already expanded and don't want inconsistant expansion
// newonly since don't want base vars in collinear list
                                                qui ivreg2_rmcollright2 `inexog0' `exexog0' `endo0' if `touse',         ///
                                                                normwt(`normwt') `noconstant' noexpand newonly
                                        }
// Collinears in inexog or exexog
                                        local collin    `collin' `r(omitted)'
                                        local inexog0   ""
                                        local exexog0   ""
                                        local nvarlist  `r(varlist)'
                                        local i                 1
                                        while `i' <= `rhs0_ct' {
                                                local nvar              : word `i' of `nvarlist'
                                                if `i' <= `inexog0_ct' {
                                                        local inexog0   `inexog0' `nvar'
                                                }
                                                else {
                                                        local exexog0   `exexog0' `nvar'
                                                }
                                                local ++i
                                        }
                                        local inexog0   : list retokenize inexog0
                                        local exexog0   : list retokenize exexog0
                                }
                        }

// Collinearity and duplicates warning messages, if necessary
                        if "`dups'" != "" {
di in gr "Warning - duplicate variables detected"
di in gr "Duplicates:" _c
                                Disp `dups', _col(21)
                        }
                        if "`ecollin'" != "" {
di in gr "Warning - endogenous variable(s) collinear with instruments"
di in gr "Vars now exogenous:" _c
                                Disp `ecollin', _col(21)
                        }
                        if "`collin'" != "" {
di in gr "Warning - collinearities detected"
di in gr "Vars dropped:" _c
                                Disp `collin', _col(21)
                        }
                }

// Last step: process partial0 so that names with o/b/n etc. match inexog0
                if wordcount("`partial0'") {
                        ivreg2_fvstrip `inexog0' if `touse'
                        local sinexog0          `r(varlist)'                                                    //  for inexog dictionary
                        ivreg2_fvstrip `partial0' if `touse'
                        local spartial0         `r(varlist)'                                                    //  for partial dictionary
                        matchnames "`spartial0'" "`sinexog0'" "`inexog0'"                       //  match using dictionary
                        local partial0  `r(names)'                                                                      //  new partial0 with matches
                        local partialcheck              : list partial0 - inexog0                       //  unmatched are still in partial0
                        if ("`partialcheck'"~="") {                                                                     //  so catch them
di in r "Error: `partialcheck' listed in partial() but not in list of regressors." 
                                error 198
                        }
                }
// Completed duplicates and collinearity checks

                foreach vl in lhs endo inexog exexog partial orthog endogtest redundant {
                        sreturn local `vl'              ``vl''
                        sreturn local `vl'0             ``vl'0'
                }
                sreturn local dups              `dups'
                sreturn local collin    `collin'
                sreturn local ecollin   `ecollin'

end

// ******************* Misc error checks *************************** //

program define CheckMisc, rclass
        version 11.2
                syntax                                                          ///
                        [ ,                                                             ///
                                rhs1_ct(integer 0)                      ///
                                iv1_ct(integer 0)                       ///
                                bvector(name)                           ///
                                smatrix(name)                           ///
                                wmatrix(name)                           ///
                                cnb1(string)                            ///
                                cnZ1(string)                            ///
                        ]

// Check variable counts
                if `rhs1_ct' == 0 {
di as err "error: no regressors specified"
                        exit 102
                }
                if `rhs1_ct' > `iv1_ct' {
di as err "equation not identified; must have at least as many instruments"
di as err "not in the regression as there are instrumented variables"
                        exit 481
                }

// Check user-supplied b vector
                if "`bvector'" != "" {
                        tempname b0
// Rearrange/select columns to mat IV matrix
                        cap matsort `bvector' "`cnb1'"
                        matrix `b0'=r(sorted)
                        local scols = colsof(`b0')
                        local bcols : word count `cnb1'
                        if _rc ~= 0 | (`scols'~=`bcols') {
di as err "-b0- option error: supplied b0 columns do not match regressor list"
exit 198
                        }
                        return mat b0 = `b0'
                }

// Check user-supplied S matrix
                if "`smatrix'" != "" {
                        tempname S0
// Check that smatrix is indeed a matrix
                        cap mat S0 = `smatrix'
                        if _rc ~= 0 {
di as err "invalid matrix `smatrix' in smatrix option"
exit _rc
                        }
// Rearrange/select columns to mat IV matrix
                        cap matsort `smatrix' "`cnZ1'"
                        matrix `S0'=r(sorted)
                        local srows = rowsof(`S0')
                        local scols = colsof(`S0')
                        local zcols : word count `cnZ1'
                        if _rc ~= 0 | (`srows'~=`zcols') | (`scols'~=`zcols') {
di as err "-smatrix- option error: supplied matrix columns/rows do not match IV list"
exit 198
                        }
                        if issymmetric(`S0')==0 {
di as err "-smatrix- option error: supplied matrix is not symmetric"
exit 198
                        }
                        return mat S0 = `S0'
                }

// Check user-supplied W matrix
                if "`wmatrix'" != "" {
                        tempname W0
// Check that wmatrix is indeed a matrix
                        cap mat W0 = `wmatrix'
                        if _rc ~= 0 {
di as err "invalid matrix `wmatrix' in wmatrix option"
exit _rc
                        }
// Rearrange/select columns to mat IV matrix
                        cap matsort `wmatrix' "`cnZ1'"
                        matrix `W0'=r(sorted)
                        local srows = rowsof(`W0')
                        local scols = colsof(`W0')
                        local zcols : word count `cnZ1'
                        if _rc ~= 0 | (`srows'~=`zcols') | (`scols'~=`zcols') {
di as err "-wmatrix- option error: supplied matrix columns/rows do not match IV list"
exit 198
                        }
                        if issymmetric(`W0')==0 {
di as err "-smatrix- option error: supplied matrix is not symmetric"
exit 198
                        }
                        return mat W0 = `W0'
                }
end


*******************************************************************************
************************* misc utilities **************************************
*******************************************************************************

// internal version of ivreg2_fvstrip 1.01 ms 24march2015
// takes varlist with possible FVs and strips out b/n/o notation
// returns results in r(varnames)
// optionally also omits omittable FVs
// expand calls fvexpand either on full varlist
// or (with onebyone option) on elements of varlist

program define ivreg2_fvstrip, rclass
        version 11.2
        syntax [anything] [if] , [ dropomit expand onebyone NOIsily ]
        if "`expand'"~="" {                                                                                             //  force call to fvexpand
                if "`onebyone'"=="" {
                        fvexpand `anything' `if'                                                                //  single call to fvexpand
                        local anything `r(varlist)'
                }
                else {
                        foreach vn of local anything {
                                fvexpand `vn' `if'                                                                      //  call fvexpand on items one-by-one
                                local newlist   `newlist' `r(varlist)'
                        }
                        local anything  : list clean newlist
                }
        }
        foreach vn of local anything {                                                                  //  loop through varnames
                if "`dropomit'"~="" {                                                                           //  check & include only if
                        _ms_parse_parts `vn'                                                                    //  not omitted (b. or o.)
                        if ~`r(omit)' {
                                local unstripped        `unstripped' `vn'                               //  add to list only if not omitted
                        }
                }
                else {                                                                                                          //  add varname to list even if
                        local unstripped                `unstripped' `vn'                               //  could be omitted (b. or o.)
                }
        }
// Now create list with b/n/o stripped out
        foreach vn of local unstripped {
                local svn ""                                                                                    //  initialize
                _ms_parse_parts `vn'
                if "`r(type)'"=="variable" & "`r(op)'"=="" {                    //  simplest case - no change
                        local svn       `vn'
                }
                else if "`r(type)'"=="variable" & "`r(op)'"=="o" {              //  next simplest case - o.varname => varname
                        local svn       `r(name)'
                }
                else if "`r(type)'"=="variable" {                                               //  has other operators so strip o but leave .
                        local op        `r(op)'
                        local op        : subinstr local op "o" "", all
                        local svn       `op'.`r(name)'
                }
                else if "`r(type)'"=="factor" {                                                 //  simple factor variable
                        local op        `r(op)'
                        local op        : subinstr local op "b" "", all
                        local op        : subinstr local op "n" "", all
                        local op        : subinstr local op "o" "", all
                        local svn       `op'.`r(name)'                                                  //  operator + . + varname
                }
                else if"`r(type)'"=="interaction" {                                             //  multiple variables
                        forvalues i=1/`r(k_names)' {
                                local op        `r(op`i')'
                                local op        : subinstr local op "b" "", all
                                local op        : subinstr local op "n" "", all
                                local op        : subinstr local op "o" "", all
                                local opv       `op'.`r(name`i')'                                       //  operator + . + varname
                                if `i'==1 {
                                        local svn       `opv'
                                }
                                else {
                                        local svn       `svn'#`opv'
                                }
                        }
                }
                else if "`r(type)'"=="product" {
                        di as err "ivreg2_fvstrip error - type=product for `vn'"
                        exit 198
                }
                else if "`r(type)'"=="error" {
                        di as err "ivreg2_fvstrip error - type=error for `vn'"
                        exit 198
                }
                else {
                        di as err "ivreg2_fvstrip error - unknown type for `vn'"
                        exit 198
                }
                local stripped `stripped' `svn'
        }
        local stripped  : list retokenize stripped                                              //  clean any extra spaces
        
        if "`noisily'"~="" {                                                                                    //  for debugging etc.
di as result "`stripped'"
        }

        return local varlist    `stripped'                                                              //  return results in r(varlist)
end

// **************** Add omitted vars to b  and V matrices ****************** //

program define AddOmitted, rclass
        version 11.2
        syntax                                                          ///
                [ ,                                                             ///
                        bmat(name)                                      ///
                        vmat(name)                                      ///
                        cnb0(string)                            ///
                        cnb1(string)                            ///
                        eqlist(string)                          /// if empty, single-equation b and V
                ]

        tempname newb newV
        local eq_ct             =max(1,wordcount("`eqlist'"))
        local rhs0_ct   : word count `cnb0'
        local rhs1_ct   : word count `cnb1'

        foreach vn in `cnb1' {
                local cnum      : list posof "`vn'" in cnb0
                local cnumlist "`cnumlist' `cnum'"
        }
// cnumlist is the list of columns in the single-equation new big matrix in which
// the non-zero entries from the reduced matrix (bmat or vmat) will appear.
// E.g., if newb will be [mpg o.mpg2 _cons] then cnum = [1 3].

        mata: s_AddOmitted(                                     ///
                                                "`bmat'",               ///
                                                "`vmat'",               ///
                                                "`cnumlist'",   ///
                                                `eq_ct',                ///
                                                `rhs0_ct',              ///
                                                `rhs1_ct')
        mat `newb' = r(b)
        mat `newV' = r(V)

        if `eq_ct'==1 {
                local allnames  `cnb0'                                          //  simple single-eqn case
        }
        else {
                foreach eqname in `eqlist' {
                        foreach vname in `cnb0' {
                                local allnames  "`allnames' `eqname':`vname'"
                        }
                }
        }
        mat colnames `newb'     = `allnames'
        mat rownames `newb' = y1
        mat colnames `newV' = `allnames'
        mat rownames `newV' = `allnames'

        return matrix b         =`newb'
        return matrix V         =`newV'
end

// ************* More misc utilities ************** //

program define matsort, rclass
        version 11.2
        args bvmat names
        tempname m1 m2
        foreach vn in `names' {
                mat `m1'=nullmat(`m1'), `bvmat'[1...,"`vn'"]
        }
        if rowsof(`m1')>1 {
                foreach vn in `names' {
                        mat `m2'=nullmat(`m2') \ `m1'["`vn'",1...]
                }
                return matrix sorted =`m2'
        }
        else {
                return matrix sorted =`m1'
        }
end


program define matchnames, rclass
        version 11.2
        args    varnames namelist1 namelist2

        local k1 : word count `namelist1'
        local k2 : word count `namelist2'

        if `k1' ~= `k2' {
                di as err "namelist error"
                exit 198
        }
        foreach vn in `varnames' {
                local i : list posof `"`vn'"' in namelist1
                if `i' > 0 {
                        local newname : word `i' of `namelist2'
                }
                else {
* Keep old name if not found in list
                        local newname "`vn'"
                }
                local names "`names' `newname'"
        }
        local names     : list clean names
        return local names "`names'"
end


program define checkversion_ranktest, rclass
        version 11.2
        args caller

* Check that -ranktest- is installed
                capture ranktest, version
                if _rc != 0 {
di as err "Error: must have ranktest version 01.3.02 or greater installed"
di as err "To install, from within Stata type " _c
di in smcl "{stata ssc install ranktest :ssc install ranktest}"
                        exit 601
                }
                local vernum "`r(version)'"
                if ("`vernum'" < "01.3.02") | ("`vernum'" > "09.9.99") {
di as err "Error: must have ranktest version 01.3.02 or greater installed"
di as err "Currently installed version is `vernum'"
di as err "To update, from within Stata type " _c
di in smcl "{stata ssc install ranktest, replace :ssc install ranktest, replace}"
                        exit 601
                }

* Minimum Stata version required for ranktest ver 2.0 or higher is Stata 16.
* If calling version is <16 then forks to ranktest ver 1.4 (aka ranktest11).
                if `caller' >= 16 {
                        return local ranktestcmd        version `caller': ranktest
                }
                else {
                        return local ranktestcmd        version 11.2: ranktest
                }
end

// ************ Replacement _rmcollright with tweaks ****************** //

program define ivreg2_rmcollright2, rclass
        version 11.2
        syntax  [ anything ]                                    ///  anything so that FVs aren't reordered
                        [if] [in]                                               ///
                        [,                                                              ///
                        NORMWT(varname)                                 ///
                        NOCONStant                                              ///
                        NOEXPAND                                                ///
                        newonly                                                 ///
                        lindep                                                  ///
                        ]

// Empty varlist, leave early
        if "`anything'"=="" {
                return scalar k_omitted =0
                exit
        }

        marksample touse
        markout `touse' `anything'

        local cons              = ("`noconstant'"=="")
        local expand    = ("`noexpand'"=="")
        local newonly   = ("`newonly'"~="")
        local forcedrop = ("`forcedrop'"~="")
        local lindep    = ("`lindep'"~="")
        local 0                 `anything'
        sreturn clear                                                           //  clear any extraneous sreturn macros
        syntax varlist(ts fv)
        local tsops             = ("`s(tsops)'"=="true")
        local fvops             = ("`s(fvops)'"=="true")

        if `tsops' | `fvops' {
                if `expand' {
                        fvexpand `anything' if `touse'
                        local anything          `r(varlist)'
                        fvrevar `anything' if `touse'
                        local fv_anything       `r(varlist)'
                }
                else {
// already expanded and in set order
// loop through fvrevar so that it doesn't rebase or reorder
                        foreach var in `anything' {
                                fvrevar `var' if `touse'
                                local fv_anything       `fv_anything' `r(varlist)'
                        }
                }
        }
        else {
                local fv_anything       `anything'
        }

        tempname wname
        if "`normwt'"=="" {
                qui gen byte `wname'=1 if `touse'
        }
        else {
                qui gen double `wname' = `normwt' if `touse'
        }

        mata: s_rmcoll2("`fv_anything'", "`anything'", "`wname'", "`touse'", `cons', `lindep')
        
        foreach var in `r(omitted)' {
                di as text "note: `var' omitted because of collinearity"
        }
        
        local omitted   "`r(omitted)'"                  //  has all omitted, both newly and previously omitted
        local k_omitted =r(k_omitted)                   //  but newly omitted not marked with omit operator o
        if `lindep' {
                tempname lindepmat
                mat `lindepmat' = r(lindep)
                mat rownames `lindepmat' = `anything'
                mat colnames `lindepmat' = `anything'
        }

// Modern Stata version, add omitted notation to newly-missing vars
        if `k_omitted' {
                foreach var in `omitted' {
                        _ms_parse_parts `var'                   //  check if already omitted
                        if r(omit) {                                    //  already omitted
                                local alreadyomitted    `alreadyomitted' `var'
                        }
                        else {                                                  //  not already omitted
                                ivreg2_rmc2_ms_put_omit `var'   //  add omitted omit operator o and replace in main varlist
                                local ovar      `s(ospec)'
                                local anything  : subinstr local anything "`var'" "`ovar'", word
                        }
                }
                if `newonly' {                                          //  omitted list should contain only newly omitted
                        local omitted   : list omitted - alreadyomitted
                        local k_omitted : word count `omitted'
                }
        }

// Return results
        return scalar k_omitted =`k_omitted'
        return local omitted    `omitted'
        return local varlist    `anything'
        if `lindep' {
                return mat lindep       `lindepmat'
        }

end

// Used by ivreg2_rmcollright2
// taken from later Stata - not available in Stata 11
// version 1.0.0  28apr2011
program ivreg2_rmc2_ms_put_omit, sclass
        version 11.2                                            //  added by MS
        args vn
        _ms_parse_parts `vn'
        if r(type) =="variable" {
                local name `r(name)'
                local ovar o.`name'
        }
        if r(type) == "factor" {
                if !r(base) {
                        local name `r(name)'
                        if "`r(ts_op)'" != "" {
                                local name `r(ts_op)'.`name'
                        }       
                        local ovar `r(level)'o.`name'
                }
                else {
                        local ovar `vn'
                }
        }
        else if r(type) == "interaction" {
                local k = r(k_names)

                forval i = 1/`k' {
                        local name = r(name`i')
                        if "`r(ts_op`i')'" != "" {
                                local name `r(ts_op`i')'.`name'
                        }
                        if "`r(level`i')'" != "" {
                                if r(base`i') {
                                        local name `r(level`i')'b.`name'
                                }
                                else {
                                        local name `r(level`i')'o.`name'
                                }
                        }
                        else {
                                local name o.`name'
                        }
                        local spec `spec'`sharp'`name'
                        local sharp "#"
                }
                local ovar `spec'
                                
        }
        _msparse `ovar'
        sreturn local ospec `r(stripe)'
end


*******************************************************************************
**************** SUBROUTINES FOR KERNEL-ROBUST ********************************
*******************************************************************************

// abw wants a varlist of [ eps | Z | touse]
// where Z includes all instruments, included and excluded, with constant if
// present as the last column; eps are a suitable set of residuals; and touse
// marks the observations in the data matrix used to generate the residuals
// (e.g. e(sample) of the appropriate model).
// The Noconstant option indicates that no constant term exists in the Z matrix.
// kern is the name of the HAC kernel. -ivregress- only provides definitions
// for Bartlett (default), Parzen, quadratic spectral.

// returns the optimal bandwidth as local abw

// abw 1.0.1  CFB 30jun2007
// 1.0.1 : redefine kernel names (3 instances) to match ivreg2
// 1.1.0 : pass nobs and tobs to s_abw; abw bug fix and also handles gaps in data correctly

prog def abw, rclass
        version 11.2
        syntax varlist(ts), [ tindex(varname) nobs(integer 0) tobs(integer 0) NOConstant Kernel(string)]
// validate kernel 
        if "`kernel'" == "" {
                local kernel = "Bartlett"
        }
// cfb B102
        if !inlist("`kernel'", "Bartlett", "Parzen", "Quadratic Spectral") {
                di as err "Error: kernel `kernel' not compatible with bw(auto)"
                return scalar abw = 1
                return local bwchoice "Kernel `kernel' not compatible with bw(auto); bw=1 (default)"
                exit
        }
        else {
// set constant
                local cons 1 
                if "`noconstant'" != "" {
                        local cons 0
                }
// deal with ts ops 
                tsrevar `varlist'
                local varlist1 `r(varlist)'
                mata: s_abw("`varlist1'", "`tindex'", `nobs', `tobs', `cons', "`kernel'")
                return scalar abw = `abw'
                return local bwchoice "Automatic bw selection according to Newey-West (1994)"
        }
end


*******************************************************************************
************** END SUBROUTINES FOR KERNEL-ROBUST ******************************
*******************************************************************************

*******************************************************************************
*************************** BEGIN MATA CODE ***********************************
*******************************************************************************

// capture in case calling under version < 11.2
capture version 11.2

mata:

// For reference:
// struct ms_vcvorthog {
//      string scalar   ename, Znames, touse, weight, wvarname
//      string scalar   robust, clustvarname, clustvarname2, clustvarname3, kernel
//      string scalar   sw, psd, ivarname, tvarname, tindexname
//      real scalar             wf, N, bw, tdelta, dofminus
//  real scalar         center
//      real matrix             ZZ
//      pointer matrix  e
//      pointer matrix  Z
//      pointer matrix  wvar
// }


void s_abw      (string scalar Zulist,
                        string scalar tindexname,
                        real scalar nobs,
                        real scalar tobs,
                        real scalar cons,
                        string scalar kernel
                        )
{

// nobs = number of observations = number of data points available = rows(uZ)
// tobs = time span of data = t_N - t_1 + 1
// nobs = tobs if no gaps in data
// nobs < tobs if there are gaps
// nobs used below when calculating means, e.g., covariances in sigmahat.
// tobs used below when time span of data is needed, e.g., mstar.

        string rowvector Zunames, tov
        string scalar v, v2
        real matrix uZ
        real rowvector h
        real scalar lenzu, abw
                                                
// access the Stata variables in Zulist, honoring touse stored as last column
        Zunames = tokens(Zulist)
        lenzu=cols(Zunames)-1
        v = Zunames[|1\lenzu|]
        v2 = Zunames[lenzu+1]
        st_view(uZ,.,v,v2)
        tnow=st_data(., tindexname)

// assume constant in last col of uZ if it exists
// account for eps as the first column of uZ
        if (cons) {
                nrows1=cols(uZ)-2
                nrows2=1
        }
        else {
                nrows1=cols(uZ)-1
                nrows2=0
        }
// [R] ivregress p.42: referencing Newey-West 1994 REStud 61(4):631-653
// define h indicator rowvector
        h = J(nrows1,1,1) \ J(nrows2,1,0)
        
// calc mstar per p.43
// Hannan (1971, 296) & Priestley (1981, 58) per Newey-West p. 633
// corrected per Alistair Hall msg to Brian Poi 17jul2008
//      T = rows(uZ)
//      oneT = 1/T
        expo = 2/9
        q = 1
//      cgamma = 1.4117
        cgamma = 1.1447
        if(kernel == "Parzen") { 
                expo = 4/25
                q = 2
                cgamma = 2.6614
        }
// cfb B102
        if(kernel == "Quadratic Spectral") {
                expo = 2/25
                q = 2
                cgamma = 1.3221
        }
// per Newey-West p.639, Anderson (1971), Priestley (1981) may provide
// guidance on setting expo for other kernels
//      mstar = trunc(20 *(T/100)^expo)
// use time span of data (not number of obs)
        mstar = trunc(20 *(tobs/100)^expo)

// calc uZ matrix
        u = uZ[.,1]
        Z = uZ[|1,2 \.,.|]
                
// calc f vector: (u_i Z_i) * h
        f =  (u :* Z) * h

// approach allows for gaps in time series
        sigmahat = J(mstar+1,1,0)
        for(j=0;j<=mstar;j++) {
                lsj = "L"+strofreal(j)
                tlag=st_data(., lsj+"."+tindexname)
                tmatrix = tnow, tlag
                svar=(tnow:<.):*(tlag:<.)               // multiply column vectors of 1s and 0s
                tmatrix=select(tmatrix,svar)    // to get intersection, and replace tmatrix
                                                                                // now calculate autocovariance; divide by nobs
                sigmahat[j+1] = quadcross(f[tmatrix[.,1],.], f[tmatrix[.,2],.]) / nobs
        }

// calc shat(q), shat(0)
        shatq = 0
        shat0 = sigmahat[1]
        for(j=1;j<=mstar;j++) {
                shatq = shatq + 2 * sigmahat[j+1] * j^q
                shat0 = shat0 + 2 * sigmahat[j+1]
        }

// calc gammahat
        expon = 1/(2*q+1)
        gammahat = cgamma*( (shatq/shat0)^2 )^expon
// use time span of data tobs (not number of obs T)
                m = gammahat * tobs^expon

// calc opt lag
        if(kernel == "Bartlett" | kernel == "Parzen") {
                optlag = min((trunc(m),mstar))
        }
        else if(kernel == "Quadratic Spectral") {
                optlag = min((m,mstar))
        }
                
// if optlag is the optimal lag to be used, we need to add one to 
// specify bandwidth in ivreg2 terms
        abw = optlag + 1
        st_local("abw",strofreal(abw))
} // end program s_abw


// *********** s_rmcoll2 (replacement for Stata _rmcollright etc. **********

void s_rmcoll2( string scalar fv_vnames,
                                string scalar vnames,
                                string scalar wname,
                                string scalar touse,
                                scalar cons,
                                scalar lindep)
{
        st_view(X=., ., tokens(fv_vnames), touse)
        st_view(w=., ., tokens(wname), touse)
        st_view(mtouse=., ., tokens(touse), touse)

        if (cons) {
                Xmean=mean(X,w)
                XX=quadcrossdev(X,Xmean, w, X,Xmean)
        }
        else {
                XX=quadcross(X, w, X)
        }

        XXinv=invsym(XX, range(1,cols(X),1))

        st_numscalar("r(k_omitted)", diag0cnt(XXinv))
        if (lindep) {
                st_matrix("r(lindep)", XX*XXinv)
        }
        smat = (diagonal(XXinv) :== 0)'
        vl=tokens(vnames)
        vl_drop = select(vl, smat)
        vl_keep = select(vl, (1 :- smat))

        if (cols(vl_keep)>0) {
                st_global("r(varlist)", invtokens(vl_keep))
        }
        if (cols(vl_drop)>0) {
                st_global("r(omitted)", invtokens(vl_drop))
        }
}       // end program s_rmcoll2


// ************** Add omitted Mata utility ************************

void s_AddOmitted(      string scalar bname,
                                        string scalar vname,
                                        string scalar cnumlist,
                                        scalar eq_ct,
                                        scalar rhs0_ct,
                                        scalar rhs1_ct)

{
        b = st_matrix(bname)
        V = st_matrix(vname)
        cn = strtoreal(tokens(cnumlist))
// cnumlist is the list of columns in the single-equation new big matrix in which
// the non-zero entries from the reduced matrix (bmat or vmat) will appear.
// E.g., if newb will be [mpg o.mpg2 _cons] then cnum = [1 3].
        col_ct = eq_ct * rhs0_ct
        
        newb = J(1,col_ct,0)
        newV = J(col_ct,col_ct,0)
        
// Code needs to accommodate multi-equation case.  Since all equations will have
// same reduced and full list of vars, in the same order, can do this with Kronecker
// products etc.  Second term below is basically the offset for each equation.
        cn = (J(1,eq_ct,1) # cn) + ((range(0,eq_ct-1,1)' # J(1,rhs1_ct,1) ) * rhs0_ct)

// Insert the values from the reduced matrices into the right places in the big matrices.
        newb[1, cn] = b
        newV[cn, cn] = V
        
        st_matrix("r(b)", newb)
        st_matrix("r(V)", newV)
        
}


// ************** Partial out *************************************

void s_partial(         string scalar yname,
                                        string scalar X1names,
                                        string scalar X2names,
                                        string scalar Z1names,
                                        string scalar Pnames,
                                        string scalar touse,
                                        string scalar weight,
                                        string scalar wvarname,
                                        scalar wf,
                                        scalar N,
                                        scalar cons)                            

{

// All varnames should be basic form, no FV or TS operators etc.
//  y = dep var
// X1 = endog regressors
// X2 = exog regressors = included IVs
// Z1 = excluded instruments
// Z2 = included IVs = X2
// PZ = variables to partial out
// cons = 0 or 1

        ytoken=tokens(yname)
        X1tokens=tokens(X1names)
        X2tokens=tokens(X2names)
        Z1tokens=tokens(Z1names)
        Ptokens=tokens(Pnames)
        Ytokens = (ytoken, X1tokens, X2tokens, Z1tokens)

        st_view(wvar, ., st_tsrevar(wvarname), touse)
        st_view(Y, ., Ytokens, touse)
        st_view(P, ., Ptokens, touse)
        L = cols(P)

        if (cons & L>0) {                                       //  Vars to partial out including constant
                Ymeans = mean(Y,wf*wvar)
                Pmeans = mean(P,wf*wvar)
                PY = quadcrossdev(P, Pmeans, wf*wvar, Y, Ymeans)
                PP = quadcrossdev(P, Pmeans, wf*wvar, P, Pmeans)
        }
        else if (!cons & L>0) {                         //  Vars to partial out NOT including constant
                PY = quadcross(P, wf*wvar, Y)
                PP = quadcross(P, wf*wvar, P)
        }
        else {                                                          //  Only constant to partial out = demean
                Ymeans = mean(Y,wf*wvar)
        }               

//      Partial-out coeffs. Default Cholesky; use QR if not full rank and collinearities present.
//      Not necessary if no vars other than constant
        if (L>0) {
                b = cholqrsolve(PP, PY)
        }
//      Replace with residuals
        if (cons & L>0) {                                       //  Vars to partial out including constant
                Y[.,.] = (Y :- Ymeans) - (P :- Pmeans)*b
        }
        else if (!cons & L>0) {                         //  Vars to partial out NOT including constant
                Y[.,.] = Y - P*b
        }
        else {                                                          //  Only constant to partial out = demean
                Y[.,.] = (Y :- Ymeans)
        }

} // end program s_partial



// ************** Common cross-products *************************************

void s_crossprods(      string scalar yname,
                                        string scalar X1names,
                                        string scalar X2names,
                                        string scalar Z1names,
                                        string scalar touse,
                                        string scalar weight,
                                        string scalar wvarname,
                                        scalar wf,
                                        scalar N)                               

{

//  y = dep var
// X1 = endog regressors
// X2 = exog regressors = included IVs
// Z1 = excluded instruments
// Z2 = included IVs = X2

        ytoken=tokens(yname)
        X1tokens=tokens(X1names)
        X2tokens=tokens(X2names)
        Z1tokens=tokens(Z1names)

        Xtokens = (X1tokens, X2tokens)
        Ztokens = (Z1tokens, X2tokens)

        K1=cols(X1tokens)
        K2=cols(X2tokens)
        K=K1+K2
        L1=cols(Z1tokens)
        L2=cols(X2tokens)
        L=L1+L2

        st_view(wvar, ., st_tsrevar(wvarname), touse)
        st_view(A, ., st_tsrevar((ytoken, Xtokens, Z1tokens)), touse)

        AA = quadcross(A, wf*wvar, A)

        if (K>0) {
                XX = AA[(2::K+1),(2..K+1)]
                Xy  = AA[(2::K+1),1]
        }
        if (K1>0) {
                X1X1 = AA[(2::K1+1),(2..K1+1)]
        }

        if (L1 > 0) {
                Z1Z1 = AA[(K+2::rows(AA)),(K+2..rows(AA))]
        }

        if (L2 > 0) {
                Z2Z2 = AA[(K1+2::K+1), (K1+2::K+1)]
                Z2y  = AA[(K1+2::K+1), 1]
        }

        if ((L1>0) & (L2>0)) {
                Z2Z1 = AA[(K1+2::K+1), (K+2::rows(AA))]
                ZZ2 = Z2Z1, Z2Z2
                ZZ1 = Z1Z1, Z2Z1'
                ZZ = ZZ1 \ ZZ2
        }
        else if (L1>0) {
                ZZ = Z1Z1
        }
        else {
// L1=0
                ZZ  = Z2Z2
                ZZ2 = Z2Z2
        }

        if ((K1>0) & (L1>0)) {                                          // K1>0, L1>0
                X1Z1 = AA[(2::K1+1), (K+2::rows(AA))]
        }

        if ((K1>0) & (L2>0)) {
                X1Z2 = AA[(2::K1+1), (K1+2::K+1)]
                if (L1>0) {                                                             // K1>0, L1>0, L2>0
                        X1Z = X1Z1, X1Z2
                        XZ = X1Z \ ZZ2
                }
                else {                                                                  // K1>0, L1=0, L2>0
                        XZ = X1Z2 \ ZZ2
                        X1Z = X1Z2
                }
        }
        else if (K1>0) {                                                        // K1>0, L2=0
                XZ = X1Z1
                X1Z= X1Z1
        }
        else if (L1>0) {                                                        // K1=0, L2>0
                XZ = AA[(2::K+1),(K+2..rows(AA))], AA[(2::K+1),(2..K+1)]
        }
        else {                                                                          // K1=0, L2=0
                XZ = ZZ
        }

        if ((L1>0) & (L2>0)) {
                Zy = AA[(K+2::rows(AA)), 1] \ AA[(K1+2::K+1), 1]
                ZY = AA[(K+2::rows(AA)), (1..K1+1)] \ AA[(K1+2::K+1), (1..K1+1)]
                Z2Y = AA[(K1+2::K+1), (1..K1+1)]
        }
        else if (L1>0) {
                Zy = AA[(K+2::rows(AA)), 1]
                ZY = AA[(K+2::rows(AA)), (1..K1+1)]
        }
        else if (L2>0) {
                Zy = AA[(K1+2::K+1), 1]
                ZY = AA[(K1+2::K+1), (1..K1+1)]
                Z2Y = ZY
        }
// Zy, ZY, Z2Y not created if L1=L2=0

        YY  = AA[(1::K1+1), (1..K1+1)]
        yy  = AA[1,1]
        st_subview(y, A, ., 1)
        ym    = sum(wf*wvar:*y)/N
        yyc   = quadcrossdev(y, ym, wf*wvar, y, ym)

        XXinv = invsym(XX)
        if (Xtokens==Ztokens) {
                ZZinv = XXinv
                XPZXinv = XXinv
        }
        else {
                ZZinv = invsym(ZZ)
                XPZX  = makesymmetric(XZ*ZZinv*XZ')
                XPZXinv=invsym(XPZX)
        }

// condition numbers
        condxx=cond(XX)
        condzz=cond(ZZ)

        st_matrix("r(XX)", XX)
        st_matrix("r(X1X1)", X1X1)
        st_matrix("r(X1Z)", X1Z)
        st_matrix("r(ZZ)", ZZ)
        st_matrix("r(Z2Z2)", Z2Z2)
        st_matrix("r(Z1Z2)", Z2Z1')
        st_matrix("r(Z2y)",Z2y)
        st_matrix("r(XZ)", XZ)
        st_matrix("r(Xy)", Xy)
        st_matrix("r(Zy)", Zy)
        st_numscalar("r(yy)", yy)
        st_numscalar("r(yyc)", yyc)
        st_matrix("r(YY)", YY)
        st_matrix("r(ZY)", ZY)
        st_matrix("r(Z2Y)", Z2Y)
        st_matrix("r(XXinv)", XXinv)
        st_matrix("r(ZZinv)", ZZinv)
        st_matrix("r(XPZXinv)", XPZXinv)
        st_numscalar("r(condxx)",condxx)
        st_numscalar("r(condzz)",condzz)

} // end program s_crossprods


// *************** 1st step GMM ******************** //
// Can be either efficient or inefficient.
// Can be IV or other 1-step GMM estimator.

void s_gmm1s(   string scalar ZZmatrix,
                                string scalar XXmatrix,
                                string scalar XZmatrix,
                                string scalar Zymatrix,
                                string scalar ZZinvmatrix,
                                string scalar yname,
                                string scalar ename,
                                string scalar Xnames, 
                                string scalar Znames, 
                                string scalar touse,
                                string scalar weight,
                                string scalar wvarname,
                                scalar wf,
                                scalar N,
                                string scalar Wmatrix,
                                string scalar Smatrix,
                                scalar dofminus,
                                scalar efficient,                       //  flag to indicate that 1st-step GMM is efficient
                                scalar overid,                          //  not guaranteed to be right if nocollin option used!
                                scalar useqr)                           //  flag to force use of QR instead of Cholesky solver
{

        Ztokens=tokens(Znames)
        Xtokens=tokens(Xnames)

        st_view(Z,    ., st_tsrevar(Ztokens),  touse)
        st_view(X,    ., st_tsrevar(Xtokens),  touse)
        st_view(y,    ., st_tsrevar(yname),  touse)
        st_view(e,    ., ename,  touse)
        st_view(wvar, ., st_tsrevar(wvarname), touse)

// Our convention is that regressors are [endog   included exog]
// and instruments are                   [excluded exog  included exog]
// If a constant is included, it is the last column.

        ZZ = st_matrix(ZZmatrix)
        XX = st_matrix(XXmatrix)
        XZ = st_matrix(XZmatrix)
        Zy = st_matrix(Zymatrix)
        ZZinv = st_matrix(ZZinvmatrix)

        QZZ    = ZZ   / N
        QXX    = XX   / N
        QXZ    = XZ   / N
        QZy    = Zy   / N
        QZZinv = ZZinv*N
        
        useqr = (diag0cnt(QZZinv)>0) | useqr

// Weighting matrix supplied (and inefficient GMM)
        if (Wmatrix~="") {
                W = st_matrix(Wmatrix)
                useqr = (diag0cnt(W)>0) | useqr
        }
// Var-cov matrix of orthog conditions supplied
        if (Smatrix~="") {
                omega=st_matrix(Smatrix)
                useqr = (diag0cnt(omega)>0) | useqr
        }

        if (efficient) {                                                                        //  Efficient 1-step GMM block: OLS, IV or provided S
                if ((Xtokens==Ztokens) & (Smatrix=="")) {               //  OLS

                        beta = cholqrsolve(QZZ, QZy, useqr)
                        beta = beta'
                        e[.,.] = y - X * beta'                                          //  update residuals
                        ee = quadcross(e, wf*wvar, e)
                        sigmasq=ee/(N-dofminus)
                        omega = sigmasq * QZZ
                        W = 1/sigmasq * QZZinv
                        V = 1/N * sigmasq * QZZinv
                        rankS = rows(omega) - diag0cnt(QZZinv)          //  inv(omega) is proportional to inv(QZZ)
                        rankV = rows(V) - diag0cnt(V)                           //  inv(V) is proportional to inv(QZZ)
                }
                else if (Smatrix=="") {                                                 //  IV
                        aux1 = cholqrsolve(QZZ, QXZ', useqr)
                        aux2 = cholqrsolve(QZZ, QZy, useqr)
                        aux3 = makesymmetric(QXZ * aux1)
                        beta = cholqrsolve(aux3, QXZ * aux2, useqr)
                        beta = beta'
                        e[.,.] = y - X * beta'                                          //  update residuals
                        ee = quadcross(e, wf*wvar, e)
                        sigmasq = ee/(N-dofminus)
                        omega = sigmasq * QZZ
                        W = 1/sigmasq * QZZinv
                        V = 1/N * sigmasq * invsym(aux3)
                        rankS = rows(omega) - diag0cnt(QZZinv)          //  inv(omega) is proportional to inv(QZZ)
                        rankV = rows(V) - diag0cnt(V)                           //  V is proportional to inv(aux3)
                }
                else {                                                                                  //  efficient GMM with provided S (=omega)
                        aux1 = cholqrsolve(omega, QXZ', useqr)
                        aux2 = cholqrsolve(omega, QZy, useqr)
                        aux3 = makesymmetric(QXZ * aux1)
                        beta = cholqrsolve(aux3, QXZ * aux2, useqr)
                        beta = beta'
                        e[.,.] = y - X * beta'                                          //  update residuals
                        ee = quadcross(e, wf*wvar, e)
                        sigmasq=ee/(N-dofminus)
                        W = invsym(omega)
                        V = 1/N * invsym(aux3)                                          //  Normalize by N
                        rankS = rows(omega) - diag0cnt(W)                       //  since W=inv(omega)
                        rankV = rows(V) - diag0cnt(V)                           //  since V is prop to inv(aux3)
                }
                if (overid) {                                                                   // J if overidentified
                        Ze = quadcross(Z, wf*wvar, e)
                        gbar = Ze / N
                        aux4 = cholqrsolve(omega, gbar, useqr)
                        j = N * gbar' * aux4
                }
                else {
                        j=0
                }
                st_matrix("r(beta)", beta)
                st_matrix("r(V)", V)
                st_matrix("r(S)", omega)
                st_matrix("r(W)", W)
                st_numscalar("r(rss)", ee)
                st_numscalar("r(j)", j)
                st_numscalar("r(sigmasq)", sigmasq)
                st_numscalar("r(rankS)", rankS)
                st_numscalar("r(rankV)", rankV)
        }
        else {                                                                                          //  inefficient 1st-step GMM; don't need V, S, j etc.
                if ((Xtokens==Ztokens) & (Wmatrix=="")) {               //  OLS
                        beta = cholqrsolve(QZZ, QZy, useqr)
                        beta = beta'
                        e[.,.] = y - X * beta'                                          //  update residuals
                        ee = quadcross(e, wf*wvar, e)
                        sigmasq=ee/(N-dofminus)
                        W = 1/sigmasq * QZZinv
                        QXZ_W_QZX = 1/sigmasq * QZZ                                     //  b/c W incorporates sigma^2
                }
                else if (Wmatrix=="") {                                                 //  IV
                        aux1 = cholqrsolve(QZZ, QXZ', useqr)
                        aux2 = cholqrsolve(QZZ, QZy, useqr)
                        aux3 = makesymmetric(QXZ * aux1)
                        beta = cholqrsolve(aux3, QXZ * aux2, useqr)
                        beta = beta'
                        e[.,.] = y - X * beta'                                          //  update residuals
                        ee = quadcross(e, wf*wvar, e)
                        sigmasq=ee/(N-dofminus)
                        W = 1/sigmasq * QZZinv
                        QXZ_W_QZX = 1/sigmasq * aux3                            //  b/c IV weighting matrix incorporates sigma^2
                }
                else {                                                                                  //  some other 1st step inefficient GMM with provided W
                        QXZ_W_QZX = QXZ * W * QXZ'
                        _makesymmetric(QXZ_W_QZX)
                        beta = cholqrsolve(QXZ_W_QZX, QXZ * W * QZy, useqr)
                        beta = beta'
                        e[.,.] = y - X * beta'                                          //  update residuals
                }
                st_matrix("r(QXZ_W_QZX)", QXZ_W_QZX)
                st_matrix("r(beta)", beta)
                st_matrix("r(W)",W)                                                             //  always return W
        }

} // end program s_gmm1s


// *************** efficient GMM ******************** //
// Uses inverse of provided S matrix as weighting matrix.
// IV won't be done here but code would work for it as a special case.

void s_egmm(    string scalar ZZmatrix,
                                string scalar XXmatrix,
                                string scalar XZmatrix,
                                string scalar Zymatrix,
                                string scalar ZZinvmatrix,
                                string scalar yname,
                                string scalar ename,
                                string scalar Xnames, 
                                string scalar Znames, 
                                string scalar touse,
                                string scalar weight,
                                string scalar wvarname,
                                scalar wf,
                                scalar N,
                                string scalar Smatrix,                                  //  always provided
                                scalar dofminus,
                                scalar overid,                                                  //  not guaranteed to be right if -nocollin- used!
                                scalar useqr)
{

        Ztokens=tokens(Znames)
        Xtokens=tokens(Xnames)

        st_view(Z,    ., st_tsrevar(Ztokens),  touse)
        st_view(X,    ., st_tsrevar(Xtokens),  touse)
        st_view(y,    ., st_tsrevar(yname),  touse)
        st_view(e,    ., ename,  touse)
        st_view(wvar, ., st_tsrevar(wvarname), touse)

// Our convention is that regressors are [endog   included exog]
// and instruments are                   [excluded exog  included exog]
// If a constant is included, it is the last column.

        ZZ                      = st_matrix(ZZmatrix)
        XX                      = st_matrix(XXmatrix)
        XZ                      = st_matrix(XZmatrix)
        Zy                      = st_matrix(Zymatrix)
        ZZinv           = st_matrix(ZZinvmatrix)

        QZZ    = ZZ   / N
        QXX    = XX   / N
        QXZ    = XZ   / N
        QZy    = Zy   / N
        QZZinv = ZZinv*N

// Var-cov matrix of orthog conditions supplied
        omega=st_matrix(Smatrix)
        W = invsym(omega)                                                       //  Efficient GMM weighting matrix
        rankS = rows(omega) - diag0cnt(W)                       //  since W=inv(omega)
        
        if (rankS<rows(omega)) {                                        //  omega not full rank; W=inv(omega) dubious, exit with error
errprintf("\nError: estimated covariance matrix of moment conditions not of full rank,")
errprintf("\n       and optimal GMM weighting matrix not unique.")
errprintf("\nPossible causes:")
errprintf("\n       singleton dummy variable (dummy with one 1 and N-1 0s or vice versa)")
errprintf("\n       {help ivreg2##partial:partial} option may address problem.\n")
                exit(506)
        }

        aux1 = cholqrsolve(omega, QXZ', useqr)
        aux2 = cholqrsolve(omega, QZy, useqr)
        aux3 = makesymmetric(QXZ * aux1)
        beta = cholqrsolve(aux3, QXZ * aux2, useqr)
        beta = beta'

// The GMM estimator is "root-N consistent", and technically we do
// inference on sqrt(N)*beta.  By convention we work with beta,
// so we adjust the var-cov matrix instead:
        V = 1/N * invsym(aux3)
        rankV = rows(V) - diag0cnt(V)           //  since V is proportional to inv(aux3)

//      above equivalent to but more accurate than:
//      W = invsym(omega) or W = QZZinv
//      QXZ_W_QZX = QXZ * W * QXZ'
//      QXZ_W_QZXinv=invsym(makesymmetric(QXZ_W_QZX))
//      beta = (QXZ_W_QZXinv * QXZ * W * QZy)
//      V = QXZ_W_QZXinv

        e[.,.] = y - X * beta'
        ee = quadcross(e, wf*wvar, e)
        sigmasq=ee/(N-dofminus)

// J if overidentified
        if (cols(Z) > cols(X)) {
                Ze = quadcross(Z, wf*wvar, e)
                gbar = Ze / N
                aux4 = cholqrsolve(omega, gbar, useqr)
                j = N * gbar' * aux4
        }
        else {
                j=0
        }

        st_matrix("r(beta)", beta)
        st_matrix("r(V)", V)
        st_matrix("r(W)", W)
        st_numscalar("r(rss)", ee)
        st_numscalar("r(j)", j)
        st_numscalar("r(sigmasq)", sigmasq)
        st_numscalar("r(rankV)",rankV)
        st_numscalar("r(rankS)",rankS)

} // end program s_egmm

// *************** inefficient GMM ******************** //

void s_iegmm(   string scalar ZZmatrix,
                                string scalar XXmatrix,
                                string scalar XZmatrix,
                                string scalar Zymatrix,
                                string scalar QXZ_W_QZXmatrix,
                                string scalar yname,
                                string scalar ename,
                                string scalar Xnames, 
                                string scalar Znames, 
                                string scalar touse,
                                string scalar weight,
                                string scalar wvarname,
                                scalar wf,
                                scalar N,
                                string scalar Wmatrix,
                                string scalar Smatrix,
                                string scalar bname,
                                scalar dofminus,
                                scalar overid,
                                scalar useqr)
{

        Ztokens=tokens(Znames)
        Xtokens=tokens(Xnames)

        st_view(Z,    ., st_tsrevar(Ztokens),  touse)
        st_view(X,    ., st_tsrevar(Xtokens),  touse)
        st_view(y,    ., st_tsrevar(yname),  touse)
        st_view(e,    ., ename,  touse)
        st_view(wvar, ., st_tsrevar(wvarname), touse)

// Our convention is that regressors are [endog   included exog]
// and instruments are                   [excluded exog  included exog]
// If a constant is included, it is the last column.

        QZZ                     = st_matrix(ZZmatrix) / N
        QXX                     = st_matrix(XXmatrix) / N
        QXZ                     = st_matrix(XZmatrix) / N
        QZy                     = st_matrix(Zymatrix) / N
        QXZ_W_QZX       = st_matrix(QXZ_W_QZXmatrix)

        useqr = (diag0cnt(QXZ_W_QZX)>0) | useqr

// beta is supplied
        beta = st_matrix(bname)

// Inefficient weighting matrix supplied
        W = st_matrix(Wmatrix)

// Var-cov matrix of orthog conditions supplied
        omega=st_matrix(Smatrix)

// Residuals are supplied
        ee = quadcross(e, wf*wvar, e)
        sigmasq=ee/(N-dofminus)

// Calculate V and J.

// V
// The GMM estimator is "root-N consistent", and technically we do
// inference on sqrt(N)*beta.  By convention we work with beta, so we adjust
// the var-cov matrix instead:
        aux5 = cholqrsolve(QXZ_W_QZX, QXZ * W, useqr)
        V = 1/N * aux5 * omega * aux5'
        _makesymmetric(V)

// alternative
//      QXZ_W_QZXinv=invsym(QXZ_W_QZX)
//      V = 1/N * QXZ_W_QZXinv * QXZ * W * omega * W * QXZ' * QXZ_W_QZXinv

        rankV = rows(V) - diag0cnt(invsym(V))                           //  need explicitly to calc rank
        rankS = rows(omega) - diag0cnt(invsym(omega))           //  need explicitly to calc rank

// J if overidentified
        if (overid) {
// Note that J requires efficient GMM residuals, which means do 2-step GMM to get them.
//              QXZ_W2s_QZX = QXZ * W2s * QXZ'
//              _makesymmetric(QXZ_W2s_QZX)
//              QXZ_W2s_QZXinv=invsym(QXZ_W2s_QZX)
//              beta2s = (QXZ_W2s_QZXinv * QXZ * W2s * QZy)
                aux1 = cholqrsolve(omega, QXZ', useqr)
                aux2 = cholqrsolve(omega, QZy, useqr)
                aux3s = makesymmetric(QXZ * aux1)
                beta2s = cholqrsolve(aux3s, QXZ * aux2, useqr)
                beta2s = beta2s'
                e2s = y - X * beta2s'
                Ze2s = quadcross(Z, wf*wvar, e2s)
                gbar = Ze2s / N
                aux4 = cholqrsolve(omega, gbar, useqr)
                j = N * gbar' * aux4
        }
        else {
                j=0
        }

        st_matrix("r(V)", V)
        st_numscalar("r(j)", j)
        st_numscalar("r(rss)", ee)
        st_numscalar("r(sigmasq)", sigmasq)
        st_numscalar("r(rankV)",rankV)
        st_numscalar("r(rankS)",rankS)

} // end program s_iegmm

// *************** LIML ******************** //

void s_liml(    string scalar ZZmatrix,
                                string scalar XXmatrix,
                                string scalar XZmatrix,
                                string scalar Zymatrix,
                                string scalar Z2Z2matrix,
                                string scalar YYmatrix,
                                string scalar ZYmatrix,
                                string scalar Z2Ymatrix,
                                string scalar Xymatrix,
                                string scalar ZZinvmatrix,
                                string scalar yname,
                                string scalar Ynames,
                                string scalar ename,
                                string scalar Xnames,
                                string scalar X1names,
                                string scalar Znames,
                                string scalar Z1names,
                                string scalar Z2names,
                                scalar fuller,
                                scalar kclass,
                                string scalar coviv,
                                string scalar touse,
                                string scalar weight,
                                string scalar wvarname,
                                scalar wf,
                                scalar N,
                                string scalar robust,
                                string scalar clustvarname,
                                string scalar clustvarname2,
                                string scalar clustvarname3,
                                scalar bw,
                                string scalar kernel,
                                string scalar sw,
                                string scalar psd,
                                string scalar ivarname,
                                string scalar tvarname,
                                string scalar tindexname,
                                scalar tdelta,
                                scalar center,
                                scalar dofminus,
                                scalar useqr)

{
        struct ms_vcvorthog scalar vcvo

        vcvo.ename                      = ename
        vcvo.Znames                     = Znames
        vcvo.touse                      = touse
        vcvo.weight                     = weight
        vcvo.wvarname           = wvarname
        vcvo.robust                     = robust
        vcvo.clustvarname       = clustvarname
        vcvo.clustvarname2      = clustvarname2
        vcvo.clustvarname3      = clustvarname3
        vcvo.kernel                     = kernel
        vcvo.sw                         = sw
        vcvo.psd                        = psd
        vcvo.ivarname           = ivarname
        vcvo.tvarname           = tvarname
        vcvo.tindexname         = tindexname
        vcvo.wf                         = wf
        vcvo.N                          = N
        vcvo.bw                         = bw
        vcvo.tdelta                     = tdelta
        vcvo.center                     = center
        vcvo.dofminus           = dofminus
        vcvo.ZZ                         = st_matrix(ZZmatrix)


// X1 = endog regressors
// X2 = exog regressors = included IVs
// Z1 = excluded instruments
// Z2 = included IVs = X2

        Ytokens=tokens(Ynames)
        Ztokens=tokens(Znames)
        Z1tokens=tokens(Z1names)
        Z2tokens=tokens(Z2names)
        Xtokens=tokens(Xnames)
        X1tokens=tokens(X1names)

        st_view(Z,     ., st_tsrevar(Ztokens),   touse)
        st_view(X,     ., st_tsrevar(Xtokens),   touse)
        st_view(y,     ., st_tsrevar(yname),     touse)
        st_view(e,     ., ename,                 touse)
        st_view(wvar,  ., st_tsrevar(wvarname),  touse)

        vcvo.e          = &e
        vcvo.Z          = &Z
        vcvo.wvar       = &wvar

// Our convention is that regressors are [endog   included exog]
// and instruments are                   [excluded exog  included exog]
// If a constant is included, it is the last column.

        QZZ             = st_matrix(ZZmatrix) / N
        QXX             = st_matrix(XXmatrix) / N
        QXZ             = st_matrix(XZmatrix) / N
        QZy             = st_matrix(Zymatrix) / N
        QZ2Z2   = st_matrix(Z2Z2matrix) / N
        QYY             = st_matrix(YYmatrix) / N
        QZY             = st_matrix(ZYmatrix) / N
        QZ2Y    = st_matrix(Z2Ymatrix) / N
        QXy             = st_matrix(Xymatrix) / N
        QZZinv  = st_matrix(ZZinvmatrix)*N

        useqr = (diag0cnt(QZZ)>0) | useqr

// kclass=0 => LIML or Fuller LIML so calculate lambda
        if (kclass == 0) {
                aux1 = cholqrsolve(QZZ, QZY, useqr)
                QWW = QYY - QZY'*aux1
                _makesymmetric(QWW)
                if (cols(Z2tokens) > 0) {
                        aux2 = cholqrsolve(QZ2Z2, QZ2Y, useqr)
                        QWW1 = QYY - QZ2Y'*aux2
                        _makesymmetric(QWW1)
                }
                else {
// Special case of no exogenous regressors
                        QWW1 = QYY
                }
                M=matpowersym(QWW, -0.5)
                Eval=symeigenvalues(M*QWW1*M)
                lambda=rowmin(Eval)
        }

// Exactly identified but might not be exactly 1, so make it so
        if (cols(Z)==cols(X)) {
                lambda=1
        }

        if (fuller > (N-cols(Z))) {
printf("\n{error:Error: invalid choice of Fuller LIML parameter.}\n")
                exit(error(3351))
        }
        else if (fuller > 0) {
                k = lambda - fuller/(N-cols(Z))
        }
        else if (kclass > 0) {
                k = kclass
        }
        else {
                k = lambda
        }

        aux3 = cholqrsolve(QZZ, QXZ', useqr)
        QXhXh=(1-k)*QXX + k*QXZ*aux3
        _makesymmetric(QXhXh)
        aux4 = cholqrsolve(QZZ, QZy, useqr)
        aux5 = cholqrsolve(QXhXh, QXZ, useqr)
        aux6 = cholqrsolve(QXhXh, QXy, useqr)
        beta = aux6*(1-k) + k*aux5*aux4
        beta = beta'

        e[.,.] = y - X * beta'
        ee = quadcross(e, wf*wvar, e)
        sigmasq = ee /(N-dofminus)

        omega = m_omega(vcvo)

        QXhXhinv=invsym(QXhXh)

        if ((robust=="") & (clustvarname=="") & (kernel=="")) {
// Efficient LIML
                if (coviv=="") {
// Note dof correction is already in sigmasq
                        V = 1/N * sigmasq * QXhXhinv
                        rankV = rows(V) - diag0cnt(V)           //  since V is proportional to inv(QXhXh)
                }
                else {
                        aux7 = makesymmetric(QXZ * aux3)
                        V = 1/N * sigmasq * invsym(aux7)
                        rankV = rows(V) - diag0cnt(V)           //  since V is proportional to inv(aux7)
                }
                rankS = rows(omega) - diag0cnt(invsym(omega))
                if (cols(Z)>cols(X)) {
                        Ze = quadcross(Z, wf*wvar, e)
                        gbar = Ze / N
                        aux8 = cholqrsolve(omega, gbar, useqr)
                        j = N * gbar' * aux8
                }
                else {
                        j=0
                }
        }
        else {
// Inefficient LIML
                if (coviv=="") {
                        aux9 = cholqrsolve(QZZ, aux5', useqr)
                        V = 1/N * aux9' * omega * aux9
                        _makesymmetric(V)
                        rankV = rows(V) - diag0cnt(invsym(V))                           // need explicitly to calc rank
                        rankS = rows(omega) - diag0cnt(invsym(omega))           // need explicitly to calc rank
                }
                else {
                        aux10 = QXZ * aux3
                        _makesymmetric(aux10)
                        aux11 = cholqrsolve(aux10, aux3', useqr)
                        V = 1/N * aux11 * omega * aux11'
                        _makesymmetric(V)
                        rankV = rows(V) - diag0cnt(invsym(V))                           // need explicitly to calc rank
                        rankS = rows(omega) - diag0cnt(invsym(omega))           // need explicitly to calc rank
                }
                if (cols(Z)>cols(X)) {
                        aux12 = cholqrsolve(omega, QXZ', useqr)
                        aux13 = cholqrsolve(omega, QZy, useqr)
                        aux14 = makesymmetric(QXZ * aux12)
                        beta2s = cholqrsolve(aux14, QXZ * aux13, useqr)
                        beta2s = beta2s'
                        e2s = y - X * beta2s'
                        Ze2s = quadcross(Z, wf*wvar, e2s)
                        gbar = Ze2s / N
                        aux15 = cholqrsolve(omega, gbar, useqr)
                        j = N * gbar' * aux15
                }
                else {
                        j=0
                }
        }
        _makesymmetric(V)

        st_matrix("r(beta)", beta)
        st_matrix("r(S)", omega)
        st_matrix("r(V)", V)
        st_numscalar("r(lambda)", lambda)
        st_numscalar("r(kclass)", k)
        st_numscalar("r(j)", j)
        st_numscalar("r(rss)", ee)
        st_numscalar("r(sigmasq)", sigmasq)
        st_numscalar("r(rankV)",rankV)
        st_numscalar("r(rankS)",rankS)

} // end program s_liml


// *************** CUE ******************** //

void s_gmmcue(  string scalar ZZmatrix,
                                string scalar XZmatrix,
                                string scalar yname,
                                string scalar ename,
                                string scalar Xnames, 
                                string scalar Znames, 
                                string scalar touse,
                                string scalar weight,
                                string scalar wvarname,
                                scalar wf,
                                scalar N,
                                string scalar robust,
                                string scalar clustvarname,
                                string scalar clustvarname2,
                                string scalar clustvarname3,
                                scalar bw,
                                string scalar kernel,
                                string scalar sw,
                                string scalar psd,
                                string scalar ivarname,
                                string scalar tvarname,
                                string scalar tindexname,
                                scalar tdelta,
                                string scalar bname,
                                string scalar b0name,
                                scalar center,
                                scalar dofminus,
                                scalar useqr)

{

        struct ms_vcvorthog scalar vcvo

        vcvo.ename                      = ename
        vcvo.Znames                     = Znames
        vcvo.touse                      = touse
        vcvo.weight                     = weight
        vcvo.wvarname           = wvarname
        vcvo.robust                     = robust
        vcvo.clustvarname       = clustvarname
        vcvo.clustvarname2      = clustvarname2
        vcvo.clustvarname3      = clustvarname3
        vcvo.kernel                     = kernel
        vcvo.sw                         = sw
        vcvo.psd                        = psd
        vcvo.ivarname           = ivarname
        vcvo.tvarname           = tvarname
        vcvo.tindexname         = tindexname
        vcvo.wf                         = wf
        vcvo.N                          = N
        vcvo.bw                         = bw
        vcvo.tdelta                     = tdelta
        vcvo.center                     = center
        vcvo.dofminus           = dofminus
        vcvo.ZZ                         = st_matrix(ZZmatrix)

        Ztokens=tokens(Znames)
        Xtokens=tokens(Xnames)

        st_view(Z,    ., st_tsrevar(Ztokens),  touse)
        st_view(X,    ., st_tsrevar(Xtokens),  touse)
        st_view(y,    ., st_tsrevar(yname),    touse)
        st_view(e,    ., ename,                touse)
        st_view(wvar, ., st_tsrevar(wvarname), touse)

// Pointers to views
        vcvo.e          = &e
        vcvo.Z          = &Z
        vcvo.wvar       = &wvar
        py                      = &y
        pX                      = &X

        if (b0name=="") {

// CUE beta not supplied, so calculate/optimize

// Our convention is that regressors are [endog   included exog]
// and instruments are                   [excluded exog  included exog]
// If a constant is included, it is the last column.

// CUE is preceded by IV or 2-step GMM to get starting values.
// Stata convention is that parameter vectors are row vectors, and optimizers
// require this, so must conform to this in what follows.

                beta_init = st_matrix(bname)

// What follows is how to set out an optimization in Stata.  First, initialize
// the optimization structure in the variable S.  Then tell Mata where the
// objective function is, that it's a minimization, that it's a "d0" type of
// objective function (no analytical derivatives or Hessians), and that the
// initial values for the parameter vector are in beta_init.  Finally, optimize.
                S = optimize_init()

                optimize_init_evaluator(S, &m_cuecrit())
                optimize_init_which(S, "min")
                optimize_init_evaluatortype(S, "d0")
                optimize_init_params(S, beta_init)
// CUE objective function takes 3 extra arguments: y, X and the structure with omega details
                optimize_init_argument(S, 1, py)
                optimize_init_argument(S, 2, pX)
                optimize_init_argument(S, 3, vcvo)
                optimize_init_argument(S, 4, useqr)

                beta = optimize(S)

// The last evaluation of the GMM objective function is J.
                j = optimize_result_value(S)

// Call m_omega one last time to get CUE weighting matrix.
                e[.,.] = y - X * beta'
                omega = m_omega(vcvo)
        }
        else {
// CUE beta supplied, so obtain maximized GMM obj function at b0
                beta = st_matrix(b0name)
                e[.,.] = y - X * beta'
                omega = m_omega(vcvo)
//              W = invsym(omega)
                gbar = 1/N * quadcross(Z, wf*wvar, e)
                j = N * gbar' * cholsolve(omega, gbar, useqr)
//              j = N * gbar' * W * gbar
        }

// Bits and pieces
        QXZ = st_matrix(XZmatrix)/N

        ee = quadcross(e, wf*wvar, e)
        sigmasq=ee/(N-dofminus)

//      QXZ_W_QZX = QXZ * W * QXZ'
//      _makesymmetric(QXZ_W_QZX)
//      QXZ_W_QZXinv=invsym(QXZ_W_QZX)
//      V = 1/N * QXZ_W_QZXinv
        aux1 = cholsolve(omega, QXZ')
        if (aux1[1,1]==.) {                                     //  omega not full rank; W=inv(omega) dubious, exit with error
errprintf("\nError: estimated covariance matrix of moment conditions not of full rank,")
errprintf("\n       and optimal GMM weighting matrix not unique.")
errprintf("\nPossible causes:")
errprintf("\n       collinearities in instruments (if -nocollin- option was used)")
errprintf("\n       singleton dummy variable (dummy with one 1 and N-1 0s or vice versa)")
errprintf("\n       {help ivreg2##partial:partial} option may address problem.\n")
                exit(506)
        }
        aux3 = makesymmetric(QXZ * aux1)
        V = 1/N * invsym(aux3)
        if (diag0cnt(V)) {                                      //  V not full rank, likely caused by collinearities;
                                                                                //  b dubious, exit with error
errprintf("\nError: estimated variance matrix of b not of full rank, and CUE estimates")
errprintf("\n       unreliable; may be caused by collinearities\n")
                exit(506)
        }
        W = invsym(omega)
        
        st_matrix("r(beta)", beta)
        st_matrix("r(S)", omega)
        st_matrix("r(W)", W)
        st_matrix("r(V)", V)
        st_numscalar("r(j)", j)
        st_numscalar("r(rss)", ee)
        st_numscalar("r(sigmasq)", sigmasq)

} // end program s_gmmcue

// CUE evaluator function.
// Handles only d0-type optimization; todo, g and H are just ignored.
// beta is the parameter set over which we optimize, and 
// J is the objective function to minimize.

void m_cuecrit(todo, beta, pointer py, pointer pX, struct ms_vcvorthog scalar vcvo, useqr, j, g, H)
{
        *vcvo.e[.,.] = *py - *pX * beta'

        omega = m_omega(vcvo)

// Calculate gbar=Z'*e/N
        gbar = 1/vcvo.N * quadcross(*vcvo.Z, vcvo.wf*(*vcvo.wvar), *vcvo.e)
        aux1 = cholqrsolve(omega, gbar, useqr)
        j = vcvo.N * gbar' * aux1

// old method
//      W = invsym(omega)
//      j = vcvo.N * gbar' * W * gbar

} // end program CUE criterion function


// ************** ffirst-stage stats *************************************

void s_ffirst(  string scalar ZZmatrix,
                                string scalar XXmatrix,
                                string scalar XZmatrix,
                                string scalar ZYmatrix,
                                string scalar ZZinvmatrix,
                                string scalar XXinvmatrix,
                                string scalar XPZXinvmatrix,
                                string scalar X2X2matrix,
                                string scalar Z1X2matrix,
                                string scalar X2ymatrix,
                                string scalar ename,                            //  Nx1
                                string scalar ematnames,                        //  Nx(K1+1)
                                string scalar yname,
                                string scalar X1names,
                                string scalar X2names,
                                string scalar Z1names, 
                                string scalar touse,
                                string scalar weight,
                                string scalar wvarname,
                                scalar wf,
                                scalar N,
                                scalar N_clust,
                                string scalar robust,
                                string scalar clustvarname,
                                string scalar clustvarname2,
                                string scalar clustvarname3,
                                scalar bw,
                                string scalar kernel,
                                string scalar sw,
                                string scalar psd,
                                string scalar ivarname,
                                string scalar tvarname,
                                string scalar tindexname,
                                scalar tdelta,
                                scalar center,
                                scalar dofminus,
                                scalar sdofminus)

{

        struct ms_vcvorthog scalar vcvo

        vcvo.Znames                     = Znames
        vcvo.touse                      = touse
        vcvo.weight                     = weight
        vcvo.wvarname           = wvarname
        vcvo.robust                     = robust
        vcvo.clustvarname       = clustvarname
        vcvo.clustvarname2      = clustvarname2
        vcvo.clustvarname3      = clustvarname3
        vcvo.kernel                     = kernel
        vcvo.sw                         = sw
        vcvo.psd                        = psd
        vcvo.ivarname           = ivarname
        vcvo.tvarname           = tvarname
        vcvo.tindexname         = tindexname
        vcvo.wf                         = wf
        vcvo.N                          = N
        vcvo.bw                         = bw
        vcvo.tdelta                     = tdelta
        vcvo.center                     = center
        vcvo.dofminus           = dofminus
        vcvo.ZZ                         = st_matrix(ZZmatrix)

// X1 = endog regressors
// X2 = exog regressors = included IVs
// Z1 = excluded instruments
// Z2 = included IVs = X2

        Xnames = invtokens( (X1names, X2names), " ")
        Znames = invtokens( (Z1names, X2names), " ")

        st_view(y,     ., st_tsrevar(tokens(yname)),      touse)
        st_view(X1,    ., st_tsrevar(tokens(X1names)),    touse)
        st_view(Z1,    ., st_tsrevar(tokens(Z1names)),    touse)
        st_view(X,     ., st_tsrevar(tokens(Xnames)),     touse)
        st_view(Z,     ., st_tsrevar(tokens(Znames)),     touse)
        st_view(e,     ., ename,                          touse)
        st_view(emat,  ., tokens(ematnames),              touse)
        st_view(wvar,  ., st_tsrevar(wvarname),           touse)

        vcvo.wvar       = &wvar
        vcvo.Z          = &Z
        vcvo.Znames     = Znames
        vcvo.ZZ         = st_matrix(ZZmatrix)

        if ("X2names"~="") {
                st_view(X2,    ., st_tsrevar(tokens(X2names)),  touse)
        }

        K1=cols(X1)
        K2=cols(X2)
        K=K1+K2
        L1=cols(Z1)
        L2=cols(X2)
        L=L1+L2
        df = L1
        df_r = N-L

        ZZinv   = st_matrix(ZZinvmatrix)
        XXinv   = st_matrix(XXinvmatrix)
        XPZXinv = st_matrix(XPZXinvmatrix)
        QZZ             = st_matrix(ZZmatrix)  / N
        QXX             = st_matrix(XXmatrix)  / N
        QZX             = st_matrix(XZmatrix)' / N
        QZY             = st_matrix(ZYmatrix)  / N
        QZZinv  = ZZinv*N
        QXXinv  = XXinv*N
        QX2X2   = st_matrix(X2X2matrix) / N
        QZ1X2   = st_matrix(Z1X2matrix) / N
        QX2y    = st_matrix(X2ymatrix)  / N

        sheaall = (diagonal(XXinv) :/ diagonal(XPZXinv))  // (X1, X2) in column vector
        sheaall = (sheaall[(1::K1), 1 ])'  // Just X1 in row vector

// Full system of reduced form (col 1) and first-stage regressions
        bz = cholsolve(QZZ, QZY)
        Yhat = Z*bz
        Xhat = Yhat[.,(2..(K1+1))], X2
// VCV for full system
        eall = (y, X1) - Yhat
        ee = quadcross(eall, wf*wvar, eall)
// sigmas have large-sample dofminus correction incorporated but no small dof corrections
        sigmasqall = ee / (N-dofminus)
// rmses have small dof corrections
        rmseall = sqrt( ee / (N-L-dofminus-sdofminus) )
// V has all the classical VCVs in block diagonals
        V = sigmasqall # ZZinv
// For Wald test of excluded instruments
        R = I(L1) , J(L1, L2, 0)
// For AP and SW stats
        QXhXh = quadcross(Xhat, wf*wvar, Xhat) / N
        QXhX1 = quadcross(Xhat, wf*wvar, X1 ) / N

//      VCV for system of first-stage eqns
//  Can be robust; even if not, has correct off-block-diagonal covariances
        vcvo.ename      = ematnames
        vcvo.e          = &emat
        emat[.,.]       = eall
        omegar          = m_omega(vcvo)
        Vr                      = makesymmetric(I(K1+1)#QZZinv * omegar * I(K1+1)#QZZinv) / N
        
// AR statistics from RF (first column)
        Rb                      = bz[ (1::L1), 1 ]
        RVR                     = Vr[| 1,1 \ L1, L1 |]
        ARWald          = Rb' * cholsolve(RVR, Rb)
        ARF                     = ARWald
        ARdf            = L1
        if (clustvarname=="") {
                ARdf2   = (N-dofminus-L-sdofminus)
                ARF             = ARWald / (N-dofminus) * ARdf2 / ARdf
        }
        else {
                ARdf2   = N_clust - 1
                ARF             = ARWald / (N-1) * (N-L-sdofminus) /(N_clust) * ARdf2 / ARdf
        }
        ARFp            = Ftail(ARdf, ARdf2, ARF)
        ARchi2          = ARWald
        ARchi2p         = chi2tail(ARdf, ARchi2)

// Stock-Wright LM S statistic
// Equivalent to J stat for model with coeff on endog=0 and with inexog partialled out
// = LM version of AR stat (matches weakiv)
        if (K2>0) {
                by              = cholsolve(QX2X2, QX2y)
                e[.,.]  = y-X2*by
        }
        else {
                e[.,.]  = y
        }
// initialize residual for VCV calc to be single Nx1 vector 
        vcvo.e          = &e
        vcvo.ename      = ename
// get VCV and sstat=J
        omega           = m_omega(vcvo)
        gbar            = 1/N * quadcross(Z, wf*wvar, e)
        sstat           = N * gbar' * cholsolve(omega, gbar)
        sstatdf         = L1
        sstatp          = chi2tail(sstatdf, sstat)

// Prepare to loop over X1s for F, SW and AP stats
// initialize matrix to save first-stage results
        firstmat=J(21,0,0)
// initialize residual for VCV calc to be single Nx1 vector 
        vcvo.e          = &e
        vcvo.ename      = ename
        
        for (i=1; i<=K1; i++) {

// RMSEs for first stage start in SECOND row/column (first has RF)
                rmse = rmseall[i+1,i+1]
// Shea partial R2
                shea = sheaall[1,i]
// first-stage coeffs for ith X1.
// (nb: first column is reduced form eqn for y)
                b=bz[., (i+1)]
// Classical Wald stat (chi2 here); also yields partial R2
// Since r is an L1 x 1 zero vector, can use Rb instead of (Rb-r)
                Rb = b[ (1::L1), . ]
                RVR = V[| 1+i*L,1+i*L \ i*L+L1, i*L+L1 |]
                Wald = Rb' * cholsolve(RVR, Rb)
// Wald stat has dofminus correction in it via sigmasq,
// so remove it to calculate partial R2
                pr2 = (Wald/(N-dofminus)) / (1 + (Wald/(N-dofminus)))

// Robustify F stat if necessary.
                if ((robust~="") | (clustvarname~="") | (kernel~="") | (sw~="")) {
                        RVR = Vr[| 1+i*L,1+i*L \ i*L+L1, i*L+L1 |]
                        Wald = Rb' * cholsolve(RVR, Rb)
                }
// small dof adjustment is effectively additional L2, e.g., partialled-out regressors
                df = L1
                if (clustvarname=="") {
                        df_r = (N-dofminus-L-sdofminus)
                        F = Wald / (N-dofminus) * df_r / df
                }
                else {
                        df_r = N_clust - 1
                        F = Wald / (N-1) * (N-L-sdofminus) * (N_clust - 1) / N_clust / df
                }
                pvalue = Ftail(df, df_r, F)

// If #endog=1, AP=SW=standard F stat
                if (K1==1) {
                        Fdf1    = df
                        Fdf2    = df_r
                        SWF             = F
                        SWFp    = pvalue
                        SWchi2  = Wald
                        SWchi2p = chi2tail(Fdf1, SWchi2)
                        SWr2    = pr2
                        APF             = SWF
                        APFp    = SWFp
                        APchi2  = SWchi2
                        APchi2p = SWchi2p
                        APr2    = SWr2
                }
                else {

// Angrist-Pischke and Sanderson-Windmeijer stats etc.
// select matrix needed for both; will select all but the endog regressor of interest
                        selmat=J(1,K,1)
                        selmat[1,i]=0           // don't select endog regressor of interest
        
// AP
// QXhXh is crossproduct of X1hats (fitted Xs) plus Z2s
// QXhX1 is crossproduct with X1s
// QXhXhi and QXhX1i remove the row/col for the endog regressor of interest
                        QXhXhi = select(select(QXhXh,selmat)', selmat)
                        QXhX1i = select(QXhX1[.,i], selmat')
// 1st step - in effect, 2nd stage of 2SLS using FITTED X1hats, and then get residuals e1
                        b1=cholsolve(QXhXhi, QXhX1i)
                        QXhXhinv = invsym(QXhXhi)       //  Need this for V
                        b1=QXhXhinv*QXhX1i
                        e1 = X1[.,i] - select(Xhat,selmat)*b1
// 2nd step - regress e1 on all Zs and test excluded ones
                        QZe1 = quadcross(Z, wf*wvar, e1 ) / N
                        b2=cholsolve(QZZ, QZe1)
                        APe2 = e1 - Z*b2
                        ee = quadcross(APe2, wf*wvar, APe2)
                        sigmasq2 = ee / (N-dofminus)
// Classical V
                        Vi = sigmasq2 * QZZinv / N
                        APRb=b2[ (1::L1), .]
                        APRVR = Vi[ (1::L1), (1..L1) ]
                        APWald = APRb' * cholsolve(APRVR, APRb)
// Wald stat has dofminus correction in it via sigmasq,
// so remove it to calculate partial R2
                        APr2 = (APWald/(N-dofminus)) / (1 + (APWald/(N-dofminus)))
        
// Now SW stat
// Uses same 2SLS coeffs as AP but resids use ACTUAL X1 (not fitted X1)
                        e1 = X1[.,i] - select(X,selmat)*b1
// next step - regress e on all Zs and test excluded ones
                        QZe1 = quadcross(Z, wf*wvar, e1 ) / N
                        b2=cholsolve(QZZ, QZe1)
                        SWe2 = e1 - Z*b2
                        ee = quadcross(SWe2, wf*wvar, SWe2)
                        sigmasq2 = ee / (N-dofminus)
                        Vi = sigmasq2 * QZZinv / N
                        SWRb=b2[ (1::L1), .]
                        SWRVR = Vi[ (1::L1), (1..L1) ]
                        SWWald = SWRb' * cholsolve(SWRVR, SWRb)
// Wald stat has dofminus correction in it via sigmasq,
// so remove it to calculate partial R2
                        SWr2 = (SWWald/(N-dofminus)) / (1 + (SWWald/(N-dofminus)))
        
// Having calculated AP and SW R-sq based on non-robust Wald, now get robust Wald if needed.
                        if ((robust~="") | (clustvarname~="") | (kernel~="") | (sw~="")) {
                                e[.,1]=APe2
                                omega=m_omega(vcvo)
                                Vi = makesymmetric(QZZinv * omega * QZZinv) / N
                                APRVR = Vi[ (1::L1), (1..L1) ]
                                APWald = APRb' * cholsolve(APRVR, APRb)                         //  re-use APRb
                                e[.,1]=SWe2
                                omega=m_omega(vcvo)
                                Vi = makesymmetric(QZZinv * omega * QZZinv) / N
                                SWRVR = Vi[ (1::L1), (1..L1) ]
                                SWWald = SWRb' * cholsolve(SWRVR, SWRb)                         //  re-use SWRb
                        }
        
// small dof adjustment is effectively additional L2, e.g., partialled-out regressors
                        Fdf1 = (L1-K1+1)
                        if (clustvarname=="") {
                                Fdf2 = (N-dofminus-L-sdofminus)
                                APF = APWald / (N-dofminus) * Fdf2 / Fdf1
                                SWF = SWWald / (N-dofminus) * Fdf2 / Fdf1
                        }
                        else {
                                Fdf2 = N_clust - 1
                                APF = APWald / (N-1) * (N-L-sdofminus) * (N_clust - 1) / N_clust / Fdf1
                                SWF = SWWald / (N-1) * (N-L-sdofminus) * (N_clust - 1) / N_clust / Fdf1
                        }
                        APFp = Ftail(Fdf1, Fdf2, APF)
                        APchi2 = APWald
                        APchi2p = chi2tail(Fdf1, APchi2)
                        SWFp = Ftail(Fdf1, Fdf2, SWF)
                        SWchi2 = SWWald
                        SWchi2p = chi2tail(Fdf1, SWchi2)
                }

// Assemble results
                firstmat = firstmat ,                                                                                                   ///
                                        (rmse \ shea \ pr2 \ F \ df \ df_r \ pvalue                             ///
                                        \ SWF \ Fdf1 \ Fdf2 \ SWFp \ SWchi2 \ SWchi2p \ SWr2            ///
                                        \ APF \ Fdf1 \ Fdf2 \ APFp \ APchi2 \ APchi2p \ APr2)
        } // end of loop for an X1 variable

        st_numscalar("r(rmse_rf)", rmseall[1,1])
        st_matrix("r(firstmat)", firstmat)
        st_matrix("r(b)", bz)
        st_matrix("r(V)", Vr)
        st_matrix("r(S)", omegar)
        st_numscalar("r(archi2)", ARchi2)
        st_numscalar("r(archi2p)", ARchi2p)
        st_numscalar("r(arf)", ARF)
        st_numscalar("r(arfp)", ARFp)
        st_numscalar("r(ardf)", ARdf)
        st_numscalar("r(ardf_r)", ARdf2)
        st_numscalar("r(sstat)",sstat)
        st_numscalar("r(sstatp)",sstatp)
        st_numscalar("r(sstatdf)",sstatdf)

} // end program s_ffirst

// **********************************************************************

void s_omega(
                                        string scalar ZZmatrix,
                                        string scalar ename,
                                        string scalar Znames,
                                        string scalar touse,
                                        string scalar weight,
                                        string scalar wvarname,
                                        scalar wf,
                                        scalar N,
                                        string scalar robust,
                                        string scalar clustvarname,
                                        string scalar clustvarname2,
                                        string scalar clustvarname3,
                                        scalar bw,
                                        string scalar kernel,
                                        string scalar sw,
                                        string scalar psd,
                                        string scalar ivarname,
                                        string scalar tvarname,
                                        string scalar tindexname,
                                        scalar tdelta,
                                        scalar center,
                                        scalar dofminus)
{

        struct ms_vcvorthog scalar vcvo

        vcvo.ename                      = ename
        vcvo.Znames                     = Znames
        vcvo.touse                      = touse
        vcvo.weight                     = weight
        vcvo.wvarname           = wvarname
        vcvo.robust                     = robust
        vcvo.clustvarname       = clustvarname
        vcvo.clustvarname2      = clustvarname2
        vcvo.clustvarname3      = clustvarname3
        vcvo.kernel                     = kernel
        vcvo.sw                         = sw
        vcvo.psd                        = psd
        vcvo.ivarname           = ivarname
        vcvo.tvarname           = tvarname
        vcvo.tindexname         = tindexname
        vcvo.wf                         = wf
        vcvo.N                          = N
        vcvo.bw                         = bw
        vcvo.tdelta                     = tdelta
        vcvo.center                     = center
        vcvo.dofminus           = dofminus
        vcvo.ZZ                         = st_matrix(ZZmatrix)

        st_view(Z,      ., st_tsrevar(tokens(Znames)),  touse)
        st_view(wvar,   ., st_tsrevar(wvarname), touse)
        st_view(e,      ., vcvo.ename,  touse)
        
        vcvo.e          = &e
        vcvo.Z          = &Z
        vcvo.wvar       = &wvar

        ZZ = st_matrix(ZZmatrix)

        S=m_omega(vcvo)

        st_matrix("r(S)", S)
} // end of s_omega program


// Mata utility for sequential use of solvers
// Default is cholesky;
// if that fails, use QR;
// if overridden, use QR.

function cholqrsolve (  numeric matrix A,
                                                numeric matrix B,
                                                | real scalar useqr)
{
        if (args()==2) useqr = 0
        
        real matrix C

        if (!useqr) {
                C = cholsolve(A, B)
                if (C[1,1]==.) {
                        C = qrsolve(A, B)
                }
        }
        else {
                C = qrsolve(A, B)
        }

        return(C)

}

end                     //  end Mata section


// Include ftools -----------------------------------------------------------
    cap findfile "ftools.mata"
    if (_rc) {
        di as error "ivreghdfe requires the {bf:ftools} package, which is not installed"
        di as error `"    - install from {stata ssc install ftools:SSC}"'
        di as error `"    - install from {stata `"net install ftools, from("https://github.com/sergiocorreia/ftools/raw/master/src/")"':Github}"'
        exit 9
    }

// Include reghdfe --------------------------------------------------
    cap findfile "reghdfe.mata"
    if (_rc) {
        di as error "ivreghdfe requires the {bf:reghdfe} package, which is not installed"
        di as error `"    - install from {stata ssc install reghdfe:SSC}"'
        di as error `"    - install from {stata `"net install reghdfe, from("https://github.com/sergiocorreia/reghdfe/raw/master/src/")"':Github}"'
        exit 9
    }
        include "reghdfe.mata", adopath


exit            //  exit before loading comments

********************************** VERSION COMMENTS **********************************
*  Initial version cloned from official ivreg version 5.0.9  19Dec2001
*  1.0.2:  add logic for reg3. Sargan test
*  1.0.3:  add prunelist to ensure that count of excluded exogeneous is correct 
*  1.0.4:  revise option to exog(), allow included exog to be specified as well
*  1.0.5:  switch from reg3 to regress, many options and output changes
*  1.0.6:  fixed treatment of nocons in Sargan and C-stat, and corrected problems
*          relating to use of nocons combined with a constant as an IV
*  1.0.7:  first option reports F-test of excluded exogenous; prunelist bug fix
*  1.0.8:  dropped prunelist and switched to housekeeping of variable lists
*  1.0.9:  added collinearity checks; C-stat calculated with recursive call;
*          added ffirst option to report only F-test of excluded exogenous
*          from 1st stage regressions
*  1.0.10: 1st stage regressions also report partial R2 of excluded exogenous
*  1.0.11: complete rewrite of collinearity approach - no longer uses calls to
*          _rmcoll, does not track specific variables dropped; prunelist removed
*  1.0.12: reorganised display code and saved results to enable -replay()-
*  1.0.13: -robust- and -cluster- now imply -small-
*  1.0.14: fixed hascons bug; removed ivreg predict fn (it didn't work); allowed
*          robust and cluster with z stats and correct dofs
*  1.0.15: implemented robust Sargan stat; changed to only F-stat, removed chi-sq;
*          removed exog option (only orthog works)
*  1.0.16: added clusterised Sargan stat; robust Sargan handles collinearities;
*          predict now works with standard SE options plus resids; fixed orthog()
*          so it accepts time series operators etc.
*  1.0.17: fixed handling of weights.  fw, aw, pw & iw all accepted.
*  1.0.18: fixed bug in robust Sargan code relating to time series variables.
*  1.0.19: fixed bugs in reporting ranks of X'X and Z'Z
*          fixed bug in reporting presence of constant
*  1.0.20: added GMM option and replaced robust Sargan with (equivalent) J;
*          added saved statistics of 1st stage regressions
*  1.0.21: added Cragg HOLS estimator, including allowing empty endog list;
*          -regress- syntax now not allowed; revised code searching for "_cons"
*  1.0.22: modified cluster output message; fixed bug in replay for Sargan/Hansen stat;
*          exactly identified Sargan/Hansen now exactly zero and p-value not saved as e();
*          cluster multiplier changed to 1 (from buggy multiplier), in keeping with
*          eg Wooldridge 2002 p. 193.
*  1.0.23: fixed orthog option to prevent abort when restricted equation is underid.
*  1.0.24: fixed bug if 1st stage regressions yielded missing values for saving in e().
*  1.0.25: Added Shea version of partial R2
*  1.0.26: Replaced Shea algorithm with Godfrey algorithm
*  1.0.27: Main call to regress is OLS form if OLS or HOLS is specified; error variance
*          in Sargan and C statistics use small-sample adjustment if -small- option is
*          specified; dfn of S matrix now correctly divided by sample size
*  1.0.28: HAC covariance estimation implemented
*          Symmetrize all matrices before calling syminv
*          Added hack to catch F stats that ought to be missing but actually have a
*          huge-but-not-missing value
*          Fixed dof of F-stat - was using rank of ZZ, should have used rank of XX (couldn't use df_r
*          because it isn't always saved.  This is because saving df_r triggers small stats
*          (t and F) even when -post- is called without dof() option, hence df_r saved only
*          with -small- option and hence a separate saved macro Fdf2 is needed.
*          Added rankS to saved macros
*          Fixed trap for "no regressors specified"
*          Added trap to catch gmm option with no excluded instruments
*          Allow OLS syntax (no endog or excluded IVs specified)
*          Fixed error messages and traps for rank-deficient robust cov matrix; includes
*          singleton dummy possibility
*          Capture error if posting estimated VCV that isn't pos def and report slightly
*          more informative error message
*          Checks 3 variable lists (endo, inexog, exexog) separately for collinearities
*          Added AC (autocorrelation-consistent but conditionally-homoskedastic) option
*          Sargan no longer has small-sample correction if -small- option
*          robust, cluster, AC, HAC all passed on to first-stage F-stat
*          bw must be < T
*  1.0.29  -orthog- also displays Hansen-Sargan of unrestricted equation
*          Fixed collinearity check to include nocons as well as hascons
*          Fixed small bug in Godfrey-Shea code - macros were global rather than local
*          Fixed larger bug in Godfrey-Shea code - was using mixture of sigma-squares from IV and OLS
*            with and without small-sample corrections
*          Added liml and kclass
*  1.0.30  Changed order of insts macro to match saved matrices S and W
*  2.0.00  Collinearities no longer -qui-
*          List of instruments tested in -orthog- option prettified
*  2.0.01  Fixed handling of nocons with no included exogenous, including LIML code
*  2.0.02  Allow C-test if unrestricted equation is just-identified.  Implemented by
*          saving Hansen-Sargan dof as = 0 in e() if just-identified.
*  2.0.03  Added score() option per latest revision to official ivreg
*  2.0.04  Changed score() option to pscore() per new official ivreg
*  2.0.05  Fixed est hold bug in first-stage regressions
*          Fixed F-stat finite sample adjustment with cluster option to match official Stata
*          Fixed F-stat so that it works with hascons (collinearity with constant is removed)
*          Fixed bug in F-stat code - wasn't handling failed posting of vcv
*          No longer allows/ignores nonsense options
*  2.0.06  Modified lsStop to sync with official ivreg 5.1.3
*  2.0.07a Working version of CUE option
*          Added sortpreserve, ivar and tvar options
*          Fixed smalls bug in calculation of T for AC/HAC - wasn't using the last ob
*          in QS kernel, and didn't take account of possible dropped observations
*  2.0.07b Fixed macro bug that truncated long varlists
*  2.0.07c Added dof option.
*          Changed display of RMSE so that more digits are displayed (was %8.1g)
*          Fixed small bug where cstat was local macro and should have been scalar
*          Fixed bug where C stat failed with cluster.  NB: wmatrix option and cluster are not compatible!
*  2.0.7d  Fixed bug in dof option
*  2.1.0   Added first-stage identification, weak instruments, and redundancy stats
*  2.1.01  Tidying up cue option checks, reporting of cue in output header, etc.
*  2.1.02  Used Poskitt-Skeels (2002) result that C-D eval = cceval / (1-cceval)
*  2.1.03  Added saved lists of separate included and excluded exogenous IVs
*  2.1.04  Added Anderson-Rubin test of signif of endog regressors
*  2.1.05  Fix minor bugs relating to cluster and new first-stage stats
*  2.1.06  Fix bug in cue: capture estimates hold without corresponding capture on estimates unhold
*  2.1.07  Minor fix to ereturn local wexp, promote to version 8.2
*  2.1.08  Added dofminus option, removed dof option.  Added A-R test p-values to e().
*          Minor bug fix to A-R chi2 test - was N chi2, should have been N-L chi2.
*          Changed output to remove potentially misleading refs to N-L etc.
*          Bug fix to rhs count - sometimes regressors could have exact zero coeffs
*          Bug fix related to cluster - if user omitted -robust-, orthog would use Sargan and not J
*          Changed output of Shea R2 to make clearer that F and p-values do not refer to it
*          Improved handling of collinearites to check across inexog, exexog and endo lists
*          Total weight statement moved to follow summ command
*          Added traps to catch errors if no room to save temporary estimations with _est hold
*          Added -savefirst- option. Removed -hascons-, now synonymous with -nocons-.
*  2.1.09  Fixes to dof option with cluster so it no longer mimics incorrect areg behavior
*          Local ivreg2cmd to allow testing under name ivreg2
*          If wmatrix supplied, used (previously not used if non-robust sargan stat generated)
*          Allowed OLS using (=) syntax (empty endo and exexog lists)
*          Clarified error message when S matrix is not of full rank
*          cdchi2p, ardf, ardf_r added to saved macros
*          first and ffirst replay() options; DispFirst and DispFFirst separately codes 1st stage output
*          Added savefprefix, macro with saved first-stage equation names.
*          Added version option.
*          Added check for duplicate variables to collinearity checks
*          Rewrote/simplified Godfrey-Shea partial r2 code
* 2.1.10   Added NOOUTput option
*          Fixed rf bug so that first does not trigger unnecessary saved rf
*          Fixed cue bug - was not starting with robust 2-step gmm if robust/cluster
* 2.1.11   Dropped incorrect/misleading dofminus adjustments in first-stage output summary
* 2.1.12   Collinearity check now checks across inexog/exexog/endog simultaneously
* 2.1.13   Added check to catch failed first-stage regressions
*          Fixed misleading failed C-stat message
* 2.1.14   Fixed mishandling of missing values in AC (non-robust) block
* 2.1.15   Fixed bug in RF - was ignoring weights
*          Added -endog- option
*          Save W matrix for all cases; ensured copy is posted with wmatrix option so original isn't zapped
*          Fixed cue bug - with robust, was entering IV block and overwriting correct VCV
* 2.1.16   Added -fwl- option
*          Saved S is now robust cov matrix of orthog conditions if robust, whereas W is possibly non-robust
*          weighting matrix used by estmator.  inv(S)=W if estimator is efficient GMM.
*          Removed pscore option (dropped by official ivreg).
*          Fixed bug where -post- would fail because of missing values in vcv
*          Remove hascons as synonym for nocons
*          OLS now outputs 2nd footer with variable lists
* 2.1.17   Reorganization of code
*          Added ll() macro
*          Fixed N bug where weights meant a non-integer ob count that was rounded down
*          Fixed -fwl- option so it correctly handles weights (must include when partialling-out)
*          smatrix option takes over from wmatrix option.  Consistent treatment of both.
*          Saved smatrix and wmatrix now differ in case of inefficient GMM.
*          Added title() and subtitle() options.
*          b0 option returns a value for the Sargan/J stat even if exactly id'd.
*          (Useful for S-stat = value of GMM objective function.)
*          HAC and AC now allowed with LIML and k-class.
*          Collinearity improvements: bug fixed because collinearity was mistakenly checked across
*          inexog/exexog/endog simultaneously; endog predicted exactly by IVs => reclassified as inexog;
*          _rmcollright enforces inexog>endo>exexog priority for collinearities, if Stata 9.2 or later.
*          K-class, LIML now report Sargan and J.  C-stat based on Sargan/J.  LIML reports AR if homosked.
*          nb: can always easily get a C-stat for LIML based on diff of two AR stats.
*          Always save Sargan-Hansen as e(j); also save as e(sargan) if homoskedastic.
*          Added Stock-Watson robust SEs options sw()
* 2.1.18   Added Cragg-Donald-Stock-Yogo weak ID statistic critical values to main output
*          Save exexog_ct, inexog_ct and endog_ct as macros
*          Stock-Watson robust SEs now assume ivar is group variable
*          Option -sw- is standard SW.  Option -swpsd- is PSD version a la page 6 point 10.
*          Added -noid- option.  Suppresses all first-stage and identification statistics.
*          Internal calls to ivreg2 use noid option.
*          Added hyperlinks to ivreg2.hlp and helpfile argument to display routines to enable this.
* 2.1.19   Added matrix rearrangement and checks for smatrix and wmatrix options
*          Recursive calls to cstat simplified - no matrix rearrangement or separate robust/nonrobust needed
*          Reintroduced weak ID stats to ffirst output
*          Added robust ID stats to ffirst output for case of single endogenous regressor
*          Fixed obscure bug in reporting 1st stage partial r2 - would report zero if no included exogenous vars
*          Removed "HOLS" in main output (misleading if, e.g., estimation is AC but not HAC)
*          Removed "ML" in main output if no endogenous regressors - now all ML is labelled LIML
*          model=gmm is now model=gmm2s; wmatrix estimation is model=gmm
*          wmatrix relates to gmm estimator; smatrix relates to gmm var-cov matrix; b0 behavior equiv to wmatrix
*          b0 option implies nooutput and noid options
*          Added nocollin option to skip collinearity checks
*          Fixed minor display bug in ffirst output for endog vars with varnames > 12 characters
*          Fixed bug in saved rf and first-stage results for vars with long varnames; uses permname
*          Fixed bug in model df - had counted RHS, now calculates rank(V) since latter may be rank-deficient
*          Rank of V now saved as macro rankV
*          fwl() now allows partialling-out of just constant with _cons
*          Added Stock-Wright S statistic (but adds overhead - calls preserve)
*          Properties now include svyj.
*          Noted only: fwl bug doesn't allow time-series operators.
* 2.1.20   Fixed Stock-Wright S stat bug - didn't allow time-series operators
* 2.1.21   Fixed Stock-Wright S stat to allow for no exog regressors cases
* 2.2.00   CUE partials out exog regressors, estimates endog coeffs, then exog regressors separately - faster
*          gmm2s becomes standard option, gmm supported as legacy option
* 2.2.01   Added explanatory messages if gmm2s used.
*          States if estimates efficient for/stats consistent for het, AC, etc.
*          Fixed small bug that prevented "{help `helpfile'##fwl:fwl}" from displaying when -capture-d.
*          Error message in footer about insuff rank of S changed to warning message with more informative message.
*          Fixed bug in CUE with weights.
* 2.2.02   Removed CUE partialling-out; still available with fwl
*          smatrix and wmatrix become documented options. e(model)="gmmw" means GMM with arbitrary W
* 2.2.03   Fixed bug in AC with aweights; was weighting zi'zi but not ei'ei.
* 2.2.04   Added abw code for bw(), removed properties(svyj)
* 2.2.05   Fixed bug in AC; need to clear variable vt1 at start of loop
*          If iweights, N (#obs with precision) rounded to nearest integer to mimic official Stata treatment
*          and therefore don't need N scalar at all - will be same as N
*          Saves fwl_ct as macro.
*          -ffirst- output, weak id stat, etc. now adjust for number of partialled-out variables.
*          Related changes: df_m, df_r include adjustments for partialled-out variables.
*          Option nofwlsmall introduced - suppresses above adjustments.  Undocumented in ivreg2.hlp.
*          Replaced ID tests based on canon corr with Kleibergen-Paap rk-based stats if not homoskedastic
*          Replaced LR ID test stats with LM test stats.
*          Checks that -ranktest- is installed.
* 2.2.06   Fixed bug with missing F df when cue called; updated required version of ranktest 
* 2.2.07   Modified redundancy test statistic to match standard regression-based LM tests
*          Change name of -fwl- option to -partial-.
*          Use of b0 means e(model)=CUE.  Added informative b0 option titles. b0 generates output but noid.
*          Removed check for integer bandwidth if auto option used.
* 2.2.08   Add -nocollin- to internal calls and to -ivreg2_cue- to speed performance.
* 2.2.09   Per msg from Brian Poi, Alastair Hall verifies that Newey-West cited constant of 1.1447
*          is correct. Corrected mata abw() function. Require -ranktest- 1.1.03.
* 2.2.10   Added Angrist-Pischke multivariate f stats.  Rewrite of first and ffirst output.
*          Added Cragg-Donald to weak ID output even when non-iid.
*          Fixed small bug in non-robust HAC code whereby extra obs could be used even if dep var missing.
*             (required addition of  L`tau'.(`s1resid') in creation of second touse variable)
*          Fixed bugs that zapped varnames with "_cons" in them
*          Changed tvar and ivar setup so that data must be tsset or xtset.
*          Fixed bug in redundancy test stat when called by xtivreg2+cluster - no dofminus adj needed in this case
*          Changed reporting so that gaps between panels are not reported as such.
*          Added check that weight variable is not transformed by partialling out.
*          Changed Stock-Wright S statistic so that it uses straight partialling-out of exog regressors
*            (had been, in effect, doing 2SGMM partialling-out)
*          Fixed bug where dropped collinear endogenous didn't get a warning or listing
*          Removed N*CDEV Wald chi-sq statistic from ffirst output (LM stat enough)
* 3.0.00   Fully rewritten and Mata-ized code.  Require min Stata 10.1 and ranktest 1.2.00.
*          Mata support for Stock-Watson SEs for fixed effects estimator; doesn't support fweights.
*          Changed handling of iweights yielding non-integer N so that (unlike official -regress-) all calcs
*          for RMSE etc. use non-integer N and N is rounded down only at the end.
*          Added support for Thompson/Cameron-Gelbach-Miller 2-level cluster-robust vcvs.
* 3.0.01   Now exits more gracefully if no regressors survive after collinearity checks
* 3.0.02   -capture- instead of -qui- before reduced form to suppress not-full-rank error warning
*          Modified Stock-Wright code to partial out all incl Xs first, to reduce possibility of not-full-rank
*          omega and missing sstat.  Added check within Stock-Wright code to catch not-full-rank omega.
*          Fixed bug where detailed first-stage stats with cluster were disrupted if data had been tsset
*          using a different variables.
*          Fixed bug that didn't allow regression on just a constant.
*          Added trap for no observations.
*          Added trap for auto bw with panel data - not allowed.
* 3.0.03   Fixed bug in m_omega that always used Stock-Watson spectral decomp to create invertible shat
*          instead of only when (undocumented) spsd option is called.
*          Fixed bug where, if matsize too small, exited with wrong error (mistakenly detected as collinearities)
*          Removed inefficient call to -ranktest- that unnecessarily requested stats for all ranks, not just full.
* 3.0.04   Fixed coding error in m_omega for cluster+kernel.  Was *vcvo.e[tmatrix[.,1]], should have been (*vcvo.e)[tmatrix[.,1]].
*          Fixed bug whereby clusters defined by strings were not handled correctly.
*          Updated ranktest version check
* 3.0.05   Added check to catch unwanted transformations of time or panel variables by partial option.
* 3.0.06   Fixed partial bug - partialcons macro saved =0 unless _cons explicitly in partial() varlist
* 3.0.07   kclass was defaulting to LIML - fixed.
*          Renamed spsd option to psda (a=abs) following Stock-Watson 2008. Added psd0 option following Politis 2007.
*          Fixed bug that would prevent RF and first-stage with cluster and TS operators if cluster code changed sort order.
*          Modified action if S matrix is not full rank and 2-step GMM chosen.  Now continue but report problem in footer
*          and do not report J stat etc.
* 3.0.08   Fixed cluster+bw; was not using all observations of all panel units if panel was unbalanced.
*          Fixed inconsequential bug in m_omega that caused kernel loop to be entered (with no impact) even if kernel==""
*          Fixed small bug that compared bw to T instead of (correctly) to T/delta when checking that bw can't be too long.
*          Added dkraay option = cluster on t var + kernel-robust
*          Added kiefer option = truncated kernel, bw=T (max), and no robust
*          Fixed minor reporting bug that reported time-series gaps in entire panel dataset rather than just portion touse-d.
*          Recoded bw and kernel checks into subroutine vkernel.  Allow non-integer bandwidth within check as in ranktest.
* 3.1.01   First ivreg2 version with accompanying Mata library (shared with -ranktest-).  Mata library includes
*          struct ms_vcvorthog, m_omega, m_calckw, s_vkernel.
*          Fixed bug in 2-way cluster code (now in m_omega in Mata library) - would crash if K>1 (relevant for -ranktest- only).
* 3.1.02   Converted cdsy to Mata code and moved to Mata library. Standardized spelling/caps/etc. of QS as "Quadratic Spectral".
* 3.1.03   Improved partialling out in s_sstat and s_ffirst: replaced qrsolve with invsym.
* 3.1.04   Fixed minor bug in s_crossprod - would crash with L1=0 K1>0, and also with K=0
* 3.1.05   Fixed minor bug in orthog - wasn't saving est results if eqn w/o suspect instruments did not execute properly
*          Fixed minor bug in s_cccollin() - didn't catch perverse case of K1>0 (endog regressors) and L1=0 (no excl IVs)
* 3.1.06   Spelling fix for Danielle kernel, correct error check for bw vs T-1
* 3.1.07   Fixed bug that would prevent save of e(sample) when partialling out just a constant
* 3.1.08   01Jan14. Fixed reporting bug with 2-way clustering and kernel-robust that would give wrong count for 2nd cluster variable.
* 3.1.09   13July14. _rmcollright under version control has serious bug for v10 and earlier. Replaced with canon corr approach.
*          Fixed obscure bug in estimation sample - was not using obs when tsset tvar is missing, even if TS operators not used.
*          Fixed bug in auto bw code so now ivreg2 and ivregress agree. Also, ivreg2 auto bw code handles gaps in TS correctly.
* 4.0.00   25Jan15. Promote to require Stata version 11.2
*          Rewrite of s_gmm1s, s_iegmm, s_egmm etc. to use matrix solvers rather than inversion.
*          rankS and rankV now calculated along with estimators; rankS now always saved.
*          Returned to use of _rmcollright to detect collinearities since bug was in Stata 10's _rmcollright and now not relevant.
*          Added reporting of collinearities and duplicates in replay mode.
*          Rewrite of legacy support for previous ivreg2x version.  Main program calls ivreg2x depending on _caller().
*          Estimation and replay moved to ivreg211 subroutine above.
* 4.0.01   8Feb15. Fixed bug in default name and command used used for saved first and RF equations
*          Fixed bug in saved command line (was ivreg211, should be ivreg2).
* 4.0.02   9Feb15. Changed forced exit at Stata <11 before continuing loading to forced exit pre-Mata code at Stata <9.
* 4.1.00   Substantial rewrite to allow factor variables. Now also accepts TS ops as well as FV ops in partial varlist.
*          Rewrite included code for dropped/collinear/reclassified.
*          Saved RF and 1st-stage estimations have "if e(sample)" instead of "if `touse'" in e(cmdline).
*          Rewrite of s_gmm1s etc. to use qrsolve if weighting matrix not full rank or cholsolve fails
*          Fixed bug in display subroutines that would display hyperlink to wrong (nonexistent) help file.
* 4.1.01   15Jun15. Fixed bug that did not allow dropped variables to be in partial(.) varlist.
*          Major rewrite of parsing code and collinearity/dropped/reclassified code.
*          Added support for display options noomitted, vsquish, noemptycells, baselevels, allbaselevels.
*          Changed from _rmcoll/_rmcollright/_rmcoll2list to internal ivreg2_rmcollright2
*          Changed failure of ranktest to obtain id stats to non-fatal so that estimation proceeds.
*          Removed recount via _rmcoll if noid option specified
*          Added partial(_all) option.
*          Improved checks of smatrix, wmatrix, b0 options
*          Rewrite of first-stage and reduced form code; rewrite of replay(.) functionality
*          Added option for displaying system of first-stage/reduced form eqns.
*          Replaced AP first-stage test stats with SW (Sanderson-Windmeijer) first-stage stats
*          Corrected S LM stat option; now calcuated in effect as J stat for case of no endog (i.e. b=0)
*          with inexog partialled out i.e. LM version of AR stat; now matches weakiv
*          Undocumented FV-related options: fvsep (expand endo, inexog, exexog separately) fvall (expand together)
* 4.1.02   17Jun15.  Fixed bug in collinearity check - was ignoring weights.
*          More informative error message if invalid matrix provided to smatrix(.) or wmatrix(.) options.
*          Caught error if depvar was FV or TS var that expanded to >1 variable.
* 4.1.03   18Jun15.  Fixed bug with robust + rf option.
* 4.1.04   18Jun15.  Fixed bug in AR stat with dofminus option + cluster (was subtracting dof, shouldn't).
* 4.1.05   18Jun15.  Added rmse, df_m, df_r to saved RF and first-stage equation results.
* 4.1.06   4July15.  Replaced mvreg with Mata code for partialling out (big speed gains with many vars).
*          Rewrote AddOmitted to avoid inefficient loop; replaced with Mata subscripting.
*          Failure of id stats because of collinearities triggers error message only; estimation continues.
*          Calculation of dofs etc. uses rankS and rankV instead of iv1_ct and rhs1_ct;
*          counts are therefore correct even in presence of collinearities and use of nocollin option.
*          nocollin options triggers use of QR instead of default Cholesky.
*          rankxx and rankzz now based on diag0cnt of (XX)^-1 and (ZZ)^-1.
*          CUE fails if either S or V not full rank; can happen if nocollin option used.
*          Added undocumented useqr option to force use of QR instead of Cholesky.
*          Misc other code tweaks to make results more robust to nocollin option.
* 4.1.07   12July15.  Fixed bugs in calculation of rank(V) (had miscounted in some cases if omega not full rank)
*          Changed calc of dofs etc. from rankS and rankV to rankzz and rankxx (had miscounted in some cases etc.).
*          Restored warning message for all exog regressors case if S not full rank.
* 4.1.08   27July15. Replaced wordcount(.) function with word count macro in AddOmitted;
*          AddOmitted called only if any omitted regressors to add.
*          Added center option for centering moments.
* 4.1.09   20Aug15. Expanded error message for failure to save first-stage estimations (var name too long).
*          Fixed bug when weighting used with new partial-out code (see 4.1.06 4July15).
*          Tweaked code so that if called under Stata version < 11, main ivreg2.ado is exited immediately after
*          loading parent ivreg2 program.  Removed automatic use of QR solver when nocollin option used.
*          Added saved condition numbers for XX and ZZ.
*          e(cmdline) now saves original string including any "s (i.e., saves `0' instead of `*').
* 4.1.10   Fixed bug with posting first-stage results if sort had been disrupted by Mata code.
*          Fixed bug which mean endog(.) and orthog(.) varlists weren't saved or displayed.
* 4.1.11   22Nov19. Added caller(.) option to ivreg211 subroutine to pass version of parent Stata _caller(.).
*          Local macro with this parent Stata version is `caller'.
*          Changed calls to ranktest so that if parent Stata is less than version 16,
*          ranktest is called under version control as version 11.2: ranktest ...,
*          otherwise it is called as version `caller': ranktest ... .
*          Added macro e(ranktestcmd); will be ranktest, or ranktest11, or ....
