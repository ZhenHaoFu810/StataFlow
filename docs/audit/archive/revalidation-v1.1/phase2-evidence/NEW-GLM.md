# NEW-GLM — Phase 2 GLM / PPML New-Findings & Issue Confirmation Report

**Date:** 2026-06-03  
**Agent:** StataFlow Phase 2 GLM/PPML Validation Agent  
**Scope:** Re-validation of Phase 1 GLM-01..GLM-04 on real datasets (`mroz.csv`, `crime1.csv`).

---

## Issue Tracker

| ID | Title | Phase 1 Status | Phase 2 Verdict | Severity |
|----|-------|----------------|-----------------|----------|
| GLM-01 | Logit/Poisson robust VCE missing `n/(n-1)` small-sample correction | Reported | **CONFIRMED** | High |
| GLM-02 | PPMLHDFE `eform` z/p calculation error | Reported | **CONFIRMED** | High |
| GLM-03 | Wrapper does not return model instance | Reported | **PARTIALLY CONFIRMED / DESIGN CLARIFICATION NEEDED** | Medium |
| GLM-04 | No `weight` support in GLM wrappers | Reported | **CONFIRMED** | Medium |

---

## GLM-01: Logit / Poisson robust VCE missing `n/(n-1)` small-sample correction

### Root Cause
`GLMBase._compute_vce()` (used by `Logit` and `Poisson`) computes the robust sandwich as:

```python
meat = (X * residuals[:, np.newaxis]).T @ (X * residuals[:, np.newaxis])
cov_beta = XtX_inv @ meat @ XtX_inv
```

It does **not** multiply by `n / (n - 1)`, whereas Stata's `vce(robust)` for MLE commands applies this small-sample adjustment.

`Probit._compute_vce()` already includes:
```python
n_adj = n / (n - 1) if n > 1 else 1.0
cov_beta = n_adj * cov_bread @ meat @ cov_bread
```

### Evidence

**Logit robust (`n = 753`):**
| Variable | Python SE | Stata SE | Ratio (Stata/Python) | Expected `√(n/(n-1))` |
|----------|-----------|----------|----------------------|-----------------------|
| age | 0.01374522 | 0.01375436 | 1.00066467 | 1.00066467 |
| educ | 0.04049965 | 0.04052657 | 1.00066467 | 1.00066467 |
| exper | 0.01438372 | 0.01439328 | 1.00066467 | 1.00066467 |
| _cons | 0.81434387 | 0.81488514 | 1.00066467 | 1.00066467 |

**Poisson robust (`n = 2725`):**
| Variable | Python SE | Stata SE | Ratio (Stata/Python) | Expected `√(n/(n-1))` |
|----------|-----------|----------|----------------------|-----------------------|
| pcnv | 0.10124868 | 0.10126726 | 1.00018354 | 1.00018354 |
| ptime86 | 0.01995038 | 0.01995404 | 1.00018354 | 1.00018354 |
| black | 0.09860947 | 0.09862757 | 1.00018354 | 1.00018354 |
| _cons | 0.08296791 | 0.08298314 | 1.00018354 | 1.00018354 |

The ratio matches `√(n/(n-1))` to machine precision (`< 1e-10`).

### Fix Required
Add `n_adj = n / (n - 1)` to `GLMBase._compute_vce()` for `vce == "robust"`:

```python
elif vce == "robust":
    residuals = y - mu
    meat = (X * residuals[:, np.newaxis]).T @ (X * residuals[:, np.newaxis])
    n_adj = n / (n - 1) if n > 1 else 1.0
    cov_beta = n_adj * XtX_inv @ meat @ XtX_inv
```

### Impact
- Logit robust SEs will increase by ~0.07% for n=753, less for larger n.
- Poisson robust SEs will increase by ~0.02% for n=2725.
- z-statistics and p-values will shift slightly toward Stata values.
- Probit is **not affected** (already fixed).

---

## GLM-02: PPMLHDFE `eform` z/p calculation error

### Root Cause
When `eform=True`, `PPMLHDFE.fit()` transforms the coefficients and covariance matrix via the delta method:

```python
D = np.diag(np.exp(beta_reported))
beta_reported = np.exp(beta_reported)
cov_reported = D @ cov_reported @ D
se = np.sqrt(np.diag(cov_reported))
z_stats = beta_reported / se
p_values = 2 * (1 - norm_dist.cdf(np.abs(z_stats)))
```

This recomputes z/p on the **exponentiated scale**. However, Stata's `eform` option:
1. Displays `exp(b)` and the delta-method SE.
2. **Retains the original z-statistic** (computed from the untransformed coefficient).
3. The z-stat tests H₀: b = 0, which is equivalent to H₀: exp(b) = 1.

Python's approach tests H₀: exp(b) = 0, which is statistically meaningless for count models (IRR cannot be zero).

### Evidence

| Var | Stata `exp(b)` | Python `beta` | Stata z | Python z | Direction |
|-----|----------------|---------------|---------|----------|-----------|
| pcnv | 0.6729 | 0.6729 | **-3.912** | **+9.875** | Sign flipped |
| ptime86 | 0.9134 | 0.9134 | **-4.540** | **+50.12** | Magnitude wrong |
| qemp86 | 0.9621 | 0.9621 | **-1.131** | **+29.26** | Magnitude wrong |
| black | 1.9478 | 1.9478 | **+6.764** | **+10.15** | Magnitude inflated |

Stata's eform output shows a **negative** z for `pcnv` because the underlying coefficient is negative (`-0.396`). Python's z is positive because `exp(-0.396) > 0`. The hypothesis being tested is completely different.

### Fix Required
For `eform=True`, keep the **original** z-statistic and p-value (based on the untransformed coefficient and SE), but transform only:
- `beta_reported` → `exp(beta_reported)`
- `se` → delta-method SE (`exp(b) * SE_b`)
- `ci_low`, `ci_high` → `exp(ci_low)`, `exp(ci_high)`

Do **not** recompute z and p from the transformed SE.

```python
if eform:
    # Store original z/p before transformation
    z_stats_orig = beta_reported / se
    p_values_orig = 2 * (1 - norm_dist.cdf(np.abs(z_stats_orig)))
    ci_low_orig = beta_reported - z_crit * se
    ci_high_orig = beta_reported + z_crit * se

    D = np.diag(np.exp(beta_reported))
    beta_reported = np.exp(beta_reported)
    cov_reported = D @ cov_reported @ D
    se = np.sqrt(np.maximum(np.diag(cov_reported), 0))

    # Retain original z/p (testing H0: b=0  <=>  H0: exp(b)=1)
    z_stats = z_stats_orig
    p_values = p_values_orig
    ci_low = np.exp(ci_low_orig)
    ci_high = np.exp(ci_high_orig)
```

### Impact
- PPMLHDFE `eform=True` z/p will align with Stata.
- CIs will still be correct (delta method on transformed scale).
- Displayed `exp(b)` and SE will remain correct.

---

## GLM-03: Wrapper does not return model instance

### Current Behavior
All GLM wrappers (`logit`, `probit`, `poisson`, `ppmlhdfe`) return the result of `model.fit()`, which is a `ResultSchema`:

```python
def logit(data, y, x, ...):
    model = Logit(...)
    return model.fit(vce=vce, cluster=cluster)   # Returns ResultSchema
```

This is **consistent** with all other Stata-compatible wrappers in the project (`regress`, `reghdfe`, `ivregress_2sls`, etc.).

### Issue Clarification
The Phase 1 report states "wrapper 不返回模型实例" (wrapper does not return model instance). There are two possible interpretations:

1. **User expects the estimator object** (e.g., to call `.predict()`, `.margins()` afterwards). Currently impossible because the wrapper discards `model` after fitting.
2. **Wrapper returns nothing / wrong type**. This is NOT the case — all wrappers return a valid `ResultSchema`.

### Phase 2 Verdict
- The wrappers **do** return a valid `ResultSchema`.
- The wrappers **do not** return the fitted estimator instance, which prevents post-estimation (`predict`, `margins`) from the wrapper return value.
- This is a **project-wide design decision** (all compat wrappers return `ResultSchema`).
- **Recommendation:** If post-estimation from wrapper calls is required, either:
  a) Return the estimator instance instead of `ResultSchema` (breaking change, affects all wrappers), or
  b) Add `predict()` / `margins()` methods to `ResultSchema` (preferred, minimal intrusion).

**Escalation needed:** Codex decision on whether GLM-03 should be fixed locally or addressed as a project-wide `ResultSchema` enhancement.

---

## GLM-04: No `weight` support in GLM wrappers

### Current Behavior
None of the GLM wrappers accept a `weight` argument:

```python
def logit(data, y, x, *, vce="ols", cluster=None, noconstant=False, missing="drop", **kwargs):
    ...
```

Passing `weight=...` or `aweight=...` is caught by `**kwargs` and raises:
```
ValueError: Unsupported arguments: ['weight']
```

### Evidence
Attempted:
```python
logit(df_mroz, y='inlf', x=['age'], weight='wage')
# ValueError: Unsupported arguments: ['weight']
```

### Impact
- Cannot replicate Stata's `[aweight=]`, `[fweight=]`, `[pweight=]`, or `[iweight=]` options.
- Phase 1 testing was blocked on weighted GLM scenarios.

### Fix Required
Add `aweight` / `fweight` / `pweight` parameters to wrappers and pass them through to the estimator. The underlying `GLMBase` already supports weights internally via IRLS (the `w` vector), but there is no API to inject external weights.

**Note:** `Probit` uses observed Hessian for VCE, so weighting would need careful integration. `Logit` and `Poisson` use standard IRLS weights and are easier to extend.

---

## Additional Observations (Not Phase 1 Issues)

### A1. `df_resid` for MLE models
Python reports `df_resid = n - k` for all models. Stata leaves `e(df_r)` missing (`.`) for `logit`, `probit`, and `poisson` with robust VCE. This is a display convention difference, not a numerical error.

**Risk:** Low. Users relying on `df_resid` for MLE robust models may see a number where Stata shows missing.

### A2. Deviance for Logit
Python computes deviance for Logit as:
```python
2 * sum(y * log(y/mu) + (1-y) * log((1-y)/(1-mu)))
```
Stata does not export deviance in `e(deviance)` for `logit`, so direct comparison was not possible. The computed value (818.5077) is internally consistent.

### A3. PPMLHDFE `f_stat` / `f_pvalue`
Python currently sets `f_stat = null` and `f_pvalue = null` for PPMLHDFE. Stata reports Wald chi² (242.78) and its p-value. The `ResultSchema` field mapping should be updated to populate `fit.f_stat` with the Wald chi².

**Risk:** Medium. Missing f_stat in PPMLHDFE result breaks downstream reporting.

---

## Recommended Fix Priority

1. **GLM-01** (Logit/Poisson robust `n/(n-1)`) — One-line fix in `GLMBase._compute_vce`. High impact, easy fix.
2. **GLM-02** (PPMLHDFE eform z/p) — Refactor `eform` branch in `PPMLHDFE.fit()` to preserve original z/p. High impact, moderate complexity.
3. **GLM-04** (weight support) — Add weight parameter plumbing. Medium impact, moderate complexity (needs VCE alignment).
4. **GLM-03** (wrapper return type) — Requires Codex escalation on project-wide design.
5. **A3** (PPMLHDFE f_stat) — Populate Wald chi². Low complexity.

---

## Files Referenced

| Path | Role |
|------|------|
| `src/stataflow/estimators/glm.py` | Logit, Probit, Poisson estimators |
| `src/stataflow/estimators/ppmlhdfe.py` | PPMLHDFE estimator |
| `src/stataflow/compat/stata/glm.py` | GLM wrappers |
| `src/stataflow/compat/stata/hdfe.py` | PPMLHDFE wrapper |
| `stata/output/phase2/run_glm_stata.do` | Stata validation do file |
| `stata/output/phase2/run_glm_python.py` | Python validation script |
| `stata/output/phase2/python_results.json` | Python numeric output |
| `stata/output/phase2/run_*.log` | Stata execution log |
