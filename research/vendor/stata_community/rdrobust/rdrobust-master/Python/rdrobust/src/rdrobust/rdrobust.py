#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul  7 19:01:48 2021

@author: rmasini
"""

import numpy as np
import pandas  as pd
import math
import scipy.stats as sct
from rdrobust.rdbwselect import rdbwselect
from rdrobust.funs import *
     
def rdrobust(y, x, c = None, fuzzy = None, deriv = None,
             p = None, q = None, h = None, b = None, rho = None, 
             covs = None, covs_drop = True,
             kernel = "tri", weights = None, bwselect = "mserd",
             vce = "nn", cluster = None, nnmatch = 3, level = 95, 
             scalepar = 1, scaleregul = 1, sharpbw = False, 
             all = None, subset = None, masspoints = "adjust",
             bwcheck = None, bwrestrict = True, stdvars = False):
    
    '''
    Implements local polynomial Regression Discontinuity (RD) point estimators with robust bias-corrected confidence intervals and inference procedures developed in Calonico, Cattaneo and Titiunik (2014a), Calonico, Cattaneo and Farrell (2018), Calonico, Cattaneo, Farrell and Titiunik (2019), and Calonico, Cattaneo and Farrell (2020). It also computes alternative estimation and inference procedures available in the literature.
   
    Parameters
    ----------
    y: array	
    is the dependent variable.
    
    x	
    is the running variable (a.k.a. score or forcing variable).
    
    c	
    specifies the RD cutoff in x; default is c = 0.
    
    fuzzy	
    specifies the treatment status variable used to implement fuzzy RD estimation (or Fuzzy Kink RD if deriv=1 is also specified). Default is Sharp RD design and hence this option is not used.
    
    deriv	
    specifies the order of the derivative of the regression functions to be estimated. Default is deriv=0 (for Sharp RD, or for Fuzzy RD if fuzzy is also specified). Setting deriv=1 results in estimation of a Kink RD design (up to scale), or Fuzzy Kink RD if fuzzy is also specified.
    
    p	
    specifies the order of the local-polynomial used to construct the point-estimator; default is p = 1 (local linear regression).
    
    q	
    specifies the order of the local-polynomial used to construct the bias-correction; default is q = 2 (local quadratic regression).
    
    h	
    specifies the main bandwidth used to construct the RD point estimator. If not specified, bandwidth h is computed by the companion command rdbwselect. If two bandwidths are specified, the first bandwidth is used for the data below the cutoff and the second bandwidth is used for the data above the cutoff.
    
    b	
    specifies the bias bandwidth used to construct the bias-correction estimator. If not specified, bandwidth b is computed by the companion command rdbwselect. If two bandwidths are specified, the first bandwidth is used for the data below the cutoff and the second bandwidth is used for the data above the cutoff.
    
    rho	
    specifies the value of rho, so that the bias bandwidth b equals h/rho. Default is rho = 1 if h is specified but b is not.
    
    covs	
    specifies additional covariates to be used for estimation and inference.
    
    covs_drop	
    if TRUE, it checks for collinear additional covariates and drops them. Default is TRUE.
    
    kernel	
    is the kernel function used to construct the local-polynomial estimator(s). Options are triangular (default option), epanechnikov and uniform.
    
    weights	
    is the variable used for optional weighting of the estimation procedure. The unit-specific weights multiply the kernel function.
    
    bwselect	
    specifies the bandwidth selection procedure to be used. By default it computes both h and b, unless rho is specified, in which case it only computes h and sets b=h/rho.
    
    Options are:
    
    mserd one common MSE-optimal bandwidth selector for the RD treatment effect estimator.
    
    msetwo two different MSE-optimal bandwidth selectors (below and above the cutoff) for the RD treatment effect estimator.
    
    msesum one common MSE-optimal bandwidth selector for the sum of regression estimates (as opposed to difference thereof).
    
    msecomb1 for min(mserd,msesum).
    
    msecomb2 for median(msetwo,mserd,msesum), for each side of the cutoff separately.
    
    cerrd one common CER-optimal bandwidth selector for the RD treatment effect estimator.
    
    certwo two different CER-optimal bandwidth selectors (below and above the cutoff) for the RD treatment effect estimator.
    
    cersum one common CER-optimal bandwidth selector for the sum of regression estimates (as opposed to difference thereof).
    
    cercomb1 for min(cerrd,cersum).
    
    cercomb2 for median(certwo,cerrd,cersum), for each side of the cutoff separately.
    
    Note: MSE = Mean Square Error; CER = Coverage Error Rate. Default is bwselect=mserd. For details on implementation see Calonico, Cattaneo and Titiunik (2014a), Calonico, Cattaneo and Farrell (2018), and Calonico, Cattaneo, Farrell and Titiunik (2019), and the companion software articles.
    
    vce	
    specifies the procedure used to compute the variance-covariance matrix estimator. Options are:
    
    nn for heteroskedasticity-robust nearest neighbor variance estimator with nnmatch the (minimum) number of neighbors to be used.
    
    hc0 for heteroskedasticity-robust plug-in residuals variance estimator without weights.
    
    hc1 for heteroskedasticity-robust plug-in residuals variance estimator with hc1 weights.
    
    hc2 for heteroskedasticity-robust plug-in residuals variance estimator with hc2 weights.
    
    hc3 for heteroskedasticity-robust plug-in residuals variance estimator with hc3 weights.
    
    Default is vce=nn.
    
    cluster	
    indicates the cluster ID variable used for cluster-robust variance estimation with degrees-of-freedom weights. By default it is combined with vce=nn for cluster-robust nearest neighbor variance estimation. Another option is plug-in residuals combined with vce=hc0.
    
    nnmatch	
    to be combined with for vce=nn for heteroskedasticity-robust nearest neighbor variance estimator with nnmatch indicating the minimum number of neighbors to be used. Default is nnmatch=3
    
    level	
    sets the confidence level for confidence intervals; default is level = 95.
    
    scalepar	
    specifies scaling factor for RD parameter of interest. This option is useful when the population parameter of interest involves a known multiplicative factor (e.g., sharp kink RD). Default is scalepar = 1 (no scaling).
    
    scaleregul	
    specifies scaling factor for the regularization term added to the denominator of the bandwidth selectors. Setting scaleregul = 0 removes the regularization term from the bandwidth selectors; default is scaleregul = 1.
    
    sharpbw	
    option to perform fuzzy RD estimation using a bandwidth selection procedure for the sharp RD model. This option is automatically selected if there is perfect compliance at either side of the cutoff.
    
    all	
    if specified, rdrobust reports three different procedures:
    
    (i) conventional RD estimates with conventional standard errors.
    
    (ii) bias-corrected estimates with conventional standard errors.
    
    (iii) bias-corrected estimates with robust standard errors.
    
    subset	
    an optional vector specifying a subset of observations to be used.
    
    masspoints	
    checks and controls for repeated observations in the running variable. Options are:
    
    (i) off: ignores the presence of mass points;
    
    (ii) check: looks for and reports the number of unique observations at each side of the cutoff.
    
    (iii) adjust: controls that the preliminary bandwidths used in the calculations contain a minimal number of unique observations. By default it uses 10 observations, but it can be manually adjusted with the option bwcheck).
    
    Default option is masspoints=adjust.
    
    bwcheck	
    if a positive integer is provided, the preliminary bandwidth used in the calculations is enlarged so that at least bwcheck unique observations are used.
    
    bwrestrict	
    if TRUE, computed bandwidths are restricted to lie within the range of x; default is bwrestrict = TRUE.
    
    stdvars	
    if TRUE, x and y are standardized before computing the bandwidths; default is stdvars = FALSE.
    
    Returns
    -------
    N	
    vector with the sample sizes used to the left and to the right of the cutoff.
    
    N_h	
    vector with the effective sample sizes used to the left and to the right of the cutoff.
    
    c	
    cutoff value.
    
    p	
    order of the polynomial used for estimation of the regression function.
    
    q	
    order of the polynomial used for estimation of the bias of the regression function.
    
    bws	
    matrix containing the bandwidths used.
    
    tau_cl	
    conventional local-polynomial estimate to the left and to the right of the cutoff.
    
    tau_bc	
    bias-corrected local-polynomial estimate to the left and to the right of the cutoff.
    
    coef	
    vector containing conventional and bias-corrected local-polynomial RD estimates.
    
    se	
    vector containing conventional and robust standard errors of the local-polynomial RD estimates.
    
    bias	
    estimated bias for the local-polynomial RD estimator below and above the cutoff.
    
    beta_p_l	
    conventional p-order local-polynomial estimates to the left of the cutoff.
    
    beta_p_r	
    conventional p-order local-polynomial estimates to the right of the cutoff.
    
    V_cl_l	
    conventional variance-covariance matrix estimated below the cutoff.
    
    V_cl_r	
    conventional variance-covariance matrix estimated above the cutoff.
    
    V_rb_l	
    robust variance-covariance matrix estimated below the cutoff.
    
    V_rb_r	
    robust variance-covariance matrix estimated above the cutoff.
    
    pv	
    vector containing the p-values associated with conventional, bias-corrected and robust local-polynomial RD estimates.
    
    ci	
    matrix containing the confidence intervals associated with conventional, bias-corrected and robust local-polynomial RD estimates.
    
    
    See Also
    --------
    rdbwselect, rdplot
    
    Example
    ------- 
    >>> x = numpy.random.uniform(low=-1, high=1, size=1000)
    >>> y = 5+3*x+2*(x>=0) + numpy.random.uniform(size = 1000)
    >>> rdrobust(y,x)
    '''
    
    # Check for errors in the INPUT
    if p is None and deriv is not None: p = deriv + 1
    if p is None: p = 1
    elif not np.isscalar(p) or p not in range(21):
        raise Exception('Polynomial order p incorrectly specified.')
        
    if q is None: q = p + 1
    elif not np.isscalar(q) or q not in range(21) or q<p:
        raise Exception('Polynomial order (for bias correction) q incorrectly specified')
    
    if deriv is None: deriv = 0
    elif deriv not in range(21) or deriv>p:
        raise Exception('Derivative order incorrectly specified')
    
    kernel   = kernel.lower()
    kernel_list = ['uni','uniform','tri','triangular','epa','epanechnikov','']
    if kernel not in kernel_list:   
        raise Exception("kernel incorrectly specified")
    
    bwselect = bwselect.lower()
    bw_list = ['mserd','msetwo','msesum','msecomb1','msecomb2','cerrd',
               'certwo','cersum','cercomb1','cercomb2','']
    if bwselect not in bw_list:
        raise Exception("bwselect incorrectly specified")
    elif bwselect=="cct" or bwselect=="ik" or bwselect=="cv":
        raise Exception("bwselect options IK, CCT and CV have been depricated. Please see help for new options")  
    
    vce = vce.lower()
    vce_list = ['nn','hc0','hc1','hc2','hc3','']
    if vce not in vce_list:
        raise Exception("vce incorrectly specified")
    
    if level>100 or level<=0:
        raise Exception("level should be set between 0 and 100")
        
    if rho is not None and rho<0:
        raise Exception("rho should be greater than 0")
    
    #=========================================================================
    # Tidy the Input and remove NAN

    x = np.array(x).reshape(-1,1)
    y = np.array(y).reshape(-1,1)
    if subset is not None:
        x = x[subset]
        y = y[subset]
    na_ok = complete_cases(x) & complete_cases(y)
    
    if cluster is not None:
        cluster = np.array(cluster).reshape(-1,1)
        if subset is not None:
            cluster = cluster[subset]
        if np.issubdtype(cluster.dtype, np.number):
            na_ok = na_ok & complete_cases(cluster)
    
    if covs is not None:
        try: covs_names = list(covs.columns)
        except: covs_names = ['z' + str(i+1) for i in range(ncol(covs))]         
        covs = np.array(covs).reshape(len(covs),-1)  
        covs_order = np.argsort([len(i) for i in covs_names])
        covs = covs[:,covs_order]
        covs_names = [covs_names[i] for i in covs_order]
        if subset is not None:
            covs = covs[subset,:]
        na_ok = na_ok & complete_cases(covs) 
    
    if fuzzy is not None:
        fuzzy = np.array(fuzzy).reshape(-1,1)
        if subset is not None:
            fuzzy = fuzzy[subset]
        na_ok = na_ok & complete_cases(fuzzy)
  
    if weights is not None:
        weights = np.array(weights).reshape(-1,1)
        if subset is not None:
            weights = weights[subset]
        na_ok = na_ok & complete_cases(weights) & (weights>=0).reshape(-1,)
    
    x = x[na_ok]
    y = y[na_ok]
    
    if covs is not None: covs = covs[na_ok,:]
    if fuzzy is not None: fuzzy   = fuzzy[na_ok]
    if cluster is not None: cluster = cluster[na_ok]
    if weights is not None: weights = weights[na_ok]
  
    if masspoints is None: masspoints = False

    if vce == "nn" or masspoints == "check" or masspoints == "adjust" : 
        order_x = np.argsort(x[:,0])
        x = x[order_x]
        y = y[order_x]
        if covs is not None: covs = covs[order_x,:]
        if fuzzy is not None: fuzzy   = fuzzy[order_x]
        if cluster is not None: cluster = cluster[order_x]
        if weights is not None: weights = weights[order_x]
    
    if c is None: c = 0
    less_c = x<c
    X_l = x[less_c]
    X_r = x[np.invert(less_c)]
    Y_l = y[less_c]
    Y_r = y[np.invert(less_c)]
    x_min = np.min(x)  
    x_max = np.max(x)
    if c<=x_min or c>=x_max:
        raise Exception("c should be set within the range of x")
    range_l = np.abs(np.max(X_l)-np.min(X_l)) 
    range_r = np.abs(np.max(X_r)-np.min(X_r))
    N_l = len(X_l)  
    N_r = len(X_r)
    N = N_r + N_l
    quant = -sct.norm.ppf(q = np.abs((1-(level/100))/2))
    
    vce_type = "NN"
    if vce=="hc0": vce_type = "HC0"
    if vce=="hc1": vce_type = "HC1"
    if vce=="hc2": vce_type = "HC2"
    if vce=="hc3": vce_type = "HC3"
    if cluster is not None: vce_type = "Cluster"
    
    #===================================================================================
    # Check for COLLINEARITY
    
    covs_drop_coll = dZ = 0
    if covs_drop: covs_drop_coll = 1 
    if covs is not None:
        dZ = ncol(covs)
        if covs_drop: 
            covs_check = covs_drop_fun(covs)
            if ncol(covs_check) < dZ:
                covs = covs_check
                dZ = ncol(covs)
    # ================================================================
                  
    if h is not None: 
        bwselect = "Manual"
        if rho is None:
            rho = 1
            if b is None:
                b = h
        else:
            b = h/rho
            
    if N<20:
        print("Not enough observations to perform bandwidth calculations. Estimates computed using entire sample")
        h = b = np.max(range_l,range_r)
        bwselect = "Manual"
  
    if kernel=="epanechnikov" or kernel=="epa":
        kernel_type = "Epanechnikov"
    elif kernel=="uniform" or kernel=="uni":
        kernel_type = "Uniform"
    else:
        kernel_type = "Triangular"

    vce_type = "NN"
    if vce=="hc0": vce_type = "HC0"
    if vce=="hc1": vce_type = "HC1"
    if vce=="hc2": vce_type = "HC2"
    if vce=="hc3": vce_type = "HC3"
    if vce=="cluster": vce_type = "Cluster"
    if vce=="nncluster": vce_type = "NNcluster"
  
    M_l = N_l
    M_r = N_r
    if masspoints=="check" or masspoints=="adjust":
      X_uniq_l = np.sort(np.unique(X_l))[::-1]
      X_uniq_r = np.unique(X_r)
      M_l = len(X_uniq_l)

      M_r = len(X_uniq_r)
      mass_l = 1-M_l/N_l
      mass_r = 1-M_r/N_r				
      if mass_l>=0.1 or mass_r>=0.1:
        print("Mass points detected in the running variable.")
        if masspoints=="check": print("Try using option masspoints=adjust.")
        if bwcheck is None and masspoints=="adjust": bwcheck = 10

    
    ######### Calculate bandwidth

    if h is None:
        rdbws = rdbwselect(y=y, x=x, c=c, fuzzy=fuzzy,  deriv=deriv, p=p, q=q,
                           covs=covs, covs_drop=covs_drop, kernel=kernel,  weights=weights,
                           bwselect=bwselect,  bwcheck = bwcheck, bwrestrict=bwrestrict,
                           vce=vce, cluster=cluster,  nnmatch=nnmatch,  
                           scaleregul=scaleregul, sharpbw = sharpbw, subset=subset,
                           all=False, masspoints=masspoints, stdvars=stdvars,
                           prchk=False)
        h_l, h_r, b_l, b_r = rdbws.bws.iloc[0].values
        if rho is not None:
            b_l = h_l/rho
            b_r = h_r/rho
    else:
        if np.isscalar(h): h_l = h_r = h
        elif len(h)==2: h_l, h_r = h
        if b is None:      
            b_l = h_l
            b_r = h_r
        else:
          if np.isscalar(b): b_l = b_r = b
          elif len(b)==2: b_l, b_r = b
    w_h_l = rdrobust_kweight(X_l,c,h_l,kernel)	
    w_h_r = rdrobust_kweight(X_r,c,h_r,kernel)
    w_b_l = rdrobust_kweight(X_l,c,b_l,kernel)	
    w_b_r = rdrobust_kweight(X_r,c,b_r,kernel)
    
    if weights is not None:
        fw_l = weights[x<c]  
        fw_r = weights[x>=c]
        w_h_l = fw_l*w_h_l
        w_h_r = fw_r*w_h_r
        w_b_l = fw_l*w_b_l
        w_b_r = fw_r*w_b_r			
      
    ind_h_l = w_h_l> 0
    ind_h_r = w_h_r> 0
    ind_b_l = w_b_l> 0
    ind_b_r = w_b_r> 0
    N_h_l = np.sum(ind_h_l)
    N_b_l = np.sum(ind_b_l)
    N_h_r = np.sum(ind_h_r)
    N_b_r = np.sum(ind_b_r)
    
    ind_l = ind_b_l 
    ind_r = ind_b_r
    if h_l>b_l: ind_l = ind_h_l   
    if h_r>b_r: ind_r = ind_h_r   
    
    eN_l = np.sum(ind_l)
    eN_r = np.sum(ind_r)
    eY_l  = Y_l[ind_l]
    eY_r  = Y_r[ind_r]
    eX_l  = X_l[ind_l]
    eX_r  = X_r[ind_r]
    W_h_l = w_h_l[ind_l].reshape(-1,1)
    W_h_r = w_h_r[ind_r].reshape(-1,1)
    W_b_l = w_b_l[ind_l].reshape(-1,1)
    W_b_r = w_b_r[ind_r].reshape(-1,1)
    
    edups_l = np.zeros(eN_l).astype(int)
    edupsid_l = np.zeros(eN_l).astype(int)
    edups_r = np.zeros(eN_r).astype(int)
    edupsid_r = np.zeros(eN_r).astype(int)
    if vce=="nn":
        aux_l  = pd.DataFrame({'nn_l': np.ones(eN_l), 'eX_l': eX_l })
        edups_l   = aux_l.groupby('eX_l')['nn_l'].transform('sum').values.astype(int)
        edupsid_l = aux_l.groupby('eX_l')['nn_l'].transform('cumsum').values.astype(int)

        aux_r  = pd.DataFrame({'nn_r': np.ones(eN_r), 'eX_r': eX_r })
        edups_r   = aux_r.groupby('eX_r')['nn_r'].transform('sum').values.astype(int)
        edupsid_r = aux_r.groupby('eX_r')['nn_r'].transform('cumsum').values.astype(int)

    u_l = ((eX_l-c)/h_l).reshape(-1,1)
    u_r = ((eX_r-c)/h_r).reshape(-1,1)
    R_q_l = nanmat(eN_l,q+1)
    R_q_r = nanmat(eN_r,q+1)
    for j in range(q+1):
        R_q_l[:,j] = (eX_l-c)**j 
        R_q_r[:,j] = (eX_r-c)**j
    R_p_l = R_q_l[:,:(p+1)]
    R_p_r = R_q_r[:,:(p+1)]
    
    # Computing RD estimates
  
    L_l = crossprod(R_p_l*W_h_l,u_l**(p+1))
    L_r = crossprod(R_p_r*W_h_r,u_r**(p+1)) 
    invG_q_l  = qrXXinv((np.sqrt(W_b_l)*R_q_l))
    invG_q_r  = qrXXinv((np.sqrt(W_b_r)*R_q_r))
    invG_p_l  = qrXXinv((np.sqrt(W_h_l)*R_p_l))
    invG_p_r  = qrXXinv((np.sqrt(W_h_r)*R_p_r))
    e_p1 = np.zeros((q+1,1))
    e_p1[p+1] = 1
    e_v  = np.zeros((p+1,1))
    e_v[deriv] = 1
    Q_q_l = ((R_p_l*W_h_l).T - np.matmul(h_l**(p+1)*np.matmul(L_l,(e_p1).T),((np.matmul(invG_q_l,R_q_l.T)).T*W_b_l).T)).T
    Q_q_r = ((R_p_r*W_h_r).T - np.matmul(h_r**(p+1)*np.matmul(L_r,(e_p1).T),((np.matmul(invG_q_r,R_q_r.T)).T*W_b_r).T)).T
    D_l = eY_l.copy()
    D_r = eY_r.copy()
    eC_l = eC_r = eT_l = eT_r = eZ_l = eZ_r = None
    
    dT = 0
    if fuzzy is not None:
        dT = 1
        T_l  = fuzzy[x<c]
        eT_l  = T_l[ind_l]
        T_r  = fuzzy[x>=c]
        eT_r  = T_r[ind_r]
        D_l  = np.column_stack((D_l,eT_l))
        D_r = np.column_stack((D_r,eT_r))
  
    if covs is not None:
        Z_l  = covs[(x<c).reshape(-1),:]
        eZ_l = Z_l[ind_l,:]
        Z_r  = covs[(x>=c).reshape(-1),:]
        eZ_r = Z_r[ind_r,:]
        D_l  = np.column_stack((D_l,eZ_l))
        D_r = np.column_stack((D_r,eZ_r))
        U_p_l = crossprod(R_p_l*W_h_l,D_l)
        U_p_r = crossprod(R_p_r*W_h_r,D_r)
  
    if cluster is not None:
        C_l  = cluster[x<c]
        C_r = cluster[x>=c]
        eC_l  = C_l[ind_l]
        eC_r  = C_r[ind_r]

    
    beta_p_l = tomat(np.matmul(invG_p_l,crossprod(R_p_l*W_h_l,D_l)))
    beta_q_l = tomat(np.matmul(invG_q_l,crossprod(R_q_l*W_b_l,D_l)))
    beta_bc_l = tomat(np.matmul(invG_p_l,crossprod(Q_q_l,D_l))) 
    beta_p_r = tomat(np.matmul(invG_p_r,crossprod(R_p_r*W_h_r,D_r)))
    beta_q_r = tomat(np.matmul(invG_q_r,crossprod(R_q_r*W_b_r,D_r)))
    beta_bc_r = tomat(np.matmul(invG_p_r,crossprod(Q_q_r,D_r)))
    beta_p  = beta_p_r  - beta_p_l
    beta_bc = beta_bc_r - beta_bc_l
    

    if covs is None:
        tau_cl = scalepar*math.factorial(deriv)*beta_p[deriv,0]
        tau_Y_cl = tau_cl.copy()
        tau_bc = scalepar*math.factorial(deriv)*beta_bc[deriv,0]
        tau_Y_bc = tau_bc.copy()
        s_Y = 1        
        tau_Y_cl_l = scalepar*math.factorial(deriv)*beta_p_l[deriv,0]
        tau_Y_cl_r = scalepar*math.factorial(deriv)*beta_p_r[deriv,0]
        tau_Y_bc_l = scalepar*math.factorial(deriv)*beta_bc_l[deriv,0]
        tau_Y_bc_r = scalepar*math.factorial(deriv)*beta_bc_r[deriv,0]
        bias_l = tau_Y_cl_l-tau_Y_bc_l
        bias_r = tau_Y_cl_r-tau_Y_bc_r 
      
        if fuzzy is not None:
            tau_T_cl = math.factorial(deriv)*beta_p[deriv,1]
            tau_T_bc = math.factorial(deriv)*beta_bc[deriv,1]
            tau_cl   = tau_Y_cl/tau_T_cl
            s_Y      = np.array([1/tau_T_cl , -(tau_Y_cl/tau_T_cl**2)])
            B_F      = np.array([tau_Y_cl-tau_Y_bc , tau_T_cl-tau_T_bc])
            tau_bc   = tau_cl - np.matmul(s_Y.T,B_F)
            
            tau_T_cl_l = math.factorial(deriv)*beta_p_l[deriv,1]
            tau_T_cl_r = math.factorial(deriv)*beta_p_l[deriv,1]
            tau_T_bc_l = math.factorial(deriv)*beta_bc_l[deriv,1]
            tau_T_bc_r = math.factorial(deriv)*beta_bc_r[deriv,1]
            B_F_l = np.array([tau_Y_cl_l-tau_Y_bc_l, tau_T_cl_l-tau_T_bc_l])
            B_F_r = np.array([tau_Y_cl_r-tau_Y_bc_r, tau_T_cl_r-tau_T_bc_r])
            bias_l = np.matmul(s_Y.T,B_F_l)
            bias_r = np.matmul(s_Y.T,B_F_r)
    else:
        ZWD_p_l  = crossprod(eZ_l*W_h_l,D_l)
        ZWD_p_r  = crossprod(eZ_r*W_h_r,D_r)
        colsZ = np.arange(1+dT, max(2+dT+dZ-1,2+dT))
        UiGU_p_l =  crossprod(U_p_l[:,colsZ],np.matmul(invG_p_l,U_p_l)) 
        UiGU_p_r =  crossprod(U_p_r[:,colsZ],np.matmul(invG_p_r,U_p_r))  
        ZWZ_p_l = ZWD_p_l[:,colsZ] - UiGU_p_l[:,colsZ] 
        ZWZ_p_r = ZWD_p_r[:,colsZ] - UiGU_p_r[:,colsZ]     
        ZWY_p_l = ZWD_p_l[:,:(1+dT)] - UiGU_p_l[:,:(1+dT)] 
        ZWY_p_r = ZWD_p_r[:,:(1+dT)] - UiGU_p_r[:,:(1+dT)]      
        ZWZ_p = ZWZ_p_r + ZWZ_p_l
        ZWY_p = ZWY_p_r + ZWY_p_l
        if covs_drop_coll == 0:
            gamma_p = np.matmul(inv_chol(ZWZ_p),ZWY_p)
        elif covs_drop_coll == 1:
            gamma_p = np.matmul(np.linalg.pinv(ZWZ_p),ZWY_p)
        s_Y = (np.hstack([1,-gamma_p[:,0]])).reshape(-1,1)
        
        if fuzzy is None:
            tau_cl = float(np.matmul(scalepar*s_Y.T,beta_p[deriv,:]))
            tau_bc = float(np.matmul(scalepar*s_Y.T,beta_bc[deriv,:]))
            tau_Y_cl_l = np.matmul(scalepar*s_Y.T,beta_p_l[deriv,:])
            tau_Y_cl_r = np.matmul(scalepar*s_Y.T,beta_p_r[deriv,:])
            tau_Y_bc_l = np.matmul(scalepar*s_Y.T,beta_bc_l[deriv,:])
            tau_Y_bc_r = np.matmul(scalepar*s_Y.T,beta_bc_r[deriv,:])
            bias_l = tau_Y_cl_l - tau_Y_bc_l
            bias_r = tau_Y_cl_r - tau_Y_bc_r 
        else:
            s_T  = np.append(1,-gamma_p[:,1])
            
            tau_Y_cl = float(np.matmul(scalepar*math.factorial(deriv)*s_Y.T,
                        np.append(beta_p[deriv,0], beta_p[deriv,colsZ]).reshape(-1,1)))
        
            tau_T_cl = float(np.matmul(math.factorial(deriv)*s_T.T,
                        np.append(beta_p[deriv,1], beta_p[deriv,colsZ]).reshape(-1,1))) 
            
            tau_Y_bc = float(np.matmul(scalepar*math.factorial(deriv)*s_Y.T,
                        np.append(beta_bc[deriv,0], beta_bc[deriv,colsZ]).reshape(-1,1)))
        
            tau_T_bc = float(np.matmul(math.factorial(deriv)*s_T.T,
                        np.append(beta_bc[deriv,1], beta_bc[deriv,colsZ]).reshape(-1,1))) 
        
            tau_Y_cl_l = float(np.matmul(scalepar*math.factorial(deriv)*s_Y.T,
                        np.append(beta_p_l[deriv,0], beta_p_l[deriv,colsZ]).reshape(-1,1)))
            
            tau_Y_cl_r = float(np.matmul(scalepar*math.factorial(deriv)*s_Y.T,
                        np.append(beta_p_r[deriv,0], beta_p_r[deriv,colsZ]).reshape(-1,1)))

            tau_Y_bc_l = float(np.matmul(scalepar*math.factorial(deriv)*s_Y.T,
                        np.append(beta_bc_l[deriv,0], beta_bc_l[deriv,colsZ]).reshape(-1,1)))
            
            tau_Y_bc_r = float(np.matmul(scalepar*math.factorial(deriv)*s_Y.T,
                        np.append(beta_bc_r[deriv,0], beta_bc_r[deriv,colsZ]).reshape(-1,1)))
   
            tau_T_cl_l = float(np.matmul(math.factorial(deriv)*s_T.T,
                        np.append(beta_p_l[deriv,1], beta_p_l[deriv,colsZ]).reshape(-1,1)))
            
            tau_T_cl_r = float(np.matmul(math.factorial(deriv)*s_T.T,
                        np.append(beta_p_r[deriv,1], beta_p_r[deriv,colsZ]).reshape(-1,1)))
            
            tau_T_bc_l = float(np.matmul(math.factorial(deriv)*s_T.T,
                        np.append(beta_bc_l[deriv,0], beta_bc_l[deriv,colsZ]).reshape(-1,1))) 
            
            tau_T_bc_r = float(np.matmul(math.factorial(deriv)*s_T.T,
                        np.append(beta_bc_r[deriv,1], beta_bc_r[deriv,colsZ]).reshape(-1,1))) 
       
            tau_cl = tau_Y_cl/tau_T_cl
            B_F   = np.array([tau_Y_cl-tau_Y_bc, tau_T_cl-tau_T_bc])
            B_F_l = np.array([tau_Y_cl_l-tau_Y_bc_l, tau_T_cl_l-tau_T_bc_l])
            B_F_r = np.array([tau_Y_cl_r-tau_Y_bc_r, tau_T_cl_r-tau_T_bc_r])
            
            s_Y = np.array([1/tau_T_cl , -(tau_Y_cl/tau_T_cl**2)])
            tau_bc = tau_cl - np.dot(s_Y,B_F)
            
            bias_l = np.dot(s_Y,B_F_l)
            bias_r = np.dot(s_Y,B_F_r)
          
            s_Y = np.hstack([s_Y,-(1/tau_T_cl)*gamma_p[:,0] + (tau_Y_cl/tau_T_cl**2)*gamma_p[:,1]])
 
    ####### Computing variance-covariance matrix.
  
    hii_l = hii_r = predicts_p_l = predicts_p_r = predicts_q_l = predicts_q_r = 0
    if vce=="hc0" or vce=="hc1" or vce=="hc2" or vce=="hc3":
        predicts_p_l = np.matmul(R_p_l,beta_p_l)
        predicts_p_r = np.matmul(R_p_r,beta_p_r)
        predicts_q_l = np.matmul(R_q_l,beta_q_l)
        predicts_q_r = np.matmul(R_q_r,beta_q_r)
        if vce=="hc2" or vce=="hc3":
            hii_l = np.sum(np.matmul(R_p_l,invG_p_l)*(R_p_l*W_h_l), axis = 1)
            hii_r = np.sum(np.matmul(R_p_r,invG_p_r)*(R_p_r*W_h_r), axis = 1)
  						
    res_h_l = rdrobust_res(eX_l, eY_l, eT_l, eZ_l, predicts_p_l, hii_l, vce, nnmatch, edups_l, edupsid_l, p+1)
    res_h_r = rdrobust_res(eX_r, eY_r, eT_r, eZ_r, predicts_p_r, hii_r, vce, nnmatch, edups_r, edupsid_r, p+1)
    if vce=="nn":
        res_b_l = res_h_l	
        res_b_r = res_h_r
    else:
        res_b_l = rdrobust_res(eX_l, eY_l, eT_l, eZ_l, predicts_q_l, hii_l, vce, nnmatch, edups_l, edupsid_l, q+1)
        res_b_r = rdrobust_res(eX_r, eY_r, eT_r, eZ_r, predicts_q_r, hii_r, vce, nnmatch, edups_r, edupsid_r, q+1)
			                       
    
    V_Y_cl_l = np.matmul(invG_p_l,np.matmul(rdrobust_vce(dT+dZ, s_Y, R_p_l*W_h_l, res_h_l, eC_l),invG_p_l))
    V_Y_cl_r = np.matmul(invG_p_r,np.matmul(rdrobust_vce(dT+dZ, s_Y, R_p_r*W_h_r, res_h_r, eC_r),invG_p_r))
    V_Y_rb_l = np.matmul(invG_p_l,np.matmul(rdrobust_vce(dT+dZ, s_Y, Q_q_l, res_b_l, eC_l),invG_p_l))
    V_Y_rb_r = np.matmul(invG_p_r,np.matmul(rdrobust_vce(dT+dZ, s_Y, Q_q_r, res_b_r, eC_r),invG_p_r))
    V_tau_cl = scalepar**2*math.factorial(deriv)**2*(V_Y_cl_l+V_Y_cl_r)[deriv,deriv]
    V_tau_rb = scalepar**2*math.factorial(deriv)**2*(V_Y_rb_l+V_Y_rb_r)[deriv,deriv]
    se_tau_cl = np.sqrt(V_tau_cl)
    se_tau_rb = np.sqrt(V_tau_rb)
     
    tau = np.array([tau_cl, tau_bc, tau_bc]).reshape(-1,1)
    se  = np.array([se_tau_cl,se_tau_cl,se_tau_rb]).reshape(-1,1)
    t   =  tau/se
    pv  = 2*sct.norm.cdf(-np.abs(t))
    ci = np.column_stack((tau - quant*se,tau + quant*se))


    # Preparing Output
    Estimate = pd.DataFrame(np.array([tau_cl,tau_bc, se_tau_cl, se_tau_rb]).reshape(1,-1),
                            columns = ["tau.us","tau.bc","se.us","se.rb"],
                            index = pd.Index(["Estimate"]))
    bws = pd.DataFrame(np.array([[h_l,h_r],[b_l,b_r]]),
                            columns = ["left","right"],
                            index = pd.Index(["h","b"]))
    label = ["Conventional","Bias-Corrected","Robust"]
    coef = pd.DataFrame(tau,
                        columns = ["Coeff"],
                        index = pd.Index(label))
    se = pd.DataFrame(se,
                      columns = ["Std. Err."],
                      index = pd.Index(label))
    t = pd.DataFrame(t,
                     columns = ["t-stat."],
                     index = pd.Index(label))
    pv = pd.DataFrame(pv,
                     columns = ["P>|t|"],
                     index = pd.Index(label))    
    ci = pd.DataFrame(ci, 
                      columns = ["CI Lower","CI Upper"],
                      index = pd.Index(["Conventional","Bias-Corrected","Robust"]))
    
    return rdrobust_output(Estimate, bws, coef, se, t, pv, ci, beta_p_l, beta_p_r,
                    V_Y_cl_l, V_Y_cl_r, V_Y_rb_l, V_Y_rb_r,
                    [N_l,N_r], [N_h_l,N_h_r], [N_b_l,N_b_r], [M_l,M_r],
                    [tau_Y_cl_l,tau_Y_cl_r], [tau_Y_bc_l,tau_Y_bc_r],
                    c, p, q, [bias_l,bias_r], kernel_type, all,
                    vce_type, bwselect, level, masspoints)