# Command Support Matrix

This directory lists the current support status for every Stata-compatible command exposed by `stataflow.compat.stata`.

Cross-command validation evidence is collected separately in [`research/results/validation/`](../../research/results/validation/).


## Quick Reference

| Command | Family | Status | Key Features |
|---------|--------|--------|--------------|
| [`regress`](./regress.md) | Linear Base | Stable | OLS, robust, cluster (1- and 2-way), aweight, noconstant |
| [`xtreg, fe`](./xtreg-fe.md) | Panel / FE | Stable | Within estimator, single FE, cluster |
| [`areg`](./areg.md) | Panel / FE | Stable | Single absorb var, OLS/cluster VCE |
| [`reghdfe`](./reghdfe.md) | Panel / HDFE | Beta | 1+ categorical FEs, 2-way cluster, MAP, slopes, DK, savefe, predict stdp |
| [`ivregress 2sls`](./ivregress-2sls.md) | IV | Stable | 2SLS, robust, cluster |
| [`ivreghdfe`](./ivreghdfe.md) | IV / HDFE | Beta | IV + 1+ FEs, 2SLS/GMM2S/LIML, 2-way cluster, first, weakiv |
| [`logit`](./logit.md) | Binary | Stable | MLE, robust, cluster, predict, margins |
| [`probit`](./probit.md) | Binary | Stable | MLE, robust, cluster, predict, margins |
| [`poisson`](./poisson.md) | Count | Stable | MLE, robust, cluster, predict, margins |
| [`ppmlhdfe`](./ppmlhdfe.md) | Count / HDFE | Beta | PPML + 1+ FEs, 2-way cluster, eform, separation, residuals, estat ic |
| [`did_imputation`](./did-imputation.md) | DID / Event Study | Beta | BJS imputation, allhorizons, controls, pretrends, cluster |
| [`rdrobust`](./rdrobust.md) | RD | Beta | Sharp / Fuzzy RD, 9 bandwidth selectors, covs, cluster/nncluster VCE |
| [`eventstudyinteract`](./eventstudyinteract.md) | DID / Event Study | Beta | Sun-Abraham IW estimator, auto dummy generation, cluster |
| [`csdid`](./csdid.md) | DID / Event Study | Beta | Callaway-Sant'Anna, method="reg"/"dr"/"dripw", event/simple/group/calendar agg |

## Status Legend

- **Stable** — validated through synthetic and real-data Stata 17 comparison; core API unlikely to change in backward-incompatible ways.
- **Beta** — high-frequency paths are implemented and verified against Stata 17, and most major functional blocks are covered. The command surface may still be a subset of the full community command; unsupported parameters are hard-rejected.

## Common Limitations Across All Commands

- Three-way and higher multi-way clustering is not yet supported. Two-way clustering (Cameron-Gelbach-Miller 2011) is supported on `regress`, `reghdfe`, `ivreghdfe`, and `ppmlhdfe`.
- Post-estimation (`predict`, `margins`) is available on the core estimator layer (`stataflow`), not directly on `compat.stata` wrappers. Most estimation wrappers return `ResultSchema`; `csdid()` returns a fitted `CSDID` model.
- Weight support is command-specific. Only commands that list `aweight` accept it.
- Any parameter not explicitly listed in a command matrix is hard-rejected via `ValueError`.

`rdplot` is an exported RD visualization helper. It is not counted among the
14 estimation commands.
