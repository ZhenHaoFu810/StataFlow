\name{rdbwselect_2014}
\alias{rdbwselect_2014}
\alias{print.rdbwselect_2014}
\alias{summary.rdbwselect_2014}
\title{Deprecated Bandwidth Selection Procedures for Local-Polynomial Regression-Discontinuity Estimators.}
\description{\code{\link{rdbwselect_2014}} is a deprecated command implementing three bandwidth selectors for local polynomial Regression Discontinuity (RD) point estimators and inference procedures, as described in Calonico, Cattaneo and Titiunik (2014).
 
    This command is no longer supported or updated, and it is made available only for backward compatibility purposes. Please use \code{\link{rdbwselect}} instead.

    The latest version of the rdrobust package includes the following commands:
        \code{\link{rdrobust}} for point estimation and inference procedures.
        \code{\link{rdbwselect}} for data-driven bandwidth selection.
        \code{\link{rdplot}} for data-driven RD plots.

    For more details, and related Stata and R packages useful for analysis of RD designs, visit \url{https://rdpackages.github.io/}}
\usage{rdbwselect_2014(y, x, subset = NULL, c = 0, p = 1, q = 2, deriv = 0,
              rho = NULL, kernel = "tri", bwselect = "CCT", scaleregul = 1,
              delta = 0.5, cvgrid_min = NULL, cvgrid_max = NULL, 
              cvgrid_length = NULL, cvplot = FALSE, vce = "nn", matches = 3, 
              all = FALSE, precalc = TRUE )}
\arguments{
  \item{y}{is the dependent variable.}
  \item{x}{is the running variable (a.k.a. score or forcing variable).}  
  \item{subset}{an optional vector specifying a subset of observations to be used.}
  \item{c}{specifies the RD cutoff in \code{x}; default is \code{c = 0}.}
    \item{p}{specifies the order of the local-polynomial used to construct the point-estimator; default is \code{p = 1} (local linear regression).}
  \item{q}{specifies the order of the local-polynomial used to construct the bias-correction; default is \code{q = 2} (local quadratic regression).}
  \item{deriv}{specifies the order of the derivative of the regression function to be estimated; default is \code{deriv = 0} (Sharp RD, or Fuzzy RD if \code{fuzzy} is also specified). Setting it equal to 1 results in estimation of a Kink RD design (or Fuzzy Kink RD if \code{fuzzy} is also specified).}  
    \item{rho}{if specified, sets the pilot bandwidth \code{b} equal to \code{h/rho}, where \code{h} is computed using the method and options chosen below.}
  \item{kernel}{is the kernel function used to construct the local-polynomial estimator(s). Options are \code{triangular} (default option), \code{epanechnikov} and \code{uniform}.}
  \item{bwselect}{selects the bandwidth selection procedure to be used. By default it computes both \code{h} and \code{b}, unless \code{rho} is specified, in which case it only computes \code{h} and sets \code{b} = \code{h/rho}. Options are:
  
  \code{CCT} for bandwidth selector proposed by Calonico, Cattaneo and Titiunik (2014)  (default option).
  
  \code{IK} for bandwidth selector proposed by Imbens and Kalyanaraman (2012) (only available for Sharp RD design).
  
  \code{CV} for cross-validation method proposded by Ludwig and Miller (2007) (only available for Sharp RD design).}
  \item{scaleregul}{specifies scaling factor for the regularization terms of \code{CCT} and \code{IK} bandwidth selectors. Setting \code{scaleregul = 0} removes the regularization term from the bandwidth selectors; default is \code{scaleregul = 1}.}
    \item{delta}{sets the quantile that defines the sample used in the cross-validation procedure. This option is used only if \code{bwselect(CV)} is specified; default is \code{delta = 0.5}, that is, the median of the control and treated samples.}
  \item{cvgrid_min}{sets the minimum value of the bandwidth grid used in the cross-validation procedure. This option is used only if \code{bwselect = "CV"} is specified.}
  \item{cvgrid_max}{sets the maximum value of the bandwidth grid used in the cross-validation procedure. This option is used only if \code{bwselect = "CV"} is specified.}
  \item{cvgrid_length}{sets the bin length of the (evenly-spaced) bandwidth grid used in the cross-validation procedure. This option is used only if \code{bwselect = "CV"} is specified.}
  \item{cvplot}{generates a graph of the CV objective function. This option is used only if \code{bwselect = "CV"} is specified.}
  \item{vce}{specifies the procedure used to compute the variance-covariance matrix estimator. This option is used only if \code{CCT} or \code{IK} bankdwith procedures are employed. Options are:

  \code{nn} for nearest-neighbor matches residuals using \code{matches} number of matches. This is the default option (with \code{matches = 3}, see below).

  \code{resid} for estimated plug-in residuals using \code{h} bandwidth.}
  \item{matches}{specifies the number of matches in the nearest-neighbor based variance-covariance matrix estimator. This options is used only when nearest-neighbor matches residuals are employed; default is \code{matches = 3}.}
  
\item{all}{if specified, \code{\link{rdbwselect_2014}} reports  three different procedures: 

  \code{CCT} for bandwidth selector proposed by Calonico, Cattaneo and Titiunik (2014).
  
  \code{IK} for bandwidth selector proposed by Imbens and Kalyanaraman (2012).
  
  \code{CV} for cross-validation method proposed by Ludwig and Miller (2007).}
  
  \item{precalc}{internal option.}
}
\value{
  \item{bws}{matrix containing the estimated bandwidths for each selected procedure.}
  \item{bwselect}{bandwidth selection procedure employed.}
  \item{kernel}{kernel function used to construct the local-polynomial estimator(s).}
  \item{p}{order of the local-polynomial used to construct the point-estimator.}
  \item{q}{order of the local-polynomial used to construct the bias-correction estimator.}
}
\references{
        Calonico, S., Cattaneo, M. D., and R. Titiunik. 2014. \href{https://rdpackages.github.io/references/Calonico-Cattaneo-Titiunik_2014_Stata.pdf}{Robust Nonparametric Confidence Intervals for Regression-Discontinuity Designs.} \emph{Econometrica} 82(6): 2295-2326.   .
}
\author{
Sebastian Calonico, University of California, Davis, CA.  \email{scalonico@ucdavis.edu}.

Matias D. Cattaneo, Princeton University, Princeton, NJ.  \email{cattaneo@princeton.edu}.

Max H. Farrell, University of California, Santa Barbara, CA. \email{maxhfarrell@ucsb.edu}.

Rocio Titiunik, Princeton University, Princeton, NJ.  \email{titiunik@princeton.edu}.
}
\examples{
x<-runif(1000,-1,1)
y<-5+3*x+2*(x>=0)+rnorm(1000)
rdbwselect_2014(y,x)
}
\seealso{
  \code{\link{rdrobust}}, \code{\link{rdplot}}
}