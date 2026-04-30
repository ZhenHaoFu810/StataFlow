# Known Issues

This document registers issues that are acknowledged but not treated as release-blocking for the current open-source Beta (v0.3.0).

---

## 1. Vendor command completeness — all are partial subsets

All community commands in `stataflow.compat.stata` are implemented as **high-frequency-path subsets**, not full Stata command reproductions. This is by design for the Beta phase, but users may misinterpret wrapper availability as full support.

| Command | Status | Largest remaining gap |
|---------|--------|----------------------|
| `reghdfe` | Beta | 3-way+ clustering, slope absorption (`var##c.slope`), mobility-group DoF adjustments, `group`/`individual` FE |
| `ivreghdfe` | Beta | CUE estimator, HAC standard误 (`dkraay`), `partial`/`fwl`, `orthog`/`endogtest`/`redundant` |
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

---

## 3. Infrastructure limitations

- **Three-way and higher multi-way clustering:** Not yet supported. Only 2-way cluster is implemented for `reghdfe`, `ivreghdfe`, and `ppmlhdfe`.
- **Weights beyond `aweight`:** `fweight`, `pweight`, `iweight` are not yet supported.
- **Post-estimation on wrappers:** The `compat.stata` wrapper layer returns `ResultSchema` and does not expose `.predict()` / `.margins()` directly. Use the core estimator layer for post-estimation.
- **CI/CD:** GitHub Actions pipeline is configured (`.github/workflows/ci.yml`) and runs on Python 3.10, 3.11, and 3.12. Golden dual-run tests (which require local Stata 17) are excluded from CI.

---

## 4. Documentation / usability

- **Source map / support matrix synchronization:** While current state is aligned, historical drift between code changes and documentation updates has occurred. The Codex review protocol now requires documentation alignment as a gating step.
- **Output formatting:** No unified `summary(style="stata")` formatter exists yet.

---

## Issue registration policy

- New issues discovered during development are added here before being promoted to the backlog or a dedicated task card.
- Issues marked as "known" in this file are explicitly **not** treated as release blockers for the Beta, but they inform the roadmap for subsequent phases.
