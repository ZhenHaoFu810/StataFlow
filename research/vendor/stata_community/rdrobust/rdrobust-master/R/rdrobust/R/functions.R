qrXXinv = function(x, ...) {
  #tcrossprod(solve(qr.R(qr(x, tol = 1e-10)), tol = 1e-10))
  #tcrossprod(solve(qr.R(qr(x))))
  chol2inv(chol(crossprod(x))) 
}

qrreg = function(x,y,w,s2=0,var.comp=TRUE, ...) {
  M.X = sqrt(w)*x
  X.M.X_inv = qrXXinv(M.X) 
  X.M.Y = crossprod(M.X,sqrt(w)*y)
  beta.hat = X.M.X_inv%*%X.M.Y
  Psi.hat=Sigma.hat=0
  if (var.comp==TRUE) {
    Psi.hat = crossprod((w*s2*w)*x,x)
    Sigma.hat = crossprod(Psi.hat%*%X.M.X_inv,X.M.X_inv)
  }
  output = list(X.M.X_inv=X.M.X_inv, X.M.Y=X.M.Y, beta.hat=beta.hat, Psi.hat=Psi.hat, Sigma.hat=Sigma.hat)
  return(output)
}

rdrobust_kweight = function(X, c,  h,  kernel){
  u = (X-c)/h
  if (kernel=="epanechnikov" | kernel=="epa") {
    w = (0.75*(1-u^2)*(abs(u)<=1))/h
  }
  else if (kernel=="uniform" | kernel=="uni") {
    w = (0.5*(abs(u)<=1))/h
  }
  else {
    w = ((1-abs(u))*(abs(u)<=1))/h
  }
  return(w)	
}

rdrobust_res = function(X, y, T, Z, m, hii, vce, matches, dups, dupsid, d) {
  n = length(y)
  dT=dZ=0
  if (!is.null(T)) dT = 1
  if (!is.null(Z)) dZ = ncol(Z)
  res = matrix(NA,n,1+dT+dZ)  	
  
  if (vce=="nn") {
    for (pos in 1:n) {
      rpos = dups[pos] - dupsid[pos]
      lpos = dupsid[pos] - 1
      while (lpos+rpos < min(c(matches,n-1))) {
        if (pos-lpos-1 <= 0) rpos = rpos + dups[pos+rpos+1]
        else if (pos+rpos+1>n) lpos = lpos + dups[pos-lpos-1]
        else if ((X[pos]-X[pos-lpos-1]) > (X[pos+rpos+1]-X[pos])) rpos = rpos + dups[pos+rpos+1]
        else if ((X[pos]-X[pos-lpos-1]) < (X[pos+rpos+1]-X[pos])) lpos = lpos + dups[pos-lpos-1]
        else {
          rpos = rpos + dups[pos+rpos+1]
          lpos = lpos + dups[pos-lpos-1]
        }
      }
      ind_J = max(c(0,(pos-lpos))):min(c(n,(pos+rpos)))
      y_J   = sum(y[ind_J])-y[pos]
      Ji = length(ind_J)-1
      res[pos,1] = sqrt(Ji/(Ji+1))*(y[pos] - y_J/Ji)
      if (!is.null(T)) {
        T_J = sum(T[ind_J])-T[pos]
        res[pos,2] = sqrt(Ji/(Ji+1))*(T[pos] - T_J/Ji)
      }
      if (!is.null(Z)) {
        for (i in 1:dZ) {
          Z_J = sum(Z[ind_J,i])-Z[pos,i]
          res[pos,1+dT+i] = sqrt(Ji/(Ji+1))*(Z[pos,i] - Z_J/Ji)
        }
      }
    }		
  }
  else {
    if (vce=="hc0") w = 1
    else if (vce=="hc1") w = sqrt(n/(n-d))
    else if (vce=="hc2") w = sqrt(1/(1-hii))
    else                 w =      1/(1-hii)
    res[,1] = w*(y-m[,1])
    if (dT==1) res[,2] = w*(T-m[,2])
    if (dZ>0) {
      for (i in 1:dZ) {
        res[,1+dT+i] = w*(Z[,i]-m[,1+dT+i])
      }
    }
  }
  return(res)
}


rdrobust_bw = function(Y, X, T, Z, C, W, c, o, nu, o_B, h_V, h_B, scale, vce, nnmatch, kernel, dups, dupsid, covs_drop_coll, ginv.tol){
  dT = dZ = dC = 0
  w = rdrobust_kweight(X, c, h_V, kernel)
  dW = length(W)
  if (dW>1) {
    w = W*w
  }
  
  ind_V = w> 0; eY = Y[ind_V];eX = X[ind_V];eW = w[ind_V]
  n_V = sum(ind_V)
  D_V = eY
  R_V = matrix(NA,n_V,o+1)
  for (j in 1:(o+1)) R_V[,j] = (eX-c)^(j-1)
  invG_V = qrXXinv(R_V*sqrt(eW))
  e_v = matrix(0,(o+1),1); e_v[nu+1]=1
  s = 1
  eT=eC=eZ=NULL
  if (!is.null(T)) {
    dT = 1
    eT = T[ind_V]
    D_V = cbind(D_V,eT)
  }
  if (!is.null(Z)) {
    dZ = ncol(Z)
    eZ = Z[ind_V,,drop=FALSE]
    D_V = cbind(D_V,eZ)
    U = crossprod(R_V*eW,D_V)
    ZWD  = crossprod(eZ*eW,D_V)
    colsZ = (2+dT):max(c(2+dT+dZ-1,(2+dT)))
    UiGU =  crossprod(matrix(U[,colsZ],nrow=o+1),invG_V%*%U) 
    ZWZ = ZWD[,colsZ] - UiGU[,colsZ] 
    ZWY = ZWD[,1:(1+dT)] - UiGU[,1:(1+dT)] 
    #if (covs_drop_coll==0) gamma = chol2inv(chol(ZWZ))%*%ZWY
    if (covs_drop_coll==1) {
      gamma = ginv(ZWZ, tol=ginv.tol)%*%ZWY
      }
    else {
      gamma = chol2inv(chol(ZWZ))%*%ZWY
    }
    s = c(1 , -gamma[,1])
  }
  if (!is.null(C)) {
    dC = 1
    eC =  C[ind_V] 
  }
  beta_V = invG_V%*%crossprod(R_V*eW,D_V)	
  if (is.null(Z) & !is.null(T)) {	
    tau_Y = c(factorial(nu)*beta_V[nu+1,1])
    tau_T = c(factorial(nu)*beta_V[nu+1,2])
    s = c(1/tau_T , -(tau_Y/tau_T^2))
  }
  if (!is.null(Z) & !is.null(T)) {	
    s_T = c(1 , -gamma[,2])
    tau_Y = c(factorial(nu)*t(s)%*%  c(beta_V[nu+1,1],beta_V[nu+1,colsZ]))
    tau_T = c(factorial(nu)*t(s_T)%*%c(beta_V[nu+1,2],beta_V[nu+1,colsZ]))
    s = c(1/tau_T , -(tau_Y/tau_T^2) , -(1/tau_T)*gamma[,1] + (tau_Y/tau_T^2)*gamma[,2])
  }	
  dups_V=dupsid_V=predicts_V=0
  
  if (vce=="nn") {
    dups_V   = dups[ind_V]
    dupsid_V = dupsid[ind_V]
  }
  
  if (vce=="hc0" | vce=="hc1" | vce=="hc2" | vce=="hc3") {
    predicts_V=R_V%*%beta_V
    if (vce=="hc2" | vce=="hc3") {
      hii = rowSums((R_V%*%invG_V)*(R_V*eW))
    }
  }	
        res_V = rdrobust_res(eX, eY, eT, eZ, predicts_V, hii, vce, nnmatch, dups_V, dupsid_V, o+1)
        aux = rdrobust_vce(dT+dZ, s, R_V*eW, res_V, eC)
        aux2 = R_V*eW
        V_V = (invG_V%*%aux%*%invG_V)[nu+1,nu+1]
        v = crossprod(R_V*eW,((eX-c)/h_V)^(o+1))
        Hp = 0
        for (j in 1:(o+1)) Hp[j] = h_V^((j-1))
        BConst = (Hp*(invG_V%*%v))[nu+1]
        
        w = rdrobust_kweight(X, c, h_B, kernel)
        if (dW>1) {
          w = W*w
        }
        ind = w> 0 
        n_B = sum(ind)
        eY = Y[ind];eX = X[ind];eW = w[ind]
        D_B = eY
        R_B = matrix(NA,n_B,o_B+1)
        for (j in 1:(o_B+1)) R_B[,j] = (eX-c)^(j-1)
        invG_B = qrXXinv(R_B*sqrt(eW))
        eT=eC=eZ=NULL
        if (!is.null(T)) {
          eT = T[ind]
          D_B = cbind(D_B,eT)
        }
        if (!is.null(Z)) {
          eZ = Z[ind,,drop=FALSE]
          D_B = cbind(D_B,eZ)
        }
        if (!is.null(C)) {
          eC=C[ind]
        }	
        beta_B = invG_B%*%crossprod(R_B*eW,D_B)	
        BWreg=0
        if (scale>0) {
        e_B = matrix(0,(o_B+1),1); e_B[o+2]=1
        dups_B=dupsid_B=hii=predicts_B=0
        if (vce=="nn") {
        dups_B   = dups[ind]
        dupsid_B = dupsid[ind]
        }
        if (vce=="hc0" | vce=="hc1" | vce=="hc2" | vce=="hc3") {
          predicts_B=R_B%*%beta_B
          if (vce=="hc2" | vce=="hc3") {
            hii = rowSums((R_B%*%invG_B)*(R_B*eW))
  		  	}
		    }	
		res_B = rdrobust_res(eX, eY, eT, eZ, predicts_B, hii, vce, nnmatch, dups_B, dupsid_B,o_B+1)
		V_B = (invG_B%*%rdrobust_vce(dT+dZ, s, R_B*eW, res_B, eC)%*%invG_B)[o+2,o+2]
		BWreg = 3*BConst^2*V_B
	}
	B =  sqrt(2*(o+1-nu))*BConst%*%(t(s)%*%(beta_B[o+2,]))
	V = (2*nu+1)*h_V^(2*nu+1)*V_V
	R = scale*(2*(o+1-nu))*BWreg
	rate = 1/(2*o+3)
  output = list(V=V,B=B,R=R,rate=rate)
  return(output)
}

rdrobust_vce = function(d, s, RX, res, C) {	
  k = ncol(as.matrix(RX))
  M = matrix(0,k,k)
  n  = length(C)
  if (is.null(C)) {
    w = 1
    if (d==0){
      M  = crossprod(c(res)*RX)
    }
    else {
      for (i in 1:(1+d)) {
        SS = res[,i]*res
        for (j in 1:(1+d)) {
            M = M + crossprod(RX*(s[i]*s[j])*SS[,j],RX)
        }
      }
    }
  }
  else {	
    clusters = unique(C)
    g     = length(clusters)
    w=((n-1)/(n-k))*(g/(g-1))
    if (d==0){
      for (i in 1:g) {
        ind=C==clusters[i]
        Xi = RX[ind,,drop=FALSE]
        ri = res[ind,,drop=FALSE]
        Xr = t(crossprod(Xi,ri))
        M = M + crossprod(Xr,Xr)
      }
    }
    else {
      for (i in 1:g) {
        ind=C==clusters[i]
        Xi = RX[ind,,drop=FALSE]
        ri = res[ind,,drop=FALSE]
        MHolder = matrix(0,1+d,k)
        for (l in 1:(1+d)) {
          MHolder[l,] = t(crossprod(Xi,s[l]*ri[,l]))
        }	
        summedvalues = t(colSums(MHolder))
        aux = crossprod(summedvalues,summedvalues)
        M = M + crossprod(summedvalues,summedvalues)
      }
    }
  }
  return(w*M)		
}

J.fun = function(B,V,n) {ceiling((((2*B)/V)*n)^(1/3))}





bwconst = function(p,v,kernel){
  if (kernel=="epanechnikov" | kernel=="epa" | kernel==3) {
    K.fun = function(u) {(0.75*(1-u^2)*(abs(u)<=1))}
  }
  else if (kernel=="uniform" | kernel=="uni" | kernel==2) {
    K.fun = function(u) {(0.5*(abs(u)<=1))}
  }
  else  {
    K.fun = function(u) {((1-abs(u))*(abs(u)<=1))}
  }
  p1 = p+1  
  Gamma_p = Phi_p = matrix(NA,p1,p1)
  Omega_pq = matrix(NA,p1,1)
  for (i in 1:p1) {
    Omega.fun = function(u) {K.fun(u)*(u^(p1))*(u^(i-1))}
    Omega_pq[i] = integrate(Omega.fun,lower=0,upper=1)$value
    for (j in 1:p1) {
      Gamma.fun = function(u) {K.fun(u)*(u^(i-1))*(u^(j-1))}
      Phi.fun   = function(u) {(K.fun(u)^2)*(u^(i-1))*(u^(j-1))}
      Gamma_p[i,j] = integrate(Gamma.fun,lower=0,upper=1)$value
      Phi_p[i,j] = integrate(Phi.fun,lower=0,upper=1)$value
    }
  }
  B_const = solve(Gamma_p)%*%Omega_pq
  V_const = solve(Gamma_p)%*%Phi_p%*%solve(Gamma_p)
  C1 = B_const[v+1,1]
  C2 = V_const[v+1,v+1]
  return(c(C1,C2))
}

rdvce= function(X,y,frd=NULL,p,h,matches,vce,kernel){
  m = matches+1
  n = length(X)
  p1 = p+1
  sigma = matrix(0,n,1)
  if (vce=="resid") {
    for (k in 1:n) {
      cutoff = matrix(X[k],n,1)
      cutoff1 = X[k]
      W = rdrobust_kweight(X,cutoff1,h,"kernel")
      ind=W>0
      if (sum(ind)>5) {
        w.p=W[ind]; X.p=X[ind]; y.p=y[ind]
        XX.p = matrix(c((X.p-cutoff1)^0, poly(X.p-cutoff1,degree=p,raw=T)),length(X.p),p+1)
        mu0_phat_y = qr.coef(qr(XX.p*sqrt(w.p), tol = 1e-10), sqrt(w.p)*y.p)[1]
        if (is.null(frd)) {
          sigma[k] = (y[k] - mu0_phat_y)^2
        }
        else if (!is.null(frd)) {
          z.p=frd[ind]
          out=qrreg(XX.p, z.p, w.p, var.comp=FALSE) 
          mu0_phat_z = out$beta.hat[1]
          sigma[k] = (y[k] - mu0_phat_y)*(frd[k] - mu0_phat_z)
        }
      }
    }
  }
  else  {
    #y_match_avg = z_match_avg = matrix(NA,n,1)
    for (k in 1:n) {
      diffx = abs(X - X[k])
      m.group = sort(unique(diffx))[2:m]
      ind = which(diffx %in% m.group)
      y_match_avg = z_match_avg = mean(y[ind])
      Ji = length(ind)
      if (is.null(frd)) {
        sigma[k] = (Ji/(Ji+1))*(y[k] - y_match_avg)^2
      } 
      else if (!is.null(frd)) {
        z_match_avg = mean(frd[ind])
        sigma[k] = (Ji/(Ji+1))*(y[k] - y_match_avg)*(frd[k] - z_match_avg)
      }
    }
  }
  return(sigma)
}

regconst = function(d,h){
  d2 = 2*d+1
  d1 = d+1
  mu = matrix(0,d2, 1)
  mu[1] = 1
  XX = matrix(0,d1,d1)
  for (j in 2:d2) {
    i = j-1
    if (j%%2==1) {
      mu[j] = (1/(i+1))*(h/2)^i
    }
  }
  for (j in 1:d1) {
    XX[j,] = t(mu[j:(j+d)])
  }
  invXX =solve(XX)
  return(invXX)
}

covs_drop_fun <- function(z) {
  z          <- as.matrix(z)
  ncovs      <- ncol(z)
  df         <- data.frame(z = z)
  constant   <- rep(1,nrow(df))
  tmp        <- lm(constant ~ ., data=df)
  to_keep    <- tmp$coefficients[!is.na(tmp$coefficients)]
  ncovs_keep <- length(to_keep)
  to_keep    <- names(to_keep[2:ncovs_keep])
  ncovs_keep <- ncovs_keep-1
  covs <- as.matrix(df[to_keep])
  #qr.X <- qr(x,  LAPACK = FALSE, tol = 1e-2) 
  #(rnkX <- qr.X$rank)
  #(keep <- qr.X$pivot[seq_len(rnkX)])
  #xx <- as.matrix(x[,keep])
  #output = list(xx=xx,rank_covs=rnkX)
  output = list(covs=covs, ncovs=ncovs_keep)
  return(output)
}
