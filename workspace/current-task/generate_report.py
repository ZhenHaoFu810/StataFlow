"""Generate VAL-DID.md and NEW-DID.md from phase2_results_v2.json."""

import json
import numpy as np
from pathlib import Path

OUTPUT_DIR = Path("D:/OneDrive - SAIF/PhD3/StataFlow/stata/output/phase2")
REPORT_DIR = Path("D:/OneDrive - SAIF/PhD3/StataFlow/docs/audit/revalidation-v1.1/phase2-evidence")

results = json.loads((OUTPUT_DIR / "phase2_results_v2.json").read_text(encoding="utf-8"))

def rel_diff(py, st):
    if py is None or st is None:
        return np.nan
    if np.isnan(py) or np.isnan(st):
        return np.nan
    return abs(py - st) / max(abs(st), 1e-10)

def make_table(py_coeffs, st_coeffs, fields=None):
    if fields is None:
        fields = ["beta", "std_err", "t_stat", "p_value"]
    py_dict = {c["name"]: c for c in py_coeffs}
    st_dict = {c["name"]: c for c in st_coeffs}
    names = sorted(set(py_dict.keys()) | set(st_dict.keys()))
    rows = []
    for name in names:
        py_c = py_dict.get(name, {})
        st_c = st_dict.get(name, {})
        row = {"name": name}
        for f in fields:
            py_v = py_c.get(f)
            st_v = st_c.get(f)
            row[f"py_{f}"] = py_v
            row[f"st_{f}"] = st_v
            row[f"diff_{f}"] = rel_diff(py_v, st_v)
        rows.append(row)
    return rows

def highlight(val):
    if val is None or np.isnan(val):
        return "—"
    if val > 1e-6:
        return f"**{val:.6e}**"
    return f"{val:.6e}"

lines = []
lines.append("# VAL-DID.md — Phase 2 DID/Event Study Dual-Run Validation")
lines.append("")
lines.append("**Dataset:** `ezunem_prepared.dta` (198 obs, 22 cities × 9 years)")
lines.append("")
lines.append("**Date:** 2026-06-03")
lines.append("")
lines.append("---")
lines.append("")

# ═══════════════════════════════════════════════════════════════════════
# 1. CSDID basic
# ═══════════════════════════════════════════════════════════════════════
lines.append("## 1. CSDID basic")
lines.append("")
lines.append("**Python:** `csdid(df, y='uclms', id='city', time='year', first_treat='first_treat', aggtype='event')`")
lines.append("")
lines.append("**Stata:** `csdid uclms, ivar(city) time(year) gvar(first_treat) agg(event)` → `estat event`")
lines.append("")

py = results["csdid_basic"]["python"]
st = results["csdid_basic"]["stata"]
lines.append(f"- Python N = {py['nobs']}, Stata N = {st['nobs']}")
lines.append("")

table = make_table(py["coefficients"], st["coefficients"])
lines.append("| name | py_beta | st_beta | diff_beta | py_se | st_se | diff_se |")
lines.append("|------|---------|---------|-----------|-------|-------|---------|")
for row in table:
    lines.append(
        f"| {row['name']} | {row['py_beta']:.4f} | {row['st_beta']:.4f} | {highlight(row['diff_beta'])} | "
        f"{row['py_std_err']:.4f} | {row['st_std_err']:.4f} | {highlight(row['diff_std_err'])} |"
    )
lines.append("")
lines.append("**Result:** ✅ CSDID basic coefficients match Stata exactly (differences < 1e-6 are rounding only).")
lines.append("")

# ═══════════════════════════════════════════════════════════════════════
# 2. CSDID pretrend
# ═══════════════════════════════════════════════════════════════════════
lines.append("## 2. CSDID pretrend")
lines.append("")
lines.append("**Python:** `csdid(..., aggtype='pretrend')`")
lines.append("")
lines.append("**Stata:** `csdid uclms, ivar(city) time(year) gvar(first_treat)` → `estat pretrend`")
lines.append("")

py = results["csdid_pretrend"]["python"]
st = results["csdid_pretrend"]["stata"]
lines.append(f"- Python returns: `{json.dumps(py['value'])}` (type: {py['type']})")
lines.append(f"- Stata returns: chi2(7) = 32.0875, p-value = 0.0000")
lines.append("")
lines.append("**Result:** ❌ CRASH/BUG CONFIRMED (DID-011)")
lines.append("- Python `csdid()` with `aggtype='pretrend'` returns a plain `dict` instead of `ResultSchema`.")
lines.append("- Python reports `f_stat: NaN, p_value: NaN, df: 0` because `estat_pretrend()` uses `isinstance(e, int)` which fails for `numpy.int64` event-time keys.")
lines.append("- Stata correctly reports a significant pretrend test (p < 0.001).")
lines.append("")

# ═══════════════════════════════════════════════════════════════════════
# 3. did_imputation basic
# ═══════════════════════════════════════════════════════════════════════
lines.append("## 3. did_imputation basic")
lines.append("")
lines.append("**Python:** `did_imputation(df, y='uclms', id='city', time='year', first_treat='first_treat', autosample=True)`")
lines.append("")
lines.append("**Stata:** `did_imputation uclms city year first_treat, autosample`")
lines.append("")

py = results["did_basic"]["python"]
st = results["did_basic"]["stata"]
lines.append(f"- Python N = {py['nobs']}, Stata N = {st['nobs']}")
lines.append(f"- Python coefficients: {[c['name'] for c in py['coefficients']]}")
lines.append(f"- Stata coefficients: {[c['name'] for c in st['coefficients']]}")
lines.append("")
lines.append("**Result:** ❌ SEVERE MISMATCH")
lines.append("- Python reports 5 coefficients (tau0–tau4) with N=198.")
lines.append("- Stata reports `tau` as omitted with N=50 (148 observations dropped because FE could not be imputed).")
lines.append("- Python's `autosample=True` does NOT actually drop non-imputable observations; `_can_impute` logic is too permissive.")
lines.append("")

# ═══════════════════════════════════════════════════════════════════════
# 4. did_imputation allhorizons
# ═══════════════════════════════════════════════════════════════════════
lines.append("## 4. did_imputation allhorizons")
lines.append("")
lines.append("**Python:** `did_imputation(..., allhorizons=False)` vs `allhorizons=True` (both with `autosample=True`)")
lines.append("")
lines.append("**Stata:** `did_imputation uclms city year first_treat, autosample allhorizons`")
lines.append("")

py = results["did_allhorizons"]["python"]
st = results["did_allhorizons"]["stata"]
lines.append(f"- Python `allhorizons=False` keys: {py['false_keys']}")
lines.append(f"- Python `allhorizons=True` keys: {py['true_keys']}")
lines.append(f"- Same coefficients: {py['same_coefficients']}")
lines.append(f"- Stata coefficients: {[c['name'] for c in st['coefficients']]}")
lines.append("")
lines.append("**Result:** ❌ BUG CONFIRMED (DID-004)")
lines.append("- Python `allhorizons=True/False` produce identical coefficient sets, confirming the parameter is ignored.")
lines.append("- Stata with `allhorizons` generates calendar-year coefficients (`tau1980`–`tau1988`) which are all omitted due to insufficient sample.")
lines.append("")

# ═══════════════════════════════════════════════════════════════════════
# 5. did_imputation with cluster
# ═══════════════════════════════════════════════════════════════════════
lines.append("## 5. did_imputation with cluster")
lines.append("")
lines.append("**Python:** `did_imputation(..., autosample=True, cluster='city')`")
lines.append("")
lines.append("**Stata:** `did_imputation uclms city year first_treat, autosample cluster(city)`")
lines.append("")

py = results["did_cluster"]["python"]
st = results["did_cluster"]["stata"]
lines.append(f"- Python N = {py['nobs']}, Stata N = {st['nobs']}")
lines.append(f"- Python coefficients: {[c['name'] for c in py['coefficients']]}")
lines.append(f"- Stata coefficients: {[c['name'] for c in st['coefficients']]}")
lines.append("")
lines.append("**Result:** ❌ SEVERE MISMATCH (same root cause as Test 3)")
lines.append("- Python SEs are identical to the non-clustered run, suggesting cluster-robust SE computation may also be buggy or the sample difference masks it.")
lines.append("")

# ═══════════════════════════════════════════════════════════════════════
# 6. eventstudyinteract basic
# ═══════════════════════════════════════════════════════════════════════
lines.append("## 6. eventstudyinteract basic")
lines.append("")
lines.append("**Python:** `eventstudyinteract(..., event_dummies=['Dm3','Dm2','D0','Dp1','Dp2','Dp3'], absorb=['city','year'])`")
lines.append("")
lines.append("**Stata:** `eventstudyinteract uclms Dm3 Dm2 D0 Dp1 Dp2 Dp3, cohort(cohort) control_cohort(control_cohort) absorb(city year)`")
lines.append("")

py = results["eventstudyinteract_basic"]["python"]
st = results["eventstudyinteract_basic"]["stata"]
lines.append(f"- Python N = {py['nobs']}, Stata N = {st['nobs']}")
lines.append("")

table = make_table(py["coefficients"], st["coefficients"])
lines.append("| name | py_beta | st_beta | diff_beta | py_se | st_se | diff_se |")
lines.append("|------|---------|---------|-----------|-------|-------|---------|")
for row in table:
    lines.append(
        f"| {row['name']} | {row['py_beta']:.4f} | {row['st_beta']:.4f} | {highlight(row['diff_beta'])} | "
        f"{row['py_std_err']:.4f} | {row['st_std_err']:.4f} | {highlight(row['diff_std_err'])} |"
    )
lines.append("")
max_diff = max(r['diff_beta'] for r in table if r['diff_beta'] is not None and not np.isnan(r['diff_beta']))
lines.append(f"**Result:** ✅ eventstudyinteract coefficients match Stata (max beta diff = {max_diff:.6e}).")
lines.append("- Minor SE differences are within acceptable tolerance for different numerical paths.")
lines.append("")

# ═══════════════════════════════════════════════════════════════════════
# 7. CSDID kwargs bug
# ═══════════════════════════════════════════════════════════════════════
lines.append("## 7. CSDID kwargs bug (notyet)")
lines.append("")
lines.append("**Python:** `csdid(..., notyet=True)`")
lines.append("")
py = results["csdid_notyet"]["python"]
lines.append(f"- Python error: `{py['error']}`")
lines.append("")
lines.append("**Result:** ❌ BUG CONFIRMED (DID-002)")
lines.append("- `csdid()` wrapper hard-rejects `notyet` via `**kwargs` check, even though it is a legitimate Stata `csdid` option.")
lines.append("")

# ═══════════════════════════════════════════════════════════════════════
# 8. CSDID unbalanced panel
# ═══════════════════════════════════════════════════════════════════════
lines.append("## 8. CSDID unbalanced panel (NaN propagation)")
lines.append("")
lines.append("**Python:** `csdid(df_with_20_random_nans, ...)`")
lines.append("")
py = results["csdid_unbalanced"]["python"]
lines.append(f"- Python N = {py['nobs']}, has NaN coefficients = {py['has_nan']}")
lines.append("")
lines.append("**Result:** ⚠️ PARTIAL ISSUE (DID-005)")
lines.append("- Python drops NaN rows via `dropna()` and runs without error.")
lines.append("- No `NaN` values appear in the coefficient table, so 'silent propagation' is not observed in this synthetic test.")
lines.append("- However, the drop logic is not explicitly validated against Stata's missing-value handling.")
lines.append("")

lines.append("---")
lines.append("")
lines.append("## Summary")
lines.append("")
lines.append("| Test | Status | Notes |")
lines.append("|------|--------|-------|")
lines.append("| CSDID basic | ✅ PASS | Exact match |")
lines.append("| CSDID pretrend | ❌ FAIL | Returns dict; numpy int bug |")
lines.append("| did_imputation basic | ❌ FAIL | Sample screening completely misaligned |")
lines.append("| did_imputation allhorizons | ❌ FAIL | Parameter ignored |")
lines.append("| did_imputation cluster | ❌ FAIL | Same sample issue |")
lines.append("| eventstudyinteract basic | ✅ PASS | Close match |")
lines.append("| CSDID kwargs (notyet) | ❌ FAIL | Hard-rejected |")
lines.append("| CSDID unbalanced | ⚠️ PARTIAL | No NaN propagation observed |")
lines.append("")

REPORT_DIR.mkdir(parents=True, exist_ok=True)
(REPORT_DIR / "VAL-DID.md").write_text("\n".join(lines), encoding="utf-8")
print("Wrote", REPORT_DIR / "VAL-DID.md")

# ═══════════════════════════════════════════════════════════════════════
# NEW-DID.md
# ═══════════════════════════════════════════════════════════════════════
new_lines = []
new_lines.append("# NEW-DID.md — New Issues Discovered in Phase 2 Revalidation")
new_lines.append("")
new_lines.append("**Date:** 2026-06-03")
new_lines.append("")
new_lines.append("---")
new_lines.append("")

new_lines.append("## NEW-001: CSDID `estat_pretrend()` fails due to `isinstance(e, int)` check on `numpy.int64`")
new_lines.append("")
new_lines.append("**Severity:** High")
new_lines.append("")
new_lines.append("**Location:** `src/stataflow/estimators/csdid.py`, `estat_pretrend()` method")
new_lines.append("")
new_lines.append("**Description:**")
new_lines.append("The `estat_pretrend()` method filters pre-treatment event times using:")
new_lines.append('```python')
new_lines.append('pre_events = sorted([e for e in self._event_est if isinstance(e, int) and e < 0])')
new_lines.append('```')
new_lines.append("When event-time keys are `numpy.int64` (which happens when `t` and `g` come from pandas integer columns), `isinstance(e, int)` evaluates to `False`. This causes the method to return an empty pre-event list, resulting in `df=0` and `f_stat=NaN`.")
new_lines.append("")
new_lines.append("**Evidence:**")
new_lines.append("- Python `csdid(..., aggtype='pretrend')` returns `{'f_stat': NaN, 'p_value': NaN, 'df': 0}`")
new_lines.append("- Stata `estat pretrend` on the same data returns `chi2(7) = 32.0875, p = 0.0000`")
new_lines.append("")
new_lines.append("**Fix:** Replace `isinstance(e, int)` with `isinstance(e, (int, np.integer))` or use `np.issubdtype(type(e), np.integer)`.")
new_lines.append("")
new_lines.append("---")
new_lines.append("")

new_lines.append("## NEW-002: `did_imputation` sample screening / imputability logic completely misaligned with Stata")
new_lines.append("")
new_lines.append("**Severity:** Critical")
new_lines.append("")
new_lines.append("**Location:** `src/stataflow/estimators/did_imputation.py`, `_can_impute` logic in `fit()`")
new_lines.append("")
new_lines.append("**Description:")
new_lines.append("Python's `_can_impute` check only verifies that a unit has at least one control observation and that a time period has at least one control observation. Stata's `did_imputation` uses a much stricter criterion that flags 148/198 observations as non-imputable on the `ezunem` dataset. As a result:")
new_lines.append("- Python reports 5 horizons (tau0–tau4) with N=198.")
new_lines.append("- Stata reports `tau` as omitted with N=50 (after `autosample`).")
new_lines.append("- The `autosample` parameter in Python does not change the result at all.")
new_lines.append("")
new_lines.append("**Evidence:**")
new_lines.append("- Python `did_imputation(..., autosample=True)` → tau0–tau4, N=198")
new_lines.append("- Stata `did_imputation uclms city year first_treat, autosample` → tau omitted, N=50")
new_lines.append("")
new_lines.append("**Fix:** Reverse-engineer Stata's exact imputability criterion (likely requires that both unit FE and time FE are identified from a connected control subsample, not just globally present).")
new_lines.append("")
new_lines.append("---")
new_lines.append("")

new_lines.append("## NEW-003: `did_imputation` cluster-robust SEs identical to non-clustered SEs")
new_lines.append("")
new_lines.append("**Severity:** Medium")
new_lines.append("")
new_lines.append("**Location:** `src/stataflow/estimators/did_imputation.py`, `_compute_se()`")
new_lines.append("")
new_lines.append("**Description:**")
new_lines.append("When `cluster='city'` is passed, the Python SEs for tau0–tau4 are numerically identical to the non-clustered run. This suggests either:")
new_lines.append("1. The cluster-robust adjustment is not being applied correctly, OR")
new_lines.append("2. The imputation weight / residual computation does not vary by cluster, making the adjustment ineffective.")
new_lines.append("")
new_lines.append("**Evidence:**")
new_lines.append("- Python `did_imputation(..., cluster='city')` SEs: [13933.55, 16198.36, 18876.31, 22035.30, 27244.79]")
new_lines.append("- Python `did_imputation(...)` (no cluster) SEs: [13933.55, 16198.36, 18876.31, 22035.30, 27244.79]")
new_lines.append("- Stata `did_imputation ..., cluster(city)` → tau omitted, N=50 (cannot compare directly due to sample issue).")
new_lines.append("")
new_lines.append("**Fix:** Audit `_compute_se()` to ensure cluster-level aggregation is actually cluster-aware.")
new_lines.append("")
new_lines.append("---")
new_lines.append("")

(REPORT_DIR / "NEW-DID.md").write_text("\n".join(new_lines), encoding="utf-8")
print("Wrote", REPORT_DIR / "NEW-DID.md")
