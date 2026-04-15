#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rdrobust module

Created on Sat Jun  5 14:07:58 2021

@author: rmasini
"""

import numpy as np
import math
from scipy.linalg import qr

class rdrobust_output:
    def __init__(self, Estimate, bws, coef, se, t, pv, ci, beta_p_l, beta_p_r,
                 V_cl_l, V_cl_r, V_rb_l, V_rb_r, N, N_h, N_b, M,
                 tau_cl, tau_bc, c, p, q, bias, kernel, all,
                 vce, bwselect, level, masspoints):
    
        self.Estimate = Estimate
        self.bws = bws
        self.coef = coef
        self.se = se
        self.t = t
        self.pv = pv
        self.ci = ci
        self.beta_p_l = beta_p_l
        self.beta_p_r = beta_p_r
        self.V_cl_l = V_cl_l
        self.V_cl_r = V_cl_r
        self.V_rb_l = V_rb_l
        self.V_rb_r = V_rb_r
        self.N = N
        self.N_h = N_h
        self.N_b = N_b
        self.M = M
        self.tau_cl = tau_cl
        self.tau_bc = tau_bc
        self.c = c 
        self.p = p
        self.q = q
        self.bias = bias
        self.kernel = kernel
        self.all = all
        self.vce = vce
        self.bwselect = bwselect 
        self.level = level
        self.masspoints = masspoints
    
    def __repr__(self):
        print('Call: rdrobust')
        fw = 30
        fw_r = 14
        print('Number of Observations:'.ljust(fw),
              str(self.N[0]+self.N[1]).rjust(fw_r))
        print('Polynomial Order Est. (p):'.ljust(fw), str(self.p).rjust(fw_r))
        print('Polynomial Order Bias (q):'.ljust(fw), str(self.q).rjust(fw_r))
        print('Kernel:'.ljust(fw), str(self.kernel).rjust(fw_r))
        print('Bandwidth Selection:'.ljust(fw), str(self.bwselect).rjust(fw_r))
        print('Var-Cov Estimator:'.ljust(fw), str(self.vce).rjust(fw_r))
        print('')
        
        # Table Sides
        fw_n = 25
        fw_l = 10
        fw_r = 10
        print(''.ljust(fw_n),'Left'.rjust(fw_l), 'Right'.rjust(fw_r))
        print('-'*(fw_n + fw_l + fw_r + 3))
        print('Number of Observations'.ljust(fw_n),
              str(self.N[0]).rjust(fw_l),
              str(self.N[1]).rjust(fw_r))
        print('Number of Unique Obs.'.ljust(fw_n),
              str(self.M[0]).rjust(fw_l),
              str(self.M[1]).rjust(fw_r))
        print('Number of Effective Obs.'.ljust(fw_n),
              str(self.N_h[0]).rjust(fw_l),
              str(self.N_h[1]).rjust(fw_r))
        print('Bandwidth Estimation'.ljust(fw_n),
              str(round(self.bws.iloc[0,0],3)).rjust(fw_l),
              str(round(self.bws.iloc[0,1],3)).rjust(fw_r))
        print('Bandwidth Bias'.ljust(fw_n),
              str(round(self.bws.iloc[1,0],3)).rjust(fw_l),
              str(round(self.bws.iloc[1,1],3)).rjust(fw_r))
        print('rho (h/b)'.ljust(fw_n),
              str(round(self.bws.iloc[0,0]/self.bws.iloc[1,0],3)).rjust(fw_l),
              str(round(self.bws.iloc[0,1]/self.bws.iloc[1,1],3)).rjust(fw_l))
        print('')
        
        # Table Estimation
        fw_l = 15
        fw_c = 8
        fw_ci = 18
        n_dec = 3
        print('Method'.ljust(fw_l),'Coef.'.rjust(fw_c),
              'S.E.'.rjust(fw_c),'t-stat'.rjust(fw_c),
              'P>|t|'.rjust(fw_c), (str(self.level) + '% CI').center(fw_ci))
        print('-'*73)
        
        if self.all is None: method_id = (0,2)
        else: method_id = (0,1,2)
        for j in method_id:
            if j==0:
                print(self.coef.index[j].ljust(fw_l),
                      str(round(self.coef.iloc[j].item(),n_dec)).rjust(fw_c),
                      str(round(self.se.iloc[j].item(),n_dec)).rjust(fw_c),
                      str(round(self.t.iloc[j].item(),n_dec)).rjust(fw_c),
                      ("{:.3e}".format(self.pv.iloc[j].item())).rjust(fw_c+3),
                      ('[' + str(round(self.ci.iloc[j,0].item(),n_dec)) + ', ' + str(round(self.ci.iloc[j,1].item(),n_dec)) + ']').rjust(fw_ci))
            else:
                if self.all:
                    print(self.coef.index[j].ljust(fw_l),
                      str(round(self.coef.iloc[j].item(),n_dec)).rjust(fw_c),
                      str(round(self.se.iloc[j].item(),n_dec)).rjust(fw_c),
                      str(round(self.t.iloc[j].item(),n_dec)).rjust(fw_c),
                      ("{:.3e}".format(self.pv.iloc[j].item())).rjust(fw_c+3),
                      ('[' + str(round(self.ci.iloc[j,0].item(),n_dec)) + ', ' + str(round(self.ci.iloc[j,1].item(),n_dec)) + ']').rjust(fw_ci))
                else:
                    print(self.coef.index[j].ljust(fw_l),
                      '-'.rjust(fw_c),
                      '-'.rjust(fw_c),
                      str(round(self.t.iloc[j].item(),n_dec)).rjust(fw_c),
                      ("{:.3e}".format(self.pv.iloc[j].item())).rjust(fw_c+3),
                      ('[' + str(round(self.ci.iloc[j,0].item(),n_dec)) + ', ' + str(round(self.ci.iloc[j,1].item(),n_dec)) + ']').rjust(fw_ci))
        
        return ''

class rdplot_output:
    def __init__(self, coef, rdplot, vars_bins, vars_poly, J, J_IMSE, J_MV, 
                 scale, rscale, bin_avg, bin_med, p, c, h, N, N_h,
                 binselect, kernel):
        self.coef = coef
        self.rdplot = rdplot
        self.vars_bins = vars_bins
        self.vars_poly = vars_poly
        self.J = J
        self.J_IMSE = J_IMSE
        self.J_MV = J_MV
        self.scale = scale
        self.rscale = rscale
        self.bin_avg = bin_avg
        self.bin_med = bin_med
        self.p = p
        self.c = c
        self.h = h
        self.N = N
        self.N_h = N_h
        self.binselect = binselect
        self.kernel = kernel
        
    def __repr__(self):
        print('Call: rdplot')
        fw = 30
        fw_r = 14
        print('Number of Observations:'.ljust(fw),
              str(self.N[0]+self.N[1]).rjust(fw_r))
        print('Kernel:'.ljust(fw), str(self.kernel).rjust(fw_r))
        print('Polynomial Order Est. (p):'.ljust(fw), str(self.p).rjust(fw_r))
        print('')
        # Table Sides
        fw_n = 25
        fw_l = 10
        fw_r = 10
        nd = 3
        print(''.ljust(fw_n),'Left'.rjust(fw_l), 'Right'.rjust(fw_r))
        print('-'*(fw_n + fw_l + fw_r + 3))
        print('Number of Observations'.ljust(fw_n),
              str(self.N[0]).rjust(fw_l),
              str(self.N[1]).rjust(fw_r))
        print('Number of Effective Obs'.ljust(fw_n),
              str(self.N_h[0]).rjust(fw_l),
              str(self.N_h[1]).rjust(fw_r))
        print('Bandwith poly. fit (h)'.ljust(fw_n),
              str(round(self.h[0],nd)).rjust(fw_l),
              str(round(self.h[1],nd)).rjust(fw_r))
        print('Number of bins scale'.ljust(fw_n),
              str(self.scale[0]).rjust(fw_l),
              str(self.scale[1]).rjust(fw_r))
        print('Bins Selected'.ljust(fw_n),
              str(self.J[0]).rjust(fw_l),
              str(self.J[1]).rjust(fw_r))
        print('Average Bin Length'.ljust(fw_n),
              str(round(self.bin_avg[0], nd)).rjust(fw_l),
              str(round(self.bin_avg[1], nd)).rjust(fw_r))
        print('Median Bin Length'.ljust(fw_n),
              str(round(self.bin_med[0], nd)).rjust(fw_l),
              str(round(self.bin_med[1], nd)).rjust(fw_r))
        print('IMSE-optimal bins'.ljust(fw_n),
              str(round(self.J_IMSE[0], nd)).rjust(fw_l),
              str(round(self.J_IMSE[1], nd)).rjust(fw_r))
        print('Mimicking Variance bins'.ljust(fw_n),
              str(round(self.J_MV[0], nd)).rjust(fw_l),
              str(round(self.J_MV[1], nd)).rjust(fw_r))
        print('')
        print('Relative to IMSE-optimal:'.ljust(fw_n))
        print('Implied scale'.ljust(fw_n),
              str(round(self.rscale[0], nd)).rjust(fw_l),
              str(round(self.rscale[1], nd)).rjust(fw_r))
        print('WIMSE variance weight'.ljust(fw_n),
              str(round(1/(1+self.rscale[0]**3),nd)).rjust(fw_l),
              str(round(1/(1+self.rscale[1]**3),nd)).rjust(fw_r))
        print('WIMSE bias weight'.ljust(fw_n),
              str(round(self.rscale[0]**3/(1+self.rscale[0]**3),nd)).rjust(fw_l),
              str(round(self.rscale[1]**3/(1+self.rscale[1]**3),nd)).rjust(fw_r))
        return ''

class rdbwselect_output:
    def __init__(self, bws, bwselect, bw_list, kernel, p, q, c,
                 N, M, vce, masspoints):
        self.bws = bws
        self.bwselect = bwselect
        self.bw_list = bw_list
        self.kernel = kernel
        self.p = p
        self.q = q
        self.c = c 
        self.N = N
        self.M = M
        self.vce = vce
        self.masspoints = masspoints
    
    def __repr__(self, nd = 3):
        fw = 30
        fw_r = 14
        print('Call: rdbwselect')
        print('Number of Observations:'.ljust(fw),
              str(self.N[0]+self.N[1]).rjust(fw_r))
        print('Polynomial Order Est. (p):'.ljust(fw), str(self.p).rjust(fw_r))
        print('Polynomial Order Bias (q):'.ljust(fw), str(self.q).rjust(fw_r))
        print('Kernel:'.ljust(fw), str(self.kernel).rjust(fw_r))
        print('Bandwidth Selection:'.ljust(fw), str(self.bwselect).rjust(fw_r))
        print('Var-Cov Estimator:'.ljust(fw), str(self.vce).rjust(fw_r))
        print('')
        print(self.bws.round(nd))
        return ''
        
def tomat(x):
    return x.reshape(len(x),-1);

def ncol(x):
    try: d = x.shape[1]
    except: d = 1
    return d;

def crossprod(x, y = None):
    if y is None: return np.matmul(x.T,x)
    else: return np.matmul(x.T,y)

def nanmat(n, m = None):
    # Create a (n x m) matrix of NaN
    if m is None: M = np.empty((n,))
    else: M = np.empty((n,m,))    
    M.fill(np.nan)
    return M;

def inv_chol(x):
    # Given a matrix X it returns the inverse of X'X using Cholesky decomposition
    # No check is made if X'X is indeed positive definite!
    Linv = np.linalg.inv(np.linalg.cholesky(x))
    return crossprod(Linv,Linv)
        
def qrXXinv(x):
    return inv_chol(crossprod(x,x))

def complete_cases(x):
    return np.all(np.invert(np.isnan(x)), axis = 1)

def covs_drop_fun(z,tol = 1e-5):
    q,r,pivot = qr(a = z, pivoting = True)
    keep = pivot[np.abs(np.diagonal(r))>tol]
    return z[:,keep]
    
def rdrobust_kweight(X, c, h, kernel):
    
    u = (X-c)/h
    if kernel=="epanechnikov" or kernel=="epa":
        w = (0.75*(1-u**2)*(abs(u)<=1))/h
    elif kernel=="uniform" or kernel=="uni":
         w = (0.5*(abs(u)<=1))/h
    else:
        w = ((1-abs(u))*(abs(u)<=1))/h
    return w

def rdrobust_res(X, y, T, Z, m, hii, vce, matches, dups, dupsid, d):
    
    n = len(y)
    dT = dZ =  0
    if T is not None:
        dT = 1
    if Z is not None:
        dZ = ncol(Z)  
    res = nanmat(n,1+dT+dZ)
    if vce=="nn":
        for pos in range(n):
            rpos = dups[pos] - dupsid[pos]
            lpos = dupsid[pos] - 1
            while lpos+rpos < min(matches,n-1):
              if pos-lpos-1 < 0:
                  rpos += dups[pos+rpos+1]
              elif pos+rpos+1 >= n:
                  lpos += dups[pos-lpos-1]
              elif (X[pos]-X[pos-lpos-1]) > (X[pos+rpos+1]-X[pos]): 
                  rpos += dups[pos+rpos+1]
              elif (X[pos]-X[pos-lpos-1]) < (X[pos+rpos+1]-X[pos]):
                  lpos += dups[pos-lpos-1]
              else:
                  rpos += dups[pos+rpos+1]
                  lpos += dups[pos-lpos-1]
            ind_J = np.arange(max(0,pos-lpos), min(n,pos+rpos)+1)
            y_J   = sum(y[ind_J])-y[pos]
            Ji = len(ind_J)-1
            res[pos,0] = np.sqrt(Ji/(Ji+1))*(y[pos] - y_J/Ji)
            if T is not None:
                T_J = sum(T[ind_J])-T[pos]
                res[pos,1] = np.sqrt(Ji/(Ji+1))*(T[pos] - T_J/Ji)
            if Z is not None:
                for i in range(dZ):
                    Z_J = sum(Z[ind_J,i])-Z[pos,i]
                    res[pos,1+dT+i] = np.sqrt(Ji/(Ji+1))*(Z[pos,i] - Z_J/Ji)	
    else:
        
        if vce=="hc0": w = 1
        elif vce=="hc1": w = np.sqrt(n/(n-d))
        elif vce=="hc2":
            hii = hii.reshape(-1)
            w = np.sqrt(1/(1-hii))
        else:
            hii = hii.reshape(-1)
            w = 1/(1-hii)
        m = m.reshape(-1,ncol(m))
        res[:,0] = w*(y-m[:,0])
        if dT==1: res[:,1] = w*(T-m[:,1])
        if dZ>0:
           for i in range(dZ):
               res[:,1+dT+i] = w*(Z[:,i]- m[:,1+dT+i])
               
    return res

def rdrobust_vce(d, s, RX, res, C):
    k = ncol(RX)
    M = np.zeros((k,k))
    if C is None:
        w = 1
        if d==0:
            M  = crossprod(res*RX,res*RX)
        else:
            for i in range(d+1):
                SS = (res[:,i].reshape(-1,1))*res
                for j in range(d+1):
                    M += crossprod(RX*(s[i]*s[j])*SS[:,j].reshape(-1,1),RX)
    else:
        try: n = len(C)
        except: n = 1
        clusters = np.unique(C)
        g = len(clusters)
        w = ((n-1)/(n-k))*(g/(g-1))
        if d==0:
            for i in range(g):
                ind = C==clusters[i]
                Xi = RX[ind,:]
                ri = res[ind,:]
                Xr = crossprod(Xi,ri).T
                M = M + crossprod(Xr,Xr)
        else:
            for i in range(g):
                ind = (C==clusters[i])
                Xi = RX[ind,:]
                ri = res[ind,:]
                MHolder = np.zeros((1+d,k))
                for l in range(d+1):
                    MHolder[l,:] = crossprod(Xi,s[l]*ri[:,l]).T
                summedvalues = np.sum(MHolder, axis = 0)
                M = M + np.outer(summedvalues,summedvalues)
                    
    return w*M	 

def rdrobust_bw(Y, X, T, Z, C, W, c, o, nu, o_B, h_V, h_B, scale, 
                 vce, nnmatch, kernel, dups, dupsid, covs_drop_coll):
    
    
    dT = dZ = eC = 0
    w = rdrobust_kweight(X, c, h_V, kernel)
    if not np.isscalar(W): w = W*w
    ind_V = w> 0 
    eY = Y[ind_V]
    eX = X[ind_V]
    eW = w[ind_V]
    n_V = np.sum(ind_V)
    D_V = eY.copy()
    R_V = nanmat(n_V,o+1)
    for j in range(o+1): R_V[:,j] = (eX-c)**j
    invG_V = qrXXinv(R_V*np.sqrt(eW).reshape(-1,1))
    e_v = np.zeros((o+1,1))
    e_v[nu] = 1
    s = 1
    eT = eC = eZ = None
    if T is not None: 
        dT = 1
        eT = T[ind_V]
        D_V = np.column_stack((D_V,eT))
    if Z is not None:
        dZ = ncol(Z)
        eZ = Z[ind_V,:]
        D_V = np.column_stack((D_V,eZ))
        U = crossprod(R_V*eW.reshape(-1,1),D_V)
        ZWD  = crossprod(eZ*eW.reshape(-1,1),D_V)
        colsZ = np.arange(1+dT, max(2+dT+dZ-1,2+dT))
        UiGU =  crossprod(U[:,colsZ],np.matmul(invG_V,U)) 
        ZWZ = ZWD[:,colsZ] - UiGU[:,colsZ] 
        ZWY = ZWD[:,:(1+dT)] - UiGU[:,:(1+dT)] 
        if covs_drop_coll == 1:
            gamma = np.matmul(np.linalg.pinv(ZWZ),ZWY)
        else:
            gamma = np.matmul(inv_chol(ZWZ),ZWY)
        s = np.append(1, -gamma[:,0])
    
    if C is not None: eC =  C[ind_V] 
        
    beta_V = np.matmul(invG_V,crossprod(R_V*eW.reshape(-1,1),D_V))	
    if Z is None and T is not None:	
        tau_Y = math.factorial(nu)*beta_V[nu,0]
        tau_T = math.factorial(nu)*beta_V[nu,1]
        s = np.array([1/tau_T , -(tau_Y/tau_T**2)])
    
    if Z is not None and T is not None:
        s_T = np.append(1, -gamma[:,1])
        beta_Y = np.append(beta_V[nu,0],beta_V[nu,colsZ])
        tau_Y = math.factorial(nu)*np.matmul(s, beta_Y)
        beta_T = np.append(beta_V[nu,1],beta_V[nu,colsZ])
        tau_T = math.factorial(nu)*np.matmul(s_T, beta_T)
        s = (np.hstack([1/tau_T , -(tau_Y/tau_T**2) , 
            -(1/tau_T)*gamma[:,0] + (tau_Y/tau_T**2)*gamma[:,1]]))
    
    dups_V = dupsid_V = hii = predicts_V =0
    if vce == "nn": 
        dups_V   = dups[ind_V]
        dupsid_V = dupsid[ind_V]
    
    if vce=="hc0" or vce=="hc1" or vce=="hc2" or vce=="hc3":
        predicts_V = np.matmul(R_V,beta_V)
        if vce=="hc2" or vce=="hc3":
            hii = np.sum(np.matmul(R_V,invG_V)*(R_V*eW.reshape(-1,1)), axis = 1).reshape(-1,1)
    
    res_V = (rdrobust_res(eX, eY, eT, eZ, predicts_V, hii, vce, 
                          nnmatch, dups_V, dupsid_V, o+1))
      
    aux = rdrobust_vce(dT+dZ, s, R_V*eW.reshape(-1,1), res_V, eC)
    V_V = np.matmul(np.matmul(invG_V,aux),invG_V)[nu,nu]

    v = crossprod(R_V*eW.reshape(-1,1),((eX-c)/h_V)**(o+1))
    Hp = np.zeros(o+1)
    for j in range(o+1): Hp[j] = h_V**j
    BConst = (Hp*np.matmul(invG_V,v))[nu]
      
    w = rdrobust_kweight(X, c, h_B, kernel)
    if not np.isscalar(W): w = W*w
    ind = w> 0 
    n_B = sum(ind)
    eY = Y[ind]
    eX = X[ind]
    eW = w[ind]
    D_B = eY
    R_B = nanmat(n_B,o_B+1)
    for j in range(o_B+1): R_B[:,j] = (eX-c)**j
    invG_B = qrXXinv(R_B*np.sqrt(eW).reshape(-1,1))
    
    eT = eC = eZ = None
    if T is not None: 
        eT = T[ind]
        D_B = np.column_stack((D_B,eT))
    if Z is not None:
        eZ = Z[ind,:]
        D_B = np.column_stack((D_B,eZ))
    if C is not None:
        eC = C[ind]
      
    beta_B = np.matmul(invG_B,crossprod(R_B*eW.reshape(-1,1),D_B))
    BWreg=0
    if scale>0:
        e_B = np.zeros(o_B+1)
        e_B[o+1]=1
        dups_B = dupsid_B = hii = predicts_B = 0
        if vce=="nn":
            dups_B   = dups[ind]
            dupsid_B = dupsid[ind]
        if vce=="hc0" or vce=="hc1" or vce=="hc2" or vce=="hc3":
            predicts_B = np.matmul(R_B,beta_B)
            if vce=="hc2" or vce=="hc3":
                hii = np.sum(np.matmul(R_B,invG_B)*(R_B*eW.reshape(-1,1)), axis = 1).reshape(-1,1)
                
        res_B = (rdrobust_res(eX, eY, eT, eZ, predicts_B, hii, vce, nnmatch,
                              dups_B, dupsid_B,o_B+1))
        aux = rdrobust_vce(dT+dZ, s, R_B*eW.reshape(-1,1), res_B, eC)
        V_B = np.matmul(np.matmul(invG_B,aux),invG_B)[-1,-1]
        BWreg = 3*BConst**2*V_B
    try: beta_aux = beta_B[-1,:]
    except: beta_aux = beta_B[-1]
    B =  np.sqrt(2*(o+1-nu))*BConst*np.dot(s,beta_aux)
    V = (2*nu+1)*h_V**(2*nu+1)*V_V
    R = scale*(2*(o+1-nu))*BWreg
    rate = 1/(2*o+3)
    
    return V, B, R, rate