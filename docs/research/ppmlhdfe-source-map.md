# `ppmlhdfe` Source-to-Python Mapping

**Version mapped:** `2.3.4 11jan2025` (local mirror `research/vendor/stata_community/ppmlhdfe/ppmlhdfe-master/`)
**Python target:** `statapy.estimators.PPMLHDFE` + `statapy.compat.stata.ppmlhdfe()`

---

## 1. ADO Entry Points

| Stata File | Program / Line | What it does | Maps to Python |
|------------|----------------|--------------|----------------|
| `src/ppmlhdfe.ado` | `program ppmlhdfe, eclass` (L5) | Top-level dispatcher, dependency checks (`ftools >= 2.45.0`, `reghdfe >= 6.0.2`), replay handling | `statapy.compat.stata.ppmlhdfe()` wrapper |
| `src/ppmlhdfe.ado` | `program Estimate, eclass` (L107) | **Main estimation entry point.** Parses `absorb()`, `vce()`, `offset`/`exposure`, `separation`, builds sample, calls Mata `GLM` class | `PPMLHDFE.__init__()` + `fit()` orchestration |

---

## 2. Mata Object Hierarchy

```
ppmlhdfe.ado
    └── Mata: glm = GLM()
            ├── glm.validate_parameters()
            ├── glm.init_fixed_effects()   [creates HDFE = FixedEffects(); singleton drop]
            ├── glm.init_variables()       [load y, x, offset, weights; standardize]
            ├── glm.init_separation()      [simplex, relu, fe separation checks]
            └── glm.solve()                [IRLS loop + final VCE]
                    └── glm.inner_irls()   [core IRLS iterator]
```

All Mata code lives in `src/ppmlhdfe.mata`, `src/ppmlhdfe_functions.mata`, and the two separation submodules.

---

## 3. Core Algorithm → Python Mapping

### 3.1 Parameter Validation

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `ppmlhdfe.ado` | `L157` | `assert (exposure != "") + (offset != "") < 2` — mutually exclusive | `ppmlhdfe()` wrapper exposes `offset` and `exposure`; `PPMLHDFE.__init__()` raises `ValueError` if both are provided |
| `ppmlhdfe.ado` | `L174–179` | Parses `separation()` option; default is `"fe simplex relu"` | Python Phase A: separation detection is **not implemented**. Default behavior runs IRLS without separation checks. |
| `ppmlhdfe.mata` | `GLM::validate_parameters()` (L156–175) | Checks `tolerance`, `maxiter`, solver flags | `PPMLHDFE.__init__()` accepts `max_iter` and `tol` with defaults `100` and `1e-8`. |

### 3.2 Fixed Effects Setup and Singleton Drop

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `ppmlhdfe.mata` | `GLM::init_fixed_effects()` (L181–227) | Calls `fixed_effects(absorb, touse, ...)` which creates the same `FixedEffects` object used by `reghdfe`. Inherits singleton-drop logic. | `PPMLHDFE` delegates to `AbsorbingOLS._prepare_data()`, which reuses the identical iterative singleton-drop algorithm. |

### 3.3 Variable Loading and Standardization

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `ppmlhdfe.mata` | `GLM::init_variables()` (L233–294) | Loads `y`, `x`, `offset`, `true_w`; standardizes data with `reghdfe_standardize()`; removes collinear variables via `remove_collinears()` | `PPMLHDFE.fit()` uses `AbsorbingOLS._prepare_data()` for matrix construction. For numerical stability, `fit()` additionally standardizes `x` columns before IRLS and rescales coefficients afterwards (L284–304). |

### 3.4 Separation Detection

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `ppmlhdfe.mata` | `GLM::init_separation()` (L300–332) | Runs `simplex_fix_separation()` and/or `relu_fix_separation()` to detect and drop observations that cause complete separation | **Not implemented in Phase A.** Documented as unsupported boundary. If a dataset triggers separation, IRLS may fail to converge or produce extreme coefficients. |
| `ppmlhdfe_separation_simplex.mata` | `simplex_fix_separation()` | Linear-programming based separation detection (Correia-Guimarães-Zylkin 2020) | N/A |
| `ppmlhdfe_separation_relu.mata` | `relu_fix_separation()` | ReLU-based iterative separation detector | N/A |

**Phase A strategy:** Separation handling is explicitly listed as out-of-scope unless triggered by test data. The source map documents this gap.

### 3.5 IRLS (Iteratively Reweighted Least Squares)

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `ppmlhdfe.mata` | `GLM::inner_irls()` (called L395) | Core loop: <br>1. `η = Wγ` <br>2. `μ = exp(η)` <br>3. `z = η + (y - μ)/μ` <br>4. `w = μ` <br>5. Solve weighted HDFE regression for `γ_new` <br>6. Step-halving if log-likelihood does not increase <br>7. Converge when log-likelihood and parameter changes are below tolerance | `PPMLHDFE._irls_fit()` (L92–176) implements the identical loop on the dense LSDV matrix `X_full`: <br>1. `eta = X @ gamma` <br>2. `mu = exp(clip(eta))` <br>3. `z = eta + (y - mu)/mu` <br>4. `w = mu` <br>5. `gamma_step = solve(Xw'Xw, Xw'zw)` where `Xw = X * sqrt(w)` <br>6. Step-halving against log-likelihood <br>7. Converge on `rel_change < tol` and `param_change < tol` |

**Key equivalence:** `ppmlhdfe` calls `reghdfe` to solve the weighted regression at each IRLS step (partialling out FEs). Python solves the weighted regression on the full LSDV matrix `[constant, dummies, x]`, which is the same regression in a different basis.

### 3.6 Initial Values

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `ppmlhdfe.mata` | `GLM::solve()` (L377–389) | Default (`guess(simple)`): `μ = 0.5 * (y + mean(y, weights))`. Alternative: OLS of `log(1+y)` on `x` via `reghdfe`. | `PPMLHDFE._irls_fit()` uses OLS of `log(y+1)` on `X` as the starting guess (L116–120), which is the same as the `"ols"` guess path. |

### 3.7 Log-Likelihood, Deviance, and Pseudo R²

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `ppmlhdfe.mata` | `GLM::solve()` (L438–458) | Computes Poisson log-likelihood: `ll = Σ [y * log(μ) - μ - log(y!)]` using `lngamma(y+1)` for non-integer support. Also computes `ll_0` (constant-only model). | `PPMLHDFE.fit()` (L313) computes `ll = Σ [y * log(μ) - μ - gammaln(y+1)]` with SciPy’s `gammaln`. `ll_0` and deviance are **not yet computed** in Phase A. |

### 3.8 Constant Recovery (`_cons`)

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `ppmlhdfe.mata` | `GLM::solve()` (L461–470) | Sets `HDFE.compute_constant = 1`; `HDFE.means = mean(log(mu), weight), mean(x, weight)`; runs `reghdfe_solve_ols` which extends `b` and `V` to include `_cons`. The constant is recovered as the weighted mean of `log(mu)` minus the weighted means of `x` times their coefficients. | `PPMLHDFE._build_t_matrix()` (L178–208) constructs `T` where the `_cons` row equals the weighted mean of each column of `X_full` (weights = `μ`), minus the weighted means of the `x` columns from their own positions. This yields the identical reported constant. |

### 3.9 VCE Computation

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `ppmlhdfe.mata` | `reghdfe_solve_ols()` called with `"vce_asymptotic"` (L468) | `ppmlhdfe` forces `vcetype = "robust"` if unadjusted. Final regression uses `vce_asymptotic` mode (no `N/(N-1)` correction) inside `reghdfe_solve_ols`. | `PPMLHDFE._compute_vce()` implements three modes:<br>- `vce="ols"`: Fisher information `(X'WX)^{-1}`<br>- `vce="robust"`: sandwich with `N/(N-1)` small-sample correction<br>- `vce="cluster"`: cluster sandwich with **only** `G/(G-1)` adjustment (asymptotic mode, matching Stata `ppmlhdfe`) |

**Alignment note:** `ppmlhdfe` uses the asymptotic VCE path, so Python’s cluster VCE intentionally does **not** apply the `N/(N-1)` factor for `vce="cluster"`. The robust VCE, however, applies `N/(N-1)` because that matches the default Stata behavior for Poisson/GLM robust SEs.

### 3.10 Offset / Exposure

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `ppmlhdfe.ado` | `L234–243` | If `exposure(var)` is given, creates `offset = ln(var)` and adds it to `η` with coefficient fixed at 1. | `PPMLHDFE.__init__()` converts `exposure` to `log(exposure)` and stores it as `_offset_vec`; `_irls_fit()` adds it to `eta` each iteration; `_build_t_matrix()` subtracts its weighted mean from the reported constant |

---

## 4. `predict` Post-estimation Mapping

`ppmlhdfe` delegates `predict` to `ppmlhdfe_p` (which in turn delegates to `reghdfe_p` for `xb`/`stdp`).

| Stata Option | Source File | Meaning | Python Method |
|--------------|-------------|---------|---------------|
| `xb` | `ppmlhdfe_p.ado` (L52) | Linear predictor `η = Xβ + FE + offset` | `PPMLHDFE.predict(type="xb")` — returns stored `eta` |
| `mu` | `ppmlhdfe_p.ado` (L83) | Fitted mean `μ = exp(η)` | `PPMLHDFE.predict(type="mu")` — returns stored `mu` |
| `response` | `ppmlhdfe_p.ado` (L104) | Response residual `y - μ` | `PPMLHDFE.predict(type="residuals")` — returns `y - mu` |
| `pearson` | `ppmlhdfe_p.ado` (L111) | Pearson residual `(y - μ) / sqrt(μ)` | **Not implemented** |
| `deviance` | `ppmlhdfe_p.ado` (L97) | Deviance residual | **Not implemented** |

---

## 5. Options → Wrapper Parameter Matrix

| Stata Option | Wrapper Parameter | Python Behavior |
|--------------|-------------------|-----------------|
| `absorb(varlist)` | `absorb=str\|list[str]` | Supported: 1–2 categorical vars |
| `vce(robust)` | `vce="robust"` (default) | Supported |
| `vce(cluster var)` | `vce="cluster"`, `cluster="var"` | Supported |
| `vce(ols)` | `vce="ols"` | Supported |
| `offset(var)` / `exposure(var)` | `offset="var"` / `exposure="var"` | Supported |
| `maxiterations(integer)` | `maxiter: int = 100` | Wrapper-exposed; maps to `PPMLHDFE(max_iter=...)` |
| `tolerance(real)` | `tolerance: float = 1e-8` | Wrapper-exposed; maps to `PPMLHDFE(tol=...)` |
| `noconstant` | `noconstant: bool = False` | **Python-only extension.** Stata `ppmlhdfe` does not officially support `noconstant`; Python supports it via `AbsorbingOLS(add_constant=False)`. |
| `separation(...)` | *(not exposed)* | Separation detection not implemented; silently skipped |
| `guess(simple\|ols)` | *(not exposed)* | Python always uses OLS of `log(y+1)` as initial guess |

---

## 6. Known Phase A Simplifications

1. **No separation detection** — `simplex`, `relu`, `fe`, and `mu` separation checks are skipped. If data triggers separation, IRLS may diverge or fail to converge.
2. **LSDV instead of HDFE partialling-out** — mathematically equivalent for 1–2 categorical FEs.
3. **No multi-way clustering** — single cluster only.

---

## 7. Source File Quick Reference

```
research/vendor/stata_community/ppmlhdfe/ppmlhdfe-master/
├── src/ppmlhdfe.ado                  ← Main ADO entry (Estimate)
├── src/ppmlhdfe.mata                 ← GLM class, IRLS, solve()
├── src/ppmlhdfe_functions.mata       ← qrsolve helpers, trim_separated_obs
├── src/ppmlhdfe_separation_simplex.mata  ← Simplex separation detection
├── src/ppmlhdfe_separation_relu.mata     ← ReLU separation detection
├── src/ppmlhdfe_p.ado                ← predict post-estimation
└── examples/                           ← Usage examples
```

---

## 8. 已实现并有明确源码依据

- **参数校验**：`PPMLHDFE.__init__()` 校验 `offset`/`exposure` 互斥（对应 `ppmlhdfe.ado` L157）；`exposure > 0` 校验已加入。
- **固定效应与 singleton drop**：委托 `AbsorbingOLS._prepare_data()`，与 `GLM::init_fixed_effects()` 一致。
- **变量加载与标准化**：`fit()` 中 `AbsorbingOLS._prepare_data()` 构造矩阵，并在 IRLS 前对 `x` 标准化，对应 `GLM::init_variables()`。
- **IRLS 核心循环**：`PPMLHDFE._irls_fit()` 实现 `η → μ → z → w → solve → step-halving` 流程，与 `GLM::inner_irls()` 一致。
- **初始值**：默认使用 `log(y+1)` 对 `X` 的 OLS 作为初始猜测，对应 `GLM::solve()` 的 `"ols"` guess。
- **对数似然**：使用 SciPy `gammaln` 计算 `ll = Σ[y*log(μ) - μ - gammaln(y+1)]`，对应 Mata 的 `lngamma(y+1)`。
- **常数项恢复**：`_build_t_matrix()` 使用加权均值（权重 = μ）恢复 `_cons`，对应 `GLM::solve()` L461–470。
- **VCE**：`vce="ols"`（Fisher info）、`vce="robust"`（sandwich + `N/(N-1)`）、`vce="cluster"`（仅 `G/(G-1)` asymptotic 修正）均与 `ppmlhdfe` 源码对齐。
- **offset / exposure**：`__init__()` 暴露参数，`_irls_fit()` 每轮加入 `eta`，`_build_t_matrix()` 减去加权均值，与 `ppmlhdfe.ado` L234–243 及 Mata L469 一致。
- **predict**：`type="xb"`、`type="mu"`、`type="residuals"` 已实现，对应 `ppmlhdfe_p.ado`。
- **deviance / pseudo R²**：`fit()` 计算 `deviance = 2 * Σ[(μ - y) + y * log(y/μ)]` 和 `pseudo_r2 = 1 - ll / ll_0`，与 `ppmlhdfe.mata` L699–706 及 `ppmlhdfe.ado` L342–344 一致。

## 9. 已实现，但属于 Phase A 的等价实现

- **LSDV 替代 HDFE partialling-out**：Python 在 IRLS 每一步直接求解稠密 LSDV 矩阵，而非调用 `reghdfe` 的 MAP 吸收。对于 1–2 个纯分类 FE，两者数学等价。

## 10. 未实现或显式拒绝

- **separation 检测**：`simplex`、`relu`、`fe`、`mu` 四种检测均未实现；IRLS 在无 separation 检查的干净数据上收敛。
- **predict 子选项**：`pearson`、`deviance`、`anscombe`、`working` 等未实现。
- **multi-way clustering**：仅支持单 cluster。
- **wrapper 参数**：`guess` 控制未暴露。
- `separation`、`d`、`vceversion`、`individual`、`group`、`noreport`、`keepmata` 等参数硬拒绝。

## 11. Phase B 新增实现（本轮）

- **`noconstant`**：`ppmlhdfe()` wrapper 新增 `noconstant: bool = False`。注意：Stata 官方 `ppmlhdfe` 命令 syntax 中未列出 `noconstant`，因此该参数是 Python 端的扩展能力，由底层 `AbsorbingOLS(add_constant=...)` 直接支持。
- **`maxiter` / `tolerance`**：`ppmlhdfe()` wrapper 新增 `maxiter: int = 100` 和 `tolerance: float = 1e-8`，分别映射到 `PPMLHDFE(max_iter=..., tol=...)`，与 `ppmlhdfe.ado` L121–122 对应。
- **`predict(residuals)`**：`PPMLHDFE.predict(type="residuals")` 返回 `y - μ`，对应 `ppmlhdfe_p.ado` L104 `response` 语义。
- **`deviance` / `pseudo_r2`**：`fit()` 新增字段计算，对应 `ppmlhdfe.mata` L699–706（deviance）和 `ppmlhdfe.ado` L342–344（pseudo R²）。Golden dual-run 验证：`tests/golden/test_p3_ppmlhdfe_fit_stats.py`。

