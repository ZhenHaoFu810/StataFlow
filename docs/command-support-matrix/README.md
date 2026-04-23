# Command Support Matrix

This directory lists the current support status for every Stata-compatible command exposed by `stataflow.compat.stata`.

Cross-command validation evidence is collected separately in [`research/results/validation/`](../../research/results/validation/).


## Quick Reference

| Command | Family | Status | Key Features |
|---------|--------|--------|--------------|
| [`regress`](./regress.md) | Linear Base | Stable | OLS, robust, cluster (1- and 2-way), aweight, noconstant |
| [`xtreg, fe`](./xtreg-fe.md) | Panel / FE | Stable | Within estimator, single FE, cluster |
| [`areg`](./areg.md) | Panel / FE | Stable | Single absorb var, OLS/cluster VCE |
| [`reghdfe`](./reghdfe.md) | Panel / HDFE | Alpha | 1+ categorical FEs, singleton drop, robust/cluster |
| [`ivregress 2sls`](./ivregress-2sls.md) | IV | Stable | 2SLS, robust, cluster |
| [`ivreghdfe`](./ivreghdfe.md) | IV / HDFE | Alpha | IV + 1+ FEs, robust/cluster |
| [`logit`](./logit.md) | Binary | Stable | MLE, robust, cluster |
| [`probit`](./probit.md) | Binary | Stable | MLE, robust, cluster |
| [`poisson`](./poisson.md) | Count | Stable | MLE, robust, cluster |
| [`ppmlhdfe`](./ppmlhdfe.md) | Count / HDFE | Alpha | PPML + 1+ FEs, offset/exposure, robust/cluster |
| [`did_imputation`](./did-imputation.md) | DID / Event Study | Alpha | BJS imputation, allhorizons, autosample, cluster |
| [`rdrobust`](./rdrobust.md) | RD | Alpha — Partial | Sharp RD minimal subset; explicit bandwidth required |
| [`eventstudyinteract`](./eventstudyinteract.md) | DID / Event Study | Alpha | Sun-Abraham IW estimator, auto dummy generation, cluster |
| [`csdid`](./csdid.md) | DID / Event Study | Alpha | Callaway-Sant'Anna, `method="reg"` only, `estat_event` |

## Status Legend

- **Stable** — synthetic + real-data dual-run verified; core API unlikely to change in backward-incompatible ways.
- **Alpha** — high-frequency paths are implemented and verified, but command surface is still a subset of the full Stata community command. Unsupported parameters are hard-rejected.
- **Alpha — Partial** — a verifiable implementation exists and is tested, but large functional areas are still missing (e.g., automatic bandwidth selection, fuzzy RD, covariates). Explicit bandwidths or reduced parameter sets may be required.

## Common Limitations Across All Commands

- Multi-way clustering is supported on `regress` (two-way, Cameron-Gelbach-Miller 2011); other commands still use single cluster only.
- Post-estimation (`predict`, `margins`) is available on the core estimator layer only; the `compat.stata` wrapper layer returns `ResultSchema` and does not expose `.predict()` / `.margins()` directly.
- Weights beyond `aweight` are not yet supported.
- Any parameter not explicitly listed in a command matrix is hard-rejected via `ValueError`.

