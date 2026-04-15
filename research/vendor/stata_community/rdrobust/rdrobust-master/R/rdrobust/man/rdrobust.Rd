\name{rdrobust}
\alias{rdrobust} 
\alias{print.rdrobust}
\alias{summary.rdrobust}
\title{Local-Polynomial RD Estimation with Robust Confidence Intervals}
\description{

\code{\link{rdrobust}} implements local polynomial Regression Discontinuity (RD) point estimators with robust bias-corrected confidence intervals and inference procedures developed in Calonico, Cattaneo and Titiunik (2014a), Calonico, Cattaneo and Farrell (2018), Calonico, Cattaneo, Farrell and Titiunik (2019), and Calonico, Cattaneo and Farrell (2020). It also computes alternative estimation and inference procedures available in the literature. 

Companion commands are: \code{\link{rdbwselect}} for data-driven bandwidth selection, and \code{\link{rdplot}} for data-driven RD plots (see Calonico, Cattaneo and Titiunik (2015a) for details).

A detailed introduction to this command is given in Calonico, Cattaneo and Titiunik (2015b), and Calonico, Cattaneo, Farrell and Titiunik (2017). A companion \code{Stata} package is described in Calonico, Cattaneo and Titiunik (2014b).

For more details, and related Stata and R packages useful for analysis of RD designs, visit \url{https://rdpackages.github.io/}

}
\usage{rdrobust(y, x, c = NULL,  fuzzy = NULL, 
          deriv = NULL, p = NULL, q = NULL, 
          h = NULL, b = NULL, rho = NULL, 
          covs = NULL,  covs_drop = TRUE, ginv.tol = 1e-20,
          kernel = "tri", weights = NULL, bwselect = "mserd", 
          vce = "nn", cluster = NULL, 
          nnmatch = 3, level = 95, scalepar = 1, scaleregul = 1, 
          sharpbw = FALSE, detail = NULL, all = NULL, subset = NULL,
          masspoints = "adjust", bwcheck = NULL,
          bwrestrict = TRUE, stdvars = FALSE)}
\arguments{
  \item{y}{is the dependent variable.}
  \item{x}{is the running variable (a.k.a. score or forcing variable).}
  \item{c}{specifies the RD cutoff in \code{x}; default is \code{c = 0}.}
  \item{fuzzy}{specifies the treatment status variable used to implement fuzzy RD estimation (or Fuzzy Kink RD if \code{deriv=1} is also specified). Default is Sharp RD design and hence this option is not used.} 
  \item{deriv}{specifies the order of the derivative of the regression functions to be estimated. Default is \code{deriv=0} (for Sharp RD, or for Fuzzy RD if \code{fuzzy} is also specified). Setting \code{deriv=1} results in estimation of a Kink RD design (up to scale), or Fuzzy Kink RD if \code{fuzzy} is also specified.}
  \item{p}{specifies the order of the local-polynomial used to construct the point-estimator; default is \code{p = 1} (local linear regression).}
  \item{q}{specifies the order of the local-polynomial used to construct the bias-correction; default is \code{q = 2} (local quadratic regression).}
  \item{h}{specifies the main bandwidth used to construct the RD point estimator. If not specified, bandwidth \code{h} is computed by the companion command \code{\link{rdbwselect}}. If two bandwidths are specified, the first bandwidth is used for the data below the cutoff and the second bandwidth is used for the data above the cutoff.}
  \item{b}{specifies the bias bandwidth used to construct the bias-correction estimator. If not specified, bandwidth \code{b} is computed by the companion command \code{\link{rdbwselect}}. If two bandwidths are specified, the first bandwidth is used for the data below the cutoff and the second bandwidth is used for the data above the cutoff.}
  \item{rho}{specifies the value of \code{rho}, so that the bias bandwidth \code{b} equals \code{h/rho}. Default is \code{rho = 1} if \code{h} is specified but \code{b} is not.}
  \item{covs}{additional covariates to be used for efficiency improvements.}
  \item{covs_drop}{if TRUE, it checks for collinear additional covariates and drops them. Default is TRUE.}
  \item{ginv.tol}{tolerance used to invert matrices involving covariates when \code{covs_drop=TRUE}.}
  \item{kernel}{is the kernel function used to construct the local-polynomial estimator(s). Options are \code{triangular} (default option), \code{epanechnikov} and \code{uniform}.}
  \item{weights}{is the variable used for optional weighting of the estimation procedure. The unit-specific weights multiply the kernel function.}

\item{bwselect}{specifies the bandwidth selection procedure to be used. By default it computes both \code{h} and \code{b}, unless \code{rho} is specified, in which case it only computes \code{h} and sets \code{b=h/rho}.}
Options are:

\code{mserd} one common MSE-optimal bandwidth selector for the RD treatment effect estimator.

\code{msetwo} two different MSE-optimal bandwidth selectors (below and above the cutoff) for the RD treatment effect estimator.

\code{msesum} one common MSE-optimal bandwidth selector for the sum of regression estimates (as opposed to difference thereof).

\code{msecomb1} for min(\code{mserd},\code{msesum}).

\code{msecomb2} for median(\code{msetwo},\code{mserd},\code{msesum}), for each side of the cutoff separately.

\code{cerrd} one common CER-optimal bandwidth selector for the RD treatment effect estimator.

\code{certwo} two different CER-optimal bandwidth selectors (below and above the cutoff) for the RD treatment effect estimator.

\code{cersum} one common CER-optimal bandwidth selector for the sum of regression estimates (as opposed to difference thereof).

\code{cercomb1} for min(\code{cerrd},\code{cersum}).

\code{cercomb2} for median(\code{certwo},\code{cerrd},\code{cersum}), for each side of the cutoff separately.

Note: MSE = Mean Square Error; CER = Coverage Error Rate.
Default is \code{bwselect=mserd}. For details on implementation see Calonico, Cattaneo and Titiunik (2014a), Calonico, Cattaneo and Farrell (2018), and Calonico, Cattaneo, Farrell and Titiunik (2019), and the companion software articles.

\item{vce}{specifies the procedure used to compute the variance-covariance matrix estimator.
Options are:

\code{nn} for heteroskedasticity-robust nearest neighbor variance estimator with \code{nnmatch} the (minimum) number of neighbors to be used.

\code{hc0} for heteroskedasticity-robust plug-in residuals variance estimator without weights.

\code{hc1} for heteroskedasticity-robust plug-in residuals variance estimator with \code{hc1} weights.

\code{hc2} for heteroskedasticity-robust plug-in residuals variance estimator with \code{hc2} weights.

\code{hc3} for heteroskedasticity-robust plug-in residuals variance estimator with \code{hc3} weights.

Default is \code{vce=nn}.}
  \item{cluster}{indicates the cluster ID variable used for cluster-robust variance estimation with degrees-of-freedom weights. By default it is combined with \code{vce=nn} for cluster-robust nearest neighbor variance estimation. Another option is plug-in residuals combined with \code{vce=hc0}.}
  \item{nnmatch}{to be combined with for \code{vce=nn} for heteroskedasticity-robust nearest neighbor variance estimator with \code{nnmatch} indicating the minimum number of neighbors to be used. Default is \code{nnmatch=3}}
  \item{level}{sets the confidence level for confidence intervals; default is \code{level = 95}.}
  \item{scalepar}{specifies scaling factor for RD parameter of interest. This option is useful when the population parameter of interest involves a known multiplicative factor (e.g., sharp kink RD).  Default is \code{scalepar = 1} (no scaling).}
  \item{scaleregul}{specifies scaling factor for the regularization term added to the denominator of the bandwidth selectors. Setting \code{scaleregul = 0} removes the regularization term from the bandwidth selectors; default is \code{scaleregul = 1}.}
  \item{sharpbw}{option to perform fuzzy RD estimation using a bandwidth selection procedure for the sharp RD model. This option is automatically selected if there is perfect compliance at either side of the cutoff.}
  \item{detail}{if specified, \code{\link{rdrobust}} reports the output from versions 2.2.0 and earlier.}
  \item{all}{if specified, \code{\link{rdrobust}} reports three different procedures:
  
  (i) conventional RD estimates with conventional standard errors.
  
  (ii) bias-corrected estimates with conventional standard errors.
  
  (iii) bias-corrected estimates with robust standard errors.}
  
  \item{subset}{an optional vector specifying a subset of observations to be used.}
  \item{masspoints}{checks and controls for repeated observations in the running variable. Options are:
  
    (i)  \code{off}: ignores the presence of mass points; 
    
    (ii) \code{check}: looks for and reports the number of unique observations at each side of the cutoff. 
    
    (iii) \code{adjust}: controls that the preliminary bandwidths used in the calculations contain a minimal number of unique observations. By default it uses 10 observations, but it can be manually adjusted with the option \code{bwcheck}). 
    
    Default option is \code{masspoints=adjust}.}
    \item{bwcheck}{if a positive integer is provided, the preliminary bandwidth used in the calculations is enlarged so that at least \code{bwcheck} unique observations are used.}
    
    \item{bwrestrict}{if \code{TRUE}, computed bandwidths are restricted to lie within the range of \code{x}; default is \code{bwrestrict = TRUE}.}
      
    \item{stdvars}{if \code{TRUE}, \code{x} and \code{y} are standardized before computing the bandwidths; default is \code{stdvars = FALSE}.}
      
}
\value{
  \item{N}{vector with the sample sizes used to the left and to the right of the cutoff.}
  \item{N_h}{vector with the effective sample sizes used to the left and to the right of the cutoff.}
  \item{c}{cutoff value.}
  \item{p}{order of the polynomial used for estimation of the regression function.}
  \item{q}{order of the polynomial used for estimation of the bias of the regression function.}
  \item{bws}{matrix containing the bandwidths used.}
  \item{tau_cl}{conventional local-polynomial estimate to the left and to the right of the cutoff.}
  \item{tau_bc}{bias-corrected local-polynomial estimate to the left and to the right of the cutoff.}
  \item{coef}{vector containing conventional and bias-corrected local-polynomial RD estimates.}
  \item{se}{vector containing conventional and robust standard errors of the local-polynomial RD estimates.}
  \item{bias}{estimated bias for the local-polynomial RD estimator below and above the cutoff.}
  \item{beta_Y_p_l}{conventional p-order local-polynomial estimates to the left of the cutoff for the outcome variable.}
  \item{beta_Y_p_r}{conventional p-order local-polynomial estimates to the right of the cutoff for the outcome variable.}
  \item{beta_T_p_l}{conventional p-order local-polynomial estimates to the left of the cutoff for the first stage (fuzzy RD).}
  \item{beta_T_p_r}{conventional p-order local-polynomial estimates to the right of the cutoff for the first stage (fuzzy RD).}
  \item{beta_covs}{coefficients of the additional covariates, only returned when \code{covs()} are used.}
  \item{V_cl_l}{conventional variance-covariance matrix estimated below the cutoff.}
  \item{V_cl_r}{conventional variance-covariance matrix estimated above the cutoff.}
  \item{V_rb_l}{robust variance-covariance matrix estimated below the cutoff.}
  \item{V_rb_r}{robust variance-covariance matrix estimated above the cutoff.}
  \item{pv}{vector containing the p-values associated with conventional, bias-corrected and robust local-polynomial RD estimates.}
  \item{ci}{matrix containing the confidence intervals associated with conventional, bias-corrected and robust local-polynomial RD estimates.}
}
\references{
Calonico, S., M. D. Cattaneo, and M. H. Farrell. 2018. \href{https://nppackages.github.io/references/Calonico-Cattaneo-Farrell_2018_JASA.pdf}{On the Effect of Bias Estimation on Coverage Accuracy in Nonparametric Inference.} \emph{Journal of the American Statistical Association}, 113(522): 767-779.

Calonico, S., M. D. Cattaneo, and M. H. Farrell. 2020. \href{https://rdpackages.github.io/references/Calonico-Cattaneo-Farrell_2020_ECTJ.pdf}{Optimal Bandwidth Choice for Robust Bias Corrected Inference in Regression Discontinuity Designs.} \emph{Econometrics Journal}, 23(2): 192-210.

Calonico, S., M. D. Cattaneo, M. H. Farrell, and R. Titiunik. 2017. \href{https://rdpackages.github.io/references/Calonico-Cattaneo-Farrell-Titiunik_2017_Stata.pdf}{rdrobust: Software for Regression Discontinuity Designs.} \emph{Stata Journal}, 17(2): 372-404.

Calonico, S., M. D. Cattaneo, M. H. Farrell, and R. Titiunik. 2019. \href{https://rdpackages.github.io/references/Calonico-Cattaneo-Farrell-Titiunik_2019_RESTAT.pdf}{Regression Discontinuity Designs using Covariates.} \emph{Review of Economics and Statistics}, 101(3): 442-451. 

Calonico, S., M. D. Cattaneo, and R. Titiunik. 2014a. \href{https://rdpackages.github.io/references/Calonico-Cattaneo-Titiunik_2014_ECMA.pdf}{Robust Nonparametric Confidence Intervals for Regression-Discontinuity Designs.} \emph{Econometrica} 82(6): 2295-2326.

Calonico, S., M. D. Cattaneo, and R. Titiunik. 2014b. \href{https://rdpackages.github.io/references/Calonico-Cattaneo-Titiunik_2014_Stata.pdf}{Robust Data-Driven Inference in the Regression-Discontinuity Design.} \emph{Stata Journal} 14(4): 909-946.

Calonico, S., M. D. Cattaneo, and R. Titiunik. 2015a. \href{https://rdpackages.github.io/references/Calonico-Cattaneo-Titiunik_2015_JASA.pdf}{Optimal Data-Driven Regression Discontinuity Plots.} \emph{Journal of the American Statistical Association} 110(512): 1753-1769.

Calonico, S., M. D. Cattaneo, and R. Titiunik. 2015b. \href{https://rdpackages.github.io/references/Calonico-Cattaneo-Titiunik_2015_R.pdf}{rdrobust: An R Package for Robust Nonparametric Inference in Regression-Discontinuity Designs.} \emph{R Journal} 7(1): 38-51.

Cattaneo, M. D., B. Frandsen, and R. Titiunik. 2015. \href{https://rdpackages.github.io/references/Cattaneo-Frandsen-Titiunik_2015_JCI.pdf}{Randomization Inference in the Regression Discontinuity Design: An Application to the Study of Party Advantages in the U.S. Senate.} \emph{Journal of Causal Inference} 3(1): 1-24.
}
\author{
Sebastian Calonico, University of California, Davis, CA.  \email{scalonico@ucdavis.edu}.

Matias D. Cattaneo, Princeton University, Princeton, NJ.  \email{cattaneo@princeton.edu}.

Max H. Farrell, University of California, Santa Barbara, CA. \email{maxhfarrell@ucsb.edu}.

Rocio Titiunik, Princeton University, Princeton, NJ.  \email{titiunik@princeton.edu}.
}
\examples{ 
x <- runif(1000,-1,1)
y <- 5 + 3*x + 2*(x>=0) + rnorm(1000)
rdrobust(y,x)
}
\keyword{ RDD }
\keyword{ Robust Estimation }
\seealso{
  \code{\link{rdbwselect}}, \code{\link{rdplot}}
}
