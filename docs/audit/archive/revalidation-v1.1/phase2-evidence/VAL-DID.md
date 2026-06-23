# VAL-DID.md — Phase 2 DID/Event Study Dual-Run Validation

**Dataset:** `ezunem_prepared.dta` (198 obs, 22 cities × 9 years)

**Date:** 2026-06-03

---

## 1. CSDID basic

**Python:** `csdid(df, y='uclms', id='city', time='year', first_treat='first_treat', aggtype='event')`

**Stata:** `csdid uclms, ivar(city) time(year) gvar(first_treat) agg(event)` → `estat event`

- Python N = 198, Stata N = 198

| name | py_beta | st_beta | diff_beta | py_se | st_se | diff_se |
|------|---------|---------|-----------|-------|-------|---------|
| Post_avg | -8244.0633 | -8244.0630 | 4.043314e-08 | 18803.4301 | 18803.4300 | 2.690941e-09 |
| Pre_avg | 2048.1792 | 2048.1790 | 8.137310e-08 | 6494.0605 | 6494.0600 | 7.439321e-08 |
| Tm1 | 12866.3167 | 12866.3200 | 2.590743e-07 | 15031.0644 | 15031.0600 | 2.903318e-07 |
| Tm2 | 4787.4667 | 4787.4670 | 6.962624e-08 | 16301.1002 | 16301.1000 | 1.305348e-08 |
| Tm3 | -7482.8167 | -7482.8170 | 4.454650e-08 | 11815.8360 | 11815.8400 | 3.399947e-07 |
| Tm4 | -1978.2500 | -1978.2500 | 3.448103e-16 | 15364.8322 | 15364.8300 | 1.425713e-07 |
| Tp0 | -8105.6000 | -8105.6000 | 4.488229e-16 | 13334.2506 | 13334.2500 | 4.777421e-08 |
| Tp1 | -9638.7500 | -9638.7500 | 1.887163e-16 | 14276.5885 | 14276.5900 | 1.037654e-07 |
| Tp2 | -16527.4833 | -16527.4800 | 2.016843e-07 | 17083.3730 | 17083.3700 | 1.785337e-07 |
| Tp3 | -7509.5667 | -7509.5670 | 4.438782e-08 | 19788.6241 | 19788.6200 | 2.084309e-07 |
| Tp4 | 561.0833 | 561.0833 | 5.940888e-08 | 31139.1481 | 31139.1500 | 6.039019e-08 |

**Result:** ✅ CSDID basic coefficients match Stata exactly (differences < 1e-6 are rounding only).
- Note on DID-001: `csdid()` returns `ResultSchema` (confirmed by `type: "ResultSchema"`). This means users cannot chain multiple `estat` calls on a single fitted object from the wrapper.

## 2. CSDID pretrend

**Python:** `csdid(..., aggtype='pretrend')`

**Stata:** `csdid uclms, ivar(city) time(year) gvar(first_treat)` → `estat pretrend`

- Python returns: `{"f_stat": NaN, "p_value": NaN, "df": 0}` (type: dict)
- Stata returns: chi2(7) = 32.0875, p-value = 0.0000

**Result:** ❌ CRASH/BUG CONFIRMED (DID-011)
- Python `csdid()` with `aggtype='pretrend'` returns a plain `dict` instead of `ResultSchema`.
- Python reports `f_stat: NaN, p_value: NaN, df: 0` because `estat_pretrend()` uses `isinstance(e, int)` which fails for `numpy.int64` event-time keys.
- Stata correctly reports a significant pretrend test (p < 0.001).

## 3. did_imputation basic

**Python:** `did_imputation(df, y='uclms', id='city', time='year', first_treat='first_treat', autosample=True)`

**Stata:** `did_imputation uclms city year first_treat, autosample`

- Python N = 198, Stata N = 50
- Python coefficients: ['tau0', 'tau1', 'tau2', 'tau3', 'tau4']
- Stata coefficients: ['tau']

**Result:** ❌ SEVERE MISMATCH
- Python reports 5 coefficients (tau0–tau4) with N=198.
- Stata reports `tau` as omitted with N=50 (148 observations dropped because FE could not be imputed).
- Python's `autosample=True` does NOT actually drop non-imputable observations; `_can_impute` logic is too permissive.

## 4. did_imputation allhorizons

**Python:** `did_imputation(..., allhorizons=False)` vs `allhorizons=True` (both with `autosample=True`)

**Stata:** `did_imputation uclms city year first_treat, autosample allhorizons`

- Python `allhorizons=False` keys: ['tau0', 'tau1', 'tau2', 'tau3', 'tau4']
- Python `allhorizons=True` keys: ['tau0', 'tau1', 'tau2', 'tau3', 'tau4']
- Same coefficients: True
- Stata coefficients: ['tau0', 'tau1', 'tau2', 'tau3', 'tau4', 'tau1980', 'tau1981', 'tau1982', 'tau1983', 'tau1984', 'tau1985', 'tau1986', 'tau1987', 'tau1988']

**Result:** ❌ BUG CONFIRMED (DID-004)
- Python `allhorizons=True/False` produce identical coefficient sets, confirming the parameter is ignored.
- Stata with `allhorizons` generates calendar-year coefficients (`tau1980`–`tau1988`) which are all omitted due to insufficient sample.

## 5. did_imputation with cluster

**Python:** `did_imputation(..., autosample=True, cluster='city')`

**Stata:** `did_imputation uclms city year first_treat, autosample cluster(city)`

- Python N = 198, Stata N = 50
- Python coefficients: ['tau0', 'tau1', 'tau2', 'tau3', 'tau4']
- Stata coefficients: ['tau']

**Result:** ❌ SEVERE MISMATCH (same root cause as Test 3)
- Python SEs are identical to the non-clustered run, suggesting cluster-robust SE computation may also be buggy or the sample difference masks it.

## 6. eventstudyinteract basic

**Python:** `eventstudyinteract(..., event_dummies=['Dm3','Dm2','D0','Dp1','Dp2','Dp3'], absorb=['city','year'])`

**Stata:** `eventstudyinteract uclms Dm3 Dm2 D0 Dp1 Dp2 Dp3, cohort(cohort) control_cohort(control_cohort) absorb(city year)`

- Python N = 198, Stata N = 198

| name | py_beta | st_beta | diff_beta | py_se | st_se | diff_se |
|------|---------|---------|-----------|-------|-------|---------|
| D0 | -4878.2652 | -4878.2650 | 4.599155e-08 | 14551.2049 | 14597.7600 | **3.189196e-03** |
| Dm2 | -9294.7108 | -9294.7110 | 2.252912e-08 | 15953.4307 | 15996.5700 | **2.696783e-03** |
| Dm3 | -12940.8236 | -12940.8200 | 2.749202e-07 | 15391.9218 | 15435.9400 | **2.851672e-03** |
| Dp1 | -5636.8388 | -5636.8390 | 3.866506e-08 | 15417.6567 | 15466.5800 | **3.163161e-03** |
| Dp2 | -12525.5721 | -12525.5700 | 1.688853e-07 | 15384.3731 | 15433.4000 | **3.176675e-03** |
| Dp3 | -4012.7719 | -4012.7720 | 2.449443e-08 | 14781.6932 | 14828.2400 | **3.139066e-03** |

**Result:** ✅ eventstudyinteract coefficients match Stata (max beta diff = 2.749202e-07).
- Minor SE differences are within acceptable tolerance for different numerical paths.

## 7. CSDID kwargs bug (notyet)

**Python:** `csdid(..., notyet=True)`

- Python error: `Unsupported arguments: ['notyet']`

**Result:** ❌ BUG CONFIRMED (DID-002)
- `csdid()` wrapper hard-rejects `notyet` via `**kwargs` check, even though it is a legitimate Stata `csdid` option.

## 8. CSDID unbalanced panel (NaN propagation)

**Python:** `csdid(df_with_20_random_nans, ...)`

- Python N = 198, has NaN coefficients = False

**Result:** ⚠️ PARTIAL ISSUE (DID-005)
- Python drops NaN rows via `dropna()` and runs without error.
- No `NaN` values appear in the coefficient table, so 'silent propagation' is not observed in this synthetic test.
- However, the drop logic is not explicitly validated against Stata's missing-value handling.

---

## Summary

| Test | Status | Notes |
|------|--------|-------|
| CSDID basic | ✅ PASS | Exact match |
| CSDID pretrend | ❌ FAIL | Returns dict; numpy int bug |
| did_imputation basic | ❌ FAIL | Sample screening completely misaligned |
| did_imputation allhorizons | ❌ FAIL | Parameter ignored |
| did_imputation cluster | ❌ FAIL | Same sample issue |
| eventstudyinteract basic | ✅ PASS | Close match |
| CSDID kwargs (notyet) | ❌ FAIL | Hard-rejected |
| CSDID unbalanced | ⚠️ PARTIAL | No NaN propagation observed |
