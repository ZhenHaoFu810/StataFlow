###########################################################################
## RDROBUST Python Package
## Script for Empirical Illustration
## Authors: Sebastian Calonico, Matias D. Cattaneo,
##          Max H. Farrell, Ricardo Masini and Rocio Titiunik 
###########################################################################

### Load RDROBUST package
from rdrobust import rdrobust,rdbwselect,rdplot
import pandas as pd

### Load data base
rdrobust_senate = pd.read_csv("rdrobust_senate.csv")

# Define the variblrs
margin = rdrobust_senate.margin
vote = rdrobust_senate.vote

### rdplot with 95% confidence intervals
rdplot(y=vote, x=margin, binselect="es", ci=95, 
         title="RD Plot: U.S. Senate Election Data", 
         y_label="Vote Share in Election at time t+2",
         x_label="Vote Share in Election at time t")

### rdplot with MSE-optimal choice
rdplot(y=vote, x=margin, binselect="es", 
       title="RD Plot: U.S. Senate Election Data", 
       y_label="Vote Share in Election at time t+2",
       x_label="Vote Share in Election at time t")

### rdplot with QS partitioning and mimicking variance choice
rdplot(y=vote, x=margin, binselect="qsmv", 
       title="RD Plot: U.S. Senate Election Data", 
       y_label="Vote Share in Election at time t+2",
       x_label="Vote Share in Election at time t")

### rdrobust 
print(rdrobust(y=vote, x=margin))

### rdrobust with all estimates
print(rdrobust(y=vote, x=margin, all=True))

## rdrobust backward compatibility
print(rdrobust(y=vote, x=margin, h=16.79369, b=27.43745))

## rdplot to show rdrobust estimate
est = rdrobust(y=vote, x=margin)
h_l, h_r = est.bws.loc['h', :].values
subset = ((-h_l<= margin) & (margin <= h_r)).values

rdplot(y=vote, x=margin, subset=subset,
       binselect="esmv", kernel="triangular", h=[h_l,h_r], p=1,
       title="RD Plot: U.S. Senate Election Data", 
       y_label="Vote Share in Election at time t+2",
       x_label="Vote Share in Election at time t")

## rdrobust with covariates within the same window (i.e., using same bandwidths)
est1 = rdrobust(y=vote, x=margin)
len1 = est1.ci.iloc[2,1] - est1.ci.iloc[2,0]
covs = rdrobust_senate[['class','termshouse','termssenate']]
b_l, b_r = est.bws.loc['b', :].values
est2 = rdrobust(y=vote, x=margin, covs=covs, 
                 h = [h_l,h_r], 
                 b = [b_l,b_r])
len2 = est2.ci.iloc[2,1] - est2.ci.iloc[2,0]
print("CI length change: " + str(round((len2/len1-1)*100,2)) + "%")

## rdrobust with covariates with data-driven optimal bandwidths
est1 = rdrobust(y=vote, x=margin)
len1 = est1.ci.iloc[2,1] - est1.ci.iloc[2,0]
est2 = rdrobust(y=vote, x=margin, covs=covs)
len2 = est2.ci.iloc[2,1] - est2.ci.iloc[2,0]
print("CI length change: " + str(round((len2/len1-1)*100,2)) + "%")

## rdrobust with useless covariate
est1 = rdrobust(y=vote, x=margin)
len1 = est1.ci.iloc[2,1] - est1.ci.iloc[2,0]
covs = rdrobust_senate['population']
est2 = rdrobust(y=vote, x=margin, covs=covs)
len2 = est2.ci.iloc[2,1] - est2.ci.iloc[2,0]
print("CI length change: " +  str(round((len2/len1-1)*100,2))+ "%")

## rdrobust check covariate "balanced"
covs = rdrobust_senate[['class','termshouse','termssenate','population']]
balance = pd.DataFrame(columns = ["RD Effect", "Robust p-val"],
                       index = pd.Index(["class","termshouse", "termssenate", "population"]))
for z in covs.columns:
    est = rdrobust(y=covs[z], x=margin)
    balance.loc[z,"RD Effect"] = est.Estimate["tau.us"].values[0]
    balance.loc[z,"Robust p-val"] = est.pv.iloc[2].values[0]
    
print(balance)

## rdrobust with clustering
state =rdrobust_senate.state.values
print(rdrobust(y=vote, x=margin, vce="nn", cluster=state))

## rdrobust with clustering and covariates, and different bandwidth
covs = rdrobust_senate[['class','termshouse','termssenate']]
print(rdrobust(y=vote, x=margin, vce="nn", bwselect="msetwo", covs=covs, cluster=state))

## rdbwselect with all estimates
print(rdbwselect(y=vote, x=margin, all=True))

## Other examples
print(rdrobust(y=vote, x=margin, kernel="uniform", vce="hc1", cluster=state))
print(rdrobust(y=vote, x=margin, bwselect="certwo", vce="hc3"))
print(rdrobust(y=vote, x=margin, h=(12,15), b=(18,20)))
print(rdrobust(y=vote, x=margin, covs=rdrobust_senate['class'], bwselect="cerrd", scaleregul=0, rho=1))
print(rdbwselect(y=vote, x=margin, kernel="uniform", vce="hc1", cluster=state, all=True))
print(rdbwselect(y=vote, x=margin, covs=rdrobust_senate['class'], bwselect="msetwo", vce="hc2", all=True))






