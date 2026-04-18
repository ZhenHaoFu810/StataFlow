# Known Issues

This document registers issues that are acknowledged but not treated as release-blocking for the current open-source Alpha.

---

## 1. Historical `REPORT.md` stale fresh-run evidence

### 1.1 Package 004 (`ivreghdfe` Phase B)

- **Issue:** The `workspace/current-task/REPORT.md` from Package 004 contained stale fresh-run numbers (`5 passed` / `76 passed`) that did not match the actual test counts at the time of closure.
- **Status:** Fixed in the Package 004 rework cycle. The actual counts were `75 passed` (ivreghdfe专项) / `676 passed` (全量).
- **Current state:** The REPORT.md file was overwritten by subsequent task packages. The underlying code, tests, source maps, and support matrices for `ivreghdfe` are correct.
- **Why not release-blocking:** This was a documentation-only artifact issue. No algorithm or test regression existed.

### 1.2 Package 005 (DID community commands Phase B)

- **Issue:** The `workspace/current-task/REPORT.md` from Package 005 initially contained fresh-run numbers that needed alignment verification.
- **Status:** Verified and aligned. Actual counts: `35 passed` (DID专项) / `681 passed` (全量).
- **Current state:** Fresh-run evidence in REPORT.md matches real rerun.
- **Why not release-blocking:** Verification confirmed no test regression.

---

## 2. Vendor command completeness — all are partial subsets

All community commands in `statapy.compat.stata` are implemented as **high-frequency-path subsets**, not full Stata command reproductions. This is by design for the Alpha phase, but users may misinterpret wrapper availability as full support.

| Command | Status | Largest remaining gap |
|---------|--------|----------------------|
| `reghdfe` | Alpha / Partial | Slopes, mobility-group DoF, multi-way clustering, keepsingletons |
| `ivreghdfe` | Alpha / Partial | First-stage diagnostics, weak-instrument tests, LIML/GMM |
| `ppmlhdfe` | Alpha / Partial | Separation detection, multi-way clustering |
| `did_imputation` | Alpha / Partial | Controls, window, minn, pretrends, repeated cross-section |
| `eventstudyinteract` | Alpha / Partial | Covariates, window, minn, multi-way clustering |
| `csdid` | Alpha / Partial | DR/IPW methods, other aggregations, wild bootstrap |
| `rdrobust` | Alpha — Partial | Fuzzy RD, additional bandwidth selectors (`msetwo`, `cerrd`, etc.), clustering, weights |

See individual support matrices in `docs/command-support-matrix/` for the exact supported/planned/unsupported split.

---

## 3. Infrastructure limitations

- **Multi-way clustering:** Not supported across any command. Only single-cluster robust inference is available.
- **Weights beyond `aweight`:** `fweight`, `pweight`, `iweight` are not yet supported.
- **Post-estimation on wrappers:** `predict` and `margins` are available on core estimator classes only; the `compat.stata` wrapper layer returns `ResultSchema` and does not expose `.predict()` / `.margins()` directly.
- **CI/CD:** No automated continuous integration pipeline is configured.

---

## 4. Documentation / usability

- **Source map / support matrix synchronization:** While current state is aligned, historical drift between code changes and documentation updates has occurred. The Codex review protocol now requires documentation alignment as a gating step.
- **Output formatting:** No unified `summary(style="stata")` formatter exists yet.

---

## Issue registration policy

- New issues discovered during development are added here before being promoted to the backlog or a dedicated task card.
- Issues marked as "known" in this file are explicitly **not** treated as release blockers for the Alpha, but they inform the roadmap for subsequent phases.
