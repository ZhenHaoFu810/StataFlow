#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul  7 18:36:35 2021

@author: rmasini
"""

import numpy as np
import scipy.stats as sct
import pandas  as pd
from sklearn.linear_model import LinearRegression as LR
from plotnine import *
from rdrobust.funs import *


def rdplot(y, x, c = 0, p = 4, nbins = None, binselect = "esmv", scale = None, 
                  kernel = "uni", weights = None, h = None, 
                  covs = None,  covs_eval = "mean", covs_drop = True,
                  support = None, subset = None, masspoints = "adjust",
                  hide = False, ci = None, shade = False, 
                  title = None, x_label = None, y_label = None, x_lim = None,
                  y_lim = None, col_dots = None, col_lines = None):
    
    '''
    Implements several data-driven Regression Discontinuity (RD) plots, using either evenly-spaced or quantile-spaced partitioning. Two type of RD plots are constructed: (i) RD plots with binned sample means tracing out the underlying regression function, and (ii) RD plots with binned sample means mimicking the underlying variability of the data. For technical and methodological details see Calonico, Cattaneo and Titiunik (2015a).
    
    Companion commands are: rdrobust for point estimation and inference procedures, and rdbwselect for data-driven bandwidth selection.
    
    A detailed introduction to this command is given in Calonico, Cattaneo and Titiunik (2015b) and Calonico, Cattaneo, Farrell and Titiunik (2017). A companion Stata package is described in Calonico, Cattaneo and Titiunik (2014).
    
    For more details, and related Stata and R packages useful for analysis of RD designs, visit https://rdpackages.github.io/
    
    
    Parameters
    ----------
    y	
    is the dependent variable.
    
    x	
    is the running variable (a.k.a. score or forcing variable).
    
    c	
    specifies the RD cutoff in x; default is c = 0.
    
    p	
    specifies the order of the global-polynomial used to approximate the population conditional mean functions for control and treated units; default is p = 4.
    
    nbins	
    specifies the number of bins used to the left of the cutoff, denoted J_-, and to the right of the cutoff, denoted J_+, respectively. If not specified, J_+ and J_- are estimated using the method and options chosen below.
    
    binselect	
    specifies the procedure to select the number of bins. This option is available only if J_- and J_+ are not set manually. Options are:
    
    es: IMSE-optimal evenly-spaced method using spacings estimators.
    
    espr: IMSE-optimal evenly-spaced method using polynomial regression.
    
    esmv: mimicking variance evenly-spaced method using spacings estimators. This is the default option.
    
    esmvpr: mimicking variance evenly-spaced method using polynomial regression.
    
    qs: IMSE-optimal quantile-spaced method using spacings estimators.
    
    qspr: IMSE-optimal quantile-spaced method using polynomial regression.
    
    qsmv: mimicking variance quantile-spaced method using spacings estimators.
    
    qsmvpr: mimicking variance quantile-spaced method using polynomial regression.
    
    scale	
    specifies a multiplicative factor to be used with the optimal numbers of bins selected. Specifically, the number of bins used for the treatment and control groups will be scale\times \hat{J}_+ and scale\times \hat{J}_-, where \hat{J}_\cdot denotes the estimated optimal numbers of bins originally computed for each group; default is scale = 1.
    
    kernel	
    specifies the kernel function used to construct the local-polynomial estimator(s). Options are: triangular, epanechnikov, and uniform. Default is kernel=uniform (i.e., equal/no weighting to all observations on the support of the kernel).
    
    weights	
    is the variable used for optional weighting of the estimation procedure. The unit-specific weights multiply the kernel function.
    
    h	
    specifies the bandwidth used to construct the (global) polynomial fits given the kernel choice kernel. If not specified, the bandwidths are chosen to span the full support of the data. If two bandwidths are specified, the first bandwidth is used for the data below the cutoff and the second bandwidth is used for the data above the cutoff.
    
    covs	
    specifies additional covariates to be used in the polynomial regression.
    
    covs_eval	
    sets the evaluation points for the additional covariates, when included in the estimation. Options are: covs_eval = 0 (default) and covs_eval = "mean"
    
    covs_drop	
    if TRUE, it checks for collinear additional covariates and drops them. Default is TRUE.
    
    support	
    specifies an optional extended support of the running variable to be used in the construction of the bins; default is the sample range.
    
    subset	
    an optional vector specifying a subset of observations to be used.
    
    masspoints	
    checks and controls for repeated observations in the running variable. Options are:
    
    (i) off: ignores the presence of mass points;
    
    (ii) check: looks for and reports the number of unique observations at each side of the cutoff.
    
    (iii) adjust: sets binselect() as polynomial regression when mass points are present.
    
    Default option is masspoints=adjust.
    
    hide	
    logical. If TRUE, it omits the RD plot; default is hide = FALSE.
    
    ci	
    optional graphical option to display confidence intervals of selected level for each bin.
    
    shade	
    optional graphical option to replace confidence intervals with shaded areas.
    
    title	
    optional title for the RD plot.
    
    x_label	
    optional label for the x-axis of the RD plot.
    
    y_label	
    optional label for the y-axis of the RD plot.
    
    x_lim	
    optional setting for the range of the x-axis in the RD plot.
    
    y_lim	
    optional setting for the range of the y-axis in the RD plot.
    
    col_dots	
    optional setting for the color of the dots in the RD plot.
    
    col_lines	
    optional setting for the color of the lines in the RD plot.
    
    Returns
    -------
    binselect	
    method used to compute the optimal number of bins.
    
    N	
    sample sizes used to the left and right of the cutoff.
    
    Nh	
    effective sample sizes used to the left and right of the cutoff.
    
    c	
    cutoff value.
    
    p	
    order of the global polynomial used.
    
    h	
    bandwidth used to the left and right of the cutoff.
    
    kernel	
    kernel used.
    
    J	
    selected number of bins to the left and right of the cutoff.
    
    J_IMSE	
    IMSE optimal number of bins to the left and right of the cutoff.
    
    J_MV	
    Mimicking variance number of bins to the left and right of the cutoff.
    
    coef	
    matrix containing the coefficients of the p^{th} order global polynomial estimated both sides of the cutoff.
    
    scale	
    selected scale value.
    
    rscale	
    implicit scale value.
    
    bin_avg	
    average bin length.
    
    bin_med	
    median bin length.
    
    vars_bins	
    data frame containing the variables used to construct the bins: bin id, cutoff values, mean of x and y within each bin, cutoff points and confidence interval bounds.
    
    vars_poly	
    data frame containing the variables used to construct the global polynomial plot.
    
    rdplot	
    a standard ggplot object that can be used for further customization.
    
    References
    ----------
    Calonico, S., M. D. Cattaneo, M. H. Farrell, and R. Titiunik. 2017. rdrobust: Software for Regression Discontinuity Designs. Stata Journal 17(2): 372-404.
    
    Calonico, S., M. D. Cattaneo, and R. Titiunik. 2014. Robust Data-Driven Inference in the Regression-Discontinuity Design. Stata Journal 14(4): 909-946.
    
    Calonico, S., M. D. Cattaneo, and R. Titiunik. 2015a. Optimal Data-Driven Regression Discontinuity Plots. Journal of the American Statistical Association 110(512): 1753-1769.
    
    Calonico, S., M. D. Cattaneo, and R. Titiunik. 2015b. rdrobust: An R Package for Robust Nonparametric Inference in Regression-Discontinuity Designs. R Journal 7(1): 38-51.
    
    Cattaneo, M. D., B. Frandsen, and R. Titiunik. 2015. Randomization Inference in the Regression Discontinuity Design: An Application to the Study of Party Advantages in the U.S. Senate. Journal of Causal Inference 3(1): 1-24.
    
    See Also
    --------
    rdbwselect, rdrobust
    
    
    Example
    -------
    >>> x = numpy.random.uniform(low=-1, high=1, size=1000)
    >>> y = 5+3*x+2*(x>=0) + numpy.random.uniform(size = 1000)
    >>> rdplot(y,x)
    '''
    
    # Tidy the Input and remove NAN
    x = np.array(x).reshape(-1,1)
    y = np.array(y).reshape(-1,1)
    if subset is not None:
        x = x[subset]
        y = y[subset]
        
    na_ok = complete_cases(x) & complete_cases(y)
    
    if covs is not None:       
        covs = np.array(covs).reshape(len(covs),-1)  
        if subset is not None: covs = covs[subset,:]
        na_ok = na_ok & complete_cases(covs)
    
    if weights is not None:
        weights = np.array(weights).reshape(-1,1)
        if subset is not None:
            weights = weights[subset]
        na_ok = na_ok & complete_cases(weights) & (weights>=0).reshape(-1,)
        
    x = x[na_ok]
    y = y[na_ok]    
    
    if covs is not None: covs = covs[na_ok,:]
    if weights is not None: weights = weights[na_ok]
    
    x_min = np.min(x)  
    x_max = np.max(x)
    x_l = x[x<c]
    x_r = x[x>=c]
    y_l = y[x<c]
    y_r = y[x>=c]
    
    if support is not None:
       support_l, support_r = support
       if support_l<x_min: x_min = support_l
       if support_r>x_max: x_max = support_r
       
    range_l = c - x_min
    range_r = x_max - c
    n_l = len(x_l)
    n_r = len(x_r)
    n = n_l + n_r
    meth="es"
    
    if scale is None: scale = scale_l = scale_r = 1  
    else:
        if np.isscalar(scale): scale_l = scale_r = scale
        else: scale_l, scale_r = scale
    
    if nbins is not None: 
        if np.isscalar(nbins): nbins_l = nbins_r = nbins
        else: nbins_l, nbins_r = nbins

    if h is None:
        h_l = range_l
        h_r = range_r
    else:
        if np.isscalar(h): h_l = h_r = h
        else: h_l, h_r = h
        
    flag_no_ci  = False
    if ci is None:
        ci =  95
        flag_no_ci = True
    
   
    
    kernel_type = "Uniform"
    if kernel=="epanechnikov" or kernel=="epa": kernel_type = "Epanechnikov"
    if kernel=="triangular" or kernel=="tri": kernel_type = "Triangular"
    
    ### Mass Points
    
    if masspoints is None: masspoints = False
    mN = n
    M_l = n_l
    M_r = n_r
    if masspoints=="check" or masspoints=="adjust":
        X_uniq_l = np.sort(np.unique(x_l))[::-1]
        X_uniq_r = np.unique(x_r)
        M_l = len(X_uniq_l)
        M_r = len(X_uniq_r)
        M = M_l + M_r
        mass_l = 1-M_l/n_l
        mass_r = 1-M_r/n_r				
        if mass_l>=0.2 or mass_r>=0.2:
          print("Mass points detected in the running variable.")
          if masspoints=="check": print("Try using option masspoints=adjust.")
          if masspoints=="adjust":
              if binselect=="es": binselect="espr"
              if binselect=="esmv": binselect="esmvpr"
              if binselect=="qs": binselect="qspr"
              if binselect=="qsmv": binselect="qsmvpr"
              
    ### COLLINEARITY
    
    covs_drop_coll = dZ = 0
    if covs_drop: covs_drop_coll = 1 
    if covs is not None:
        dZ = ncol(covs)
        if covs_drop: 
            covs_check = covs_drop_fun(covs)
            if ncol(covs_check) < dZ:
                covs = covs_check
                dZ = ncol(covs)

    ### ERRORS
    
    if c<=x_min or c>=x_max:
        raise Exception("c should be set within the range of x")
    
    kernel   = kernel.lower()
    kernel_list = ['uni','uniform','tri','triangular','epa','epanechnikov','']
    if kernel not in kernel_list:   
        raise Exception("kernel incorrectly specified")
        
    if not np.isscalar(p) or p not in range(21):
        raise Exception('Polynomial order p incorrectly specified.')
        
    if scale<=0 or scale_l<=0 or scale_r<=0:
        raise Exception("scale should be a positive number")
    
    if n<20:
        raise Exception("Not enough observations to perform bin calculations")
      
	###################################################################
	### Polynomial curve (order = p) ##################################
	###################################################################

    R_p_l = nanmat(n_l,p+1)
    R_p_r = nanmat(n_r,p+1)
    for j in range(p+1):
        R_p_l[:,j] = (x_l-c)**j
        R_p_r[:,j] = (x_r-c)**j
	
    W_h_l = rdrobust_kweight(x_l,c,h_l,kernel).reshape(-1,1)
    W_h_r = rdrobust_kweight(x_r,c,h_r,kernel).reshape(-1,1)
	
    n_h_l = np.sum(W_h_l>0)
    n_h_r = np.sum(W_h_r>0)
	
    if weights is not None:
        fw_l = weights[x<c].reshape(-1,1)
        fw_r = weights[x>=c].reshape(-1,1)
        W_h_l = fw_l*W_h_l
        W_h_r = fw_r*W_h_r
	
    invG_p_l  = qrXXinv(np.sqrt(W_h_l)*R_p_l)
    invG_p_r  = qrXXinv(np.sqrt(W_h_r)*R_p_r)
	
    if covs is None:
        gamma_p1_l = np.matmul(invG_p_l,crossprod(R_p_l*W_h_l,y_l))
        gamma_p1_r = np.matmul(invG_p_r,crossprod(R_p_r*W_h_r,y_r))
    else:
        z_l  = covs[(x<c).reshape(-1),:]
        z_r  = covs[(x>=c).reshape(-1),:]	
        D_l  = np.column_stack((y_l,z_l))
        D_r = np.column_stack((y_r,z_r))
        U_p_l = crossprod(R_p_l*W_h_l,D_l)
        U_p_r = crossprod(R_p_r*W_h_r,D_r)
        beta_p_l = np.matmul(invG_p_l,crossprod(R_p_l*W_h_l,D_l))
        beta_p_r = np.matmul(invG_p_r,crossprod(R_p_r*W_h_r,D_r))
        ZWD_p_l  = crossprod(z_l*W_h_l,D_l)
        ZWD_p_r  = crossprod(z_r*W_h_r,D_r)
        colsZ = np.arange(1,max(2+dZ-1,2))
        UiGU_p_l =  crossprod(U_p_l[:,colsZ],np.matmul(invG_p_l,U_p_l)) 
        UiGU_p_r =  crossprod(U_p_r[:,colsZ],np.matmul(invG_p_r,U_p_r))  
        ZWZ_p_l = ZWD_p_l[:,colsZ] - UiGU_p_l[:,colsZ] 
        ZWZ_p_r = ZWD_p_r[:,colsZ] - UiGU_p_r[:,colsZ]     
        ZWY_p_l = ZWD_p_l[:,:1] - UiGU_p_l[:,:1] 
        ZWY_p_r = ZWD_p_r[:,:1] - UiGU_p_r[:,:1]      
        ZWZ_p = ZWZ_p_r + ZWZ_p_l
        ZWY_p = ZWY_p_r + ZWY_p_l
        if covs_drop_coll == 0:
            gamma_p = np.matmul(inv_chol(ZWZ_p),ZWY_p)
        elif covs_drop_coll == 1:
            gamma_p = np.matmul(np.linalg.pinv(ZWZ_p),ZWY_p)
        s_Y = (np.hstack([1,-gamma_p[:,0]])).reshape(-1,1)
        gamma_p1_l = (np.matmul(s_Y.T,(beta_p_l).T)).T
        gamma_p1_r = (np.matmul(s_Y.T,(beta_p_r).T)).T
       
	###############################################
	### Prepare data for polynomial curve plot ####
	###############################################
	
    nplot = 500
    x_plot_l = np.linspace(c-h_l, c, nplot)
    x_plot_r = np.linspace(c, c+h_r, nplot)
    rplot_l = nanmat(nplot,p+1)
    rplot_r = nanmat(nplot,p+1)
    for j in range(p+1):
        rplot_l[:,j] = (x_plot_l-c)**j
        rplot_r[:,j] = (x_plot_r-c)**j
    y_hat_l = np.matmul(rplot_l,gamma_p1_l)
    y_hat_r = np.matmul(rplot_r,gamma_p1_r)

    if covs is not None and covs_eval=="mean":
        gammaZ = np.dot(np.mean(covs, axis = 0),gamma_p)
        y_hat_l = np.matmul(rplot_l,gamma_p1_l) + gammaZ
        y_hat_r = np.matmul(rplot_r,gamma_p1_r) + gammaZ
	
    ###############################################
    ### Optimal Bins (using polynomial order k) ###
    ###############################################
  
    max_k=4
    for k in range(max_k,1,-1):
        rk_l = nanmat(n_l,k+1)
        rk_r = nanmat(n_r,k+1)
        for i in range(k+1):
            rk_l[:,i] = x_l**i
            rk_r[:,i] = x_r**i
        try:
            invG_k_l = qrXXinv(rk_l)
            invG_k_r = qrXXinv(rk_r)
            break
        except:
            pass
        
    gamma_k1_l = np.matmul(invG_k_l,crossprod(rk_l, y_l))
    gamma_k2_l = np.matmul(invG_k_l,crossprod(rk_l, y_l**2))
    gamma_k1_r = np.matmul(invG_k_r,crossprod(rk_r, y_r))  
    gamma_k2_r = np.matmul(invG_k_r,crossprod(rk_r, y_r**2))
  
  ### Bias w/sample
  
    mu0_k1_l = np.matmul(rk_l,gamma_k1_l)
    mu0_k1_r = np.matmul(rk_r,gamma_k1_r)
    mu0_k2_l = np.matmul(rk_l,gamma_k2_l)
    mu0_k2_r = np.matmul(rk_r,gamma_k2_r)
    
    drk_l = nanmat(n_l,k)
    drk_r = nanmat(n_r,k)
    for j in range(k):
        drk_l[:,j] = (j+1)*x_l**j
        drk_r[:,j] = (j+1)*x_r**j

    ind_l = np.argsort(x_l)
    ind_r = np.argsort(x_r)
    x_i_l = x_l[ind_l]
    y_i_l = y_l[ind_l]
    x_i_r = x_r[ind_r]
    y_i_r = y_r[ind_r]
                         
    dxi_l = x_i_l[1:]-x_i_l[:-1]
    dxi_r = x_i_r[1:]-x_i_r[:-1]
    dyi_l = y_i_l[1:]-y_i_l[:-1]
    dyi_r = y_i_r[1:]-y_i_r[:-1]
                         
    x_bar_i_l = (x_i_l[1:] + x_i_l[:-1])/2
    x_bar_i_r = (x_i_r[1:] + x_i_r[:-1])/2
                         
    	
    rk_i_l  = nanmat(n_l-1,k+1)
    rk_i_r  = nanmat(n_r-1,k+1)
    for j in range(k+1):
        rk_i_l[:,j] = x_bar_i_l**j   
        rk_i_r[:,j] = x_bar_i_r**j
        
    drk_i_l = nanmat(n_l-1,k)
    drk_i_r = nanmat(n_r-1,k)	
    for j in range(k):
        drk_i_l[:,j] = (j+1)*x_bar_i_l**j
        drk_i_r[:,j] = (j+1)*x_bar_i_r**j
        
    mu1_i_hat_l = np.matmul(drk_i_l,gamma_k1_l[1:])
    mu1_i_hat_r = np.matmul(drk_i_r,gamma_k1_r[1:])
    
    mu0_i_hat_l = np.matmul(rk_i_l,gamma_k1_l)
    mu0_i_hat_r = np.matmul(rk_i_r,gamma_k1_r)
    mu2_i_hat_l = np.matmul(rk_i_l,gamma_k2_l)
    mu2_i_hat_r = np.matmul(rk_i_r,gamma_k2_r)
                         
    mu0_hat_l = np.matmul(rk_l,gamma_k1_l)
    mu0_hat_r = np.matmul(rk_r,gamma_k1_r)
    mu2_hat_l = np.matmul(rk_l,gamma_k2_l)
    mu2_hat_r = np.matmul(rk_r,gamma_k2_r)
                         
    mu1_hat_l = np.matmul(drk_l,gamma_k1_l[1:])
    mu1_hat_r = np.matmul(drk_r,gamma_k1_r[1:])
                         
    mu1_i_hat_l = np.matmul(drk_i_l,gamma_k1_l[1:])
    mu1_i_hat_r = np.matmul(drk_i_r,gamma_k1_r[1:])

    var_y_l = np.var(y_l)
    var_y_r = np.var(y_r)
    
    sigma2_hat_l_bar = mu2_i_hat_l - mu0_i_hat_l**2
    sigma2_hat_r_bar = mu2_i_hat_r - mu0_i_hat_r**2
    ind_s2_l = sigma2_hat_l_bar<0
    ind_s2_r = sigma2_hat_r_bar<0
    sigma2_hat_l_bar[ind_s2_l] = var_y_l 
    sigma2_hat_r_bar[ind_s2_r] = var_y_r 
    
    sigma2_hat_l = mu2_hat_l - mu0_hat_l**2
    sigma2_hat_r = mu2_hat_r - mu0_hat_r**2
    ind_s2_l = sigma2_hat_l<0
    ind_s2_r = sigma2_hat_r<0
    sigma2_hat_l[ind_s2_l] = var_y_l 
    sigma2_hat_r[ind_s2_r] = var_y_r
    
    def J_fun(B,V): return np.ceil((((2*B)/V)*n)**(1/3))

    B_es_hat_dw = np.array([((c-x_min)**2/(12*n))*np.sum(mu1_hat_l**2),((x_max-c)**2/(12*n))*np.sum(mu1_hat_r**2)])
    V_es_hat_dw = np.array([(0.5/(c-x_min))*sum(dxi_l*dyi_l**2),(0.5/(x_max-c))*sum(dxi_r*dyi_r**2)])
    V_es_chk_dw = np.array([(1/(c-x_min))*sum(dxi_l*sigma2_hat_l_bar),(1/(x_max-c))*sum(dxi_r*sigma2_hat_r_bar)])
    J_es_hat_dw = J_fun(B_es_hat_dw, V_es_hat_dw)
    J_es_chk_dw = J_fun(B_es_hat_dw, V_es_chk_dw)
    
    B_qs_hat_dw = np.array([(n_l**2/(24*n))*sum(dxi_l**2*mu1_i_hat_l**2), (n_r**2/(24*n))*sum(dxi_r**2*mu1_i_hat_r**2)])
    V_qs_hat_dw = np.array([(1/(2*n_l))*sum(dyi_l**2),(1/(2*n_r))*sum(dyi_r**2)])
    V_qs_chk_dw = np.array([(1/n_l)*sum(sigma2_hat_l), (1/n_r)*sum(sigma2_hat_r)])
    J_qs_hat_dw = J_fun(B_qs_hat_dw, V_qs_hat_dw)
    J_qs_chk_dw = J_fun(B_qs_hat_dw, V_qs_chk_dw)
    
    J_es_hat_mv  = np.array([np.ceil((var_y_l/V_es_hat_dw[0])*(n/np.log(n)**2)), np.ceil((var_y_r/V_es_hat_dw[1])*(n/np.log(n)**2))])
    J_es_chk_mv  = np.array([np.ceil((var_y_l/V_es_chk_dw[0])*(n/np.log(n)**2)), np.ceil((var_y_r/V_es_chk_dw[1])*(n/np.log(n)**2))])
    J_qs_hat_mv  = np.array([np.ceil((var_y_l/V_qs_hat_dw[0])*(n/np.log(n)**2)), np.ceil((var_y_r/V_qs_hat_dw[1])*(n/np.log(n)**2))])
    J_qs_chk_mv  = np.array([np.ceil((var_y_l/V_qs_chk_dw[0])*(n/np.log(n)**2)), np.ceil((var_y_r/V_qs_chk_dw[1])*(n/np.log(n)**2))])
  
  #########################################################
  
    if binselect=="es":
        J_star_orig = J_es_hat_dw
        meth = "es"
        binselect_type="IMSE-optimal evenly-spaced method using spacings estimators"
        J_IMSE = J_es_hat_dw
        J_MV   = J_es_hat_mv
    elif binselect=="espr":
        J_star_orig = J_es_chk_dw
        meth="es"
        binselect_type="IMSE-optimal evenly-spaced method using polynomial regression"
        J_IMSE = J_es_chk_dw
        J_MV   = J_es_chk_mv
    elif binselect=="esmv":
        J_star_orig = J_es_hat_mv
        meth = "es"
        binselect_type="mimicking variance evenly-spaced method using spacings estimators"
        J_IMSE = J_es_hat_dw
        J_MV   = J_es_hat_mv
    elif binselect=="esmvpr":
        J_star_orig = J_es_chk_mv
        meth="es"
        binselect_type="mimicking variance evenly-spaced method using polynomial regression"
        J_IMSE = J_es_chk_dw
        J_MV   = J_es_chk_mv 
    elif binselect=="qs":
        J_star_orig = J_qs_hat_dw
        meth="qs"
        binselect_type="IMSE-optimal quantile-spaced method using spacings estimators"
        J_IMSE = J_qs_hat_dw
        J_MV   = J_qs_hat_mv
    elif binselect=="qspr":
        J_star_orig = J_qs_chk_dw
        meth="qs"
        binselect_type="IMSE-optimal quantile-spaced method using polynomial regression"
        J_IMSE = J_qs_chk_dw
        J_MV   = J_qs_chk_mv
    elif binselect=="qsmv":
        J_star_orig = J_qs_hat_mv
        meth="qs"
        binselect_type="mimicking variance quantile-spaced method using spacings estimators"
        J_IMSE = J_qs_hat_dw
        J_MV   = J_qs_hat_mv
    elif binselect=="qsmvpr":
        J_star_orig = J_qs_chk_mv
        meth="qs"
        binselect_type="mimicking variance quantile-spaced method using polynomial regression"
        J_IMSE = J_qs_chk_dw
        J_MV   = J_qs_chk_mv

    J_star_l = scale_l*J_star_orig[0]
    if not np.isnan(J_star_l): J_star_l = int(J_star_l)
    J_star_r = scale_r*J_star_orig[1]
    if not np.isnan(J_star_r): J_star_r = int(J_star_r)

    if nbins is not None:
        if not np.isnan(J_star_l): J_star_l = int(nbins_l)
        if not np.isnan(J_star_r): J_star_r = int(nbins_r)
        binselect_type="manually evenly spaced"
  
    if var_y_l==0.0:
        J_star_l  = 1
        print("Warning: not enough variability in the outcome variable below the threshold")
      
    if var_y_r==0.0:
        J_star_r = 1
        print("Warning: not enough variability in the outcome variable above the threshold")
    
    rscale_l = J_star_l / J_IMSE[0]
    rscale_r = J_star_r / J_IMSE[1]
  
    
  
    jump_l  = range_l/J_star_l
    jump_r = range_r/J_star_r
  
    if meth=="es":
        jumps_l=np.linspace(x_min,c,J_star_l+1)       
        jumps_r=np.linspace(c,x_max,J_star_r+1)
        #binselect_type="Evenly-Spaced"
    elif meth=="qs":
       jumps_l=np.quantile(x_l,np.linspace(0,1,J_star_l+1))
       jumps_r=np.quantile(x_r,np.linspace(0,1,J_star_r+1))
      # binselect_type="Quantile-Spaced"
    
    
    
    def mean(x):
        if not np.any(x): return(np.nan)
        else: return np.mean(x)
    
    bin_x_l = np.searchsorted(jumps_l, x_l,side='right') - J_star_l - 1
    bin_x_l[bin_x_l==0] =-1   # to mimick R behaviour of FindInterval function in R
    bin_x_r = np.searchsorted(jumps_r, x_r,side='left')
    bin_x_r[bin_x_r==J_star_r] = J_star_r-1  # to mimick R behaviour of FindInterval function in R

    aux_l  = pd.DataFrame({'bin_x_l':bin_x_l, 'y_l':y_l, 'x_l':x_l})
    rdplot_l  = aux_l.groupby('bin_x_l').agg({'y_l': 'mean', 'x_l':'mean'}).reset_index()
    rdplot_bin_l =  rdplot_l['bin_x_l'].values
    rdplot_bin_l = rdplot_bin_l[:J_star_l]
    rdplot_mean_y_l = rdplot_l['y_l'].values
    rdplot_mean_x_l = rdplot_l['x_l'].values

    aux_r  = pd.DataFrame({'bin_x_r':bin_x_r, 'y_r':y_r, 'x_r':x_r})
    rdplot_r  = aux_r.groupby('bin_x_r').agg({'y_r': 'mean', 'x_r':'mean'}).reset_index()    
    rdplot_bin_r =  rdplot_r['bin_x_r'].values
    rdplot_mean_y_r = rdplot_r['y_r'].values
    rdplot_mean_x_r = rdplot_r['x_r'].values

    if covs is not None and covs_eval=="mean":
        dummy_l = pd.get_dummies(data=bin_x_l, drop_first=True)
        dummy_l = np.array(dummy_l).reshape(-1,ncol(dummy_l))
        regressors_l = np.column_stack([z_l,dummy_l])
        covs_model_l = LR().fit(regressors_l,y_l.reshape(-1,1))
        yhatZ_l = covs_model_l.predict(regressors_l).reshape(-1)
        aux_l  = pd.DataFrame({'bin_x_l':bin_x_l, 'yhatZ_l':yhatZ_l})
        rdplot_mean_y_l  = aux_l.groupby('bin_x_l').agg({'yhatZ_l': 'mean'})['yhatZ_l'].values
        
        dummy_r = pd.get_dummies(data=bin_x_r, drop_first=True)
        dummy_r = np.array(dummy_r).reshape(-1,ncol(dummy_r))
        regressors_r = np.column_stack([z_r,dummy_r])
        covs_model_r = LR().fit(regressors_r,y_r.reshape(-1,1))
        yhatZ_r = covs_model_r.predict(regressors_r).reshape(-1)
        aux_r  = pd.DataFrame({'bin_x_r':bin_x_r, 'yhatZ_r':yhatZ_r})
        rdplot_mean_y_r  = aux_r.groupby('bin_x_r').agg({'yhatZ_r': 'mean'})['yhatZ_r'].values

    t_ind_l = np.arange(J_star_l)
    t_ind_r = np.arange(J_star_r)

    rdplot_mean_bin_l = np.mean(np.column_stack((jumps_l[t_ind_l],jumps_l[t_ind_l+1])),axis=1)
    rdplot_mean_bin_r = np.mean(np.column_stack((jumps_r[t_ind_r],jumps_r[t_ind_r+1])),axis=1)

    
    # rdplot_mean_bin_l = rdplot_mean_bin_l[np.flip(-rdplot_bin_l)-1]
    rdplot_mean_bin_l = rdplot_mean_bin_l[rdplot_bin_l+J_star_l]
    rdplot_mean_bin_r = rdplot_mean_bin_r[rdplot_bin_r-1]

    bin_x = np.concatenate((bin_x_l,bin_x_r))

    rdplot_mean_bin = np.concatenate((rdplot_mean_bin_l, rdplot_mean_bin_r))
    rdplot_mean_x   = np.concatenate((rdplot_mean_x_l, rdplot_mean_x_r))
    rdplot_mean_y   = np.concatenate((rdplot_mean_y_l, rdplot_mean_y_r))
    
    aux_l = pd.DataFrame({'bin':-bin_x_l, 'y':y_l}).groupby('bin').agg({'y':['count','std']})
    aux_r = pd.DataFrame({'bin':bin_x_r, 'y':y_r}).groupby('bin').agg({'y':['count','std']})

    rdplot_N_l    = aux_l['y']['count'].values
    rdplot_sd_y_l = aux_l['y']['std'].values
    rdplot_N_r    = aux_r['y']['count'].values
    rdplot_sd_y_r = aux_r['y']['std'].values
		
    rdplot_sd_y_l[np.isnan(rdplot_sd_y_l)] = 0
    rdplot_sd_y_r[np.isnan(rdplot_sd_y_r)] = 0
    rdplot_sd_y = np.concatenate([rdplot_sd_y_l[::-1],rdplot_sd_y_r])
    rdplot_N = np.concatenate([rdplot_N_l[::-1],rdplot_N_r])
	
    quant = -sct.t.ppf((1-(ci/100))/2, np.maximum(rdplot_N-1,1))
    non_zero = rdplot_N>0
    rdplot_se_y = nanmat(len(rdplot_sd_y))
    rdplot_se_y[non_zero] = rdplot_sd_y[non_zero]/np.sqrt(rdplot_N[non_zero])
    rdplot_cil_bin = rdplot_mean_y - quant*rdplot_se_y
    rdplot_cir_bin = rdplot_mean_y + quant*rdplot_se_y
    temp_plot = None
	
    if not hide:
        if col_lines is None: col_lines = "red"
        if col_dots is None: col_dots  = "darkblue"
        if title is None: title = "RD Plot"
        if x_label is None: x_label = "X axis"
        if y_label is None: y_label = "Y axis"
        
        data_bins = pd.DataFrame({
                        'rdplot_mean_bin':rdplot_mean_bin,
                        'rdplot_mean_y': rdplot_mean_y,
                        'rdplot_cil_bin': rdplot_cil_bin,
                        'rdplot_cir_bin' : rdplot_cir_bin
            })
           
        data_poly = pd.DataFrame({
                                  'x_plot_l': x_plot_l,
                                  'y_hat_l': y_hat_l.reshape(-1),
                                  'x_plot_r': x_plot_r,
                                  'y_hat_r': y_hat_r.reshape(-1)
            })
        
        temp_plot = (ggplot() + theme_bw() + 
                     geom_point(data=data_bins, mapping = aes(x=rdplot_mean_bin, y=rdplot_mean_y), color=col_dots, na_rm=True) +
                     geom_line( data=data_poly, mapping = aes(x=x_plot_l, y=y_hat_l), color=col_lines, na_rm=True) +
                     geom_line( data=data_poly, mapping = aes(x=x_plot_r, y=y_hat_r), color=col_lines, na_rm=True)) 
      
        if flag_no_ci==False:
            temp_plot = (temp_plot +
                         geom_errorbar(data=data_bins, mapping = aes(x=rdplot_mean_bin, ymin=rdplot_cil_bin, ymax=rdplot_cir_bin))) 
        if shade:
            temp_plot = (temp_plot +
                         geom_ribbon(data=data_bins, mapping = aes(x=rdplot_mean_bin, ymin=rdplot_cil_bin, ymax=rdplot_cir_bin)))
      
        temp_plot  = (temp_plot + labs(x = x_label, y = y_label) + ggtitle(title)+
                      coord_cartesian(xlim = x_lim, ylim = y_lim) +
                      theme(legend_position = "None") +
                      geom_vline(xintercept = c, size = 0.5)) 
        
        ggplot.show(temp_plot)
  
    rdplot_min_bin_l = jumps_l[0:J_star_l]
    rdplot_max_bin_l = jumps_l[1:(J_star_l + 1)]
    rdplot_min_bin_r = jumps_r[0:J_star_r]
    rdplot_max_bin_r = jumps_r[1:(J_star_r + 1)]
    rdplot_min_bin = np.concatenate((rdplot_min_bin_l[np.flip(-rdplot_bin_l)-1], rdplot_min_bin_r[rdplot_bin_r-1]))
    rdplot_max_bin = np.concatenate((rdplot_max_bin_l[np.flip(-rdplot_bin_l)-1], rdplot_max_bin_r[rdplot_bin_r-1]))

    bin_length = rdplot_max_bin-rdplot_min_bin
    bin_avg_l = mean(bin_length[:J_star_l])
    bin_med_l = np.median(bin_length[:J_star_l])
  	
    bin_avg_r = mean(bin_length[J_star_l:])
    bin_med_r = np.median(bin_length[J_star_l:])


    vars_bins = pd.DataFrame({
          "rdplot_mean_bin": rdplot_mean_bin,
          "rdplot_mean_x": rdplot_mean_x,
          "rdplot_mean_y": rdplot_mean_y,
          "rdplot_min_bin": rdplot_min_bin,
          "rdplot_max_bin": rdplot_max_bin,
          "rdplot_se_y": rdplot_se_y,
          "rdplot_N": rdplot_N,
          "rdplot_ci_l": rdplot_cil_bin,
          "rdplot_ci_r": rdplot_cir_bin
          })
    
    vars_poly = pd.DataFrame({
        "rdplot_x": np.concatenate([x_plot_l, x_plot_r]),
        "rdplot_y": np.concatenate([y_hat_l, y_hat_r]).reshape(-1)
        })
    
    coef = pd.DataFrame({
        "Left": gamma_p1_l.reshape(-1),
        "Right": gamma_p1_r.reshape(-1)
        })
    
    return rdplot_output(coef, temp_plot, vars_bins, vars_poly,
                        [J_star_l,J_star_r], J_IMSE, J_MV, 
                        [scale_l,scale_r], [rscale_l,rscale_r],
                        [bin_avg_l,bin_avg_r], [bin_med_l,bin_med_r],
                        p, c, [h_l,h_r], [n_l,n_r], [n_h_l,n_h_r],
                        binselect_type, kernel_type)