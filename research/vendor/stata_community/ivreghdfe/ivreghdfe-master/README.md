# IVREGHDFE: reghdfe + ivreg2 (adds instrumental variable and additional robust SE estimators to reghdfe)
![GitHub release (latest by date)](https://img.shields.io/github/v/release/sergiocorreia/ivreghdfe?label=last%20version)
![GitHub Release Date](https://img.shields.io/github/release-date/sergiocorreia/ivreghdfe)
![GitHub commits since latest release (by date)](https://img.shields.io/github/commits-since/sergiocorreia/ivreghdfe/latest)
![StataMin](https://img.shields.io/badge/stata-%3E%3D%2013.1-blue)
[![DOI](https://zenodo.org/badge/82003805.svg)](https://zenodo.org/badge/latestdoi/82003805)
- Jump to: [`usage`](#usage) [`benchmarks`](#benchmarks) [`install`](#installation)

This package integrates [`reghdfe`](https://github.com/sergiocorreia/reghdfe/) into [`ivreg2`](https://ideas.repec.org/c/boc/bocode/s425401.html), through an `absorb()` option. This allows IV/2SLS regressions with multiple levels of fixed effects.

## Recent updates

- **version 1.1.4 29Nov2025**:
	- Fix bug #61; where `resid(...)` returned incorrectly sorted residuals if these three conditions were met: i) `cluster(...)` was used, and ii) data was not already sorted by cluster, and iii) data was not `xtset` or `tsset`
- **version 1.1.2 29Sep2022**:
	- Fix bug #44; where cluster(...) worked but vce(cluster ...) was silently ignored
	- Fix bug #46; small correction to e(cmdline)
- **version 1.1.1 14dec2021**:
	- Add experimental support for `margins` postestimation command.
- **version 1.1 26feb2021**:
	- Update `ivreg2` dependency from _4.1.10 9Feb2016_ to  _4.1.11 22Nov2019_.
	- Update `reghdfe` dependency from _5.9.0 03jun2020_ to _6.0.2 25feb2021_
	- Before, reghdfe options had to be passed as suboptions of `absorb()`. Now they are passed directly as normal options
	- Note that some options are slightly different in reghdfe v6 (e.g. the exact technique used is set through the `technique()` option, following Stata convention).
	- Note that there might be a tiny difference in the SE estimates of ivreghdfe wrt those in reghdfe when both are used to run OLS instead of IV.
		- This happens if we have clustered standard errors, and the fixed effects are nested within the clusters.
		- Then, when computing the small sample adjustment `q`, reghdfe divides by (N-K-1) while ivreg2 (and thus ivreghdfe) divides by (N-K)
		- `reghdfe` does so to keep consistency with the small sample adjustment done by `xtreg`
		- For more details see comment in code ("minor adj. so we match xtreg when the absvar is nested within cluster")


## Comparison with other commands

As seen in the table below, `ivreghdfe` is recommended if you want to run IV/LIML/GMM2S regressions with fixed effects, or run OLS regressions with advanced standard errors (HAC, Kiefer, etc.)

| Command                   | regress | areg    | reghdfe   | ivreg2                               | ivreghdfe                            |
|---------------------------|---------|---------|-----------|--------------------------------------|--------------------------------------|
| Models:                   | OLS     | OLS     | OLS       | OLS, IV, LIML, GMM2S, CUE            | OLS, IV, LIML, GMM2S (not CUE!)      |
| Fixed effects?            | -       | One-way | Multi-way | -                                    | Multi-way                            |
| Cluster SE?               | One-way | One-way | Multi-way | Two-way                              | Two-way                              |
| Additional SEs:           | -       | -       | -         | AC, HAC, Kiefer, Driscol-Kraay, etc. | AC, HAC, Kiefer, Driscol-Kraay, etc. |
| (Speed) Time without FEs: | 1x      | -       | 2x        | 3.7x                                 | 4.3x                                 |
| (Speed) Time with one FE: | -       | 6.3x    | 2.1x      | -                                    | 4.6x                                 |

*([Benchmark](simple_benchmark.do) run on Stata 14-MP (4 cores), with a dataset of 4 regressors, 10mm obs., 100 clusters and 10,000 FEs)*

## Installation

`ivreghdfe` requires three packages: `ivreg2`, `reghdfe` (version 5.x) and `ftools`. Run the lines below to install everything you might possibly need. You can install the latest version by using `global ivrvers master`, otherwise specify the precise version.


```
* Set versions
global ftvers  master
global rhvers  master
global ivrvers master
* Use an older version
* global ivrvers 1.1.2

* Install ftools (remove program if it existed previously)
cap ado uninstall ftools
net install ftools, from("https://raw.githubusercontent.com/sergiocorreia/ftools/$ftvers/src/")

* Install reghdfe
cap ado uninstall reghdfe
net install reghdfe, from("https://raw.githubusercontent.com/sergiocorreia/reghdfe/$rhvers/src/")

* Install ivreg2, the core package
cap ado uninstall ivreg2
ssc install ivreg2

* Finally, install this package
cap ado uninstall ivreghdfe
net install ivreghdfe, from(https://raw.githubusercontent.com/sergiocorreia/ivreghdfe/$ivrvers/src/)
```

## Advice

This code just modifies `ivreg2` adding an `absorb()` option that uses
`reghdfe`s Mata functions (see [this link](https://www.diffchecker.com/tzvmpKis) for the line-by-line differences).
When used, `absorb()` will also activate the `small`, `noconstant` and `nopartialsmall`
options of `ivreg2` (basically to force small sample adjustments, which are
required as we might have a substantial number of fixed effects).

You can also use all other reghdfe options as normal options of `ivreghdfe`
(e.g. tolerance, choice of transform, etc.):

```stata
sysuse auto, clear
ivreghdfe price weight (length=gear), absorb(turn trunk) tol(1e-6) accel(sd)
```

This is gives the same result as using the old version of reghdfe (but slower):

```stata
reghdfe price weight (length=gear), absorb(turn trunk) tol(1e-6) accel(sd) version(3)
```

### Residuals

To save residuals, do this:

```stata
sysuse auto
ivreghdfe price weight, absorb(trunk) resid(myresidname)
```

You can also use the other predict options of `reghdfe`, such as `d`:

```stata
predict d, d
```
