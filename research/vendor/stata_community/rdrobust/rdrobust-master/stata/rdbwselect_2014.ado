*!version 6.0  2014-10-14

capture program drop rdbwselect_2014
program define rdbwselect_2014, eclass
	syntax anything [if] [in] [, c(real 0) deriv(real 0) p(real 1) q(real 0) kernel(string) bwselect(string) rho(real 0) vce(string) matches(real 3) delta(real 0.5) cvgrid_min(real 0) cvgrid_max(real 0) cvgrid_length(real 0) cvplot all precalc scaleregul(real 1) ]

	local kernel = lower("`kernel'")
	local bwselect = upper("`bwselect'")
	local vce = lower("`vce'")

	marksample touse
	preserve
	qui keep if `touse'
	tokenize "`anything'"
	local y `1'
	local x `2'
	qui drop if `y'==. | `x'==.
	tempvar x_l x_r y_l y_r  
	local b_calc = 0
	
	if (`rho'==0){
		local b_calc = 1
		local rho = 1
	}
	
		qui su `x'  if `x'<`c', d
		local medX_l = r(p50)
		qui su `x'  if `x'>=`c', d
		local medX_r = r(p50)
		
	if ("`precalc'"==""){
		qui gen `x_l' = `x' if `x'<`c'
		qui gen `x_r' = `x' if `x'>=`c'
		qui gen `y_l' = `y' if `x'<`c'
		qui gen `y_r' = `y' if `x'>=`c'

		qui su `x'
		local x_min = r(min)
		local x_max = r(max)
		qui su `x_l',d
		local N_l = r(N)
		local range_l = abs(r(max)-r(min))
		qui su `x_r',d 
		local N_r = r(N)
		local range_r = abs(r(max)-r(min))
		local N = `N_r' + `N_l'

	if ("`deriv'">"0" & "`p'"=="1" & "`q'"=="0"){
		local p = `deriv'+1
	}

		if ("`q'"=="0") {
			local q = `p'+1
		}

		
		**************************** ERRORS
	if (`c'<=`x_min' | `c'>=`x_max'){
	 di "{err}{cmd:c()} should be set within the range of `x'"  
	 exit 125
	}
	
	if (`N_l'<20 | `N_r'<20){
	 di "{err}Not enough observations to perform calculations"  
	 exit 2001
	}
	
	if ("`p'">"8"){
	 di "{err}{cmd:p()} should be less or equal than 8 for this version of the software package"  
	 exit 125
	}
	
	
	if ("`kernel'"~="uni" & "`kernel'"~="uniform" & "`kernel'"~="tri" & "`kernel'"~="triangular" & "`kernel'"~="epa" & "`kernel'"~="epanechnikov" & "`kernel'"~="" ){
	 di "{err}{cmd:kernel()} incorrectly specified"  
	 exit 7
	}

	if ("`bwselect'"~="CCT" & "`bwselect'"~="IK" & "`bwselect'"~="CV" & "`bwselect'"~=""){
	 di "{err}{cmd:bwselect()} incorrectly specified"  
	 exit 7
	}

	if ("`vce'"~="resid" & "`vce'"~="nn" & "`vce'"~=""){ 
	 di "{err}{cmd:vce()} incorrectly specified"  
	 exit 7
	}

	if ("`p'"<"0" | "`q'"<="0" | "`deriv'"<"0" | "`matches'"<="0" | `scaleregul'<0){
	 di "{err}{cmd:p()}, {cmd:q()}, {cmd:deriv()}, {cmd:matches()} and {cmd:scaleregul()} should be positive"  
	 exit 411
	}

	if ("`p'">="`q'" & "`q'">"0"){
	 di "{err}{cmd:q()} should be higher than {cmd:p()}"  
	 exit 125
	}

	if ("`deriv'">"`p'" & "`deriv'">"0" ){
	 di "{err}{cmd:deriv()} can not be higher than {cmd:p()}"  
	 exit 125
	}

	if ("`p'">"0" ) {
		local p_round = round(`p')/`p'
		local q_round = round(`q')/`q'
		local d_round = round(`deriv'+1)/(`deriv'+1)
		local m_round = round(`matches')/`matches'

	if (`p_round'!=1 | `q_round'!=1 |`d_round'!=1 |`m_round'!=1 ){
	 di "{err}{cmd:p()}, {cmd:q()}, {cmd:deriv()} and {cmd:matches()} should be integers"  
	 exit 126
	}
	}
	
	if (`delta'>1 | `delta'<=0){
	 di "{err}{cmd:delta()}should be set between 0 and 1"  
	 exit 125
	}

	if (`rho'>1 | `rho'<0){
	 di "{err}{cmd:rho()}should be set between 0 and 1"  
	 exit 125
	}

	if (`cvgrid_min'<0 | `cvgrid_max'<0 | `cvgrid_length'<0 ){
	 di "{err}{cmd:cvgrid_min()}, {cmd:cvgrid_max()} and {cmd:cvgrid_length()} should be positive numbers"
	 exit 126
	}

	if (`cvgrid_min'>`cvgrid_max' ){
		di "{err}{cmd:cvgrid_min()} should be lower than {cmd:cvgrid_max()}"
		exit 125
	}

	if (`deriv'>0 & ("`bwselect'"=="IK" | "`bwselect'"=="CV" | "`all'"!="")) {
		di "{err}{cmd:IK} and {cmd:CV} implementations are not availale for {cmd:deriv}>0; use CCT instead"
		exit 125
	}
	
		if ("`exit'">"0") {
			exit
		}

	if ("`kernel'"=="epanechnikov" | "`kernel'"=="epa") {
			local kernel_type = "Epanechnikov"
		}
	else if ("`kernel'"=="uniform" | "`kernel'"=="uni") {
			local kernel_type = "Uniform"
		}
	else  {
			local kernel_type = "Triangular"
		}
	}	

	local p1 = `p' + 1
	local p2 = `p' + 2
	local q1 = `q' + 1
	local q2 = `q' + 2
	local q3 = `q' + 3
	quietly count if `x'<`c' 
	local N_l = r(N)
	quietly count if `c'<=`x' 
	local N_r = r(N)
	local N = `N_r' + `N_l'
	local m = `matches' + 1

	if ("`kernel'"=="epanechnikov" | "`kernel'"=="epa") {
			local kid=3
			local C_pilot=2.34
	}
	else if ("`kernel'"=="uniform" | "`kernel'"=="uni") {
			local kid=2
			local C_pilot=1.84
	}
	else  {
			local kid=1
			local C_pilot=2.58
	}
	
	rdbwselect_2014_kconst `p' `deriv' `kid'
	local C1_h = e(C1)
	local C2_h = e(C2)
	rdbwselect_2014_kconst `q' `q' `kid'
	local C1_b = e(C1)
	local C2_b = e(C2)
	rdbwselect_2014_kconst `q1' `q1' `kid'
	local C1_q = e(C1)
	local C2_q = e(C2)
		
	rdbwselect_2014_kconst `q' `q' 2
	local C1_b_uni = e(C1)
	local C2_b_uni = e(C2)
	rdbwselect_2014_kconst `q1' `q1' 2
	local C1_q_uni = e(C1)
	local C2_q_uni = e(C2)
		
	***********************************************************************
	**************************** CCT Approach
	***********************************************************************
	qui su `x', d
	local h_pilot_CCT = `C_pilot'*min(r(sd),(r(p75)-r(p25))/1.349)*r(N)^(-1/5)
		
	mata{
	h_pilot_CCT=`h_pilot_CCT'
	N_l = `N_l'
	N_r = `N_r'
	p = `p'
	q = `q'
	c = `c'
	C1_h=`C1_h'
	C2_h=`C2_h'
	C1_b=`C1_b'
	C2_b=`C2_b'
	C1_q=`C1_q'
	C2_q=`C2_q'

	C1_b_uni=`C1_b_uni'
	C2_b_uni=`C2_b_uni'
	C1_q_uni=`C1_q_uni'
	C2_q_uni=`C2_q_uni'
	
	deriv = `deriv'
	p1 = p+1;	q1 = q+1;	p2 = p+2;	q2 = q+2;	p3 = p+3;	q3 = q+3
	Y = st_data(.,("`y'"), 0);	X = st_data(.,("`x'"), 0)
	X_l = select(X,X:<c);	X_r = select(X,X:>=c)
	Y_l = select(Y,X:<c);	Y_r = select(Y,X:>=c)
	X_lq2 = J(N_l, q+3, .);	X_rq2 = J(N_r, q+3, .)
	for (j=1; j<=q3; j++) {
		X_lq2[.,j] = (X_l:-c):^(j-1)
		X_rq2[.,j] = (X_r:-c):^(j-1)
	}
	
	X_lq1 = X_lq2[.,1::q2];X_rq1 = X_rq2[.,1::q2]
	X_lq  = X_lq2[.,1::q1];X_rq  = X_rq2[.,1::q1]
	X_lp  = X_lq2[.,1::p1];X_rp  = X_rq2[.,1::p1]

	if ("`bwselect'"=="CCT" | "`bwselect'"=="" | "`all'"!="") {

	display("Computing CCT bandwidth selector.")

	*** Step 1: q_CCT
	* Variances for all CCT estimators
	w_pilot_l = rdbwselect_2014_kweight(X_l,c,h_pilot_CCT,"`kernel'")
	w_pilot_r = rdbwselect_2014_kweight(X_r,c,h_pilot_CCT,"`kernel'")
	Gamma_pilot_lq1 = cross(X_lq1, w_pilot_l, X_lq1);	Gamma_pilot_rq1 = cross(X_rq1, w_pilot_r, X_rq1)
	Gamma_pilot_lq = Gamma_pilot_lq1[1::`q1',1::`q1'];	Gamma_pilot_rq = Gamma_pilot_rq1[1::`q1',1::`q1']
	Gamma_pilot_lp = Gamma_pilot_lq1[1::`p1',1::`p1'];	Gamma_pilot_rp = Gamma_pilot_rq1[1::`p1',1::`p1']
	invGamma_pilot_lq1 = invsym(Gamma_pilot_lq1);	invGamma_pilot_rq1 = invsym(Gamma_pilot_rq1)
	invGamma_pilot_lq  = invsym(Gamma_pilot_lq);	invGamma_pilot_rq  = invsym(Gamma_pilot_rq)
	invGamma_pilot_lp  = invsym(Gamma_pilot_lp);	invGamma_pilot_rp  = invsym(Gamma_pilot_rp)
	sigma_l_pilot = rdbwselect_2014_rdvce(X_l, Y_l, Y_l, `p', `h_pilot_CCT', `matches', "`vce'", "`kernel'")
	sigma_r_pilot = rdbwselect_2014_rdvce(X_r, Y_r, Y_r, `p', `h_pilot_CCT', `matches', "`vce'", "`kernel'")
	Psi_pilot_lq1 = cross(X_lq1, w_pilot_l:*sigma_l_pilot:*w_pilot_l, X_lq1)
	Psi_pilot_rq1 = cross(X_rq1, w_pilot_r:*sigma_r_pilot:*w_pilot_r, X_rq1)
	Psi_pilot_lq  = Psi_pilot_lq1[1::`q1',1::`q1'];	Psi_pilot_rq  = Psi_pilot_rq1[1::`q1',1::`q1']
	Psi_pilot_lp  = Psi_pilot_lq1[1::`p1',1::`p1'];	Psi_pilot_rp  = Psi_pilot_rq1[1::`p1',1::`p1']
	V_m3_pilot_CCT = (invGamma_pilot_lq1*Psi_pilot_lq1*invGamma_pilot_lq1)[`q'+2,`q'+2]      + (invGamma_pilot_rq1*Psi_pilot_rq1*invGamma_pilot_rq1)[`q'+2,`q'+2]
	V_m2_pilot_CCT = (invGamma_pilot_lq*Psi_pilot_lq*invGamma_pilot_lq)[`q'+1,`q'+1]         + (invGamma_pilot_rq*Psi_pilot_rq*invGamma_pilot_rq)[`q'+1,`q'+1]
	V_m0_pilot_CCT = (invGamma_pilot_lp*Psi_pilot_lp*invGamma_pilot_lp)[`deriv'+1,`deriv'+1] + (invGamma_pilot_rp*Psi_pilot_rp*invGamma_pilot_rp)[`deriv'+1,`deriv'+1]
	* Numerator
	N_q_CCT=(2*q+3)*`N'*`h_pilot_CCT'^(2*q+3)*V_m3_pilot_CCT
	* Denominator
	m4_l_pilot_CCT = (invsym(cross(X_lq2,X_lq2))*cross(X_lq2,Y_l))[`q3',1]
	m4_r_pilot_CCT = (invsym(cross(X_rq2,X_rq2))*cross(X_rq2,Y_r))[`q3',1]
	D_q_CCT = 2*(C1_q*(m4_r_pilot_CCT-(-1)^(deriv+q)*m4_l_pilot_CCT))^2
	* Final
	q_CCT = (N_q_CCT/(`N'*D_q_CCT))^(1/(2*q+5))

	*** Step 2: b_CCT
	* Numerator
	N_b_CCT = (2*p+3)*`N'*`h_pilot_CCT'^(2*p+3)*V_m2_pilot_CCT
	* Denominator
	w_q_l=rdbwselect_2014_kweight(X_l,c,q_CCT,"`kernel'")
	w_q_r=rdbwselect_2014_kweight(X_r,c,q_CCT,"`kernel'")
	m3_l_CCT = (invsym(cross(X_lq1, w_q_l, X_lq1))*cross(X_lq1, w_q_l, Y_l))[q2,1]
	m3_r_CCT = (invsym(cross(X_rq1, w_q_r, X_rq1))*cross(X_rq1, w_q_r, Y_r))[q2,1]
	D_b_CCT = 2*(q-p)*(C1_b*(m3_r_CCT - (-1)^(deriv+q+1)*m3_l_CCT))^2
	* Regul
	invGamma_q_lq1_CCT = invsym(cross(X_lq1, w_q_l, X_lq1))
	invGamma_q_rq1_CCT = invsym(cross(X_rq1, w_q_r, X_rq1))
	Psi_q_lq1_CCT = cross(X_lq1, w_q_l:*sigma_l_pilot:*w_q_l, X_lq1)
	Psi_q_rq1_CCT = cross(X_rq1, w_q_r:*sigma_r_pilot:*w_q_r, X_rq1)
	V_m3_q_CCT = (invGamma_q_lq1_CCT*Psi_q_lq1_CCT*invGamma_q_lq1_CCT)[`q'+2,`q'+2] + (invGamma_q_rq1_CCT*Psi_q_rq1_CCT*invGamma_q_rq1_CCT)[`q'+2,`q'+2]
	R_b_CCT = `scaleregul'*2*(q-p)*C1_b^2*3*V_m3_q_CCT
	* Final
	b_CCT = (N_b_CCT / (`N'*(D_b_CCT + R_b_CCT)))^(1/(2*q+3))
		
	*** Step 3: h_CCT
	* Numerator
	N_h_CCT = (2*`deriv'+1)*`N'*`h_pilot_CCT'^(2*`deriv'+1)*V_m0_pilot_CCT
	* Denominator
	w_b_l=rdbwselect_2014_kweight(X_l,`c',b_CCT,"`kernel'")
	w_b_r=rdbwselect_2014_kweight(X_r,`c',b_CCT,"`kernel'")
	m2_l_CCT = (invsym(cross(X_lq, w_b_l, X_lq))*cross(X_lq, w_b_l, Y_l))[`p2',1]
	m2_r_CCT = (invsym(cross(X_rq, w_b_r, X_rq))*cross(X_rq, w_b_r, Y_r))[`p2',1]
	D_h_CCT = 2*(p+1-`deriv')*(C1_h*(m2_r_CCT - (-1)^(`deriv'+p+1)*m2_l_CCT))^2
	* Regul
	invGamma_b_lq_CCT = invsym(cross(X_lq, w_b_l, X_lq))
	invGamma_b_rq_CCT = invsym(cross(X_rq, w_b_r, X_rq))
	Psi_b_lq_CCT = cross(X_lq, w_b_l:*sigma_l_pilot:*w_b_l, X_lq)
	Psi_b_rq_CCT = cross(X_rq, w_b_r:*sigma_r_pilot:*w_b_r, X_rq)
	V_m2_b_CCT = (invGamma_b_lq_CCT*Psi_b_lq_CCT*invGamma_b_lq_CCT)[`p2',`p2'] + (invGamma_b_rq_CCT*Psi_b_rq_CCT*invGamma_b_rq_CCT)[`p2',`p2']
	R_h_CCT = `scaleregul'*2*(`p'+1-`deriv')*C1_h^2*3*V_m2_b_CCT
	* Final
	h_CCT = (N_h_CCT / (`N'*(D_h_CCT+R_h_CCT)))^(1/(2*p+3))

	st_numscalar("h_CCT",h_CCT)
	st_numscalar("q_CCT",q_CCT)
	
	if (`b_calc'==0) {
		b_CCT = h_CCT/`rho'
	}
	st_numscalar("b_CCT",b_CCT)
	}

	***************************************************************************************************
	******************** IK
	**************************************************************************************************
	if ("`bwselect'"=="IK" | "`all'"~="") {

	display("Computing IK bandwidth selector.")
	h_pilot_IK = 1.84*sqrt(variance(X))*length(X)^(-1/5)
	n_l_h1 = length(select(X_l,X_l:>=`c'-h_pilot_IK))
	n_r_h1 = length(select(X_r,X_r:<=`c'+h_pilot_IK))
	f0_pilot=(n_r_h1+n_l_h1)/(2*`N'*h_pilot_IK)
	s2_l_pilot = variance(select(Y_l,X_l:>=`c'-h_pilot_IK))
	s2_r_pilot = variance(select(Y_r,X_r:<=`c'+h_pilot_IK))

	if (s2_l_pilot==0){
		s2_l_pilot=variance(select(Y_l,X_l:>=`c'-2*h_pilot_IK))
	}
	
	if (s2_r_pilot==0){
		s2_r_pilot=variance(select(Y_r,X_r:<=`c'+2*h_pilot_IK))
	}
	
	V_IK_pilot = (s2_r_pilot+s2_l_pilot)/f0_pilot
	Vm0_pilot_IK = C2_h*V_IK_pilot
	Vm2_pilot_IK = C2_b*V_IK_pilot
	Vm3_pilot_IK = C2_q*V_IK_pilot
	
	* Select Median Sample to compute derivative (as in IK code)
	x_IK_med_l = select(X_l,X_l:>=`medX_l'); y_IK_med_l = select(Y_l,X_l:>=`medX_l')
	x_IK_med_r = select(X_r,X_r:<=`medX_r'); y_IK_med_r = select(Y_r,X_r:<=`medX_r')
	x_IK_med = x_IK_med_r \ x_IK_med_l
	y_IK_med = y_IK_med_r \ y_IK_med_l
	sample_IK = length(x_IK_med)
	X_IK_med_q2 = J(sample_IK, `q3', .)
	for (j=1; j<= `q3' ; j++) {
			X_IK_med_q2[.,j] = (x_IK_med:-`c'):^(j-1)
	}
	X_IK_med_q1 = X_IK_med_q2[.,1::`q2']
	* Add cutoff dummy
	X_IK_med_q2 = (X_IK_med_q2, x_IK_med:>=c)
	X_IK_med_q1 = (X_IK_med_q1, x_IK_med:>=c)
	
	*** Compute b_IK
	* Pilot Bandwidth
		N_q_r_pilot_IK = (2*q+3)*C2_q_uni*(s2_r_pilot/f0_pilot)
		N_q_l_pilot_IK = (2*q+3)*C2_q_uni*(s2_l_pilot/f0_pilot)
		m4_pilot_IK = (invsym(cross(X_IK_med_q2, X_IK_med_q2))*cross(X_IK_med_q2, y_IK_med))[q+3,1]
		D_q_pilot_IK = 2*(C1_q_uni*m4_pilot_IK)^2
		h3_r_pilot_IK = (N_q_r_pilot_IK / (N_r*D_q_pilot_IK))^(1/(2*q+5))
		h3_l_pilot_IK = (N_q_l_pilot_IK / (N_l*D_q_pilot_IK))^(1/(2*q+5))
	* Data for derivative
		X_lq_IK_h3=select(X_lq1,X_l:>=c-h3_l_pilot_IK); Y_l_IK_h3 =select(Y_l,X_l:>=c-h3_l_pilot_IK)
		X_rq_IK_h3=select(X_rq1,X_r:<=c+h3_r_pilot_IK);	Y_r_IK_h3 =select(Y_r,X_r:<=c+h3_r_pilot_IK)
		m3_l_IK = (invsym(cross(X_lq_IK_h3, X_lq_IK_h3))*cross(X_lq_IK_h3, Y_l_IK_h3))[q+2,1]
		m3_r_IK = (invsym(cross(X_rq_IK_h3, X_rq_IK_h3))*cross(X_rq_IK_h3, Y_r_IK_h3))[q+2,1]
		D_b_IK = 2*(q-p)*(C1_b*(m3_r_IK - (-1)^(`deriv'+`q'+1)*m3_l_IK))^2
		N_b_IK = (2*p+3)*Vm2_pilot_IK
	* Regularization
		temp = rdbwselect_2014_regconst(`q1',1)
		con = temp[`q2',`q2']
		n_l_h3 = length(Y_l_IK_h3);	n_r_h3 = length(Y_r_IK_h3)
		r_l_b = (con*s2_l_pilot)/(n_l_h3*h3_l_pilot_IK^(2*`q1'))
		r_r_b = (con*s2_r_pilot)/(n_r_h3*h3_r_pilot_IK^(2*`q1'))
		R_b_IK = `scaleregul'*2*(q-p)*C1_b^2*3*(r_l_b + r_r_b)
	* Final bandwidth:
		b_IK   = (N_b_IK / (`N'*(D_b_IK + R_b_IK)))^(1/(2*q+3))
	
	*** Compute h_IK
	* Pilot Bandwidth
		N_b_r_pilot_IK = (2*p+3)*C2_b_uni*(s2_r_pilot/f0_pilot)
		N_b_l_pilot_IK = (2*p+3)*C2_b_uni*(s2_l_pilot/f0_pilot)
		m3_pilot_IK = (invsym(cross(X_IK_med_q1, X_IK_med_q1))*cross(X_IK_med_q1, y_IK_med))[q+2,1]
		D_b_pilot_IK = 2*(q-p)*(C1_b_uni*m3_pilot_IK)^2
		h2_l_pilot_IK  = (N_b_l_pilot_IK / (N_l*D_b_pilot_IK))^(1/(2*q+3))
		h2_r_pilot_IK  = (N_b_r_pilot_IK / (N_r*D_b_pilot_IK))^(1/(2*q+3))
	* Data for derivative
		X_lq_IK_h2=select(X_lq,X_l:>=c-h2_l_pilot_IK); Y_l_IK_h2 =select(Y_l,X_l:>=c-h2_l_pilot_IK)
		X_rq_IK_h2=select(X_rq,X_r:<=c+h2_r_pilot_IK); Y_r_IK_h2 =select(Y_r,X_r:<=c+h2_r_pilot_IK)
		m2_l_IK = (invsym(cross(X_lq_IK_h2, X_lq_IK_h2))*cross(X_lq_IK_h2, Y_l_IK_h2))[p+2,1]
		m2_r_IK = (invsym(cross(X_rq_IK_h2, X_rq_IK_h2))*cross(X_rq_IK_h2, Y_r_IK_h2))[p+2,1]
		D_h_IK = 2*(`p'+1-`deriv')*(C1_h*(m2_r_IK - (-1)^(`deriv'+`p'+1)*m2_l_IK))^2
		N_h_IK = (2*`deriv'+1)*Vm0_pilot_IK
	* Regularization
		temp = rdbwselect_2014_regconst(`p1',1)
		con = temp[`p2',`p2']
		n_l_h2 = length(Y_l_IK_h2);	n_r_h2 = length(Y_r_IK_h2)
		r_l_h = (con*s2_l_pilot)/(n_l_h2*h2_l_pilot_IK^(2*`p1'))
		r_r_h = (con*s2_r_pilot)/(n_r_h2*h2_r_pilot_IK^(2*`p1'))
		R_h_IK = `scaleregul'*2*(`p'+1-`deriv')*C1_h^2*3*(r_l_h + r_r_h)
	* Final bandwidth
		h_IK  = (N_h_IK / (`N'*(D_h_IK + R_h_IK)))^(1/(2*p+3))

	*** DJMC (not documented)
		D_h_DM  = 2*(`p'+1-`deriv')*C1_h^2*(m2_r_IK^2 + m2_l_IK^2)
		D_b_DM  =       2*(`q'-`p')*C1_b^2*(m3_r_IK^2 + m3_l_IK^2)
		h_DM = (N_h_IK / (`N'*D_h_DM))^(1/(2*`p'+3))
		b_DM = (N_b_IK / (`N'*D_b_DM))^(1/(2*`q'+3))

	st_numscalar("h_IK", h_IK)
	st_numscalar("b_IK", b_IK)
	
	if (`b_calc'==0) {
		b_IK = h_IK/`rho'
	}
	st_numscalar("b_IK",b_IK)
	}

	*********************************************************************
	********************************** C-V  *****************************
	*********************************************************************
	if ("`bwselect'"=="CV" | "`all'"~="") {

	display("Computing CV bandwidth selector.")
	v_CV_l = 0;w_CV_l = 0
	minindex(X_l, `N_l', v_CV_l, w_CV_l)
	x_sort_l = X_l[v_CV_l];y_sort_l = Y_l[v_CV_l]
	v_CV_r = 0;w_CV_r = 0
	maxindex(X_r, `N_r', v_CV_r, w_CV_r)
	x_sort_r = X_r[v_CV_r];y_sort_r = Y_r[v_CV_r]
	h_CV_min = 0
	if (`N_r'>20 & `N_l'>20){
	h_CV_min  = min((abs(x_sort_r[`N_r']-x_sort_r[`N_r'-20]),abs(x_sort_l[`N_l']-x_sort_l[`N_l'-20])))
	}
	h_CV_max  = min((abs(x_sort_r[1]-x_sort_r[`N_r']),abs(x_sort_l[1]-x_sort_l[`N_l'])))
	h_CV_jump = min((abs(x_sort_r[1]-x_sort_r[`N_r'])/10,abs(x_sort_l[1]-x_sort_l[`N_l']))/10)
	st_numscalar("h_CV_min", h_CV_min[1,1])
	st_numscalar("h_CV_max", h_CV_max[1,1])
	st_numscalar("h_CV_jump", h_CV_jump[1,1])
	if ("`cvgrid_min'"=="0") {
		cvgrid_min = h_CV_min
	}
	else if ("`cvgrid_min'"!="0") {
		cvgrid_min = `cvgrid_min'
	}
	if ("`cvgrid_max'"=="0") {
		cvgrid_max = h_CV_max
	}
	else if ("`cvgrid_max'"!="0") {
		cvgrid_max = `cvgrid_max'
	}
	if ("`cvgrid_length'"=="0") {
		cvgrid_length = abs(cvgrid_max-cvgrid_min)/20
	}
	else if ("`cvgrid_length'"!="0") {
		cvgrid_length = `cvgrid_length'
	}
	if (cvgrid_min>=cvgrid_max){
		cvgrid_min = 0
	}
	st_numscalar("cvgrid_min",    cvgrid_min)
	st_numscalar("cvgrid_max",    cvgrid_max)
	st_numscalar("cvgrid_length", cvgrid_length)
	h_CV_seq  = range(cvgrid_min, cvgrid_max, cvgrid_length)
	s_CV = length(h_CV_seq)
	CV_l = CV_r = J(1, s_CV, 0)
	n_CV_l = round(`delta'*`N_l')-3
	n_CV_r = round(`delta'*`N_r')-3

	for (v=1; v<=s_CV; v++) {
	for (k=0; k<=n_CV_l; k++) {
		ind_l = `N_l'-k-1
		x_CV_sort_l = x_sort_l[1::ind_l] 
		y_CV_sort_l = y_sort_l[1::ind_l] 
		w_CV_sort_l = rdbwselect_2014_kweight(x_CV_sort_l,x_sort_l[ind_l+1],h_CV_seq[v],"`kernel'")
		x_CV_l = select(x_CV_sort_l,w_CV_sort_l:>0)
		y_CV_l = select(y_CV_sort_l,w_CV_sort_l:>0)
		w_CV_l = select(w_CV_sort_l,w_CV_sort_l:>0)
		XX_CV_l = J(length(w_CV_l),`p1',.)
	for (j=1; j<=`p1'; j++) {
		XX_CV_l[.,j] = (x_CV_l :- x_sort_l[ind_l+1]):^(j-1)
		}
	y_CV_hat_l = (invsym(cross(XX_CV_l,w_CV_l,XX_CV_l))*cross(XX_CV_l,w_CV_l,y_CV_l))[1]
	mse_CV_l = (y_sort_l[ind_l+1] - y_CV_hat_l)^2
	CV_l[v] = CV_l[v] + mse_CV_l
	}
	for (k=0; k<=n_CV_r; k++) {
		ind_r = `N_r'-k-1
		x_CV_sort_r = x_sort_r[1::ind_r] 
		y_CV_sort_r = y_sort_r[1::ind_r] 
		w_CV_sort_r = rdbwselect_2014_kweight(x_CV_sort_r,x_sort_r[ind_r+1],h_CV_seq[v],"`kernel'")
		x_CV_r = select(x_CV_sort_r,w_CV_sort_r:>0)
		y_CV_r = select(y_CV_sort_r,w_CV_sort_r:>0)
		w_CV_r = select(w_CV_sort_r,w_CV_sort_r:>0)
		XX_CV_r = J(length(w_CV_r),`p1',.)
		
		for (j=1; j<= `p1' ; j++) {
			XX_CV_r[.,j] = (x_CV_r :- x_sort_r[ind_r+1]):^(j-1)
		}
		
		y_CV_hat_r = (invsym(cross(XX_CV_r,w_CV_r,XX_CV_r))*cross(XX_CV_r,w_CV_r,y_CV_r))[1]
		mse_CV_r = (y_sort_r[ind_r+1] - y_CV_hat_r)^2
		CV_r[v] = CV_r[v] + mse_CV_r
	}
	}

	CV_sum = CV_l + CV_r
	CV_sum_order = order(abs(CV_sum'),1)
	h_CV = h_CV_seq[CV_sum_order] 
	h_CV = h_CV[1,1]

	if (`b_calc'==0) {
		b_CV = h_CV/`rho'
	}
	st_numscalar("h_CV", h_CV)
	st_numscalar("b_CV", b_CV)
	}
	}

	*******************************************************************************

	disp ""
	disp in smcl in gr "Bandwidth estimators for RD local polynomial regression" 
	disp ""
	disp ""
	disp in smcl in gr "{ralign 21: Cutoff c = `c'}"      _col(22) " {c |} " _col(23) in gr "Left of " in yellow "c"  _col(36) in gr "Right of " in yellow "c" _col(61) in gr "Number of obs  = "  in yellow %10.0f `N_l'+`N_r'
	disp in smcl in gr "{hline 22}{c +}{hline 22}"                                                                                                             _col(61) in gr "NN matches     = "  in yellow %10.0f `matches'
	disp in smcl in gr "{ralign 21:Number of obs}"        _col(22) " {c |} " _col(23) as result %9.0f `N_l'   _col(37) %9.0f  `N_r'                            _col(61) in gr "Kernel type    = "  in yellow "{ralign 10:`kernel_type'}" 
	if ("`all'"=="" & "`bwselect'"!="CV")  {  
	disp in smcl in gr "{ralign 21:Order loc. poly. (p)}" _col(22) " {c |} " _col(23) as result %9.0f `p'        _col(37) %9.0f  `p'                              
	disp in smcl in gr "{ralign 21:Order bias (q)}"       _col(22) " {c |} " _col(23) as result %9.0f `q'        _col(37) %9.0f  `q'  
	disp in smcl in gr "{ralign 21:Range of `x'}"         _col(22) " {c |} " _col(23) as result %9.3f `range_l'  _col(37) %9.3f  `range_r'                               
	}
	if ("`bwselect'"=="CV" | "`all'"!="")  {  
	disp in smcl in gr "{ralign 21:Order loc. poly. (p)}" _col(22) " {c |} " _col(23) as result %9.0f `p'        _col(37) %9.0f  `p'       _col(61) in gr "Min BW grid    = " in yellow %10.5f cvgrid_min
	disp in smcl in gr "{ralign 21:Order bias (q)}"       _col(22) " {c |} " _col(23) as result %9.0f `q'        _col(37) %9.0f  `q'       _col(61) in gr "Max BW grid    = " in yellow %10.5f cvgrid_max
	disp in smcl in gr "{ralign 21:Range of `x'}"         _col(22) " {c |} " _col(23) as result %9.3f `range_l'  _col(37) %9.3f  `range_r' _col(61) in gr "Length BW grid = " in yellow %10.5f cvgrid_length
	}   

	disp ""
	disp in smcl in gr "{hline 10}{c TT}{hline 35}" 
	disp in smcl in gr "{ralign 9:Method}"   _col(10) " {c |} " _col(18) "h" _col(30) "b" _col(41) "rho" _n  "{hline 10}{c +}{hline 35}"
	if ("`bwselect'"=="IK")  {
	disp in smcl in gr "{ralign 9:IK }"      _col(10) " {c |} " _col(11) in ye %9.0g h_IK  _col(25) in ye %9.0g b_IK  _col(38) in ye %9.0g h_IK/b_IK
	}
	if ("`bwselect'"=="CV")  {
	disp in smcl in gr "{ralign 9:CV }"      _col(10) " {c |} " _col(11) in ye %9.0g h_CV  _col(30) in ye "NA"  _col(42) in ye %9.0g "NA"
	}	
	if ("`all'"~="") {
	disp in smcl in gr "{ralign 9:CCT}"     _col(10) " {c |} " _col(11) in ye %9.0g h_CCT _col(25) in ye %9.0g b_CCT _col(38) in ye %9.0g h_CCT/b_CCT
	disp in smcl in gr "{ralign 9:IK}"      _col(10) " {c |} " _col(11) in ye %9.0g h_IK  _col(25) in ye %9.0g b_IK  _col(38) in ye %9.0g h_IK/b_IK
	disp in smcl in gr "{ralign 9:CV}"      _col(10) " {c |} " _col(11) in ye %9.0g h_CV  _col(30) in ye  "NA"         _col(42) in ye  "NA"
	}
	if ("`bwselect'"=="" & "`all'"=="") | ("`bwselect'"=="CCT" & "`all'"=="") {
		disp in smcl in gr "{ralign 9:CCT}"      _col(10) " {c |} " _col(11) in ye %9.0g h_CCT _col(25) in ye %9.0g b_CCT _col(38) in ye %9.0g h_CCT/b_CCT
	}
	disp in smcl in gr "{hline 10}{c BT}{hline 35}"

	if ("`bwselect'"=="CV" & "`cvplot'"!="" | "`all'"!="" & "`cvplot'"!="")  {  
		local h_CV= h_CV
		mata rdbwselect_2014_cvplot(CV_sum', h_CV_seq, "xtitle(Grid of bandwidth (h)) ytitle(Cross-Validation objective function) c(l) ylabel(none) xline(`h_CV') title(Cross-Validation objective function)")
	}

	restore
	ereturn clear
	ereturn scalar N_l = `N_l'
	ereturn scalar N_r = `N_r'
	ereturn scalar c = `c'
	ereturn scalar p = `p'
	ereturn scalar q = `q'
	
	if ("`bwselect'"=="CCT" | "`bwselect'"=="" | "`all'"~="") {
	ereturn scalar h_CCT = h_CCT
	ereturn scalar b_CCT = b_CCT
	*ereturn scalar q_CCT = q_CCT
	}
	if ("`bwselect'"=="IK" | "`all'"~="") {
	ereturn scalar h_IK   = h_IK
	ereturn scalar b_IK   = b_IK
	*ereturn scalar h_djmc = `h_DJMC'
	*ereturn scalar b_djmc = `b_DJMC'
	}
	if ("`bwselect'"=="CV" | "`all'"~="") {
	ereturn scalar h_CV   = h_CV
	*ereturn scalar b_CV   = b_cv
	}
	
	mata mata clear

end


