# StataFlow

**Stata-aligned econometrics for Python, with field-level validation across the documented support surface.**

[简体中文](README.zh-CN.md)

[![CI](https://github.com/ZhenHaoFu810/StataFlow/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/ZhenHaoFu810/StataFlow/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/stataflow.svg)](https://pypi.org/project/StataFlow/)
[![Downloads](https://static.pepy.tech/badge/stataflow)](https://pepy.tech/projects/stataflow?timeRange=threeMonths&category=version&includeCIDownloads=true&granularity=weekly&viewType=line&versions=Total%2C1.*%2C0.*)
[![Python 3.10-3.14](https://img.shields.io/badge/Python-3.10--3.14-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![License](https://img.shields.io/pypi/l/stataflow.svg)](LICENSE)
[![Typing](https://img.shields.io/pypi/types/stataflow.svg)](https://pypi.org/project/StataFlow/)
[![Stata validation](https://img.shields.io/badge/Stata_validation-documented_support_surface-1f6f5f.svg)](VALIDATION.md)

[Installation](#installation) · [Quick Start](#quick-start) · [Validation](#validation) · [Documentation](#documentation) · [Contributing](CONTRIBUTING.md)

---

```python
from stataflow.compat.stata import reghdfe

result = reghdfe(
    df,
    y="lwage",
    x=["exper", "edu"],
    absorb="firm_id year_id",
    vce="cluster",
    cluster="firm_id",
)
result.display()
```

---

## Why StataFlow

StataFlow is for researchers who want Python workflows without giving up the empirical conventions they rely on in Stata. The project is not a generic statistics library: public capabilities have Stata validation across the documented support surface, backed by synthetic cases, public real-data cases, and field-level comparisons.

The latest release is **1.3.1**, covering 14 Stata-style commands.

## Features

- **14 estimation commands in Python**: `regress`, `xtreg_fe`, `areg`, `reghdfe`, `ivregress_2sls`, `ivreghdfe`, `logit`, `probit`, `poisson`, `ppmlhdfe`, `did_imputation`, `eventstudyinteract`, `csdid`, and `rdrobust`. The exported `rdplot` companion is a helper and is not counted as an estimation command.
- **Two API layers**: a Stata-compatible command layer (`stataflow.compat.stata`) and a Python-native estimator layer (`stataflow.estimators`).
- **Command-aware Stata-style output**: `result.display()` prints a complete,
  adaptive result table with the statistics and diagnostics relevant to each
  command; notebooks receive the same content as escaped HTML.
- **High-dimensional fixed effects**: MAP absorption for large FE designs, multi-FE workflows, singleton handling, individual slopes, and cluster-aware VCE paths.
- **Instrumental variables**: 2SLS, GMM2S, LIML, Fuller/k-class, first-stage diagnostics, weak-instrument tests, and overidentification tests.
- **Binary, count, and PPML models**: Logit, Probit, Poisson, and PPML-HDFE with robust and clustered covariance estimators.
- **Causal inference**: BJS DID imputation, Sun-Abraham event-study interactions, Callaway-Sant'Anna DID, and sharp/fuzzy regression discontinuity.
- **Stata-compatible syntax subsets**: factor variables, command-specific analytic-weight support, multiple fixed effects, common VCE choices, and hard rejection of unsupported parameters.
- **Validation-first development**: public commands have field-level Stata validation across the documented support surface.

## Installation

```bash
pip install StataFlow
```

StataFlow requires Python 3.10 or later. The current release is tested on Python 3.10-3.14. Core dependencies are NumPy, pandas, SciPy, scikit-learn, and PyYAML.

## Quick Start

### Stata-Compatible API

```python
from stataflow.compat.stata import regress, reghdfe, logit, ivregress_2sls, ppmlhdfe

# OLS with robust standard errors
result = regress(df, y="wage", x=["edu", "exper"], vce="robust")
result.display()

# High-dimensional fixed effects
result = reghdfe(
    df,
    y="wage",
    x=["edu", "exper"],
    absorb="firm_id year_id",
    vce="cluster",
    cluster="industry",
)

# Logit
result = logit(df, y="inlf", x=["nwifeinc", "educ", "exper"])
result.display()

# 2SLS with robust VCE
result = ivregress_2sls(
    df,
    y="lwage",
    x_exog=["educ"],
    x_endog=["exper"],
    instruments=["age", "kidslt6"],
    vce="robust",
)

# PPML with high-dimensional fixed effects
result = ppmlhdfe(
    df,
    y="trade",
    x=["lndist", "contig", "fta"],
    absorb=["exporter", "importer", "year"],
    vce="cluster",
    cluster="exporter",
)
```

### Native Python API

```python
from stataflow import OLS, AbsorbingOLS, Logit

model = OLS(data=df, y="wage", x=["edu", "exper"])
result = model.fit(vce="robust")
result.display()
```

### Working with Results

```python
result.display()                         # Full output with 95% CI
result.display(detail="compact")        # Header, coefficients, core fit
result.display(show_ci=False)           # Hide confidence intervals
text = result.summary(width=100)        # Return the same table as text
html = result.to_html()                 # Escaped HTML for reports/notebooks
```

## Supported Models

| Family | Available via | Estimators and VCE |
|--------|---------------|--------------------|
| Linear | `regress`, `areg`, `xtreg_fe`, `reghdfe` | OLS with `ols`, `robust` (HC1), and command-specific clustering; `reghdfe` also supports `dkraay` panel HAC |
| IV | `ivregress_2sls`, `ivreghdfe` | 2SLS, GMM2S, LIML, Fuller/k-class, first-stage diagnostics, weak-IV tests |
| Binary / Count | `logit`, `probit`, `poisson` | MLE with `ols`, `robust`, and `cluster` VCE |
| PPML + HDFE | `ppmlhdfe` | IRLS with fixed effects, offset/exposure, separation checks, `eform`, and common prediction types |
| DID | `did_imputation`, `csdid`, `eventstudyinteract` | BJS imputation, Callaway-Sant'Anna, and Sun-Abraham IW estimators |
| RD | `rdrobust` | Sharp/fuzzy RD, MSE/CER bandwidth selectors, covariates, weights, mass points, and cluster/nncluster VCE |

See the [Command Support Matrix](docs/command-support-matrix/README.md) and [Known Issues](docs/release/known-issues.md) for exact support boundaries.

## Validation

The July 2026 table is the 1.2.0 estimator-validation snapshot retained for
1.3.0; the actual comparison environment was Stata 17.
The retained snapshot covers the coefficient and standard-error comparisons reported below.
It does not cover result statistics first added in 1.3.0.
Relative deviation is `|Python - Stata| / max(|Stata|, 1e-15)`.

| Family | Covered commands | Stata 17 comparisons | Max coefficient deviation | Max SE deviation |
|---|---|---:|---:|---:|
| Linear / FE | `regress`, `areg`, `xtreg_fe`, `reghdfe` | 18/18 | 2.48e-7 | 2.25e-7 |
| IV | `ivregress_2sls`, `ivreghdfe` | 5/5 | 1.16e-8 | 3.74e-8 |
| Binary / count | `logit`, `probit`, `poisson`, `ppmlhdfe` | 12/12 | 1.33e-7 | 8.42e-8 |
| DID | `did_imputation`, `csdid`, `eventstudyinteract` | 2/2 + 1 functional check | 8.13e-8 | 5.13e-8 |
| RD | `rdrobust` | 3/3 | 9.23e-8 | 2.96e-8 |
| **Total** | **14 public estimation commands** | **40/40** | **2.48e-7** | **2.25e-7** |

Full local Stata validation checks: `856 passed, 12 skipped`. The public,
self-contained suite passes `10/10` reproducible validation cases with Stata
17. The values above are stored in
[`evidence-summary.json`](research/results/validation/evidence-summary.json).

## Documentation

- [User Guide](docs/USER_GUIDE.md) ([中文](docs/USER_GUIDE.zh-CN.md))
- [Cookbook](docs/cookbook.md) ([中文](docs/cookbook.zh-CN.md))
- [Examples](examples/) — nine deterministic demo scripts covering all 14 public commands; no network or local Stata required
- [Validation Evidence (JSON)](research/results/validation/evidence-summary.json)
- [Validation Evidence (readable)](research/results/validation/evidence-summary.md)
- [Changelog](CHANGELOG.md)

## Running Tests

```bash
# Unit and integration tests
pytest tests/ -v

# Reproducible Stata validation cases (require local Stata 17)
pytest tests/stata_validation/ -v -s
```

## Community

- [Contributing Guide](CONTRIBUTING.md) — development workflow, testing requirements, and PR checks
- [Security Policy](SECURITY.md) — supported versions and private vulnerability reporting
- [Code of Conduct](CODE_OF_CONDUCT.md)

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
