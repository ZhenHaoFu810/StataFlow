# Open-Source Alpha Status

**Version:** Alpha
**Last updated:** 2026-04-18

---

## What this project is

`stataflow` is a Python econometrics toolkit that reproduces Stata 17 estimation results with high precision. It provides:

- A **Stata-compatible command layer** (`stataflow.compat.stata`) for researchers migrating from Stata.
- A **native Python estimator layer** (`stataflow.estimators`) for advanced users who want direct control.
- **Field-level dual-run verification** against Stata 17 on both synthetic and real public datasets.

---

## What "Alpha" means

This release is **functionally solid and extensively tested**, but it is **not a complete reproduction of every Stata community command**. 

Specifically:

- **Base commands** (`regress`, `xtreg, fe`, `areg`, `ivregress 2sls`, `logit`, `probit`, `poisson`) are stable and verified.
- **Community commands** (`reghdfe`, `ivreghdfe`, `ppmlhdfe`, `did_imputation`, `eventstudyinteract`, `csdid`, `rdrobust`) are implemented as **verified high-frequency subsets**. They cover the most common usage paths but do not yet reproduce the full parameter surface, post-estimation ecosystem, or advanced options of the original Stata commands.
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
| HDFE | `reghdfe` | Alpha | 1鈥? categorical FEs, singleton drop, robust/cluster |
| IV / HDFE | `ivreghdfe` | Alpha | IV + 1鈥? FEs, robust/cluster |
| Count / HDFE | `ppmlhdfe` | Alpha | PPML + 1鈥? FEs, offset/exposure, robust/cluster |
| DID | `did_imputation` | Alpha | BJS imputation, allhorizons, autosample, cluster |
| DID | `eventstudyinteract` | Alpha | Sun-Abraham IW estimator, auto dummy generation, cluster |
| DID | `csdid` | Alpha | Callaway-Sant'Anna `method="reg"` only, `estat_event` |
| RD | `rdrobust` | Alpha 鈥?Partial | Sharp RD with `bwselect="mserd"` and `covs`; fuzzy RD, clustering, and other selectors not yet supported |

**Legend:**
- **Stable** 鈥?synthetic + real-data dual-run verified; core API unlikely to change in backward-incompatible ways.
- **Alpha** 鈥?high-frequency paths implemented and verified, but command surface is a subset of the full Stata community command.
- **Alpha 鈥?Partial** 鈥?verifiable implementation exists, but large functional areas are still missing.

---

## Common limitations across all commands

- **Single-cluster robust inference only.** Multi-way clustering is not yet supported.
- **`aweight` only.** `fweight`, `pweight`, `iweight` are not yet supported.
- **Post-estimation on wrappers.** `predict` and `margins` are available on core estimator classes only. The `compat.stata` wrapper layer returns `ResultSchema` objects and does not expose `.predict()` / `.margins()` directly.
- **No CI/CD pipeline** is configured yet.

---

## Verification

Every public command is validated with two lines of evidence:

1. **Synthetic / controlled cases** 鈥?formula, degrees of freedom, sample screening, edge cases.
2. **Real public datasets** 鈥?field-level comparison against Stata 17 on openly available data.

Current test status: **681 passed, 0 failed** (as of 2026-04-18).

Out-of-sample validation status (Validation Package 001): **16 passed, 1 blocked** (as of 2026-04-20).

Public validation evidence:

- [`docs/validation/overview.md`](../validation/overview.md)
- [`docs/validation/evidence-matrix.md`](../validation/evidence-matrix.md)
- [`research/results/validation/oos/oos_master_summary.md`](../research/results/validation/oos/oos_master_summary.md)

---

## Roadmap

See [`docs/audit/next-development-plan.md`](../audit/next-development-plan.md) for the detailed development plan. High-level priorities:

1. Deepen vendor command completeness (HDFE series first, then DID, then RD).
2. Expand `rdrobust` bandwidth selectors beyond `mserd` (`msetwo`, `cerrd`, etc.).
3. Add separation detection for `ppmlhdfe`.
4. Expand post-estimation exposure on the wrapper layer.
5. Add multi-way clustering and additional weight types.

---

## Feedback and contributions

- Issues: [https://github.com/ZhenHaoFu810/StataFlow/issues](https://github.com/ZhenHaoFu810/StataFlow/issues)
- The project uses a dual-governance model: **Codex** (architecture and review) and **Claude Code** (implementation and testing).
