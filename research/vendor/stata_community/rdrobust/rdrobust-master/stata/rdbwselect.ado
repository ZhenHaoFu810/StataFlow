********************************************************************************
* RDROBUST STATA PACKAGE -- rdbwselect
* Authors: Sebastian Calonico, Matias D. Cattaneo, Max Farrell, Rocio Tititunik
********************************************************************************
*!version 10.0.0  2025-06-30

capture program drop rdbwselect
program define rdbwselect, eclass
	syntax anything [if] [in] [, c(real 0) fuzzy(string) deriv(real 0) p(string) q(real 0) covs(string) covs_drop(string) kernel(string) weights(string) bwselect(string) vce(string) scaleregul(real 1) all nochecks masspoints(string) bwcheck(real 0) bwrestrict(string) stdvars(string)]

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
		if ("`vce_select'"!="cluster" & "`vce_select'"!="nncluster") di as error "{err}{cmd:vce()} incorrectly specified"  
	}
	if `w' > 3 {
		di as error "{err}{cmd:vce()} incorrectly specified"  
		exit 125
	}
	
	local vce_type = "NN"
	if ("`vce_select'"=="hc0")       local vce_type = "HC0"
	if ("`vce_select'"=="hc1")       local vce_type = "HC1"
	if ("`vce_select'"=="hc2")       local vce_type = "HC2"
	if ("`vce_select'"=="hc3")       local vce_type = "HC3"
	if ("`vce_select'"=="cluster")   local vce_type = "Cluster"
	if ("`vce_select'"=="nncluster") local vce_type = "NNcluster"

	if ("`vce_select'"=="cluster" | "`vce_select'"=="nncluster") local cluster = "cluster"
	if ("`vce_select'"=="cluster")   local vce_select = "hc0"
	if ("`vce_select'"=="nncluster") local vce_select = "nn"
	if ("`vce_select'"=="")          local vce_select = "nn"
	
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
		di as error "{err}{cmd:fuzzy()} only accepts two inputs"  
		exit 125
	}
	************************************************************

	**** DROP MISSINGS ******************************************
	qui drop if mi(`y') | mi(`x')
	if ("`cluster'"!="") qui drop if mi(`clustvar')
	if ("`fuzzy'"~="") {
		qui drop if mi(`fuzzyvar')
	}

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
			local x_min = r(min)
			local x_max = r(max)
			local N = r(N)
			local x_iq = r(p75)-r(p25)
			local x_sd = r(sd)
			
			if ("`deriv'">"0" & "`p'"=="" & "`q'"=="0")  local p = (`deriv'+1)
			if ("`p'"=="") local p = 1
			if ("`q'"=="0")                              local q = (`p'+1)
			
			**************************** BEGIN ERROR CHECKING ************************************************
			if ("`nochecks'"=="") {
			
			if (`c'<=`x_min' | `c'>=`x_max'){
			 di as error "{err}{cmd:c()} should be set within the range of `x'"  
			 exit 125
			}
			
			if (`N'<20){
			 di as error "{err}Not enough observations to perform bandwidth calculations"  
			 exit 2001
			}
			
			if ("`kernel'"~="uni" & "`kernel'"~="uniform" & "`kernel'"~="tri" & "`kernel'"~="triangular" & "`kernel'"~="epa" & "`kernel'"~="epanechnikov" & "`kernel'"~="" ){
			 di as error "{err}{cmd:kernel()} incorrectly specified"  
			 exit 7
			}

			if ("`bwselect'"=="CCT" | "`bwselect'"=="IK" | "`bwselect'"=="CV" |"`bwselect'"=="cct" | "`bwselect'"=="ik" | "`bwselect'"=="cv"){
				di as error "{err}{cmd:bwselect()} options IK, CCT and CV have been depricated. Please see help for new options"  
				exit 7
			}
					
			if  ("`bwselect'"!="mserd" & "`bwselect'"!="msetwo" & "`bwselect'"!="msesum" & "`bwselect'"!="msecomb1" & "`bwselect'"!="msecomb2"  & "`bwselect'"!="cerrd" & "`bwselect'"!="certwo" & "`bwselect'"!="cersum" & "`bwselect'"!="cercomb1" & "`bwselect'"!="cercomb2" & "`bwselect'"~=""){
				di as error  "{err}{cmd:bwselect()} incorrectly specified"  
				exit 7
			}

			if ("`vce_select'"~="nn" & "`vce_select'"~="" & "`vce_select'"~="cluster" & "`vce_select'"~="nncluster" & "`vce_select'"~="hc1" & "`vce_select'"~="hc2" & "`vce_select'"~="hc3" & "`vce_select'"~="hc0"){ 
			 di as error  "{err}{cmd:vce()} incorrectly specified"  
			 exit 7
			}

			if ("`p'"<"0" | "`q'"<="0" | "`deriv'"<"0" | "`nnmatch'"<="0" ){
			 di as error  "{err}{cmd:p()}, {cmd:q()}, {cmd:deriv()}, {cmd:nnmatch()} imson should be positive"  
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
	
	if ("`vce_select'"=="nn" | "`masspoints'"=="check" | "`masspoints'"=="adjust") {
		sort `x', stable
		if ("`vce_select'"=="nn") {
			tempvar dups dupsid
			by `x': gen dups = _N
			by `x': gen dupsid = _n
		}
	}	
	
	
	
	
	
	
*************************************************************************************************************************************
	mata{
	c = `c'
	p = `p'
	q = `q'
	covs_drop_coll = `covs_drop_coll'
	nnmatch =  strtoreal("`nnmatch'")
		
	Y = st_data(.,("`y'"), 0);	X = st_data(.,("`x'"), 0)
	
	BWp = min((`x_sd',`x_iq'/1.349))
	x_sd = y_sd = 1
	if  ("`stdvars'"=="on")  {	
		y_sd = sqrt(variance(Y))
		x_sd = sqrt(variance(X))
		Y = Y/y_sd
		X = X/x_sd
		c = c/x_sd
		BWp = min((1, (`x_iq'/x_sd)/1.349))
	}

	ind_r = X:>=c
	ind_l = abs(1:-ind_r)
	
	X_l = select(X,ind_l);	X_r = select(X,ind_r)
	Y_l = select(Y,ind_l);	Y_r = select(Y,ind_r)
	
	N   = length(X);	N_l = length(X_l);	N_r = length(X_r)
	
	x_l_min = min(X_l);	x_l_max = max(X_l)
	x_r_min = min(X_r);	x_r_max = max(X_r)
	
	range_l = c - x_l_min
	range_r = x_r_max - c  
	
	dZ=Z_l=Z_r=T_l=T_r=Cind_l=Cind_r=g_l=g_r=dups_l=dups_r=dupsid_l=dupsid_r=0

	if ("`vce_select'"=="nn") {
		dups      = st_data(.,("dups"), 0); dupsid    = st_data(.,("dupsid"), 0)
		dups_l    = select(dups,ind_l);    dups_r    = select(dups,ind_r)
		dupsid_l  = select(dupsid,ind_l);  dupsid_r  = select(dupsid,ind_r)
	}
	
	if ("`covs'"~="") {
		Z   = st_data(.,tokens("`covs_list'"), 0)
		dZ  = cols(Z)
		Z_l = select(Z,ind_l);	Z_r = select(Z,ind_r)
	}
	
	if ("`fuzzy'"~="") {
		T   = st_data(.,("`fuzzyvar'"), 0)
		T_l = select(T,ind_l);	T_r = select(T,ind_r)
		if (variance(T_l)==0 | variance(T_r)==0){
			T_l = T_r =0
			st_local("perf_comp","perf_comp")
		}
		if ("`sharpbw'"!=""){
			T_l = T_r =0
			st_local("sharpbw","sharpbw")
		}
	}
	
	C_l=C_r=0
	if ("`cluster'"!="") {
		C  = st_data(.,("`clustvar'"), 0)
		C_l  = select(C,ind_l); C_r  = select(C,ind_r)
		indC_l = order(C_l,1);  indC_r = order(C_r,1) 
		g_l = rows(panelsetup(C_l[indC_l],1));	g_r = rows(panelsetup(C_r[indC_r],1))
		st_numscalar("g_l",  g_l);     st_numscalar("g_r",   g_r)
	}
	
	fw_l = fw_r = 0
	if ("`weights'"~="") {
		fw = st_data(.,("`weights'"), 0)
		fw_l = select(fw,ind_l);	fw_r = select(fw,ind_r)
	}
	
	mN = N
	bwcheck = `bwcheck'
	masspoints_found = 0
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
			if ("`masspoints'"=="check") display("{err}Try using option {cmd:masspoints(adjust)}")
		}				
	}
	

	***********************************************************************
	******** Computing bandwidth selector *********************************
	***********************************************************************					
	c_bw = `C_c'*BWp*mN^(-1/5)
	if ("`masspoints'"=="adjust") c_bw = `C_c'*BWp*M^(-1/5)
	
	if  ("`bwrestrict'"=="on")  {	
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
		
	c_bw_l = c_bw_r = c_bw
	
	
	*** Step 1: d_bw
	C_d_l = rdrobust_bw(Y_l, X_l, T_l, Z_l, C_l, fw_l, c=c, o=q+1, nu=q+1, o_B=q+2, h_V=c_bw_l, h_B=range_l+1e-8, 0, "`vce_select'", nnmatch, "`kernel'", dups_l, dupsid_l, covs_drop_coll)
	C_d_r = rdrobust_bw(Y_r, X_r, T_r, Z_r, C_r, fw_r, c=c, o=q+1, nu=q+1, o_B=q+2, h_V=c_bw_r, h_B=range_r+1e-8, 0, "`vce_select'", nnmatch, "`kernel'", dups_r, dupsid_r, covs_drop_coll)
	
	if (C_d_l[1]==. | C_d_l[2]==. | C_d_l[3]==. |C_d_r[1]==. | C_d_r[2]==. | C_d_r[3]==.) printf("{err}Invertibility problem in the computation of preliminary bandwidth. Try checking for mass points with option {cmd:masspoints(check)}.\n")  
	if (C_d_l[1]==0 | C_d_l[2]==0 | C_d_r[1]==0 | C_d_r[2]==0)                            printf("{err}Not enough variability to compute the preliminary bandwidth. Try checking for mass points with option {cmd:masspoints(check)}.\n")  
			
	*** TWO
	if  ("`bwselect'"=="msetwo" |  "`bwselect'"=="certwo" | "`bwselect'"=="msecomb2" | "`bwselect'"=="cercomb2"  | "`all'"!="")  {		
		d_bw_l = (  (C_d_l[1]              /   C_d_l[2]^2)    * (N/mN)         )^C_d_l[4] 
		d_bw_r = (  (C_d_r[1]              /   C_d_r[2]^2)    * (N/mN)         )^C_d_l[4]
		if  ("`bwrestrict'"=="on")  {		
			d_bw_l = min((d_bw_l, range_l))
			d_bw_r = min((d_bw_r, range_r))
		}
		if (bwcheck > 0) {
			d_bw_l = max((d_bw_l, bw_min_l))
			d_bw_r = max((d_bw_r, bw_min_r))
		}
		C_b_l  = rdrobust_bw(Y_l, X_l, T_l, Z_l, C_l, fw_l, c=c, o=q, nu=p+1, o_B=q+1, h_V=c_bw_l, h_B=d_bw_l, `scaleregul', "`vce_select'", nnmatch, "`kernel'", dups_l, dupsid_l, covs_drop_coll)
		b_bw_l = (  (C_b_l[1]              /   (C_b_l[2]^2 + `scaleregul'*C_b_l[3]))  * (N/mN)     )^C_b_l[4]
		C_b_r  = rdrobust_bw(Y_r, X_r, T_r, Z_r, C_r, fw_r, c=c, o=q, nu=p+1, o_B=q+1, h_V=c_bw_r, h_B=d_bw_r, `scaleregul', "`vce_select'", nnmatch, "`kernel'", dups_r, dupsid_r, covs_drop_coll)
		b_bw_r = (  (C_b_r[1]              /   (C_b_r[2]^2 + `scaleregul'*C_b_r[3]))   * (N/mN)    )^C_b_l[4]
		if  ("`bwrestrict'"=="on")  {	
			b_bw_l = min((b_bw_l, range_l))
			b_bw_r = min((b_bw_r, range_r))
		}

		C_h_l  = rdrobust_bw(Y_l, X_l, T_l, Z_l, C_l, fw_l, c=c, o=p, nu=`deriv', o_B=q, h_V=c_bw_l, h_B=b_bw_l, `scaleregul', "`vce_select'", nnmatch, "`kernel'", dups_l, dupsid_l, covs_drop_coll)
		h_bw_l = (  (C_h_l[1]              /   (C_h_l[2]^2 + `scaleregul'*C_h_l[3]))  * (N/mN)       )^C_h_l[4]
		C_h_r  = rdrobust_bw(Y_r, X_r, T_r, Z_r, C_r, fw_r, c=c, o=p, nu=`deriv', o_B=q, h_V=c_bw_r, h_B=b_bw_r, `scaleregul', "`vce_select'", nnmatch, "`kernel'", dups_r, dupsid_r, covs_drop_coll)
		h_bw_r = (  (C_h_r[1]              /   (C_h_r[2]^2 + `scaleregul'*C_h_r[3]))  * (N/mN)       )^C_h_l[4]
		
		if  ("`bwrestrict'"=="on")  {	
			h_bw_l = min((h_bw_l, range_l))
			h_bw_r = min((h_bw_r, range_r))
		}

	}
	
	*** SUM
	if  ("`bwselect'"=="msesum" | "`bwselect'"=="cersum" |  "`bwselect'"=="msecomb1" | "`bwselect'"=="msecomb2" |  "`bwselect'"=="cercomb1" | "`bwselect'"=="cercomb2"  |  "`all'"!="")  {
		d_bw_s = ( ((C_d_l[1] + C_d_r[1])  /  (C_d_r[2] + C_d_l[2])^2)  * (N/mN)  )^C_d_l[4]
		if  ("`bwrestrict'"=="on")  d_bw_s = min((d_bw_s, bw_max))
		if (bwcheck > 0) d_bw_s = max((d_bw_s, bw_min_l, bw_min_r))		
		C_b_l  = rdrobust_bw(Y_l, X_l, T_l, Z_l, C_l, fw_l, c=c, o=q, nu=p+1, o_B=q+1, h_V=c_bw_l, h_B=d_bw_s, `scaleregul', "`vce_select'", nnmatch, "`kernel'", dups_l, dupsid_l, covs_drop_coll)
		C_b_r  = rdrobust_bw(Y_r, X_r, T_r, Z_r, C_r, fw_r, c=c, o=q, nu=p+1, o_B=q+1, h_V=c_bw_r, h_B=d_bw_s, `scaleregul', "`vce_select'", nnmatch, "`kernel'", dups_r, dupsid_r, covs_drop_coll)
		b_bw_s = ( ((C_b_l[1] + C_b_r[1])  /  ((C_b_r[2] + C_b_l[2])^2 + `scaleregul'*(C_b_r[3]+C_b_l[3])))  * (N/mN)  )^C_b_l[4]
		if  ("`bwrestrict'"=="on")  b_bw_s = min((b_bw_s, bw_max))
		C_h_l  = rdrobust_bw(Y_l, X_l, T_l, Z_l, C_l, fw_l, c=c, o=p, nu=`deriv', o_B=q, h_V=c_bw_l, h_B=b_bw_s, `scaleregul', "`vce_select'", nnmatch, "`kernel'", dups_l, dupsid_l, covs_drop_coll)
		C_h_r  = rdrobust_bw(Y_r, X_r, T_r, Z_r, C_r, fw_r, c=c, o=p, nu=`deriv', o_B=q, h_V=c_bw_r, h_B=b_bw_s, `scaleregul', "`vce_select'", nnmatch, "`kernel'", dups_r, dupsid_r, covs_drop_coll)
		h_bw_s = ( ((C_h_l[1] + C_h_r[1])  /  ((C_h_r[2] + C_h_l[2])^2 + `scaleregul'*(C_h_r[3] + C_h_l[3])))  * (N/mN)  )^C_h_l[4]
		if  ("`bwrestrict'"=="on")  h_bw_s = min((h_bw_s, bw_max))
	}
	
	*** RD
	if  ("`bwselect'"=="mserd" | "`bwselect'"=="cerrd" | "`bwselect'"=="msecomb1" | "`bwselect'"=="msecomb2" | "`bwselect'"=="cercomb1" | "`bwselect'"=="cercomb2" | "`bwselect'"=="" | "`all'"!="" ) {
		d_bw_d = ( ((C_d_l[1] + C_d_r[1])  /  (C_d_r[2] - C_d_l[2])^2)  * (N/mN)   )^C_d_l[4]
		if  ("`bwrestrict'"=="on")  d_bw_d = min((d_bw_d, bw_max))
		if (bwcheck > 0) d_bw_d = max((d_bw_d, bw_min_l, bw_min_r))		
		C_b_l  = rdrobust_bw(Y_l, X_l, T_l, Z_l, C_l, fw_l, c=c, o=q, nu=p+1, o_B=q+1, h_V=c_bw_l, h_B=d_bw_d, `scaleregul', "`vce_select'", nnmatch, "`kernel'", dups_l, dupsid_l, covs_drop_coll)
		C_b_r  = rdrobust_bw(Y_r, X_r, T_r, Z_r, C_r, fw_r, c=c, o=q, nu=p+1, o_B=q+1, h_V=c_bw_r, h_B=d_bw_d, `scaleregul', "`vce_select'", nnmatch, "`kernel'", dups_r, dupsid_r, covs_drop_coll)
		b_bw_d = ( ((C_b_l[1] + C_b_r[1])  /  ((C_b_r[2] - C_b_l[2])^2 + `scaleregul'*(C_b_r[3] + C_b_l[3])))  * (N/mN)    )^C_b_l[4]
		if  ("`bwrestrict'"=="on")  b_bw_d = min((b_bw_d, bw_max))
		C_h_l  = rdrobust_bw(Y_l, X_l, T_l, Z_l, C_l, fw_l, c=c, o=p, nu=`deriv', o_B=q, h_V=c_bw_l, h_B=b_bw_d, `scaleregul', "`vce_select'", nnmatch, "`kernel'", dups_l, dupsid_l, covs_drop_coll)
		C_h_r  = rdrobust_bw(Y_r, X_r, T_r, Z_r, C_r, fw_r, c=c, o=p, nu=`deriv', o_B=q, h_V=c_bw_r, h_B=b_bw_d, `scaleregul', "`vce_select'", nnmatch, "`kernel'", dups_r, dupsid_r, covs_drop_coll)
		h_bw_d = ( ((C_h_l[1] + C_h_r[1])  /  ((C_h_r[2] - C_h_l[2])^2 + `scaleregul'*(C_h_r[3] + C_h_l[3])))  * (N/mN)   )^C_h_l[4]
		if  ("`bwrestrict'"=="on")  h_bw_d = min((h_bw_d, bw_max))
		
	}	
	
	
	mat_h   = J(1, 2, .)
	mat_b   = J(1, 2, .)
	
	if (C_b_l[1]==0 | C_b_l[2]==0 | C_b_r[1]==0 | C_b_r[2]==0 |C_b_l[1]==. | C_b_l[2]==. | C_b_l[3]==. | C_b_r[1]==. | C_b_r[2]==. | C_b_r[3]==.) printf("{err}Not enough variability to compute the bias bandwidth (b). Try checking for mass points with option {cmd:masspoints(check)}. \n")  
	if (C_h_l[1]==0 | C_h_l[2]==0 | C_h_r[1]==0 | C_h_r[2]==0 |C_h_l[1]==. | C_h_l[2]==. | C_h_l[3]==. | C_h_r[1]==. | C_h_r[2]==. | C_h_r[3]==.) printf("{err}Not enough variability to compute the loc. poly. bandwidth (h). Try checking for mass points with option {cmd:masspoints(check)}.\n") 
			
	st_numscalar("N", N)
	st_numscalar("N_l", N_l)
	st_numscalar("N_r", N_r)
	st_numscalar("x_l_min", x_sd*x_l_min)
	st_numscalar("x_l_max", x_sd*x_l_max)
	st_numscalar("x_r_min", x_sd*x_r_min)
	st_numscalar("x_r_max", x_sd*x_r_max)
	st_numscalar("masspoints_found", masspoints_found)
	
	if  ("`bwselect'"=="mserd" | "`bwselect'"=="cerrd" | "`bwselect'"=="msecomb1" | "`bwselect'"=="msecomb2" | "`bwselect'"=="cercomb1" | "`bwselect'"=="cercomb2" | "`bwselect'"=="" | "`all'"!="" ) {
		h_mserd = x_sd*h_bw_d
		b_mserd = x_sd*b_bw_d
		st_numscalar("h_mserd", h_mserd); st_numscalar("b_mserd", b_mserd)
		mat_h[1, 1] = h_mserd
		mat_h[1, 2] = h_mserd
		mat_b[1, 1] = b_mserd
		mat_b[1, 2] = b_mserd
		
	}	
	if  ("`bwselect'"=="msesum" | "`bwselect'"=="cersum" |  "`bwselect'"=="msecomb1" | "`bwselect'"=="msecomb2" |  "`bwselect'"=="cercomb1" | "`bwselect'"=="cercomb2"  |  "`all'"!="")  {
		h_msesum = x_sd*h_bw_s
		b_msesum = x_sd*b_bw_s
		st_numscalar("h_msesum", h_msesum); st_numscalar("b_msesum", b_msesum)
		mat_h[1, 1] = h_msesum
		mat_h[1, 2] = h_msesum
		mat_b[1, 1] = b_msesum
		mat_b[1, 2] = b_msesum
		}
	if  ("`bwselect'"=="msetwo" |  "`bwselect'"=="certwo" | "`bwselect'"=="msecomb2" | "`bwselect'"=="cercomb2"  | "`all'"!="")  {		
		h_msetwo_l = x_sd*h_bw_l
		h_msetwo_r = x_sd*h_bw_r
		b_msetwo_l = x_sd*b_bw_l
		b_msetwo_r = x_sd*b_bw_r
		st_numscalar("h_msetwo_l", h_msetwo_l); st_numscalar("h_msetwo_r", h_msetwo_r)
		st_numscalar("b_msetwo_l", b_msetwo_l); st_numscalar("b_msetwo_r", b_msetwo_r)
		mat_h[1, 1] = h_msetwo_l
		mat_h[1, 2] = h_msetwo_r
		mat_b[1, 1] = b_msetwo_l
		mat_b[1, 2] = b_msetwo_r		
		}
	if  ("`bwselect'"=="msecomb1" | "`bwselect'"=="cercomb1" | "`all'"!="" ) {
		h_msecomb1 = min((h_mserd,h_msesum))
		b_msecomb1 = min((b_mserd,b_msesum))
		st_numscalar("h_msecomb1", h_msecomb1);  st_numscalar("b_msecomb1", b_msecomb1) 
		mat_h[1, 1] = h_msecomb1
		mat_h[1, 2] = h_msecomb1
		mat_b[1, 1] = b_msecomb1
		mat_b[1, 2] = b_msecomb1
		}
	if  ("`bwselect'"=="msecomb2" | "`bwselect'"=="cercomb2" |  "`all'"!="" ) {
		h_msecomb2_l = (sort((h_mserd,h_msesum,h_msetwo_l)',1))[2]
		h_msecomb2_r = (sort((h_mserd,h_msesum,h_msetwo_r)',1))[2]
		b_msecomb2_l = (sort((b_mserd,b_msesum,b_msetwo_l)',1))[2]
		b_msecomb2_r = (sort((b_mserd,b_msesum,b_msetwo_r)',1))[2]
		st_numscalar("h_msecomb2_l", h_msecomb2_l); st_numscalar("h_msecomb2_r", h_msecomb2_r);
		st_numscalar("b_msecomb2_l", b_msecomb2_l); st_numscalar("b_msecomb2_r", b_msecomb2_r);
		mat_h[1, 1] = h_msecomb2_l
		mat_h[1, 2] = h_msecomb2_r
		mat_b[1, 1] = b_msecomb2_l
		mat_b[1, 2] = b_msecomb2_r
	}
	
	cer_h = N^(-(`p'/((3+`p')*(3+2*`p'))))
	if ("`cluster'"!="") cer_h = (g_l+g_r)^(-(`p'/((3+`p')*(3+2*`p'))))
	cer_b = 1
	
	if  ("`bwselect'"=="cerrd" | "`all'"!="" ){
		h_cerrd = h_mserd*cer_h
		b_cerrd = b_mserd*cer_b
		st_numscalar("h_cerrd", h_cerrd); st_numscalar("b_cerrd", b_cerrd)
		mat_h[1, 1] = h_cerrd
		mat_h[1, 2] = h_cerrd
		mat_b[1, 1] = b_cerrd
		mat_b[1, 2] = b_cerrd
		}
	if  ("`bwselect'"=="cersum" | "`all'"!="" ){
		h_cersum = h_msesum*cer_h
		b_cersum=  b_msesum*cer_b
		st_numscalar("h_cersum", h_cersum); st_numscalar("b_cersum", b_cersum)
		mat_h[1, 1] = h_cersum
		mat_h[1, 2] = h_cersum
		mat_b[1, 1] = b_cersum
		mat_b[1, 2] = b_cersum
		}
	if  ("`bwselect'"=="certwo" | "`all'"!="" ){
		h_certwo_l   = h_msetwo_l*cer_h
		h_certwo_r   = h_msetwo_r*cer_h
		b_certwo_l   = b_msetwo_l*cer_b
		b_certwo_r   = b_msetwo_r*cer_b
		st_numscalar("h_certwo_l", h_certwo_l); st_numscalar("h_certwo_r", h_certwo_r);
		st_numscalar("b_certwo_l", b_certwo_l); st_numscalar("b_certwo_r", b_certwo_r);
		mat_h[1, 1] = h_cersum
		mat_h[1, 2] = h_cersum
		mat_b[1, 1] = b_cersum
		mat_b[1, 2] = b_cersum
		}
	if  ("`bwselect'"=="cercomb1" | "`all'"!="" ){
		h_cercomb1 = h_msecomb1*cer_h
		b_cercomb1 = b_msecomb1*cer_b
		st_numscalar("h_cercomb1", h_cercomb1);	st_numscalar("b_cercomb1", b_cercomb1)
		mat_h[1, 1] = h_cercomb1
		mat_h[1, 2] = h_cercomb1
		mat_b[1, 1] = b_cercomb1
		mat_b[1, 2] = b_cercomb1
		}
	if  ("`bwselect'"=="cercomb2" | "`all'"!="" ){
		h_cercomb2_l = h_msecomb2_l*cer_h
		h_cercomb2_r = h_msecomb2_r*cer_h
		b_cercomb2_l = b_msecomb2_l*cer_b
		b_cercomb2_r = b_msecomb2_r*cer_b
		st_numscalar("h_cercomb2_l", h_cercomb2_l); st_numscalar("h_cercomb2_r", h_cercomb2_r);
		st_numscalar("b_cercomb2_l", b_cercomb2_l); st_numscalar("b_cercomb2_r", b_cercomb2_r);
		mat_h[1, 1] = h_cercomb2_l
		mat_h[1, 2] = h_cercomb2_r
		mat_b[1, 1] = b_cercomb2_l
		mat_b[1, 2] = b_cercomb2_r
	}
	
	
		st_matrix("mat_h", mat_h)
		st_matrix("mat_b", mat_b)

}
* close mata




	*******************************************************************************
	disp ""
	if ("`fuzzy'"=="") {
		if ("`covs'"=="") {
			if      ("`deriv'"=="0") disp in yellow "Bandwidth estimators for sharp RD local polynomial regression." 
			else if ("`deriv'"=="1") disp in yellow "Bandwidth estimators for sharp kink RD local polynomial regression."	
			else                     disp in yellow "Bandwidth estimators for sharp RD local polynomial regression. Derivative of order " `deriv' "."	
		}
		else {
			if      ("`deriv'"=="0") disp in yellow "Bandwidth estimators for covariate-adjusted sharp RD local polynomial regression." 
			else if ("`deriv'"=="1") disp in yellow "Bandwidth estimators for covariate-adjusted sharp kink RD local polynomial regression."	
			else                     disp in yellow "Bandwidth estimators for covariate-adjusted sharp RD local polynomial regression. Derivative of order " `deriv' "."	
		}
	}
	else {
		if ("`covs'"=="") {
			if      ("`deriv'"=="0") disp in yellow "Bandwidth estimators for fuzzy RD local polynomial regression." 
			else if ("`deriv'"=="1") disp in yellow "Bandwidth estimators for fuzzy kink RD local polynomial regression."	
			else                     disp in yellow "Bandwidth estimators for fuzzy RD local polynomial regression. Derivative of order " `deriv' "."	
		}
		else {
			if      ("`deriv'"=="0") disp in yellow "Bandwidth estimators for covariate-adjusted fuzzy RD local polynomial regression." 
			else if ("`deriv'"=="1") disp in yellow "Bandwidth estimators for covariate-adjusted fuzzy kink RD local polynomial regression."	
			else                     disp in yellow "Bandwidth estimators for covariate-adjusted fuzzy RD local polynomial regression. Derivative of order " `deriv' "."	
		}
	}
	disp ""

	disp in smcl in gr "{ralign 18: Cutoff c = `c_orig'}"  _col(19) " {c |} " _col(21) in gr "Left of " in yellow "c"  _col(33) in gr "Right of " in yellow "c" _col(55) in gr "Number of obs = "  in yellow %10.0f scalar(N)
	disp in smcl in gr "{hline 19}{c +}{hline 22}"                                                                                                              _col(55) in gr "Kernel        = "  in yellow "{ralign 10:`kernel_type'}" 
	disp in smcl in gr "{ralign 18:Number of obs}"         _col(19) " {c |} " _col(21) as result %9.0f scalar(N_l)      _col(34) %9.0f  scalar(N_r)                         _col(55) in gr "VCE method    = "  in yellow "{ralign 10:`vce_type'}" 
	disp in smcl in gr "{ralign 18:Min of `x'}"            _col(19) " {c |} " _col(21) as result %9.3f scalar(x_l_min)  _col(34) %9.3f  scalar(x_r_min)  
	disp in smcl in gr "{ralign 18:Max of `x'}"            _col(19) " {c |} " _col(21) as result %9.3f scalar(x_l_max)  _col(34) %9.3f  scalar(x_r_max)  
	disp in smcl in gr "{ralign 18:Order est. (p)}"        _col(19) " {c |} " _col(21) as result %9.0f `p'        _col(34) %9.0f  `p'                              
	disp in smcl in gr "{ralign 18:Order bias (q)}"        _col(19) " {c |} " _col(21) as result %9.0f `q'        _col(34) %9.0f  `q'  
	if ("`masspoints'"=="check" | masspoints_found==1) disp in smcl in gr "{ralign 18:Unique obs}"     _col(19) " {c |} " _col(21) as result %9.0f scalar(M_l)           _col(34) %9.0f  scalar(M_r)                    
	if ("`cluster'"!="") disp in smcl in gr "{ralign 18:Number of clusters}" _col(19) " {c |} " _col(21) as result %9.0f scalar(g_l)       _col(34) %9.0f  scalar(g_r)                         
				
			
	disp ""
	if ("`fuzzy'"=="") disp           "Outcome: `y'. Running variable: `x'."
	else               disp in yellow "Outcome: `y'. Running variable: `x'. Treatment Status: `fuzzyvar'."	
	disp in smcl in gr "{hline 19}{c TT}{hline 30}{c TT}{hline 29}"
	disp in smcl in gr _col(19) " {c |} "             _col(30) "BW est. (h)"    _col(50) " {c |} " _col(60) "BW bias (b)"  
	disp in smcl in gr "{ralign 18:Method}"        _col(19) " {c |} " _col(22) "Left of " in yellow "c" _col(40) in green "Right of " in yellow "c"  in green _col(50) " {c |} " _col(53)  "Left of " in yellow "c" _col(70) in green "Right of " in yellow "c" 
	disp in smcl in gr "{hline 19}{c +}{hline 30}{c +}{hline 29}" 
		
	if  ("`bwselect'"=="mserd" | "`bwselect'"=="" | "`all'"!="" ) {
		disp in smcl in gr "{ralign 18:mserd}"    _col(19) " {c |} " _col(22) as result %9.3f scalar(h_mserd)  _col(41) %9.3f  scalar(h_mserd)  in green _col(50) " {c |} " _col(51) as result %9.3f scalar(b_mserd)  _col(71) %9.3f  scalar(b_mserd)                                
	}
	if  ("`bwselect'"=="msetwo"  | "`all'"!="")  {		
		disp in smcl in gr "{ralign 18:msetwo}"   _col(19) " {c |} " _col(22) as result %9.3f scalar(h_msetwo_l) _col(41) %9.3f  scalar(h_msetwo_r) in green _col(50) " {c |} " _col(51) as result %9.3f scalar(b_msetwo_l)           _col(71) %9.3f  scalar(b_msetwo_r)                                
	}
	if  ("`bwselect'"=="msesum"  |  "`all'"!="")  {
		disp in smcl in gr "{ralign 18:msesum}"   _col(19) " {c |} " _col(22) as result %9.3f scalar(h_msesum) _col(41) %9.3f  scalar(h_msesum)  in green _col(50) " {c |} " _col(51) as result %9.3f scalar(b_msesum)           _col(71) %9.3f  scalar(b_msesum)                             
	}
	if  ("`bwselect'"=="msecomb1" | "`all'"!="" ) {
		disp in smcl in gr "{ralign 18:msecomb1}" _col(19) " {c |} " _col(22) as result %9.3f scalar(h_msecomb1) _col(41) %9.3f  scalar(h_msecomb1) in green _col(50) " {c |} " _col(51) as result %9.3f scalar(b_msecomb1)           _col(71) %9.3f  scalar(b_msecomb1)                                 
	}
	if  ("`bwselect'"=="msecomb2" |  "`all'"!="" ) {
		disp in smcl in gr "{ralign 18:msecomb2}" _col(19) " {c |} " _col(22) as result %9.3f scalar(h_msecomb2_l) _col(41) %9.3f  scalar(h_msecomb2_r) in green _col(50) " {c |} " _col(51) as result %9.3f scalar(b_msecomb2_l)           _col(71) %9.3f  scalar(b_msecomb2_r)                                  
	}
	if  ("`all'"!="" ) disp in smcl in gr "{hline 19}{c +}{hline 30}{c +}{hline 29}"
	if  ("`bwselect'"=="cerrd" | "`all'"!="" ){
		disp in smcl in gr "{ralign 18:cerrd}"    _col(19) " {c |} " _col(22) as result %9.3f scalar(h_cerrd) _col(41) %9.3f  scalar(h_cerrd) in green _col(50) " {c |} " _col(51) as result %9.3f scalar(b_cerrd)           _col(71) %9.3f  scalar(b_cerrd)                                
	}
	if  ("`bwselect'"=="certwo" | "`all'"!="" ){
		disp in smcl in gr "{ralign 18:certwo}"   _col(19) " {c |} " _col(22) as result %9.3f scalar(h_certwo_l) _col(41) %9.3f  scalar(h_certwo_r) in green _col(50) " {c |} " _col(51) as result %9.3f scalar(b_certwo_l)           _col(71) %9.3f  scalar(b_certwo_r)                                
	}
	if  ("`bwselect'"=="cersum" | "`all'"!="" ){
		disp in smcl in gr "{ralign 18:cersum}"   _col(19) " {c |} " _col(22) as result %9.3f scalar(h_cersum) _col(41) %9.3f  scalar(h_cersum) in green _col(50) " {c |} " _col(51) as result %9.3f scalar(b_cersum)           _col(71) %9.3f  scalar(b_cersum)                                
	}
	if  ("`bwselect'"=="cercomb1" | "`all'"!="" ){
		disp in smcl in gr "{ralign 18:cercomb1}" _col(19) " {c |} " _col(22) as result %9.3f scalar(h_cercomb1) _col(41) %9.3f  scalar(h_cercomb1) in green _col(50) " {c |} " _col(51) as result %9.3f scalar(b_cercomb1)           _col(71) %9.3f  scalar(b_cercomb1)                              
	}
	if  ("`bwselect'"=="cercomb2" | "`all'"!="" ){
		disp in smcl in gr "{ralign 18:cercomb2}" _col(19) " {c |} " _col(22) as result %9.3f scalar(h_cercomb2_l) _col(41) %9.3f  scalar(h_cercomb2_r) in green _col(50) " {c |} " _col(51) as result %9.3f scalar(b_cercomb2_l)           _col(71) %9.3f  scalar(b_cercomb2_r)                              
	}
	disp in smcl in gr "{hline 19}{c BT}{hline 30}{c BT}{hline 29}" 
   	if ("`covs'"!="")        di "Covariate-adjusted estimates. Additional covariates included: `ncovs'"
*	if (`covs_drop_coll'>=1) di "Variables dropped due to multicollinearity."
	if ("`masspoints'"=="check")  di "Running variable checked for mass points."  
	if ("`masspoints'"=="adjust" &  masspoints_found==1) di "Estimates adjusted for mass points in the running variable."  	 	

	if ("`cluster'"!="")     di "Std. Err. adjusted for clusters in " "`clustvar'"
	if ("`scaleregul'"!="1") di "Scale regularization: " `scaleregul'
	if ("`sharpbw'"~="")   	 di in red "WARNING: bandwidths automatically computed for sharp RD estimation."
	if ("`perf_comp'"~="")   di in red "WARNING: bandwidths automatically computed for sharp RD estimation because perfect compliance was detected on at least one side of the threshold."

	restore
	ereturn clear
	ereturn scalar N_l = scalar(N_l)
	ereturn scalar N_r = scalar(N_r)
	ereturn scalar c = `c'
	ereturn scalar p = `p'
	ereturn scalar q = `q'
	ereturn local kernel = "`kernel_type'"
	ereturn local bwselect = "`bwselect'"
	ereturn local vce_select = "`vce_type'"
	if ("`covs'"!="")    ereturn local covs "`covs'"
	if ("`cluster'"!="") ereturn local clustvar "`clustvar'"
	ereturn local outcomevar "`y'"
	ereturn local runningvar "`x'"
	ereturn local depvar "`y'"
	ereturn local cmd "rdbwselect"

	ereturn matrix mat_h = mat_h
	ereturn matrix mat_b = mat_b
	
	if  ("`bwselect'"=="mserd" | "`bwselect'"=="" | "`all'"!="" ) {
		ereturn scalar h_mserd = scalar(h_mserd)
		ereturn scalar b_mserd = scalar(b_mserd)
		}
	if  ("`bwselect'"=="msesum"  |  "`all'"!="")  {
		ereturn scalar h_msesum = scalar(h_msesum)
		ereturn scalar b_msesum = scalar(b_msesum)
		}
	if  ("`bwselect'"=="msetwo"  | "`all'"!="")  {	
		ereturn scalar h_msetwo_l = scalar(h_msetwo_l)
		ereturn scalar h_msetwo_r = scalar(h_msetwo_r)
		ereturn scalar b_msetwo_l = scalar(b_msetwo_l)
		ereturn scalar b_msetwo_r = scalar(b_msetwo_r)
		}
	if  ("`bwselect'"=="msecomb1" | "`all'"!="" ) {
		ereturn scalar h_msecomb1 = scalar(h_msecomb1)
		ereturn scalar b_msecomb1 = scalar(b_msecomb1)
		}
	if  ("`bwselect'"=="msecomb2" | "`all'"!="" ) {
		ereturn scalar h_msecomb2_l = scalar(h_msecomb2_l)
		ereturn scalar h_msecomb2_r = scalar(h_msecomb2_r)
		ereturn scalar b_msecomb2_l = scalar(b_msecomb2_l)
		ereturn scalar b_msecomb2_r = scalar(b_msecomb2_r)
		}
	if  ("`bwselect'"=="cerrd" | "`all'"!="") {
		ereturn scalar h_cerrd = scalar(h_cerrd)
		ereturn scalar b_cerrd = scalar(b_cerrd)
		}
	if  ("`bwselect'"=="cersum" | "`all'"!="") {
		ereturn scalar h_cersum = scalar(h_cersum)
		ereturn scalar b_cersum = scalar(b_cersum)
		}
	if  ("`bwselect'"=="certwo" | "`all'"!="") {
		ereturn scalar h_certwo_l = scalar(h_certwo_l)
		ereturn scalar h_certwo_r = scalar(h_certwo_r)
		ereturn scalar b_certwo_l = scalar(b_certwo_l)
		ereturn scalar b_certwo_r = scalar(b_certwo_r)
		}
	if  ("`bwselect'"=="cercomb1" | "`all'"!="") {
		ereturn scalar h_cercomb1 = scalar(h_cercomb1)
		ereturn scalar b_cercomb1 = scalar(b_cercomb1)
		}
	if  ("`bwselect'"=="cercomb2" | "`all'"!="") { 
		ereturn scalar h_cercomb2_l = scalar(h_cercomb2_l)
		ereturn scalar h_cercomb2_r = scalar(h_cercomb2_r)
		ereturn scalar b_cercomb2_l = scalar(b_cercomb2_l)
		ereturn scalar b_cercomb2_r = scalar(b_cercomb2_r)
	}
	
	mata mata clear 

end
