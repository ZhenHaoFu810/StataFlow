# Known Issues

This document registers issues that are acknowledged but not treated as release-blocking for the current Stable release (v1.1.0).

## v1.1.0 update

The `revalidation-v1.1` audit remediation (2026-06-04) closed all 108 identified issues:

- **96** were fixed in code and verified.
- **4** were promoted to documented known limitations (see below and [ADR-0003](../adr/ADR-0003-lsdv-cons-se-under-multiway-cluster.md)).
- **8** were deferred to v1.2.0+ (display-layer parameters and advanced first-stage statistics).

See [`open-source-update-log-1.1.0.md`](./open-source-update-log-1.1.0.md) for the full user-facing change list.

---

## 1. Vendor command completeness — all are partial subsets

All community commands in `stataflow.compat.stata` are implemented as **high-frequency-path subsets**, not full Stata command reproductions. This is by design for the Beta phase, but users may misinterpret wrapper availability as full support.

| Command | Status | Largest remaining gap |
|---------|--------|----------------------|
| `reghdfe` | Beta | 3-way+ clustering, mobility-group DoF adjustments, `group`/`individual` FE |
| `ivreghdfe` | Beta | CUE estimator, HAC standard errors (`dkraay`), `partial`/`fwl`, `orthog`/`endogtest`/`redundant` |
| `ppmlhdfe` | Beta | Full `separation` methods (`ir`, `simplex`, `mu`), 3-way+ clustering, `keepsingletons` |
| `did_imputation` | Beta | `window`, `minn`, `hbalance`, `leaveout`, `avgeffectsby` |
| `eventstudyinteract` | Beta | `covariates`, `window`, `minn`, complete matrix returns (`e(b_interact)`, etc.) |
| `csdid` | Beta | `method="ipw"`, `gtcontrol`, `longdiff` |
| `rdrobust` | Beta | `deriv > 0` (Kink RD), `rdplot` bin-selection algorithm alignment (2-3x difference vs Stata) |

See individual support matrices in `docs/command-support-matrix/` for the exact supported/planned/unsupported split.

---

## 2. Structural alignment residuals

The following are known mathematical/algorithmic gaps where Python and Stata results differ within documented tolerances. These are **not fixable without architectural changes** and are governed by ADRs:

| Area | Residual | Tolerance | ADR / Explanation |
|------|----------|-----------|-------------------|
| `reghdfe` / `ivreghdfe` _cons SE under 2-way cluster | ~2-16% | Documented | ADR-0003: LSDV vs iterative demeaning structural difference |
| `ivreghdfe` cluster `stdp` when cluster nests all FEs | ~0.28% | `rtol=5e-3` | Known VCE small-sample factor difference |
| `ppmlhdfe` residuals (pearson/deviance/working) | ~0.35% | `rtol=5e-3` | IRLS/HDFE convergence precision difference |
| `reghdfe` MAP cluster slope SE when cluster nests FE (1-way) | ~0.5% | `rtol=5e-3` | MAP builds cluster meat on partialled-out data; LSDV builds on full design matrix. Constant SE and OLS/robust VCEs are exact. |

---

## 3. Infrastructure limitations

- **Three-way and higher multi-way clustering:** Not yet supported. Only 2-way cluster is implemented for `reghdfe`, `ivreghdfe`, and `ppmlhdfe`.
- **Weights beyond `aweight`:** `fweight`, `pweight`, `iweight` are not yet supported.
- **Post-estimation on wrappers:** The `compat.stata` wrapper layer returns `ResultSchema` and does not expose `.predict()` / `.margins()` directly. Use the core estimator layer for post-estimation.
- **CI/CD:** GitHub Actions pipeline is configured (`.github/workflows/ci.yml`) and runs on Python 3.10, 3.11, and 3.12. Golden dual-run tests (which require local Stata 17) are excluded from CI.

## 4. Runtime warnings and intentional fallbacks

- **2-way cluster rank-deficiency detection:** When the Cameron-Gelbach-Miller meat matrix is not positive semi-definite (for example, when one cluster dimension is small or nested within fixed effects), `reghdfe`, `ivreghdfe`, and `ppmlhdfe` emit a `RuntimeWarning` and apply a PSD-fix fallback. This is intentional behavior and matches the documented fallback path; standard errors in these cases may differ slightly from Stata's internal fallback. Slope SEs in non-rank-deficient cases remain aligned to `< 1e-6`.

---

## 4. Documentation / usability

- **Source map / support matrix synchronization:** While current state is aligned, historical drift between code changes and documentation updates has occurred. The Codex review protocol now requires documentation alignment as a gating step.
- **Output formatting:** No unified `summary(style="stata")` formatter exists yet.

---

## Issue registration policy

- New issues discovered during development are added here before being promoted to the backlog or a dedicated task card.
- Issues marked as "known" in this file are explicitly **not** treated as release blockers for the Beta, but they inform the roadmap for subsequent phases.
