{smcl}
{* *! version 6.0  2014-10-14}{...}
{viewerjumpto "Syntax" "rdbwselect##syntax"}{...}
{viewerjumpto "Description" "rdbwselect##description"}{...}
{viewerjumpto "Options" "rdbwselect##options"}{...}
{viewerjumpto "Examples" "rdbwselect##examples"}{...}
{viewerjumpto "Saved results" "rdbwselect##saved_results"}{...}

{title:Title}

{p 4 8}{cmd:rdbwselect_2014} {hline 2} Deprecated Bandwidth Selection Procedures for Local-Polynomial Regression-Discontinuity Estimators.{p_end}

{p 4 8}{ul:Important}: this command is no longer supported or updated, and it is made available only for backward compatibility purposes. Please use {help rdbwselect:rdbwselect} instead.{p_end}


{marker syntax}{...} 
{title:Syntax}

{p 4 8}{cmd:rdbwselect_2014} {it:depvar} {it:indepvar} {ifin} 
[{cmd:,} 
{cmd:c(}{it:#}{cmd:)} 
{cmd:p(}{it:#}{cmd:)} 
{cmd:q(}{it:#}{cmd:)}
{cmd:deriv(}{it:#}{cmd:)}
{cmd:rho(}{it:#}{cmd:)}
{cmd:kernel(}{it:kernelfn}{cmd:)}
{cmd:bwselect(}{it:bwmethod}{cmd:)}
{cmd:scaleregul(}{it:#}{cmd:)}
{cmd:delta(}{it:#}{cmd:)}
{cmd:cvgrid_min(}{it:#}{cmd:)}
{cmd:cvgrid_max(}{it:#}{cmd:)}
{cmd:cvgrid_length(}{it:#}{cmd:)}
{cmd:cvplot}
{cmd:vce(}{it:vcemethod}{cmd:)}
{cmd:matches(}{it:#}{cmd:)}
{cmd:all}
]{p_end}

{synoptset 28 tabbed}{...}

{marker description}{...}
{title:Description}

{p 4 8}{cmd:rdbwselect_2014} is a deprecated command implementing three bandwidth selectors for local polynomial Regression Discontinuity (RD) point estimators and inference procedures, as described in
{browse "https://rdpackages.github.io/references/Calonico-Cattaneo-Titiunik_2014_Stata.pdf":Calonico, Cattaneo and Titiunik (2014a)}.
This command is no longer supported or updated, and it is made available only for backward compatibility purposes.{p_end}
{p 8 8}This command uses compiled MATA functions given in
{it:rdbwselect_2014_functions.do}.{p_end}

{p 4 8}The latest version of the {cmd:rdrobust} package includes the following commands:{p_end}
{p 8 8}{help rdrobust:rdrobust} for point estimation and inference procedures.{p_end}
{p 8 8}{help rdbwselect:rdbwselect} for data-driven bandwidth selection.{p_end}
{p 8 8}{help rdplot:rdplot} for data-driven RD plots.{p_end}

{p 4 8}For more details, and related Stata and R packages useful for analysis of RD designs, visit:
{browse "https://rdpackages.github.io/"}{p_end}


{marker options}{...}
{title:Options}

{p 4 8}{cmd:c(}{it:#}{cmd:)} specifies the RD cutoff in {it:indepvar}.
Default is {cmd:c(0)}.

{p 4 8}{cmd:p(}{it:#}{cmd:)} specifies the order of the local-polynomial used to construct the point estimator.
Default is {cmd:p(1)} (local linear regression).

{p 4 8}{cmd:q(}{it:#}{cmd:)} specifies the order of the local-polynomial used to construct the bias-correction.
Default is {cmd:q(2)} (local quadratic regression).

{p 4 8}{cmd:deriv(}{it:#}{cmd:)} specifies the order of the derivative of the regression functions to be estimated.
Default is {cmd:deriv(0)} (Sharp RD, or Fuzzy RD if {cmd:fuzzy(.)} is also specified). Setting {cmd:deriv(1)} results in estimation of a Kink RD design (up to scale), or Fuzzy Kink RD if {cmd:fuzzy(.)} is also specified.

{p 4 8}{cmd:rho(}{it:#}{cmd:)} if specified, sets the pilot bandwidth {it:b} equal to {it:h}/{it:rho}, where {it:h} is computed using the method and options chosen below.

{p 4 8}{cmd:kernel(}{it:kernelfn}{cmd:)} specifies the kernel function used to construct the local-polynomial estimator(s). Options are: {opt tri:angular}, {opt epa:nechnikov}, and {opt uni:form}.
Default is {opt triangular}.

{p 4 8}{cmd:bwselect(}{it:bwmethod}{cmd:)} specifies the bandwidth selection procedure to be used. By default it computes both {it:h} and {it:b}, unless {it:rho} is specified, in which case it only computes {it:h} and sets {it:b}={it:h}/{it:rho}.
Options are:{p_end}
{p 8 12}{opt CCT} for bandwidth selector proposed by {browse "https://rdpackages.github.io/references/Calonico-Cattaneo-Titiunik_2014_ECMA.pdf":Calonico, Cattaneo and Titiunik (2014b)}. This is the default option.{p_end}
{p 8 12}{opt IK} for bandwidth selector proposed by Imbens and Kalyanaraman (2012) (only available for Sharp RD design).{p_end}
{p 8 12}{opt CV} for cross-validation method proposed by Ludwig and Miller (2007) (only available for Sharp RD design).{p_end}

{p 4 8}{cmd:scaleregul(}{it:#}{cmd:)} specifies scaling factor for the regularization terms of {opt CCT} and {opt IK} bandwidth selectors. Setting {cmd:scaleregul(0)} removes the regularization term from the bandwidth selectors.
Default is {cmd:scaleregul(1)}.

{p 4 8}{cmd:delta(}{it:#}{cmd:)} specifies the quantile that defines the sample used in the cross-validation procedure. This option is used only if {cmd:bwselect(}{opt CV}{cmd:)} is specified.
Default is {cmd:delta(0.5)}, that is, the median of the control and treated subsamples.

{p 4 8}{cmd:cvgrid_min(}{it:#}{cmd:)} specifies the minimum value of the bandwidth grid used in the cross-validation procedure. This option is used only if {cmd:bwselect(}{opt CV}{cmd:)} is specified.

{p 4 8}{cmd:cvgrid_max(}{it:#}{cmd:)} specifies the maximum value of the bandwidth grid used in the cross-validation procedure. This option is used only if {cmd:bwselect(}{opt CV}{cmd:)} is specified.

{p 4 8}{cmd:cvgrid_length(}{it:#}{cmd:)} specifies the bin length of the (evenly-spaced) bandwidth grid used in the cross-validation procedure. This option is used only if {cmd:bwselect(}{opt CV}{cmd:)} is specified.

{p 4 8}{cmd:cvplot} if specified, {cmd:rdbwselect} also reports a graph of the CV objective function. This option is used only if {cmd:bwselect(}{opt CV}{cmd:)} is specified.

{p 4 8}{cmd:vce(}{it:vcemethod}{cmd:)} specifies the procedure used to compute the variance-covariance matrix estimator. This option is used only if {opt CCT} or {opt IK} bandwidth procedures are used.
Options are:{p_end}
{p 8 12}{opt nn} for nearest-neighbor matches residuals using {cmd:matches(}{it:#}{cmd:)} matches. This is the default option (with {cmd:matches(3)}, see below).{p_end}
{p 8 12}{opt resid} for estimated plug-in residuals using {it:h} bandwidth.{p_end}

{p 4 8}{cmd:matches(}{it:#}{cmd:)} specifies the number of matches in the nearest-neighbor based variance-covariance matrix estimator. This option is used only when nearest-neighbor matches residuals are employed.
Default is {cmd:matches(3)}.

{p 4 8}{cmd:all} if specified, {cmd:rdbwselect} reports all three available procedures: {opt CCT}, {opt IK}, and {opt CV}{p_end}

	
    {hline}

	
{title:References}

{p 4 8}Calonico, S., M. D. Cattaneo, and R. Titiunik. 2014a.
{browse "https://rdpackages.github.io/references/Calonico-Cattaneo-Titiunik_2014_Stata.pdf":Robust Data-Driven Inference in the Regression-Discontinuity Design}.
{it:Stata Journal} 14(4): 909-946.{p_end}

{p 4 8}Calonico, S., M. D. Cattaneo, and R. Titiunik. 2014b.
{browse "https://rdpackages.github.io/references/Calonico-Cattaneo-Titiunik_2014_ECMA.pdf":Robust Nonparametric Confidence Intervals for Regression-Discontinuity Designs}.
{it:Econometrica} 82(6): 2295-2326.{p_end}

{title:Authors}

{p 4 8}Sebastian Calonico, University of California, Davis, CA.
{browse "mailto:scalonico@ucdavis.edu":scalonico@ucdavis.edu}.{p_end}

{p 4 8}Matias D. Cattaneo, Princeton University, Princeton, NJ.
{browse "mailto:cattaneo@princeton.edu":cattaneo@princeton.edu}.{p_end}

{p 4 8}Max H. Farrell, University of California, Santa Barbara, CA.
{browse "mailto:maxhfarrell@ucsb.edu":maxhfarrell@ucsb.edu}.{p_end}

{p 4 8}Rocio Titiunik, Princeton University, Princeton, NJ.
{browse "mailto:titiunik@princeton.edu":titiunik@princeton.edu}.{p_end}


