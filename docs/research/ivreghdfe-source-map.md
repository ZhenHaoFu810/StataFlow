# `ivreghdfe` Source-to-Python Mapping

**Version mapped:** `1.1.4 29nov2025` (local mirror `research/vendor/stata_community/ivreghdfe/ivreghdfe-master/`)
**Python target:** `statapy.estimators.IVAbsorbingOLS` + `statapy.compat.stata.ivreghdfe()`

---

## 1. ADO Entry Points

| Stata File | Program / Line | What it does | Maps to Python |
|------------|----------------|--------------|----------------|
| `src/ivreghdfe.ado` | `program ivreghdfe` (L43) | Parent dispatcher, dependency checks (`ftools >= 2.49.1`, `reghdfe >= 6.12.5`), replay handling | `statapy.compat.stata.ivreghdfe()` wrapper |
| `src/ivreghdfe.ado` | `program ivreg211` (L159) | **Main estimation entry point.** Parses IV syntax, `absorb()`, `vce()`, `cluster()`, constructs `reghdfe_options` | `IVAbsorbingOLS.__init__()` + `fit()` orchestration |

---

## 2. Core Architectural Insight

`ivreghdfe` is **not** a standalone IV solver. It is a thin glue layer:

1. Parses `absorb(varlist)`
2. Calls `reghdfe` to create a `FixedEffects` (HDFE) object
3. Uses `reghdfe` to **partial out** (residualize) **every variable**: `y`, `X_endog`, `X_exog`, `Z_instruments`
4. Runs `ivreg2`’s 2SLS machinery on the residualized variables
5. Adjusts reported DoF (`df_a`, nested cluster corrections) to account for absorbed FEs

**Mathematical equivalence:**
- Let `M_FE = I - D(D'D)^{-1}D'` be the partialling-out operator (same as `reghdfe`’s MAP).
- `ivreghdfe` computes `β = [X' M_FE Z (Z' M_FE Z)^{-1} Z' M_FE X]^{-1} X' M_FE Z (Z' M_FE Z)^{-1} Z' M_FE y`.
- This is **exactly** the 2SLS estimator on the full LSDV design matrix `W = [D, X, Z]`.

Python `IVAbsorbingOLS` therefore implements this by building the unified LSDV matrix and running 2SLS directly on it, which is mathematically identical.

---

## 3. Detailed Step Mapping

### 3.1 Syntax Parsing and absorb() Handling

| Source | Lines | Logic | Python Equivalent |
|--------|-------|-------|-------------------|
| `ivreghdfe.ado` | `L258–272` | If `absorb()` is present, sets `small`, `noconstant`, `nopartialsmall`, and builds `reghdfe_options` string | Wrapper exposes `noconstant: bool` (default `False`); `IVAbsorbingOLS.__init__()` receives `add_constant=not noconstant`. The `small` option is implicit in our finite-sample VCE formulas. |

### 3.2 Variable Residualization (Partialling Out)

| Source | Lines | Logic | Python Equivalent |
|--------|-------|-------|-------------------|
| `ivreghdfe.ado` | Internal call to `reghdfe, nopartialout varlist_is_touse` | Creates `FixedEffects` object and residualizes all IV variables | `IVAbsorbingOLS._prepare_data()` builds a **single** LSDV matrix containing `[constant, dummies, x_exog, x_endog, instruments]`. The first-stage and second-stage OLS regressions automatically project out the FE dummies because they are explicit columns in the matrix. |

**Why this is equivalent:**
- `reghdfe` residualizes each variable separately and then runs 2SLS on the residuals.
- LSDV includes the dummies as regressors, so the 2SLS first stage `Z → X_endog` already conditions on the same FE space.
- Both yield the identical `β` vector for the non-FE coefficients.

### 3.3 Collinearity and Identification

| Source | Lines | Logic | Python Equivalent |
|--------|-------|-------|-------------------|
| `ivreghdfe.ado` | `ivparse` + `ivreg2` Mata libs | Drops collinear instruments / regressors; checks underidentification (`#Z >= #X`) | `IVAbsorbingOLS._detect_collinearity()` runs QR on the full LSDV matrix, dropping `x` or `z` columns if they are collinear with `[constant, dummies]`. Post-QR, it checks `k_z_full >= k_x_full`. |

### 3.4 Two-Stage Least Squares

| Source | Lines | Logic | Python Equivalent |
|--------|-------|-------|-------------------|
| `ivreghdfe.ado` / `ivreg2` Mata | First stage: `Π = (Z_r'Z_r)^{-1} Z_r'X_r`; Second stage: `β = (X̂'X̂)^{-1} X̂'y_r` | Standard 2SLS on residualized data | `IVAbsorbingOLS.fit()` (L705–714): `Pi = solve(ZtZ, ZtX)`; `X_proj = Z @ Pi`; `beta_full = solve(XtX_proj, Xty_proj)` |

### 3.5 Structural Residuals and R²

| Source | Lines | Logic | Python Equivalent |
|--------|-------|-------|-------------------|
| `ivreghdfe.ado` / `ivreg2` | Uses **structural residuals** `e = y - Xβ` (not `y - X̂β`) for RSS, RMSE, and VCE | `IVAbsorbingOLS.fit()` (L717–718) computes `residuals = y - X_full @ beta_full` |
| `ivreghdfe.ado` | R² is based on `y` after partialling out FEs (`y_resid`) vs structural residuals | `IVAbsorbingOLS.fit()` (L728–748) computes `y_resid = y - Wγ` where `W = [constant, dummies]`, then `r2 = 1 - rss_struct / tss_resid` |

### 3.6 VCE and Cluster-Robust Standard Errors

| Source | Lines | Logic | Python Equivalent |
|--------|-------|-------|-------------------|
| `ivreghdfe.ado` | `vce(ols)` | Conventional 2SLS VCE: `σ² (X̂'X̂)^{-1}` with `σ² = RSS / df_r` | `IVAbsorbingOLS.fit(vce="ols")` (L769–771) |
| `ivreghdfe.ado` | `vce(robust)` | HC1 sandwich on `X_proj`: `(X̂'X̂)^{-1} X̂' diag(e²) X̂ (X̂'X̂)^{-1}` | `IVAbsorbingOLS.fit(vce="robust")` (L772–775): `XtOmegaX = (X_proj * e_sq[:, np.newaxis]).T @ X_proj`; `cov_full = M_inv @ XtOmegaX @ M_inv` |
| `ivreghdfe.ado` | `vce(cluster var)` | Cluster-robust sandwich on `X_proj` with small-sample correction using `k_eff = k_x_reported + df_a` | `IVAbsorbingOLS.fit(vce="cluster")` (L776–789) computes meat by cluster, then `n_adj * g_adj` with `k_eff = k_x_reported + df_a` |

**Important alignment detail:** `ivreghdfe` applies the small-sample DoF correction based on the **reported** number of slope parameters plus the absorbed FE parameters (`df_a`), not the full LSDV parameter count. This is reproduced in Python.

### 3.7 Degrees of Freedom (`df_a`)

| Source | Lines | Logic | Python Equivalent |
|--------|-------|-------|-------------------|
| `ivreghdfe.ado` | Inherits from `reghdfe` | `df_a` computed by `FixedEffects::estimate_dof()` | `IVAbsorbingOLS._prepare_data()` reuses the same Phase A formulas as `AbsorbingOLS`:
- 1 FE: `df_a = G`
- 2 FEs: `df_a = G1 + G2 - 1`
- cluster nested in FE: that FE contributes `0` |

### 3.8 Reported Coefficients and `_cons`

| Source | Lines | Logic | Python Equivalent |
|--------|-------|-------|-------------------|
| `ivreghdfe.ado` | `ivreg2` output + `reghdfe` constant recovery | Reports only `X_endog` and `X_exog` coefficients. The constant is partialled out by the FE structure and **not reported** (unlike `reghdfe`, which recovers `_cons` as the unweighted mean of FE intercepts). | `IVAbsorbingOLS.fit()` builds `T` matrix that maps full LSDV `beta_full` to reported space. Only `x_endog` and `x_exog` coefficients are reported; `_cons` is intentionally omitted (`_coef_names = kept_x_endog_names + kept_x_exog_names`). The legacy `_cons` recovery logic in the `T` matrix is retained for structural compatibility but is never active because `_cons` ∉ `_coef_names`. |

**Note:** `ivreghdfe` wrapper in Python previously had a bug where single `absorb` was treated as `areg` (command label). This has been fixed: `ivreghdfe()` wrapper now always passes `absorb` as a list, and the command label is always `"ivreghdfe"`.

---

## 4. `predict` Post-estimation Mapping

`ivreghdfe` delegates `predict` to `reghdfe_p` when `e(N_hdfe) != .` (i.e. when `absorb()` was used). The supported options are identical to `reghdfe`:

| Stata Option | Meaning | Python Status |
|--------------|---------|---------------|
| `xb` | Linear prediction (reported coefficients only) | `IVAbsorbingOLS.predict(type="xb")` — returns `X_reported @ beta_reported` |
| `xbd` | Linear prediction including FEs | `IVAbsorbingOLS.predict(type="xbd")` — returns `X_full @ beta_full` |
| `residuals` | `y - xbd` | `IVAbsorbingOLS.predict(type="residuals")` |
| `d` | Sum of FEs (`xbd - xb`) | `IVAbsorbingOLS.predict(type="d")` |
| `dresiduals` | `y - xb` | `IVAbsorbingOLS.predict(type="dresiduals")` |

---

## 5. Wrapper Parameter Matrix

| Stata Option | Wrapper Parameter | Python Behavior |
|--------------|-------------------|-----------------|
| `absorb(varlist)` | `absorb=str\|list[str]` | Supported: 1–2 categorical vars |
| `vce(ols)` | `vce="ols"` | Supported |
| `vce(cluster var)` | `vce="cluster"`, `cluster="var"` | Supported |
| `vce(robust)` | `vce="robust"` | Supported |
| `noconstant` | `noconstant: bool` | Supported (Phase B): passed through to `IVAbsorbingOLS(add_constant=not noconstant)` |
| `keepsingletons` | `keepsingletons: bool` | Supported (Phase B): passed through as `drop_singletons=not keepsingletons` |
| `first` / `ffirst` | *(not exposed)* | Hard-rejected via `**kwargs` |

---

## 6. Known Phase A Simplifications

1. **No LIML / GMM / CUE** — only 2SLS.
2. **No `first` stage diagnostics** — wrapper rejects `first=True` etc. Phase B did not tackle this (requires sub-regression result objects).
3. **No multi-way clustering** — single cluster only.
4. **LSDV instead of explicit residualization** — mathematically equivalent for 1–2 categorical FEs.

---

## 7. Source File Quick Reference

```
research/vendor/stata_community/ivreghdfe/ivreghdfe-master/
├── src/ivreghdfe.ado          ← Parent dispatcher
├── src/ivreghdfe.sthlp        ← Help file (useful for option semantics)
├── example.do                 ← Usage examples
└── test.do                    ← Basic verification do-file
```

`ivreghdfe` calls into:
- `reghdfe` Mata libraries (`FixedEffects`, `partial_out`, `estimate_dof`)
- `ivreg2` Mata libraries (2SLS solver, VCE computation)

---

## 8. 已实现并有明确源码依据

- **absorb() 解析与 reghdfe_options 构造**：`IVAbsorbingOLS.__init__()` 对应 `ivreghdfe.ado` L258–272。
- **变量残差化（partialling out）**：统一 LSDV 矩阵 `[constant, dummies, x_exog, x_endog, instruments]` 自动投影出 FE，与 `reghdfe` 残差化 + `ivreg2` 2SLS 严格等价。
- **共线性与识别检验**：`IVAbsorbingOLS._detect_collinearity()` 运行 QR 检测并校验 `#Z >= #X`。
- **2SLS**：第一阶段 `Pi = solve(ZtZ, ZtX)`、第二阶段 `beta_full = solve(XtX_proj, Xty_proj)` 对应 `ivreg2` Mata 实现。
- **结构性残差**：使用 `y - Xβ` 计算 RSS、RMSE、VCE，与 `ivreghdfe.ado` / `ivreg2` 一致。
- **VCE**：`vce="ols"`、`vce="robust"`、`vce="cluster"` 均已实现；cluster 小样本修正使用 `k_eff = k_x_reported + df_a`，与源码惯例一致。
- **自由度 `df_a`**：复用 `AbsorbingOLS` 的 Phase A 公式。
- **命令语义修正**：`ivreghdfe()` wrapper 始终报告 `command="ivreghdfe"`。
- **predict**：`type="xb"`、`"xbd"`、`"residuals"`、`"d"`、`"dresiduals"` 均已实现 (Phase B)。

## 9. 已实现，但属于 Phase A 的等价实现

- **LSDV 替代显式 residualization**：Python 将 FE dummies 作为显式回归元放入 2SLS，而非先对每变量单独调用 `reghdfe` 残差化。数学上完全等价。

## 10. 未实现或显式拒绝

- **LIML / GMM / CUE**：仅支持 2SLS。
- **first / ffirst 一阶段诊断**：wrapper 通过 `**kwargs` 硬拒绝。Phase B 未触及（需要返回完整的子回归结果对象，与当前 `ResultSchema` 结构差异较大）。
- **multi-way clustering**：仅支持单 cluster。

