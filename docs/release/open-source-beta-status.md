# Open-Source Stable Status

**Version:** 1.0.0 (Stable)
**Last updated:** 2026-04-30

---

## What this project is

`stataflow` is a Python econometrics toolkit that reproduces Stata 17 estimation results with high precision. It provides:

- A **Stata-compatible command layer** (`stataflow.compat.stata`) for researchers migrating from Stata.
- A **native Python estimator layer** (`stataflow.estimators`) for advanced users who want direct control.
- **Field-level dual-run verification** against Stata 17 on both synthetic and real public datasets.

---

## What "Beta" means

This release is **functionally solid and extensively tested**. The core estimation paths for all supported commands are verified against Stata 17.

Specifically:

- **Base commands** (`regress`, `xtreg, fe`, `areg`, `ivregress 2sls`, `logit`, `probit`, `poisson`) are stable and verified.
- **Community commands** (`reghdfe`, `ivreghdfe`, `ppmlhdfe`, `did_imputation`, `eventstudyinteract`, `csdid`, `rdrobust`) are implemented as **verified high-frequency subsets**. They cover the most common usage paths but do not yet reproduce the full parameter surface or advanced options of the original Stata commands.
- Unsupported parameters are **hard-rejected** (raise `ValueError` or `NotImplementedError`) rather than silently ignored.

---

## Command completeness summary

| Category | Command | Status | Notes |
|----------|---------|--------|-------|
| Linear base | `regress` | Stable | OLS, robust, cluster, aweight, noconstant |
| Panel / FE | `xtreg, fe` | Stable | Within estimator, single FE, cluster |
| Panel / FE | `areg` | Stable | Single absorb var, OLS/cluster VCE |
| IV | `ivregress 2sls` | Stable | 2SLS, robust, cluster |
| Binary | `logit` | Stable | MLE, robust, cluster |
| Binary | `probit` | Stable | MLE, robust, cluster |
| Count | `poisson` | Stable | MLE, robust, cluster |
| HDFE | `reghdfe` | Beta | 1+ categorical FEs, singleton drop, 2-way cluster, `savefe`, `noconstant`, `keepsingletons`, `predict` (xb/xbd/d/residuals/dresiduals/stdp), `estat_summarize` |
| IV / HDFE | `ivreghdfe` | Beta | IV + 1+ FEs, 2SLS/GMM2S/LIML/Fuller/k-class, 2-way cluster, `first`, `weakiv`, `predict` (xb/xbd/d/residuals/dresiduals/stdp) |
| Count / HDFE | `ppmlhdfe` | Beta | PPML + 1+ FEs, offset/exposure, 2-way cluster, `separation(fe)`, `eform`, `predict` (xb/mu/residuals/pearson/deviance/working), `estat_ic` |
| DID | `did_imputation` | Beta | BJS imputation, allhorizons, autosample, cluster, `controls`, `unitcontrols`, `timecontrols`, `pretrends`, `wtr`, `hetby`, `saveestimates`, `saveweights`, `sum` |
| DID | `eventstudyinteract` | Beta | Sun-Abraham IW estimator, auto dummy generation, cluster |
| DID | `csdid` | Beta | Callaway-Sant'Anna `method="reg"` and `method="dr"`, `aggtype` (simple/group/calendar/pretrend), `estat_event` |
| RD | `rdrobust` | Beta | Sharp RD, full bandwidth selector family (`mserd`/`msetwo`/`msesum`/`msecomb1/2`/`cerrd`/`certwo`/`cersum`/`cercomb1/2`), fuzzy RD, `covs`, `weights`, `masspoints`, cluster/nncluster VCE, `rdplot` |

**Legend:**
- **Stable** — synthetic + real-data dual-run verified; core API unlikely to change in backward-incompatible ways.
- **Beta** — high-frequency paths implemented and verified, but command surface is a subset of the full Stata community command.

---

## Common limitations across all commands

- **Two-way clustering** is supported on `regress`, `reghdfe`, `ivreghdfe`, and `ppmlhdfe`. Three-way and higher multi-way clustering is not yet supported.
- **`aweight` only.** `fweight`, `pweight`, `iweight` are not yet supported.
- **Post-estimation on wrappers.** The `compat.stata` wrapper layer returns `ResultSchema` objects and does not expose `.predict()` / `.margins()` directly. Use the core estimator layer for post-estimation.
- **CI/CD pipeline** is configured via GitHub Actions (`.github/workflows/ci.yml`) and runs on Python 3.10, 3.11, and 3.12.

---

## Verification

Every public command is validated with two lines of evidence:

1. **Synthetic / controlled cases** — formula, degrees of freedom, sample screening, edge cases.
2. **Real public datasets** — field-level comparison against Stata 17 on openly available data.

Current non-golden test status: **271 passed, 0 failed** (as of 2026-04-30).

Golden dual-run test status: **87+ passed, 0 failed** (requires local Stata 17).

Public validation evidence:

- [`docs/validation/overview.md`](../validation/overview.md)
- [`docs/validation/evidence-matrix.md`](../validation/evidence-matrix.md)
- [`research/results/validation/oos/oos_master_summary.md`](../research/results/validation/oos/oos_master_summary.md)

---

## Roadmap

High-level priorities for v1.0.0:

1. Iterative MAP/LSMR absorption kernel (performance for very high-dimensional FEs).
2. Individual slope absorption (`absorb(var##c.slope)`).
3. Advanced VCE: Driscoll-Kraay, three-way+ clustering.
4. Complete `separation` methods for `ppmlhdfe` (`ir`, `simplex`, `mu`).
5. CUE estimator for `ivreghdfe`.

---

## Feedback and contributions

- Issues: [https://github.com/ZhenHaoFu810/StataFlow/issues](https://github.com/ZhenHaoFu810/StataFlow/issues)
- The project uses a dual-governance model: **Codex** (architecture and review) and **Claude Code** (implementation and testing).
