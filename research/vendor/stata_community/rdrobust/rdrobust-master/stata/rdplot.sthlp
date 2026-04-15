{smcl}
{* *!version 10.0.0  2025-06-30}{...}
{viewerjumpto "Syntax" "rdplot##syntax"}{...}
{viewerjumpto "Description" "rdplot##description"}{...}
{viewerjumpto "Options" "rdplot##options"}{...}
{viewerjumpto "Examples" "rdplot##examples"}{...}
{viewerjumpto "Stored results" "rdplot##stored_results"}{...}
{viewerjumpto "References" "rdplot##references"}{...}
{viewerjumpto "Authors" "rdplot##authors"}{...}

{title:Title}

{p 4 8}{cmd:rdplot} {hline 2} Data-Driven Regression Discontinuity Plots.{p_end}

{marker syntax}{...}
{title:Syntax}

{p 4 8}{cmd:rdplot } {it:depvar} {it:indepvar} {ifin} 
[{cmd:,} 
{cmd:c(}{it:#}{cmd:)} 
{cmd:nbins(}{it:# #}{cmd:)}
{cmd:binselect(}{it:binmethod}{cmd:)}
{cmd:scale(}{it:# #}{cmd:)}
{cmd:support(}{it:# #}{cmd:)}  
{cmd:p(}{it:#}{cmd:)}
{cmd:h(}{it:# #}{cmd:)} 
{cmd:kernel(}{it:kernelfn}{cmd:)}
{cmd:weights(}{it:weightsvar}{cmd:)}
{cmd:covs(}{it:covars}{cmd:)}
{cmd:covs_eval(}{it:covars_eval}{cmd:)}
{cmd:covs_drop(}{it:covsdropoption}{cmd:)}
{cmd:masspoints(}{it:masspointsoption}{cmd:)}
{cmd:ci(}{it:cilevel}{cmd:)}
{it:shade}
{cmd:graph_options(}{it:gphopts}{cmd:)}
{it:hide}
{it:genvars}
]{p_end}

{synoptset 28 tabbed}{...}

{marker description}{...}
{title:Description}

{p 4 8}{cmd:rdplot} implements several data-driven Regression Discontinuity (RD) plots, using either evenly-spaced or quantile-spaced partitioning. Two type of RD plots are constructed: (i) RD plots with binned sample means tracing out the underlying regression function, and (ii) RD plots with binned sample means
mimicking the underlying variability of the data. For technical and methodological details see 
{browse "https://rdpackages.github.io/references/Calonico-Cattaneo-Titiunik_2015_JASA.pdf":Calonico, Cattaneo and Titiunik (2015a)}.{p_end}

{p 8 8} Companion commands are: {help rdrobust:rdrobust} for point estimation and inference procedures, and {help rdbwselect:rdbwselect} for data-driven bandwidth selection.{p_end}

{p 8 8}A detailed introduction to this command is given in
{browse "https://rdpackages.github.io/references/Calonico-Cattaneo-Titiunik_2014_Stata.pdf":Calonico, Cattaneo and Titiunik (2014)},
and {browse "https://rdpackages.github.io/references/Calonico-Cattaneo-Farrell-Titiunik_2017_Stata.pdf":Calonico, Cattaneo, Farrell and Titiunik (2017)}. A companion {browse "www.r-project.org":R} package is also described in
{browse "https://rdpackages.github.io/references/Calonico-Cattaneo-Titiunik_2015_R.pdf":Calonico, Cattaneo and Titiunik (2015b)}.{p_end}

{p 4 8}Related Stata and R packages useful for inference in RD designs are described in the following website:{p_end}

{p 8 8}{browse "https://rdpackages.github.io":https://rdpackages.github.io}{p_end}


{marker options}{...}
{title:Options}

{dlgtab:Estimand}

{p 4 8}{cmd:c(}{it:#}{cmd:)} specifies the RD cutoff in {it:indepvar}.
Default is {cmd:c(0)}. 

{dlgtab:Bin Selection}

{p 4 8}{cmd:nbins(}{it:# #}{cmd:)} specifies the number of bins used to the left of the cutoff, denoted {it:J-}, and to the right of the cutoff, denoted {it:J+}, respectively.
If not specified, {it:J+} and {it:J-} are estimated using the method and options chosen below.

{p 4 8}{cmd:binselect(}{it:binmethod}{cmd:)} specifies the data-driven procedure to select the number of bins. This option is available only if {it:J-} and {it:J+} are not set manually using {cmd:nbins(.)}.
Options are:{p_end}
{p 8 12}{opt es} IMSE-optimal evenly-spaced method using spacings estimators.{p_end}
{p 8 12}{opt espr} IMSE-optimal evenly-spaced method using polynomial regression.{p_end}
{p 8 12}{opt esmv} mimicking variance evenly-spaced method using spacings estimators.{p_end}
{p 8 12}{opt esmvpr} mimicking variance evenly-spaced method using polynomial regression.{p_end}
{p 8 12}{opt qs} IMSE-optimal quantile-spaced method using spacings estimators.{p_end}
{p 8 12}{opt qspr} IMSE-optimal quantile-spaced method using polynomial regression.{p_end}
{p 8 12}{opt qsmv} mimicking variance quantile-spaced method using spacings estimators.{p_end}
{p 8 12}{opt qsmvpr} mimicking variance quantile-spaced method using polynomial regression.{p_end}
{p 8 12}Default is {cmd:binselect(esmv)}.{p_end}
{p 8 12}Note: procedures involving spacing estimators are not invariant to rearrangements of {it:depvar} when there are repeated values (i.e., mass points in the running variable).{p_end}

{p 4 8}{cmd:scale(}{it:# #}{cmd:)} specifies multiplicative factors, denoted {it:s-} and {it:s+}, respectively, to adjust the number of bins selected. Specifically, the number of bins used for the treatment and control groups will be
ceil({cmd:s- * J-}) and ceil({cmd:s+ * J+}), where J- and J+ denote the optimal numbers of bins originally computed for each group. 
Default is {cmd:scale(1 1)}.

{p 4 8}{cmd:support(}{it:# #}{cmd:)} sets an optional extended support of the running variable to be used in the construction of the bins. Default is the sample range.

{p 4 8}{cmd:masspoints(}{it:masspointsoption}{cmd:)} checks and controls for repeated observations in the running variable. 
Options are:{p_end}
{p 8 12}{opt off}  ignores the presence of mass points. {p_end}
{p 8 12}{opt check}  looks for and reports the number of unique observations at each side of the cutoff.   {p_end}
{p 8 12}{opt adjust}  sets {cmd:binselect(}{it:binmethod}{cmd:)} as polynomial regression when mass points are present. {p_end}
{p 8 12} Default option is {cmd:masspoints(adjust)}.{p_end}

{dlgtab:Polynomial Fit}

{p 4 8}{cmd:p(}{it:#}{cmd:)} specifies the order of the (global) polynomial fit used to approximate the population conditional expectation functions for control and treated units.
Default is {cmd:p(4)}.

{p 4 8}{cmd:h(}{it:# #}{cmd:)} specifies the bandwidth used to construct the (global) polynomial fits given the kernel choice {cmd:kernel(.)}.
If not specified, the bandwidths are chosen to span the full support of the data. If two bandwidths are specified, the first bandwidth is used for the data below the cutoff and the second bandwidth is used for the data above the cutoff.

{p 4 8}{cmd:kernel(}{it:kernelfn}{cmd:)} specifies the kernel function used to construct the local-polynomial estimator(s). Options are: {opt tri:angular}, {opt epa:nechnikov}, and {opt uni:form}.
Default is {cmd:kernel(uniform)} (i.e., equal/no weighting to all observations on the support of the kernel).

{p 4 8}{cmd:weights(}{it:weightsvar}{cmd:)} is the variable used for optional weighting of the estimation procedure. The unit-specific weights multiply the kernel function.{p_end}

{p 4 8}{cmd:covs(}{it:covars}{cmd:)} additional covariates used to construct the local-polynomial estimator(s).{p_end}

{p 4 8}{cmd:covs_eval(}{it:covars_eval}{cmd:)} sets the evaluation points for the additional covariates, when included in the estimation. Options are: {opt 0} and {opt mean} (default).

{p 4 8}{cmd:covs_drop(}{it:covsdropoption}{cmd:)} assess collinearity in additional covariates used for estimation and inference. Options {opt pinv} (default choice) and {opt invsym} drops collinear additional covariates, differing only in the type of inverse function used. Option {opt off} omits the check for collinear additional covariates.{p_end}

{dlgtab:Plot Options}

{p 4 8}{cmd:ci(}{it:cilevel}{cmd:)} graphical option to display confidence intervals of level {it:cilevel} for each bin. 

{p 4 8}{cmd:shade} graphical option to replace confidence intervals with shaded areas.

{p 4 8}{cmd:graph_options(}{it:gphopts}{cmd:)} graphical options to be passed on to the underlying graph command.

{p 4 8}{cmd:hide} omits the RD plot.

{dlgtab:Generate Variables}

{p 4 8}{it:genvars} generates new variables storing the following results.{p_end}
{p 8 12}{opt rdplot_id} unique bin ID for each observation. Negative natural numbers are assigned to observations to the left of the cutoff, and positive natural numbers are assigned to observations to the right of the cutoff.{p_end}
{p 8 12}{opt rdplot_N} number of observations in the corresponding bin for each observation.{p_end}
{p 8 12}{opt rdplot_min_bin} lower end value of the bin for each observation.{p_end}
{p 8 12}{opt rdplot_max_bin} upper end value of the bin for each observation.{p_end}
{p 8 12}{opt rdplot_mean_bin} middle point of the corresponding bin for each observation.{p_end}
{p 8 12}{opt rdplot_mean_x} sample mean of the running variable within the corresponding bin for each observation.{p_end}
{p 8 12}{opt rdplot_mean_y} sample mean of the outcome variable within the corresponding bin for each observation.{p_end}
{p 8 12}{opt rdplot_se_y} standard deviation of the mean of the outcome variable within the corresponding bin for each observation.{p_end}
{p 8 12}{opt rdplot_ci_l} lower end value of the confidence interval for the sample mean of the outcome variable within the corresponding bin for each observation.{p_end}
{p 8 12}{opt rdplot_ci_r} upper end value of the confidence interval for the sample mean of the outcome variable within the corresponding bin for each observation.{p_end}
{p 8 12}{opt rdplot_hat_y} predicted value of the outcome variable given by the global polynomial estimator.{p_end}


    {hline}


{marker examples}{...}
{title:Example: Cattaneo, Frandsen and Titiunik (2015) Incumbency Data}

{p 4 8}Setup{p_end}
{p 8 8}{cmd:. use rdrobust_senate.dta}{p_end}

{p 4 8}Basic specification with title{p_end}
{p 8 8}{cmd:. rdplot vote margin, graph_options(title(RD Plot))}{p_end}

{p 4 8}Quadratic global polynomial with confidence bands{p_end}
{p 8 8}{cmd:. rdplot vote margin, p(2) ci(95) shade}{p_end}

{marker stored_results}{...}
{title:Stored results}

{p 4 8}{cmd:rdplot} stores the following in {cmd:e()}:

{synoptset 20 tabbed}{...}
{p2col 5 20 24 2: Scalars}{p_end}
{synopt:{cmd:e(N_l)}}original number of observations to the left of the cutoff{p_end}
{synopt:{cmd:e(N_r)}}original number of observations to the right of the cutoff{p_end}
{synopt:{cmd:e(c)}}cutoff value{p_end}
{synopt:{cmd:e(J_star_l)}}selected number of bins to the left of the cutoff{p_end}
{synopt:{cmd:e(J_star_r)}}selected number of bins to the right of the cutoff{p_end}

{p2col 5 20 24 2: Macros}{p_end}
{synopt:{cmd:e(binselect)}}method used to compute the optimal number of bins{p_end}

{synoptset 20 tabbed}{...}
{p2col 5 20 24 2: Matrices}{p_end}
{synopt:{cmd:e(coef_l)}}coefficients of the {it:p}-th order polynomial estimated to the left of the cutoff{p_end}
{synopt:{cmd:e(coef_r)}}coefficients of the {it:p}-th order polynomial estimated to the right of the cutoff{p_end}
{synopt:{cmd:e(coef_covs)}}coefficients of the additional covariates, only returned when {cmd:covs()} are used{p_end}


{marker references}{...}
{title:References}

{p 4 8}Calonico, S., M. D. Cattaneo, M. H. Farrell, and R. Titiunik. 2017.
{browse "https://rdpackages.github.io/references/Calonico-Cattaneo-Farrell-Titiunik_2017_Stata.pdf":rdrobust: Software for Regression Discontinuity Designs}.
{it:Stata Journal} 17(2): 372-404.{p_end}

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



