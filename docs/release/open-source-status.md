# Open-Source Status

**Current package version:** 1.1.0 (Stable)
**Release-candidate sync:** v1.2.0+ correctness hardening
**Last updated:** 2026-07-09

---

## What this project is

`stataflow` is a Python econometrics toolkit that reproduces Stata 17 estimation results with high precision. It provides:

- A **Stata-compatible command layer** (`stataflow.compat.stata`) for researchers migrating from Stata.
- A **native Python estimator layer** (`stataflow.estimators`) for advanced users who want direct control.
- **Field-level dual-run verification** against Stata 17 on synthetic and real public datasets.

The current public package version remains `1.1.0`. The July 2026 sync does not change the public version number; it prepares a release-candidate branch that hardens correctness evidence, documentation, golden-test collection, and public-export hygiene for the v1.2.0+ line.

---

## Status model

This release is **functionally solid and extensively tested**. The core estimation paths for all supported commands are verified against Stata 17.

- **Stable commands** are base Stata-compatible commands with mature public API surfaces.
- **Beta commands** are verified high-frequency subsets of community or advanced Stata commands. They cover common research paths but do not promise the full Stata option surface.
- Unsupported parameters are **hard-rejected** (`ValueError` or `NotImplementedError`) rather than silently ignored.

---

## Command completeness summary

| Category | Command | Status | Notes |
|----------|---------|--------|-------|
| Linear base | `regress` | Stable | OLS, robust, cluster, aweight, noconstant |
| Panel / FE | `xtreg, fe` | Stable | Within estimator, single FE, cluster |
| Panel / FE | `areg` | Stable | Single absorb var, OLS/cluster VCE |
| IV | `ivregress 2sls` | Stable | 2SLS, robust, cluster, first-stage diagnostics, weak-IV tests, Sargan overid test |
| Binary | `logit` | Stable | MLE, robust, cluster |
| Binary | `probit` | Stable | MLE, robust, cluster |
| Count | `poisson` | Stable | MLE, robust, cluster |
| HDFE | `reghdfe` | Beta | 1+ categorical FEs, singleton drop, 2-way cluster, `savefe`, `noconstant`, `keepsingletons`, prediction types, `estat_summarize` |
| IV / HDFE | `ivreghdfe` | Beta | IV + FEs, 2SLS/GMM2S/LIML/Fuller/k-class, 2-way cluster, `first`, `weakiv`, prediction types |
| Count / HDFE | `ppmlhdfe` | Beta | PPML + FEs, offset/exposure, 2-way cluster, `separation(fe)`, `eform`, common residuals, `estat_ic` |
| DID | `did_imputation` | Beta | BJS imputation, allhorizons, autosample, cluster, controls, pretrends, weights, heterogeneous effects, save outputs |
| DID | `eventstudyinteract` | Beta | Sun-Abraham IW estimator, auto dummy generation, cluster |
| DID | `csdid` | Beta | Callaway-Sant'Anna `method="reg"` and `method="dr"`, aggregation and event-study helpers |
| RD | `rdrobust` | Beta | Sharp/fuzzy RD, MSE/CER bandwidth selectors, covariates, weights, mass points, cluster/nncluster VCE, `rdplot` |

---

## July 2026 correctness-hardening sync

The v1.2.0+ release-candidate sync closed the internal remediation and modular revalidation queue:

- R0/R1/R2/R4 completed work organized into separate commits.
- R3 M03 HDFE findings closed, including omitted-VCE comparison handling in the audit helper.
- M02 FE, M05 GLM, M06 PPMLHDFE, and M10 factor/shared-infrastructure contract evidence closed.
- R8 residual revalidation completed for M03, M04, M05, M06, M07, and M08.
- M09 postestimation evidence closed with the verified contract that `FixedEffectsOLS.predict(type="residuals")` maps to Stata `predict, residuals` (`y - xb`).
- Golden/final-gate cleanup completed for active-row comparisons, unsupported weight markers, DID sample invariants, and golden collection guards.

---

## Verification

Recent local release-candidate checks on 2026-07-09:

| Gate | Result |
|------|--------|
| Public unit/integration tests | `405 passed, 76 warnings` |
| Internal modular audit suite | `95 passed, 19 warnings` |
| Golden collection guard | `839 tests collected` |
| Compile check | `python -m compileall -q src/stataflow tests/golden tests/audit_v1_3` passed |
| Example smoke tests | `demo_regress`, `demo_reghdfe`, `demo_ppmlhdfe`, `demo_ivregress_2sls` passed |
| Wheel build | `stataflow-1.1.0-py3-none-any.whl` built |
| Open-source export dry-run | 150 files selected, 0 orphan removals |

One full audit attempt hit a Stata 17 batch timeout on an `estat ic` logit check after 300 seconds. The same test then passed independently in 11.26 seconds, and the full audit suite passed on rerun. This is tracked as an external Stata batch flake, not as a Python/Stata contract failure.

Public validation evidence:

- [`research/results/validation/README.md`](../../research/results/validation/README.md)
- [`research/results/validation/evidence-summary.md`](../../research/results/validation/evidence-summary.md)
- [`research/results/validation/oos/oos_master_summary.md`](../../research/results/validation/oos/oos_master_summary.md)

---

## Common limitations

- Two-way clustering is supported on `regress`, `reghdfe`, `ivreghdfe`, and `ppmlhdfe`; three-way and higher multi-way clustering is not yet supported.
- `aweight` is the only supported Stata weight type. `fweight`, `pweight`, and `iweight` are not yet public API.
- The `compat.stata` wrapper layer returns `ResultSchema` objects and does not expose `.predict()` / `.margins()` directly. Use the core estimator layer for post-estimation.
- Golden dual-run tests require local Stata 17 and are excluded from public CI.
- Community command surfaces remain verified subsets, not complete reproductions of every Stata/community option.

---

## Roadmap

High-level priorities after this sync:

1. Publish and monitor the release-candidate PR.
2. Keep public docs, support matrices, and hard-rejected option behavior synchronized.
3. Decide whether the next public version should remain `1.1.0` with a maintenance tag or become `1.2.0`.
4. Only then resume feature expansion, prioritizing documented gaps such as 3-way+ clustering, deeper IV diagnostics, and remaining `ppmlhdfe` separation modes.

---

## Feedback and contributions

- Issues: [https://github.com/ZhenHaoFu810/StataFlow/issues](https://github.com/ZhenHaoFu810/StataFlow/issues)
- Pull requests should include tests or validation evidence when they change statistical behavior.
