********************************************************************************
* RDROBUST STATA PACKAGE -- rdrobust
* Authors: Sebastian Calonico, Matias D. Cattaneo, Max Farrell, Rocio Tititunik
********************************************************************************
*!version 10.0.0  2025-06-30

capture program drop rdrobust 
program define rdrobust, eclass
	syntax anything [if] [in] [, c(real 0) fuzzy(string) deriv(real 0) p(string) q(real 0) h(string) b(string) rho(real 0) covs(string) covs_drop(string) kernel(string) weights(string) bwselect(string) vce(string) level(real 95) all scalepar(real 1) scaleregul(real 1) nochecks masspoints(string) bwcheck(real 0) bwrestrict(string) stdvars(string) detail vleverage]
	*disp in yellow "Preparing data." 
	marksample touse
	preserve
	qui keep if `touse'
	tokenize "`anything'"
	local y `1'
	local x `2'
	local kernel   = lower("`kernel'")
	local bwselect = lower("`bwselect'")
	
	******************** Set VCE ***************************
	local nnmatch = 3
	tokenize `vce'	
	local w : word count `vce'
	if `w' == 1 {
		local vce_select `"`1'"'
	}
	if `w' == 2 {
		local vce_select `"`1'"'
		if ("`vce_select'"=="nn")      local nnmatch     `"`2'"'
		if ("`vce_select'"=="cluster" | "`vce_select'"=="nncluster") local clustvar `"`2'"'	
	}
	if `w' == 3 {
		local vce_select `"`1'"'
		local clustvar   `"`2'"'
		local nnmatch    `"`3'"'
		if ("`vce_select'"!="cluster" & "`vce_select'"!="nncluster") di as error  "{err}{cmd:vce()} incorrectly specified"  
	}
	if `w' > 3 {
		di as error "{err}{cmd:vce()} incorrectly specified"  
		exit 125
	}
	
	local vce_type = "NN"
	if ("`vce_select'"=="hc0")     		 local vce_type = "HC0"
	if ("`vce_select'"=="hc1")      	 local vce_type = "HC1"
	if ("`vce_select'"=="hc2")      	 local vce_type = "HC2"
	if ("`vce_select'"=="hc3")      	 local vce_type = "HC3"
	if ("`vce_select'"=="cluster")  	 local vce_type = "Cluster"
	if ("`vce_select'"=="nncluster") 	 local vce_type = "NNcluster"

	if ("`vce_select'"=="cluster" | "`vce_select'"=="nncluster") local cluster = "cluster"
	if ("`vce_select'"=="cluster")       local vce_select = "hc0"
	if ("`vce_select'"=="nncluster")     local vce_select = "nn"
	if ("`vce_select'"=="")              local vce_select = "nn"

	******************** Set BW ***************************
	tokenize `h'	
	local w : word count `h'
	if `w' == 1 {
		local h_l `"`1'"'
		local h_r `"`1'"'
	}
	if `w' == 2 {
		local h_l `"`1'"'
		local h_r `"`2'"'
	}
	if `w' >= 3 {
		di as error  "{err}{cmd:h()} only accepts two inputs"  
		exit 125
	}
	
	tokenize `b'	
	local w : word count `b'
	if `w' == 1 {
		local b_l `"`1'"'
		local b_r `"`1'"'
	}
	if `w' == 2 {
		local b_l `"`1'"'
		local b_r `"`2'"'
	}
	if `w' >= 3 {
		di as error  "{err}{cmd:b()} only accepts two inputs"  
		exit 125
	}
	
	*** Manual bandwidth 
	if ("`h'"!="") {	
		local bwselect = "Manual"
		*if ("`b_l'"=="" & "`b_r'"=="" & "`h_l'"!="" & "`h_r'"!="") {
		if ("`b'"=="") {	
			local b_r = `h_r'
			local b_l = `h_l'
		}		
		
		scalar rho= round(`rho', .0001)
		if (rho>0)  {
			local b_l = `h_l'/`rho'
			local b_r = `h_r'/`rho'
		}		
	}	
	
	*** Default bandwidth 
	if ("`h'"=="" & "`bwselect'"=="") local bwselect= "mserd"
	
	******************** Set Fuzzy***************************
	tokenize `fuzzy'	
	local w : word count `fuzzy'
	if `w' == 1 {
		local fuzzyvar `"`1'"'
	}
	if `w' == 2 {
		local fuzzyvar `"`1'"'
		local sharpbw  `"`2'"'
		if `"`2'"' != "sharpbw" {
			di as error  "{err}fuzzy() only accepts sharpbw as a second input" 
			exit 125
		}
	}
	if `w' >= 3 {
		di as error  "{err}{cmd:fuzzy()} only accepts two inputs"  
		exit 125
	}
	
	**** DROP MISSINGS **********************************************
	qui drop if mi(`y') | mi(`x')
	if ("`fuzzy'"~="")   qui drop if mi(`fuzzyvar')
	if ("`cluster'"!="") qui drop if mi(`clustvar')
	if ("`covs'"~="") {
		qui ds `covs', alpha
		local covs_list = r(varlist)
		local ncovs: word count `covs_list'	
		foreach z in `covs_list' {
			qui drop if mi(`z')
		}
	}
	
	if ("`weights'"~="") {
	    qui drop if mi(`weights')
		qui drop if `weights'<=0
	}
		
	**** CHECK colinearity ******************************************
	local covs_drop_coll = 0	
	if ("`covs_drop'"=="") local covs_drop = "pinv"	
	if ("`covs'"~="") {	
		
	if ("`covs_drop'"=="invsym")  local covs_drop_coll = 1
	if ("`covs_drop'"=="pinv")    local covs_drop_coll = 2
	
	if ("`covs_drop'"!="off") {	
		
		qui _rmcoll `covs_list'
		local nocoll_controls_cat `r(varlist)'
		local nocoll_controls ""
		foreach myString of local nocoll_controls_cat {
			if ~strpos("`myString'", "o."){
				if ~strpos("`myString'", "MYRUNVAR"){
					local nocoll_controls "`nocoll_controls' `myString'"
				}
				}
			}			
		local covs_new `nocoll_controls'
		qui ds `covs_new', alpha
		local covs_list_new = r(varlist)
		local ncovs_new: word count `covs_list_new'
		
		if (`ncovs_new'<`ncovs') {
				local ncovs = "`ncovs_new'"
				local covs_list = "`covs_list_new'"
				di as error  "{err}Multicollinearity issue detected in {cmd:covs}. Redundant covariates were removed." 				
			}	
		}	
	}
	
				
	**** DEFAULTS ***************************************
	if ("`masspoints'"=="") local masspoints = "adjust"
	if ("`stdvars'"=="")    local stdvars    = "off"	
	if ("`bwrestrict'"=="") local bwrestrict = "on"	
	*****************************************************************
	
	qui su `x', d
	local N = r(N)
	local x_min = r(min)
	local x_max = r(max)
	local x_iq = r(p75)-r(p25)
	local x_sd = r(sd)
	
	if ("`deriv'">"0" & "`p'"=="" & "`q'"=="0") local p = `deriv'+1
	if ("`p'"=="")  local p = 1
	if ("`q'"=="0") local q = `p'+1

	**************************** BEGIN ERROR CHECKING ************************************************
	if ("`nochecks'"=="") {
			if (`c'<=`x_min' | `c'>=`x_max'){
			 di as error  "{err}{cmd:c()} should be set within the range of `x'"  
			 exit 125
			}
						
			if (`N'<20){
			 di as error  "{err}Not enough observations to perform bandwidth calculations"  
			 di as error  "{err}Estimates computed using entire sample"  
			 local bwselect= "Manual"
			
			qui su `x' if `x'<`c'
			local range_l = abs(r(max)-r(min))
			qui su `x' if `x'>=`c'
			local range_r = abs(r(max)-r(min))
			local bw_range = max(`range_l',`range_r')
			
			local h   = `bw_range'
			local b   = `bw_range'
			local h_l = `bw_range'
			local h_r = `bw_range'
			local b_l = `bw_range'
			local b_r = `bw_range'	
			}
			
			if ("`kernel'"~="uni" & "`kernel'"~="uniform" & "`kernel'"~="tri" & "`kernel'"~="triangular" & "`kernel'"~="epa" & "`kernel'"~="epanechnikov" & "`kernel'"~="" ){
			 di as error  "{err}{cmd:kernel()} incorrectly specified"  
			 exit 7
			}

			if ("`bwselect'"=="CCT" | "`bwselect'"=="IK" | "`bwselect'"=="CV" |"`bwselect'"=="cct" | "`bwselect'"=="ik" | "`bwselect'"=="cv"){
				di as error  "{err}{cmd:bwselect()} options IK, CCT and CV have been depricated. Please see help for new options"  
				exit 7
			}
	
			if  ("`bwselect'"!="mserd" & "`bwselect'"!="msetwo" & "`bwselect'"!="msesum" & "`bwselect'"!="msecomb1" & "`bwselect'"!="msecomb2"  & "`bwselect'"!="cerrd" & "`bwselect'"!="certwo" & "`bwselect'"!="cersum" & "`bwselect'"!="cercomb1" & "`bwselect'"!="cercomb2" & "`bwselect'"~="Manual"){
				di as error  "{err}{cmd:bwselect()} incorrectly specified"  
				exit 7
			}

			if ("`vce_select'"~="nn" & "`vce_select'"~="" & "`vce_select'"~="cluster" & "`vce_select'"~="nncluster" & "`vce_select'"~="hc1" & "`vce_select'"~="hc2" & "`vce_select'"~="hc3" & "`vce_select'"~="hc0"){ 
			 di as error  "{err}{cmd:vce()} incorrectly specified"  
			 exit 7
			}

			if ("`p'"<"0" | "`q'"<="0" | "`deriv'"<"0" | "`nnmatch'"<="0" ){
			 di as error  "{err}{cmd:p()}, {cmd:q()}, {cmd:deriv()}, {cmd:nnmatch()} should be positive"  
			 exit 411
			}
				
			if ("`p'">="`q'" & "`q'">"0"){
			 di as error  "{err}{cmd:q()} should be higher than {cmd:p()}"  
			 exit 125
			}
			
			if ("`deriv'">"`p'" & "`deriv'">"0" ){
			 di as error  "{err}{cmd:deriv()} can not be higher than {cmd:p()}"  
			 exit 125
			}

			if ("`p'">"0" ) {
				local p_round = round(`p')/`p'
				local q_round = round(`q')/`q'
				local d_round = round(`deriv'+1)/(`deriv'+1)
				local m_round = round(`nnmatch')/`nnmatch'

				if (`p_round'!=1 | `q_round'!=1 |`d_round'!=1 |`m_round'!=1 ){
				 di as error  "{err}{cmd:p()}, {cmd:q()}, {cmd:deriv()} and {cmd:nnmatch()} should be integers"  
				 exit 126
				}
			}
			if (`level'>100 | `level'<=0){
			 di as error  "{err}{cmd:level()}should be set between 0 and 100"  
			 exit 125
			}
	}
	*********************** END ERROR CHECKING ************************************************************
		
	if ("`vce_select'"=="nn" | "`masspoints'"=="check" | "`masspoints'"=="adjust") {
		sort `x', stable
		if ("`vce_select'"=="nn") {
			tempvar dups dupsid
			by `x': gen dups = _N
			by `x': gen dupsid = _n
		}
	}

	if ("`kernel'"=="epanechnikov" | "`kernel'"=="epa") {
		local kernel_type = "Epanechnikov"
		local C_c = 2.34
	}
	else if ("`kernel'"=="uniform" | "`kernel'"=="uni") {
		local kernel_type = "Uniform"
		local C_c = 1.843
	}
	else {
		local kernel_type = "Triangular"
		local C_c = 2.576
	}
	
	*** Start MATA ********************************************************

	mata{
	
	*** Preparing data
		Y = st_data(.,("`y'"), 0);	X = st_data(.,("`x'"), 0)		
		ind_l = selectindex(X:<`c'); ind_r = selectindex(X:>=`c')			
		X_l = X[ind_l];	X_r = X[ind_r]
		Y_l = Y[ind_l];	Y_r = Y[ind_r]
		dZ=dT=dC=Z_l=Z_r=T_l=T_r=C_l=C_r=fw_l=fw_r=g_l=g_r=dups_l=dups_r=dupsid_l=dupsid_r=g_l=g_r=eT_l=eT_r=eZ_l=eZ_r=indC_l=indC_r=eC_l=eC_r=0
		
		N   = length(X);	N_l = length(X_l);	N_r = length(X_r)
				
		if ("`covs'"~="") {
			Z   = st_data(.,tokens("`covs_list'"), 0); dZ  = cols(Z)
			Z_l = Z[ind_l,];	Z_r = Z[ind_r,]
		}
	
		if ("`fuzzy'"~="") {
			T = st_data(.,("`fuzzyvar'"), 0);	T_l = T[ind_l];	T_r = T[ind_r]; dT = 1
			if (variance(T_l)==0 | variance(T_r)==0){
				T_l = T_r = 0
				st_local("perf_comp","perf_comp")
			}
			if ("`sharpbw'"!=""){
				T_l = T_r = 0
				st_local("sharpbw","sharpbw")
			}
		}	
	
		if ("`cluster'"!="") {
			C  = st_data(.,("`clustvar'"), 0)
			C_l  = C[ind_l]; C_r  = C[ind_r]
			indC_l = order(C_l,1);  indC_r = order(C_r,1) 
			g_l = rows(panelsetup(C_l[indC_l],1));	g_r = rows(panelsetup(C_r[indC_r],1))
			st_numscalar("g_l",  g_l);     st_numscalar("g_r",   g_r)
		}	
	
		if ("`weights'"~="") {
			fw = st_data(.,("`weights'"), 0)
			fw_l = fw[ind_l];	fw_r = fw[ind_r]
		}
		
		if ("`vce_select'"=="nn") {
			dups      = st_data(.,("dups"), 0); dupsid    = st_data(.,("dupsid"), 0)
			dups_l    = dups[ind_l];    dups_r    = dups[ind_r]
			dupsid_l  = dupsid[ind_l];  dupsid_r  = dupsid[ind_r]
		}
		
		
		h_l = `h_l'
		h_r = `h_r'
		b_l = `b_l'
		b_r = `b_r'

	***********************************************************************
	******** Computing bandwidth selector *********************************
	***********************************************************************		
masspoints_found = 0
	
	if ("`h'"=="") {	
	
		BWp = min((`x_sd',`x_iq'/1.349))
		x_sd = y_sd = 1
		c = `c'
		*** Starndardized ******************
		if  ("`stdvars'"=="on")  {	
			y_sd = sqrt(variance(Y))
			x_sd = sqrt(variance(X))
			X_l = X_l/x_sd;	X_r = X_r/x_sd
			Y_l = Y_l/y_sd;	Y_r = Y_r/y_sd
			c = `c'/x_sd
			BWp = min((1, (`x_iq'/x_sd)/1.349))
		}		
		x_l_min = min(X_l);	x_l_max = max(X_l)
		x_r_min = min(X_r);	x_r_max = max(X_r)
	
		range_l = c - x_l_min
		range_r = x_r_max - c  
		************************************		
		
		mN = `N'
		bwcheck = `bwcheck'
		covs_drop_coll = `covs_drop_coll'

		if ("`masspoints'"=="check" | "`masspoints'"=="adjust") {
			X_uniq_l = sort(uniqrows(X_l),-1)
			X_uniq_r = uniqrows(X_r)
			M_l = length(X_uniq_l)
			M_r = length(X_uniq_r)
			M = M_l + M_r
			st_numscalar("M_l", M_l); st_numscalar("M_r", M_r)
			mass_l = 1-M_l/N_l
			mass_r = 1-M_r/N_r				
			if (mass_l>=0.2 | mass_r>=0.2){
				masspoints_found = 1
				display("{err}Mass points detected in the running variable.")
				if ("`masspoints'"=="adjust" & "`bwcheck'"=="0") bwcheck = 10
				if ("`masspoints'"=="check") display("{err}Try using option {cmd:masspoints(adjust)}.")
			}				
		}	
				
		c_bw = `C_c'*BWp*mN^(-1/5)
		if ("`masspoints'"=="adjust") c_bw = `C_c'*BWp*M^(-1/5)
		if  ("`bwrestrict'"=="on") {
			bw_max = max((range_l,range_r))
			c_bw = min((c_bw, bw_max))
		}
		if (bwcheck > 0) {
			bwcheck_l = min((bwcheck, M_l))
			bwcheck_r = min((bwcheck, M_r))
			bw_min_l = abs(X_uniq_l:-c)[bwcheck_l] + 1e-8
			bw_min_r = abs(X_uniq_r:-c)[bwcheck_r] + 1e-8
			c_bw = max((c_bw, bw_min_l, bw_min_r))
		}		
		
			
		*** Step 1: d_bw
		C_d_l = rdrobust_bw(Y_l, X_l, T_l, Z_l, C_l, fw_l, c=c, o=`q'+1, nu=`q'+1, o_B=`q'+2, h_V=c_bw, h_B=range_l+1e-8, 0, "`vce_select'", `nnmatch', "`kernel'", dups_l, dupsid_l, covs_drop_coll)
		C_d_r = rdrobust_bw(Y_r, X_r, T_r, Z_r, C_r, fw_r, c=c, o=`q'+1, nu=`q'+1, o_B=`q'+2, h_V=c_bw, h_B=range_r+1e-8, 0, "`vce_select'", `nnmatch', "`kernel'", dups_r, dupsid_r, covs_drop_coll)
		if (C_d_l[1]==0 | C_d_l[2]==0 | C_d_r[1]==0 | C_d_r[2]==0 |C_d_l[1]==. | C_d_l[2]==. | C_d_l[3]==. |C_d_r[1]==. | C_d_r[2]==. | C_d_r[3]==.) printf("{err}Not enough variability to compute the preliminary bandwidth. Try checking for mass points with option {cmd:masspoints(check)}.\n")  
	
		*** BW-TWO
		if  ("`bwselect'"=="msetwo" |  "`bwselect'"=="certwo" | "`bwselect'"=="msecomb2" | "`bwselect'"=="cercomb2" )  {		
			* Preliminar bw
			d_bw_l = (  (C_d_l[1]              /   C_d_l[2]^2)    * (`N'/mN)         )^C_d_l[4] 
			d_bw_r = (  (C_d_r[1]              /   C_d_r[2]^2)    * (`N'/mN)         )^C_d_l[4]
			if  ("`bwrestrict'"=="on") {
			d_bw_l = min((d_bw_l, range_l))
			d_bw_r = min((d_bw_r, range_r))
			}
			if (bwcheck > 0) {
				d_bw_l = max((d_bw_l, bw_min_l))
				d_bw_r = max((d_bw_r, bw_min_r))
			}
			* Bias bw
			C_b_l  = rdrobust_bw(Y_l, X_l, T_l, Z_l, C_l, fw_l, c=c, o=`q', nu=`p'+1, o_B=`q'+1, h_V=c_bw, h_B=d_bw_l, `scaleregul', "`vce_select'", `nnmatch', "`kernel'", dups_l, dupsid_l, covs_drop_coll)
			b_bw_l = (  (C_b_l[1]              /   (C_b_l[2]^2 + `scaleregul'*C_b_l[3]))  * (`N'/mN)     )^C_b_l[4]
			C_b_r  = rdrobust_bw(Y_r, X_r, T_r, Z_r, C_r, fw_r, c=c, o=`q', nu=`p'+1, o_B=`q'+1, h_V=c_bw, h_B=d_bw_r, `scaleregul', "`vce_select'", `nnmatch', "`kernel'", dups_r, dupsid_r, covs_drop_coll)
			b_bw_r = (  (C_b_r[1]              /   (C_b_r[2]^2 + `scaleregul'*C_b_r[3]))   * (`N'/mN)    )^C_b_l[4]
			if  ("`bwrestrict'"=="on") {
			b_bw_l = min((b_bw_l, range_l))
			b_bw_r = min((b_bw_r, range_r))
			}
			* Main bw
			C_h_l  = rdrobust_bw(Y_l, X_l, T_l, Z_l, C_l, fw_l, c=c, o=`p', nu=`deriv', o_B=`q', h_V=c_bw, h_B=b_bw_l, `scaleregul', "`vce_select'", `nnmatch', "`kernel'", dups_l, dupsid_l, covs_drop_coll)
			h_bw_l = (  (C_h_l[1]              /   (C_h_l[2]^2 + `scaleregul'*C_h_l[3]))  * (`N'/mN)       )^C_h_l[4]
			C_h_r  = rdrobust_bw(Y_r, X_r, T_r, Z_r, C_r, fw_r, c=c, o=`p', nu=`deriv', o_B=`q', h_V=c_bw, h_B=b_bw_r, `scaleregul', "`vce_select'", `nnmatch', "`kernel'", dups_r, dupsid_r, covs_drop_coll)
			h_bw_r = (  (C_h_r[1]              /   (C_h_r[2]^2 + `scaleregul'*C_h_r[3]))  * (`N'/mN)       )^C_h_l[4]
			if  ("`bwrestrict'"=="on") {
			h_bw_l = min((h_bw_l, range_l))
			h_bw_r = min((h_bw_r, range_r))
			}
		}
		
		*** BW-SUM
		if  ("`bwselect'"=="msesum" | "`bwselect'"=="cersum" |  "`bwselect'"=="msecomb1" | "`bwselect'"=="msecomb2" |  "`bwselect'"=="cercomb1" | "`bwselect'"=="cercomb2")  {
			* Preliminar bw
			d_bw_s = ( ((C_d_l[1] + C_d_r[1])  /  (C_d_r[2] + C_d_l[2])^2)  * (`N'/mN)  )^C_d_l[4]
			if  ("`bwrestrict'"=="on")  d_bw_s = min((d_bw_s, bw_max))
			if (bwcheck > 0) d_bw_s = max((d_bw_s, bw_min_l, bw_min_r))		
			* Bias bw
			C_b_l  = rdrobust_bw(Y_l, X_l, T_l, Z_l, C_l, fw_l, c=c, o=`q', nu=`p'+1, o_B=`q'+1, h_V=c_bw, h_B=d_bw_s, `scaleregul', "`vce_select'", `nnmatch', "`kernel'", dups_l, dupsid_l, covs_drop_coll)
			C_b_r  = rdrobust_bw(Y_r, X_r, T_r, Z_r, C_r, fw_r, c=c, o=`q', nu=`p'+1, o_B=`q'+1, h_V=c_bw, h_B=d_bw_s, `scaleregul', "`vce_select'", `nnmatch', "`kernel'", dups_r, dupsid_r, covs_drop_coll)
			b_bw_s = ( ((C_b_l[1] + C_b_r[1])  /  ((C_b_r[2] + C_b_l[2])^2 + `scaleregul'*(C_b_r[3]+C_b_l[3])))  * (`N'/mN)  )^C_b_l[4]
			if  ("`bwrestrict'"=="on") b_bw_s = min((b_bw_s, bw_max))
			* Main bw
			C_h_l  = rdrobust_bw(Y_l, X_l, T_l, Z_l, C_l, fw_l, c=c, o=`p', nu=`deriv', o_B=`q', h_V=c_bw, h_B=b_bw_s, `scaleregul', "`vce_select'", `nnmatch', "`kernel'", dups_l, dupsid_l, covs_drop_coll)
			C_h_r  = rdrobust_bw(Y_r, X_r, T_r, Z_r, C_r, fw_r, c=c, o=`p', nu=`deriv', o_B=`q', h_V=c_bw, h_B=b_bw_s, `scaleregul', "`vce_select'", `nnmatch', "`kernel'", dups_r, dupsid_r, covs_drop_coll)
			h_bw_s = ( ((C_h_l[1] + C_h_r[1])  /  ((C_h_r[2] + C_h_l[2])^2 + `scaleregul'*(C_h_r[3] + C_h_l[3])))  * (`N'/mN)  )^C_h_l[4]			
			if  ("`bwrestrict'"=="on") h_bw_s = min((h_bw_s, bw_max))
		}
		
		*** RD
		if  ("`bwselect'"=="mserd" | "`bwselect'"=="cerrd" | "`bwselect'"=="msecomb1" | "`bwselect'"=="msecomb2" | "`bwselect'"=="cercomb1" | "`bwselect'"=="cercomb2" | "`bwselect'"=="") {
			* Preliminar bw
			d_bw_d = ( ((C_d_l[1] + C_d_r[1])  /  (C_d_r[2] - C_d_l[2])^2)  * (`N'/mN)   )^C_d_l[4]
			if  ("`bwrestrict'"=="on") d_bw_d = min((d_bw_d, bw_max))
			
			if (bwcheck > 0) d_bw_d = max((d_bw_d, bw_min_l, bw_min_r))		
			* Bias bw
			C_b_l  = rdrobust_bw(Y_l, X_l, T_l, Z_l, C_l, fw_l, c=c, o=`q', nu=`p'+1, o_B=`q'+1, h_V=c_bw, h_B=d_bw_d, `scaleregul', "`vce_select'", `nnmatch', "`kernel'", dups_l, dupsid_l, covs_drop_coll)
			C_b_r  = rdrobust_bw(Y_r, X_r, T_r, Z_r, C_r, fw_r, c=c, o=`q', nu=`p'+1, o_B=`q'+1, h_V=c_bw, h_B=d_bw_d, `scaleregul', "`vce_select'", `nnmatch', "`kernel'", dups_r, dupsid_r, covs_drop_coll)
			b_bw_d = ( ((C_b_l[1] + C_b_r[1])  /  ((C_b_r[2] - C_b_l[2])^2 + `scaleregul'*(C_b_r[3] + C_b_l[3])))  * (`N'/mN)    )^C_b_l[4]
			if  ("`bwrestrict'"=="on") b_bw_d = min((b_bw_d, bw_max))
			
			* Main bw
			C_h_l  = rdrobust_bw(Y_l, X_l, T_l, Z_l, C_l, fw_l, c=c, o=`p', nu=`deriv', o_B=`q', h_V=c_bw, h_B=b_bw_d, `scaleregul', "`vce_select'", `nnmatch', "`kernel'", dups_l, dupsid_l, covs_drop_coll)
			C_h_r  = rdrobust_bw(Y_r, X_r, T_r, Z_r, C_r, fw_r, c=c, o=`p', nu=`deriv', o_B=`q', h_V=c_bw, h_B=b_bw_d, `scaleregul', "`vce_select'", `nnmatch', "`kernel'", dups_r, dupsid_r, covs_drop_coll)
			h_bw_d = ( ((C_h_l[1] + C_h_r[1])  /  ((C_h_r[2] - C_h_l[2])^2 + `scaleregul'*(C_h_r[3] + C_h_l[3])))  * (`N'/mN)   )^C_h_l[4]
			if  ("`bwrestrict'"=="on") h_bw_d = min((h_bw_d, bw_max))
			
		}	
		


		if (C_b_l[1]==0 | C_b_l[2]==0 | C_b_r[1]==0 | C_b_r[2]==0 |C_b_l[1]==. | C_b_l[2]==. | C_b_l[3]==. | C_b_r[1]==. | C_b_r[2]==. | C_b_r[3]==.) printf("{err}Not enough variability to compute the bias bandwidth (b). Try checking for mass points with option {cmd:masspoints(check)}. \n")  
		if (C_h_l[1]==0 | C_h_l[2]==0 | C_h_r[1]==0 | C_h_r[2]==0 |C_h_l[1]==. | C_h_l[2]==. | C_h_l[3]==. | C_h_r[1]==. | C_h_r[2]==. | C_h_r[3]==.) printf("{err}Not enough variability to compute the loc. poly. bandwidth (h). Try checking for mass points with option {cmd:masspoints(check)}.\n") 
	
		cer_h = mN^(-(`p'/((3+`p')*(3+2*`p'))))
		if ("`cluster'"!="") cer_h = (g_l+g_r)^(-(`p'/((3+`p')*(3+2*`p'))))
		cer_b = 1	
			
		if  ("`bwselect'"=="mserd" | "`bwselect'"=="cerrd" | "`bwselect'"=="msecomb1" | "`bwselect'"=="msecomb2" | "`bwselect'"=="cercomb1" | "`bwselect'"=="cercomb2") {
			h_l = h_r = h_mserd = x_sd*h_bw_d
			b_l = b_r = b_mserd = x_sd*b_bw_d
		}	
		if  ("`bwselect'"=="msesum" | "`bwselect'"=="cersum" |  "`bwselect'"=="msecomb1" | "`bwselect'"=="msecomb2" |  "`bwselect'"=="cercomb1" | "`bwselect'"=="cercomb2")  {
			h_l = h_r = h_msesum = x_sd*h_bw_s
			b_l = b_r = b_msesum = x_sd*b_bw_s
		}
		if  ("`bwselect'"=="msetwo" |  "`bwselect'"=="certwo" | "`bwselect'"=="msecomb2" | "`bwselect'"=="cercomb2")  {		
			h_l = h_msetwo_l = x_sd*h_bw_l
			h_r = h_msetwo_r = x_sd*h_bw_r
			b_l = b_msetwo_l = x_sd*b_bw_l
			b_r = b_msetwo_r = x_sd*b_bw_r
		}
		if  ("`bwselect'"=="msecomb1" | "`bwselect'"=="cercomb1") {
			h_l = h_r = h_msecomb1 = min((h_mserd,h_msesum))
			b_l = b_r = b_msecomb1 = min((b_mserd,b_msesum))
		}
		if  ("`bwselect'"=="msecomb2" | "`bwselect'"=="cercomb2") {
			h_l = (sort((h_mserd,h_msesum,h_msetwo_l)',1))[2]
			h_r = (sort((h_mserd,h_msesum,h_msetwo_r)',1))[2]
			b_l = (sort((b_mserd,b_msesum,b_msetwo_l)',1))[2]
			b_r = (sort((b_mserd,b_msesum,b_msetwo_r)',1))[2]
		}		
		if  ("`bwselect'"=="cerrd" | "`bwselect'"=="cersum" | "`bwselect'"=="certwo" | "`bwselect'"=="cercomb1" | "`bwselect'"=="cercomb2"){
			h_l = h_l*cer_h
			h_r = h_r*cer_h
			b_l = b_l*cer_b
			b_r = b_r*cer_b
		}
		
		rho = `rho'
		if (rho>0)  {
			b_l = h_l/rho
			b_r = h_r/rho
		}
					
		*** De-Starndardized *********************************
		c = `c'*x_sd
		X_uniq_l = X_uniq_l*x_sd
		X_uniq_r = X_uniq_r*x_sd
		X_l = X_l*x_sd;	X_r = X_r*x_sd
		Y_l = Y_l*y_sd;	Y_r = Y_r*y_sd
		range_l = range_l*x_sd
		range_r = range_r*x_sd  
		*****************************************************

		
		} /* close if for bw selector */
	
	}
	

	mata{
	
		*** Estimation and Inference
		
		c = strtoreal("`c'")
	
		w_h_l = rdrobust_kweight(X_l,`c',h_l,"`kernel'");	w_h_r = rdrobust_kweight(X_r,`c',h_r,"`kernel'")
		w_b_l = rdrobust_kweight(X_l,`c',b_l,"`kernel'");	w_b_r = rdrobust_kweight(X_r,`c',b_r,"`kernel'")
		
		if ("`weights'"~="") {
			w_h_l = fw_l:*w_h_l;	w_h_r = fw_r:*w_h_r
			w_b_l = fw_l:*w_b_l;	w_b_r = fw_r:*w_b_r			
		}
		
		ind_h_l = selectindex(w_h_l:> 0);		ind_h_r = selectindex(w_h_r:> 0)
		ind_b_l = selectindex(w_b_l:> 0);		ind_b_r = selectindex(w_b_r:> 0)
		N_h_l = length(ind_h_l);	N_b_l = length(ind_b_l)
		N_h_r = length(ind_h_r);	N_b_r = length(ind_b_r)
		
		if (N_h_l<10 | N_h_r<10 | N_b_l<10 | N_b_r<10){
		 display("{err}Estimates might be unreliable due to low number of effective observations.")
		}
		
		ind_l = ind_b_l; ind_r = ind_b_r
		if (h_l>b_l) ind_l = ind_h_l   
		if (h_r>b_r) ind_r = ind_h_r   
		eN_l = length(ind_l); eN_r = length(ind_r)
		eY_l  = Y_l[ind_l];	eY_r  = Y_r[ind_r]
		eX_l  = X_l[ind_l];	eX_r  = X_r[ind_r]
		W_h_l = w_h_l[ind_l];	W_h_r = w_h_r[ind_r]
		W_b_l = w_b_l[ind_l];	W_b_r = w_b_r[ind_r]
		
		edups_l = edups_r = edupsid_l= edupsid_r = 0	
		if ("`vce_select'"=="nn") {
			edups_l   = dups_l[ind_l];	  	    edups_r   = dups_r[ind_r]
			edupsid_l = dupsid_l[ind_l];	    edupsid_r = dupsid_r[ind_r]
		}
		
		u_l = (eX_l:-`c')/h_l;	u_r = (eX_r:-`c')/h_r;
		R_q_l = J(eN_l,(`q'+1),.); R_q_r = J(eN_r,(`q'+1),.)
		for (j=1; j<=(`q'+1); j++)  {
			R_q_l[.,j] = (eX_l:-`c'):^(j-1);  R_q_r[.,j] = (eX_r:-`c'):^(j-1)
		}
		R_p_l = R_q_l[,1::(`p'+1)]; R_p_r = R_q_r[,1::(`p'+1)]	
	
		********************************************************************************
		************ Computing RD estimates ********************************************
		********************************************************************************
		L_l = quadcross(R_p_l:*W_h_l,u_l:^(`p'+1)); L_r = quadcross(R_p_r:*W_h_r,u_r:^(`p'+1)) 
			invG_q_l  = cholinv(quadcross(R_q_l,W_b_l,R_q_l));	invG_q_r  = cholinv(quadcross(R_q_r,W_b_r,R_q_r))
			invG_p_l  = cholinv(quadcross(R_p_l,W_h_l,R_p_l));	invG_p_r  = cholinv(quadcross(R_p_r,W_h_r,R_p_r)) 
		
		if (rank(invG_p_l)==. | rank(invG_p_r)==. | rank(invG_q_l)==. | rank(invG_q_r)==. ){
		display("{err}Invertibility problem: check variability of running variable around cutoff. Try checking for mass points with option {cmd:masspoints(check)}.")
			exit(1)
		}
		
		e_p1 = J((`q'+1),1,0); e_p1[`p'+2]=1
		e_v  = J((`p'+1),1,0); e_v[`deriv'+1]=1
		Q_q_l = ((R_p_l:*W_h_l)' - h_l^(`p'+1)*(L_l*e_p1')*((invG_q_l*R_q_l')':*W_b_l)')'
		Q_q_r = ((R_p_r:*W_h_r)' - h_r^(`p'+1)*(L_r*e_p1')*((invG_q_r*R_q_r')':*W_b_r)')'
		D_l = eY_l; D_r = eY_r		
		
		if ("`fuzzy'"~="") {
			T    = st_data(.,("`fuzzyvar'"), 0);	dT = 1
			T_l  = select(T,X:<`c');  eT_l  = T_l[ind_l]
			T_r  = select(T,X:>=`c'); eT_r  = T_r[ind_r]
			D_l  = D_l,eT_l; D_r = D_r,eT_r
		}
		
		if ("`covs'"~="") {
			eZ_l = Z_l[ind_l,]; eZ_r = Z_r[ind_r,]
			D_l  = D_l,eZ_l; D_r = D_r,eZ_r
			U_p_l = quadcross(R_p_l:*W_h_l,D_l); U_p_r = quadcross(R_p_r:*W_h_r,D_r)
		}
		
		if ("`cluster'"~="") {
			eC_l  = C_l[ind_l];	     eC_r  = C_r[ind_r]
			indC_l = order(eC_l,1);  indC_r = order(eC_r,1) 
			g_l = rows(panelsetup(eC_l[indC_l],1));	g_r = rows(panelsetup(eC_r[indC_r],1))
		}
		
		beta_p_l = invG_p_l*quadcross(R_p_l:*W_h_l,D_l); beta_q_l = invG_q_l*quadcross(R_q_l:*W_b_l,D_l); beta_bc_l = invG_p_l*quadcross(Q_q_l,D_l) 
		beta_p_r = invG_p_r*quadcross(R_p_r:*W_h_r,D_r); beta_q_r = invG_q_r*quadcross(R_q_r:*W_b_r,D_r); beta_bc_r = invG_p_r*quadcross(Q_q_r,D_r)
		beta_p  = beta_p_r  - beta_p_l
		beta_q  = beta_q_r  - beta_q_l
		beta_bc = beta_bc_r - beta_bc_l
		
		************************************ No Covariates **********************************
		
		if (dZ==0) {		
				tau_cl = tau_Y_cl = `scalepar'*factorial(`deriv')*beta_p[(`deriv'+1),1]
				tau_bc = tau_Y_bc = `scalepar'*factorial(`deriv')*beta_bc[(`deriv'+1),1]
				s_Y = 1				
				tau_Y_cl_l = `scalepar'*factorial(`deriv')*beta_p_l[(`deriv'+1),1]
				tau_Y_cl_r = `scalepar'*factorial(`deriv')*beta_p_r[(`deriv'+1),1]
				tau_Y_bc_l = `scalepar'*factorial(`deriv')*beta_bc_l[(`deriv'+1),1]
				tau_Y_bc_r = `scalepar'*factorial(`deriv')*beta_bc_r[(`deriv'+1),1]				
				bias_l = tau_Y_cl_l - tau_Y_bc_l
				bias_r = tau_Y_cl_r - tau_Y_bc_r 		
	
				beta_Y_p_l = `scalepar'*factorial(`deriv')*beta_p_l[,1]
				beta_Y_p_r = `scalepar'*factorial(`deriv')*beta_p_r[,1]

				*** Fuzzy RD ********************
				if (dT>0) {
					tau_T_cl =  factorial(`deriv')*beta_p[(`deriv'+1),2]
					tau_T_bc = 	factorial(`deriv')*beta_bc[(`deriv'+1),2]
					
					beta_T_p_l = factorial(`deriv')*beta_p_l[,2]
					beta_T_p_r = factorial(`deriv')*beta_p_r[,2]
					
					s_Y = (1/tau_T_cl \ -(tau_Y_cl/tau_T_cl^2))
					B_F = tau_Y_cl-tau_Y_bc \ tau_T_cl-tau_T_bc
					tau_cl = tau_Y_cl/tau_T_cl
					tau_bc = tau_cl - s_Y'*B_F
					sV_T = 0 \ 1										
					tau_T_cl_l =  factorial(`deriv')*beta_p_l[(`deriv'+1),2]
					tau_T_cl_r =  factorial(`deriv')*beta_p_r[(`deriv'+1),2]
					tau_T_bc_l =  factorial(`deriv')*beta_bc_l[(`deriv'+1),2]
					tau_T_bc_r =  factorial(`deriv')*beta_bc_r[(`deriv'+1),2]					
					B_F_l = tau_Y_cl_l-tau_Y_bc_l \ tau_T_cl_l-tau_T_bc_l
					B_F_r = tau_Y_cl_r-tau_Y_bc_r \ tau_T_cl_r-tau_T_bc_r					
					bias_l = s_Y'*B_F_l
					bias_r = s_Y'*B_F_r		
		
				
				}	
				
		}
		
		*********************************** Covariates **********************************
				
		if (dZ>0) {				
			ZWD_p_l  = quadcross(eZ_l,W_h_l,D_l)
			ZWD_p_r  = quadcross(eZ_r,W_h_r,D_r)
			colsZ = (2+dT)::(2+dT+dZ-1)
			UiGU_p_l =  quadcross(U_p_l[,colsZ],invG_p_l*U_p_l) 
			UiGU_p_r =  quadcross(U_p_r[,colsZ],invG_p_r*U_p_r) 
			ZWZ_p_l = ZWD_p_l[,colsZ] - UiGU_p_l[,colsZ] 
			ZWZ_p_r = ZWD_p_r[,colsZ] - UiGU_p_r[,colsZ]     
			ZWY_p_l = ZWD_p_l[,1::1+dT] - UiGU_p_l[,1::1+dT] 
			ZWY_p_r = ZWD_p_r[,1::1+dT] - UiGU_p_r[,1::1+dT]     
			ZWZ_p = ZWZ_p_r + ZWZ_p_l
			ZWY_p = ZWY_p_r + ZWY_p_l
			if ("`covs_drop_coll'"=="0") gamma_p = cholinv(ZWZ_p)*ZWY_p
			if ("`covs_drop_coll'"=="1") gamma_p =  invsym(ZWZ_p)*ZWY_p
			if ("`covs_drop_coll'"=="2") gamma_p =    pinv(ZWZ_p)*ZWY_p
	
			s_Y = (1 \  -gamma_p[,1])
			
			*** Sharp RD ********************
			if (dT==0) {
				tau_cl = `scalepar'*s_Y'*beta_p[(`deriv'+1),]'
				tau_bc = `scalepar'*s_Y'*beta_bc[(`deriv'+1),]'				
				tau_Y_cl_l = `scalepar'*s_Y'*beta_p_l[(`deriv'+1),]'
				tau_Y_cl_r = `scalepar'*s_Y'*beta_p_r[(`deriv'+1),]'
				tau_Y_bc_l = `scalepar'*s_Y'*beta_bc_l[(`deriv'+1),]'
				tau_Y_bc_r = `scalepar'*s_Y'*beta_bc_r[(`deriv'+1),]'				
				bias_l = tau_Y_cl_l-tau_Y_bc_l
				bias_r = tau_Y_cl_r-tau_Y_bc_r 		
				
				beta_Y_p_l = `scalepar'*factorial(`deriv')*(s_Y'*beta_p_l')'
				beta_Y_p_r = `scalepar'*factorial(`deriv')*(s_Y'*beta_p_r')	'				
			}
			
			*** Fuzzy RD ********************
			if (dT>0) {
					s_T  = 1 \ -gamma_p[,2]
					sV_T = (0 \ 1 \ -gamma_p[,2] )
					tau_Y_cl   = `scalepar'*factorial(`deriv')*s_Y'*vec((beta_p[  (`deriv'+1),1], beta_p[  (`deriv'+1),colsZ]))
					tau_Y_cl_l = `scalepar'*factorial(`deriv')*s_Y'*vec((beta_p_l[(`deriv'+1),1], beta_p_l[(`deriv'+1),colsZ]))
					tau_Y_cl_r = `scalepar'*factorial(`deriv')*s_Y'*vec((beta_p_r[(`deriv'+1),1], beta_p_r[(`deriv'+1),colsZ]))
			
					tau_Y_bc   = `scalepar'*factorial(`deriv')*s_Y'*vec((beta_bc[  (`deriv'+1),1], beta_bc[  (`deriv'+1),colsZ]))
					tau_Y_bc_l = `scalepar'*factorial(`deriv')*s_Y'*vec((beta_bc_l[(`deriv'+1),1], beta_bc_l[(`deriv'+1),colsZ]))
					tau_Y_bc_r = `scalepar'*factorial(`deriv')*s_Y'*vec((beta_bc_r[(`deriv'+1),1], beta_bc_r[(`deriv'+1),colsZ]))	
					
					tau_T_cl   = factorial(`deriv')*s_T'*vec((beta_p[  (`deriv'+1),2], beta_p[  (`deriv'+1),colsZ]))
					tau_T_cl_l = factorial(`deriv')*s_T'*vec((beta_p_l[(`deriv'+1),2], beta_p_l[(`deriv'+1),colsZ]))
					tau_T_cl_r = factorial(`deriv')*s_T'*vec((beta_p_r[(`deriv'+1),2], beta_p_r[(`deriv'+1),colsZ]))
					
					tau_T_bc =   factorial(`deriv')*s_T'*vec((beta_bc[  (`deriv'+1),2], beta_bc[  (`deriv'+1),colsZ]))
					tau_T_bc_l = factorial(`deriv')*s_T'*vec((beta_bc_l[(`deriv'+1),2], beta_bc_l[(`deriv'+1),colsZ]))
					tau_T_bc_r = factorial(`deriv')*s_T'*vec((beta_bc_r[(`deriv'+1),2], beta_bc_r[(`deriv'+1),colsZ]))
					
					beta_Y_p_l = `scalepar'*factorial(`deriv')*(s_Y'*(beta_p_l[,1], beta_p_l[,colsZ])')'
					beta_Y_p_r = `scalepar'*factorial(`deriv')*(s_Y'*(beta_p_r[,1], beta_p_r[,colsZ])')'
					beta_T_p_l =            factorial(`deriv')*(s_T'*(beta_p_l[,2], beta_p_l[,colsZ])')'
					beta_T_p_r =            factorial(`deriv')*(s_T'*(beta_p_r[,2], beta_p_r[,colsZ])')'
					
					
					B_F = tau_Y_cl-tau_Y_bc \ tau_T_cl-tau_T_bc
					s_Y = 1/tau_T_cl \ -(tau_Y_cl/tau_T_cl^2)
					tau_cl = tau_Y_cl/tau_T_cl
					tau_bc = tau_cl - s_Y'*B_F
					
					B_F_l = tau_Y_cl_l-tau_Y_bc_l \ tau_T_cl_l-tau_T_bc_l
					B_F_r = tau_Y_cl_r-tau_Y_bc_r \ tau_T_cl_r-tau_T_bc_r
					
					bias_l = s_Y'*B_F_l
					bias_r = s_Y'*B_F_r
					
					s_Y = (1/tau_T_cl \ -(tau_Y_cl/tau_T_cl^2) \ -(1/tau_T_cl)*gamma_p[,1] + (tau_Y_cl/tau_T_cl^2)*gamma_p[,2])
			}
		}
			
		**************************************************************************
		************ Computing variance-covariance matrix ************************
		**************************************************************************
		hii_p_l=hii_p_r=hii_q_l=hii_q_r=predicts_p_l=predicts_p_r=predicts_q_l=predicts_q_r=0
		if ("`vce_select'"=="hc0" | "`vce_select'"=="hc1" | "`vce_select'"=="hc2" | "`vce_select'"=="hc3") {
			predicts_p_l=R_p_l*beta_p_l
			predicts_p_r=R_p_r*beta_p_r
			predicts_q_l=R_q_l*beta_q_l
			predicts_q_r=R_q_r*beta_q_r
			
			if ("`vce_select'"=="hc2" | "`vce_select'"=="hc3") {
				hii_p_l = rowsum((R_p_l*invG_p_l):*(R_p_l:*W_h_l))
				hii_p_r = rowsum((R_p_r*invG_p_r):*(R_p_r:*W_h_r))
				
				
				if ("`vleverage'"=="") {
				
					hii_q_l = rowsum((R_q_l*invG_q_l):*(R_q_l:*W_b_l))
					hii_q_r = rowsum((R_q_r*invG_q_r):*(R_q_r:*W_b_r))
				
				}
				else {
				
					hii_q_l = hii_p_l
					hii_q_r = hii_p_r
				
				}
				
			}
			
		}
			
		res_h_l = rdrobust_res(eX_l, eY_l, eT_l, eZ_l, predicts_p_l, hii_p_l, "`vce_select'", `nnmatch', edups_l, edupsid_l, `p'+1)
		res_h_r = rdrobust_res(eX_r, eY_r, eT_r, eZ_r, predicts_p_r, hii_p_r, "`vce_select'", `nnmatch', edups_r, edupsid_r, `p'+1)
		
		if ("`vce_select'"=="nn") {
				res_b_l = res_h_l;	res_b_r = res_h_r
		}
		else {
		
				res_b_l = rdrobust_res(eX_l, eY_l, eT_l, eZ_l, predicts_q_l, hii_q_l, "`vce_select'", `nnmatch', edups_l, edupsid_l, `q'+1)
				res_b_r = rdrobust_res(eX_r, eY_r, eT_r, eZ_r, predicts_q_r, hii_q_r, "`vce_select'", `nnmatch', edups_r, edupsid_r, `q'+1)
		
		}

		V_Y_cl_l = invG_p_l*rdrobust_vce(dT+dZ, s_Y, R_p_l:*W_h_l, res_h_l, eC_l, indC_l)*invG_p_l
		V_Y_cl_r = invG_p_r*rdrobust_vce(dT+dZ, s_Y, R_p_r:*W_h_r, res_h_r, eC_r, indC_r)*invG_p_r
		V_Y_bc_l = invG_p_l*rdrobust_vce(dT+dZ, s_Y, Q_q_l, res_b_l, eC_l, indC_l)*invG_p_l
		V_Y_bc_r = invG_p_r*rdrobust_vce(dT+dZ, s_Y, Q_q_r, res_b_r, eC_r, indC_r)*invG_p_r
		V_tau_cl = (`scalepar')^2*factorial(`deriv')^2*(V_Y_cl_l+V_Y_cl_r)[`deriv'+1,`deriv'+1]
		V_tau_rb = (`scalepar')^2*factorial(`deriv')^2*(V_Y_bc_l+V_Y_bc_r)[`deriv'+1,`deriv'+1]
		se_tau_cl = sqrt(V_tau_cl);	se_tau_rb = sqrt(V_tau_rb)

		if ("`fuzzy'"!="") {
			V_T_cl_l = invG_p_l*rdrobust_vce(dT+dZ, sV_T, R_p_l:*W_h_l, res_h_l, eC_l, indC_l)*invG_p_l
			V_T_cl_r = invG_p_r*rdrobust_vce(dT+dZ, sV_T, R_p_r:*W_h_r, res_h_r, eC_r, indC_r)*invG_p_r
			V_T_bc_l = invG_p_l*rdrobust_vce(dT+dZ, sV_T, Q_q_l, res_b_l, eC_l, indC_l)*invG_p_l
			V_T_bc_r = invG_p_r*rdrobust_vce(dT+dZ, sV_T, Q_q_r, res_b_r, eC_r, indC_r)*invG_p_r
			V_T_cl = factorial(`deriv')^2*(V_T_cl_l+V_T_cl_r)[`deriv'+1,`deriv'+1]
			V_T_rb = factorial(`deriv')^2*(V_T_bc_l+V_T_bc_r)[`deriv'+1,`deriv'+1]
			se_tau_T_cl = sqrt(V_T_cl);	se_tau_T_rb = sqrt(V_T_rb)
		}
		
	
		
		**** Stored results
		st_numscalar("N", N)
		st_numscalar("N_l", N_l)
		st_numscalar("N_r", N_r)
		st_numscalar("x_l_min", x_l_min)
		st_numscalar("x_l_max", x_l_max)
		st_numscalar("x_r_min", x_r_min)
		st_numscalar("x_r_max", x_r_max)
	
		st_numscalar("h_l", h_l)
		st_numscalar("h_r", h_r)
		st_numscalar("b_l", b_l)
		st_numscalar("b_r", b_r)
	
		st_numscalar("quant", -invnormal(abs((1-(`level'/100))/2)))
		st_numscalar("N_h_l", N_h_l);	st_numscalar("N_b_l", N_b_l)
		st_numscalar("N_h_r", N_h_r);	st_numscalar("N_b_r", N_b_r)
		
		st_numscalar("tau_cl", tau_cl); st_numscalar("se_tau_cl", se_tau_cl)
		st_numscalar("tau_bc", tau_bc);	st_numscalar("se_tau_rb", se_tau_rb)
		
		st_numscalar("tau_Y_cl_r", tau_Y_cl_r); st_numscalar("tau_Y_cl_l", tau_Y_cl_l)
		st_numscalar("tau_Y_bc_r", tau_Y_bc_r);	st_numscalar("tau_Y_bc_l", tau_Y_bc_l)
		
		st_numscalar("bias_l", bias_l);  st_numscalar("bias_r", bias_r)
		
		st_matrix("beta_Y_p_r", beta_Y_p_r); st_matrix("beta_Y_p_l", beta_Y_p_l)
		
		st_matrix("beta_q_r", beta_q_r); st_matrix("beta_q_l", beta_q_l)
		st_numscalar("g_l",  g_l);       st_numscalar("g_r",   g_r)
		st_matrix("b", (tau_cl))
		st_matrix("V", (V_tau_cl))
		st_matrix("V_Y_cl_r", V_Y_cl_r); st_matrix("V_Y_cl_l", V_Y_cl_l)
		st_matrix("V_Y_bc_r", V_Y_bc_r); st_matrix("V_Y_bc_l", V_Y_bc_l)
		st_numscalar("masspoints_found", masspoints_found)
		
		if ("`all'"~="") {
			st_matrix("b", (tau_cl,tau_bc,tau_bc))
			st_matrix("V", (V_tau_cl,0,0 \ 0,V_tau_cl,0 \0,0,V_tau_rb))
		}		
		
		if ("`covs'"!="") {
			st_matrix("gamma_p", gamma_p)
		}
					
					
		if ("`fuzzy'"!="") {
			st_numscalar("tau_T_cl", tau_T_cl); st_numscalar("se_tau_T_cl", se_tau_T_cl)
			st_numscalar("tau_T_bc", tau_T_bc);	st_numscalar("se_tau_T_rb", se_tau_T_rb)	
			
			st_numscalar("tau_T_cl_r", tau_T_cl_r); st_numscalar("tau_T_cl_l", tau_T_cl_l)
			st_numscalar("tau_T_bc_r", tau_T_bc_r);	st_numscalar("tau_T_bc_l", tau_T_bc_l)
			
			st_matrix("beta_T_p_r", beta_T_p_r); st_matrix("beta_T_p_l", beta_T_p_l)

		}
	}
	
	************************************************
	********* OUTPUT TABLE *************************
	************************************************
	local rho_l = scalar(h_l)/scalar(b_l)
	local rho_r = scalar(h_r)/scalar(b_r)
	
	disp ""
	if "`fuzzy'"=="" {
		if ("`covs'"=="") {
			if      ("`deriv'"=="0") disp "Sharp RD estimates using local polynomial regression." 
			else if ("`deriv'"=="1") disp "Sharp Kink RD estimates using local polynomial regression."	
			else                     disp "Sharp RD estimates using local polynomial regression. Derivative of order " `deriv' "."	
		}
		else {
			if      ("`deriv'"=="0") disp "Covariate-adjusted Sharp RD estimates using local polynomial regression." 
			else if ("`deriv'"=="1") disp "Covariate-adjusted Sharp Kink RD estimates using local polynomial regression."	
			else                     disp "Covariate-adjusted Sharp RD estimates using local polynomial regression. Derivative of order " `deriv' "."	
		}
	}
	else {
		if ("`covs'"=="") {
			if      ("`deriv'"=="0") disp "Fuzzy RD estimates using local polynomial regression." 
			else if ("`deriv'"=="1") disp "Fuzzy Kink RD estimates using local polynomial regression."	
			else                     disp "Fuzzy RD estimates using local polynomial regression. Derivative of order " `deriv' "."	
		}
		else {
			if      ("`deriv'"=="0") disp "Covariate-adjusted Fuzzy RD estimates using local polynomial regression." 
			else if ("`deriv'"=="1") disp "Covariate-adjusted Fuzzy Kink RD estimates using local polynomial regression."	
			else                     disp "Covariate-adjusted Fuzzy RD estimates using local polynomial regression. Derivative of order " `deriv' "."			
		}
	}

	disp ""
	disp in smcl in gr "{ralign 18: Cutoff c = `c'}"        _col(19) " {c |} " _col(21) in gr "Left of " in yellow "c"  _col(33) in gr "Right of " in yellow "c"         _col(55) in gr "Number of obs = "  in yellow %10.0f scalar(N)
	disp in smcl in gr "{hline 19}{c +}{hline 22}"                                                                                                                       _col(55) in gr "BW type       = "  in yellow "{ralign 10:`bwselect'}" 
	disp in smcl in gr "{ralign 18:Number of obs}"          _col(19) " {c |} " _col(21) as result %9.0f scalar(N_l)             _col(34) %9.0f  scalar(N_r)                              _col(55) in gr "Kernel        = "  in yellow "{ralign 10:`kernel_type'}" 
	disp in smcl in gr "{ralign 18:Eff. Number of obs}"     _col(19) " {c |} " _col(21) as result %9.0f scalar(N_h_l)           _col(34) %9.0f  scalar(N_h_r)                            _col(55) in gr "VCE method    = "  in yellow "{ralign 10:`vce_type'}" 
	disp in smcl in gr "{ralign 18:Order est. (p)}"         _col(19) " {c |} " _col(21) as result %9.0f `p'             _col(34) %9.0f  `p'         
	disp in smcl in gr "{ralign 18:Order bias (q)}"         _col(19) " {c |} " _col(21) as result %9.0f `q'             _col(34) %9.0f  `q'                              
	disp in smcl in gr "{ralign 18:BW est. (h)}"            _col(19) " {c |} " _col(21) as result %9.3f scalar(h_l)           _col(34) %9.3f  scalar(h_r)                                   
	disp in smcl in gr "{ralign 18:BW bias (b)}"            _col(19) " {c |} " _col(21) as result %9.3f scalar(b_l)           _col(34) %9.3f  scalar(b_r)
	disp in smcl in gr "{ralign 18:rho (h/b)}"              _col(19) " {c |} " _col(21) as result %9.3f `rho_l'         _col(34) %9.3f  `rho_r'
	if ("`masspoints'"=="check" | masspoints_found==1) disp in smcl in gr "{ralign 18:Unique obs}"         _col(19) " {c |} " _col(21) as result %9.0f scalar(M_l)           _col(34) %9.0f  scalar(M_r)                    
	if ("`cluster'"!="")                               disp in smcl in gr "{ralign 18:Number of clusters}" _col(19) " {c |} " _col(21) as result %9.0f scalar(g_l)           _col(34) %9.0f  scalar(g_r)                         
	disp ""
			
	if ("`fuzzy'"~="") {		
		disp in yellow "First-stage estimates. Outcome: `fuzzyvar'. Running variable: `x'."
		disp in smcl in gr "{hline 19}{c TT}{hline 60}"
		
		
		if ("`all'"!="") {
			disp in smcl in gr "{ralign 18:Method}"  _col(19) " {c |} " _col(24) "Coef."  _col(33) `"Std. Err."'   _col(46) "z"    _col(52) "P>|z|"   _col(61) `"[`level'% Conf. Interval]"'
			disp in smcl in gr "{hline 19}{c +}{hline 60}"
			disp in smcl in gr "{ralign 18:Conventional}"      _col(19) " {c |} " _col(22) in ye %7.0g scalar(tau_T_cl) _col(33) %7.0g scalar(se_tau_T_cl) _col(43) %5.4f scalar(tau_T_cl/se_tau_T_cl) _col(52) %5.3f  scalar(2*normal(-abs(tau_T_cl/se_tau_T_cl))) _col(60) %8.0g  scalar(tau_T_cl - quant*se_tau_T_cl) _col(73) %8.0g scalar(tau_T_cl + quant*se_tau_T_cl)  
			disp in smcl in gr "{ralign 18:Bias-corrected}"    _col(19) " {c |} " _col(22) in ye %7.0g scalar(tau_T_bc) _col(33) %7.0g scalar(se_tau_T_cl) _col(43) %5.4f scalar(tau_T_bc/se_tau_T_cl) _col(52) %5.3f  scalar(2*normal(-abs(tau_T_bc/se_tau_T_cl))) _col(60) %8.0g  scalar(tau_T_bc - quant*se_tau_T_cl) _col(73) %8.0g scalar(tau_T_bc + quant*se_tau_T_cl) 
			disp in smcl in gr "{ralign 18:Robust}"            _col(19) " {c |} " _col(22) in ye %7.0g scalar(tau_T_bc) _col(33) %7.0g scalar(se_tau_T_rb) _col(43) %5.4f scalar(tau_T_bc/se_tau_T_rb) _col(52) %5.3f  scalar(2*normal(-abs(tau_T_bc/se_tau_T_rb))) _col(60) %8.0g  scalar(tau_T_bc - quant*se_tau_T_rb) _col(73) %8.0g scalar(tau_T_bc + quant*se_tau_T_rb) 
		}
		else if ("`detail'"!="") {
			disp in smcl in gr "{ralign 18:Method}"  _col(19) " {c |} " _col(24) "Coef."  _col(33) `"Std. Err."'   _col(46) "z"    _col(52) "P>|z|"   _col(61) `"[`level'% Conf. Interval]"'
			disp in smcl in gr "{hline 19}{c +}{hline 60}"
			disp in smcl in gr "{ralign 18:Conventional}"      _col(19) " {c |} " _col(22) in ye %7.0g scalar(tau_T_cl) _col(33) %7.0g scalar(se_tau_T_cl) _col(43) %5.4f scalar(tau_T_cl/se_tau_T_cl) _col(52) %5.3f  scalar(2*normal(-abs(tau_T_cl/se_tau_T_cl)))  _col(60) %8.0g  scalar(tau_T_cl) - scalar(quant*se_tau_T_cl) _col(73) %8.0g scalar(tau_T_cl + quant*se_tau_T_cl) 
			disp in smcl in gr "{ralign 18:Robust}"            _col(19) " {c |} " _col(22) in ye %7.0g "    -"  _col(33) %7.0g "    -"     _col(43) %5.4f scalar(tau_T_bc/se_tau_T_rb) _col(52) %5.3f  scalar(2*normal(-abs(tau_T_bc/se_tau_T_rb)))  _col(60) %8.0g  scalar(tau_T_bc - quant*se_tau_T_rb) _col(73) %8.0g scalar(tau_T_bc + quant*se_tau_T_rb) 
		}
		else {
			disp in smcl in gr "{ralign 18:}"                   _col(19) " {c |} " _col(22) "Point"    _col(35) " {c |} "    "Robust Inference" 
			disp in smcl in gr "{ralign 18:}"                   _col(19) " {c |} " _col(22) "Estimate" _col(35) " {c |} "    "z-stat"       _col(52) "P>|z|"    _col(61) `"[`level'% Conf. Interval]"'
			disp in smcl in gr "{hline 19}{c +}{hline 60}"			 
			disp in smcl in gr "{ralign 18:RD Effect}"          _col(19) " {c |} " _col(22) in ye %7.0g scalar(tau_T_cl)  _col(35) " {c |} "  %5.4f scalar(tau_T_bc/se_tau_T_rb)  _col(52) %5.3f  scalar(2*normal(-abs(tau_T_bc/se_tau_T_rb))) _col(61) %8.0g scalar(tau_T_cl - quant*se_tau_T_cl)  _col(73)  %8.0g scalar(tau_T_cl + quant*se_tau_T_cl)			

		}
		
			disp in smcl in gr "{hline 19}{c BT}{hline 60}"
			disp ""
	}
	
	if ("`fuzzy'"=="") disp           "Outcome: `y'. Running variable: `x'."
	else               disp in yellow "Treatment effect estimates. Outcome: `y'. Running variable: `x'. Treatment Status: `fuzzyvar'."
		
	disp in smcl in gr "{hline 19}{c TT}{hline 60}"
		
	if ("`all'"!="") {
		disp in smcl in gr "{ralign 18:Method}"         _col(19) " {c |} " _col(24) "Coef."               _col(33) `"Std. Err."'    _col(46) "z"                    _col(52) "P>|z|"                                  _col(61) `"[`level'% Conf. Interval]"'
		disp in smcl in gr "{hline 19}{c +}{hline 60}"
		disp in smcl in gr "{ralign 18:Conventional}"   _col(19) " {c |} " _col(22) in ye %7.0g scalar(tau_cl)    _col(33) %7.0g scalar(se_tau_cl) _col(43) %5.4f scalar(tau_cl/se_tau_cl) _col(52) %5.3f  scalar(2*normal(-abs(tau_cl/se_tau_cl))) _col(60) %8.0g  scalar(tau_cl - quant*se_tau_cl) _col(73) %8.0g scalar(tau_cl + quant*se_tau_cl)  
		disp in smcl in gr "{ralign 18:Bias-corrected}" _col(19) " {c |} " _col(22) in ye %7.0g scalar(tau_bc)    _col(33) %7.0g scalar(se_tau_cl) _col(43) %5.4f scalar(tau_bc/se_tau_cl) _col(52) %5.3f  scalar(2*normal(-abs(tau_bc/se_tau_cl))) _col(60) %8.0g  scalar(tau_bc - quant*se_tau_cl) _col(73) %8.0g scalar(tau_bc + quant*se_tau_cl)  
		disp in smcl in gr "{ralign 18:Robust}"         _col(19) " {c |} " _col(22) in ye %7.0g scalar(tau_bc)    _col(33) %7.0g scalar(se_tau_rb) _col(43) %5.4f scalar(tau_bc/se_tau_rb) _col(52) %5.3f  scalar(2*normal(-abs(tau_bc/se_tau_rb))) _col(60) %8.0g  scalar(tau_bc - quant*se_tau_rb) _col(73) %8.0g scalar(tau_bc + quant*se_tau_rb)  
	}
	else if ("`detail'"!="") {
		disp in smcl in gr "{ralign 18:Method}"         _col(19) " {c |} " _col(24) "Coef."               _col(33) `"Std. Err."'    _col(46) "z"                    _col(52) "P>|z|"                                  _col(61) `"[`level'% Conf. Interval]"'
		disp in smcl in gr "{hline 19}{c +}{hline 60}"
		disp in smcl in gr "{ralign 18:Conventional}"   _col(19) " {c |} " _col(22) in ye %7.0g scalar(tau_cl)    _col(33) %7.0g scalar(se_tau_cl)  _col(43) %5.4f scalar(tau_cl/se_tau_cl) _col(52) %5.3f  scalar(2*normal(-abs(tau_cl/se_tau_cl)))  _col(60) %8.0g scalar(tau_cl - quant*se_tau_cl) _col(73) %8.0g scalar(tau_cl + quant*se_tau_cl) 
		disp in smcl in gr "{ralign 18:Robust}"         _col(19) " {c |} " _col(22) in ye %7.0g "    -"           _col(33) %7.0g "    -"            _col(43) %5.4f scalar(tau_bc/se_tau_rb) _col(52) %5.3f  scalar(2*normal(-abs(tau_bc/se_tau_rb)))  _col(60) %8.0g scalar(tau_bc - quant*se_tau_rb) _col(73) %8.0g scalar(tau_bc + quant*se_tau_rb) 
	} 
	else {
*		disp in smcl in gr "{ralign 18:}"                   _col(19) " {c |} " _col(22) "Estimate"     _col(35) "P>|z|"     _col(47)   `"[`level'% Robust CI]"'
*		disp in smcl in gr "{hline 19}{c +}{hline 60}"
*		disp in smcl in gr "{ralign 18:RD Effect}"   _col(19) " {c |} " _col(22) in ye %7.0g scalar(tau_cl)    _col(35)   %5.3f  scalar(2*normal(-abs(tau_bc/se_tau_rb)))   _col(45) %8.0g scalar(tau_bc - quant*se_tau_rb)   _col(55)  %8.0g scalar(tau_bc + quant*se_tau_rb) 
*		disp in smcl in gr "{hline 19}{c BT}{hline 60}"
*		disp ""
*		disp ""
		*disp in smcl in gr "{hline 19}{c TT}{hline 60}"
		disp in smcl in gr "{ralign 18:}"                   _col(19) " {c |} " _col(22) "Point"    _col(35) " {c |} "    "Robust Inference" 
		disp in smcl in gr "{ralign 18:}"                   _col(19) " {c |} " _col(22) "Estimate" _col(35) " {c |} "    "z-stat"       _col(52) "P>|z|"    _col(61) `"[`level'% Conf. Interval]"'
		disp in smcl in gr "{hline 19}{c +}{hline 60}"
		disp in smcl in gr "{ralign 18:RD Effect}"          _col(19) " {c |} " _col(22) in ye %7.0g scalar(tau_cl) _col(35) " {c |} "   %5.4f scalar(tau_bc/se_tau_rb)   _col(52) %5.3f scalar(2*normal(-abs(tau_bc/se_tau_rb))) _col(61) %8.0g scalar(tau_bc - quant*se_tau_rb)  _col(73) %8.0g scalar(tau_bc + quant*se_tau_rb) 
		
	}
		disp in smcl in gr "{hline 19}{c BT}{hline 60}"

	if ("`covs'"!="")        di "Covariate-adjusted estimates. Additional covariates included: `ncovs'"
*	if (`covs_drop_coll'>=1) di "Variables dropped due to multicollinearity."
	if ("`cluster'"!="")     di "Std. Err. adjusted for clusters in " "`clustvar'"
	if ("`scalepar'"!="1")   di "Scale parameter: " `scalepar' 
	if ("`scaleregul'"!="1") di "Scale regularization: " `scaleregul'
	if ("`masspoints'"=="check")  di "Running variable checked for mass points."  
	if ("`masspoints'"=="adjust" & masspoints_found==1) di "Estimates adjusted for mass points in the running variable."  	
	
	if ("`nowarnings'"!="") {
		if (scalar(h_l)>=`range_l' | scalar(h_r)>=`range_r') disp in red "WARNING: bandwidth {it:h} greater than the range of the data."
		if (scalar(b_l)>=`range_l' | scalar(b_r)>=`range_r') disp in red "WARNING: bandwidth {it:b} greater than the range of the data."
		if (scalar(N_h_l)<20 | scalar(N_h_r)<20) 				 disp in red "WARNING: bandwidth {it:h} too low."
		if (scalar(N_b_l)<20 | scalar(N_b_r)<20) 				 disp in red "WARNING: bandwidth {it:b} too low."
		if ("`sharpbw'"~="")   					 disp in red "WARNING: bandwidths automatically computed for sharp RD estimation."
		if ("`perf_comp'"~="")   				 disp in red "WARNING: bandwidths automatically computed for sharp RD estimation because perfect compliance was detected on at least one side of the threshold."
	}
	
	local ci_l_rb = round(scalar(tau_bc - quant*se_tau_rb),0.001)
	local ci_r_rb = round(scalar(tau_bc + quant*se_tau_rb),0.001)

	matrix rownames V = RD_Estimate
	matrix colnames V = RD_Estimate
	matrix colnames b = RD_Estimate
	
	local tempo: colfullnames V
	matrix rownames V = `tempo'
	
	if ("`all'"~="") {
		matrix rownames V = Conventional Bias-corrected Robust
		matrix colnames V = Conventional Bias-corrected Robust
		matrix colnames b = Conventional Bias-corrected Robust
	}
		
	restore

	ereturn clear
	
	cap ereturn post b V, esample(`touse')
	
	ereturn scalar N = `N'
	ereturn scalar N_l = scalar(N_l)
	ereturn scalar N_r = scalar(N_r)
	ereturn scalar N_h_l = scalar(N_h_l)
	ereturn scalar N_h_r = scalar(N_h_r)
	ereturn scalar N_b_l = scalar(N_b_l)
	ereturn scalar N_b_r = scalar(N_b_r)
	
	ereturn scalar c = `c'
	ereturn scalar p = `p'
	ereturn scalar q = `q'
	
	ereturn scalar h_l = scalar(h_l)
	ereturn scalar h_r = scalar(h_r)
	ereturn scalar b_l = scalar(b_l)
	ereturn scalar b_r = scalar(b_r)
	
	ereturn scalar tau_cl   = scalar(tau_cl)
	ereturn scalar tau_cl_l = scalar(tau_Y_cl_l)
	ereturn scalar tau_cl_r = scalar(tau_Y_cl_r)
	ereturn scalar tau_bc   = scalar(tau_bc)
	ereturn scalar tau_bc_l = scalar(tau_Y_bc_l)
	ereturn scalar tau_bc_r = scalar(tau_Y_bc_r)

	ereturn scalar bias_l    = scalar(bias_l)
	ereturn scalar bias_r    = scalar(bias_r)
	ereturn scalar se_tau_cl = scalar(se_tau_cl)
	ereturn scalar se_tau_rb = scalar(se_tau_rb)
	
	ereturn scalar level   = `level'
	ereturn scalar ci_l_cl = scalar(tau_cl - quant*se_tau_cl)
	ereturn scalar ci_r_cl = scalar(tau_cl + quant*se_tau_cl)
	ereturn scalar ci_l_rb = scalar(tau_bc - quant*se_tau_rb)
	ereturn scalar ci_r_rb = scalar(tau_bc + quant*se_tau_rb)
	ereturn scalar pv_cl   = scalar(2*normal(-abs(tau_cl/se_tau_cl)))
	ereturn scalar pv_rb   = scalar(2*normal(-abs(tau_bc/se_tau_rb)))
	
	if ("`fuzzy'"!="") {
		ereturn scalar tau_T_cl    = scalar(tau_T_cl)
		ereturn scalar tau_T_bc    = scalar(tau_T_bc)
		ereturn scalar se_tau_T_cl = scalar(se_tau_T_cl)
		ereturn scalar se_tau_T_rb = scalar(se_tau_T_rb)
		ereturn scalar tau_T_cl_l  = scalar(tau_T_cl_l)
		ereturn scalar tau_T_cl_r  = scalar(tau_T_cl_r)
		ereturn scalar tau_T_bc_l  = scalar(tau_T_bc_l)
		ereturn scalar tau_T_bc_r  = scalar(tau_T_bc_r)
		
		ereturn matrix beta_T_p_r = beta_T_p_r
		ereturn matrix beta_T_p_l = beta_T_p_l
	
	}
	
	ereturn matrix beta_Y_p_r = beta_Y_p_r
	ereturn matrix beta_Y_p_l = beta_Y_p_l
	
	if ("`covs'"!="") {
		ereturn matrix beta_covs = gamma_p
	}
	
	ereturn matrix V_cl_l = V_Y_cl_l 
	ereturn matrix V_cl_r = V_Y_cl_r 
	ereturn matrix V_rb_l = V_Y_bc_l 
	ereturn matrix V_rb_r = V_Y_bc_r 
	
	ereturn local ci_rb  [`ci_l_rb' ; `ci_r_rb']
	ereturn local kernel     = "`kernel_type'"
	ereturn local bwselect   = "`bwselect'"
	ereturn local vce_select = "`vce_type'"
	if ("`covs'"!="")    ereturn local covs "`covs_list'"
	if ("`cluster'"!="") ereturn local clustvar "`clustvar'"
	ereturn local outcomevar "`y'"
	ereturn local runningvar "`x'"
	ereturn local depvar "`y'"
	ereturn local cmd "rdrobust"

	mata mata clear
 
end
