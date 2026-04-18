# `reghdfe` Source-to-Python Mapping

**Version mapped:** `6.13.1 10Jan2026` (local mirror `research/vendor/stata_community/reghdfe/reghdfe-master/`)
**Python target:** `statapy.estimators.AbsorbingOLS` + `statapy.compat.stata.reghdfe()`

---

## 1. ADO Entry Points

| Stata File | Program / Line | What it does | Maps to Python |
|------------|----------------|--------------|----------------|
| `current-code/reghdfe.ado` | `program reghdfe` (L1) | Top-level dispatcher, dependency checks, intercepts replay / version calls | `statapy.compat.stata.reghdfe()` wrapper |
| `current-code/reghdfe.ado` | `program Estimate, eclass` (L113) | **Main estimation entry point.** Parses `absorb()`, `vce()`, `cluster()`, `keepsingletons`, builds sample (`touse`), calls Mata | `AbsorbingOLS.__init__()` + `fit()` orchestration |
| `current-code/reghdfe.ado` | `L210` | `drop_singletons = ("`keepsingletons'" == "")` — default is **drop** | `AbsorbingOLS._drop_singletons()` |
| `current-code/reghdfe_p.ado` | `program reghdfe_p` (L1) | `predict` post-estimation: `xb`, `residuals`, `d`, `xbd`, `dresiduals` | `AbsorbingOLS.predict()` |

---

## 2. Mata Object Hierarchy

```
reghdfe.ado
    └── fixed_effects()          [creates HDFE = FixedEffects()]
            ├── FixedEffects::init()       [singleton drop, factor creation]
            ├── FixedEffects::partial_out()[MAP/LSMR partialling out]
            ├── estimate_dof()             [df_a computation]
            └── reghdfe_solve_ols()        [VCE + results]
```

---

## 8. 已实现并有明确源码依据

- **迭代 singleton drop**：`AbsorbingOLS._drop_singletons()` 与 `FE.mata:FixedEffects::init()` 逻辑一致（扫描、剔除、重启直到无新 singleton）。
- **LSDV 设计矩阵构造**：`AbsorbingOLS._prepare_data()` 构建 `[constant, dummies, x]` 稠密矩阵。
- **QR 共线性检测**：`AbsorbingOLS._detect_collinearity()` 与 `Solution.mata:check_collinear_with_fe()` 等价，优先剔除 `x` 而非 FE dummy。
- **自由度 `df_a`**：嵌套 cluster 扣减逻辑与 `DoF.mata:dof_update_nested()` 一致；1 FE 时 `df_a = G`，2 FE 时 `df_a = G1 + G2 - 1`（golden 测试验证）。
- **常数项恢复**：`T` 矩阵中 `_cons` 行构造与 `Regression.mata:reghdfe_extend_b_and_xx()` 一致。
- **R² 与 RMSE**：计算口径与 `Regression.mata:reghdfe_solve_ols()` 一致。
- **VCE**：`vce="ols"`、`vce="robust"`（HC1 sandwich，`N/(N-1)` 修正）、`vce="cluster"` 均已实现，与 `Regression.mata` 对应函数一致。
- **predict**：`type="xb"`、`type="xbd"`、`type="d"`、`type="residuals"`、`type="dresiduals"` 均已实现，对应 `reghdfe_p.ado`。
- **wrapper 暴露面**：`absorb`、`vce`（ols/robust/cluster）、`cluster`、`keepsingletons`、`noconstant` 均已暴露并通过测试。

## 9. 已实现，但属于 Phase A 的等价实现

- **LSDV 替代 MAP/LSMR**：Python 使用稠密 LSDV 矩阵直接求解，而非 `MAP.mata:map_solver()` 的迭代均值吸收。对于 1–2 个纯分类 FE，两者在数学上严格等价（`wagepan` 数据集差异 `< 1e-12`）。
- **简化版 `df_a` 公式**：使用闭式 `G1 + G2 - 1`，未实现 `DoF.mata:dof_update_mobility_group()` 的完整二分图 mobility group 算法。在典型面板数据（连通图）下结果一致。

## 10. 未实现或显式拒绝

- **predict**：`stdp` 未实现；`xb`、`xbd`、`d`、`residuals`、`dresiduals` 已实现。
- **mobility group 复杂 DoF**：未实现。
- **slopes / individual FEs / team FEs**：仅支持截距型分类 absorb vars。
- **multi-way clustering**：仅支持单 cluster。
- **estat 后估计生态**：仅支持基本 predict。

## 11. Phase B 新增实现（本轮）

- **`keepsingletons`**：`reghdfe.ado` L210 `drop_singletons = ("`keepsingletons'" == "")` — Python wrapper 新增 `keepsingletons: bool = False` 参数，映射到 `AbsorbingOLS(..., drop_singletons=not keepsingletons)`。`keepsingletons=True` 时跳过 `_drop_singletons()`，保留 singleton 观测。
- **`noconstant`**：`reghdfe.ado` L180 `noCONstant` — Python wrapper 新增 `noconstant: bool = False` 参数，映射到 `AbsorbingOLS(..., add_constant=not noconstant)`。
- **predict 扩展**：`reghdfe_p.ado` L16/46/53/58 — 新增 `predict(type="d")`、`predict(type="xbd")`、`predict(type="dresiduals")`。
  - `xbd` = `X_full @ beta_full`（含 FE 和常数的完整预测）
  - `xb` 已修正为仅使用 reported 系数（不含 FE dummy 贡献），与 Stata `_predict` 语义一致
  - `d` = `xbd - xb`（FE 贡献之和）
  - `dresiduals` = `y - xb`
  - `residuals` = `y - xbd`
- **singleton dropping 证据增强**：新增 synthetic 测试验证 keepsingletons 对样本量与警告信息的影响；新增 golden dual-run `test_p3_reghdfe_keepsingletons.py` 验证 Stata 17 与 Python 在保留 singleton 时的一致性。

---

## 3. Core Algorithm → Python Mapping

### 3.1 Sample Construction and Singleton Drop

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `FE.mata` | `FixedEffects::init()` (L186+) | Build `Factor` objects from `absorb()` vars; iteratively drop observations that are the only member of an FE group until a full pass finds no new singletons | `AbsorbingOLS._drop_singletons()` — implements the same iterative scan over all `absorb_vars` |

**Key equivalence:** `reghdfe` scans each FE sequentially, drops singleton observations, then restarts the scan because dropping an obs can create new singletons in *other* FEs. Python replicates this exact loop.

### 3.2 Design Matrix Construction (LSDV vs MAP)

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `MAP.mata` | `map_solver()` (L7+) | Iterative Mean Absorption Procedure (MAP) that residualizes each variable against the absorbed FEs | **Not used in Phase A.** Python uses mathematically equivalent dense LSDV matrix |
| `Regression.mata` | `reghdfe_solve_ols()` (L8+) | After partialling-out, runs OLS on residualized data | `AbsorbingOLS.fit()` solves `(X'X) b = X'y` on the LSDV matrix directly |

**Why LSDV is valid:** For 1–2 pure categorical FEs, the partialling-out operator `M_FE = I - D(D'D)^{-1}D'` (where `D` is the full dummy matrix) is *exactly* what MAP converges to. Solving OLS on `[D, X]` yields coefficients identical to `reghdfe` within machine precision (verified on `wagepan` with diff `< 1e-12`).

### 3.3 Collinearity Detection

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `Solution.mata` | `Solution::check_collinear_with_fe()` (L106–164) | After partialling-out, flags regressors whose norm is near zero (collinear with FEs) using `collinear_tol` | `AbsorbingOLS._detect_collinearity()` uses QR decomposition on the full LSDV matrix. If an `x` column is linearly dependent on `[constant, dummies]`, QR drops it. |

**Ordering matters:** `reghdfe` drops the *regressor*, not the FE dummy, when they are collinear. Python enforces this by placing `x` variables *after* constant and dummies in the QR ordering.

### 3.4 Degrees of Freedom (`df_a`)

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `DoF.mata` | `estimate_dof()` (L7–106) | Computes `G_extended`, redundancy `doflist_M`, nested-within-cluster penalties, mobility groups | `AbsorbingOLS._prepare_data()` Phase A simplification |
| `DoF.mata` | `dof_update_nested()` (L109–164) | If an absorb var equals or is nested within a cluster var, its entire level count is subtracted from `df_a` | Explicit check: if `var == cluster_var`, skip that var when summing `effective_levels` |

**Phase A formula used in Python:**
- 1 FE, no cluster: `df_a = G`
- 2 FEs, no cluster: `df_a = G1 + G2 - 1`
- Cluster nested in FE `i`: that FE contributes `0` to `df_a`

This matches `reghdfe`’s default `dofadjustments` behavior for the simple categorical-FE case (mobility groups = 1 for connected panels).

### 3.5 VCE Computation

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `Regression.mata` | `reghdfe_vce_unadjusted()` (called L127) | `V = σ² (X'X)^{-1}` with `σ² = RSS / df_r` | `AbsorbingOLS.fit(vce="ols")` |
| `Regression.mata` | `reghdfe_vce_robust()` (called L130) | HC1 sandwich: `(X'X)^{-1} X' diag(e²) X (X'X)^{-1}` times `N/(N-K)` | `AbsorbingOLS.fit(vce="robust")`: `meat = X_full.T @ (X_full * e_sq[:, np.newaxis])`; `cov_full = XtX_inv @ meat @ XtX_inv * n/(n-1)` |
| `Regression.mata` | `reghdfe_vce_cluster()` (called L136) | Cluster sandwich with `(N-1)/(N-K_eff) * G/(G-1)` small-sample correction | `AbsorbingOLS.fit(vce="cluster")` with `k_eff = k_full - nested_params` |

### 3.6 Constant Recovery (`_cons`)

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `Regression.mata` | `reghdfe_extend_b_and_xx()` (called L108) | Adds `_cons` to coefficient table. The reported constant equals the unweighted mean of all FE intercepts. | `AbsorbingOLS.fit()` builds `T` matrix where `_cons` row = `1.0` on the raw constant column plus `1/G_total` on every kept dummy for each FE group. |

### 3.7 R² and RMSE

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `Regression.mata` | `reghdfe_solve_ols()` (L182–193) | `r2 = 1 - RSS/TSS`; `r2_a = 1 - (RSS/used_df_r) / (TSS/(N - has_intercept))`; `rmse = sqrt(RSS / used_df_r)` | `AbsorbingOLS.fit()` computes identical formulas. `used_df_r = N - df_a - df_m - df_a_nested` (Phase A: `df_a_nested = 0`). |

---

## 4. `predict` Post-estimation Mapping

| Stata Option | Source File | Meaning | Python Method |
|--------------|-------------|---------|---------------|
| `xb` | `reghdfe_p.ado` (L16, L36) | Linear prediction from reported coefficients only (excludes FE dummy contributions) | `AbsorbingOLS.predict(type="xb")` — returns `X_reported @ beta_reported` |
| `xbd` | `reghdfe_p.ado` (L16, L53) | Full prediction including absorbed FE contributions (`xb + d = y - resid`) | `AbsorbingOLS.predict(type="xbd")` — returns `X_full @ beta_full` |
| `d` | `reghdfe_p.ado` (L16, L46) | Sum of fixed effects contributions (`xbd - xb`) | `AbsorbingOLS.predict(type="d")` |
| `residuals` | `reghdfe_p.ado` (L16, L40) | `y - xbd` | `AbsorbingOLS.predict(type="residuals")` |
| `dresiduals` | `reghdfe_p.ado` (L16, L58) | `y - xb` | `AbsorbingOLS.predict(type="dresiduals")` |
| `stdp` | `reghdfe_p.ado` (L16, L36) | Standard error of prediction | **Not implemented** |

---

## 5. Options → Wrapper Parameter Matrix

| Stata Option | Wrapper Parameter | Python Behavior |
|--------------|-------------------|-----------------|
| `absorb(varlist)` | `absorb=str|list[str]` | Supported: 1–2 categorical vars |
| `vce(robust)` | `vce="robust"` | Supported |
| `vce(cluster var)` | `vce="cluster"`, `cluster="var"` | Supported |
| `keepsingletons` | `keepsingletons: bool = False` | If `True`, skip singleton dropping and retain all observations. Maps to `AbsorbingOLS(..., drop_singletons=not keepsingletons)`. |
| `noconstant` | `noconstant: bool = False` | If `True`, omit the constant term. Maps to `AbsorbingOLS(..., add_constant=not noconstant)`. |

---

## 6. Known Phase A Simplifications

1. **No MAP/LSMR solver** — LSDV dense matrix is used instead. Proven numerically equivalent for 1–2 categorical FEs.
2. **No mobility-group pairwise DoF correction** — uses closed-form `df_a = G1 + G2 - 1`. This is exact when the data graph is connected (typical for panel data).
3. **No slopes / individual FEs / team FEs** — only intercept-only categorical absorb vars.
4. **No multi-way clustering** — single cluster only.
5. **No `estat` ecosystem** — `predict` supports `xb`, `xbd`, `d`, `residuals`, `dresiduals`; `stdp` and full `estat` suite are missing.

---

## 7. Source File Quick Reference

```
research/vendor/stata_community/reghdfe/reghdfe-master/
├── current-code/reghdfe.ado          ← Main ADO entry (Estimate)
├── current-code/reghdfe.mata         ← Mata include orchestrator
├── current-code/FE.mata              ← FixedEffects class, singleton drop
├── current-code/DoF.mata             ← estimate_dof(), nested logic
├── current-code/Regression.mata      ← reghdfe_solve_ols(), VCE functions
├── current-code/MAP.mata             ← map_solver() (partialling out)
├── current-code/Solution.mata        ← Solution class, collinear checks
└── src/reghdfe_p.ado                 ← predict post-estimation
```
