# Changelog

## v1.2.0+ correctness-hardening release-candidate sync

**Date:** 2026-07-09
**Package version:** 1.1.0
**Scope:** Public-documentation refresh, release-candidate verification, golden/final-gate cleanup, and open-source sync preparation.

This sync does not change the package version or introduce breaking API changes. It prepares the public repository for a v1.2.0+ correctness-hardening PR after the internal modular revalidation queue was closed.

### Highlights

- Closed the R3 HDFE remediation queue, including M03 omitted-VCE audit-helper handling.
- Organized completed R0/R1/R2/R4 remediation work into reviewable commit units.
- Closed FE, GLM, PPMLHDFE, factor-variable, residual, DID, RD, IV, and postestimation revalidation evidence.
- Clarified the M09 postestimation contract: `FixedEffectsOLS.predict(type="residuals")` maps to Stata `predict, residuals` (`y - xb`).
- Cleaned golden/final-gate contracts for active-row comparisons, unsupported weight cases, DID sample invariants, and golden collection guards.
- Refreshed README and release docs for public sync.

### Verification

- Public tests: `405 passed, 76 warnings`.
- Internal audit suite: `95 passed, 19 warnings`.
- Golden collect-only guard: `839 tests collected`.
- Compile check passed for `src/stataflow`, `tests/golden`, and `tests/audit_v1_3`.
- Public examples passed: `demo_regress`, `demo_reghdfe`, `demo_ppmlhdfe`, `demo_ivregress_2sls`.
- Wheel build passed: `stataflow-1.1.0-py3-none-any.whl`.
- Open-source export dry-run selected 150 public files and reported 0 orphan removals.

One Stata 17 batch timeout was observed during a full internal audit attempt. The affected logit `estat ic` test passed independently in 11.26 seconds and the full audit suite passed on rerun, so this is treated as an external Stata batch flake rather than a contract failure.

---

# Open-Source Update Log: 1.1.0

**Date:** 2026-06-04  
**Scope:** Hotfix release closing the `docs/audit/revalidation-v1.1` audit remediation loop.  
**Baseline:** `fix/v1.0.1-hotfix`

---

## Summary

`1.1.0` is a focused correctness and documentation hotfix. It does not introduce breaking API changes. All 108 issues identified in the revalidation-v1.1 audit have been dispositioned:

| Category | Count | Meaning |
|----------|-------|---------|
| Code fixes completed | 96 | Implementation changed and verified with regression or golden dual-run tests |
| Known limitations | 4 | Closed as documented structural constraints (see ADR-0003, LINEAR-11, LINEAR-12, PANEL-11) |
| v1.2.0+ deferred | 8 | Display-layer parameters and advanced first-stage statistics scheduled for later |
| **Open items** | **0** | Audit loop closed |

---

## Notable User-Visible Improvements

### IV / GMM
- `ivregress_2sls` and `ivreghdfe` now report **first-stage diagnostics** (`first=True`), including R², partial R², Shea R², and F-statistics for each endogenous variable.
- **Weak-instrument diagnostics** are now attached to both `ivregress_2sls` and `ivreghdfe` results:
  - Kleibergen-Paap LM (`idstat`)
  - Cragg-Donald Wald F (`widstat`)
  - Stock-Yogo critical values (`widstat_cv`)
- **Overidentification tests**:
  - `ivregress_2sls` reports the Sargan statistic.
  - `ivreghdfe` GMM2S reports the Hansen J statistic.
- `first_stage` output format has been unified to a structured dict across `IV2SLS` and `IVAbsorbingOLS`.
- A `RuntimeWarning` is emitted when Stock-Yogo critical values are requested outside the supported 10×10 lookup table.

### Linear / Panel / HDFE
- `reghdfe` advanced `absorb` API now accepts tuples and lists in addition to space-separated strings, e.g.:
  - `[("firm_id", "time_trend")]`
  - `[("firm_id", ["x1", "x2"], False)]` (no intercept)
- 2-way cluster VCE now detects rank-deficiency in the moment matrix and emits a `RuntimeWarning` before applying a PSD fallback.
- `aweight` now accepts string names, NumPy arrays, or pandas Series.

### GLM / PPML
- `logit`, `probit`, and `poisson` wrappers now accept `eform`, `irr`, and `or_` aliases for exponentiated coefficients (odds ratios / incidence-rate ratios).
- Robust VCE for GLM models now includes the `n/(n-1)` small-sample correction, matching Stata.
- `ppmlhdfe` `eform` z-statistics and p-values are now computed on the raw scale before exponentiation, matching Stata output.

### DID / Event Study
- `did_imputation(..., allhorizons=True)` now correctly includes pre-treatment horizons (e.g. `tau1980`–`tau1988`).
- `csdid(..., method="reg", notyet=True)` is now supported.
- `csdid` pretrend and aggregation outputs have been unified to `ResultSchema` objects.
- Unbalanced panel `ATT(g,t)` NaN propagation has been fixed.

### RD
- `rdrobust` default bandwidth selection is now `bwselect="mserd"`.
- Cluster-aware bandwidth selection has been fixed for `vce="cluster"` and `vce="nncluster"`.

---

## Known Limitations (documented, not treated as open bugs)

1. **2-way cluster `_cons` SE in HDFE/PPML/IV-HDFE**  
   Under 2-way clustering, the constant-term standard error may deviate from Stata `reghdfe` by up to ~3% on synthetic data and ~16% on real data. Slope SEs remain aligned to `< 1e-6`. This is a structural difference between StataFlow's LSDV framework and Stata's iterative-demeaning framework. Governed by ADR-0003.

2. **Factor variable `#` in coefficient names**  
   Interaction terms such as `c.x1#c.x2` retain `#` in coefficient names. This matches Stata standard syntax.

3. **`xtreg_fe` `df_model` and `f_stat` dfn**  
   The degrees-of-freedom convention for `xtreg_fe` follows Stata's design choice and may differ from some textbook formulas.

4. **`df_a` simplified calculation**  
   `df_a` uses a simplified algorithm and does not implement pairwise mobility groups.

---

## Deferred to v1.2.0+

The following are scheduled for future releases and are **not** regressions:

- First-stage AP/SW F statistics (IV-10)
- Display-layer parameters: `level()`, `noci`, `nopvalues`, full `eform` display controls
- `ivreghdfe` CUE estimator
- Three-way and higher multi-way clustering
- Complete `ppmlhdfe` separation methods (`ir`, `simplex`, `mu`)

---

## Verification Status

- Non-golden tests: **392 passed, 0 failed** (synthetic / controlled cases; excludes internal `tests/audit_v1_3/`)
- Golden dual-run tests: **~606 passed** against Stata 17 (requires local Stata 17; real-data tests may skip when external datasets are unavailable)

No breaking API changes were introduced relative to v1.0.0.

---

## 中文摘要

**v1.1.0 是专注于正确性和文档同步的热修复版本，无破坏性 API 变更。**

- **IV**：`ivregress_2sls` / `ivreghdfe` 新增一阶段诊断、弱工具变量检验、过度识别检验；`first_stage` 输出格式统一。
- **HDFE**：`reghdfe` 支持 tuple/list 形式的高级 `absorb` API；双向聚类 VCE 增加秩亏检测与警告。
- **GLM/PPML**：`logit`/`probit`/`poisson` 支持 `eform`/`irr`/`or_` 别名；robust VCE 增加小样本修正；`ppmlhdfe` eform 的 z/p 口径与 Stata 一致。
- **DID**：`did_imputation` 的 `allhorizons` 生效；`csdid` 支持 `notyet=True`；不平衡面板 NaN 静默传播已修复。
- **RD**：`rdrobust` 默认 `bwselect="mserd"`；cluster VCE 带宽选择修复。

本轮审计发现的 108 项问题已全部收口：96 项修复完成，4 项列为已知局限（见上文），8 项排入 v1.2.0+ 规划，无开放项。
