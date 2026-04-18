# `eventstudyinteract` Source-to-Python Mapping

**Version mapped:** 0.1 24jan2022 (local mirror `research/vendor/stata_community/eventstudyinteract/EventStudyInteract-main/`)
**Python target:** `statapy.estimators.EventStudyInteract` + `statapy.compat.stata.eventstudyinteract()`

---

## 1. ADO Entry Points

| Stata File | Program / Line | What it does | Maps to Python |
|------------|----------------|--------------|----------------|
| `eventstudyinteract.ado` | `program define eventstudyinteract, eclass` (L4) | Top-level dispatcher, syntax parsing, sample marking | `statapy.compat.stata.eventstudyinteract()` wrapper |
| `eventstudyinteract.ado` | `syntax varlist(min=1 numeric) [if] [in] [aw fw iw pw], absorb(varlist) cohort(varname) control_cohort(varname) [covariates(varlist) vce(string)]` (L6–9) | Parses `y event_dummies`, `cohort`, `control_cohort`, `absorb`, `vce` | `EventStudyInteract.__init__()` + `fit()` parameter handling |

---

## 2. Core Algorithm → Python Mapping

### 2.1 Sample Screening

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `eventstudyinteract.ado` | `marksample touse` (L13) | Initialize sample indicator from `if`/`in` | `EventStudyInteract.fit()` missing-value drop on `y`, `cohort`, `control_cohort`, `event_dummies`, `absorb`, and `cluster` |
| `eventstudyinteract.ado` | `markout touse by xq covariates absorb, strok` (L14) | Drop rows with missing RHS variables | Included in the unified `notna().all(axis=1)` mask |

### 2.2 nD Construction (Control Cohort Zeroing)

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `eventstudyinteract.ado` | `gen n`l' = `l'; replace n`l' = 0 if control_cohort == 1` (L24–26) | For each relative-time dummy, create a copy that is zeroed out for the control cohort | `EventStudyInteract.fit()` creates `col = f"_n{d}"` where `df[col] = df[d] * (df[control_cohort] == 0).astype(float)` |

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
| `eventstudyinteract.ado` | `mat Sxx = XX * 1/r(N); mat Sxxi = syminv(Sxx)` (L56–57) | Scale and invert | `XtX_nd_inv = np.linalg.pinv(XtX_nd)` (Phase A uses direct pseudo-inverse) |
| `eventstudyinteract.ado` | `avar (nresidlist) (nvarlist) ..., nocons robust` (L58) | Compute robust sandwich `S` for the stacked cohort-share system | Python manually computes stacked score outer-products:<br>`S = sum_i outer(score_i, score_i)` where `score_i = vec(xi[:, None] * ei[None, :])` |
| `eventstudyinteract.ado` | `mat KSxxi = I(ncohort)#Sxxi; mat Sigma_ff = KSxxi * S * KSxxi * 1/r(N)` (L60–61) | Assemble variance of cohort-share matrix | `KSxxi = np.kron(np.eye(n_cohort), XtX_nd_inv); Sigma_ff = KSxxi @ S @ KSxxi` (note: Python does not multiply by `1/N` because the `avar` normalization is absorbed into the score construction) |

**Normalization note:** The `.ado` explicitly comments that the scaling factor differs from the paper for unbalanced panels (L62–65). Python follows the estimator-level numerical alignment verified by golden tests rather than replicating the `1/NT` scalar exactly.

### 2.5 Interaction Term Construction

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `eventstudyinteract.ado` | `gen n`l'_`yy' = (cohort == yy) * `l'` (L72) | Create full interaction set `cohort × relative_time` | `df[col] = (df[cohort_var] == g).astype(float) * df[d]` for each dummy `d` and cohort `g` |

### 2.6 Interacted Regression (Second-Step)

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `eventstudyinteract.ado` | `reghdfe lhs cohort_rel_varlist covariates if touse, absorb(absorb) vce(vce)` (L84) | Estimate full interaction model with FE absorption and requested VCE | `EventStudyInteract.fit()`:<br>1. Iteratively residualize `y` and each interaction column by demeaning within `absorb_vars`.<br>2. Detect collinearity in residualized design via QR.<br>3. Run OLS on kept columns. |

**Key equivalence:** Stata uses `reghdfe` to partial out FEs. Python's iterative demeaning over the `absorb_vars` computes the same within-transformed values (verified on `wagepan`-style panels to machine precision).

### 2.7 Coefficient Matrix Reconstruction

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `eventstudyinteract.ado` | Mata / matrix loop reshaping `b` and `V` into `evt_bb` and `evt_VV` (L89–101) | Reshape the long coefficient vector into a `n_cohort × n_rel` matrix | `evt_bb = beta_full.reshape((n_cohort, n_rel), order="F")` |

### 2.8 Interaction-Weighted (IW) Estimator

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `eventstudyinteract.ado` | `mata: b_iw = colsum(w :* delta)` (L107) | Compute IW coefficients as cohort-share-weighted average of interaction coefficients | `b_iw = np.sum(ff_w * evt_bb, axis=0)` |

### 2.9 Variance of the IW Estimator

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `eventstudyinteract.ado` | `mata: VV = st_matrix("e(V)")` (L116) | Extract full VCE from the interacted regression | `VV` extracted from OLS/cluster VCE on residualized design |
| `eventstudyinteract.ado` | `mata: wlong = w' :* J(1,nc,e(1,nr)')` and loop expansion (L118–120) | Build block-diagonal weighting matrix for delta-method variance | `wlong` constructed by horizontally stacking `w.T * eye(n_rel)[i, :]` for each relative time `i` |
| `eventstudyinteract.ado` | `mata: V_iw = wlong * VV * wlong'` (L122) | Delta-method variance from regression step | `V_iw = wlong @ VV @ wlong.T` |
| `eventstudyinteract.ado` | Mata loop adding `Vshare` contribution (L127–134) | Add variance from cohort-share estimation: `delta_i' * Vshare_evt * delta_j` | Python nested loop over `i, j` adding `evt_bb[:, i] @ Vshare_evt @ evt_bb[:, j]` to `V_iw[i, j]` |

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
| `absorb(varlist)` | `absorb` | Supported: 1–2 categorical vars |
| `vce(cluster varname)` | `vce="cluster"`, `cluster="var"` | Supported |
| `covariates(varlist)` | *(not exposed)* | Phase A not implemented |

---

## 5. Known Phase A Simplifications

1. **No automatic covariate support** — `covariates()` option not exposed.
2. **No multi-way clustering** — single cluster only.
3. **Unbalanced panel normalization** — the `avar` scaling factor `1/NT` vs `1/N` is not fully replicated; alignment relies on golden-test verified numerical equivalence.
4. **No `window` / `minn` / `graph` options** — not exposed.

---

## 6. 已实现并有明确源码依据

- **样本筛选**：`marksample`/`markout` 逻辑等价实现。
- **nD 构造**：对照 cohort 的 dummy 归零与源码 L24–26 一致。
- **Cohort share 回归**：`regress cohort_ind nvarlist, nocons` 对应 Python 的 `pinv(X'X) X'y` 计算。
- **Cohort share 稳健协方差**：`avar` 风格的 stacked score outer-product 与 `KSxxi @ S @ KSxxi` 构造已映射。
- **交互项生成**：`cohort × relative_time` 全交互集生成与源码 L72 一致。
- **FE 吸收回归**：迭代去均值 + QR 共线性检测 + OLS，与 `reghdfe` 在数学上等价。
- **IW 系数**：`colsum(w :* delta)` 对应 `np.sum(ff_w * evt_bb, axis=0)`。
- **IW 方差**：`wlong * VV * wlong'` + cohort-share 方差贡献的两步 delta method 与源码 L116–134 一致。

## 7. 已实现，但属于 Phase A 的等价实现

- **FE 吸收方式**：Stata 使用 `reghdfe` 的 MAP/稠密求解，Python 使用迭代去均值；对 1–2 个分类 FE 数学等价。
- **Cohort share 协方差缩放**：未完全复现 `avar` 在面板数据下的 `1/NT` 归一化细节，golden 测试容差内已对齐。

## 8. 未实现或显式拒绝

- `covariates()` — wrapper 硬拒绝。
- `window()`、`minn()`、`graph`、`save`、`replace` — 硬拒绝。
- Multi-way clustering — 仅支持单 cluster。

