# `eventstudyinteract` Source-to-Python Mapping

**Version mapped:** 0.1 24jan2022 (local mirror `research/vendor/stata_community/eventstudyinteract/EventStudyInteract-main/`)
**Python target:** `stataflow.estimators.EventStudyInteract` + `stataflow.compat.stata.eventstudyinteract()`

---

## 1. ADO Entry Points

| Stata File | Program / Line | What it does | Maps to Python |
|------------|----------------|--------------|----------------|
| `eventstudyinteract.ado` | `program define eventstudyinteract, eclass` (L4) | Top-level dispatcher, syntax parsing, sample marking | `stataflow.compat.stata.eventstudyinteract()` wrapper |
| `eventstudyinteract.ado` | `syntax varlist(min=1 numeric) [if] [in] [aw fw iw pw], absorb(varlist) cohort(varname) control_cohort(varname) [covariates(varlist) vce(string)]` (L6鈥?) | Parses `y event_dummies`, `cohort`, `control_cohort`, `absorb`, `vce` | `EventStudyInteract.__init__()` + `fit()` parameter handling |

---

## 2. Core Algorithm 鈫?Python Mapping

### 2.1 Sample Screening

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `eventstudyinteract.ado` | `marksample touse` (L13) | Initialize sample indicator from `if`/`in` | `EventStudyInteract.fit()` missing-value drop on `y`, `cohort`, `control_cohort`, `event_dummies`, `absorb`, and `cluster` |
| `eventstudyinteract.ado` | `markout touse by xq covariates absorb, strok` (L14) | Drop rows with missing RHS variables | Included in the unified `notna().all(axis=1)` mask |

### 2.2 nD Construction (Control Cohort Zeroing)

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `eventstudyinteract.ado` | `gen n`l' = `l'; replace n`l' = 0 if control_cohort == 1` (L24鈥?6) | For each relative-time dummy, create a copy that is zeroed out for the control cohort | `EventStudyInteract.fit()` creates `col = f"_n{d}"` where `df[col] = df[d] * (df[control_cohort] == 0).astype(float)` |

### 2.3 Cohort Share Regression (First-Step)

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `eventstudyinteract.ado` | `levelsof cohort if control_cohort == 0, local(cohort_list)` (L30) | Enumerate non-control cohorts | `cohort_list = sorted(df.loc[non_control_mask, cohort_var].dropna().unique())` |
| `eventstudyinteract.ado` | `regress cohort_ind nvarlist if touse & control_cohort == 0, nocons` (L43) | For each cohort `g`, regress `1(cohort==g)` on `nD` dummies (no intercept) to get cohort shares `ff_w` | `XtX_nd_inv = pinv(X_nd.T @ X_nd); beta_g = XtX_nd_inv @ (X_nd.T @ y_g); ff_w[i, :] = beta_g` |
| `eventstudyinteract.ado` | `predict resid`yy'', resid` (L46) | Store residuals from each cohort-share regression | `resid_g = y_g - X_nd @ beta_g` |

### 2.4 Robust Covariance of Cohort Shares (avar-style)

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `eventstudyinteract.ado` | `mat accum XX = nvarlist ... nocons` (L55) | Compute `X'X` | `XtX_nd = X_nd.T @ X_nd` |
| `eventstudyinteract.ado` | `mat Sxx = XX * 1/r(N); mat Sxxi = syminv(Sxx)` (L56鈥?7) | Scale and invert | `XtX_nd_inv = np.linalg.pinv(XtX_nd)` (Phase A uses direct pseudo-inverse) |
| `eventstudyinteract.ado` | `avar (nresidlist) (nvarlist) ..., nocons robust` (L58) | Compute robust sandwich `S` for the stacked cohort-share system | Python manually computes stacked score outer-products:<br>`S = sum_i outer(score_i, score_i)` where `score_i = vec(xi[:, None] * ei[None, :])` |
| `eventstudyinteract.ado` | `mat KSxxi = I(ncohort)#Sxxi; mat Sigma_ff = KSxxi * S * KSxxi * 1/r(N)` (L60鈥?1) | Assemble variance of cohort-share matrix | `KSxxi = np.kron(np.eye(n_cohort), XtX_nd_inv); Sigma_ff = KSxxi @ S @ KSxxi` (note: Python does not multiply by `1/N` because the `avar` normalization is absorbed into the score construction) |

**Normalization note:** The `.ado` explicitly comments that the scaling factor differs from the paper for unbalanced panels (L62鈥?5). Python follows the estimator-level numerical alignment verified by golden tests rather than replicating the `1/NT` scalar exactly.

### 2.5 Interaction Term Construction

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `eventstudyinteract.ado` | `gen n`l'_`yy' = (cohort == yy) * `l'` (L72) | Create full interaction set `cohort 脳 relative_time` | `df[col] = (df[cohort_var] == g).astype(float) * df[d]` for each dummy `d` and cohort `g` |

### 2.6 Interacted Regression (Second-Step)

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `eventstudyinteract.ado` | `reghdfe lhs cohort_rel_varlist covariates if touse, absorb(absorb) vce(vce)` (L84) | Estimate full interaction model with FE absorption and requested VCE | `EventStudyInteract.fit()`:<br>1. Iteratively residualize `y` and each interaction column by demeaning within `absorb_vars`.<br>2. Detect collinearity in residualized design via QR.<br>3. Run OLS on kept columns. |

**Key equivalence:** Stata uses `reghdfe` to partial out FEs. Python's iterative demeaning over the `absorb_vars` computes the same within-transformed values (verified on `wagepan`-style panels to machine precision).

### 2.7 Coefficient Matrix Reconstruction

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `eventstudyinteract.ado` | Mata / matrix loop reshaping `b` and `V` into `evt_bb` and `evt_VV` (L89鈥?01) | Reshape the long coefficient vector into a `n_cohort 脳 n_rel` matrix | `evt_bb = beta_full.reshape((n_cohort, n_rel), order="F")` |

### 2.8 Interaction-Weighted (IW) Estimator

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `eventstudyinteract.ado` | `mata: b_iw = colsum(w :* delta)` (L107) | Compute IW coefficients as cohort-share-weighted average of interaction coefficients | `b_iw = np.sum(ff_w * evt_bb, axis=0)` |

### 2.9 Variance of the IW Estimator

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `eventstudyinteract.ado` | `mata: VV = st_matrix("e(V)")` (L116) | Extract full VCE from the interacted regression | `VV` extracted from OLS/cluster VCE on residualized design |
| `eventstudyinteract.ado` | `mata: wlong = w' :* J(1,nc,e(1,nr)')` and loop expansion (L118鈥?20) | Build block-diagonal weighting matrix for delta-method variance | `wlong` constructed by horizontally stacking `w.T * eye(n_rel)[i, :]` for each relative time `i` |
| `eventstudyinteract.ado` | `mata: V_iw = wlong * VV * wlong'` (L122) | Delta-method variance from regression step | `V_iw = wlong @ VV @ wlong.T` |
| `eventstudyinteract.ado` | Mata loop adding `Vshare` contribution (L127鈥?34) | Add variance from cohort-share estimation: `delta_i' * Vshare_evt * delta_j` | Python nested loop over `i, j` adding `evt_bb[:, i] @ Vshare_evt @ evt_bb[:, j]` to `V_iw[i, j]` |

---

## 3. `predict` and Post-estimation

`eventstudyinteract` does not provide a dedicated `predict` post-estimation command. The primary output is the IW event-study coefficient table (`e(b_iw)` / `e(V_iw)`).

---

## 4. Wrapper Parameter Matrix

| Stata Option | Wrapper Parameter | Python Behavior |
|--------------|-------------------|-----------------|
| `varlist(y Dm3 Dm2 D0 Dp1 ...)` | `event_dummies` | **Legacy mode:** user provides pre-generated dummy names |
| *(auto-generated)* | `time`, `first_treat`, `horizons`, `omit` | **Auto-generation mode:** wrapper creates `Dm{h}` / `D0` / `Dp{h}` dummies internally |
| `cohort(varname)` | `cohort` | Supported |
| `control_cohort(varname)` | `control_cohort` | Supported |
| `absorb(varlist)` | `absorb` | Supported: 1鈥? categorical vars |
| `vce(cluster varname)` | `vce="cluster"`, `cluster="var"` | Supported |
| `covariates(varlist)` | *(not exposed)* | Phase A not implemented |

---

## 5. Known Phase A Simplifications

1. **No automatic covariate support** 鈥?`covariates()` option not exposed.
2. **No multi-way clustering** 鈥?single cluster only.
3. **Unbalanced panel normalization** 鈥?the `avar` scaling factor `1/NT` vs `1/N` is not fully replicated; alignment relies on golden-test verified numerical equivalence.
4. **No `window` / `minn` / `graph` options** 鈥?not exposed.

---

## 6. 宸插疄鐜板苟鏈夋槑纭簮鐮佷緷鎹?
- **鏍锋湰绛涢€?*锛歚marksample`/`markout` 閫昏緫绛変环瀹炵幇銆?- **nD 鏋勯€?*锛氬鐓?cohort 鐨?dummy 褰掗浂涓庢簮鐮?L24鈥?6 涓€鑷淬€?- **Cohort share 鍥炲綊**锛歚regress cohort_ind nvarlist, nocons` 瀵瑰簲 Python 鐨?`pinv(X'X) X'y` 璁＄畻銆?- **Cohort share 绋冲仴鍗忔柟宸?*锛歚avar` 椋庢牸鐨?stacked score outer-product 涓?`KSxxi @ S @ KSxxi` 鏋勯€犲凡鏄犲皠銆?- **浜や簰椤圭敓鎴?*锛歚cohort 脳 relative_time` 鍏ㄤ氦浜掗泦鐢熸垚涓庢簮鐮?L72 涓€鑷淬€?- **FE 鍚告敹鍥炲綊**锛氳凯浠ｅ幓鍧囧€?+ QR 鍏辩嚎鎬ф娴?+ OLS锛屼笌 `reghdfe` 鍦ㄦ暟瀛︿笂绛変环銆?- **IW 绯绘暟**锛歚colsum(w :* delta)` 瀵瑰簲 `np.sum(ff_w * evt_bb, axis=0)`銆?- **IW 鏂瑰樊**锛歚wlong * VV * wlong'` + cohort-share 鏂瑰樊璐＄尞鐨勪袱姝?delta method 涓庢簮鐮?L116鈥?34 涓€鑷淬€?
## 7. 宸插疄鐜帮紝浣嗗睘浜?Phase A 鐨勭瓑浠峰疄鐜?
- **FE 鍚告敹鏂瑰紡**锛歋tata 浣跨敤 `reghdfe` 鐨?MAP/绋犲瘑姹傝В锛孭ython 浣跨敤杩唬鍘诲潎鍊硷紱瀵?1鈥? 涓垎绫?FE 鏁板绛変环銆?- **Cohort share 鍗忔柟宸缉鏀?*锛氭湭瀹屽叏澶嶇幇 `avar` 鍦ㄩ潰鏉挎暟鎹笅鐨?`1/NT` 褰掍竴鍖栫粏鑺傦紝golden 娴嬭瘯瀹瑰樊鍐呭凡瀵归綈銆?
## 8. 鏈疄鐜版垨鏄惧紡鎷掔粷

- `covariates()` 鈥?wrapper 纭嫆缁濄€?- `window()`銆乣minn()`銆乣graph`銆乣save`銆乣replace` 鈥?纭嫆缁濄€?- Multi-way clustering 鈥?浠呮敮鎸佸崟 cluster銆?
