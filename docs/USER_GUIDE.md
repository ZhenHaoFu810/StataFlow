# User Guide

## 1. Purpose

This document is for external users of StataFlow. It covers installation, the two main usage layers, validation assets, and recommended reading order.

## 2. Two main usage layers

### `stataflow.compat.stata`

Use this layer when you want a Stata-like command surface.

Typical commands include:

- `regress`
- `xtreg_fe`
- `areg`
- `reghdfe`
- `ivregress_2sls`
- `ivreghdfe`
- `logit`
- `probit`
- `poisson`
- `ppmlhdfe`
- `did_imputation`
- `eventstudyinteract`
- `csdid`
- `rdrobust`

### Core estimators

Use the estimator layer when you want lower-level control. The estimator classes live under [src/stataflow/estimators](/src/stataflow/estimators).

## 3. Installation and environment

Install in editable mode:

```bash
pip install -e .
```

For validation scripts that dual-run against Stata, a working local Stata 17 installation is required. The package keeps the Stata-facing execution logic in [src/stataflow/stata_runner](/src/stataflow/stata_runner).

## 4. Examples

See:

- [examples/demo_regress.py](/examples/demo_regress.py)
- [examples/demo_reghdfe.py](/examples/demo_reghdfe.py)
- [examples/demo_ppmlhdfe.py](/examples/demo_ppmlhdfe.py)
- [examples/demo_ivregress_2sls.py](/examples/demo_ivregress_2sls.py)

## 5. Factor-variable surface

The command layer includes a Stata-style factor-variable subset. Coverage is documented in the relevant support matrices and research docs. Supported patterns should be checked command by command, especially for:

- continuous interactions such as `x1#x2`, `x1##x2`
- categorical interactions using `i.`
- FE/HDFE models where main effects may be absorbed while interaction terms remain identified

## 6. Fixed effects and HDFE usage

Use `absorb="firm year"` or list-style absorb specifications where supported by the command wrapper. Current HDFE support is subset-specific; always check:

- [docs/command-support-matrix/reghdfe.md](/docs/command-support-matrix/reghdfe.md)
- [docs/command-support-matrix/ivreghdfe.md](/docs/command-support-matrix/ivreghdfe.md)
- [docs/command-support-matrix/ppmlhdfe.md](/docs/command-support-matrix/ppmlhdfe.md)

## 7. Validation assets

This package includes runnable validation scripts and generated artifacts.

Scripts:

- [scripts/validation](/scripts/validation)
- [scripts/validation/oos](/scripts/validation/oos)

Generated artifacts:

- [research/results/validation](/research/results/validation)

## 8. Recommended reading order

Recommended reading order for new users:

1. [README.md](/README.md)
2. [docs/command-support-matrix/README.md](/docs/command-support-matrix/README.md)
3. command-specific support matrices
