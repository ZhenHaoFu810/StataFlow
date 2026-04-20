# Command Support Matrix

This directory lists the current support status for every Stata-compatible command exposed by `stataflow.compat.stata`.

Cross-command validation evidence is collected separately in:

- [`docs/validation/overview.md`](../validation/overview.md)
- [`docs/validation/evidence-matrix.md`](../validation/evidence-matrix.md)
- [`docs/validation/validation-policy.md`](../validation/validation-policy.md)

## Quick Reference

| Command | Family | Status | Key Features |
|---------|--------|--------|--------------|
| [`regress`](./regress.md) | Linear Base | Stable | OLS, robust, cluster, aweight, noconstant |
| [`xtreg, fe`](./xtreg-fe.md) | Panel / FE | Stable | Within estimator, single FE, cluster |
| [`areg`](./areg.md) | Panel / FE | Stable | Single absorb var, OLS/cluster VCE |
| [`reghdfe`](./reghdfe.md) | Panel / HDFE | Alpha | 1-2 categorical FEs, singleton drop, robust/cluster |
| [`ivregress 2sls`](./ivregress-2sls.md) | IV | Stable | 2SLS, robust, cluster |
| [`ivreghdfe`](./ivreghdfe.md) | IV / HDFE | Alpha | IV + 1-2 FEs, robust/cluster |
| [`logit`](./logit.md) | Binary | Stable | MLE, robust, cluster |
| [`probit`](./probit.md) | Binary | Stable | MLE, robust, cluster |
| [`poisson`](./poisson.md) | Count | Stable | MLE, robust, cluster |
| [`ppmlhdfe`](./ppmlhdfe.md) | Count / HDFE | Alpha | PPML + 1-2 FEs, offset/exposure, robust/cluster |
| [`did_imputation`](./did-imputation.md) | DID / Event Study | Alpha | BJS imputation, allhorizons, autosample, cluster |
| [`rdrobust`](./rdrobust.md) | RD | Alpha 鈥?Partial | Sharp RD minimal subset; explicit bandwidth required |
| [`eventstudyinteract`](./eventstudyinteract.md) | DID / Event Study | Alpha | Sun-Abraham IW estimator, auto dummy generation, cluster |
| [`csdid`](./csdid.md) | DID / Event Study | Alpha | Callaway-Sant'Anna, `method="reg"` only, `estat_event` |

## Status Legend

- **Stable** 鈥?synthetic + real-data dual-run verified; core API unlikely to change in backward-incompatible ways.
- **Alpha** 鈥?high-frequency paths are implemented and verified, but command surface is still a subset of the full Stata community command. Unsupported parameters are hard-rejected.
- **Alpha 鈥?Partial** 鈥?a verifiable implementation exists and is tested, but large functional areas are still missing (e.g., automatic bandwidth selection, fuzzy RD, covariates). Explicit bandwidths or reduced parameter sets may be required.

## Common Limitations Across All Commands

- Multi-way clustering is not yet supported (single cluster only).
- Post-estimation (`predict`, `margins`) is available on the core estimator layer only; the `compat.stata` wrapper layer returns `ResultSchema` and does not expose `.predict()` / `.margins()` directly.
- Weights beyond `aweight` are not yet supported.
- Any parameter not explicitly listed in a command matrix is hard-rejected via `ValueError`.

## Research Archives

For commands marked **Alpha**, detailed source-to-Python mapping documents are available in `docs/research/`:

- `reghdfe-source-map.md`
- `ivreghdfe-source-map.md`
- `ppmlhdfe-source-map.md`
- `did_imputation-source-map.md`
- `eventstudyinteract-source-map.md`
- `rdrobust-source-map.md`
