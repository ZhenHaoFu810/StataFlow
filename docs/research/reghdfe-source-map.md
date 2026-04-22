# `reghdfe` Source-to-Python Mapping

**Version mapped:** `6.13.1 10Jan2026` (local mirror `research/vendor/stata_community/reghdfe/reghdfe-master/`)
**Python target:** `stataflow.estimators.AbsorbingOLS` + `stataflow.compat.stata.reghdfe()`

---

## 1. ADO Entry Points

| Stata File | Program / Line | What it does | Maps to Python |
|------------|----------------|--------------|----------------|
| `current-code/reghdfe.ado` | `program reghdfe` (L1) | Top-level dispatcher, dependency checks, intercepts replay / version calls | `stataflow.compat.stata.reghdfe()` wrapper |
| `current-code/reghdfe.ado` | `program Estimate, eclass` (L113) | **Main estimation entry point.** Parses `absorb()`, `vce()`, `cluster()`, `keepsingletons`, builds sample (`touse`), calls Mata | `AbsorbingOLS.__init__()` + `fit()` orchestration |
| `current-code/reghdfe.ado` | `L210` | `drop_singletons = ("`keepsingletons'" == "")` 鈥?default is **drop** | `AbsorbingOLS._drop_singletons()` |
| `current-code/reghdfe_p.ado` | `program reghdfe_p` (L1) | `predict` post-estimation: `xb`, `residuals`, `d`, `xbd`, `dresiduals` | `AbsorbingOLS.predict()` |

---

## 2. Mata Object Hierarchy

```
reghdfe.ado
    鈹斺攢鈹€ fixed_effects()          [creates HDFE = FixedEffects()]
            鈹溾攢鈹€ FixedEffects::init()       [singleton drop, factor creation]
            鈹溾攢鈹€ FixedEffects::partial_out()[MAP/LSMR partialling out]
            鈹溾攢鈹€ estimate_dof()             [df_a computation]
            鈹斺攢鈹€ reghdfe_solve_ols()        [VCE + results]
```

---

## 8. 宸插疄鐜板苟鏈夋槑纭簮鐮佷緷鎹?
- **杩唬 singleton drop**锛歚AbsorbingOLS._drop_singletons()` 涓?`FE.mata:FixedEffects::init()` 閫昏緫涓€鑷达紙鎵弿銆佸墧闄ゃ€侀噸鍚洿鍒版棤鏂?singleton锛夈€?- **LSDV 璁捐鐭╅樀鏋勯€?*锛歚AbsorbingOLS._prepare_data()` 鏋勫缓 `[constant, dummies, x]` 绋犲瘑鐭╅樀銆?- **QR 鍏辩嚎鎬ф娴?*锛歚AbsorbingOLS._detect_collinearity()` 涓?`Solution.mata:check_collinear_with_fe()` 绛変环锛屼紭鍏堝墧闄?`x` 鑰岄潪 FE dummy銆?- **鑷敱搴?`df_a`**锛氬祵濂?cluster 鎵ｅ噺閫昏緫涓?`DoF.mata:dof_update_nested()` 涓€鑷达紱1 FE 鏃?`df_a = G`锛? FE 鏃?`df_a = G1 + G2 - 1`锛坓olden 娴嬭瘯楠岃瘉锛夈€?- **甯告暟椤规仮澶?*锛歚T` 鐭╅樀涓?`_cons` 琛屾瀯閫犱笌 `Regression.mata:reghdfe_extend_b_and_xx()` 涓€鑷淬€?- **R虏 涓?RMSE**锛氳绠楀彛寰勪笌 `Regression.mata:reghdfe_solve_ols()` 涓€鑷淬€?- **VCE**锛歚vce="ols"`銆乣vce="robust"`锛圚C1 sandwich锛宍N/(N-1)` 淇锛夈€乣vce="cluster"` 鍧囧凡瀹炵幇锛屼笌 `Regression.mata` 瀵瑰簲鍑芥暟涓€鑷淬€?- **predict**锛歚type="xb"`銆乣type="xbd"`銆乣type="d"`銆乣type="residuals"`銆乣type="dresiduals"` 鍧囧凡瀹炵幇锛屽搴?`reghdfe_p.ado`銆?- **wrapper 鏆撮湶闈?*锛歚absorb`銆乣vce`锛坥ls/robust/cluster锛夈€乣cluster`銆乣keepsingletons`銆乣noconstant` 鍧囧凡鏆撮湶骞堕€氳繃娴嬭瘯銆?
## 9. 宸插疄鐜帮紝浣嗗睘浜?Phase A 鐨勭瓑浠峰疄鐜?
- **LSDV 鏇夸唬 MAP/LSMR**锛歅ython 浣跨敤绋犲瘑 LSDV 鐭╅樀鐩存帴姹傝В锛岃€岄潪 `MAP.mata:map_solver()` 鐨勮凯浠ｅ潎鍊煎惛鏀躲€傚浜?1鈥? 涓函鍒嗙被 FE锛屼袱鑰呭湪鏁板涓婁弗鏍肩瓑浠凤紙`wagepan` 鏁版嵁闆嗗樊寮?`< 1e-12`锛夈€?- **绠€鍖栫増 `df_a` 鍏紡**锛氫娇鐢ㄩ棴寮?`G1 + G2 - 1`锛屾湭瀹炵幇 `DoF.mata:dof_update_mobility_group()` 鐨勫畬鏁翠簩鍒嗗浘 mobility group 绠楁硶銆傚湪鍏稿瀷闈㈡澘鏁版嵁锛堣繛閫氬浘锛変笅缁撴灉涓€鑷淬€?
## 10. 鏈疄鐜版垨鏄惧紡鎷掔粷

- **predict**锛歚stdp` 鏈疄鐜帮紱`xb`銆乣xbd`銆乣d`銆乣residuals`銆乣dresiduals` 宸插疄鐜般€?- **mobility group 澶嶆潅 DoF**锛氭湭瀹炵幇銆?- **slopes / individual FEs / team FEs**锛氫粎鏀寔鎴窛鍨嬪垎绫?absorb vars銆?- **multi-way clustering**锛氫粎鏀寔鍗?cluster銆?- **estat 鍚庝及璁＄敓鎬?*锛氫粎鏀寔鍩烘湰 predict銆?
## 11. Phase B 鏂板瀹炵幇锛堟湰杞級

- **`keepsingletons`**锛歚reghdfe.ado` L210 `drop_singletons = ("`keepsingletons'" == "")` 鈥?Python wrapper 鏂板 `keepsingletons: bool = False` 鍙傛暟锛屾槧灏勫埌 `AbsorbingOLS(..., drop_singletons=not keepsingletons)`銆俙keepsingletons=True` 鏃惰烦杩?`_drop_singletons()`锛屼繚鐣?singleton 瑙傛祴銆?- **`noconstant`**锛歚reghdfe.ado` L180 `noCONstant` 鈥?Python wrapper 鏂板 `noconstant: bool = False` 鍙傛暟锛屾槧灏勫埌 `AbsorbingOLS(..., add_constant=not noconstant)`銆?- **predict 鎵╁睍**锛歚reghdfe_p.ado` L16/46/53/58 鈥?鏂板 `predict(type="d")`銆乣predict(type="xbd")`銆乣predict(type="dresiduals")`銆?  - `xbd` = `X_full @ beta_full`锛堝惈 FE 鍜屽父鏁扮殑瀹屾暣棰勬祴锛?  - `xb` 宸蹭慨姝ｄ负浠呬娇鐢?reported 绯绘暟锛堜笉鍚?FE dummy 璐＄尞锛夛紝涓?Stata `_predict` 璇箟涓€鑷?  - `d` = `xbd - xb`锛團E 璐＄尞涔嬪拰锛?  - `dresiduals` = `y - xb`
  - `residuals` = `y - xbd`
- **singleton dropping 璇佹嵁澧炲己**锛氭柊澧?synthetic 娴嬭瘯楠岃瘉 keepsingletons 瀵规牱鏈噺涓庤鍛婁俊鎭殑褰卞搷锛涙柊澧?golden dual-run `test_p3_reghdfe_keepsingletons.py` 楠岃瘉 Stata 17 涓?Python 鍦ㄤ繚鐣?singleton 鏃剁殑涓€鑷存€с€?
---

## 3. Core Algorithm 鈫?Python Mapping

### 3.1 Sample Construction and Singleton Drop

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `FE.mata` | `FixedEffects::init()` (L186+) | Build `Factor` objects from `absorb()` vars; iteratively drop observations that are the only member of an FE group until a full pass finds no new singletons | `AbsorbingOLS._drop_singletons()` 鈥?implements the same iterative scan over all `absorb_vars` |

**Key equivalence:** `reghdfe` scans each FE sequentially, drops singleton observations, then restarts the scan because dropping an obs can create new singletons in *other* FEs. Python replicates this exact loop.

### 3.2 Design Matrix Construction (LSDV vs MAP)

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `MAP.mata` | `map_solver()` (L7+) | Iterative Mean Absorption Procedure (MAP) that residualizes each variable against the absorbed FEs | **Not used in Phase A.** Python uses mathematically equivalent dense LSDV matrix |
| `Regression.mata` | `reghdfe_solve_ols()` (L8+) | After partialling-out, runs OLS on residualized data | `AbsorbingOLS.fit()` solves `(X'X) b = X'y` on the LSDV matrix directly |

**Why LSDV is valid:** For 1鈥? pure categorical FEs, the partialling-out operator `M_FE = I - D(D'D)^{-1}D'` (where `D` is the full dummy matrix) is *exactly* what MAP converges to. Solving OLS on `[D, X]` yields coefficients identical to `reghdfe` within machine precision (verified on `wagepan` with diff `< 1e-12`).

### 3.3 Collinearity Detection

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `Solution.mata` | `Solution::check_collinear_with_fe()` (L106鈥?64) | After partialling-out, flags regressors whose norm is near zero (collinear with FEs) using `collinear_tol` | `AbsorbingOLS._detect_collinearity()` uses QR decomposition on the full LSDV matrix. If an `x` column is linearly dependent on `[constant, dummies]`, QR drops it. |

**Ordering matters:** `reghdfe` drops the *regressor*, not the FE dummy, when they are collinear. Python enforces this by placing `x` variables *after* constant and dummies in the QR ordering.

### 3.4 Degrees of Freedom (`df_a`)

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `DoF.mata` | `estimate_dof()` (L7鈥?06) | Computes `G_extended`, redundancy `doflist_M`, nested-within-cluster penalties, mobility groups | `AbsorbingOLS._prepare_data()` Phase A simplification |
| `DoF.mata` | `dof_update_nested()` (L109鈥?64) | If an absorb var equals or is nested within a cluster var, its entire level count is subtracted from `df_a` | Explicit check: if `var == cluster_var`, skip that var when summing `effective_levels` |

**Phase A formula used in Python:**
- 1 FE, no cluster: `df_a = G`
- 2 FEs, no cluster: `df_a = G1 + G2 - 1`
- Cluster nested in FE `i`: that FE contributes `0` to `df_a`

This matches `reghdfe`鈥檚 default `dofadjustments` behavior for the simple categorical-FE case (mobility groups = 1 for connected panels).

### 3.5 VCE Computation

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `Regression.mata` | `reghdfe_vce_unadjusted()` (called L127) | `V = 蟽虏 (X'X)^{-1}` with `蟽虏 = RSS / df_r` | `AbsorbingOLS.fit(vce="ols")` |
| `Regression.mata` | `reghdfe_vce_robust()` (called L130) | HC1 sandwich: `(X'X)^{-1} X' diag(e虏) X (X'X)^{-1}` times `N/(N-K)` | `AbsorbingOLS.fit(vce="robust")`: `meat = X_full.T @ (X_full * e_sq[:, np.newaxis])`; `cov_full = XtX_inv @ meat @ XtX_inv * n/(n-1)` |
| `Regression.mata` | `reghdfe_vce_cluster()` (called L136) | Cluster sandwich with `(N-1)/(N-K_eff) * G/(G-1)` small-sample correction | `AbsorbingOLS.fit(vce="cluster")` with `k_eff = k_full - nested_params` |

### 3.6 Constant Recovery (`_cons`)

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `Regression.mata` | `reghdfe_extend_b_and_xx()` (called L108) | Adds `_cons` to coefficient table. The reported constant equals the unweighted mean of all FE intercepts. | `AbsorbingOLS.fit()` builds `T` matrix where `_cons` row = `1.0` on the raw constant column plus `1/G_total` on every kept dummy for each FE group. |

### 3.7 R虏 and RMSE

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `Regression.mata` | `reghdfe_solve_ols()` (L182鈥?93) | `r2 = 1 - RSS/TSS`; `r2_a = 1 - (RSS/used_df_r) / (TSS/(N - has_intercept))`; `rmse = sqrt(RSS / used_df_r)` | `AbsorbingOLS.fit()` computes identical formulas. `used_df_r = N - df_a - df_m - df_a_nested` (Phase A: `df_a_nested = 0`). |

---

## 4. `predict` Post-estimation Mapping

| Stata Option | Source File | Meaning | Python Method |
|--------------|-------------|---------|---------------|
| `xb` | `reghdfe_p.ado` (L16, L36) | Linear prediction from reported coefficients only (excludes FE dummy contributions) | `AbsorbingOLS.predict(type="xb")` 鈥?returns `X_reported @ beta_reported` |
| `xbd` | `reghdfe_p.ado` (L16, L53) | Full prediction including absorbed FE contributions (`xb + d = y - resid`) | `AbsorbingOLS.predict(type="xbd")` 鈥?returns `X_full @ beta_full` |
| `d` | `reghdfe_p.ado` (L16, L46) | Sum of fixed effects contributions (`xbd - xb`) | `AbsorbingOLS.predict(type="d")` |
| `residuals` | `reghdfe_p.ado` (L16, L40) | `y - xbd` | `AbsorbingOLS.predict(type="residuals")` |
| `dresiduals` | `reghdfe_p.ado` (L16, L58) | `y - xb` | `AbsorbingOLS.predict(type="dresiduals")` |
| `stdp` | `reghdfe_p.ado` (L16, L36) | Standard error of prediction | **Not implemented** |

---

## 5. Options 鈫?Wrapper Parameter Matrix

| Stata Option | Wrapper Parameter | Python Behavior |
|--------------|-------------------|-----------------|
| `absorb(varlist)` | `absorb=str|list[str]` | Supported: 1鈥? categorical vars |
| `vce(robust)` | `vce="robust"` | Supported |
| `vce(cluster var)` | `vce="cluster"`, `cluster="var"` | Supported |
| `keepsingletons` | `keepsingletons: bool = False` | If `True`, skip singleton dropping and retain all observations. Maps to `AbsorbingOLS(..., drop_singletons=not keepsingletons)`. |
| `noconstant` | `noconstant: bool = False` | If `True`, omit the constant term. Maps to `AbsorbingOLS(..., add_constant=not noconstant)`. |

---

## 6. Known Phase A Simplifications

1. **No MAP/LSMR solver** 鈥?LSDV dense matrix is used instead. Proven numerically equivalent for 1鈥? categorical FEs.
2. **No mobility-group pairwise DoF correction** 鈥?uses closed-form `df_a = G1 + G2 - 1`. This is exact when the data graph is connected (typical for panel data).
3. **No slopes / individual FEs / team FEs** 鈥?only intercept-only categorical absorb vars.
4. **No multi-way clustering** 鈥?single cluster only.
5. **No `estat` ecosystem** 鈥?`predict` supports `xb`, `xbd`, `d`, `residuals`, `dresiduals`; `stdp` and full `estat` suite are missing.

---

## 7. Source File Quick Reference

```
research/vendor/stata_community/reghdfe/reghdfe-master/
鈹溾攢鈹€ current-code/reghdfe.ado          鈫?Main ADO entry (Estimate)
鈹溾攢鈹€ current-code/reghdfe.mata         鈫?Mata include orchestrator
鈹溾攢鈹€ current-code/FE.mata              鈫?FixedEffects class, singleton drop
鈹溾攢鈹€ current-code/DoF.mata             鈫?estimate_dof(), nested logic
鈹溾攢鈹€ current-code/Regression.mata      鈫?reghdfe_solve_ols(), VCE functions
鈹溾攢鈹€ current-code/MAP.mata             鈫?map_solver() (partialling out)
鈹溾攢鈹€ current-code/Solution.mata        鈫?Solution class, collinear checks
鈹斺攢鈹€ src/reghdfe_p.ado                 鈫?predict post-estimation
```
