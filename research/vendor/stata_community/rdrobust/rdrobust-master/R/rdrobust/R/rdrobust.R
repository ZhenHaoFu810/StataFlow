rdrobust = function(y, x, c = NULL, fuzzy = NULL, deriv = NULL,  
                    p = NULL, q = NULL, h = NULL, b = NULL, rho = NULL, 
                    covs = NULL, covs_drop = TRUE, ginv.tol = 1e-20,
                    kernel = "tri", weights = NULL, bwselect = "mserd",
                    vce = "nn", cluster = NULL, nnmatch = 3, level = 95, 
                    scalepar = 1, scaleregul = 1, sharpbw = FALSE, 
                    detail = NULL, all = NULL, subset = NULL, masspoints = "adjust",
                    bwcheck = NULL, bwrestrict = TRUE, stdvars = FALSE) {
 
  #print("Start Code")
  #start_time <- Sys.time()
  
  if (!is.null(subset)) {
    x <- x[subset]
    y <- y[subset]
  }
  
  if (is.null(c)) c <- 0
  if (is.null(p) & !is.null(deriv)) {p = deriv+1}
  
  if (length(p) == 0) {
    flag_no_p <- TRUE
    p <- 1
  } else if ((length(p) != 1) | !(p[1]%in%0:20)) {
    stop("Polynomial order p incorrectly specified.\n")
  } else {
    flag_no_p <- FALSE
  }
  
  if (length(q) == 0) {
    flag_no_q <- TRUE
    q <- p + 1
  } else if ((length(q) > 1) | !(q[1]%in%c(0:20)) | (q[1]<p)) {
    stop("Polynomial order (for bias correction) q incorrectly specified.\n")
  } else {
    flag_no_q <- FALSE
  }
  
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
  if (!is.null(fuzzy))   fuzzy   = as.matrix(  fuzzy[na.ok])
  if (!is.null(cluster)) cluster = as.matrix(cluster[na.ok])
  if (!is.null(weights)) weights = as.matrix(weights[na.ok])
  
  if (is.null(masspoints)) masspoints <- FALSE

  if (vce=="nn" | masspoints=="check" |masspoints=="adjust") {
    order_x <- order(x)
    x <- x[order_x,,drop=FALSE]
    y <- y[order_x,,drop=FALSE]
    if (!is.null(covs))    covs    =  as.matrix(covs)[order_x,,drop=FALSE]
    if (!is.null(fuzzy))   fuzzy   =   fuzzy[order_x,,drop=FALSE]
    if (!is.null(cluster)) cluster = cluster[order_x,,drop=FALSE]
    if (!is.null(weights)) weights = weights[order_x,,drop=FALSE]
  }

  ############## COLLINEARITY
  covs_drop_coll=dZ=0
  if (covs_drop == TRUE) covs_drop_coll = 1 
  if (!is.null(covs)) dZ = ncol(covs)
  
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
  
  kernel   <- tolower(kernel)
  bwselect <- tolower(bwselect)
  vce      <- tolower(vce)
  
  if (is.null(h)) {
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
  }

  ind_l = x<c;  ind_r = x>=c
  X_l = x[ind_l,,drop=FALSE];  X_r = x[ind_r,,drop=FALSE]
  Y_l = y[ind_l,,drop=FALSE];  Y_r = y[ind_r,,drop=FALSE]
  x_min = min(x);  x_max = max(x)
  range_l = abs(c-x_min);  range_r = abs(c-x_max)
  N_l = length(X_l);   N_r = length(X_r)
  N = N_r + N_l
  quant = -qnorm(abs((1-(level/100))/2))
  
  dT = 0
  T_l = T_r = NULL
  perf_comp = FALSE
  if (!is.null(fuzzy)) {
    dT = 1
    T_l  = fuzzy[ind_l,,drop=FALSE];  T_r  = fuzzy[ind_r,,drop=FALSE]
    
    if (var(T_l)==0 | var(T_r)==0) perf_comp=TRUE
    
  if (perf_comp==TRUE | sharpbw==TRUE) {
      dT = 0
      T_l = T_r = NULL
    }
  }
  

  
  
  Z_l = Z_r = NULL
  if (!is.null(covs)) {
    Z_l  = covs[ind_l,,drop=FALSE];   Z_r  = covs[ind_r,,drop=FALSE]
  }
  
  g_l = g_r = 0       
  C_l = C_r = NULL
  if (!is.null(cluster)) {
    C_l = cluster[ind_l,,drop=FALSE]; g_l = length(unique(C_l))
    C_r = cluster[ind_r,,drop=FALSE]; g_r = length(unique(C_r))
  }
  
  fw_l = fw_r = 0 
  if (!is.null(weights)) {
    fw_l = weights[ind_l,,drop=FALSE];  fw_r = weights[ind_r,,drop=FALSE]
  }  	
  
  vce_type = "NN"
  if (vce=="hc0")         vce_type = "HC0"
  if (vce=="hc1")         vce_type = "HC1"
  if (vce=="hc2")         vce_type = "HC2"
  if (vce=="hc3")      	  vce_type = "HC3"
  if (!is.null(cluster))	vce_type = "Cluster"

  if (vce=="nn") {
    nn_l = rep(1,N_l)
    nn_r = rep(1,N_r)
    dups_l   = ave(nn_l, X_l, FUN = sum)
    dups_r   = ave(nn_r, X_r, FUN = sum)
    dupsid_l = ave(nn_l, X_l, FUN = cumsum)
    dupsid_r = ave(nn_r, X_r, FUN = cumsum)
  }          
  
  #####################################################   CHECK ERRORS
  exit=0
  if (kernel!="uni" & kernel!="uniform" & kernel!="tri" & kernel!="triangular" & kernel!="epa" & kernel!="epanechnikov" & kernel!="" ){
    warning("kernel incorrectly specified")
    exit = 1
  }
  
  if  (bwselect!="mserd" & bwselect!="msetwo" & bwselect!="msesum" & bwselect!="msecomb1" & bwselect!="msecomb2" & bwselect!="cerrd" & bwselect!="certwo" & bwselect!="cersum" & bwselect!="cercomb1" & bwselect!="cercomb2" & bwselect!=""){
    warning("bwselect incorrectly specified")  
    exit = 1
  }
  
  if (bwselect=="cct" | bwselect=="ik" | bwselect=="cv"){
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
    
  if (level>100 | level<=0){
    warning("level should be set between 0 and 100")
    exit = 1
  }
    
  if (!is.null(rho)){  
     if (rho<0){
        warning("rho should be greater than 0")
        exit = 1
      }
  }
  
  if (exit>0) stop()
  if (!is.null(h)) bwselect = "Manual"
  if (!is.null(h) & is.null(rho) & is.null(b)) {
    rho = 1
    b = h
  }
  if (!is.null(h) & !is.null(rho) ) b = h/rho
    
  
  if (N<20){
			warning("Not enough observations to perform bandwidth calculations. Estimates computed using entire sample")
      h = b = max(range_l,range_r)
			bwselect = "Manual"
		}
  
  if (kernel=="epanechnikov" | kernel=="epa") {
    kernel_type = "Epanechnikov"
    C_c = 2.34
  }  else if (kernel=="uniform" | kernel=="uni") {
    kernel_type = "Uniform"
    C_c = 1.843
  }   else  {
    kernel_type = "Triangular"
    C_c = 2.576
  }
  
  vce_type = "NN"
  if (vce=="hc0")     		vce_type = "HC0"
  if (vce=="hc1")      	  vce_type = "HC1"
  if (vce=="hc2")      	  vce_type = "HC2"
  if (vce=="hc3")      	  vce_type = "HC3"
  if (vce=="cluster")  	  vce_type = "Cluster"
  if (vce=="nncluster") 	vce_type = "NNcluster"
  
  
  ############################################################################################
  #cat(paste("Preparing data -> ",  Sys.time()-start_time,"\n", sep=""))
  #start_time <- Sys.time()
  ############################################################################################
  mN = N;  M_l = N_l;  M_r = N_r
  
  if (is.null(h)) {
 
    if (masspoints=="check" | masspoints=="adjust") {
      X_uniq_l = sort(unique(X_l), decreasing=TRUE)
      X_uniq_r = unique(X_r)
      M_l = length(X_uniq_l)
      M_r = length(X_uniq_r)
      M = M_l + M_r
      mass_l = 1-M_l/N_l
      mass_r = 1-M_r/N_r				
      if (mass_l>=0.2 | mass_r>=0.2){
        warning("Mass points detected in the running variable.")
        if (masspoints=="check") warning("Try using option masspoints=adjust.")
        if (is.null(bwcheck) & masspoints=="adjust") bwcheck <- 10
      }				
    }
  

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
      
      #### TWO
      if  (bwselect=="msetwo" |  bwselect=="certwo" | bwselect=="msecomb2" | bwselect=="cercomb2" )  {		
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
      if  (bwselect=="msesum" | bwselect=="cersum" |  bwselect=="msecomb1" | bwselect=="msecomb2" |  bwselect=="cercomb1" | bwselect=="cercomb2")  {
        
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
      if  (bwselect=="mserd" | bwselect=="cerrd" | bwselect=="msecomb1" | bwselect=="msecomb2" | bwselect=="cercomb1" | bwselect=="cercomb2" | bwselect=="" ) {
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
     
      if  (bwselect=="mserd" | bwselect=="cerrd" | bwselect=="msecomb1" | bwselect=="msecomb2" | bwselect=="cercomb1" | bwselect=="cercomb2" | bwselect=="" ) {
        h_mserd = x_sd*h_bw_d
        b_mserd = x_sd*b_bw_d
      }	
      if  (bwselect=="msesum" | bwselect=="cersum" |  bwselect=="msecomb1" | bwselect=="msecomb2" |  bwselect=="cercomb1" | bwselect=="cercomb2" )  {
        h_msesum = x_sd*h_bw_s
        b_msesum = x_sd*b_bw_s
      }
      if  (bwselect=="msetwo" |  bwselect=="certwo" | bwselect=="msecomb2" | bwselect=="cercomb2")  {		
        h_msetwo_l = x_sd*h_bw_l
        h_msetwo_r = x_sd*h_bw_r
        b_msetwo_l = x_sd*b_bw_l
        b_msetwo_r = x_sd*b_bw_r
      }
      if  (bwselect=="msecomb1" | bwselect=="cercomb1" ) {
        h_msecomb1 = min(c(h_mserd,h_msesum))
        b_msecomb1 = min(c(b_mserd,b_msesum))
      }
      if  (bwselect=="msecomb2" | bwselect=="cercomb2") {
        h_msecomb2_l = median(c(h_mserd,h_msesum,h_msetwo_l))
        h_msecomb2_r = median(c(h_mserd,h_msesum,h_msetwo_r))
        b_msecomb2_l = median(c(b_mserd,b_msesum,b_msetwo_l))
        b_msecomb2_r = median(c(b_mserd,b_msesum,b_msetwo_r))
      }
      
      
      cer_h = N^(-(p/((3+p)*(3+2*p))))
      
      if (!is.null(cluster)) {
        cer_h = (g_l+g_r)^(-(p/((3+p)*(3+2*p))))
      }
      
      cer_b = 1
      if  (bwselect=="cerrd"){
        h_cerrd = h_mserd*cer_h
        b_cerrd = b_mserd*cer_b
      }
      if  (bwselect=="cersum"){
        h_cersum = h_msesum*cer_h
        b_cersum=  b_msesum*cer_b
      }
      if  (bwselect=="certwo"){
        h_certwo_l   = h_msetwo_l*cer_h
        h_certwo_r   = h_msetwo_r*cer_h
        b_certwo_l   = b_msetwo_l*cer_b
        b_certwo_r   = b_msetwo_r*cer_b
      }
      if  (bwselect=="cercomb1"){
        h_cercomb1 = h_msecomb1*cer_h
        b_cercomb1 = b_msecomb1*cer_b
      }
      if  (bwselect=="cercomb2"){
        h_cercomb2_l = h_msecomb2_l*cer_h
        h_cercomb2_r = h_msecomb2_r*cer_h
        b_cercomb2_l = b_msecomb2_l*cer_b
        b_cercomb2_r = b_msecomb2_r*cer_b
      }
      
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
     
      h_l = c(bws[1]); b_l = c(bws[3])
      h_r = c(bws[2]); b_r = c(bws[4])
 
      if (!is.null(rho)) {
        b_l = h_l/rho
    		b_r = h_r/rho
      }
      
    } else{
      if (length(h)==1) h_l = h_r = h
      if (length(h)==2) {
        h_l = h[1]
        h_r = h[2]
      }
      if (is.null(b)) {
        b_l = h_l
        b_r = h_r
      } else {
        if (length(b)==1) b_l = b_r = b
        if (length(b)==2) {
          b_l = b[1]
          b_r = b[2]
        }  
      }  
    }

  if (isTRUE(stdvars)) { 
    c = c*x_sd
  	X_l = X_l*x_sd;	X_r = X_r*x_sd
  	Y_l = Y_l*y_sd;	Y_r = Y_r*y_sd
  }
  
  ### end BW selection
  
  
  ### Estimation
  w_h_l <- rdrobust_kweight(X_l,c,h_l,kernel);	w_h_r <- rdrobust_kweight(X_r,c,h_r,kernel)
  w_b_l <- rdrobust_kweight(X_l,c,b_l,kernel);	w_b_r <- rdrobust_kweight(X_r,c,b_r,kernel)
  
  if (!is.null(weights)) {
    w_h_l <- fw_l*w_h_l;	w_h_r <- fw_r*w_h_r
    w_b_l <- fw_l*w_b_l;	w_b_r <- fw_r*w_b_r			
  }

  ind_h_l <- w_h_l> 0;		ind_h_r <- w_h_r> 0
  ind_b_l <- w_b_l> 0;		ind_b_r <- w_b_r> 0
  N_h_l <- sum(ind_h_l); N_b_l <- sum(ind_b_l)
  N_h_r <- sum(ind_h_r); N_b_r <- sum(ind_b_r)
  
  ind_l = ind_b_l; ind_r = ind_b_r
  if (h_l>b_l) ind_l = ind_h_l   
  if (h_r>b_r) ind_r = ind_h_r   
  
  eN_l = sum(ind_l); eN_r = sum(ind_r)
  eY_l  = Y_l[ind_l,,drop=FALSE];	eY_r  = Y_r[ind_r,,drop=FALSE]
  eX_l  = X_l[ind_l,,drop=FALSE];	eX_r  = X_r[ind_r,,drop=FALSE]
  W_h_l = w_h_l[ind_l];	W_h_r = w_h_r[ind_r]
  W_b_l = w_b_l[ind_l];	W_b_r = w_b_r[ind_r]
  
  edups_l = edupsid_l = edups_r = edupsid_r = 0
 
  if (vce=="nn") {
    edups_l   = dups_l[ind_l] 
    edups_r   = dups_r[ind_r]
    edupsid_l = dupsid_l[ind_l]
    edupsid_r = dupsid_r[ind_r]
  }          
          
  u_l <- (eX_l-c)/h_l;	u_r <-(eX_r-c)/h_r
  R_q_l = matrix(NA,eN_l,(q+1)); R_q_r = matrix(NA,eN_r,(q+1))
  for (j in 1:(q+1))  {
    R_q_l[,j] = (eX_l-c)^(j-1)
    R_q_r[,j] = (eX_r-c)^(j-1)
  }
  R_p_l = R_q_l[,1:(p+1)]; R_p_r = R_q_r[,1:(p+1)]

  
  #print(Sys.time()-start_time)
  #print("Computing RD estimates.")
  #start_time <- Sys.time()
  
  L_l = crossprod(R_p_l*W_h_l,u_l^(p+1)); L_r = crossprod(R_p_r*W_h_r,u_r^(p+1)) 
  invG_q_l  = qrXXinv((sqrt(W_b_l)*R_q_l));	invG_q_r  = qrXXinv((sqrt(W_b_r)*R_q_r))
  invG_p_l  = qrXXinv((sqrt(W_h_l)*R_p_l));	invG_p_r  = qrXXinv((sqrt(W_h_r)*R_p_r))
  e_p1 = matrix(0,(q+1),1); e_p1[p+2]=1
  e_v  = matrix(0,(p+1),1); e_v[deriv+1]=1
  Q_q_l = t(t(R_p_l*W_h_l) - h_l^(p+1)*(L_l%*%t(e_p1))%*%t(t(invG_q_l%*%t(R_q_l))*W_b_l))
  Q_q_r = t(t(R_p_r*W_h_r) - h_r^(p+1)*(L_r%*%t(e_p1))%*%t(t(invG_q_r%*%t(R_q_r))*W_b_r))
  D_l = eY_l; D_r = eY_r

  eT_l = eT_r = NULL
  if (!is.null(fuzzy)) {
  
    if (perf_comp==TRUE | sharpbw==TRUE) {
      dT = 1
      T_l  = fuzzy[x<c,,drop=FALSE];  T_r  = fuzzy[x>=c,,drop=FALSE]
    }
    
    eT_l = T_l[ind_l,,drop=FALSE]; D_l  = cbind(D_l,eT_l)
    eT_r = T_r[ind_r,,drop=FALSE]; D_r  = cbind(D_r,eT_r)
  }
  
  eZ_l = eZ_r = NULL
  if (!is.null(covs)) {
    eZ_l  = Z_l[ind_l,,drop=FALSE]; D_l   = cbind(D_l,eZ_l)
    eZ_r  = Z_r[ind_r,,drop=FALSE]; D_r   = cbind(D_r,eZ_r)
    U_p_l = crossprod(R_p_l*W_h_l,D_l); U_p_r = crossprod(R_p_r*W_h_r,D_r)
  }
    
  eC_l = eC_r = NULL
  if (!is.null(cluster)) {
    eC_l  = C_l[ind_l]; eC_r  = C_r[ind_r]
  }
  
  beta_p_l  = invG_p_l%*%crossprod(R_p_l*W_h_l,D_l) 
  beta_p_r  = invG_p_r%*%crossprod(R_p_r*W_h_r,D_r) 
  beta_q_l  = invG_q_l%*%crossprod(R_q_l*W_b_l,D_l)
  beta_q_r  = invG_q_r%*%crossprod(R_q_r*W_b_r,D_r)
  beta_bc_l = invG_p_l%*%crossprod(Q_q_l,D_l) 
  beta_bc_r = invG_p_r%*%crossprod(Q_q_r,D_r)
  beta_p    = beta_p_r  - beta_p_l
  beta_q    = beta_q_r  - beta_q_l
  beta_bc   = beta_bc_r - beta_bc_l

  gamma_p = NULL
  if (is.null(covs)) {	
    tau_cl = tau_Y_cl = scalepar*factorial(deriv)*beta_p[(deriv+1),1]
    tau_bc = tau_Y_bc = scalepar*factorial(deriv)*beta_bc[(deriv+1),1]
    s_Y = 1
    
    tau_Y_cl_l = scalepar*factorial(deriv)*beta_p_l[(deriv+1),1]
    tau_Y_cl_r = scalepar*factorial(deriv)*beta_p_r[(deriv+1),1]
    tau_Y_bc_l = scalepar*factorial(deriv)*beta_bc_l[(deriv+1),1]
    tau_Y_bc_r = scalepar*factorial(deriv)*beta_bc_r[(deriv+1),1]
    bias_l = tau_Y_cl_l-tau_Y_bc_l
    bias_r = tau_Y_cl_r-tau_Y_bc_r 
    
    beta_Y_p_l = scalepar*factorial(deriv)*beta_p_l[,1]
    beta_Y_p_r = scalepar*factorial(deriv)*beta_p_r[,1]
    
    
    if (!is.null(fuzzy)) {
       tau_T_cl = factorial(deriv)*beta_p[(deriv+1),2]
       tau_T_bc = factorial(deriv)*beta_bc[(deriv+1),2]
       tau_cl   = tau_Y_cl/tau_T_cl
       s_Y      = c(1/tau_T_cl , -(tau_Y_cl/tau_T_cl^2))
       B_F      = c(tau_Y_cl-tau_Y_bc , tau_T_cl-tau_T_bc)
       tau_bc   = tau_cl - t(s_Y)%*%B_F
       sV_T     = c(0 , 1)
       
       tau_T_cl_l = factorial(deriv)*beta_p_l[(deriv+1),2]
       tau_T_cl_r = factorial(deriv)*beta_p_r[(deriv+1),2]
       tau_T_bc_l = factorial(deriv)*beta_bc_l[(deriv+1),2]
       tau_T_bc_r = factorial(deriv)*beta_bc_r[(deriv+1),2]
       B_F_l = c(tau_Y_cl_l-tau_Y_bc_l, tau_T_cl_l-tau_T_bc_l)
       B_F_r = c(tau_Y_cl_r-tau_Y_bc_r, tau_T_cl_r-tau_T_bc_r)
       bias_l = t(s_Y)%*%B_F_l
  		 bias_r = t(s_Y)%*%B_F_r
  		 
  		 beta_T_p_l = scalepar*factorial(deriv)*beta_p_l[,2]
  		 beta_T_p_r = scalepar*factorial(deriv)*beta_p_r[,2]
  		 
  }	
  } else {	
    ZWD_p_l  = crossprod(eZ_l*W_h_l,D_l)
    ZWD_p_r  = crossprod(eZ_r*W_h_r,D_r)
    colsZ = (2+dT):max(c(2+dT+dZ-1,(2+dT)))
    UiGU_p_l =  crossprod(matrix(U_p_l[,colsZ],nrow=p+1),invG_p_l%*%U_p_l) 
    UiGU_p_r =  crossprod(matrix(U_p_r[,colsZ],nrow=p+1),invG_p_r%*%U_p_r) 
    ZWZ_p_l = ZWD_p_l[,colsZ] - UiGU_p_l[,colsZ] 
    ZWZ_p_r = ZWD_p_r[,colsZ] - UiGU_p_r[,colsZ]     
    ZWY_p_l = ZWD_p_l[,1:(1+dT)] - UiGU_p_l[,1:(1+dT)] 
    ZWY_p_r = ZWD_p_r[,1:(1+dT)] - UiGU_p_r[,1:(1+dT)]     
    ZWZ_p = ZWZ_p_r + ZWZ_p_l
    ZWY_p = ZWY_p_r + ZWY_p_l
    if (covs_drop_coll == 0) gamma_p = chol2inv(chol(ZWZ_p))%*%ZWY_p
    if (covs_drop_coll == 1) gamma_p = ginv(ZWZ_p, tol = ginv.tol)%*%ZWY_p
    s_Y = c(1 ,  -gamma_p[,1])
    
    if (is.null(fuzzy)) {
        tau_cl = scalepar*t(s_Y)%*%beta_p[(deriv+1),]
        tau_bc = scalepar*t(s_Y)%*%beta_bc[(deriv+1),]
        
        tau_Y_cl_l = scalepar*t(s_Y)%*%beta_p_l[(deriv+1),]
        tau_Y_cl_r = scalepar*t(s_Y)%*%beta_p_r[(deriv+1),]
        tau_Y_bc_l = scalepar*t(s_Y)%*%beta_bc_l[(deriv+1),]
        tau_Y_bc_r = scalepar*t(s_Y)%*%beta_bc_r[(deriv+1),]
        bias_l = tau_Y_cl_l-tau_Y_bc_l
        bias_r = tau_Y_cl_r-tau_Y_bc_r 
        
        beta_Y_p_l = scalepar*tcrossprod(s_Y,beta_p_l)
        beta_Y_p_r = scalepar*tcrossprod(s_Y,beta_p_r)

    } else {
      s_T  = c(1,    -gamma_p[,2])
      sV_T = c(0, 1, -gamma_p[,2])
      tau_Y_cl = c(scalepar*factorial(deriv)*t(s_Y)%*%c(beta_p[(deriv+1),1], beta_p[(deriv+1),colsZ]))
      tau_Y_bc = c(scalepar*factorial(deriv)*t(s_Y)%*%c(beta_bc[(deriv+1),1],beta_bc[(deriv+1),colsZ]))
      tau_T_cl = c(         factorial(deriv)*t(s_T)%*%c(beta_p[(deriv+1),2], beta_p[(deriv+1),colsZ]))
      tau_T_bc = c(         factorial(deriv)*t(s_T)%*%c(beta_bc[(deriv+1),2],beta_bc[(deriv+1),colsZ]))

      tau_Y_cl_l = c(scalepar*factorial(deriv)*t(s_Y)%*%c(beta_p_l[(deriv+1),1], beta_p_l[(deriv+1),colsZ]))
      tau_Y_cl_r = c(scalepar*factorial(deriv)*t(s_Y)%*%c(beta_p_r[(deriv+1),2], beta_p_r[(deriv+1),colsZ]))
      tau_Y_bc_l = c(scalepar*factorial(deriv)*t(s_Y)%*%c(beta_bc_l[(deriv+1),1],beta_bc_l[(deriv+1),colsZ]))
      tau_Y_bc_r = c(scalepar*factorial(deriv)*t(s_Y)%*%c(beta_bc_r[(deriv+1),2],beta_bc_r[(deriv+1),colsZ]))

      tau_T_cl_l = c(factorial(deriv)*t(s_T)%*%c(beta_p_l[(deriv+1),1], beta_p_l[(deriv+1), colsZ]))
      tau_T_cl_r = c(factorial(deriv)*t(s_T)%*%c(beta_p_r[(deriv+1),2], beta_p_r[(deriv+1), colsZ]))
      tau_T_bc_l = c(factorial(deriv)*t(s_T)%*%c(beta_bc_l[(deriv+1),1],beta_bc_l[(deriv+1),colsZ]))
      tau_T_bc_r = c(factorial(deriv)*t(s_T)%*%c(beta_bc_r[(deriv+1),2],beta_bc_r[(deriv+1),colsZ]))

      beta_Y_p_l = scalepar*factorial(deriv)*t(s_Y)%*%t(cbind(beta_p_l[,1], beta_p_l[,colsZ]))
      beta_Y_p_r = scalepar*factorial(deriv)*t(s_Y)%*%t(cbind(beta_p_r[,1], beta_p_r[,colsZ]))
      beta_T_p_l =          factorial(deriv)*t(s_T)%*%t(cbind(beta_p_l[,2], beta_p_l[,colsZ]))
      beta_T_p_r =          factorial(deriv)*t(s_T)%*%t(cbind(beta_p_r[,2], beta_p_r[,colsZ]))
      
      tau_cl = tau_Y_cl/tau_T_cl
      B_F   = c(tau_Y_cl-tau_Y_bc,     tau_T_cl-tau_T_bc)
      B_F_l = c(tau_Y_cl_l-tau_Y_bc_l, tau_T_cl_l-tau_T_bc_l)
      B_F_r = c(tau_Y_cl_r-tau_Y_bc_r, tau_T_cl_r-tau_T_bc_r)
      
      s_Y = c(1/tau_T_cl , -(tau_Y_cl/tau_T_cl^2))
      tau_bc = tau_cl - t(s_Y)%*%B_F
      
      bias_l = t(s_Y)%*%B_F_l
      bias_r = t(s_Y)%*%B_F_r

      s_Y = c(1/tau_T_cl , -(tau_Y_cl/tau_T_cl^2) , -(1/tau_T_cl)*gamma_p[,1] + (tau_Y_cl/tau_T_cl^2)*gamma_p[,2])
    }
  }

  #print(Sys.time()-start_time)
  #print("Computing variance-covariance matrix.")
  #start_time <- Sys.time()

  hii_p_l = hii_p_r = hii_q_l = hii_q_r = predicts_p_l = predicts_p_r = predicts_q_l = predicts_q_r = 0
  if (vce=="hc0" | vce=="hc1" | vce=="hc2" | vce=="hc3") {
    predicts_p_l = R_p_l%*%beta_p_l
    predicts_p_r = R_p_r%*%beta_p_r
    predicts_q_l = R_q_l%*%beta_q_l
    predicts_q_r = R_q_r%*%beta_q_r
    
    if (vce=="hc2" | vce=="hc3") {
      hii_p_l = rowSums((R_p_l%*%invG_p_l)*(R_p_l*W_h_l))
      hii_p_r = rowSums((R_p_r%*%invG_p_r)*(R_p_r*W_h_r))
      
      hii_q_l = rowSums((R_q_l%*%invG_q_l)*(R_q_l*W_b_l))
      hii_q_r = rowSums((R_q_r%*%invG_q_r)*(R_q_r*W_b_r))
    }
  }
  
	res_h_l = rdrobust_res(eX_l, eY_l, eT_l, eZ_l, predicts_p_l, hii_p_l, vce, nnmatch, edups_l, edupsid_l, p+1)
	res_h_r = rdrobust_res(eX_r, eY_r, eT_r, eZ_r, predicts_p_r, hii_p_r, vce, nnmatch, edups_r, edupsid_r, p+1)

		if (vce=="nn") {
			res_b_l = res_h_l;	res_b_r = res_h_r
	} 	else {
			res_b_l = rdrobust_res(eX_l, eY_l, eT_l, eZ_l, predicts_q_l, hii_q_l, vce, nnmatch, edups_l, edupsid_l, q+1)
			res_b_r = rdrobust_res(eX_r, eY_r, eT_r, eZ_r, predicts_q_r, hii_q_r, vce, nnmatch, edups_r, edupsid_r, q+1)
  }
			                       
	V_Y_cl_l = invG_p_l%*%rdrobust_vce(dT+dZ, s_Y, as.matrix(R_p_l*W_h_l), res_h_l, eC_l)%*%invG_p_l
	V_Y_cl_r = invG_p_r%*%rdrobust_vce(dT+dZ, s_Y, as.matrix(R_p_r*W_h_r), res_h_r, eC_r)%*%invG_p_r
	V_Y_rb_l = invG_p_l%*%rdrobust_vce(dT+dZ, s_Y, as.matrix(Q_q_l),       res_b_l, eC_l)%*%invG_p_l
	V_Y_rb_r = invG_p_r%*%rdrobust_vce(dT+dZ, s_Y, as.matrix(Q_q_r),       res_b_r, eC_r)%*%invG_p_r
	V_tau_cl = scalepar^2*factorial(deriv)^2*(V_Y_cl_l+V_Y_cl_r)[deriv+1,deriv+1]
	V_tau_rb = scalepar^2*factorial(deriv)^2*(V_Y_rb_l+V_Y_rb_r)[deriv+1,deriv+1]
	se_tau_cl = sqrt(V_tau_cl);	se_tau_rb = sqrt(V_tau_rb)

	if (!is.null(fuzzy)) {
		V_T_cl_l = invG_p_l%*%rdrobust_vce(dT+dZ, sV_T, as.matrix(R_p_l*W_h_l), res_h_l, eC_l)%*%invG_p_l
		V_T_cl_r = invG_p_r%*%rdrobust_vce(dT+dZ, sV_T, as.matrix(R_p_r*W_h_r), res_h_r, eC_r)%*%invG_p_r
		V_T_rb_l = invG_p_l%*%rdrobust_vce(dT+dZ, sV_T, as.matrix(Q_q_l), res_b_l, eC_l)%*%invG_p_l
		V_T_rb_r = invG_p_r%*%rdrobust_vce(dT+dZ, sV_T, as.matrix(Q_q_r), res_b_r, eC_r)%*%invG_p_r
		V_T_cl = factorial(deriv)^2*(V_T_cl_l+V_T_cl_r)[deriv+1,deriv+1]
		V_T_rb = factorial(deriv)^2*(V_T_rb_l+V_T_rb_r)[deriv+1,deriv+1]
		se_tau_T_cl = sqrt(V_T_cl);	se_tau_T_rb = sqrt(V_T_rb)
	}
  
	#print(Sys.time()-start_time)
	
	if (is.null(fuzzy)) {
	  if (is.null(covs)) {
	    if      (deriv==0) rdmodel = "Sharp RD estimates using local polynomial regression." 
	    else if (deriv==1) rdmodel = "Sharp Kink RD estimates using local polynomial regression."	
	    else               rdmodel = "Sharp RD estimates using local polynomial regression. Derivative of order d" 
		}
		else {
			if      (deriv==0) rdmodel = "Covariate-adjusted Sharp RD estimates using local polynomial regression." 
			else if (deriv==1) rdmodel = "Covariate-adjusted Sharp Kink RD estimates using local polynomial regression."	
			else               rdmodel = paste("Covariate-adjusted Sharp RD estimates using local polynomial regression. Derivative of order ", deriv, ".")	
	  }
	} else {
	  if (is.null(covs)) {
	    if      (deriv==0) rdmodel = "Fuzzy RD estimates using local polynomial regression." 
	    else if (deriv==1) rdmodel = "Fuzzy Kink RD estimates using local polynomial regression."	
	    else               rdmodel = paste("Fuzzy RD estimates using local polynomial regression. Derivative of order ", deriv, ".")	
		}
		else {
			if      (deriv==0) rdmodel = "Covariate-adjusted Fuzzy RD estimates using local polynomial regression." 
			else if (deriv==1) rdmodel = "Covariate-adjusted Fuzzy Kink RD estimates using local polynomial regression."	
			else               rdmodel = paste("Covariate-adjusted Fuzzy RD estimates using local polynomial regression. Derivative of order ", deriv, ".")			
	  }
	}
	
  tau = c(tau_cl, tau_bc, tau_bc)
  se  = c(se_tau_cl,se_tau_cl,se_tau_rb)
  t   =  tau/se
  pv  = 2*pnorm(-abs(t))
  ci  = matrix(NA,nrow=3,ncol=2)
  rownames(ci) = c("Conventional","Bias-Corrected","Robust")
  colnames(ci) = c("Lower","Upper")
  ci[1,] = c(tau[1] - quant*se[1], tau[1] + quant*se[1])
  ci[2,] = c(tau[2] - quant*se[2], tau[2] + quant*se[2])
  ci[3,] = c(tau[3] - quant*se[3], tau[3] + quant*se[3])
    
  if (!is.null(fuzzy)) {  
      tau_T = c(tau_T_cl, tau_T_bc, tau_T_bc)
      se_T  = c(se_tau_T_cl, se_tau_T_cl, se_tau_T_rb)
      t_T   = tau_T/se_T
      pv_T  = 2*pnorm(-abs(t_T))
      ci_T  = matrix(NA,nrow=3,ncol=2)
      ci_T[1,] = c(tau_T[1] - quant*se_T[1], tau_T[1] + quant*se_T[1])
      ci_T[2,] = c(tau_T[2] - quant*se_T[2], tau_T[2] + quant*se_T[2])
      ci_T[3,] = c(tau_T[3] - quant*se_T[3], tau_T[3] + quant*se_T[3])
  }

    coef = matrix(tau,3,1)
    se   = matrix(se, 3,1)
    z    = matrix(t,  3,1)
    pv   = matrix(pv, 3,1)
    ci   = ci

  bws=matrix(c(h_l,b_l,h_r,b_r),2,2)
  colnames(bws)=c("left","right")
  rownames(bws)=c("h","b")
  
  rownames(coef)=rownames(se)=rownames(se)=rownames(z)=rownames(pv)=c("Conventional","Bias-Corrected","Robust")
  colnames(coef)="Coeff"
  colnames(se)="Std. Err."
  colnames(z)="z"
  colnames(pv)="P>|z|"
  colnames(bws)=c("left","right")
  rownames(ci)=c("Conventional","Bias-Corrected","Robust")
  colnames(ci)=c("CI Lower","CI Upper")
    
  Estimate=matrix(NA,1,4)
  colnames(Estimate)=c("tau.us","tau.bc","se.us","se.rb")
  Estimate[1,] <- c(tau_cl,tau_bc, se_tau_cl, se_tau_rb) 

  if (is.null(fuzzy)) { 
  out <- list(Estimate = Estimate, bws = bws, coef = coef, se = se, z = z, pv = pv, ci = ci,
           beta_Y_p_l = beta_Y_p_l, beta_Y_p_r = beta_Y_p_r,
           V_cl_l=V_Y_cl_l, V_cl_r=V_Y_cl_r, V_rb_l=V_Y_rb_l, V_rb_r=V_Y_rb_r,
           N=c(N_l,N_r), N_h=c(N_h_l,N_h_r), N_b=c(N_b_l,N_b_r), M=c(M_l,M_r),
           tau_cl=c(tau_Y_cl_l,tau_Y_cl_r), tau_bc=c(tau_Y_bc_l,tau_Y_bc_r),
           c=c, p=p, q=q, bias=c(bias_l,bias_r), kernel=kernel_type, detail=detail, all=all,
           vce=vce_type, bwselect=bwselect, level=level, masspoints=masspoints,
           rdmodel=rdmodel, beta_covs=gamma_p)
  } else {  
    out <- list(Estimate = Estimate, bws = bws, coef = coef, se = se, z = z, pv = pv, ci = ci,
             beta_Y_p_l = beta_Y_p_l, beta_Y_p_r = beta_Y_p_r,
             beta_T_p_l = beta_T_p_l, beta_T_p_r = beta_T_p_r,
             tau_T = tau_T, se_T  = se_T, t_T   = t_T, pv_T  = pv_T, ci_T  = ci_T,
             V_cl_l=V_Y_cl_l, V_cl_r=V_Y_cl_r, V_rb_l=V_Y_rb_l, V_rb_r=V_Y_rb_r,
             N=c(N_l,N_r), N_h=c(N_h_l,N_h_r), N_b=c(N_b_l,N_b_r), M=c(M_l,M_r),
             tau_cl=c(tau_Y_cl_l,tau_Y_cl_r), tau_bc=c(tau_Y_bc_l,tau_Y_bc_r),
             c=c, p=p, q=q, bias=c(bias_l,bias_r), kernel=kernel_type, detail=detail, all=all,
             vce=vce_type, bwselect=bwselect, level=level, masspoints=masspoints,
             rdmodel=rdmodel, beta_covs=gamma_p)
    }
  
  out$call <- match.call()
  class(out) <- "rdrobust"
  return(out)


}


print.rdrobust <- function(x,...){
  cat("Call: rdrobust\n\n")
  cat(paste("Number of Obs.           ",  format(x$N[1]+x$N[2], width=10, justify="right"),"\n", sep=""))
  cat(paste("BW type                  ",  format(x$bwselect, width=10, justify="right"),"\n", sep=""))
  cat(paste("Kernel                   ",  format(x$kernel,   width=10, justify="right"),"\n", sep=""))
  cat(paste("VCE method               ",  format(x$vce,      width=10, justify="right"),"\n", sep=""))
  cat("\n")
  cat(paste("Number of Obs.           ",  format(x$N[1],  width=10, justify="right"),  "   ", format(x$N[2],   width=10, justify="right"),       "\n", sep=""))
  cat(paste("Eff. Number of Obs.      ",  format(x$N_h[1],width=10, justify="right"),  "   ", format(x$N_h[2], width=10, justify="right"),       "\n", sep=""))
  cat(paste("Order est. (p)           ",  format(x$p,     width=10, justify="right"),  "   ", format(x$p,      width=10, justify="right"),       "\n", sep=""))
  cat(paste("Order bias  (q)          ",  format(x$q,     width=10, justify="right"),  "   ", format(x$q,      width=10, justify="right"),       "\n", sep=""))
  cat(paste("BW est. (h)              ",  format(sprintf("%10.3f",x$bws[1,1])),         "   ", format(sprintf("%10.3f",x$bws[1,2])),       "\n", sep=""))
  cat(paste("BW bias (b)              ",  format(sprintf("%10.3f",x$bws[2,1])),         "   ", format(sprintf("%10.3f",x$bws[2,2])),       "\n", sep=""))
  cat(paste("rho (h/b)                ",  format(sprintf("%10.3f",x$bws[1,1]/x$bws[2,1])),  "   ", format(sprintf("%10.3f",x$bws[1,2]/x$bws[2,2])),       "\n", sep=""))
  if (x$masspoints=="adjust" | x$masspoints=="check") cat(paste("Unique Obs.              ",  format(x$M[1], width=10, justify="right"), "   ", format(x$M[2],width=10, justify="right"),        "\n", sep=""))
  cat("\n")
}

summary.rdrobust <- function(object,...) {
  x    <- object
  args <- list(...)

  cat(paste(x$rdmodel,"\n", sep=""))
  cat(paste("","\n", sep=""))
  
  #cat("Call: rdrobust\n\n")
  cat(paste("Number of Obs.           ",  format(x$N[1]+x$N[2], width=10, justify="right"),"\n", sep=""))
  cat(paste("BW type                  ",  format(x$bwselect, width=10, justify="right"),"\n", sep=""))
  cat(paste("Kernel                   ",  format(x$kernel,   width=10, justify="right"),"\n", sep=""))
  cat(paste("VCE method               ",  format(x$vce,      width=10, justify="right"),"\n", sep=""))
  cat("\n")
  cat(paste("Number of Obs.           ",  format(x$N[1],   width=10, justify="right"),  "   ", format(x$N[2],   width=10, justify="right"),       "\n", sep=""))
  cat(paste("Eff. Number of Obs.      ",  format(x$N_h[1], width=10, justify="right"),  "   ", format(x$N_h[2], width=10, justify="right"),       "\n", sep=""))
  cat(paste("Order est. (p)           ",  format(x$p,      width=10, justify="right"),  "   ", format(x$p,      width=10, justify="right"),       "\n", sep=""))
  cat(paste("Order bias  (q)          ",  format(x$q,      width=10, justify="right"),  "   ", format(x$q,      width=10, justify="right"),       "\n", sep=""))
  cat(paste("BW est. (h)              ",  format(sprintf("%10.3f",x$bws[1,1])),  "   ", format(sprintf("%10.3f",x$bws[1,2])),      "\n", sep=""))
  cat(paste("BW bias (b)              ",  format(sprintf("%10.3f",x$bws[2,1])),  "   ", format(sprintf("%10.3f",x$bws[2,2])),      "\n", sep=""))
  cat(paste("rho (h/b)                ",  format(sprintf("%10.3f",x$bws[1,1]/x$bws[2,1])),  "   ", format(sprintf("%10.3f",x$bws[1,2]/x$bws[2,2])),       "\n", sep=""))
  if (x$masspoints=="adjust" | x$masspoints=="check") cat(paste("Unique Obs.              ",  format(x$M[1], width=10, justify="right"), "   ", format(x$M[2],width=10, justify="right"),        "\n", sep=""))
  cat("\n")

  ### compute CI
  z <- -qnorm(abs((1-(x$level/100))/2))
  
  CI_us_l <- x$Estimate[, "tau.us"] - x$Estimate[, "se.us"] * z;
  CI_us_r <- x$Estimate[, "tau.us"] + x$Estimate[, "se.us"] * z;
  CI_bc_l <- x$Estimate[, "tau.bc"] - x$Estimate[, "se.us"] * z;
  CI_bc_r <- x$Estimate[, "tau.bc"] + x$Estimate[, "se.us"] * z;
  CI_rb_l <- x$Estimate[, "tau.bc"] - x$Estimate[, "se.rb"] * z;
  CI_rb_r <- x$Estimate[, "tau.bc"] + x$Estimate[, "se.rb"] * z;
  
  t_us =x$Estimate[, "tau.us"]/x$Estimate[, "se.us"]
  t_bc =x$Estimate[, "tau.bc"]/x$Estimate[, "se.us"]
  t_rb =x$Estimate[, "tau.bc"]/x$Estimate[, "se.rb"]
  
  pv_us = 2*pnorm(-abs(t_us))
  pv_bc = 2*pnorm(-abs(t_bc))
  pv_rb = 2*pnorm(-abs(t_rb))
  
  
  if (!is.null(x$tau_T)) {
    
    cat(paste("First-stage estimates.","\n", sep=""))
    cat(paste("","\n", sep=""))    
    
    ### print output

    if (!is.null(x$detail) | !is.null(x$all)) {
    
    llength = 14 + 10 + 8 + 10 + 10 +  25
    
    cat(paste(rep("=", llength), collapse="")); cat("\n")
    
    cat(format("Method"          , width=14, justify="right"))
    cat(format("Coef."           , width=10, justify="right"))
    cat(format("Std. Err."       , width=10 , justify="right"))
    cat(format("z"               , width=10, justify="right"))
    cat(format("P>|z|"           , width=10, justify="right"))
    cat(format(paste("[ ", x$level, "%", " C.I. ]", sep=""), width=25, justify="centre"))
    cat("\n")
    
    cat(paste(rep("=", llength), collapse="")); cat("\n")
    } else {
      
      llength = 14 + 10  + 10 + 10 + 25
      
      cat(paste(rep("=", llength), collapse="")); cat("\n")
      
      cat(format(""          , width=14, justify="right"))
      cat(format("Point"           , width=10, justify="right"))
      cat(format("Robust Inference"               , width=20, justify="right"))
      cat("\n")
      
      cat(format(""          , width=14, justify="right"))
      cat(format("Estimate"           , width=10, justify="right"))
      cat(format("z"               , width=10, justify="right"))
      cat(format("P>|z|"           , width=10, justify="right"))
      cat(format(paste("[ ", x$level, "%", " C.I. ]", sep=""), width=25, justify="centre"))
      cat("\n")
      
      cat(paste(rep("=", llength), collapse="")); cat("\n")
    
    
      cat(format("Rd Effect", width=14, justify="right"))
      cat(format(      sprintf("%3.3f", x$tau_T[1]) , width=10, justify="right"))
      cat(format(sprintf("%3.3f", x$t_T[3]) , width=10, justify="right"))
      cat(format(sprintf("%3.3f", x$pv_T[3]), width=10, justify="right"))
      cat(format(paste("[", sprintf("%3.3f", x$ci_T[3,1]), " , ", sep="")  , width=14, justify="right"))
      cat(format(paste(sprintf("%3.3f", x$ci_T[3,2]), "]", sep=""), width=11, justify="left"))
     cat("\n")
    }
    
    if (!is.null(x$detail)) {
        
    cat(format("Conventional", width=14, justify="right"))
    cat(format(      sprintf("%3.3f", x$tau_T[1]) , width=10, justify="right"))
    cat(format(paste(sprintf("%3.3f", x$se_T[1]), sep=""), width=10, justify="right"))
    cat(format(      sprintf("%3.3f", x$t_T[1]) , width=10, justify="right"))
    cat(format(      sprintf("%3.3f", x$pv_T[1]), width=10, justify="right"))
    cat(format(paste("[", sprintf("%3.3f", x$ci_T[1,1]), " , ", sep="")  , width=14, justify="right"))
    cat(format(paste(     sprintf("%3.3f", x$ci_T[1,2]), "]", sep=""), width=11, justify="left"))
    cat("\n")

        
      cat(format("Robust", width=14, justify="right"))
      cat(format("-", width=10, justify="right"))
      cat(format("-", width=10, justify="right"))
       cat(format(sprintf("%3.3f", x$t_T[3]) , width=10, justify="right"))
      cat(format(sprintf("%3.3f", x$pv_T[3]), width=10, justify="right"))
      cat(format(paste("[", sprintf("%3.3f", x$ci_T[3,1]), " , ", sep="")  , width=14, justify="right"))
      cat(format(paste(sprintf("%3.3f", x$ci_T[3,2]), "]", sep=""), width=11, justify="left"))
      cat("\n") 
      }
      
    if (!is.null(x$all)) {
      
      cat(format("Conventional", width=14, justify="right"))
      cat(format(      sprintf("%3.3f", x$tau_T[1]) , width=10, justify="right"))
      cat(format(paste(sprintf("%3.3f", x$se_T[1]), sep=""), width=10, justify="right"))
      cat(format(      sprintf("%3.3f", x$t_T[1]) , width=10, justify="right"))
      cat(format(      sprintf("%3.3f", x$pv_T[1]), width=10, justify="right"))
      cat(format(paste("[", sprintf("%3.3f", x$ci_T[1,1]), " , ", sep="")  , width=14, justify="right"))
      cat(format(paste(     sprintf("%3.3f", x$ci_T[1,2]), "]", sep=""), width=11, justify="left"))
      cat("\n")
      
      cat(format("Bias-Corrected", width=14, justify="right"))
      cat(format(sprintf("%3.3f", x$tau_T[2]) , width=10, justify="right"))
      cat(format(paste(sprintf("%3.3f", x$se_T[2]), sep=""), width=10, justify="right"))
      cat(format(sprintf("%3.3f", x$t_T[2]) , width=10, justify="right"))
      cat(format(sprintf("%3.3f", x$pv_T[2]), width=10, justify="right"))
      cat(format(paste("[", sprintf("%3.3f", x$ci_T[2,1]), " , ", sep="")  , width=14, justify="right"))
      cat(format(paste(sprintf("%3.3f", x$ci_T[2,2]), "]", sep=""), width=11, justify="left"))
      cat("\n")
      
      cat(format("Robust", width=14, justify="right"))
      cat(format(sprintf("%3.3f", x$tau_T[3]) , width=10, justify="right"))
      cat(format(paste(sprintf("%3.3f", x$se_T[3]), sep=""), width=10, justify="right"))
      cat(format(sprintf("%3.3f", x$t_T[3]) , width=10, justify="right"))
      cat(format(sprintf("%3.3f", x$pv_T[3]), width=10, justify="right"))
      cat(format(paste("[", sprintf("%3.3f", x$ci_T[3,1]), " , ", sep="")  , width=14, justify="right"))
      cat(format(paste(sprintf("%3.3f", x$ci_T[3,2]), "]", sep=""), width=11, justify="left"))
      cat("\n")
    }
    
    cat(paste(rep("=", llength), collapse="")); cat("\n")
    
    cat(paste("","\n", sep="")) 
    cat(paste("Treatment effect estimates.","\n", sep=""))
    cat(paste("","\n", sep=""))   
  }
  
  ### print output
  if (!is.null(x$detail) | !is.null(x$all)) {
    
    llength = 14 + 10 + 8 + 10 + 10 + 10 + 25
    cat(paste(rep("=", llength), collapse="")); cat("\n")
    
    cat(format("Method"          , width=14, justify="right"))
    cat(format("Coef."           , width=10, justify="right"))
    cat(format("Std. Err."       , width=10 , justify="right"))
    cat(format("z"               , width=10, justify="right"))
    cat(format("P>|z|"           , width=10, justify="right"))
    cat(format(paste("[ ", x$level, "%", " C.I. ]", sep=""), width=25, justify="centre"))
    cat("\n")
    
    cat(paste(rep("=", llength), collapse="")); cat("\n")
  } else {
    
    llength = 14 + 10 + 10+ 10+ 25
    cat(paste(rep("=", llength), collapse="")); cat("\n")
    
    
    cat(format(""          , width=14, justify="right"))
    cat(format("Point"           , width=10, justify="right"))
    cat(format("Robust Inference"               , width=20, justify="right"))
    cat("\n")
    
    
    cat(format(""               , width=14, justify="right"))
    cat(format("Estimate"       , width=10, justify="right"))
    cat(format("z"              , width=10, justify="right"))
    cat(format("P>|z|"          , width=10, justify="right"))
    cat(format(paste("[ ", x$level, "%", " C.I. ]", sep=""), width=25, justify="centre"))
    cat("\n")
    
    cat(paste(rep("-", llength), collapse="")); cat("\n")
  
    cat(format("RD Effect", width=14, justify="right"))
    cat(format(sprintf("%3.3f", x$Estimate[1, "tau.us"]) , width=10, justify="right"))
    cat(format(sprintf("%3.3f", t_rb) , width=10, justify="right"))
    cat(format(sprintf("%3.3f", pv_rb), width=10, justify="right"))
    cat(format(paste("[", sprintf("%3.3f", CI_rb_l[1]), " , ", sep="")  , width=14, justify="right"))
    cat(format(paste(sprintf("%3.3f", CI_rb_r[1]), "]", sep=""), width=11, justify="left"))
    cat("\n") 
    
  }
    
    if (!is.null(x$detail)) {
      
    cat(format("Conventional", width=14, justify="right"))
    cat(format(sprintf("%3.3f", x$Estimate[1, "tau.us"]) , width=10, justify="right"))
    cat(format(paste(sprintf("%3.3f", x$Estimate[1, "se.us"]), sep=""), width=10, justify="right"))
    cat(format(sprintf("%3.3f", t_us) , width=10, justify="right"))
    cat(format(sprintf("%3.3f", pv_us), width=10, justify="right"))
    cat(format(paste("[", sprintf("%3.3f", CI_us_l[1]), " , ", sep="")  , width=14, justify="right"))
    cat(format(paste(sprintf("%3.3f", CI_us_r[1]), "]", sep=""), width=11, justify="left"))
    cat("\n")
  
      cat(format("Robust", width=14, justify="right"))
      cat(format("-", width=10, justify="right"))
      cat(format("-", width=10, justify="right"))
      cat(format(sprintf("%3.3f", t_rb) , width=10, justify="right"))
      cat(format(sprintf("%3.3f", pv_rb), width=10, justify="right"))
      cat(format(paste("[", sprintf("%3.3f", CI_rb_l[1]), " , ", sep="")  , width=14, justify="right"))
      cat(format(paste(sprintf("%3.3f", CI_rb_r[1]), "]", sep=""), width=11, justify="left"))
      cat("\n") 
  
    }      
      
      if (!is.null(x$all)) {
        
        cat(format("Conventional", width=14, justify="right"))
        cat(format(sprintf("%3.3f", x$Estimate[1, "tau.us"]) , width=10, justify="right"))
        cat(format(paste(sprintf("%3.3f", x$Estimate[1, "se.us"]), sep=""), width=10, justify="right"))
        cat(format(sprintf("%3.3f", t_us) , width=10, justify="right"))
        cat(format(sprintf("%3.3f", pv_us), width=10, justify="right"))
        cat(format(paste("[", sprintf("%3.3f", CI_us_l[1]), " , ", sep="")  , width=14, justify="right"))
        cat(format(paste(sprintf("%3.3f", CI_us_r[1]), "]", sep=""), width=11, justify="left"))
        cat("\n")
        
      cat(format("Bias-Corrected", width=14, justify="right"))
      cat(format(sprintf("%3.3f", x$Estimate[1, "tau.bc"]) , width=10, justify="right"))
      cat(format(paste(sprintf("%3.3f", x$Estimate[1, "se.us"]), sep=""), width=10, justify="right"))
      cat(format(sprintf("%3.3f", t_bc) , width=10, justify="right"))
      cat(format(sprintf("%3.3f", pv_bc), width=10, justify="right"))
      cat(format(paste("[", sprintf("%3.3f", CI_bc_l[1]), " , ", sep="")  , width=14, justify="right"))
      cat(format(paste(sprintf("%3.3f", CI_bc_r[1]), "]", sep=""), width=11, justify="left"))
      cat("\n")
  
      cat(format("Robust", width=14, justify="right"))
      cat(format(sprintf("%3.3f", x$Estimate[1, "tau.bc"]) , width=10, justify="right"))
      cat(format(paste(sprintf("%3.3f", x$Estimate[1, "se.rb"]), sep=""), width=10, justify="right"))
      cat(format(sprintf("%3.3f", t_rb) , width=10, justify="right"))
      cat(format(sprintf("%3.3f", pv_rb), width=10, justify="right"))
      cat(format(paste("[", sprintf("%3.3f", CI_rb_l[1]), " , ", sep="")  , width=14, justify="right"))
      cat(format(paste(sprintf("%3.3f", CI_rb_r[1]), "]", sep=""), width=11, justify="left"))
      cat("\n")
    }
    
  cat(paste(rep("=", llength), collapse="")); cat("\n")
}


tidy.rdrobust <- function(object, ...){
  ret <- data.frame(term = row.names(object$coef), 
                    estimate  = object$coef[, 1], 
                    std.error = object$se[, 1], 
                    statistic = object$z[, 1],
                    p.value   = object$pv[, 1], 
                    conf.low  = object$ci[,1],
                    conf.high = object$ci[, 2])
  row.names(ret) <- NULL
  ret
}

glance.rdrobust <- function(object, ...){
  ret <- data.frame(nobs.left  = object$N[1],
                    nobs.right = object$N[2],
                    nobs.effective.left  = object$N_h[1],
                    nobs.effective.right = object$N_h[2],
                    cutoff = object$c,
                    order.regression = object$q,
                    order.bias = object$q,
                    kernel  = object$kernel,
                    bwselect = object$bwselect)
  ret
}

