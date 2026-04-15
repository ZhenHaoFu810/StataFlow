rdbwselect = function(y, x, c = NULL, fuzzy = NULL, deriv = NULL, p = NULL, q = NULL, 
                      covs = NULL,  covs_drop = TRUE, ginv.tol = 1e-20,
                      kernel = "tri", weights = NULL, bwselect = "mserd", 
                      vce = "nn", cluster = NULL, 
                      nnmatch = 3,  scaleregul = 1, sharpbw = FALSE,  
                      all = NULL, subset = NULL, masspoints = "adjust",
                      bwcheck = NULL, bwrestrict = TRUE, stdvars = FALSE){
  
  if (!is.null(subset)) { 
    x <- x[subset]
    y <- y[subset]
  }
  
  if (is.null(all)) all<-FALSE
  if (is.null(c)) c <- 0
    
  # p
  if (is.null(p) & !is.null(deriv)) {p = deriv+1}
  if (length(p) == 0) {
    flag_no_p <- TRUE
    p <- 1
  } else if ((length(p) != 1) | !(p[1]%in%0:20)) {
    stop("Polynomial order p incorrectly specified.\n")
  } else {
    flag_no_p <- FALSE
  }
  
  # q
  if (length(q) == 0) {
    flag_no_q <- TRUE
    q <- p + 1
  } else if ((length(q) > 1) | !(q[1]%in%c(0:20)) | (q[1]<p)) {
    stop("Polynomial order (for bias correction) q incorrectly specified.\n")
  } else {
    flag_no_q <- FALSE
  }
  
  # deriv
  if (length(deriv) == 0) {
    flag_no_deriv <- TRUE
    deriv <- 0
  } else if ((length(deriv) > 1) | !(deriv[1]%in%c(0:20)) | (deriv[1]>p)) {
    stop("Derivative order incorrectly specified.\n")
  } else {
    flag_no_deriv <- FALSE
  }
  
  na.ok <- complete.cases(x) & complete.cases(y)
  
  if (!is.null(cluster)){
    if (!is.null(subset))  cluster <- cluster[subset]
    na.ok <- na.ok & complete.cases(cluster)
  } 
  
  if (!is.null(covs)){
    #if (!is.null(subset))  covs <- subset(covs,subset)
    if (!is.null(subset)) covs <- covs[subset, ,drop=FALSE]
    na.ok <- na.ok & complete.cases(covs)
  } 
  
  if (!is.null(fuzzy)){
    if (!is.null(subset)) fuzzy <- fuzzy[subset]
    na.ok <- na.ok & complete.cases(fuzzy)
  } 
  
  if (!is.null(weights)){
    if (!is.null(subset)) weights <- weights[subset]
    na.ok <- na.ok & complete.cases(weights) & weights>=0
  } 
  
  x = as.matrix(x[na.ok])
  y = as.matrix(y[na.ok])
  if (!is.null(covs))    covs    = as.matrix(covs)[na.ok, , drop = FALSE]
  if (!is.null(fuzzy))   fuzzy   = as.matrix(fuzzy[na.ok])
  if (!is.null(cluster)) cluster = as.matrix(cluster[na.ok])
  if (!is.null(weights)) weights = as.matrix(weights[na.ok])
  
  if (is.null(masspoints)) masspoints=FALSE
  
  if (vce=="nn" | masspoints=="check" | masspoints=="adjust") {
    order_x = order(x)
    x = x[order_x,,drop=FALSE]
    y = y[order_x,,drop=FALSE]
    if (!is.null(covs))    covs    =  as.matrix(covs)[order_x,,drop=FALSE]
    if (!is.null(fuzzy))   fuzzy   =   fuzzy[order_x,,drop=FALSE]
    if (!is.null(cluster)) cluster = cluster[order_x,,drop=FALSE]
    if (!is.null(weights)) weights = weights[order_x,,drop=FALSE]
  }
  
  ### reescaling
  x_iq = quantile(x,.75,type=2) - quantile(x,.25,type=2)
  BWp = min(c(sd(x),x_iq/1.349))
  
  x_sd = y_sd = 1
  c_orig = c
  if (isTRUE(stdvars)) { 
    y_sd = sd(y)
    x_sd = sd(x)
    y = y/y_sd
	  x = x/x_sd
	  c = c/x_sd
	  BWp = min(c(1,(x_iq/x_sd)/1.349))
  }
  ###############################################
  ind_l = x<c; ind_r = x>=c
  X_l = x[ind_l];   X_r = x[ind_r]
  x_l_min = min(X_l);  x_l_max = max(X_l)
  x_r_min = min(X_r);  x_r_max = max(X_r)
  range_l = abs(c-x_l_min);  range_r = abs(c-x_r_max)

  Y_l = y[ind_l];    Y_r = y[ind_r]
  N_l = length(X_l);   N_r = length(X_r)
  x_min=min(x);  x_max=max(x)
  N = N_r + N_l

  M_l = N_l;  M_r = N_r
    
  if (masspoints=="check" | masspoints=="adjust") {
    X_uniq_l = sort(unique(X_l), decreasing=TRUE)
    X_uniq_r = unique(X_r)
    M_l = length(X_uniq_l)
    M_r = length(X_uniq_r)
    M = M_l + M_r
    mass_l = 1-M_l/N_l
    mass_r = 1-M_r/N_r				
    if (mass_l>=0.2 | mass_r>=0.2){
      #warning("Mass points detected in the running variable.")
      if (masspoints=="check") warning("Try using option masspoints=adjust.")
      if (is.null(bwcheck) & masspoints=="adjust") bwcheck <- 10
    }				
  }
  


  ############## COLLINEARITY
  covs_drop_coll=dZ=0
  if (!is.null(covs)) dZ = ncol(covs)
  if (covs_drop == TRUE) covs_drop_coll = 1 
  
  if (!is.null(covs) & isTRUE(covs_drop)) {
    covs.names = colnames(covs)
    if (is.null(covs.names)) {
      covs.names = paste("z",1:ncol(covs),sep="")
      colnames(covs) = covs.names
    }
    covs = covs[,order(nchar(covs.names))]
    covs = as.matrix(covs)
    dZ = length(covs.names)
    covs.check = covs_drop_fun(covs)
    if (covs.check$ncovs < dZ) {
      covs  <- as.matrix(covs.check$covs)
      dZ    <- covs.check$ncovs
      warning("Multicollinearity issue detected in covs. Redundant covariates dropped.")  
    }
  }
  
    exit=0
    #################  ERRORS
    if (kernel!="uni" & kernel!="uniform" & kernel!="tri" & kernel!="triangular" & kernel!="epa" & kernel!="epanechnikov" & kernel!="" ){
      warning("kernel incorrectly specified")
      exit = 1
    }
    
    if  (bwselect!="mserd" & bwselect!="msetwo" & bwselect!="msesum" & bwselect!="msecomb1" & bwselect!="msecomb2"  & bwselect!="cerrd" & bwselect!="certwo" & bwselect!="cersum" & bwselect!="cercomb1" & bwselect!="cercomb2" & bwselect!=""){
      warning("bwselect incorrectly specified")  
      exit = 1
    }
    
    if (bwselect=="CCT" | bwselect=="IK" | bwselect=="CV" | bwselect=="cct" | bwselect=="ik" | bwselect=="cv"){
      warning("bwselect options IK, CCT and CV have been depricated. Please see help for new options")  
      exit = 1
    }
    
    if (vce!="nn" & vce!="" & vce!="hc1" & vce!="hc2" & vce!="hc3" & vce!="hc0"){ 
      warning("vce incorrectly specified")
      exit = 1
    }

    if (c<=x_min | c>=x_max){
      warning("c should be set within the range of x")
      exit = 1
    }
    
    if (p<0 | q<0 | deriv<0 | nnmatch<=0 ){
      warning("p, q, deriv and matches should be positive integers")
      exit = 1
    }
    
    if (p>=q){
      warning("q should be set higher than p")
      exit = 1
    }
    
    if (deriv>p){
      warning("deriv can only be equal or lower p")
      exit = 1
    }
    
    p_round = round(p)/p;    q_round = round(q)/q;    d_round = round(deriv+1)/(deriv+1);    m_round = round(nnmatch)/nnmatch
        
    if ((p_round!=1 &p>0) | (q_round!=1&q>0) | d_round!=1 | m_round!=1 ){
      warning("p,q,deriv and matches should be integer numbers")
      exit = 1
    }
    
    if (N<20){
      warning("Not enough observations to perform bandwidth calculations")
      exit = 1
    }
    
    
    if (exit>0) stop()
    
  
  
  
  if (kernel=="epanechnikov" | kernel=="epa") {
    kernel_type = "Epanechnikov"
    C_c=2.34
  }  else if (kernel=="uniform" | kernel=="uni") {
    kernel_type = "Uniform"
    C_c=1.843
  }   else  {
    kernel_type = "Triangular"
    C_c=2.576
  }
  
    vce_type = "NN"
    if (vce=="hc0")     		vce_type = "HC0"
    if (vce=="hc1")      	  vce_type = "HC1"
    if (vce=="hc2")      	  vce_type = "HC2"
    if (vce=="hc3")      	  vce_type = "HC3"
    if (vce=="cluster")  	  vce_type = "Cluster"
    if (vce=="nncluster") 	vce_type = "NNcluster"
    
  #***********************************************************************
  Z_l=Z_r=T_l=T_r=C_l=C_r=NULL
  g_l=g_r=0
  
  if (vce=="nn") {
    nn_l = rep(1,N_l);  nn_r = rep(1,N_r)
    dups_l   = ave(nn_l, X_l, FUN = sum); dupsid_l = ave(nn_l, X_l, FUN = cumsum)
    dups_r   = ave(nn_r, X_r, FUN = sum); dupsid_r = ave(nn_r, X_r, FUN = cumsum)
  } 
  
  if (!is.null(covs)) {
    Z_l  = covs[ind_l,,drop=FALSE];  Z_r  = covs[ind_r,,drop=FALSE]
  }
  
  perf_comp=FALSE
  if (!is.null(fuzzy)) {
    T_l  = fuzzy[ind_l,,drop=FALSE];  T_r  = fuzzy[ind_r,,drop=FALSE]; 
    if (var(T_l)==0 | var(T_r)==0) perf_comp=TRUE
    if (perf_comp==TRUE | sharpbw==TRUE) {
      T_l = T_r = NULL
      }
    }
   
  if (!is.null(cluster)) {
    C_l  = cluster[ind_l,,drop=FALSE]; C_r= cluster[ind_r,,drop=FALSE]
    g_l = length(unique(C_l));	g_r = length(unique(C_r))
  }
  
  fw_l = fw_r = 0 
  if (!is.null(weights)) {
    fw_l=weights[ind_l];  fw_r=weights[ind_r]
  }                                                                           

  
  ######################################################################
    c_bw = C_c*BWp*N^(-1/5)
    if (masspoints=="adjust") c_bw = C_c*BWp*M^(-1/5)
    
    if (isTRUE(bwrestrict)) {
      bw_max_l = abs(c-x_min)
      bw_max_r = abs(c-x_max)
      bw_max = max(bw_max_l, bw_max_r)
      c_bw <- min(c_bw, bw_max)
    }
    
    bw.adj <- 0
    if (!is.null(bwcheck)) {
      bwcheck_l = min(bwcheck, M_l)
			bwcheck_r = min(bwcheck, M_r)
      bw_min_l = abs(X_uniq_l-c)[bwcheck_l] + 1e-8
      bw_min_r = abs(X_uniq_r-c)[bwcheck_r] + 1e-8
      c_bw = max(c_bw, bw_min_l, bw_min_r)
      bw.adj <- 1
    }
    
    
    ### Step 1: d_bw
    C_d_l = rdrobust_bw(Y_l, X_l, T_l, Z_l, C_l, fw_l, c=c, o=q+1, nu=q+1, o_B=q+2, h_V=c_bw, h_B=range_l, 0, vce, nnmatch, kernel, dups_l, dupsid_l, covs_drop_coll, ginv.tol)
    C_d_r = rdrobust_bw(Y_r, X_r, T_r, Z_r, C_r, fw_r, c=c, o=q+1, nu=q+1, o_B=q+2, h_V=c_bw, h_B=range_r, 0, vce, nnmatch, kernel, dups_r, dupsid_r, covs_drop_coll, ginv.tol)
    ### TWO
    if  (bwselect=="msetwo" |  bwselect=="certwo" | bwselect=="msecomb2" | bwselect=="cercomb2"  | all=="TRUE")  {		
      d_bw_l = c((  C_d_l$V              /   C_d_l$B^2             )^C_d_l$rate)
      d_bw_r = c((  C_d_r$V              /   C_d_r$B^2             )^C_d_l$rate)
      if (isTRUE(bwrestrict)) {
        d_bw_l <- min(d_bw_l, bw_max_l)
        d_bw_r <- min(d_bw_r, bw_max_r)
      }
      
      if (!is.null(bwcheck)) {
        d_bw_l  <- max(d_bw_l, bw_min_l)
        d_bw_r  <- max(d_bw_r, bw_min_r)
      }
      C_b_l  = rdrobust_bw(Y_l, X_l, T_l, Z_l, C_l, fw_l, c=c, o=q, nu=p+1, o_B=q+1, h_V=c_bw, h_B=d_bw_l, scaleregul, vce, nnmatch, kernel, dups_l, dupsid_l, covs_drop_coll, ginv.tol)
      b_bw_l = c((  C_b_l$V              /   (C_b_l$B^2 + scaleregul*C_b_l$R)        )^C_b_l$rate)
      C_b_r  = rdrobust_bw(Y_r, X_r, T_r, Z_r, C_r, fw_r, c=c, o=q, nu=p+1, o_B=q+1, h_V=c_bw, h_B=d_bw_r, scaleregul, vce, nnmatch, kernel, dups_r, dupsid_r, covs_drop_coll, ginv.tol)
      b_bw_r = c((  C_b_r$V              /   (C_b_r$B^2 + scaleregul*C_b_r$R)        )^C_b_l$rate)
      if (isTRUE(bwrestrict)) {
        b_bw_l <- min(b_bw_l, bw_max_l)
        b_bw_r <- min(b_bw_r, bw_max_r)
      }
      
      C_h_l  = rdrobust_bw(Y_l, X_l, T_l, Z_l, C_l, fw_l, c=c, o=p, nu=deriv, o_B=q, h_V=c_bw, h_B=b_bw_l, scaleregul, vce, nnmatch, kernel, dups_l, dupsid_l, covs_drop_coll, ginv.tol)
      h_bw_l = c((  C_h_l$V              /   (C_h_l$B^2 + scaleregul*C_h_l$R)         )^C_h_l$rate)
      C_h_r  = rdrobust_bw(Y_r, X_r, T_r, Z_r, C_r, fw_r, c=c, o=p, nu=deriv, o_B=q, h_V=c_bw, h_B=b_bw_r, scaleregul, vce, nnmatch, kernel, dups_r, dupsid_r, covs_drop_coll, ginv.tol)
      h_bw_r = c((  C_h_r$V              /   (C_h_r$B^2 + scaleregul*C_h_r$R)         )^C_h_l$rate)
      if (isTRUE(bwrestrict)) {
        h_bw_l <- min(h_bw_l, bw_max_l)
        h_bw_r <- min(h_bw_r, bw_max_r) 
      }
      
    }
  
  ### SUM
  if  (bwselect=="msesum" | bwselect=="cersum" |  bwselect=="msecomb1" | bwselect=="msecomb2" |  bwselect=="cercomb1" | bwselect=="cercomb2"  |  all=="TRUE")  {
    d_bw_s = c(( (C_d_l$V + C_d_r$V)  /  (C_d_r$B + C_d_l$B)^2 )^C_d_l$rate)
    if (isTRUE(bwrestrict)) {
    d_bw_s <- min(d_bw_s, bw_max)
    }
    
    if (!is.null(bwcheck)) d_bw_s  <-  max(d_bw_s, bw_min_l, bw_min_r)
    C_b_l  = rdrobust_bw(Y_l, X_l, T_l, Z_l, C_l, fw_l, c=c, o=q, nu=p+1, o_B=q+1, h_V=c_bw, h_B=d_bw_s, scaleregul, vce, nnmatch, kernel, dups_l, dupsid_l, covs_drop_coll, ginv.tol)
    C_b_r  = rdrobust_bw(Y_r, X_r, T_r, Z_r, C_r, fw_r, c=c, o=q, nu=p+1, o_B=q+1, h_V=c_bw, h_B=d_bw_s, scaleregul, vce, nnmatch, kernel, dups_r, dupsid_r, covs_drop_coll, ginv.tol)
    b_bw_s = c(( (C_b_l$V + C_b_r$V)  /  ((C_b_r$B + C_b_l$B)^2 + scaleregul*(C_b_r$R+C_b_l$R)) )^C_b_l$rate)
    if (isTRUE(bwrestrict)) {
    b_bw_s <- min(b_bw_s, bw_max)
    }
    C_h_l  = rdrobust_bw(Y_l, X_l, T_l, Z_l, C_l, fw_l, c=c, o=p, nu=deriv, o_B=q, h_V=c_bw, h_B=b_bw_s, scaleregul, vce, nnmatch, kernel, dups_l, dupsid_l, covs_drop_coll, ginv.tol)
    C_h_r  = rdrobust_bw(Y_r, X_r, T_r, Z_r, C_r, fw_r, c=c, o=p, nu=deriv, o_B=q, h_V=c_bw, h_B=b_bw_s, scaleregul, vce, nnmatch, kernel, dups_r, dupsid_r, covs_drop_coll, ginv.tol)
    h_bw_s = c(( (C_h_l$V + C_h_r$V)  /  ((C_h_r$B + C_h_l$B)^2 + scaleregul*(C_h_r$R + C_h_l$R)) )^C_h_l$rate)
    if (isTRUE(bwrestrict)) {
    h_bw_s <- min(h_bw_s, bw_max)
    }
}

    ### RD
if  (bwselect=="mserd" | bwselect=="cerrd" | bwselect=="msecomb1" | bwselect=="msecomb2" | bwselect=="cercomb1" | bwselect=="cercomb2" | bwselect=="" | all=="TRUE" ) {
  d_bw_d = c(( (C_d_l$V + C_d_r$V)  /  (C_d_r$B - C_d_l$B)^2 )^C_d_l$rate)
  if (isTRUE(bwrestrict)) {
    d_bw_d <- min(d_bw_d, bw_max)
  }
  if (!is.null(bwcheck)) d_bw_d  <- max(d_bw_d, bw_min_l, bw_min_r)
  C_b_l  = rdrobust_bw(Y_l, X_l, T_l, Z_l, C_l, fw_l, c=c, o=q, nu=p+1, o_B=q+1, h_V=c_bw, h_B=d_bw_d, scaleregul, vce, nnmatch, kernel, dups_l, dupsid_l, covs_drop_coll, ginv.tol)
  C_b_r  = rdrobust_bw(Y_r, X_r, T_r, Z_r, C_r, fw_r, c=c, o=q, nu=p+1, o_B=q+1, h_V=c_bw, h_B=d_bw_d, scaleregul, vce, nnmatch, kernel, dups_r, dupsid_r, covs_drop_coll, ginv.tol)
  b_bw_d = c(( (C_b_l$V + C_b_r$V)  /  ((C_b_r$B - C_b_l$B)^2 + scaleregul*(C_b_r$R + C_b_l$R)) )^C_b_l$rate)
  if (isTRUE(bwrestrict)) {
    b_bw_d <- min(b_bw_d, bw_max)
  }
  C_h_l  = rdrobust_bw(Y_l, X_l, T_l, Z_l, C_l, fw_l, c=c, o=p, nu=deriv, o_B=q, h_V=c_bw, h_B=b_bw_d, scaleregul, vce, nnmatch, kernel, dups_l, dupsid_l, covs_drop_coll, ginv.tol)
  C_h_r  = rdrobust_bw(Y_r, X_r, T_r, Z_r, C_r, fw_r, c=c, o=p, nu=deriv, o_B=q, h_V=c_bw, h_B=b_bw_d, scaleregul, vce, nnmatch, kernel, dups_r, dupsid_r, covs_drop_coll, ginv.tol)
  h_bw_d = c(( (C_h_l$V + C_h_r$V)  /  ((C_h_r$B - C_h_l$B)^2 + scaleregul*(C_h_r$R + C_h_l$R)) )^C_h_l$rate)
  if (isTRUE(bwrestrict)) {
  h_bw_d <- min(h_bw_d, bw_max)
  }
}	

if  (bwselect=="mserd" | bwselect=="cerrd" | bwselect=="msecomb1" | bwselect=="msecomb2" | bwselect=="cercomb1" | bwselect=="cercomb2" | bwselect=="" | all=="TRUE" ) {
  h_mserd = x_sd*h_bw_d
  b_mserd = x_sd*b_bw_d
}	
if  (bwselect=="msesum" | bwselect=="cersum" |  bwselect=="msecomb1" | bwselect=="msecomb2" |  bwselect=="cercomb1" | bwselect=="cercomb2"  |  all=="TRUE")  {
  h_msesum = x_sd*h_bw_s
  b_msesum = x_sd*b_bw_s
}
if  (bwselect=="msetwo" |  bwselect=="certwo" | bwselect=="msecomb2" | bwselect=="cercomb2"  | all=="TRUE")  {		
  h_msetwo_l = x_sd*h_bw_l
  h_msetwo_r = x_sd*h_bw_r
  b_msetwo_l = x_sd*b_bw_l
  b_msetwo_r = x_sd*b_bw_r
}
if  (bwselect=="msecomb1" | bwselect=="cercomb1" | all=="TRUE" ) {
  h_msecomb1 = min(c(h_mserd,h_msesum))
  b_msecomb1 = min(c(b_mserd,b_msesum))
}
if  (bwselect=="msecomb2" | bwselect=="cercomb2" |  all=="TRUE" ) {
  h_msecomb2_l = median(c(h_mserd,h_msesum,h_msetwo_l))
  h_msecomb2_r = median(c(h_mserd,h_msesum,h_msetwo_r))
  b_msecomb2_l = median(c(b_mserd,b_msesum,b_msetwo_l))
  b_msecomb2_r = median(c(b_mserd,b_msesum,b_msetwo_r))
}
cer_h = N^(-(p/((3+p)*(3+2*p))))

if (!is.null(cluster)) {
  cer_h = (g_l+g_r)^(-(p/((3+p)*(3+2*p))))
}

#cer_b = N^(-(q/((3+q)*(3+2*q))))
cer_b = 1
	if  (bwselect=="cerrd" | all=="TRUE" ){
		h_cerrd = h_mserd*cer_h
		b_cerrd = b_mserd*cer_b
	}
	if  (bwselect=="cersum" | all=="TRUE" ){
		h_cersum = h_msesum*cer_h
		b_cersum=  b_msesum*cer_b
		}
	if  (bwselect=="certwo" | all=="TRUE" ){
		h_certwo_l   = h_msetwo_l*cer_h
		h_certwo_r   = h_msetwo_r*cer_h
		b_certwo_l   = b_msetwo_l*cer_b
		b_certwo_r   = b_msetwo_r*cer_b
		}
	if  (bwselect=="cercomb1" | all=="TRUE" ){
		h_cercomb1 = h_msecomb1*cer_h
		b_cercomb1 = b_msecomb1*cer_b
		}
	if  (bwselect=="cercomb2" | all=="TRUE" ){
		h_cercomb2_l = h_msecomb2_l*cer_h
		h_cercomb2_r = h_msecomb2_r*cer_h
		b_cercomb2_l = b_msecomb2_l*cer_b
		b_cercomb2_r = b_msecomb2_r*cer_b
	}

if (all==FALSE){
  bw_list = bwselect
  bws = matrix(NA,1,4)
  colnames(bws)=c("h (left)","h (right)","b (left)","b (right)")
  rownames(bws)=bwselect
  if  (bwselect=="mserd" | bwselect=="") bws[1,] = c(h_mserd,      h_mserd,      b_mserd,      b_mserd)
  if  (bwselect=="msetwo")               bws[1,] = c(h_msetwo_l,   h_msetwo_r,   b_msetwo_l,   b_msetwo_r)
  if  (bwselect=="msesum")               bws[1,] = c(h_msesum,     h_msesum,     b_msesum,     b_msesum)
  if  (bwselect=="msecomb1")             bws[1,] = c(h_msecomb1,   h_msecomb1,   b_msecomb1,   b_msecomb1)
  if  (bwselect=="msecomb2")             bws[1,] = c(h_msecomb2_l, h_msecomb2_r, b_msecomb2_l, b_msecomb2_r) 
  if  (bwselect=="cerrd")                bws[1,] = c(h_cerrd,      h_cerrd,      b_cerrd,      b_cerrd)
  if  (bwselect=="certwo")               bws[1,] = c(h_certwo_l,   h_certwo_r,   b_certwo_l,   b_certwo_r)
  if  (bwselect=="cersum")               bws[1,] = c(h_cersum,     h_cersum,     b_cersum,     b_cersum)
  if  (bwselect=="cercomb1")             bws[1,] = c(h_cercomb1,   h_cercomb1,   b_cercomb1,   b_cercomb1)
  if  (bwselect=="cercomb2")             bws[1,] = c(h_cercomb2_l, h_cercomb2_r, b_cercomb2_l, b_cercomb2_r)
}

  if (all=="TRUE"){
    bwselect="All"
    bws = matrix(NA,10,4)
    colnames(bws)=c("h (left)","h (right)","b (left)","b (right)")
    bw_list=c("mserd","msetwo","msesum","msecomb1","msecomb2","cerrd","certwo","cersum","cercomb1","cercomb2") 
    rownames(bws)=c("mserd","msetwo","msesum","msecomb1","msecomb2","cerrd","certwo","cersum","cercomb1","cercomb2") 
    bws[1,] =c(h_mserd,      h_mserd,      b_mserd,      b_mserd)
    bws[2,] =c(h_msetwo_l,   h_msetwo_r,   b_msetwo_l,   b_msetwo_r)
    bws[3,] =c(h_msesum,     h_msesum,     b_msesum,     b_msesum)
    bws[4,] =c(h_msecomb1,   h_msecomb1,   b_msecomb1,   b_msecomb1)
    bws[5,] =c(h_msecomb2_l, h_msecomb2_r, b_msecomb2_l, b_msecomb2_r) 
    bws[6,] =c(h_cerrd,      h_cerrd,      b_cerrd,      b_cerrd)
    bws[7,] =c(h_certwo_l,   h_certwo_r,   b_certwo_l,   b_certwo_r)
    bws[8,] =c(h_cersum,     h_cersum,     b_cersum,     b_cersum)
    bws[9,] =c(h_cercomb1,   h_cercomb1,   b_cercomb1,   b_cercomb1)
    bws[10,]=c(h_cercomb2_l, h_cercomb2_r, b_cercomb2_l, b_cercomb2_r)
  }



### Eff N
w_h_l <- rdrobust_kweight(X_l,c,bws[1,1],kernel)
w_h_r <- rdrobust_kweight(X_r,c,bws[1,2],kernel)
N_h_l <- sum(w_h_l> 0)
N_h_r <- sum(w_h_r> 0)

  out = list(bws=bws, 
             bwselect=bwselect, bw_list=bw_list, kernel=kernel_type, p=p, q=q, c=c,
             N=c(N_l,N_r), N_h = c(N_h_l,N_h_r),  M=c(M_l,M_r), vce=vce_type, masspoints=masspoints)
  out$call <- match.call()
  class(out) <- "rdbwselect"
  return(out)
}

print.rdbwselect <- function(x,...){
  cat("Call: rdbwselect\n\n")
  cat(paste("Number of Obs.           ",  format(x$N[1]+x$N[2], width=10, justify="right"),"\n", sep=""))
  cat(paste("BW type                  ",  format(x$bwselect, width=10, justify="right"),"\n", sep=""))
  cat(paste("Kernel                   ",  format(x$kernel,   width=10, justify="right"),"\n", sep=""))
  cat(paste("VCE method               ",  format(x$vce,      width=10, justify="right"),"\n", sep=""))
  cat("\n")
  cat(paste("Number of Obs.           ",  format(x$N[1], width=10, justify="right"),  "   ", format(x$N[2], width=10, justify="right"),        "\n", sep=""))
  cat(paste("Order est. (p)           ",  format(x$p,    width=10, justify="right"),  "   ", format(x$p,    width=10, justify="right"),       "\n", sep=""))
  cat(paste("Order bias  (q)          ",  format(x$q,    width=10, justify="right"),  "   ", format(x$q,    width=10, justify="right"),       "\n", sep=""))
  if (x$masspoints=="adjust" | x$masspoints=="check") cat(paste("Unique Obs.              ", format(x$M[1], width=10, justify="right"), "   ", format(x$M[2],width=10, justify="right"),        "\n", sep=""))
  cat("\n")
}

summary.rdbwselect <- function(object,...) {
  x    <- object
  args <- list(...)
  
  cat("Call: rdbwselect\n\n")
  
  cat(paste("Number of Obs.           ",  format(x$N[1]+x$N[2], width=10, justify="right"),"\n", sep=""))
  cat(paste("BW type                  ",  format(x$bwselect, width=10, justify="right"),"\n", sep=""))
  cat(paste("Kernel                   ",  format(x$kernel,   width=10, justify="right"),"\n", sep=""))
  cat(paste("VCE method               ",  format(x$vce,      width=10, justify="right"),"\n", sep=""))
  cat("\n")
  cat(paste("Number of Obs.           ",  format(x$N[1], width=10, justify="right"),  "   ", format(x$N[2], width=10, justify="right"),        "\n", sep=""))
  cat(paste("Order est. (p)           ",  format(x$p,    width=10, justify="right"),  "   ", format(x$p,    width=10, justify="right"),       "\n", sep=""))
  cat(paste("Order bias  (q)          ",  format(x$q,    width=10, justify="right"),  "   ", format(x$q,    width=10, justify="right"),       "\n", sep=""))
  if (x$masspoints=="adjust" | x$masspoints=="check") cat(paste("Unique Obs.              ", format(x$M[1], width=10, justify="right"), "   ", format(x$M[2],width=10, justify="right"),        "\n", sep=""))
  cat("\n")
  
  
    col1.names = c("","BW est. (h)", "BW bias (b)")
    col2.names = c("","Left of c", "Right of c","Left of c", "Right of c")

  ### print output
  cat(paste(rep("=", 15 + 10*4), collapse="")); cat("\n")

    cat(format(col1.names  , width=14, justify="right"))
    cat("\n")
    cat(format(col2.names            , width=10, justify="right"))
    cat("\n")
    
  cat(paste(rep("=", 15 + 10*4), collapse="")); cat("\n")
  
    for (j in 1:nrow(x$bws)) {
      #cat(format(toString(j), width=4))
      cat(format(x$bw_list[j]           , width=10, justify="right"))
      cat(format(sprintf("%3.3f", x$bws[j,]), width=10, justify="right"))
      cat("\n")
    }
    cat(paste(rep("=", 15 + 10*ncol(x$bws)), collapse="")); cat("\n")   
}

