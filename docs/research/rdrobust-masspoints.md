# RD Robust Mass Points Handling — Research Archive

**Version researched:** `rdrobust` v10.0.0 (2025-06-30)
**Stata source:** `rdrobust.ado` L178 (default), L273–279 (NN pre-sort), L353, L380–395 (masspoints detection + adjust), L398 (c_bw adjustment), L998 (output warning)
**Reference:** CCT (2014a, 2016b)
**Python target:** `stataflow.estimators.rdrobust.RDRobust.fit()`

---

## 1. Syntax and Default

**Source:** L178

```stata
if ("`masspoints'"=="") local masspoints = "adjust"
```

Three valid values: `"adjust"`, `"check"`, `"off"`. Default is `"adjust"`.

---

## 2. Detection Logic

**Source:** L380–395

### 2.1 Unique Value Counting

```mata
X_uniq_l = sort(uniqrows(X_l), -1)  // descending sort
X_uniq_r = uniqrows(X_r)            // ascending (default)
M_l = length(X_uniq_l)
M_r = length(X_uniq_r)
M = M_l + M_r
```

`M_l`, `M_r` = number of unique running variable values on each side.

### 2.2 Mass Points Threshold

```mata
mass_l = 1 - M_l/N_l
mass_r = 1 - M_r/N_r
if (mass_l >= 0.2 | mass_r >= 0.2){
    masspoints_found = 1
    display("Mass points detected in the running variable.")
}
```

A side has mass points if **fewer than 80% of observations have unique X values** on that side. In other words, if more than 20% of observations share an X value with at least one other observation, mass points are flagged.

### 2.3 Pre-Sort Requirement

**Source:** L273–279

```stata
if ("`vce_select'"=="nn" | "`masspoints'"=="check" | "`masspoints'"=="adjust") {
    sort `x', stable
    ...
}
```

The data must be sorted by running variable for NN residual computation and mass points detection.

---

## 3. Mode: `check`

**Source:** L393

```stata
if ("`masspoints'"=="check") display("Try using option masspoints(adjust).")
```

When `masspoints="check"`:
- Detects mass points and reports a warning
- Does NOT adjust the bandwidth computation
- The user is advised to use `masspoints(adjust)` instead

Output flag: `st_numscalar("masspoints_found", masspoints_found)`

---

## 4. Mode: `adjust`

**Source:** L392, L398

### 4.1 Automatic bwcheck

```stata
if ("`masspoints'"=="adjust" & "`bwcheck'"=="0") bwcheck = 10
```

When mass points are detected AND `masspoints="adjust"`, the `bwcheck` parameter is automatically set to 10 (if not already set by user).

### 4.2 Pilot Bandwidth Adjustment (L398)

```stata
if ("`masspoints'"=="adjust") c_bw = C_c * BWp * M^(-1/5)
```

With adjustment, the pilot bandwidth uses **M** (number of unique X values) instead of **N** (total observations) in the scaling factor:

```
Standard:  c_bw = C_c * BWp * N^(-1/5)
Adjusted:  c_bw = C_c * BWp * M^(-1/5)
```

Since `M ≤ N`, the adjusted bandwidth is **larger**, which helps ensure sufficient unique X values within the bandwidth window.

### 4.3 bwcheck Enforcement (L403–409)

After mass points adjustment:
```mata
if (bwcheck > 0) {
    bwcheck_l = min((bwcheck, M_l))
    bwcheck_r = min((bwcheck, M_r))
    bw_min_l = abs(X_uniq_l:-c)[bwcheck_l] + 1e-8
    bw_min_r = abs(X_uniq_r:-c)[bwcheck_r] + 1e-8
    c_bw = max((c_bw, bw_min_l, bw_min_r))
}
```

This ensures the bandwidth is at least wide enough to include `bwcheck` unique X values on each side of the cutoff. The `+1e-8` prevents exact boundary issues.

### 4.4 Output Message (L998)

```stata
if ("`masspoints'"=="adjust" & masspoints_found==1)
    di "Estimates adjusted for mass points in the running variable."
```

---

## 5. Mode: `off`

No mass points detection or adjustment is performed. The raw `N` is used in the pilot bandwidth formula with no bwcheck enforcement.

---

## 6. Output in Results Table

**Source:** L923

```stata
if ("`masspoints'"=="check" | masspoints_found==1)
    disp ... "Unique obs" ... M_l ... M_r
```

When mass points are relevant, the output table shows the unique observation counts on each side of the cutoff.

---

## 7. Interaction with Other Features

### 7.1 NN VCE Pre-Sort

The pre-sort for mass points (L274) is shared with NN VCE:
```stata
if ("`vce_select'"=="nn" | "`masspoints'"=="check" | "`masspoints'"=="adjust") {
    sort `x', stable
    if ("`vce_select'"=="nn") {
        tempvar dups dupsid
        by `x': gen dups = _N
        by `x': gen dupsid = _n
    }
}
```

When both NN and masspoints are active, the sort happens once and serves both purposes.

### 7.2 bwselect Interaction

The mass points adjustment affects the initial pilot `c_bw`, which flows through all three bandwidth selection steps. Therefore, ALL bandwidth selectors (mserd, msetwo, msesum, CER variants, comb variants) automatically benefit from mass points adjustment.

### 7.3 bwcheck Interaction

When `masspoints="adjust"` triggers automatic `bwcheck=10`, and the user has also specified `bwcheck`, the user's value takes precedence (the automatic setting only applies when `bwcheck==0`).

---

## 8. Python Implementation Path

### 8.1 Detection Function

```python
def _detect_masspoints(X_l, X_r, threshold=0.2):
    """Detect mass points in the running variable."""
    M_l = len(np.unique(X_l))
    M_r = len(np.unique(X_r))
    N_l = len(X_l)
    N_r = len(X_r)
    mass_l = 1.0 - M_l / N_l
    mass_r = 1.0 - M_r / N_r
    found = (mass_l >= threshold) or (mass_r >= threshold)
    return found, M_l, M_r, mass_l, mass_r
```

### 8.2 Adjustment

```python
if masspoints == "adjust" and masspoints_found:
    M = M_l + M_r
    c_bw = C_c * BWp * M**(-0.2)  # M instead of N
    if bwcheck == 0:
        bwcheck = 10
elif masspoints == "adjust" and not masspoints_found:
    c_bw = C_c * BWp * N**(-0.2)  # standard formula
else:
    c_bw = C_c * BWp * N**(-0.2)  # check or off: standard formula
```

### 8.3 bwcheck Enforcement

```python
if bwcheck > 0:
    X_uniq_l = np.sort(np.unique(X_l))[::-1]  # descending
    X_uniq_r = np.sort(np.unique(X_r))         # ascending
    bwcheck_l = min(bwcheck, M_l)
    bwcheck_r = min(bwcheck, M_r)
    bw_min_l = np.abs(X_uniq_l - c)[bwcheck_l - 1] + 1e-8  # 0-indexed
    bw_min_r = np.abs(X_uniq_r - c)[bwcheck_r - 1] + 1e-8
    c_bw = max(c_bw, bw_min_l, bw_min_r)
```

### 8.4 Parameter Interface

```python
def fit(self, masspoints: str = "adjust", bwcheck: int = 0, ...):
    """masspoints: 'adjust', 'check', or 'off'"""
```

### 8.5 Implementation Complexity

**LOW-MEDIUM** — the logic is straightforward counting + conditional formula choice. The main work is integrating the detection/adjustment into the bandwidth selection pipeline.

---

## 9. Stata Source Line Reference

| Feature | Lines | Description |
|---------|-------|-------------|
| Default value | L178 | `masspoints = "adjust"` |
| Pre-sort | L273–279 | Sort by X for NN + masspoints |
| Detection | L380–395 | Unique values count, 20% threshold |
| Auto-bwcheck | L392 | Set `bwcheck=10` when adjusting |
| Adjusted c_bw | L398 | `C_c * BWp * M^(-1/5)` |
| bwcheck enforce | L403–409 | Minimum bandwidth by unique obs |
| Output table | L923 | Unique obs counts |
| Warning message | L998 | "Estimates adjusted..." |

---

## 10. Validation Strategy

| case_id | Description | Risk Focus |
|---------|-------------|------------|
| `w8_mp_off` | No mass points, `masspoints(off)` | Baseline: same as current behavior |
| `w8_mp_check` | Mass points data, `masspoints(check)` | Correct detection, no adjustment |
| `w8_mp_adjust` | Mass points data, `masspoints(adjust)` | M-based c_bw, bwcheck=10 |
| `w8_mp_threshold` | Exactly 20% repeated values | Boundary behavior |
| `w8_mp_bwselect` | Mass points + mserd | Bandwidth differs from no-masspoints |
