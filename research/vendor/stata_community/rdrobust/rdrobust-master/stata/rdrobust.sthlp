{smcl}
{* *!version 10.0.0  2025-06-30}{...}
{viewerjumpto "Syntax" "rdrobust##syntax"}{...}
{viewerjumpto "Description" "rdrobust##description"}{...}
{viewerjumpto "Options" "rdrobust##options"}{...}
{viewerjumpto "Examples" "rdrobust##examples"}{...}
{viewerjumpto "Stored results" "rdrobust##stored_results"}{...}
{viewerjumpto "References" "rdrobust##references"}{...}
{viewerjumpto "Authors" "rdrobust##authors"}{...}

{title:Title}

{p 4 8}{cmd:rdrobust} {hline 2} Local Polynomial Regression Discontinuity Estimation with Robust Bias-Corrected Confidence Intervals and Inference Procedures.{p_end}

{marker syntax}{...}
{title:Syntax}

{p 4 8}{cmd:rdrobust} {it:depvar} {it:runvar} {ifin} 
[{cmd:,} 
{cmd:c(}{it:#}{cmd:)} 
{cmd:fuzzy(}{it:fuzzyvar [sharpbw]}{cmd:)}
{cmd:deriv(}{it:#}{cmd:)}
{cmd:scalepar(}{it:#}{cmd:)}
{cmd:p(}{it:#}{cmd:)} 
{cmd:q(}{it:#}{cmd:)}
{cmd:h(}{it:# #}{cmd:)} 
{cmd:b(}{it:# #}{cmd:)}
{cmd:rho(}{it:#}{cmd:)}
{cmd:covs(}{it:covars}{cmd:)}
{cmd:covs_drop(}{it:covsdropoption}{cmd:)}
{cmd:kernel(}{it:kernelfn}{cmd:)}
{cmd:weights(}{it:weightsvar}{cmd:)}
{cmd:bwselect(}{it:bwmethod}{cmd:)}
{cmd:scaleregul(}{it:#}{cmd:)}
{cmd:masspoints(}{it:masspointsoption}{cmd:)}
{cmd:bwcheck(}{it:#}{cmd:)}
{cmd:bwrestrict(}{it:bwropt}{cmd:)}
{cmd:stdvars(}{it:stdopt}{cmd:)}
{cmd:vce(}{it:vcetype [vceopt1 vceopt2]}{cmd:)}
{cmd:level(}{it:#}{cmd:)}
{cmd:detail} 
{cmd:all} 
]{p_end}

{synoptset 28 tabbed}{...}

{marker description}{...}
{title:Description}

{p 4 8}{cmd:rdrobust} implements local polynomial Regression Discontinuity (RD) point estimators with robust bias-corrected confidence intervals and inference procedures developed in
{browse "https://rdpackages.github.io/references/Calonico-Cattaneo-Titiunik_2014_ECMA.pdf":Calonico, Cattaneo and Titiunik (2014a)},
{browse "https://rdpackages.github.io/references/Calonico-Cattaneo-Farrell_2018_JASA.pdf":Calonico, Cattaneo and Farrell (2018)},
{browse "https://rdpackages.github.io/references/Calonico-Cattaneo-Farrell-Titiunik_2019_RESTAT.pdf":Calonico, Cattaneo, Farrell and Titiunik (2019)}, 
and {browse "https://rdpackages.github.io/references/Calonico-Cattaneo-Farrell_2020_ECTJ.pdf":Calonico, Cattaneo and Farrell (2020)}.
It also computes alternative estimation and inference procedures available in the literature.{p_end}

{p 8 8} Companion commands are: {help rdbwselect:rdbwselect} for data-driven bandwidth selection, and {help rdplot:rdplot} for data-driven RD plots (see
{browse "https://rdpackages.github.io/references/Calonico-Cattaneo-Titiunik_2015_JASA.pdf":Calonico, Cattaneo and Titiunik (2015a)} for details).{p_end}

{p 8 8}A detailed introduction to this command is given in
{browse "https://rdpackages.github.io/references/Calonico-Cattaneo-Titiunik_2014_Stata.pdf":Calonico, Cattaneo and Titiunik (2014b)},
and {browse "https://rdpackages.github.io/references/Calonico-Cattaneo-Farrell-Titiunik_2017_Stata.pdf":Calonico, Cattaneo, Farrell and Titiunik (2017)}. A companion {browse "www.r-project.org":R} package is also described in
{browse "https://rdpackages.github.io/references/Calonico-Cattaneo-Titiunik_2015_R.pdf":Calonico, Cattaneo and Titiunik (2015b)}.{p_end}

{p 4 8}Related Stata and R packages useful for inference in RD designs are described in the following website:{p_end}

{p 8 8}{browse "https://rdpackages.github.io/":https://rdpackages.github.io/}{p_end}


{marker options}{...}
{title:Options}

{dlgtab:Estimand}

{p 4 8}{cmd:c(}{it:#}{cmd:)} specifies the RD cutoff for {it:indepvar}.
Default is {cmd:c(0)}.{p_end}

{p 4 8}{cmd:fuzzy(}{it:fuzzyvar [sharpbw]}{cmd:)} specifies the treatment status variable used to implement fuzzy RD estimation (or Fuzzy Kink RD if {cmd:deriv(1)} is also specified).
Default is Sharp RD design and hence this option is not used.
If the option {it:sharpbw} is set, the fuzzy RD estimation is performed using a bandwidth selection procedure for the sharp RD model. This option is automatically selected if there is perfect compliance at either side of the threshold.
{p_end}

{p 4 8}{cmd:deriv(}{it:#}{cmd:)} specifies the order of the derivative of the regression functions to be estimated.
Default is {cmd:deriv(0)} (for Sharp RD, or for Fuzzy RD if {cmd:fuzzy(.)} is also specified). Setting {cmd:deriv(1)} results in estimation of a Kink RD design (up to scale), or Fuzzy Kink RD if {cmd:fuzzy(.)} is also specified.{p_end}

{p 4 8}{cmd:scalepar(}{it:#}{cmd:)} specifies scaling factor for RD parameter of interest. This option is useful when the estimator of interest requires a known multiplicative factor rescaling (e.g., Sharp Kink RD).
Default is {cmd:scalepar(1)} (no rescaling).{p_end}

{dlgtab:Local Polynomial Regression}

{p 4 8}{cmd:p(}{it:#}{cmd:)} specifies the order of the local polynomial used to construct the point estimator.
Default is {cmd:p(1)} (local linear regression).{p_end}

{p 4 8}{cmd:q(}{it:#}{cmd:)} specifies the order of the local polynomial used to construct the bias correction.
Default is {cmd:q(2)} (local quadratic regression).{p_end}

{p 4 8}{cmd:h(}{it:# #}{cmd:)} specifies the main bandwidth ({it:h}) used to construct the RD point estimator. If not specified, bandwidth {it:h} is computed by the companion command {help rdbwselect:rdbwselect}.
If two bandwidths are specified, the first bandwidth is used for the data below the cutoff and the second bandwidth is used for the data above the cutoff.{p_end}

{p 4 8}{cmd:b(}{it:# #}{cmd:)} specifies the bias bandwidth ({it:b}) used to construct the bias-correction estimator. If not specified, bandwidth {it:b} is computed by the companion command {help rdbwselect:rdbwselect}.
If two bandwidths are specified, the first bandwidth is used for the data below the cutoff and the second bandwidth is used for the data above the cutoff.{p_end}

{p 4 8}{cmd:rho(}{it:#}{cmd:)} specifies the value of {it:rho}, so that the bias bandwidth {it:b} equals {it:b}={it:h}/{it:rho}.
Default is {cmd:rho(1)} if {it:h} is specified but {it:b} is not.{p_end}

{p 4 8}{cmd:covs(}{it:covars}{cmd:)} specifies additional covariates to be used for estimation and inference.{p_end}

{p 4 8}{cmd:covs_drop(}{it:covsdropoption}{cmd:)} assess collinearity in additional covariates used for estimation and inference. Options {opt pinv} (default choice) and {opt invsym} drops collinear additional covariates, differing only in the type of inverse function used. Option {opt off} omits the check for collinear additional covariates.{p_end}

{p 4 8}{cmd:kernel(}{it:kernelfn}{cmd:)} specifies the kernel function used to construct the local-polynomial estimator(s). Options are: {opt tri:angular}, {opt epa:nechnikov}, and {opt uni:form}.
Default is {cmd:kernel(triangular)}.{p_end}

{p 4 8}{cmd:weights(}{it:weightsvar}{cmd:)} is the variable used for optional weighting of the estimation procedure. The unit-specific weights multiply the kernel function.{p_end}

{dlgtab:Bandwidth Selection}

{p 4 8}{cmd:bwselect(}{it:bwmethod}{cmd:)} specifies the bandwidth selection procedure to be used. By default it computes both {it:h} and {it:b}, unless {it:rho} is specified, in which case it only computes {it:h} and sets {it:b}={it:h}/{it:rho}.
Options are:{p_end}
{p 8 12}{opt mserd} one common MSE-optimal bandwidth selector for the RD treatment effect estimator.{p_end}
{p 8 12}{opt msetwo} two different MSE-optimal bandwidth selectors (below and above the cutoff) for the RD treatment effect estimator.{p_end}
{p 8 12}{opt msesum} one common MSE-optimal bandwidth selector for the sum of regression estimates (as opposed to difference thereof).{p_end}
{p 8 12}{opt msecomb1} for min({opt mserd},{opt msesum}).{p_end}
{p 8 12}{opt msecomb2} for median({opt msetwo},{opt mserd},{opt msesum}), for each side of the cutoff separately.{p_end}
{p 8 12}{opt cerrd} one common CER-optimal bandwidth selector for the RD treatment effect estimator.{p_end}
{p 8 12}{opt certwo} two different CER-optimal bandwidth selectors (below and above the cutoff) for the RD treatment effect estimator.{p_end}
{p 8 12}{opt cersum} one common CER-optimal bandwidth selector for the sum of regression estimates (as opposed to difference thereof).{p_end}
{p 8 12}{opt cercomb1} for min({opt cerrd},{opt cersum}).{p_end}
{p 8 12}{opt cercomb2} for median({opt certwo},{opt cerrd},{opt cersum}), for each side of the cutoff separately.{p_end}
{p 8 12}Note: MSE = Mean Square Error; CER = Coverage Error Rate.{p_end}
{p 8 12}Default is {cmd:bwselect(mserd)}. For details on implementation see
{browse "https://rdpackages.github.io/references/Calonico-Cattaneo-Titiunik_2014_ECMA.pdf":Calonico, Cattaneo and Titiunik (2014a)},
{browse "https://rdpackages.github.io/references/Calonico-Cattaneo-Farrell_2018_JASA.pdf":Calonico, Cattaneo and Farrell (2017)},
{browse "https://rdpackages.github.io/references/Calonico-Cattaneo-Farrell_2020_ECTJ.pdf":Calonico, Cattaneo and Farrell (2020)},
and {browse "https://rdpackages.github.io/references/Calonico-Cattaneo-Farrell-Titiunik_2019_RESTAT.pdf":Calonico, Cattaneo, Farrell and Titiunik (2019)},
and the companion software articles.{p_end}

{p 4 8}{cmd:scaleregul(}{it:#}{cmd:)} specifies scaling factor for the regularization term added to the denominator of the bandwidth selectors. Setting {cmd:scaleregul(0)} removes the regularization term from the bandwidth selectors.
Default is {cmd:scaleregul(1)}.{p_end}

{p 4 8}{cmd:masspoints(}{it:masspointsoption}{cmd:)} checks and controls for repeated observations in the running variable. 
Options are:{p_end}
{p 8 12}{opt off}  ignores the presence of mass points. {p_end}
{p 8 12}{opt check}  looks for and reports the number of unique observations at each side of the cutoff.   {p_end}
{p 8 12}{opt adjust}  controls that the preliminary bandwidths used in the calculations contain a minimal number of unique observations. By default it uses 10 observations, but it can be manually adjusted with the option {cmd:bwcheck}.{p_end}
{p 8 12} Default option is {cmd:masspoints(adjust)}.{p_end}
		
{p 4 8}{cmd:bwcheck(}{it:bwcheck}{cmd:)} if a positive integer is provided, the preliminary bandwidth used in the calculations is enlarged so that at least {it:bwcheck} unique observations are used. {p_end}
  
{p 4 8}{cmd:bwrestrict(}{it:bwropt}{cmd:)} if set {opt on}, computed bandwidths are restricted to lie within the range of {it:runvar}. Default is {opt on}.{p_end}

{p 4 8}{cmd:stdvars(}{it:stdopt}{cmd:)} if set {opt on}, {it:depvar} and {it:runvar} are standardized before computing the bandwidths. Default is {opt off}.{p_end}

{dlgtab:Variance-Covariance Estimation}

{p 4 8}{cmd:vce(}{it:vcetype [vceopt1 vceopt2]}{cmd:)} specifies the procedure used to compute the variance-covariance matrix estimator.
Options are:{p_end}
{p 8 12}{cmd:vce(nn }{it:[nnmatch]}{cmd:)} for heteroskedasticity-robust nearest neighbor variance estimator with {it:nnmatch} indicating the minimum number of neighbors to be used.{p_end}
{p 8 12}{cmd:vce(hc0)} for heteroskedasticity-robust plug-in residuals variance estimator without weights.{p_end}
{p 8 12}{cmd:vce(hc1)} for heteroskedasticity-robust plug-in residuals variance estimator with {it:hc1} weights.{p_end}
{p 8 12}{cmd:vce(hc2)} for heteroskedasticity-robust plug-in residuals variance estimator with {it:hc2} weights.{p_end}
{p 8 12}{cmd:vce(hc3)} for heteroskedasticity-robust plug-in residuals variance estimator with {it:hc3} weights.{p_end}
{p 8 12}{cmd:vce(nncluster }{it:clustervar [nnmatch]}{cmd:)} for cluster-robust nearest neighbor variance estimation using with {it:clustervar} indicating the cluster ID variable and {it: nnmatch} matches indicating the minimum number of neighbors to be used.{p_end}
{p 8 12}{cmd:vce(cluster }{it:clustervar}{cmd:)} for cluster-robust plug-in residuals variance estimation with degrees-of-freedom weights and {it:clustervar} indicating the cluster ID variable.{p_end}
{p 8 12}Default is {cmd:vce(nn 3)}.{p_end}

{p 4 8}{cmd:level(}{it:#}{cmd:)} specifies confidence level for confidence intervals.
Default is {cmd:level(95)}.{p_end}

{dlgtab:Other Options}

{p 4 8}{cmd:all} if specified, {cmd:rdrobust} reports three different procedures:{p_end}
{p 8 12}   (i) conventional RD estimates with conventional variance estimator.{p_end}
{p 8 12}  (ii) bias-corrected RD estimates with conventional variance estimator.{p_end}
{p 8 12} (iii) bias-corrected RD estimates with robust variance estimator.{p_end}

{p 4 8}{cmd:detail} if specified, {cmd:rdrobust} reports the original output up to version 9.2.0{p_end}


   {hline}


{marker examples}{...}
{title:Example: Cattaneo, Frandsen and Titiunik (2015) Incumbency Data}

{p 4 8}Setup{p_end}
{p 8 8}{cmd:. use rdrobust_senate.dta}{p_end}

{p 4 8}Robust RD Estimation using MSE bandwidth selection procedure{p_end}
{p 8 8}{cmd:. rdrobust vote margin}{p_end}

{p 4 8}Robust RD Estimation with both bandwidths set to 15{p_end}
{p 8 8}{cmd:. rdrobust vote margin, h(15)}{p_end}

{p 4 8}Other generic examples ({cmd:y} outcome variable, {cmd:x} running variable, {cmd:t} treatment take-up indicator):

{p 8 8}Estimation for Sharp RD designs{p_end}
{p 12 12}{cmd:. rdrobust y x, deriv(0)}{p_end}

{p 8 8}Estimation for Sharp Kink RD designs{p_end}
{p 12 12}{cmd:. rdrobust y x, deriv(1)}{p_end}

{p 8 8}Estimation for Fuzzy RD designs{p_end}
{p 12 12}{cmd:. rdrobust y x, fuzzy(t)}{p_end}

{p 8 8}Estimation for Fuzzy Kink RD designs{p_end}
{p 12 12}{cmd:. rdrobust y x, fuzzy(t) deriv(1)}{p_end}


{marker stored_results}{...}
{title:Stored results}

{p 4 8}{cmd:rdrobust} stores the following in {cmd:e()}:

{synoptset 20 tabbed}{...}
{p2col 5 20 24 2: Scalars}{p_end}
{synopt:{cmd:e(N)}}original number of observations{p_end}
{synopt:{cmd:e(N_l)}}original number of observations to the left of the cutoff{p_end}
{synopt:{cmd:e(N_r)}}original number of observations to the right of the cutoff{p_end}
{synopt:{cmd:e(N_h_l)}}effective number of observations (given by the bandwidth h_l) used to the left of the cutoff{p_end}
{synopt:{cmd:e(N_h_r)}}effective number of observations (given by the bandwidth h_r) used to the right of the cutoff{p_end}
{synopt:{cmd:e(N_b_l)}}effective number of observations (given by the bandwidth b_l) used to the left of the cutoff{p_end}
{synopt:{cmd:e(N_b_r)}}effective number of observations (given by the bandwidth b_r) used to the right of the cutoff{p_end}
{synopt:{cmd:e(c)}}cutoff value{p_end}
{synopt:{cmd:e(p)}}order of the polynomial used for estimation of the regression function{p_end}
{synopt:{cmd:e(q)}}order of the polynomial used for estimation of the bias of the regression function estimator{p_end}
{synopt:{cmd:e(h_l)}}bandwidth used for estimation of the regression function below the cutoff{p_end}
{synopt:{cmd:e(h_r)}}bandwidth used for estimation of the regression function above the cutoff{p_end}
{synopt:{cmd:e(b_l)}}bandwidth used for estimation of the bias of the regression function estimator below the cutoff{p_end}
{synopt:{cmd:e(b_r)}}bandwidth used for estimation of the bias of the regression function estimator above the cutoff{p_end}
{synopt:{cmd:e(tau_cl)}}conventional local-polynomial RD estimate{p_end}
{synopt:{cmd:e(tau_cl_l)}}conventional local-polynomial left estimate{p_end}
{synopt:{cmd:e(tau_cl_r)}}conventional local-polynomial right estimate{p_end}
{synopt:{cmd:e(tau_bc)}}bias-corrected local-polynomial RD estimate{p_end}
{synopt:{cmd:e(tau_bc_l)}}bias-corrected local-polynomial left estimate{p_end}
{synopt:{cmd:e(tau_bc_r)}}bias-corrected local-polynomial right estimate{p_end}
{synopt:{cmd:e(se_tau_cl)}}conventional standard error of the local-polynomial RD estimator{p_end}
{synopt:{cmd:e(se_tau_rb)}}robust standard error of the local-polynomial RD estimator{p_end}
{synopt:{cmd:e(bias_l)}}estimated bias for the local-polynomial RD estimator below the cutoff{p_end}
{synopt:{cmd:e(bias_r)}}estimated bias for the local-polynomial RD estimator above the cutoff{p_end}

{p2col 5 20 24 2: Macros}{p_end}
{synopt:{cmd:e(runningvar)}}name of running variable{p_end}
{synopt:{cmd:e(outcomevar)}}name of outcome variable{p_end}
{synopt:{cmd:e(clustvar)}}name of cluster variable{p_end}
{synopt:{cmd:e(covs)}}name of covariates{p_end}
{synopt:{cmd:e(vce_select)}}vcetype specified in vce(){p_end}
{synopt:{cmd:e(bwselect)}}bandwidth selection choice{p_end}
{synopt:{cmd:e(kernel)}}kernel choice{p_end}

{p2col 5 20 24 2: Matrices}{p_end}
{synopt:{cmd:e(beta_Y_p_r)}}conventional p-order local-polynomial estimates to the right of the cutoff for the outcome variable{p_end}
{synopt:{cmd:e(beta_Y_p_l)}}conventional p-order local-polynomial estimates to the left of the cutoff for the outcome variable{p_end}
{synopt:{cmd:e(beta_T_p_r)}}conventional p-order local-polynomial estimates to the right of the cutoff for the first stage (fuzzy RD){p_end}
{synopt:{cmd:e(beta_T_p_l)}}conventional p-order local-polynomial estimates to the left of the cutoff for the first stage (fuzzy RD){p_end}
{synopt:{cmd:e(beta_covs)}}coefficients of the additional covariates, only returned when {cmd:covs()} are used{p_end}
{synopt:{cmd:e(V_cl_r)}}conventional variance-covariance matrix to the right of the cutoff{p_end}
{synopt:{cmd:e(V_cl_l)}}conventional variance-covariance matrix to the left of the cutoff{p_end}
{synopt:{cmd:e(V_rb_r)}}robust variance-covariance matrix to the right of the cutoff{p_end}
{synopt:{cmd:e(V_rb_l)}}robust variance-covariance matrix to the left of the cutoff{p_end}

{marker references}{...}
{title:References}

{p 4 8}Calonico, S., M. D. Cattaneo, and M. H. Farrell. 2020.
{browse "https://rdpackages.github.io/references/Calonico-Cattaneo-Farrell_2020_ECTJ.pdf":Optimal Bandwidth Choice for Robust Bias Corrected Inference in Regression Discontinuity Designs}.
{it:Econometrics Journal} 23(2): 192-210.{p_end}

{p 4 8}Calonico, S., M. D. Cattaneo, and M. H. Farrell. 2018.
{browse "https://rdpackages.github.io/references/Calonico-Cattaneo-Farrell_2018_JASA.pdf":On the Effect of Bias Estimation on Coverage Accuracy in Nonparametric Inference}.
{it:Journal of the American Statistical Association} 113(522): 767-779.{p_end}

{p 4 8}Calonico, S., M. D. Cattaneo, M. H. Farrell, and R. Titiunik. 2019.
{browse "https://rdpackages.github.io/references/Calonico-Cattaneo-Farrell-Titiunik_2019_RESTAT.pdf":Regression Discontinuity Designs using Covariates}.
{it:Review of Economics and Statistics}, 101(3): 442-451.{p_end}

{p 4 8}Calonico, S., M. D. Cattaneo, M. H. Farrell, and R. Titiunik. 2017.
{browse "https://rdpackages.github.io/references/Calonico-Cattaneo-Farrell-Titiunik_2017_Stata.pdf":rdrobust: Software for Regression Discontinuity Designs}.
{it:Stata Journal} 17(2): 372-404.{p_end}

{p 4 8}Calonico, S., M. D. Cattaneo, and R. Titiunik. 2014a.
{browse "https://rdpackages.github.io/references/Calonico-Cattaneo-Titiunik_2014_ECMA.pdf":Robust Nonparametric Confidence Intervals for Regression-Discontinuity Designs}.
{it:Econometrica} 82(6): 2295-2326.{p_end}

{p 4 8}Calonico, S., M. D. Cattaneo, and R. Titiunik. 2014b.
{browse "https://rdpackages.github.io/references/Calonico-Cattaneo-Titiunik_2014_Stata.pdf":Robust Data-Driven Inference in the Regression-Discontinuity Design}.
{it:Stata Journal} 14(4): 909-946.{p_end}

{p 4 8}Calonico, S., M. D. Cattaneo, and R. Titiunik. 2015a.
{browse "https://rdpackages.github.io/references/Calonico-Cattaneo-Titiunik_2015_JASA.pdf":Optimal Data-Driven Regression Discontinuity Plots}.
{it:Journal of the American Statistical Association} 110(512): 1753-1769.{p_end}

{p 4 8}Calonico, S., M. D. Cattaneo, and R. Titiunik. 2015b.
{browse "https://rdpackages.github.io/references/Calonico-Cattaneo-Titiunik_2015_R.pdf":rdrobust: An R Package for Robust Nonparametric Inference in Regression-Discontinuity Designs}.
{it:R Journal} 7(1): 38-51.{p_end}

{p 4 8}Cattaneo, M. D., B. Frandsen, and R. Titiunik. 2015.
{browse "https://rdpackages.github.io/references/Cattaneo-Frandsen-Titiunik_2015_JCI.pdf":Randomization Inference in the Regression Discontinuity Design: An Application to Party Advantages in the U.S. Senate}.
{it:Journal of Causal Inference} 3(1): 1-24.{p_end} 

{marker authors}{...}
{title:Authors}

{p 4 8}Sebastian Calonico, University of California, Davis, CA.
{browse "mailto:scalonico@ucdavis.edu":scalonico@ucdavis.edu}.{p_end}

{p 4 8}Matias D. Cattaneo, Princeton University, Princeton, NJ.
{browse "mailto:cattaneo@princeton.edu":cattaneo@princeton.edu}.{p_end}

{p 4 8}Max H. Farrell, University of California, Santa Barbara, CA.
{browse "mailto:maxhfarrell@ucsb.edu":maxhfarrell@ucsb.edu}.{p_end}

{p 4 8}Rocio Titiunik, Princeton University, Princeton, NJ.
{browse "mailto:titiunik@princeton.edu":titiunik@princeton.edu}.{p_end}


