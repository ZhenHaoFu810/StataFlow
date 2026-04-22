# `ivreghdfe` Source-to-Python Mapping

**Version mapped:** `1.1.4 29nov2025` (local mirror `research/vendor/stata_community/ivreghdfe/ivreghdfe-master/`)
**Python target:** `stataflow.estimators.IVAbsorbingOLS` + `stataflow.compat.stata.ivreghdfe()`

---

## 1. ADO Entry Points

| Stata File | Program / Line | What it does | Maps to Python |
|------------|----------------|--------------|----------------|
| `src/ivreghdfe.ado` | `program ivreghdfe` (L43) | Parent dispatcher, dependency checks (`ftools >= 2.49.1`, `reghdfe >= 6.12.5`), replay handling | `stataflow.compat.stata.ivreghdfe()` wrapper |
| `src/ivreghdfe.ado` | `program ivreg211` (L159) | **Main estimation entry point.** Parses IV syntax, `absorb()`, `vce()`, `cluster()`, constructs `reghdfe_options` | `IVAbsorbingOLS.__init__()` + `fit()` orchestration |

---

## 2. Core Architectural Insight

`ivreghdfe` is **not** a standalone IV solver. It is a thin glue layer:

1. Parses `absorb(varlist)`
2. Calls `reghdfe` to create a `FixedEffects` (HDFE) object
3. Uses `reghdfe` to **partial out** (residualize) **every variable**: `y`, `X_endog`, `X_exog`, `Z_instruments`
4. Runs `ivreg2`鈥檚 2SLS machinery on the residualized variables
5. Adjusts reported DoF (`df_a`, nested cluster corrections) to account for absorbed FEs

**Mathematical equivalence:**
- Let `M_FE = I - D(D'D)^{-1}D'` be the partialling-out operator (same as `reghdfe`鈥檚 MAP).
- `ivreghdfe` computes `尾 = [X' M_FE Z (Z' M_FE Z)^{-1} Z' M_FE X]^{-1} X' M_FE Z (Z' M_FE Z)^{-1} Z' M_FE y`.
- This is **exactly** the 2SLS estimator on the full LSDV design matrix `W = [D, X, Z]`.

Python `IVAbsorbingOLS` therefore implements this by building the unified LSDV matrix and running 2SLS directly on it, which is mathematically identical.

---

## 3. Detailed Step Mapping

### 3.1 Syntax Parsing and absorb() Handling

| Source | Lines | Logic | Python Equivalent |
|--------|-------|-------|-------------------|
| `ivreghdfe.ado` | `L258鈥?72` | If `absorb()` is present, sets `small`, `noconstant`, `nopartialsmall`, and builds `reghdfe_options` string | Wrapper exposes `noconstant: bool` (default `False`); `IVAbsorbingOLS.__init__()` receives `add_constant=not noconstant`. The `small` option is implicit in our finite-sample VCE formulas. |

### 3.2 Variable Residualization (Partialling Out)

| Source | Lines | Logic | Python Equivalent |
|--------|-------|-------|-------------------|
| `ivreghdfe.ado` | Internal call to `reghdfe, nopartialout varlist_is_touse` | Creates `FixedEffects` object and residualizes all IV variables | `IVAbsorbingOLS._prepare_data()` builds a **single** LSDV matrix containing `[constant, dummies, x_exog, x_endog, instruments]`. The first-stage and second-stage OLS regressions automatically project out the FE dummies because they are explicit columns in the matrix. |

**Why this is equivalent:**
- `reghdfe` residualizes each variable separately and then runs 2SLS on the residuals.
- LSDV includes the dummies as regressors, so the 2SLS first stage `Z 鈫?X_endog` already conditions on the same FE space.
- Both yield the identical `尾` vector for the non-FE coefficients.

### 3.3 Collinearity and Identification

| Source | Lines | Logic | Python Equivalent |
|--------|-------|-------|-------------------|
| `ivreghdfe.ado` | `ivparse` + `ivreg2` Mata libs | Drops collinear instruments / regressors; checks underidentification (`#Z >= #X`) | `IVAbsorbingOLS._detect_collinearity()` runs QR on the full LSDV matrix, dropping `x` or `z` columns if they are collinear with `[constant, dummies]`. Post-QR, it checks `k_z_full >= k_x_full`. |

### 3.4 Two-Stage Least Squares

| Source | Lines | Logic | Python Equivalent |
|--------|-------|-------|-------------------|
| `ivreghdfe.ado` / `ivreg2` Mata | First stage: `螤 = (Z_r'Z_r)^{-1} Z_r'X_r`; Second stage: `尾 = (X虃'X虃)^{-1} X虃'y_r` | Standard 2SLS on residualized data | `IVAbsorbingOLS.fit()` (L705鈥?14): `Pi = solve(ZtZ, ZtX)`; `X_proj = Z @ Pi`; `beta_full = solve(XtX_proj, Xty_proj)` |

### 3.5 Structural Residuals and R虏

| Source | Lines | Logic | Python Equivalent |
|--------|-------|-------|-------------------|
| `ivreghdfe.ado` / `ivreg2` | Uses **structural residuals** `e = y - X尾` (not `y - X虃尾`) for RSS, RMSE, and VCE | `IVAbsorbingOLS.fit()` (L717鈥?18) computes `residuals = y - X_full @ beta_full` |
| `ivreghdfe.ado` | R虏 is based on `y` after partialling out FEs (`y_resid`) vs structural residuals | `IVAbsorbingOLS.fit()` (L728鈥?48) computes `y_resid = y - W纬` where `W = [constant, dummies]`, then `r2 = 1 - rss_struct / tss_resid` |

### 3.6 VCE and Cluster-Robust Standard Errors

| Source | Lines | Logic | Python Equivalent |
|--------|-------|-------|-------------------|
| `ivreghdfe.ado` | `vce(ols)` | Conventional 2SLS VCE: `蟽虏 (X虃'X虃)^{-1}` with `蟽虏 = RSS / df_r` | `IVAbsorbingOLS.fit(vce="ols")` (L769鈥?71) |
| `ivreghdfe.ado` | `vce(robust)` | HC1 sandwich on `X_proj`: `(X虃'X虃)^{-1} X虃' diag(e虏) X虃 (X虃'X虃)^{-1}` | `IVAbsorbingOLS.fit(vce="robust")` (L772鈥?75): `XtOmegaX = (X_proj * e_sq[:, np.newaxis]).T @ X_proj`; `cov_full = M_inv @ XtOmegaX @ M_inv` |
| `ivreghdfe.ado` | `vce(cluster var)` | Cluster-robust sandwich on `X_proj` with small-sample correction using `k_eff = k_x_reported + df_a` | `IVAbsorbingOLS.fit(vce="cluster")` (L776鈥?89) computes meat by cluster, then `n_adj * g_adj` with `k_eff = k_x_reported + df_a` |

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
| `ivreghdfe.ado` | `ivreg2` output + `reghdfe` constant recovery | Reports only `X_endog` and `X_exog` coefficients. The constant is partialled out by the FE structure and **not reported** (unlike `reghdfe`, which recovers `_cons` as the unweighted mean of FE intercepts). | `IVAbsorbingOLS.fit()` builds `T` matrix that maps full LSDV `beta_full` to reported space. Only `x_endog` and `x_exog` coefficients are reported; `_cons` is intentionally omitted (`_coef_names = kept_x_endog_names + kept_x_exog_names`). The legacy `_cons` recovery logic in the `T` matrix is retained for structural compatibility but is never active because `_cons` 鈭?`_coef_names`. |

**Note:** `ivreghdfe` wrapper in Python previously had a bug where single `absorb` was treated as `areg` (command label). This has been fixed: `ivreghdfe()` wrapper now always passes `absorb` as a list, and the command label is always `"ivreghdfe"`.

---

## 4. `predict` Post-estimation Mapping

`ivreghdfe` delegates `predict` to `reghdfe_p` when `e(N_hdfe) != .` (i.e. when `absorb()` was used). The supported options are identical to `reghdfe`:

| Stata Option | Meaning | Python Status |
|--------------|---------|---------------|
| `xb` | Linear prediction (reported coefficients only) | `IVAbsorbingOLS.predict(type="xb")` 鈥?returns `X_reported @ beta_reported` |
| `xbd` | Linear prediction including FEs | `IVAbsorbingOLS.predict(type="xbd")` 鈥?returns `X_full @ beta_full` |
| `residuals` | `y - xbd` | `IVAbsorbingOLS.predict(type="residuals")` |
| `d` | Sum of FEs (`xbd - xb`) | `IVAbsorbingOLS.predict(type="d")` |
| `dresiduals` | `y - xb` | `IVAbsorbingOLS.predict(type="dresiduals")` |

---

## 5. Wrapper Parameter Matrix

| Stata Option | Wrapper Parameter | Python Behavior |
|--------------|-------------------|-----------------|
| `absorb(varlist)` | `absorb=str\|list[str]` | Supported: 1鈥? categorical vars |
| `vce(ols)` | `vce="ols"` | Supported |
| `vce(cluster var)` | `vce="cluster"`, `cluster="var"` | Supported |
| `vce(robust)` | `vce="robust"` | Supported |
| `noconstant` | `noconstant: bool` | Supported (Phase B): passed through to `IVAbsorbingOLS(add_constant=not noconstant)` |
| `keepsingletons` | `keepsingletons: bool` | Supported (Phase B): passed through as `drop_singletons=not keepsingletons` |
| `first` / `ffirst` | *(not exposed)* | Hard-rejected via `**kwargs` |

---

## 6. Known Phase A Simplifications

1. **No LIML / GMM / CUE** 鈥?only 2SLS.
2. **No `first` stage diagnostics** 鈥?wrapper rejects `first=True` etc. Phase B did not tackle this (requires sub-regression result objects).
3. **No multi-way clustering** 鈥?single cluster only.
4. **LSDV instead of explicit residualization** 鈥?mathematically equivalent for 1鈥? categorical FEs.

---

## 7. Source File Quick Reference

```
research/vendor/stata_community/ivreghdfe/ivreghdfe-master/
鈹溾攢鈹€ src/ivreghdfe.ado          鈫?Parent dispatcher
鈹溾攢鈹€ src/ivreghdfe.sthlp        鈫?Help file (useful for option semantics)
鈹溾攢鈹€ example.do                 鈫?Usage examples
鈹斺攢鈹€ test.do                    鈫?Basic verification do-file
```

`ivreghdfe` calls into:
- `reghdfe` Mata libraries (`FixedEffects`, `partial_out`, `estimate_dof`)
- `ivreg2` Mata libraries (2SLS solver, VCE computation)

---

## 8. 宸插疄鐜板苟鏈夋槑纭簮鐮佷緷鎹?
- **absorb() 瑙ｆ瀽涓?reghdfe_options 鏋勯€?*锛歚IVAbsorbingOLS.__init__()` 瀵瑰簲 `ivreghdfe.ado` L258鈥?72銆?- **鍙橀噺娈嬪樊鍖栵紙partialling out锛?*锛氱粺涓€ LSDV 鐭╅樀 `[constant, dummies, x_exog, x_endog, instruments]` 鑷姩鎶曞奖鍑?FE锛屼笌 `reghdfe` 娈嬪樊鍖?+ `ivreg2` 2SLS 涓ユ牸绛変环銆?- **鍏辩嚎鎬т笌璇嗗埆妫€楠?*锛歚IVAbsorbingOLS._detect_collinearity()` 杩愯 QR 妫€娴嬪苟鏍￠獙 `#Z >= #X`銆?- **2SLS**锛氱涓€闃舵 `Pi = solve(ZtZ, ZtX)`銆佺浜岄樁娈?`beta_full = solve(XtX_proj, Xty_proj)` 瀵瑰簲 `ivreg2` Mata 瀹炵幇銆?- **缁撴瀯鎬ф畫宸?*锛氫娇鐢?`y - X尾` 璁＄畻 RSS銆丷MSE銆乂CE锛屼笌 `ivreghdfe.ado` / `ivreg2` 涓€鑷淬€?- **VCE**锛歚vce="ols"`銆乣vce="robust"`銆乣vce="cluster"` 鍧囧凡瀹炵幇锛沜luster 灏忔牱鏈慨姝ｄ娇鐢?`k_eff = k_x_reported + df_a`锛屼笌婧愮爜鎯緥涓€鑷淬€?- **鑷敱搴?`df_a`**锛氬鐢?`AbsorbingOLS` 鐨?Phase A 鍏紡銆?- **鍛戒护璇箟淇**锛歚ivreghdfe()` wrapper 濮嬬粓鎶ュ憡 `command="ivreghdfe"`銆?- **predict**锛歚type="xb"`銆乣"xbd"`銆乣"residuals"`銆乣"d"`銆乣"dresiduals"` 鍧囧凡瀹炵幇 (Phase B)銆?
## 9. 宸插疄鐜帮紝浣嗗睘浜?Phase A 鐨勭瓑浠峰疄鐜?
- **LSDV 鏇夸唬鏄惧紡 residualization**锛歅ython 灏?FE dummies 浣滀负鏄惧紡鍥炲綊鍏冩斁鍏?2SLS锛岃€岄潪鍏堝姣忓彉閲忓崟鐙皟鐢?`reghdfe` 娈嬪樊鍖栥€傛暟瀛︿笂瀹屽叏绛変环銆?
## 10. 鏈疄鐜版垨鏄惧紡鎷掔粷

- **LIML / GMM / CUE**锛氫粎鏀寔 2SLS銆?- **first / ffirst 涓€闃舵璇婃柇**锛歸rapper 閫氳繃 `**kwargs` 纭嫆缁濄€侾hase B 鏈Е鍙婏紙闇€瑕佽繑鍥炲畬鏁寸殑瀛愬洖褰掔粨鏋滃璞★紝涓庡綋鍓?`ResultSchema` 缁撴瀯宸紓杈冨ぇ锛夈€?- **multi-way clustering**锛氫粎鏀寔鍗?cluster銆?
