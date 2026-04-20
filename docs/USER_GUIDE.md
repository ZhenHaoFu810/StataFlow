# User Guide

## 1. Purpose

This package is a clean release-oriented copy of the StataFlow project. It is intended for external use, reproducible validation, and open-source distribution. Internal planning artifacts, review loops, and most development-only coordination files are intentionally excluded.

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

Use the estimator layer when you want lower-level control. The estimator classes live under [src/stataflow/estimators](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/src/stataflow/estimators).

## 3. Installation and environment

Install in editable mode:

```bash
pip install -e .
```

For validation scripts that dual-run against Stata, a working local Stata 17 installation is required. The package keeps the Stata-facing execution logic in [src/stataflow/stata_runner](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/src/stataflow/stata_runner).

## 4. Examples

See:

- [examples/demo_regress.py](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/examples/demo_regress.py)
- [examples/demo_reghdfe.py](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/examples/demo_reghdfe.py)
- [examples/demo_ppmlhdfe.py](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/examples/demo_ppmlhdfe.py)
- [examples/demo_ivregress_2sls.py](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/examples/demo_ivregress_2sls.py)

## 5. Factor-variable surface

The command layer includes a Stata-style factor-variable subset. Coverage is documented in the relevant support matrices and research docs. Supported patterns should be checked command by command, especially for:

- continuous interactions such as `x1#x2`, `x1##x2`
- categorical interactions using `i.`
- FE/HDFE models where main effects may be absorbed while interaction terms remain identified

## 6. Fixed effects and HDFE usage

Use `absorb="firm year"` or list-style absorb specifications where supported by the command wrapper. Current HDFE support is subset-specific; always check:

- [docs/command-support-matrix/reghdfe.md](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/docs/command-support-matrix/reghdfe.md)
- [docs/command-support-matrix/ivreghdfe.md](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/docs/command-support-matrix/ivreghdfe.md)
- [docs/command-support-matrix/ppmlhdfe.md](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/docs/command-support-matrix/ppmlhdfe.md)

## 7. Validation assets

This package includes both validation documentation and runnable validation scripts.

Documentation:

- [docs/validation/README.md](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/docs/validation/README.md)
- [docs/validation/overview.md](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/docs/validation/overview.md)
- [docs/validation/evidence-matrix.md](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/docs/validation/evidence-matrix.md)

Scripts:

- [scripts/validation](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/scripts/validation)
- [scripts/validation/oos](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/scripts/validation/oos)

Generated artifacts:

- [research/results/validation](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/research/results/validation)

## 8. Public datasets

Public validation datasets are stored in:

- [research/data/public](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/research/data/public)

Use [docs/validation/dataset-registry.md](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/docs/validation/dataset-registry.md) to see data provenance, intended command coverage, and validation status.

## 9. Release-facing reading order

Recommended reading order for new users:

1. [README.md](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/README.md)
2. [docs/command-support-matrix/README.md](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/docs/command-support-matrix/README.md)
3. [docs/validation/README.md](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/docs/validation/README.md)
4. [docs/validation/overview.md](/D:/OneDrive%20-%20SAIF/PhD3/StataFlow_open_source/docs/validation/overview.md)
5. command-specific support matrices

## 10. What this clean package excludes

This package intentionally excludes most of the following:

- internal AI task prompts
- iterative review reports
- development-time backlog coordination
- temporary logs and one-off progress files

That material remains in the original working repository, not in this release-focused copy.
