\name{rdplot}
\alias{rdplot}
\alias{print.rdplot}
\alias{summary.rdplot}
\title{Data-Driven Regression Discontinuity Plots}
\description{

\code{\link{rdplot}}  implements several data-driven Regression Discontinuity (RD) plots, using either evenly-spaced or quantile-spaced partitioning. Two type of RD plots are constructed: (i) RD plots with binned sample means tracing out the underlying regression function, and (ii) RD plots with binned sample means mimicking the underlying variability of the data. For technical and methodological details see Calonico, Cattaneo and Titiunik (2015a).

Companion commands are: \code{\link{rdrobust}} for point estimation and inference procedures, and \code{\link{rdbwselect}} for data-driven bandwidth selection.

A detailed introduction to this command is given in Calonico, Cattaneo and Titiunik (2015b) and Calonico, Cattaneo, Farrell and Titiunik (2017). A companion \code{Stata} package is described in Calonico, Cattaneo and Titiunik (2014).

For more details, and related Stata and R packages useful for analysis of RD designs, visit \url{https://rdpackages.github.io/}
}
\usage{
rdplot(y, x, c = 0, p = 4, nbins = NULL, binselect = "esmv",  
          scale = NULL, kernel = "uni", weights = NULL, h = NULL, 
          covs = NULL, covs_eval = "mean", covs_drop = TRUE, ginv.tol = 1e-20,
          support = NULL, subset = NULL, masspoints = "adjust",
          hide = FALSE, ci = NULL, shade = FALSE, title = NULL, 
          x.label = NULL, y.label = NULL, x.lim = NULL, y.lim = NULL, 
          col.dots = NULL, col.lines = NULL)
}
\arguments{
  \item{y}{is the dependent variable.}
  \item{x}{is the running variable (a.k.a. score or forcing variable).}
  \item{c}{specifies the RD cutoff in \code{x}; default is \code{c = 0}.}
  \item{p}{specifies the order of the global-polynomial used to approximate the population conditional mean functions for control and treated units; default is \code{p = 4}.} 
  \item{nbins}{specifies the number of bins used to the left of the cutoff, denoted \eqn{J_-}, and to the right of the cutoff, denoted \eqn{J_+}, respectively. If not specified, \eqn{J_+} and \eqn{J_-} are estimated using the method and options chosen below.}
  \item{binselect}{specifies the procedure to select the number of bins. This option is available only if \eqn{J_-} and \eqn{J_+} are not set manually. Options are:  

        \code{es}: IMSE-optimal evenly-spaced method using spacings estimators.
        
        \code{espr}: IMSE-optimal evenly-spaced method using polynomial regression.
        
        \code{esmv}: mimicking variance evenly-spaced method using spacings estimators. This is the default option.
        
        \code{esmvpr}: mimicking variance evenly-spaced method using polynomial regression.
        
        \code{qs}: IMSE-optimal quantile-spaced method using spacings estimators.
        
        \code{qspr}: IMSE-optimal quantile-spaced method using polynomial regression.
        
        \code{qsmv}: mimicking variance quantile-spaced method using spacings estimators.
        
        \code{qsmvpr}: mimicking variance quantile-spaced method using polynomial regression.
     }
       \item{scale}{specifies a multiplicative factor to be used with the optimal numbers of bins selected. Specifically, the number of bins used for the treatment and control groups will be \code{scale}\eqn{\times \hat{J}_+} and \code{scale}\eqn{\times \hat{J}_-}, where \eqn{\hat{J}_\cdot} denotes the estimated optimal numbers of bins originally computed for each group; default is \code{scale = 1}.}
  \item{kernel}{specifies the kernel function used to construct the local-polynomial estimator(s). Options are: \code{triangular}, \code{epanechnikov}, and \code{uniform}. Default is \code{kernel=uniform} (i.e., equal/no weighting to all observations on the support of the kernel).}
  \item{weights}{is the variable used for optional weighting of the estimation procedure. The unit-specific weights multiply the kernel function.}
  \item{h}{specifies the bandwidth used to construct the (global) polynomial fits given the kernel choice \code{kernel}.
If not specified, the bandwidths are chosen to span the full support of the data. If two bandwidths are specified, the first bandwidth is used for the data below the cutoff and the second bandwidth is used for the data above the cutoff.}
  \item{covs}{specifies additional covariates to be used in the polynomial regression.}
  \item{covs_eval}{sets the evaluation points for the additional covariates, when included in the estimation. Options are: \code{covs_eval = 0} and \code{covs_eval = "mean"} (default)}
  \item{covs_drop}{if TRUE, it checks for collinear additional covariates and drops them. Default is TRUE.}
    \item{ginv.tol}{tolerance used to invert matrices involving covariates when \code{covs_drop=TRUE}.}
  \item{support}{specifies an optional extended support of the running variable to be used in the construction of the bins;  default is the sample range.}
  \item{subset}{an optional vector specifying a subset of observations to be used.}
    \item{masspoints}{checks and controls for repeated observations in the running variable. Options are:
  
    (i)  \code{off}: ignores the presence of mass points; 
    
    (ii) \code{check}: looks for and reports the number of unique observations at each side of the cutoff. 
    
    (iii) \code{adjust}: sets \code{binselect()} as polynomial regression when mass points are present. 
    
    Default option is \code{masspoints=adjust}.}

  \item{hide}{logical. If \code{TRUE}, it omits the RD plot; default is \code{hide = FALSE}.}
  \item{ci}{optional graphical option to display confidence intervals of selected level for each bin.}
  \item{shade}{optional graphical option to replace confidence intervals with shaded areas.}
  \item{title}{optional title for the RD plot.}
  \item{x.label}{optional label for the x-axis of the RD plot.}
  \item{y.label}{optional label for the y-axis of the RD plot.}
  \item{x.lim}{optional setting for the range of the x-axis in the RD plot.}
  \item{y.lim}{optional setting for the range of the y-axis in the RD plot.}
  \item{col.dots}{optional setting for the color of the dots in the RD plot.}
  \item{col.lines}{optional setting for the color of the lines in the RD plot.}
}
\value{
  \item{binselect}{method used to compute the optimal number of bins.}
  \item{N}{sample sizes used to the left and right of the cutoff.}
  \item{Nh}{effective sample sizes used to the left and right of the cutoff.}
  \item{c}{cutoff value.}
  \item{p}{order of the global polynomial used.}
  \item{h}{bandwidth used to the left and right of the cutoff.}
  \item{kernel}{kernel used.}
  \item{J}{selected number of bins to the left and right of the cutoff.}
  \item{J_IMSE}{IMSE optimal number of bins to the left and right of the cutoff.}
  \item{J_MV}{Mimicking variance number of bins to the left and right of the cutoff.}
  \item{coef}{matrix containing the coefficients of the \eqn{p^{th}} order global polynomial estimated both sides of the cutoff.}
  \item{coef_covs}{coefficients of the additional covariates, only returned when \code{covs()} are used.}
  \item{scale}{selected scale value.}
  \item{rscale}{implicit scale value.}
  \item{bin_avg}{average bin length.}
  \item{bin_med}{median bin length.}
  \item{vars_bins}{data frame containing the variables used to construct the bins: bin id, cutoff values, mean of x and y within each bin, cutoff points and confidence interval bounds.}
  \item{vars_poly}{data frame containing the variables used to construct the global polynomial plot.}
  \item{rdplot}{a standard \code{ggplot} object that can be used for further customization.}
}
\references{
Calonico, S., M. D. Cattaneo, M. H. Farrell, and R. Titiunik. 2017. \href{https://rdpackages.github.io/references/Calonico-Cattaneo-Farrell-Titiunik_2017_Stata.pdf}{rdrobust: Software for Regression Discontinuity Designs.} \emph{Stata Journal} 17(2): 372-404. 

Calonico, S., M. D. Cattaneo, and R. Titiunik. 2014. \href{https://rdpackages.github.io/references/Calonico-Cattaneo-Titiunik_2014_Stata.pdf}{Robust Data-Driven Inference in the Regression-Discontinuity Design.} \emph{Stata Journal} 14(4): 909-946.

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
rdplot(y,x)
}
\keyword{ regression discontinuity }
\keyword{ RD plots }
\keyword{ binning }
\keyword{ partitioning}
\keyword{ tuning parameter selection}
\seealso{
  \code{\link{rdbwselect}}, \code{\link{rdrobust}}
}