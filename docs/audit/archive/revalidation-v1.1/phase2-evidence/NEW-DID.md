# NEW-DID.md — New Issues Discovered in Phase 2 Revalidation

**Date:** 2026-06-03

---

## NEW-001: CSDID `estat_pretrend()` fails due to `isinstance(e, int)` check on `numpy.int64`

**Severity:** High

**Location:** `src/stataflow/estimators/csdid.py`, `estat_pretrend()` method

**Description:**
The `estat_pretrend()` method filters pre-treatment event times using:
```python
pre_events = sorted([e for e in self._event_est if isinstance(e, int) and e < 0])
```
When event-time keys are `numpy.int64` (which happens when `t` and `g` come from pandas integer columns), `isinstance(e, int)` evaluates to `False`. This causes the method to return an empty pre-event list, resulting in `df=0` and `f_stat=NaN`.

**Evidence:**
- Python `csdid(..., aggtype='pretrend')` returns `{'f_stat': NaN, 'p_value': NaN, 'df': 0}`
- Stata `estat pretrend` on the same data returns `chi2(7) = 32.0875, p = 0.0000`

**Fix:** Replace `isinstance(e, int)` with `isinstance(e, (int, np.integer))` or use `np.issubdtype(type(e), np.integer)`.

---

## NEW-002: `did_imputation` sample screening / imputability logic completely misaligned with Stata

**Severity:** Critical

**Location:** `src/stataflow/estimators/did_imputation.py`, `_can_impute` logic in `fit()`

**Description:**
Python's `_can_impute` check only verifies that a unit has at least one control observation and that a time period has at least one control observation. Stata's `did_imputation` uses a much stricter criterion that flags 148/198 observations as non-imputable on the `ezunem` dataset. As a result:
- Python reports 5 horizons (tau0–tau4) with N=198.
- Stata reports `tau` as omitted with N=50 (after `autosample`).
- The `autosample` parameter in Python does not change the result at all.

**Evidence:**
- Python `did_imputation(..., autosample=True)` → tau0–tau4, N=198
- Stata `did_imputation uclms city year first_treat, autosample` → tau omitted, N=50

**Fix:** Reverse-engineer Stata's exact imputability criterion (likely requires that both unit FE and time FE are identified from a connected control subsample, not just globally present).

---

## NEW-003: `did_imputation` cluster-robust SEs identical to non-clustered SEs

**Severity:** Medium

**Location:** `src/stataflow/estimators/did_imputation.py`, `_compute_se()`

**Description:**
When `cluster='city'` is passed, the Python SEs for tau0–tau4 are numerically identical to the non-clustered run. This suggests either:
1. The cluster-robust adjustment is not being applied correctly, OR
2. The imputation weight / residual computation does not vary by cluster, making the adjustment ineffective.

**Evidence:**
- Python `did_imputation(..., cluster='city')` SEs: [13933.55, 16198.36, 18876.31, 22035.30, 27244.79]
- Python `did_imputation(...)` (no cluster) SEs: [13933.55, 16198.36, 18876.31, 22035.30, 27244.79]
- Stata `did_imputation ..., cluster(city)` → tau omitted, N=50 (cannot compare directly due to sample issue).

**Fix:** Audit `_compute_se()` to ensure cluster-level aggregation is actually cluster-aware.

---
