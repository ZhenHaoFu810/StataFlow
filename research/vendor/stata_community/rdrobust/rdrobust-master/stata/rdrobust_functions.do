********************************************************************************
* RDROBUST STATA PACKAGE -- rdrobust_functions
* Authors: Sebastian Calonico, Matias D. Cattaneo, Max Farrell, Rocio Tititunik
********************************************************************************
*!version 10.0.0  2025-06-30
   
capture mata mata drop rdrobust_res()
mata
real matrix rdrobust_res(real matrix X, real matrix y, real matrix T, real matrix Z, real matrix m, real matrix hii, string vce, real scalar matches, dups, dupsid, real scalar d)
{
n = length(y)
dT=dZ=0
if (rows(T)>1) dT = 1
if (rows(Z)>1) dZ = cols(Z)
res = J(n,1+dT+dZ,.)		
if (vce=="nn") {
	for (pos=1; pos<=n; pos++) {
		rpos = dups[pos] - dupsid[pos]
		lpos = dupsid[pos] - 1
		while (lpos+rpos < min((matches,n-1))) {
			if (pos-lpos-1 <= 0) rpos = rpos + dups[pos+rpos+1]
			else if (pos+rpos+1>n) lpos = lpos + dups[pos-lpos-1]
			else if ((X[pos]-X[pos-lpos-1]) > (X[pos+rpos+1]-X[pos])) rpos = rpos + dups[pos+rpos+1]
			else if ((X[pos]-X[pos-lpos-1]) < (X[pos+rpos+1]-X[pos])) lpos = lpos + dups[pos-lpos-1]
			else {
				rpos = rpos + dups[pos+rpos+1]
				lpos = lpos + dups[pos-lpos-1]
			}
		}
		ind_J = (pos-lpos)::(pos+rpos)
		y_J   = sum(y[ind_J])-y[pos]
		Ji = length(ind_J)-1
		res[pos,1] = sqrt(Ji/(Ji+1))*(y[pos] :- y_J/Ji)
		if (dT==1) {
				T_J = sum(T[ind_J])-T[pos]
				res[pos,2] = sqrt(Ji/(Ji+1))*(T[pos] :- T_J/Ji)
		}
		if (dZ>0) {
			for (i=1; i<=dZ; i++) {
				Z_J = sum(Z[ind_J,i])-Z[pos,i]
				res[pos,1+dT+i] = sqrt(Ji/(Ji+1))*(Z[pos,i] :- Z_J/Ji)
			}
		}
	}		
}
else if (vce=="hc0" | vce=="hc1" | vce=="hc2" | vce=="hc3") {
 	 if (vce=="hc0") w = 1
	 if (vce=="hc1") w = sqrt(n/(n-d))
	 if (vce=="hc2") w = sqrt(1:/(1:-hii))
	 if (vce=="hc3") w =      1:/(1:-hii)
	 res[,1] = w:*(y-m[,1])
	 if (dT==1) res[,2] = w:*(T-m[,2])
	 if (dZ>0) {
		for (i=1; i<=dZ; i++) {
			res[,1+dT+i] = w:*(Z[,i]-m[,1+dT+i])
		}
	}
}
return(res)
}
mata mosave rdrobust_res(), replace
end

*************************************************************************************************************************************************************
capture mata mata drop rdrobust_kweight()
mata
real matrix rdrobust_kweight(real matrix X, real scalar c, real scalar h, string kernel)
{
u = (X:-c)/h
	if (kernel=="epanechnikov" | kernel=="epa") {
		w = (0.75:*(1:-u:^2):*(abs(u):<=1))/h
	}
	else if (kernel=="uniform" | kernel=="uni") {
		w = (0.5:*(abs(u):<=1))/h
	}
	else {
		w = ((1:-abs(u)):*(abs(u):<=1))/h
	}	
return(w)	
}
mata mosave rdrobust_kweight(), replace
end

*************************************************************************************************************************************************************
capture mata mata drop rdrobust_bw()
mata
real matrix rdrobust_bw(real matrix Y, real matrix X, real matrix T, real matrix Z, real matrix C, real matrix W, real scalar c, real scalar o, real scalar nu, real scalar o_B, real scalar h_V, real scalar h_B, real scalar scale, string vce, real scalar nnmatch, string kernel, dups, dupsid, covs_drop_coll)
{
	dT = dZ = dC = eC = indC = 0
	dW = length(W)
	w = rdrobust_kweight(X, c, h_V, kernel)
	if (dW>1) {
		w = W:*w
	}
	ind_V = selectindex(w:> 0); eY = Y[ind_V];eX = X[ind_V];eW = w[ind_V]
	n_V = length(ind_V)
	D_V = eY
	R_V = J(n_V,o+1,.)
	for (j=1; j<=(o+1); j++) R_V[.,j] = (eX:-c):^(j-1)
	invG_V = cholinv(quadcross(R_V,eW,R_V))
	e_v = J((o+1),1,0); e_v[nu+1]=1
	s = 1
	if (rows(T)>1) {
		dT = 1
		eT = T[ind_V]
		D_V = D_V,eT
	}
	if (rows(Z)>1) {
		dZ = cols(Z)
		colsZ = (2+dT)::(2+dT+dZ-1)
		eZ   = Z[ind_V,]
		D_V  = D_V,eZ
		U    = quadcross(R_V:*eW,D_V)
		ZWD  = quadcross(eZ,eW,D_V)
		UiGU = quadcross(U[,colsZ],invG_V*U) 
		ZWZ  = ZWD[,colsZ] - UiGU[,colsZ] 
		ZWY  = ZWD[,1::1+dT] - UiGU[,1::1+dT] 		
		if (covs_drop_coll==0) gamma = cholinv(ZWZ)*ZWY
		if (covs_drop_coll==1) gamma =  invsym(ZWZ)*ZWY
		if (covs_drop_coll==2) gamma =    pinv(ZWZ)*ZWY
		s = 1 \ -gamma[,1]
	}
	if (rows(C)>1) {
		dC = 1
		eC =  C[ind_V] 
		indC = order(eC,1) 
	}
	beta_V = invG_V*quadcross(R_V:*eW,D_V)	
	if (dZ==0 & dT==1) {	
	    tau_Y = factorial(nu)*beta_V[nu+1,1]
		tau_T = factorial(nu)*beta_V[nu+1,2]
		s = (1/tau_T \ -(tau_Y/tau_T^2))
	}
	if (dZ>0 & dT==1) {	
				s_T = (1 \ -gamma[,2])
                tau_Y = factorial(nu)*s'*  vec((beta_V[nu+1,1],beta_V[nu+1,colsZ]))
				tau_T = factorial(nu)*s_T'*vec((beta_V[nu+1,2],beta_V[nu+1,colsZ]))
				s = (1/tau_T \ -(tau_Y/tau_T^2) \ -(1/tau_T)*gamma[,1] + (tau_Y/tau_T^2)*gamma[,2])
	}	
	dups_V=dupsid_V=predicts_V=0
	if (vce=="nn") {
		dups_V   = dups[ind_V]
		dupsid_V = dupsid[ind_V]
	}
	if (vce=="hc0" | vce=="hc1" | vce=="hc2" | vce=="hc3") {
		predicts_V=R_V*beta_V
		if (vce=="hc2" | vce=="hc3") {
			
			hii = rowsum((R_V*invG_V):*(R_V:*eW))
			
		}
	}	
	res_V = rdrobust_res(eX, eY, eT, eZ, predicts_V, hii, vce, nnmatch, dups_V, dupsid_V, o+1)
	V_V = (invG_V*rdrobust_vce(dT+dZ, s, R_V:*eW, res_V, eC, indC)*invG_V)[nu+1,nu+1]
	v = quadcross(R_V:*eW,((eX:-c):/h_V):^(o+1))
	Hp = J(o+1, 1, 1)
	for (j=1; j<=(o+1); j++) Hp[j] = h_V^((j-1))
	BConst = (diag(Hp)*(invG_V*v))[nu+1]
		
	w = rdrobust_kweight(X, c, h_B, kernel)
	if (dW>1) {
		w = W:*w
	}
	ind = selectindex(w:> 0) 
	n_B = length(ind)
	eY = Y[ind];eX = X[ind];eW = w[ind]
	D_B = eY
	R_B = J(n_B,o_B+1,.)
	for (j=1; j<=(o_B+1); j++) R_B[.,j] = (eX:-c):^(j-1)
	invG_B = cholinv(quadcross(R_B,eW,R_B))
	if (dT==1) {
		eT = T[ind]
		D_B = D_B,eT
	}
	if (dZ>0) {
		eZ = Z[ind,]
		D_B = D_B,eZ
	}
	if (dC==1) {
		eC=C[ind]
		indC = order(eC,1) 
	}	
	beta_B = invG_B*quadcross(R_B:*eW,D_B)	
	BWreg=0
	if (scale>0) {
		e_B = J((o_B+1),1,0); e_B[o+2]=1
		dups_B=dupsid_B=hii=predicts_B=0
		if (vce=="nn") {
			dups_B   = dups[ind]
			dupsid_B = dupsid[ind]
		}
		if (vce=="hc0" | vce=="hc1" | vce=="hc2" | vce=="hc3") {
			predicts_B=R_B*beta_B
			if (vce=="hc2" | vce=="hc3") {
				
				hii = rowsum((R_B*invG_B):*(R_B:*eW))
				
			}
		}	
		res_B = rdrobust_res(eX, eY, eT, eZ, predicts_B, hii, vce, nnmatch, dups_B, dupsid_B,o_B+1)
		V_B = (invG_B*rdrobust_vce(dT+dZ, s, R_B:*eW, res_B, eC, indC)*invG_B)[o+2,o+2]
		BWreg = 3*BConst^2*V_B
	}
	B =  sqrt(2*(o+1-nu))*BConst*(s'*beta_B[o+2,]')
	V = (2*nu+1)*h_V^(2*nu+1)*V_V
	R = scale*(2*(o+1-nu))*BWreg
	rate = 1/(2*o+3)
	return(V,B,R,rate)	
}
mata mosave rdrobust_bw(), replace
end

****************************************************
capture mata mata drop rdrobust_vce()
mata
real matrix rdrobust_vce(real scalar d, real matrix s, real matrix RX, real matrix res, real matrix C, real matrix ind)
{	
	k = cols(RX)
	M = J(k,k,0)
	n  = length(C)
	if (n==1) {
		w = 1
		if (d==0){
			SS = res:^2
			M  = quadcross(RX,SS,RX)
		}
		else {
			for (i = 1; i <= 1+d; i++) {
				SS = res[,i]:*res
				for (j = 1; j <= 1+d; j++) {
					M = M + quadcross(RX,(s[i]*s[j]):*SS[,j],RX)
				}
			}
		}
	}
	else {	
		C_o   = C[ind]
		RX_o  = RX[ind,]
		res_o = res[ind,]
		info  = panelsetup(C_o,1)
		g     = rows(info)
		w = ((n-1) / (n-k)) * (g / (g-1))
		if (d==0){
			for (i=1; i<=g; i++) {
				Xi = panelsubmatrix(RX_o,  i, info)
				ri = panelsubmatrix(res_o, i, info)
				Xr = quadcross(Xi,ri)'
				M = M + quadcross(Xr,Xr)
			}
		}
		else {
			for (i=1; i<=g; i++) {
				Xi = panelsubmatrix(RX_o,  i, info)
				ri = panelsubmatrix(res_o, i, info)				
				MHolder = J(1+d,k,.)
				for (l=1; l<=1+d; l++) {
					MHolder[l,] = quadcross(Xi,s[l]:*ri[,l])'
				}
				summedvalues = colsum(MHolder)
				M = M + quadcross(summedvalues,summedvalues)
			}		
		}
	}
	return(w*M)		
}
mata mosave rdrobust_vce(), replace 
end

capture mata mata drop rdrobust_groupid()
mata
real colvector rdrobust_groupid(real colvector x, real vector at)
{
        real scalar i, j
        real colvector result, p
        result = J(rows(x),1,.)
        j = length(at)
		
        for (i=rows(x); i>0; i--) {
                        if (x[i]>=.) continue
         
			for (; j>0; j--) {
				if (at[j]<=x[i]) break
			}
            if (j>0) result[i,1] = j
        }
		
        return(result)
}
mata mosave rdrobust_groupid(), replace 
end


capture mata mata drop rdrobust_median()
mata
real colvector rdrobust_median(real colvector x)
{	
  n = length(x)
  s = sort(x,1)
  if (mod(n,2)==1) {  	
	result = s[(n+1)/2]
  } 
  else{
    i = n/2
    med1 = s[i]
    med2 = s[i+1]
    result = (med1+med2)/2	
  }     
	return(result)  
}
mata mosave rdrobust_median(), replace 
end


capture mata mata drop rdrobust_collapse()
mata
real matrix rdrobust_collapse(real matrix x, real colvector id)
{	
	info  = panelsetup(id,1)
	g     = rows(info)
	mean = J(g,2,.)
	var  = J(g,1,.)
	
	for (i=1; i<=g; i++) {
			Xi       = panelsubmatrix(x,  i, info)
			mean[i,] = mean(Xi)
			var[i]   = variance(Xi[,2])
	}
		
		nobs =  (info[,2]-info[,1]) :+ 1
		result = nobs, mean, var	
		return(result)  		
}	
mata mosave rdrobust_collapse(), replace 
end
