# Validation Evidence

StataFlow is validated through **Stata-Python dual-run testing**: every public command runs on identical data in both Stata 17 and Python, with field-level comparison of results. This document summarizes the validation evidence organized by command family.

---

## Methodology

For each command, we run:

1. **Synthetic data tests** — designed to lock down specific statistical properties: coefficient estimates, standard errors (homoskedastic, robust, clustered), degrees of freedom, R-squared, and edge cases (missing values, collinearity, singleton groups, boundary values).
2. **Real public data tests** — standard econometric datasets (Fama-French factors, Card returns-to-schooling, Wooldridge wagepan, Cattaneo et al. Senate election data, etc.) to verify behavior on realistic research data.

**Comparison standard:** Stata 17 output. All coefficients, standard errors, t/z-statistics, p-values, confidence intervals, and fit statistics (R², RMSE, F-statistic, log-likelihood, deviance) are compared field-by-field.

**Precision standards:**
- Coefficients: relative tolerance < 10⁻⁶
- Standard errors (OLS, robust): relative tolerance < 10⁻⁶
- Standard errors (cluster, Driscoll-Kraay HAC): relative tolerance < 10⁻⁴
- Fit statistics: relative tolerance < 10⁻⁶

Exceptions governed by Architecture Decision Records (see main repository for details).

---

## Linear Models

### `regress` — Ordinary Least Squares

| Capability | Synthetic | Real Data |
|-----------|-----------|-----------|
| OLS (homoskedastic) | ✓ | ✓ (Fama-French 3-factor, N=1,196) |
| Robust HC1 | ✓ | ✓ |
| Cluster (1-way) | ✓ | ✓ |
| Cluster (2-way) | ✓ | — |
| Analytic weights | ✓ | — |
| No constant | ✓ | — |
| Missing value handling | ✓ | — |
| Collinearity detection | ✓ | — |

**Golden test files:** 14

### `xtreg, fe` — Fixed Effects (Within)

| Capability | Synthetic | Real Data |
|-----------|-----------|-----------|
| Within transformation | ✓ | ✓ (Grunfeld, N=200) |
| Cluster-robust VCE | ✓ | — |

**Golden test files:** 2

### `areg` — Single Absorbed Variable

| Capability | Synthetic | Real Data |
|-----------|-----------|-----------|
| Single FE absorption | ✓ | ✓ (wagepan, N=4,360) |

**Golden test files:** 4

### `reghdfe` — High-Dimensional Fixed Effects

| Capability | Synthetic | Real Data |
|-----------|-----------|-----------|
| 1-way FE absorption | ✓ | ✓ (wagepan) |
| 2-way FE absorption | ✓ | ✓ |
| 3-way FE absorption | ✓ | — |
| Cluster (1-way) | ✓ | ✓ |
| Cluster (2-way) | ✓ | ✓ |
| Robust HC1 | ✓ | — |
| Driscoll-Kraay panel HAC (`vce(dkraay)`) | ✓ | ✓ (wagepan) |
| MAP iterative absorption (`technique="map"`) | ✓ (10K obs) | — |
| Individual slope absorption (`##c.` / `#c.`) | ✓ | ✓ (wagepan) |
| Multi-slope absorption | ✓ | — |
| Saves FE estimates (`savefe`) | ✓ | — |
| Keeps singleton groups | ✓ | — |
| Noconstant | ✓ | — |
| Predict (xb, residuals, stdp) | ✓ | — |
| Factor-variable syntax | ✓ | — |

**Golden test files:** 38

---

## Instrumental Variables

### `ivregress 2sls` — Two-Stage Least Squares

| Capability | Synthetic | Real Data |
|-----------|-----------|-----------|
| 2SLS (homoskedastic) | ✓ | ✓ (Card, N=3,010) |
| Robust VCE | ✓ | — |
| Cluster VCE | ✓ | — |

**Golden test files:** 6

### `ivreghdfe` — IV with High-Dimensional Fixed Effects

| Capability | Synthetic | Real Data |
|-----------|-----------|-----------|
| 2SLS + FE absorption | ✓ | ✓ (Card, wagepan) |
| GMM2S estimator | ✓ | ✓ (Card) |
| LIML estimator (with Fuller) | ✓ | ✓ (Card) |
| K-class estimator | ✓ | — |
| Cluster (1-way, 2-way) | ✓ | ✓ |
| First-stage diagnostics (`first`) | ✓ | — |
| Weak-IV diagnostics (`weakiv`) | ✓ | ✓ (Card) |
| Kleibergen-Paap rk Wald F | ✓ | ✓ |
| Stock-Yogo critical values | ✓ | ✓ |
| Hansen J overidentification test | ✓ | — |
| Factor-variable syntax | ✓ | — |
| Predict (xb, residuals, stdp) | ✓ | — |

**Golden test files:** 12

---

## Binary and Count Models

### `logit` — Logistic Regression

| Capability | Synthetic | Real Data |
|-----------|-----------|-----------|
| MLE estimation | ✓ | ✓ (Mroz, N=753) |
| Robust VCE | ✓ | — |
| Cluster VCE | ✓ | — |
| Factor-variable syntax | ✓ | — |

**Golden test files:** 12

### `probit` — Probit Regression

| Capability | Synthetic | Real Data |
|-----------|-----------|-----------|
| MLE estimation | ✓ | ✓ (Mroz) |
| Robust VCE | ✓ | — |
| Cluster VCE | ✓ | — |

**Golden test files:** 6

### `poisson` — Poisson Regression

| Capability | Synthetic | Real Data |
|-----------|-----------|-----------|
| MLE estimation | ✓ | ✓ (crime1) |
| Robust VCE | ✓ | — |
| Cluster VCE | ✓ | — |

**Golden test files:** 6

### `ppmlhdfe` — Poisson Pseudo-Maximum Likelihood with HDFE

| Capability | Synthetic | Real Data |
|-----------|-----------|-----------|
| PPML + 1+ group HDFE | ✓ | ✓ (gravity trade, N=17,850) |
| Robust VCE | ✓ | ✓ |
| Cluster (1-way, 2-way) | ✓ | ✓ |
| Separation detection (`separation="fe"`) | ✓ | — |
| Incidence-rate ratios (`eform`) | ✓ | — |
| Offset / exposure | ✓ | — |
| Predict (pearson, deviance, working residuals) | ✓ | — |
| `estat ic` (AIC / BIC) | ✓ | — |
| Factor-variable syntax | ✓ | — |

**Golden test files:** 22

---

## Difference-in-Differences

### `did_imputation` — Borusyak-Jaravel-Spiess Imputation

| Capability | Synthetic | Real Data |
|-----------|-----------|-----------|
| Core estimator | ✓ | ✓ (ezunem, N=198) |
| Controls (`controls`) | ✓ | — |
| Unit-level controls (`unitcontrols`) | ✓ | — |
| Time-level controls (`timecontrols`) | ✓ | — |
| Pretrends tests (`pretrends`) | ✓ | — |
| Heterogeneous effects (`hetby`) | ✓ | — |
| Custom weighting (`wtr`, `sum`) | ✓ | — |
| Save estimates (`saveestimates`) | ✓ | — |

**Golden test files:** 4

### `eventstudyinteract` — Sun-Abraham Interaction-Weighted Estimator

| Capability | Synthetic | Real Data |
|-----------|-----------|-----------|
| Auto-generated dummies | ✓ | ✓ (ezunem) |
| Pre-generated dummies | ✓ | — |

**Golden test files:** 4

### `csdid` — Callaway-Sant'Anna DID

| Capability | Synthetic | Real Data |
|-----------|-----------|-----------|
| Regression adjustment (`method="reg"`) | ✓ | ✓ (ezunem) |
| Doubly-robust (`method="drimp"` / `"dripw"`) | ✓ | ✓ |
| Aggregation (simple, group, calendar, event) | ✓ | — |

**Golden test files:** 8

---

## Regression Discontinuity

### `rdrobust` — Local Polynomial RD

| Capability | Synthetic | Real Data |
|-----------|-----------|-----------|
| Sharp RD | ✓ | ✓ (Senate, N=1,390) |
| Fuzzy RD | ✓ | ✓ |
| 11 MSE/CER bandwidth selectors | ✓ | ✓ |
| Cluster VCE, NN-cluster VCE | ✓ | ✓ |
| Covariates adjustment (`covs`) | ✓ | — |
| Analytical weights (`weights`) | ✓ | — |
| Mass points correction (`masspoints`) | ✓ | — |
| Kernel selection (triangular, epanechnikov, uniform) | ✓ | — |
| RD plot (`rdplot`) | ✓ | — |

**Golden test files:** 8

---

## Summary

| Command Family | Commands | Golden Test Files | Synthetic | Real Data |
|---------------|----------|-------------------|-----------|-----------|
| Linear Models | `regress`, `xtreg_fe`, `areg`, `reghdfe` | 58 | ✓ | ✓ |
| Instrumental Variables | `ivregress_2sls`, `ivreghdfe` | 18 | ✓ | ✓ |
| Binary / Count | `logit`, `probit`, `poisson`, `ppmlhdfe` | 46 | ✓ | ✓ |
| Difference-in-Differences | `did_imputation`, `eventstudyinteract`, `csdid` | 16 | ✓ | ✓ |
| Regression Discontinuity | `rdrobust` | 8 | ✓ | ✓ |
| **Total** | **14 commands** | **146** | — | — |

All 14 commands have both synthetic and real-data dual-run evidence. Full test code, datasets, and comparison logs are maintained in the main development repository.
