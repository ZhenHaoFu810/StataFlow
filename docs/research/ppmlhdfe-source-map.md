# `ppmlhdfe` Source-to-Python Mapping

**Version mapped:** `2.3.4 11jan2025` (local mirror `research/vendor/stata_community/ppmlhdfe/ppmlhdfe-master/`)
**Python target:** `stataflow.estimators.PPMLHDFE` + `stataflow.compat.stata.ppmlhdfe()`

---

## 1. ADO Entry Points

| Stata File | Program / Line | What it does | Maps to Python |
|------------|----------------|--------------|----------------|
| `src/ppmlhdfe.ado` | `program ppmlhdfe, eclass` (L5) | Top-level dispatcher, dependency checks (`ftools >= 2.45.0`, `reghdfe >= 6.0.2`), replay handling | `stataflow.compat.stata.ppmlhdfe()` wrapper |
| `src/ppmlhdfe.ado` | `program Estimate, eclass` (L107) | **Main estimation entry point.** Parses `absorb()`, `vce()`, `offset`/`exposure`, `separation`, builds sample, calls Mata `GLM` class | `PPMLHDFE.__init__()` + `fit()` orchestration |

---

## 2. Mata Object Hierarchy

```
ppmlhdfe.ado
    鈹斺攢鈹€ Mata: glm = GLM()
            鈹溾攢鈹€ glm.validate_parameters()
            鈹溾攢鈹€ glm.init_fixed_effects()   [creates HDFE = FixedEffects(); singleton drop]
            鈹溾攢鈹€ glm.init_variables()       [load y, x, offset, weights; standardize]
            鈹溾攢鈹€ glm.init_separation()      [simplex, relu, fe separation checks]
            鈹斺攢鈹€ glm.solve()                [IRLS loop + final VCE]
                    鈹斺攢鈹€ glm.inner_irls()   [core IRLS iterator]
```

All Mata code lives in `src/ppmlhdfe.mata`, `src/ppmlhdfe_functions.mata`, and the two separation submodules.

---

## 3. Core Algorithm 鈫?Python Mapping

### 3.1 Parameter Validation

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `ppmlhdfe.ado` | `L157` | `assert (exposure != "") + (offset != "") < 2` 鈥?mutually exclusive | `ppmlhdfe()` wrapper exposes `offset` and `exposure`; `PPMLHDFE.__init__()` raises `ValueError` if both are provided |
| `ppmlhdfe.ado` | `L174鈥?79` | Parses `separation()` option; default is `"fe simplex relu"` | Python Phase A: separation detection is **not implemented**. Default behavior runs IRLS without separation checks. |
| `ppmlhdfe.mata` | `GLM::validate_parameters()` (L156鈥?75) | Checks `tolerance`, `maxiter`, solver flags | `PPMLHDFE.__init__()` accepts `max_iter` and `tol` with defaults `100` and `1e-8`. |

### 3.2 Fixed Effects Setup and Singleton Drop

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `ppmlhdfe.mata` | `GLM::init_fixed_effects()` (L181鈥?27) | Calls `fixed_effects(absorb, touse, ...)` which creates the same `FixedEffects` object used by `reghdfe`. Inherits singleton-drop logic. | `PPMLHDFE` delegates to `AbsorbingOLS._prepare_data()`, which reuses the identical iterative singleton-drop algorithm. |

### 3.3 Variable Loading and Standardization

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `ppmlhdfe.mata` | `GLM::init_variables()` (L233鈥?94) | Loads `y`, `x`, `offset`, `true_w`; standardizes data with `reghdfe_standardize()`; removes collinear variables via `remove_collinears()` | `PPMLHDFE.fit()` uses `AbsorbingOLS._prepare_data()` for matrix construction. For numerical stability, `fit()` additionally standardizes `x` columns before IRLS and rescales coefficients afterwards (L284鈥?04). |

### 3.4 Separation Detection

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `ppmlhdfe.mata` | `GLM::init_separation()` (L300鈥?32) | Runs `simplex_fix_separation()` and/or `relu_fix_separation()` to detect and drop observations that cause complete separation | **Not implemented in Phase A.** Documented as unsupported boundary. If a dataset triggers separation, IRLS may fail to converge or produce extreme coefficients. |
| `ppmlhdfe_separation_simplex.mata` | `simplex_fix_separation()` | Linear-programming based separation detection (Correia-Guimar茫es-Zylkin 2020) | N/A |
| `ppmlhdfe_separation_relu.mata` | `relu_fix_separation()` | ReLU-based iterative separation detector | N/A |

**Phase A strategy:** Separation handling is explicitly listed as out-of-scope unless triggered by test data. The source map documents this gap.

### 3.5 IRLS (Iteratively Reweighted Least Squares)

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `ppmlhdfe.mata` | `GLM::inner_irls()` (called L395) | Core loop: <br>1. `畏 = W纬` <br>2. `渭 = exp(畏)` <br>3. `z = 畏 + (y - 渭)/渭` <br>4. `w = 渭` <br>5. Solve weighted HDFE regression for `纬_new` <br>6. Step-halving if log-likelihood does not increase <br>7. Converge when log-likelihood and parameter changes are below tolerance | `PPMLHDFE._irls_fit()` (L92鈥?76) implements the identical loop on the dense LSDV matrix `X_full`: <br>1. `eta = X @ gamma` <br>2. `mu = exp(clip(eta))` <br>3. `z = eta + (y - mu)/mu` <br>4. `w = mu` <br>5. `gamma_step = solve(Xw'Xw, Xw'zw)` where `Xw = X * sqrt(w)` <br>6. Step-halving against log-likelihood <br>7. Converge on `rel_change < tol` and `param_change < tol` |

**Key equivalence:** `ppmlhdfe` calls `reghdfe` to solve the weighted regression at each IRLS step (partialling out FEs). Python solves the weighted regression on the full LSDV matrix `[constant, dummies, x]`, which is the same regression in a different basis.

### 3.6 Initial Values

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `ppmlhdfe.mata` | `GLM::solve()` (L377鈥?89) | Default (`guess(simple)`): `渭 = 0.5 * (y + mean(y, weights))`. Alternative: OLS of `log(1+y)` on `x` via `reghdfe`. | `PPMLHDFE._irls_fit()` uses OLS of `log(y+1)` on `X` as the starting guess (L116鈥?20), which is the same as the `"ols"` guess path. |

### 3.7 Log-Likelihood, Deviance, and Pseudo R虏

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `ppmlhdfe.mata` | `GLM::solve()` (L438鈥?58) | Computes Poisson log-likelihood: `ll = 危 [y * log(渭) - 渭 - log(y!)]` using `lngamma(y+1)` for non-integer support. Also computes `ll_0` (constant-only model). | `PPMLHDFE.fit()` (L313) computes `ll = 危 [y * log(渭) - 渭 - gammaln(y+1)]` with SciPy鈥檚 `gammaln`. `ll_0` and deviance are **not yet computed** in Phase A. |

### 3.8 Constant Recovery (`_cons`)

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `ppmlhdfe.mata` | `GLM::solve()` (L461鈥?70) | Sets `HDFE.compute_constant = 1`; `HDFE.means = mean(log(mu), weight), mean(x, weight)`; runs `reghdfe_solve_ols` which extends `b` and `V` to include `_cons`. The constant is recovered as the weighted mean of `log(mu)` minus the weighted means of `x` times their coefficients. | `PPMLHDFE._build_t_matrix()` (L178鈥?08) constructs `T` where the `_cons` row equals the weighted mean of each column of `X_full` (weights = `渭`), minus the weighted means of the `x` columns from their own positions. This yields the identical reported constant. |

### 3.9 VCE Computation

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `ppmlhdfe.mata` | `reghdfe_solve_ols()` called with `"vce_asymptotic"` (L468) | `ppmlhdfe` forces `vcetype = "robust"` if unadjusted. Final regression uses `vce_asymptotic` mode (no `N/(N-1)` correction) inside `reghdfe_solve_ols`. | `PPMLHDFE._compute_vce()` implements three modes:<br>- `vce="ols"`: Fisher information `(X'WX)^{-1}`<br>- `vce="robust"`: sandwich with `N/(N-1)` small-sample correction<br>- `vce="cluster"`: cluster sandwich with **only** `G/(G-1)` adjustment (asymptotic mode, matching Stata `ppmlhdfe`) |

**Alignment note:** `ppmlhdfe` uses the asymptotic VCE path, so Python鈥檚 cluster VCE intentionally does **not** apply the `N/(N-1)` factor for `vce="cluster"`. The robust VCE, however, applies `N/(N-1)` because that matches the default Stata behavior for Poisson/GLM robust SEs.

### 3.10 Offset / Exposure

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `ppmlhdfe.ado` | `L234鈥?43` | If `exposure(var)` is given, creates `offset = ln(var)` and adds it to `畏` with coefficient fixed at 1. | `PPMLHDFE.__init__()` converts `exposure` to `log(exposure)` and stores it as `_offset_vec`; `_irls_fit()` adds it to `eta` each iteration; `_build_t_matrix()` subtracts its weighted mean from the reported constant |

---

## 4. `predict` Post-estimation Mapping

`ppmlhdfe` delegates `predict` to `ppmlhdfe_p` (which in turn delegates to `reghdfe_p` for `xb`/`stdp`).

| Stata Option | Source File | Meaning | Python Method |
|--------------|-------------|---------|---------------|
| `xb` | `ppmlhdfe_p.ado` (L52) | Linear predictor `畏 = X尾 + FE + offset` | `PPMLHDFE.predict(type="xb")` 鈥?returns stored `eta` |
| `mu` | `ppmlhdfe_p.ado` (L83) | Fitted mean `渭 = exp(畏)` | `PPMLHDFE.predict(type="mu")` 鈥?returns stored `mu` |
| `response` | `ppmlhdfe_p.ado` (L104) | Response residual `y - 渭` | `PPMLHDFE.predict(type="residuals")` 鈥?returns `y - mu` |
| `pearson` | `ppmlhdfe_p.ado` (L111) | Pearson residual `(y - 渭) / sqrt(渭)` | **Not implemented** |
| `deviance` | `ppmlhdfe_p.ado` (L97) | Deviance residual | **Not implemented** |

---

## 5. Options 鈫?Wrapper Parameter Matrix

| Stata Option | Wrapper Parameter | Python Behavior |
|--------------|-------------------|-----------------|
| `absorb(varlist)` | `absorb=str\|list[str]` | Supported: 1鈥? categorical vars |
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

1. **No separation detection** 鈥?`simplex`, `relu`, `fe`, and `mu` separation checks are skipped. If data triggers separation, IRLS may diverge or fail to converge.
2. **LSDV instead of HDFE partialling-out** 鈥?mathematically equivalent for 1鈥? categorical FEs.
3. **No multi-way clustering** 鈥?single cluster only.

---

## 7. Source File Quick Reference

```
research/vendor/stata_community/ppmlhdfe/ppmlhdfe-master/
鈹溾攢鈹€ src/ppmlhdfe.ado                  鈫?Main ADO entry (Estimate)
鈹溾攢鈹€ src/ppmlhdfe.mata                 鈫?GLM class, IRLS, solve()
鈹溾攢鈹€ src/ppmlhdfe_functions.mata       鈫?qrsolve helpers, trim_separated_obs
鈹溾攢鈹€ src/ppmlhdfe_separation_simplex.mata  鈫?Simplex separation detection
鈹溾攢鈹€ src/ppmlhdfe_separation_relu.mata     鈫?ReLU separation detection
鈹溾攢鈹€ src/ppmlhdfe_p.ado                鈫?predict post-estimation
鈹斺攢鈹€ examples/                           鈫?Usage examples
```

---

## 8. 宸插疄鐜板苟鏈夋槑纭簮鐮佷緷鎹?
- **鍙傛暟鏍￠獙**锛歚PPMLHDFE.__init__()` 鏍￠獙 `offset`/`exposure` 浜掓枼锛堝搴?`ppmlhdfe.ado` L157锛夛紱`exposure > 0` 鏍￠獙宸插姞鍏ャ€?- **鍥哄畾鏁堝簲涓?singleton drop**锛氬鎵?`AbsorbingOLS._prepare_data()`锛屼笌 `GLM::init_fixed_effects()` 涓€鑷淬€?- **鍙橀噺鍔犺浇涓庢爣鍑嗗寲**锛歚fit()` 涓?`AbsorbingOLS._prepare_data()` 鏋勯€犵煩闃碉紝骞跺湪 IRLS 鍓嶅 `x` 鏍囧噯鍖栵紝瀵瑰簲 `GLM::init_variables()`銆?- **IRLS 鏍稿績寰幆**锛歚PPMLHDFE._irls_fit()` 瀹炵幇 `畏 鈫?渭 鈫?z 鈫?w 鈫?solve 鈫?step-halving` 娴佺▼锛屼笌 `GLM::inner_irls()` 涓€鑷淬€?- **鍒濆鍊?*锛氶粯璁や娇鐢?`log(y+1)` 瀵?`X` 鐨?OLS 浣滀负鍒濆鐚滄祴锛屽搴?`GLM::solve()` 鐨?`"ols"` guess銆?- **瀵规暟浼肩劧**锛氫娇鐢?SciPy `gammaln` 璁＄畻 `ll = 危[y*log(渭) - 渭 - gammaln(y+1)]`锛屽搴?Mata 鐨?`lngamma(y+1)`銆?- **甯告暟椤规仮澶?*锛歚_build_t_matrix()` 浣跨敤鍔犳潈鍧囧€硷紙鏉冮噸 = 渭锛夋仮澶?`_cons`锛屽搴?`GLM::solve()` L461鈥?70銆?- **VCE**锛歚vce="ols"`锛團isher info锛夈€乣vce="robust"`锛坰andwich + `N/(N-1)`锛夈€乣vce="cluster"`锛堜粎 `G/(G-1)` asymptotic 淇锛夊潎涓?`ppmlhdfe` 婧愮爜瀵归綈銆?- **offset / exposure**锛歚__init__()` 鏆撮湶鍙傛暟锛宍_irls_fit()` 姣忚疆鍔犲叆 `eta`锛宍_build_t_matrix()` 鍑忓幓鍔犳潈鍧囧€硷紝涓?`ppmlhdfe.ado` L234鈥?43 鍙?Mata L469 涓€鑷淬€?- **predict**锛歚type="xb"`銆乣type="mu"`銆乣type="residuals"` 宸插疄鐜帮紝瀵瑰簲 `ppmlhdfe_p.ado`銆?- **deviance / pseudo R虏**锛歚fit()` 璁＄畻 `deviance = 2 * 危[(渭 - y) + y * log(y/渭)]` 鍜?`pseudo_r2 = 1 - ll / ll_0`锛屼笌 `ppmlhdfe.mata` L699鈥?06 鍙?`ppmlhdfe.ado` L342鈥?44 涓€鑷淬€?
## 9. 宸插疄鐜帮紝浣嗗睘浜?Phase A 鐨勭瓑浠峰疄鐜?
- **LSDV 鏇夸唬 HDFE partialling-out**锛歅ython 鍦?IRLS 姣忎竴姝ョ洿鎺ユ眰瑙ｇ瀵?LSDV 鐭╅樀锛岃€岄潪璋冪敤 `reghdfe` 鐨?MAP 鍚告敹銆傚浜?1鈥? 涓函鍒嗙被 FE锛屼袱鑰呮暟瀛︾瓑浠枫€?
## 10. 鏈疄鐜版垨鏄惧紡鎷掔粷

- **separation 妫€娴?*锛歚simplex`銆乣relu`銆乣fe`銆乣mu` 鍥涚妫€娴嬪潎鏈疄鐜帮紱IRLS 鍦ㄦ棤 separation 妫€鏌ョ殑骞插噣鏁版嵁涓婃敹鏁涖€?- **predict 瀛愰€夐」**锛歚pearson`銆乣deviance`銆乣anscombe`銆乣working` 绛夋湭瀹炵幇銆?- **multi-way clustering**锛氫粎鏀寔鍗?cluster銆?- **wrapper 鍙傛暟**锛歚guess` 鎺у埗鏈毚闇层€?- `separation`銆乣d`銆乣vceversion`銆乣individual`銆乣group`銆乣noreport`銆乣keepmata` 绛夊弬鏁扮‖鎷掔粷銆?
## 11. Phase B 鏂板瀹炵幇锛堟湰杞級

- **`noconstant`**锛歚ppmlhdfe()` wrapper 鏂板 `noconstant: bool = False`銆傛敞鎰忥細Stata 瀹樻柟 `ppmlhdfe` 鍛戒护 syntax 涓湭鍒楀嚭 `noconstant`锛屽洜姝よ鍙傛暟鏄?Python 绔殑鎵╁睍鑳藉姏锛岀敱搴曞眰 `AbsorbingOLS(add_constant=...)` 鐩存帴鏀寔銆?- **`maxiter` / `tolerance`**锛歚ppmlhdfe()` wrapper 鏂板 `maxiter: int = 100` 鍜?`tolerance: float = 1e-8`锛屽垎鍒槧灏勫埌 `PPMLHDFE(max_iter=..., tol=...)`锛屼笌 `ppmlhdfe.ado` L121鈥?22 瀵瑰簲銆?- **`predict(residuals)`**锛歚PPMLHDFE.predict(type="residuals")` 杩斿洖 `y - 渭`锛屽搴?`ppmlhdfe_p.ado` L104 `response` 璇箟銆?- **`deviance` / `pseudo_r2`**锛歚fit()` 鏂板瀛楁璁＄畻锛屽搴?`ppmlhdfe.mata` L699鈥?06锛坉eviance锛夊拰 `ppmlhdfe.ado` L342鈥?44锛坧seudo R虏锛夈€侴olden dual-run 楠岃瘉锛歚tests/golden/test_p3_ppmlhdfe_fit_stats.py`銆?
