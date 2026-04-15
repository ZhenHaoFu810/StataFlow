# RDROBUST

The `rdrobust` package provides Python, R and Stata implementations of statistical inference and graphical procedures for Regression Discontinuity designs employing local polynomial and partitioning methods. It provides point estimators, confidence intervals estimators, bandwidth selectors, automatic RD plots, and many other features.

This work was supported in part by the National Science Foundation through grants [SES-1357561](https://www.nsf.gov/awardsearch/showAward?AWD_ID=1357561), [SES-1459931](https://www.nsf.gov/awardsearch/showAward?AWD_ID=1459931), [SES-1947805](https://www.nsf.gov/awardsearch/showAward?AWD_ID=1947805), and [SES-2019432](https://www.nsf.gov/awardsearch/showAward?AWD_ID=2019432).

## Website

https://rdpackages.github.io/rdrobust

## Queries and Requests

Please email: [rdpackages@googlegroups.com](mailto:rdpackages@googlegroups.com)

## Major Upgrades

This package was first released in Spring 2014, and had two major upgrades in Fall 2016 and in Winter 2020.

- _Fall 2016 new features include_: (i) major speed improvements; (ii) covariate-adjusted bandwidth selection, point estimation, and robust inference; (iii) cluster-robust bandwidth selection, point estimation, and robust inference; (iv) weighted global polynomial fits and pointwise confidence bands for RD plots; and (v) several new bandwidths selectors (e.g., different bandwidths for control and treatment groups, coverage error optimal bandwidths, and optimal bandwidths for fuzzy designs).

- _Winter 2020 new features include_: (i) discrete running variable checks and adjustments; (ii) bandwidth selection adjustments for too few mass points in and/or overshooting of the support of the running variable; (iii) RD Plots with additional covariates plotted at their mean (previously the package set additional covariates at zero); (iv) automatic removal of co-linear additional covariates; (v) turn on/off standardization of variables (which may lead to small numerical/rounding discrepancies with prior versions); and (vi) rdplot output using ggplot2 in R.

## Python Implementation

To install/update in Python type:
```
pip install rdrobust
```

- Help: [PYPI repository](https://pypi.org/project/rdrobust/).

- Replication: [py-script](Python/rdrobust_illustration.py), [rdplot illustration](Python/rdplot_illustration.py), [senate data](Python/rdrobust_senate.csv).

## R Implementation

To install/update in R type:
```
install.packages('rdrobust')
```

- Help: [R Manual](https://cran.r-project.org/web/packages/rdrobust/rdrobust.pdf), [CRAN repository](https://cran.r-project.org/package=rdrobust).

- Replication: [R-script](R/rdrobust_illustration.r), [rdplot illustration](R/rdplot_illustration.R), [senate data](R/rdrobust_senate.csv).

## Stata Implementation

To install/update in Stata type:
```
net install rdrobust, from(https://raw.githubusercontent.com/rdpackages/rdrobust/master/stata) replace
```

- Help: [rdrobust](stata/rdrobust.pdf), [rdbwselect](stata/rdbwselect.pdf), [rdplot](stata/rdplot.pdf).

- Replication: [do-file](stata/rdrobust_illustration.do), [rdplot illustration](stata/rdplot_illustration.do), [senate data](stata/rdrobust_senate.dta).


## References

For overviews and introductions, see [rdpackages website](https://rdpackages.github.io).

### Software and Implementation

- Calonico, Cattaneo and Titiunik (2014): [Robust Data-Driven Inference in the Regression-Discontinuity Design](https://rdpackages.github.io/references/Calonico-Cattaneo-Titiunik_2014_Stata.pdf).<br>
_Stata Journal_ 14(4): 909-946.

- Calonico, Cattaneo and Titiunik (2015): [rdrobust: An R Package for Robust Nonparametric Inference in Regression-Discontinuity Designs](https://rdpackages.github.io/references/Calonico-Cattaneo-Titiunik_2015_R.pdf).<br>
_R Journal_ 7(1): 38-51.

- Calonico, Cattaneo, Farrell and Titiunik (2017): [rdrobust: Software for Regression Discontinuity Designs](https://rdpackages.github.io/references/Calonico-Cattaneo-Farrell-Titiunik_2017_Stata.pdf).<br>
_Stata Journal_ 17(2): 372-404.

### Technical and Methodological

- Calonico, Cattaneo and Titiunik (2014): [Robust Nonparametric Confidence Intervals for Regression-Discontinuity Designs](https://rdpackages.github.io/references/Calonico-Cattaneo-Titiunik_2014_ECMA.pdf).<br>
_Econometrica_ 82(6): 2295-2326.<br>
[Supplemental Appendix](https://rdpackages.github.io/references/Calonico-Cattaneo-Titiunik_2014_ECMA--Supplemental.pdf).

- Calonico, Cattaneo and Titiunik (2015): [Optimal Data-Driven Regression Discontinuity Plots](https://rdpackages.github.io/references/Calonico-Cattaneo-Titiunik_2015_JASA.pdf).<br>
_Journal of the American Statistical Association_ 110(512): 1753-1769.<br>
[Supplemental Appendix](https://rdpackages.github.io/references/Calonico-Cattaneo-Titiunik_2015_JASA--Supplement.pdf).

- Calonico, Cattaneo and Farrell (2018): [On the Effect of Bias Estimation on Coverage Accuracy in Nonparametric Inference](https://rdpackages.github.io/references/Calonico-Cattaneo-Farrell_2018_JASA.pdf).<br>
_Journal of the American Statistical Association_ 113(522): 767-779.<br>
[Supplemental Appendix](https://rdpackages.github.io/references/Calonico-Cattaneo-Farrell_2018_JASA--Supplement.pdf).

- Calonico, Cattaneo, Farrell and Titiunik (2019): [Regression Discontinuity Designs Using Covariates](https://rdpackages.github.io/references/Calonico-Cattaneo-Farrell-Titiunik_2019_RESTAT.pdf).<br>
_Review of Economics and Statistics_ 101(3): 442-451.<br>
[Supplemental Appendix](https://rdpackages.github.io/references/Calonico-Cattaneo-Farrell-Titiunik_2019_RESTAT--Supplement.pdf).

- Calonico, Cattaneo and Farrell (2020): [Optimal Bandwidth Choice for Robust Bias Corrected Inference in Regression Discontinuity Designs](https://rdpackages.github.io/references/Calonico-Cattaneo-Farrell_2020_ECTJ.pdf).<br>
_Econometrics Journal_ 23(2): 192-210.<br>
[Supplemental Appendix](https://rdpackages.github.io/references/Calonico-Cattaneo-Farrell_2020_ECTJ--Supplement.pdf).

- Calonico, Cattaneo and Farrell (2022): [Coverage Error Optimal Confidence Intervals for Local Polynomial Regression](https://rdpackages.github.io/references/Calonico-Cattaneo-Farrell_2022_Bernoulli.pdf).<br>
_Bernoulli_ 28(4): 2998-3022.<br>
[Supplemental Appendix](https://rdpackages.github.io/references/Calonico-Cattaneo-Farrell_2022_Bernoulli--Supplement.pdf).

<br><br>
