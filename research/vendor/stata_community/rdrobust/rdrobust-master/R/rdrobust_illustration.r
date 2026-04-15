###########################################################################
## RDROBUST R Package
## Do-file for Empirical Illustration
## Authors: Sebastian Calonico, Matias D. Cattaneo, Max H. Farrell and Rocio Titiunik 
###########################################################################
### Clear R environment
rm(list=ls(all=TRUE))

### Install R library
### NOTE: depending on your system, you may need to do it as root
#install.packages('rdrobust')

### Load RDROBUST package
library(rdrobust)

### Load data base
rdrobust_senate <- read.csv("rdrobust_senate.csv")
attach(rdrobust_senate)

### Summary stats
summary(rdrobust_senate)

### rdplot with 95% confidence intervals
rdplot(y=vote, x=margin, binselect="es", ci=95, 
         title="RD Plot: U.S. Senate Election Data", 
         y.label="Vote Share in Election at time t+2",
         x.label="Vote Share in Election at time t")

### rdplot with MSE-optimal choice
rdplot(y=vote, x=margin, binselect="es", 
       title="RD Plot: U.S. Senate Election Data", 
       y.label="Vote Share in Election at time t+2",
       x.label="Vote Share in Election at time t")

### rdplot with QS partitioning and mimicking variance choice
rdplot(y=vote, x=margin, binselect="qsmv", 
       title="RD Plot: U.S. Senate Election Data", 
       y.label="Vote Share in Election at time t+2",
       x.label="Vote Share in Election at time t")

### rdrobust 
summary(rdrobust(y=vote, x=margin))

### rdrobust with all estimates
summary(rdrobust(y=vote, x=margin, all=TRUE))

## rdrobust backward compatibility
summary(rdrobust(y=vote, x=margin, h=16.79369, b=27.43745))

## rdplot to show rdrobust estimate
est <- rdrobust(y=vote, x=margin)
rdplot(y=vote, x=margin, subset=-est$bws[1,1]<= margin & margin <= est$bws[1,2],
       binselect="esmv", kernel="triangular", h=c(est$bws[1,1], est$bws[1,2]), p=1,
       title="RD Plot: U.S. Senate Election Data", 
       y.label="Vote Share in Election at time t+2",
       x.label="Vote Share in Election at time t")


## rdrobust with covariates within the same window (i.e., using same bandwidths)
est1 <- rdrobust(y=vote, x=margin)
len1 <- est1$ci[3,2] - est1$ci[3,1]
est2 <- rdrobust(y=vote, x=margin, covs=cbind(class,termshouse,termssenate), 
                 h = c(est$bws[1,1], est$bws[1,2]), 
                 b = c(est$bws[2,1], est$bws[2,2]))
len2 <- est2$ci[3,2] - est2$ci[3,1]
paste("CI length change: ", round((len2/len1-1)*100,2), "%")
                                   

## rdrobust with covariates with data-driven optimal bandwidths
est1 <- rdrobust(y=vote, x=margin)
len1 <- est1$ci[3,2] - est1$ci[3,1]
est2 <- rdrobust(y=vote, x=margin, covs=cbind(class,termshouse,termssenate))
len2 <- est2$ci[3,2] - est2$ci[3,1]
paste("CI length change: ", round((len2/len1-1)*100,2), "%")

## rdrobust with useless covariate
est1 <- rdrobust(y=vote, x=margin)
len1 <- est1$ci[3,2] - est1$ci[3,1]
est2 <- rdrobust(y=vote, x=margin, covs=cbind(population))
len2 <- est2$ci[3,2] - est2$ci[3,1]
paste("CI length change: ", round((len2/len1-1)*100,2), "%")

## rdrobust check covariate "balanced"
covs <- cbind(class, termshouse, termssenate, population)
balance <- matrix(NA,4,2)
for (z in 1:ncol(covs)) {
  est <- rdrobust(y=covs[,z], x=margin)
  balance[z,1] = est$Estimate[,"tau.us"]
  balance[z,2] = est$pv[3]
}
rownames(balance) = c("class", "termshouse", "termssenate", "population")
colnames(balance) = c("RD Effect", "Robust p-val")
print(balance)

## rdrobust with clustering
summary(rdrobust(y=vote, x=margin, vce="nn", cluster=state))

## rdrobust with clustering and covariates, and different bandwidth
summary(rdrobust(y=vote, x=margin, vce="nn", bwselect="msetwo", covs=cbind(class,termshouse,termssenate), cluster=state))

## rdbwselect with all estimates
summary(rdbwselect(y=vote, x=margin, all=TRUE))

## Other examples
summary(rdrobust(y=vote, x=margin, kernel="uniform", vce="hc1", cluster=state))
summary(rdrobust(y=vote, x=margin, bwselect="certwo", vce="hc3"))
summary(rdrobust(y=vote, x=margin, h=c(12,15), b=c(18,20)))
summary(rdrobust(y=vote, x=margin, covs=cbind(class), bwselect="cerrd", scaleregul=0, rho=1))
summary(rdbwselect(y=vote, x=margin, kernel="uniform", vce="hc1", cluster=state, all=TRUE))
summary(rdbwselect(y=vote, x=margin, covs=cbind(class), bwselect="msetwo", vce="hc2", all=TRUE))






