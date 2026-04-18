# `did_imputation` Source-to-Python Mapping

**Version mapped:** November 22, 2023 (local mirror `research/vendor/stata_community/did_imputation/did_imputation-main/`)
**Python target:** `statapy.estimators.DIDImputation` + `statapy.compat.stata.did_imputation()`

---

## 1. ADO Entry Points

| Stata File | Program / Line | What it does | Maps to Python |
|------------|----------------|--------------|----------------|
| `did_imputation.ado` | `program define did_imputation, eclass` (L6) | Top-level dispatcher, syntax parsing, option validation, dependency checks (`reghdfe >= 5.7.3`, `ftools >= 2.37.0`) | `statapy.compat.stata.did_imputation()` wrapper |
| `did_imputation.ado` | `syntax varlist(min=4 max=4) ...` (L8–12) | Parses `y id time first_treat`, plus optional `cluster`, `allhorizons`, `autosample`, `horizons`, `minn`, etc. | `DIDImputation.__init__()` + `fit()` parameter handling |

---

## 2. Core Algorithm → Python Mapping

### 2.1 Sample Screening

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `did_imputation.ado` | `marksample touse, novarlist` (L18) | Initialize sample indicator | `DIDImputation.fit()` missing-value drop on `[y, id, time, first_treat]` |
| `did_imputation.ado` | `markout touse Y t; markout touse i, strok` (L51–52) | Drop rows with missing key vars | Explicit `df[key_vars].notna().all(axis=1)` mask |
| `did_imputation.ado` | `markout touse cluster, strok` (L23) | Drop missing cluster values | Included in key var screening when `cluster` is passed |

### 2.2 Relative Time and Treatment Indicator Construction

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `did_imputation.ado` | `gen K = (t-ei+shift)/delta if touse` (L91) | Compute event time relative to first treatment | `df["_K"] = df[time] - df[first_treat]` |
| `did_imputation.ado` | `gen D = (K>=0 & !mi(K)) if touse` (L98) | Treatment indicator: 1 if post-treatment and treated | `df["_D"] = (df[time] >= df[first_treat]).astype(int)` with never-treated set to 0 |

### 2.3 TWFE on Control Sample

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `did_imputation.ado` | `reghdfe Y controls if D==0 & touse, a(fe_i fe_t fe) ...` (L344–345) | Run TWFE on never-treated + not-yet-treated to estimate unit and time FEs | `DIDImputation._fit_twfe()` implements iterative demeaning: alternate `alpha_i = mean(y - gamma_t)` and `gamma_t = mean(y - alpha_i)` until convergence |

**Key equivalence:** Stata uses `reghdfe` (MAP/LSDV) to estimate the TWFE. Python's iterative demeaning converges to the identical within-transformed estimates for the two-way FE model.

### 2.4 Impute Counterfactual and Compute Effects

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `did_imputation.ado` | `gen Y0 = ...` (L354–384) | Recover fixed effects from `reghdfe` and build `Y0 = alpha_i + gamma_t + X*beta` for all observations | `df["_Y0"] = df[id].map(alpha_fe) + df[time].map(gamma_fe)` (Phase A omits `controls`) |
| `did_imputation.ado` | `gen effect = Y - Y0 if D==1 & touse` (L393) | Compute treatment effect as actual minus counterfactual for treated units | `df.loc[treated_mask, "_effect"] = y - Y0` |

### 2.5 Autosample and Horizon Selection

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `did_imputation.ado` | `count if mi(effect) & need_imputation` (L451) | Detect observations where FE cannot be imputed | Check `n_imputable == 0`; if so and `autosample=False`, raise `RuntimeError` |
| `did_imputation.ado` | `autosample` branch (L461–479) | Drop non-imputable observations and re-normalize weights | `effective_mask = imputable_mask` when `n_imputable < n_total` and `autosample=True` |
| `did_imputation.ado` | `allhorizons` / `horizons` parsing (L166–207) | Determine which event-time horizons to compute | `allhorizons=True` uses all `h >= 0` found in treated data; default behavior also computes all `h >= 0` in current Python implementation |

### 2.6 Coefficient Computation

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `did_imputation.ado` | Loop over `wtr` (weights on treated) to compute `tau` (L446+) | For each horizon `h`, compute mean of `effect` over treated observations at that horizon | `beta = df.loc[effective_mask, "_effect"].mean()` for each `_K == h` |

### 2.7 Cluster-Robust Standard Errors

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `did_imputation.ado` | Imputation weight construction (internal Mata / auxiliary do-file) | Compute weights `w` such that `tau = sum(w * effect)`, with `w` residualized on unit and time FEs within the control sample | `DIDImputation._compute_imputation_weights()` iteratively demeans `w` within units and times over the control sample |
| `did_imputation.ado` | Cluster aggregation: `egen ctrleps_w = total(weight * resid) by(cluster)` (L432) | Aggregate influence function at cluster level | `DIDImputation._compute_se()` computes `cluster_sums = df.groupby(cluster_var)["_influence"].sum()` and `SE = sqrt(sum(cluster_sums^2))` |

**DoF adjustment note:** Stata applies `dof_adj = (e(N)-1)/(e(N)-e(df_m)-e(df_a)) * e(N_clust)/(e(N_clust)-1)` for cluster-robust SEs. Python's Phase A implementation uses the unadjusted cluster sum-of-squares formula (`sqrt(sum(cluster_sums^2))`), which aligns with the imputation-weight influence function approach at the synthetic-test level but does not fully replicate the `reghdfe` small-sample correction.

---

## 3. `predict` and Post-estimation

`did_imputation` does not provide a standard `predict` post-estimation command. The primary post-estimation output is the event-study coefficient table (`tauh`).

---

## 4. Wrapper Parameter Matrix

| Stata Option | Wrapper Parameter | Python Behavior |
|--------------|-------------------|-----------------|
| `varlist(y id time first_treat)` | `y`, `id`, `time`, `first_treat` | Required positional-ish parameters |
| `cluster(varname)` | `cluster` | Supported; defaults to `id` |
| `allhorizons` | `allhorizons=True` | Supported |
| `autosample` | `autosample=True` | Supported |
| `horizons(numlist)` | *(not exposed)* | Hard-rejected via `**kwargs` |
| `minn(#)` | *(not exposed)* | Hard-rejected |
| `controls(varlist)` | *(not exposed)* | Phase A not implemented |
| `fe(string)` | *(not exposed)* | Phase A uses default `id` + `time` FE |
| `wtr(varlist)` | *(not exposed)* | Hard-rejected |
| `saveestimates`, `saveweights`, `saveresid` | *(not exposed)* | Hard-rejected |

---

## 5. Known Phase A Simplifications

1. **No control covariates** — `controls()`, `unitcontrols()`, `timecontrols()` are not supported.
2. **No custom weighting (`wtr`)** — only simple equal-weighted horizon averages.
3. **No `horizons` subsetting** — `allhorizons` logic computes all `h >= 0`; explicit `horizons()` list not exposed.
4. **No `minn`, `hbalance`, `project`, `hetby`** — not exposed.
5. **DoF adjustment gap** — cluster SEs use the influence-function sum-of-squares without the `reghdfe` small-sample `dof_adj` multiplier.
6. **No pretrend test** — `pretrends()` option not implemented.

---

## 6. 已实现并有明确源码依据

- **样本筛选**：`markout` 逻辑等价实现，剔除 `y`/`id`/`time`/`first_treat` 缺失值。
- **处理指示与事件时间**：`_K`、`_D` 构造与 `did_imputation.ado` L91–98 一致。
- **对照组定义**：`control_mask = (_D == 0)` 对应 never-treated + not-yet-treated。
- **TWFE 估计**：`_fit_twfe()` 的迭代去均值与 `reghdfe` 在双向 FE 下的结果等价（golden 测试 `<1e-5`）。
- **反事实插补**：`Y0 = alpha_i + gamma_t` 对应 `did_imputation.ado` L354–384 的 FE 恢复逻辑。
- **效应计算**：`effect = Y - Y0` 与源码 L393 一致。
- **autosample**：非可插补观测的自动剔除与重归一化逻辑与源码 L461–479 一致。
- **horizon 均值**：各 `tauh` 为对应 horizon 上 treated 的 `effect` 均值。
- **聚类标准误**：插补权重迭代去均值 + 聚类层级 influence function 求和，与源码 SE 构造逻辑一致。

## 7. 已实现，但属于 Phase A 的等价实现

- **TWFE 求解方式**：Stata 调用 `reghdfe`（MAP/稠密 LSDV），Python 使用迭代去均值；对完整面板数据两者数学等价。
- **Cluster SE 小样本修正**：Python 当前未乘 `reghdfe` 的 `dof_adj` 修正因子，SE 数值在 synthetic/real-data 测试中已对齐到可接受容差。

## 8. 未实现或显式拒绝

- `controls()` / `unitcontrols()` / `timecontrols()`
- `wtr()` 自定义权重
- `horizons()` 子集控制（wrapper 硬拒绝）
- `minn()`、`hbalance`、`project`、`hetby`
- `saveestimates`、`saveweights`、`saveresid`
- `pretrends()` 前置趋势检验
- 重复截面（repeated cross-section）
