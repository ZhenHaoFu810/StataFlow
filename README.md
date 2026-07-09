# StataFlow

**A Python econometrics toolkit designed to reproduce Stata 17 estimation results with field-level validation.**

[![PyPI version](https://img.shields.io/pypi/v/stataflow)](https://pypi.org/project/stataflow/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

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

StataFlow is for researchers who want Python workflows without giving up the empirical conventions they rely on in Stata. The project is not a generic statistics library: public capabilities are validated against Stata 17 with synthetic cases, public real-data cases, and Stata/Python dual-run evidence where Stata is available.

The current public line is **1.1.0 Stable**, with an additional **v1.2.0+ correctness-hardening release-candidate sync** prepared on July 9, 2026.

## Features

- **14 Stata-style commands in Python**: `regress`, `xtreg_fe`, `areg`, `reghdfe`, `ivregress_2sls`, `ivreghdfe`, `logit`, `probit`, `poisson`, `ppmlhdfe`, `did_imputation`, `eventstudyinteract`, `csdid`, and `rdrobust`.
- **Two API layers**: a Stata-compatible command layer (`stataflow.compat.stata`) and a Python-native estimator layer (`stataflow.estimators`).
- **Stata-style output**: `result.display()` prints compact regression tables with coefficients, standard errors, test statistics, p-values, and fit statistics.
- **High-dimensional fixed effects**: MAP absorption for large FE designs, multi-FE workflows, singleton handling, individual slopes, and cluster-aware VCE paths.
- **Instrumental variables**: 2SLS, GMM2S, LIML, Fuller/k-class, first-stage diagnostics, weak-instrument tests, and overidentification tests.
- **Binary, count, and PPML models**: Logit, Probit, Poisson, and PPML-HDFE with robust and clustered covariance estimators.
- **Causal inference**: BJS DID imputation, Sun-Abraham event-study interactions, Callaway-Sant'Anna DID, and sharp/fuzzy regression discontinuity.
- **Stata-compatible syntax subsets**: factor variables, analytic weights, multiple fixed effects, common VCE choices, and hard rejection of unsupported parameters.
- **Validation-first development**: public commands are backed by field-level Stata 17 comparison evidence.

## Installation

```bash
pip install StataFlow
```

Python 3.10, 3.11, or 3.12 is required. Core dependencies are NumPy, pandas, SciPy, scikit-learn, and PyYAML.

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

### Programmatic Results

```python
result.display(show_ci=True)

for coef in result.coefficients:
    print(f"{coef.name}: b={coef.beta:.6f}, se={coef.std_err:.6f}, t={coef.t_stat:.2f}")

print(f"R2 = {result.fit.r2:.4f}, N = {result.sample.nobs}")
```

## Supported Models

| Family | Available via | Estimators and VCE |
|--------|---------------|--------------------|
| Linear | `regress`, `areg`, `xtreg_fe`, `reghdfe` | OLS with `ols`, `robust` (HC1), `cluster` (1-way, 2-way where supported), and `dkraay` panel HAC |
| IV | `ivregress_2sls`, `ivreghdfe` | 2SLS, GMM2S, LIML, Fuller/k-class, first-stage diagnostics, weak-IV tests |
| Binary / Count | `logit`, `probit`, `poisson` | MLE with `ols`, `robust`, and `cluster` VCE |
| PPML + HDFE | `ppmlhdfe` | IRLS with fixed effects, offset/exposure, separation checks, `eform`, and common prediction types |
| DID | `did_imputation`, `csdid`, `eventstudyinteract` | BJS imputation, Callaway-Sant'Anna, and Sun-Abraham IW estimators |
| RD | `rdrobust` | Sharp/fuzzy RD, MSE/CER bandwidth selectors, covariates, weights, mass points, and cluster/nncluster VCE |

See [Open-Source Status](docs/release/open-source-status.md) and [Known Issues](docs/release/known-issues.md) for exact support boundaries.

## Validation

Recent local release-candidate checks (July 9, 2026):

- Public unit/integration suite: `405 passed`
- Internal modular audit suite: `95 passed`
- Golden dual-run collection guard: `839 tests collected`
- Example smoke scripts: all four public demos passed
- Wheel build: `stataflow-1.1.0-py3-none-any.whl` built successfully
- Open-source export dry-run: 150 files selected, 0 orphan removals

Golden Stata dual-run tests require a local Stata 17 installation and are not part of the public CI gate.

## Documentation

- [User Guide](docs/USER_GUIDE.md) ([中文](docs/USER_GUIDE.zh-CN.md))
- [Cookbook](docs/cookbook.md) ([中文](docs/cookbook.zh-CN.md))
- [Examples](examples/)
- [Validation Evidence](research/results/validation/README.md)
- [Changelog](CHANGELOG.md)

## Running Tests

```bash
# Unit and integration tests
pytest tests/ -v --ignore=tests/golden/ --ignore=tests/audit_v1_3

# Golden dual-run tests (require local Stata 17)
pytest tests/golden/ -v
```

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
