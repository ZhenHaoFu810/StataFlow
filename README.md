# StataFlow

**A Python econometrics toolkit that reproduces Stata 17 results with high precision.**

[![PyPI version](https://img.shields.io/pypi/v/stataflow)](https://pypi.org/project/stataflow/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

---

```python
from stataflow.compat.stata import reghdfe

result = reghdfe(df, y="lwage", x=["exper", "edu"],
                 absorb="firm_id year_id", vce="cluster", cluster="firm_id")
result.display()
```

---

## Features

- **14 Stata commands in Python**: `regress`, `reghdfe`, `ivregress 2sls`, `ivreghdfe`, `logit`, `probit`, `poisson`, `ppmlhdfe`, `did_imputation`, `eventstudyinteract`, `csdid`, `rdrobust`, `areg`, `xtreg_fe`
- **Stata-style regression table**: `result.display()` produces a formatted output matching Stata's layout
- **High-dimensional fixed effects**: MAP iterative absorption handles 10K+ FE levels without memory issues; individual slope absorption (`absorb(firm_id##c.time)`)
- **Driscoll-Kraay panel HAC**: time-series-robust standard errors with Bartlett kernel autocorrelation correction
- **Instrumental variables**: 2SLS, GMM2S, and LIML estimators with weak-instrument diagnostics (Kleibergen-Paap F + Stock-Yogo critical values)
- **Binary, count, and PPML models**: Logit, Probit, Poisson, and PPML with HDFE
- **Causal inference**: DID (BJS imputation, Sun-Abraham, Callaway-Sant'Anna) with doubly-robust methods; Regression Discontinuity with 11 bandwidth selectors
- **Stata-compatible syntax**: factor variables (`i.group##c.post`), analytic weights, multiple FEs
- **Validated against Stata 17**: every public capability has field-level Python-Stata dual-run evidence

## Installation

```bash
pip install StataFlow
```

Python 3.10+ required. Dependencies: NumPy, pandas, SciPy.

## Quick Start

### Stata-compatible API

```python
import pandas as pd
from stataflow.compat.stata import regress, reghdfe, logit, ivregress_2sls, ppmlhdfe

# OLS with robust standard errors
result = regress(df, y="wage", x=["edu", "exper"], vce="robust")
result.display()

# High-dimensional fixed effects
result = reghdfe(
    df, y="wage", x=["edu", "exper"],
    absorb="firm_id year_id", vce="cluster", cluster="industry"
)

# Logit
result = logit(df, y="inlf", x=["nwifeinc", "educ", "exper"])
result.display()

# 2SLS with LIML
result = ivregress_2sls(
    df, y="lwage", x_exog=["edu"], x_endog=["exper"],
    instruments=["age", "kidslt6"], vce="robust"
)

# PPML with HDFE
result = ppmlhdfe(
    df, y="trade", x=["lndist", "contig", "fta"],
    absorb=["exporter", "importer", "year"], vce="cluster", cluster="exporter"
)
```

### Native Python API

```python
from stataflow import OLS, AbsorbingOLS, Logit

model = OLS(data=df, y="wage", x=["edu", "exper"])
result = model.fit(vce="robust")
result.display()
```

### Using results

```python
# Stata-style table
result.display()
result.display(show_ci=True)  # with confidence intervals

# Programmatic access
for c in result.coefficients:
    print(f"{c.name}: b={c.beta:.6f}, se={c.std_err:.6f}, t={c.t_stat:.2f}")

print(f"R² = {result.fit.r2:.4f}, N = {result.sample.nobs}")
```

## Supported Models

| Family | Available via | Estimators & VCE |
|--------|--------------|------------------|
| **Linear** | `regress`, `areg`, `xtreg_fe`, `reghdfe` | OLS with `ols` / `robust` (HC1) / `cluster` (1-way, 2-way) / `dkraay` (panel HAC) |
| **IV** | `ivregress_2sls`, `ivreghdfe` | 2SLS, GMM2S, LIML (with Fuller), first-stage diagnostics, weak-IV tests |
| **Binary / Count** | `logit`, `probit`, `poisson` | MLE with `ols` / `robust` / `cluster` |
| **PPML + HDFE** | `ppmlhdfe` | IRLS with `ols` / `robust` / `cluster`, separation detection, eform |
| **DID** | `did_imputation`, `csdid`, `eventstudyinteract` | BJS imputation, Callaway-Sant'Anna (reg + DR), Sun-Abraham IW |
| **RDD** | `rdrobust` | Sharp / Fuzzy RD, 11 MSE+CER bandwidth selectors, cluster/nncluster VCE |

## Documentation

- [User Guide](docs/USER_GUIDE.md) — full tutorial and concept guide (中文: [用户手册](docs/USER_GUIDE.zh-CN.md))
- [Cookbook](docs/cookbook.md) — copy-pasteable recipes for common tasks (中文: [中文 Cookbook](docs/cookbook.zh-CN.md))
- [Examples](examples/) — runnable demo scripts

## Running Tests

```bash
# Unit and integration tests
pytest tests/ -v --ignore=tests/golden/

# Golden dual-run tests (require local Stata 17)
pytest tests/golden/ -v
```

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
