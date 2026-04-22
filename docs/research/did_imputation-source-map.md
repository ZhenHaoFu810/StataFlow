# `did_imputation` Source-to-Python Mapping

**Version mapped:** November 22, 2023 (local mirror `research/vendor/stata_community/did_imputation/did_imputation-main/`)
**Python target:** `stataflow.estimators.DIDImputation` + `stataflow.compat.stata.did_imputation()`

---

## 1. ADO Entry Points

| Stata File | Program / Line | What it does | Maps to Python |
|------------|----------------|--------------|----------------|
| `did_imputation.ado` | `program define did_imputation, eclass` (L6) | Top-level dispatcher, syntax parsing, option validation, dependency checks (`reghdfe >= 5.7.3`, `ftools >= 2.37.0`) | `stataflow.compat.stata.did_imputation()` wrapper |
| `did_imputation.ado` | `syntax varlist(min=4 max=4) ...` (L8鈥?2) | Parses `y id time first_treat`, plus optional `cluster`, `allhorizons`, `autosample`, `horizons`, `minn`, etc. | `DIDImputation.__init__()` + `fit()` parameter handling |

---

## 2. Core Algorithm 鈫?Python Mapping

### 2.1 Sample Screening

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `did_imputation.ado` | `marksample touse, novarlist` (L18) | Initialize sample indicator | `DIDImputation.fit()` missing-value drop on `[y, id, time, first_treat]` |
| `did_imputation.ado` | `markout touse Y t; markout touse i, strok` (L51鈥?2) | Drop rows with missing key vars | Explicit `df[key_vars].notna().all(axis=1)` mask |
| `did_imputation.ado` | `markout touse cluster, strok` (L23) | Drop missing cluster values | Included in key var screening when `cluster` is passed |

### 2.2 Relative Time and Treatment Indicator Construction

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `did_imputation.ado` | `gen K = (t-ei+shift)/delta if touse` (L91) | Compute event time relative to first treatment | `df["_K"] = df[time] - df[first_treat]` |
| `did_imputation.ado` | `gen D = (K>=0 & !mi(K)) if touse` (L98) | Treatment indicator: 1 if post-treatment and treated | `df["_D"] = (df[time] >= df[first_treat]).astype(int)` with never-treated set to 0 |

### 2.3 TWFE on Control Sample

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `did_imputation.ado` | `reghdfe Y controls if D==0 & touse, a(fe_i fe_t fe) ...` (L344鈥?45) | Run TWFE on never-treated + not-yet-treated to estimate unit and time FEs | `DIDImputation._fit_twfe()` implements iterative demeaning: alternate `alpha_i = mean(y - gamma_t)` and `gamma_t = mean(y - alpha_i)` until convergence |

**Key equivalence:** Stata uses `reghdfe` (MAP/LSDV) to estimate the TWFE. Python's iterative demeaning converges to the identical within-transformed estimates for the two-way FE model.

### 2.4 Impute Counterfactual and Compute Effects

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `did_imputation.ado` | `gen Y0 = ...` (L354鈥?84) | Recover fixed effects from `reghdfe` and build `Y0 = alpha_i + gamma_t + X*beta` for all observations | `df["_Y0"] = df[id].map(alpha_fe) + df[time].map(gamma_fe)` (Phase A omits `controls`) |
| `did_imputation.ado` | `gen effect = Y - Y0 if D==1 & touse` (L393) | Compute treatment effect as actual minus counterfactual for treated units | `df.loc[treated_mask, "_effect"] = y - Y0` |

### 2.5 Autosample and Horizon Selection

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `did_imputation.ado` | `count if mi(effect) & need_imputation` (L451) | Detect observations where FE cannot be imputed | Check `n_imputable == 0`; if so and `autosample=False`, raise `RuntimeError` |
| `did_imputation.ado` | `autosample` branch (L461鈥?79) | Drop non-imputable observations and re-normalize weights | `effective_mask = imputable_mask` when `n_imputable < n_total` and `autosample=True` |
| `did_imputation.ado` | `allhorizons` / `horizons` parsing (L166鈥?07) | Determine which event-time horizons to compute | `allhorizons=True` uses all `h >= 0` found in treated data; default behavior also computes all `h >= 0` in current Python implementation |

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

1. **No control covariates** 鈥?`controls()`, `unitcontrols()`, `timecontrols()` are not supported.
2. **No custom weighting (`wtr`)** 鈥?only simple equal-weighted horizon averages.
3. **No `horizons` subsetting** 鈥?`allhorizons` logic computes all `h >= 0`; explicit `horizons()` list not exposed.
4. **No `minn`, `hbalance`, `project`, `hetby`** 鈥?not exposed.
5. **DoF adjustment gap** 鈥?cluster SEs use the influence-function sum-of-squares without the `reghdfe` small-sample `dof_adj` multiplier.
6. **No pretrend test** 鈥?`pretrends()` option not implemented.

---

## 6. 宸插疄鐜板苟鏈夋槑纭簮鐮佷緷鎹?
- **鏍锋湰绛涢€?*锛歚markout` 閫昏緫绛変环瀹炵幇锛屽墧闄?`y`/`id`/`time`/`first_treat` 缂哄け鍊笺€?- **澶勭悊鎸囩ず涓庝簨浠舵椂闂?*锛歚_K`銆乣_D` 鏋勯€犱笌 `did_imputation.ado` L91鈥?8 涓€鑷淬€?- **瀵圭収缁勫畾涔?*锛歚control_mask = (_D == 0)` 瀵瑰簲 never-treated + not-yet-treated銆?- **TWFE 浼拌**锛歚_fit_twfe()` 鐨勮凯浠ｅ幓鍧囧€间笌 `reghdfe` 鍦ㄥ弻鍚?FE 涓嬬殑缁撴灉绛変环锛坓olden 娴嬭瘯 `<1e-5`锛夈€?- **鍙嶄簨瀹炴彃琛?*锛歚Y0 = alpha_i + gamma_t` 瀵瑰簲 `did_imputation.ado` L354鈥?84 鐨?FE 鎭㈠閫昏緫銆?- **鏁堝簲璁＄畻**锛歚effect = Y - Y0` 涓庢簮鐮?L393 涓€鑷淬€?- **autosample**锛氶潪鍙彃琛ヨ娴嬬殑鑷姩鍓旈櫎涓庨噸褰掍竴鍖栭€昏緫涓庢簮鐮?L461鈥?79 涓€鑷淬€?- **horizon 鍧囧€?*锛氬悇 `tauh` 涓哄搴?horizon 涓?treated 鐨?`effect` 鍧囧€笺€?- **鑱氱被鏍囧噯璇?*锛氭彃琛ユ潈閲嶈凯浠ｅ幓鍧囧€?+ 鑱氱被灞傜骇 influence function 姹傚拰锛屼笌婧愮爜 SE 鏋勯€犻€昏緫涓€鑷淬€?
## 7. 宸插疄鐜帮紝浣嗗睘浜?Phase A 鐨勭瓑浠峰疄鐜?
- **TWFE 姹傝В鏂瑰紡**锛歋tata 璋冪敤 `reghdfe`锛圡AP/绋犲瘑 LSDV锛夛紝Python 浣跨敤杩唬鍘诲潎鍊硷紱瀵瑰畬鏁撮潰鏉挎暟鎹袱鑰呮暟瀛︾瓑浠枫€?- **Cluster SE 灏忔牱鏈慨姝?*锛歅ython 褰撳墠鏈箻 `reghdfe` 鐨?`dof_adj` 淇鍥犲瓙锛孲E 鏁板€煎湪 synthetic/real-data 娴嬭瘯涓凡瀵归綈鍒板彲鎺ュ彈瀹瑰樊銆?
## 8. 鏈疄鐜版垨鏄惧紡鎷掔粷

- `controls()` / `unitcontrols()` / `timecontrols()`
- `wtr()` 鑷畾涔夋潈閲?- `horizons()` 瀛愰泦鎺у埗锛坵rapper 纭嫆缁濓級
- `minn()`銆乣hbalance`銆乣project`銆乣hetby`
- `saveestimates`銆乣saveweights`銆乣saveresid`
- `pretrends()` 鍓嶇疆瓒嬪娍妫€楠?- 閲嶅鎴潰锛坮epeated cross-section锛?