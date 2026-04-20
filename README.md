# StataFlow

StataFlow is a Python library that mirrors a focused subset of common Stata econometrics workflows with a Stata-like command surface and source-backed validation.

This clean open-source package is separated from the original development workspace. It keeps the core library, public examples, validation evidence, public datasets, and release-facing documentation, while excluding most internal planning, review, and task-tracking material.

## What is included

- Core package code in [src/stataflow](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/src/stataflow)
- Public examples in [examples](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/examples)
- Command support documentation in [docs/command-support-matrix](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/docs/command-support-matrix)
- Validation evidence in [docs/validation](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/docs/validation)
- Public datasets and validation artifacts in [research/data/public](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/research/data/public) and [research/results/validation](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/research/results/validation)
- A concise user manual in [docs/USER_GUIDE.md](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/docs/USER_GUIDE.md)

Chinese documentation:
- [README.zh-CN.md](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/README.zh-CN.md)
- [docs/USER_GUIDE.zh-CN.md](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/docs/USER_GUIDE.zh-CN.md)

## Installation

```bash
pip install StataFlow
```

Python 3.10+ required. Dependencies: NumPy, pandas, SciPy, PyYAML.

For development (editable install from source):

```bash
git clone https://github.com/ZhenHaoFu810/StataFlow.git
cd StataFlow
pip install -e .
```

## Quick start

```python
import pandas as pd
from stataflow.compat.stata import regress, reghdfe

df = pd.read_csv("research/data/public/panel/oos/airfare.csv")

ols_res = regress(
    df=df,
    y="lfare",
    x=["ldist", "y98", "y99"],
    vce="robust",
)

hdfe_res = reghdfe(
    df=df,
    y="lfare",
    x=["ldist", "y98##y99"],
    absorb="id year",
    vce="cluster",
    cluster="id",
)
```

The `compat.stata` wrappers return stable result schemas for command-style usage. Lower-level estimators remain available in the core package for programmatic workflows.

## Supported command families

Current coverage focuses on validated subsets of:

- `regress`
- `xtreg, fe`
- `areg`
- `reghdfe`
- `ivregress 2sls`
- `ivreghdfe`
- `logit`
- `probit`
- `poisson`
- `ppmlhdfe`
- `did_imputation`
- `eventstudyinteract`
- `csdid`
- `rdrobust`

Support is command-specific and subset-specific. Do not assume full Stata parity from command name alone. Check the command matrices:

- [docs/command-support-matrix/README.md](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/docs/command-support-matrix/README.md)

## Validation evidence

The main public evidence entry points are:

- [Validation overview](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/docs/validation/README.md)
- [Validation summary](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/docs/validation/overview.md)
- [Evidence matrix](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/docs/validation/evidence-matrix.md)
- [Out-of-sample results summary](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/research/results/validation/oos/oos_master_summary.md)

The validation policy is strict field-level comparison against Stata 17 for the implemented subset. Synthetic development tests exist in the codebase, but the public evidence book emphasizes real public-data dual runs.

## Repository structure

- [src](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/src): package source
- [examples](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/examples): runnable examples
- [docs](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/docs): user-facing documentation
- [scripts/validation](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/scripts/validation): validation runners and summary builders
- [research/data/public](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/research/data/public): public datasets used for validation
- [research/results/validation](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/research/results/validation): generated validation artifacts

## Known limitations

- Several community commands are validated subsets rather than full command reimplementations.
- Validation evidence is strongest for the documented subset and the included public datasets.
- Some internal development reports were intentionally excluded from this clean package.

For current release notes and known issues:

- [docs/release/open-source-alpha-status.md](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/docs/release/open-source-alpha-status.md)
- [docs/release/known-issues.md](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/docs/release/known-issues.md)
