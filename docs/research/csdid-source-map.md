# `csdid` Source-to-Python Mapping

**Version mapped:** v1.81 (local Stata installation `/c/Users/fzh/ado/plus/c/csdid.ado`, plus `csdid_estat.ado`)
**Python target:** `stataflow.estimators.CSDID` + `stataflow.compat.stata.csdid()`
**Paper:** Callaway \& Sant'Anna (2021) "Difference-in-Differences with Multiple Time Periods"

---

## 1. ADO Entry Points

| Stata File | Program / Line | What it does | Maps to Python |
|------------|----------------|--------------|----------------|
| `csdid.ado` | `program csdid` (L140) | Top-level dispatcher, version check, drdid dependency check, replay handler | `stataflow.compat.stata.csdid()` wrapper |
| `csdid.ado` | `program csdid_r` (L363) | Main estimation program. Syntax parsing, sample marking, method selection, aggregation dispatch | `CSDID.__init__()` + `fit()` parameter handling |
| `csdid.ado` | `syntax ...` (L364鈥?85) | Parses `varlist(y xvars)`, `ivar()`, `time()`, `gvar()`, `cluster()`, `notyet`, `method()`, `agg()`, `wboot`, etc. | `CSDID.__init__()` and `fit()` parameters |
| `csdid_estat.ado` | `program csdid_estat` (L15) | Post-estimation aggregator dispatcher (`event`, `simple`, `group`, `calendar`, `attgt`, `pretrend`) | `CSDID.estat_event()` (Python implements only `event` aggregation) |

---

## 2. Core Algorithm to Python Mapping

### 2.1 Sample Screening

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `csdid.ado` | `marksample touse` (L390) | Initialize sample indicator | `CSDID.fit()` missing-value drop on `[y, id, time, first_treat]` |
| `csdid.ado` | `markout touse ivar time gvar y xvar cluster` (L393) | Drop rows with missing key vars | Explicit `df[key_vars].notna().all(axis=1)` mask |
| `csdid.ado` | `mata:data_check(time, gvar, touse)` (L448) | Validate time/gvar structure, detect never-treated, compute time delta | Python computes `cohorts`, `years`, `min_year` from data directly |
| `csdid.ado` | Not-yet-treated fallback (L451鈥?61) | If no never-treated (`no_notyet==0`), auto-switch to not-yet-treated control group | Python `has_never_treated` flag with identical fallback logic (L74鈥?2) |
| `csdid.ado` | Drop always-treated (L493鈥?97) | `replace touse=0 if (gvar<=mintime) \& (gvar>0)` | Python implicitly handles this because `base < min_year` check skips invalid pairs |

### 2.2 ATT(g,t) Computation (method="reg")

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `csdid.ado` | Loop over `glev` x `tlev` (L569鈥? | For each cohort `g` and time `t`, define control group (never-treated or not-yet-treated), run `drdid` with `method(reg)` | Python computes ATT(g,t) directly without calling `drdid`: `att = (mu_g_t - mu_c_t) - (mu_g_base - mu_c_base)` |
| `csdid.ado` | Control group selection (L576鈥?83) | `gsel = inlist(gvar, 0, i)` for never-treated; extended with `gvar > max(i,j)` for not-yet-treated | Python `control_mask` uses identical logic (L79鈥?2) |
| `csdid.ado` | Base period selection | `time1` is base: `t-1` for pre-treatment, `g-1` for post-treatment | Python identical: `base = t-1 if t < g else g-1` (L88鈥?1) |
| `csdid.ado` | `drdid ... method(reg)` (L589) | Calls `drdid` which internally runs regression adjustment | Python bypasses `drdid` and computes sample means directly, which is mathematically equivalent for `method(reg)` with no covariates |

**Key equivalence:** For `method="reg"` with no covariates, `drdid` computes ATT(g,t) as the difference-in-differences of group means. Python implements the same formula directly. When covariates are absent, regression adjustment collapses to sample means.

### 2.3 Influence Functions

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `csdid.ado` | `drdid` IF construction (internal to drdid.ado) | Unit-level influence function for each ATT(g,t) | Python `_compute_if()` (L112鈥?34): `term = (1/N_g)*((y_t - mu_g_t) - (y_base - mu_g_base))` for treated, minus `(1/N_c)*((y_t - mu_c_t) - (y_base - mu_c_base))` for controls |
| `csdid.ado` | RIF scaling in `makerif2` (L1008鈥?014) | `rifgt = (rifgt - mean_y) * exp_factor + mean_y` where `exp_factor = rows(rifgt)/colnonmissing(rifgt)` | Python `rifgt[(g,t)] = {u: n_units_total * if_gt[(g,t)][u] + att for u in units}` (L187), matching the n-times scaling |

### 2.4 Event Study Aggregation (aggte)

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `csdid.ado` | `makerif2` event branch (L1179鈥?230) | Select RIFs by event time `e = t - g`, run `aggte` for each event horizon, then `aggte` over pre/post averages | Python `_aggte()` (L190鈥?01) replicates the Mata `aggte` function: `atte = sum(mn_attg * mn_wgt) / sum(mn_wgt)`, `rif_event = rowsum(r1 + r2 - r3) + atte` |
| `csdid.ado` | Mata `aggte` (L1320鈥?334) | `mn_attg = mean(attg)`, `mn_wgt = mean(wgt)`, `atte = sum(mn_attg :* mn_wgt) / sum(mn_wgt)`, then delta-method RIF | Python `_aggte` identical: `mn_attg = ag_rif.mean(axis=0)`, `mn_wgt = ag_wt.mean(axis=0)`, `atte = np.sum(mn_attg * mn_wgt) / np.sum(mn_wgt)` |
| `csdid.ado` | `event_list()` (L962) | Build unique event-time list from all `(g,t)` pairs | Python `event_map` dict built by iterating `att_gt` keys (L171鈥?74) |
| `csdid.ado` | Pre_avg / Post_avg (L1224鈥?225) | `aggte(select(aux, iit==0), J(...,1))` for pre, `aggte(select(aux, iit), J(...,1))` for post | Python identical: OLS-style equal-weight aggregation over pre/post event RIFs (L226鈥?51) |

### 2.5 Standard Errors

| Source | Function / Lines | Logic | Python Equivalent |
|--------|------------------|-------|-------------------|
| `csdid.ado` | `make_tbl` (L1244) | `bb = mean(rif)`, `VV` computed via cluster-sum of squared RIF deviations | Python `event_se[e] = np.sqrt(np.sum(if_event ** 2)) / n_units_total` (L222), dividing by `n^2` to match Stata's SE formula |
| `csdid.ado` | Cluster SE in `make_tbl` | Within-cluster sum of RIFs, then squared sum across clusters | Python `_event_se` uses unit-level IF squared sum divided by `n_units_total` to match the RIF scaling |

---

## 3. Post-estimation

| Stata Command | Description | Python Equivalent |
|---------------|-------------|-------------------|
| `csdid_estat event` | Event-study dynamic effects aggregation | `CSDID.estat_event()` returns `ResultSchema` with `Pre_avg`, `Post_avg`, `Tm*`, `Tp*` coefficients |
| `csdid_estat simple` | Simple average ATT | **Not implemented** |
| `csdid_estat group` | Group-average ATT | **Not implemented** |
| `csdid_estat calendar` | Calendar-time average ATT | **Not implemented** |
| `csdid_estat pretrend` | Pre-trend test (chi2) | **Not implemented** |

---

## 4. Wrapper Parameter Matrix

| Stata Option | Wrapper Parameter | Python Behavior |
|--------------|-------------------|-----------------|
| `varlist(y)` | `y` | Required |
| `ivar(idvar)` | `id` | Required |
| `time(timevar)` | `time` | Required |
| `gvar(first_treat)` | `first_treat` | Required |
| `method(str)` | `method` | Only `"reg"` supported; `"dr"`, `"ipw"`, etc. hard-rejected via `ValueError` |
| `vce(cluster)` | `vce` | Only `"cluster"` supported (implicitly via `cluster` parameter) |
| `cluster(varname)` | `cluster` | Supported; defaults to `id` |
| `notyet` | *(not exposed)* | Python auto-detects never-treated absence and falls back automatically |
| `agg(str)` | *(not exposed)* | Python only implements `event` aggregation via `estat_event()` |
| `wboot`, `reps`, `rseed` | *(not exposed)* | Wild bootstrap not implemented |
| `window`, `from`, `long` | *(not exposed)* | Hard-rejected via `**kwargs` |
| `saverif`, `replace` | *(not exposed)* | Hard-rejected |

---

## 5. Known Phase A Simplifications

1. **Only `method="reg"`** 鈥?`drimp`, `dripw`, `ipw`, `stdipw` are not supported.
2. **No covariates (`xvar`)** 鈥?`csdid.ado` allows RHS controls; Python ignores them.
3. **Only `agg="event"`** 鈥?`simple`, `group`, `calendar`, `attgt`, `pretrend` aggregations not exposed.
4. **No wild bootstrap** 鈥?`wboot`, `reps`, `rseed`, `wbtype` not supported.
5. **No `window` / `from` / `long` / `long2`** 鈥?event-study uses all available horizons.
6. **No `saverif` / `replace`** 鈥?RIF saving not supported.
7. **No always-treated explicit drop** 鈥?handled implicitly via base-period validity check.
8. **Panel balance check skipped** 鈥?Python assumes balanced-ish panel; Stata checks `isbalanced()`.

---

## 6. Implemented and Source-Backed

- **鏍锋湰绛涢€?*: `markout` logic equivalent; missing values in `y`/`id`/`time`/`first_treat` dropped.
- **瀵圭収缁勫畾涔?*: Never-treated default, not-yet-treated fallback, identical to `csdid.ado` L451鈥?61 and L576鈥?83.
- **ATT(g,t) 璁＄畻**: Direct DiD of sample means for `method(reg)` with no covariates, equivalent to `drdid` regression adjustment in this restricted case.
- **Base period 閫夋嫨**: `t-1` for pre, `g-1` for post, matching Stata logic.
- **Influence function 鏋勯€?*: Unit-level IF with treated/control mean-deviation terms, matching `drdid` IF structure.
- **RIF scaling**: `n_units_total * IF + att` to match Stata's `exp_factor` scaling in `makerif2`.
- **Event study 鑱氬悎**: `_aggte()` replicates Mata `aggte()` function exactly (mean-weighted average with delta-method RIF).
- **Pre_avg / Post_avg**: Equal-weight aggregation over pre/post event RIFs, matching `makerif2` L1224鈥?225.
- **鏍囧噯璇绠?*: Unit-level IF squared sum divided by `n`, matching Stata's RIF-based SE formula.

---

## 7. Implemented but Phase A Equivalent

- **ATT(g,t) 姹傝В鏂瑰紡**: Stata calls `drdid` (which runs internal regression/GLM); Python computes group means directly. With no covariates and `method(reg)`, these are mathematically equivalent.
- **RIF 鏋勯€?*: Python builds IFs from first principles rather than extracting from `drdid`'s `e(RIF)` matrices.
- **Cluster SE 鍙ｅ緞**: Python uses unit-level RIF aggregation; Stata's `make_tbl` applies additional cluster-level grouping. For `cluster=id`, both reduce to the same formula.

---

## 8. Not Implemented or Explicitly Rejected

- `method="drimp"`, `"dripw"`, `"ipw"`, `"stdipw"`
- Covariates (`xvar` in varlist)
- `agg="simple"`, `"group"`, `"calendar"`, `"attgt"`, `"pretrend"`
- Wild bootstrap (`wboot`, `reps`, `rseed`, `wbtype`)
- `window()`, `from()`, `long`, `long2`
- `saverif()`, `replace`
- `notyet` explicit option (Python auto-detects)
- Panel balance checks (`isbalanced`)
- Always-treated explicit warnings
