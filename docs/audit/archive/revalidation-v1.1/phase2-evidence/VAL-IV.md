# Phase 2 IV/GMM Dual-Run Validation Report

**Date**: 2026-06-03
**Agent**: Phase 2 IV/GMM Revalidation Agent
**Dataset**: Card (1995) IV dataset — 3,010 observations, 34 variables
**Stata version**: 17.0 MP
**Python package**: StataFlow (editable install from src/)

---

## 1. Scope

Validation covers the IV command family against Stata 17 ground truth:

| # | Scenario | Python command | Stata command |
|---|----------|---------------|---------------|
| 1 | ivregress 2sls — conventional VCE | `ivregress_2sls(vce="ols")` | `ivregress 2sls` (default) |
| 2 | ivregress 2sls — robust VCE | `ivregress_2sls(vce="robust")` | `ivregress 2sls, vce(robust)` |
| 3 | ivregress 2sls — cluster VCE (age) | `ivregress_2sls(vce="cluster", cluster="age")` | `ivregress 2sls, vce(cluster age)` |
| 4 | ivregress 2sls — cluster VCE (south) | `ivregress_2sls(vce="cluster", cluster="south")` | `ivregress 2sls, vce(cluster south)` |
| 5 | ivreghdfe — 1-way cluster + FE | `ivreghdfe(absorb="age_group", vce="cluster", cluster="age_group")` | `ivreghdfe, absorb(age_group) cluster(age_group)` |
| 6 | ivreghdfe — 2-way cluster + FE | `ivreghdfe(absorb="age_group", vce="cluster", cluster=["age_group","south"])` | `ivreghdfe, absorb(age_group) vce(cluster age_group south)` |
| 7 | First-stage F statistics | `first=True` on IVAbsorbingOLS | `ivregress 2sls, first` / `ivreghdfe, first` |

---

## 2. Method

- **Python side**: Run `stataflow.compat.stata.iv` wrappers on the Card CSV.
- **Stata side**: Generate `.do` files, execute via `StataMP-64.exe /e do`, parse `.log` output.
- **Comparison fields**: `beta`, `std_err`, `t_stat`/`z_stat`, `nobs`, `df_model`, `df_resid`, `rmse`, `r2`, `r2_adj`.
- **Tolerance**: Relative tolerance `rtol = 1e-6`, absolute tolerance `atol = 1e-8`.
- **Missing-value rule**: Both sides drop rows with missing values in `y`, `x`, `endog`, `instruments`, `cluster`, or `absorb` variables. Card data has zero missing in the used variables, so `N = 3,010` on both sides.

---

## 3. Scenario Results

### 3.1 ivregress 2sls — conventional VCE

| var | Python beta | Stata beta | beta diff | Python SE | Stata SE | SE diff | stat diff | status |
|-----|-------------|------------|-----------|-----------|----------|---------|-----------|--------|
| educ | 0.132289 | 0.132289 | 6.19e-13 | 0.049176 | 0.049176 | 4.85e-09 | 2.03e-08 | **PASS** |
| exper | 0.107498 | 0.107498 | 4.32e-09 | 0.021276 | 0.021276 | 4.62e-09 | 3.42e-08 | **PASS** |
| expersq | -0.002284 | -0.002284 | 1.97e-09 | 0.000334 | 0.000334 | 4.03e-09 | 1.10e-08 | **PASS** |
| black | -0.130802 | -0.130802 | 4.16e-09 | 0.052811 | 0.052811 | 1.21e-10 | 4.62e-08 | **PASS** |
| south | -0.104901 | -0.104901 | 3.62e-09 | 0.023046 | 0.023046 | 1.18e-09 | 3.02e-08 | **PASS** |
| smsa | 0.131324 | 0.131324 | 2.87e-09 | 0.030095 | 0.030095 | 4.56e-11 | 3.70e-08 | **PASS** |
| _cons | 3.752781 | 3.752781 | 4.14e-08 | 0.828376 | 0.828376 | 3.31e-09 | 3.46e-08 | **PASS** |

Fit stats: `nobs`, `df_model`, `rmse`, `r2`, `r2_adj` all **PASS**.

> **Observation (IV-03)**: Python reports `t_stat` field but internally uses the normal distribution (z) for p-values and CIs. Stata `ivregress 2sls` with conventional VCE reports t-statistics in the table but, because `ivregress` is an asymptotic estimator, the numerical `beta/se` ratio is identical to Python’s. The divergence is in inference (p-values / CIs) not in the displayed ratio. With N=3,010 the t vs z difference is < 0.0001 in critical values, so field-level numeric comparison still passes.

---

### 3.2 ivregress 2sls — robust VCE

| var | Python beta | Stata beta | beta diff | Python SE | Stata SE | SE diff | stat diff | status |
|-----|-------------|------------|-----------|-----------|----------|---------|-----------|--------|
| educ | 0.132289 | 0.132289 | 6.19e-13 | 0.048521 | 0.048521 | 1.54e-09 | 4.39e-08 | **PASS** |
| exper | 0.107498 | 0.107498 | 4.32e-09 | 0.021113 | 0.021113 | 4.36e-09 | 4.40e-08 | **PASS** |
| expersq | -0.002284 | -0.002284 | 1.97e-09 | 0.000346 | 0.000346 | 1.54e-09 | 2.60e-08 | **PASS** |
| black | -0.130802 | -0.130802 | 4.16e-09 | 0.051451 | 0.051451 | 1.29e-09 | 1.56e-08 | **PASS** |
| south | -0.104901 | -0.104901 | 3.62e-09 | 0.022900 | 0.022900 | 1.09e-09 | 4.20e-08 | **PASS** |
| smsa | 0.131324 | 0.131324 | 2.87e-09 | 0.029768 | 0.029768 | 2.64e-09 | 4.07e-08 | **PASS** |
| _cons | 3.752781 | 3.752781 | 4.14e-08 | 0.816750 | 0.816750 | 2.49e-09 | 3.02e-09 | **PASS** |

Fit stats all **PASS**.

> Both sides use z-statistics for robust VCE. Full alignment.

---

### 3.3 ivregress 2sls — cluster VCE (age)

| var | Python beta | Stata beta | beta diff | Python SE | Stata SE | SE diff | stat diff | status |
|-----|-------------|------------|-----------|-----------|----------|---------|-----------|--------|
| educ | 0.132289 | 0.132289 | 6.19e-13 | 0.039223 | 0.039223 | 4.15e-09 | 2.12e-08 | **PASS** |
| exper | 0.107498 | 0.107498 | 4.32e-09 | 0.018409 | 0.018409 | 5.41e-11 | 1.59e-08 | **PASS** |
| expersq | -0.002284 | -0.002284 | 1.97e-09 | 0.000893 | 0.000893 | 3.94e-09 | 2.34e-09 | **PASS** |
| black | -0.130802 | -0.130802 | 4.16e-09 | 0.037859 | 0.037859 | 4.68e-09 | 8.71e-09 | **PASS** |
| south | -0.104901 | -0.104901 | 3.62e-09 | 0.024529 | 0.024529 | 2.25e-09 | 3.95e-08 | **PASS** |
| smsa | 0.131324 | 0.131324 | 2.87e-09 | 0.027676 | 0.027676 | 1.23e-09 | 4.89e-08 | **PASS** |
| _cons | 3.752781 | 3.752781 | 4.14e-08 | 0.625176 | 0.625176 | 5.85e-10 | 2.60e-08 | **PASS** |

Fit stats all **PASS**. `n_clust = 11` on both sides.

---

### 3.4 ivregress 2sls — cluster VCE (south)

| var | Python beta | Stata beta | beta diff | Python SE | Stata SE | SE diff | stat diff | status |
|-----|-------------|------------|-----------|-----------|----------|---------|-----------|--------|
| educ | 0.132289 | 0.132289 | 6.19e-13 | 0.064109 | 0.064109 | 4.34e-09 | 7.89e-09 | **PASS** |
| exper | 0.107498 | 0.107498 | 4.32e-09 | 0.017173 | 0.017173 | 5.63e-10 | 2.46e-08 | **PASS** |
| expersq | -0.002284 | -0.002284 | 1.97e-09 | 0.000298 | 0.000298 | 4.94e-09 | 4.76e-08 | **PASS** |
| black | -0.130802 | -0.130802 | 4.16e-09 | 0.027493 | 0.027493 | 3.51e-09 | 2.33e-08 | **PASS** |
| south | -0.104901 | -0.104901 | 3.62e-09 | 0.033807 | 0.033807 | 2.14e-09 | 3.68e-08 | **PASS** |
| smsa | 0.131324 | 0.131324 | 2.87e-09 | 0.036767 | 0.036767 | 1.05e-09 | 4.93e-08 | **PASS** |
| _cons | 3.752781 | 3.752781 | 4.14e-08 | 1.024767 | 1.024767 | 5.00e-08 | 7.08e-09 | **PASS** |

Fit stats all **PASS**. `n_clust = 2` on both sides.

---

### 3.5 ivreghdfe — absorb(age_group) cluster(age_group)

| var | Python beta | Stata beta | beta diff | Python SE | Stata SE | SE diff | stat diff | status |
|-----|-------------|------------|-----------|-----------|----------|---------|-----------|--------|
| educ | 0.242805 | 0.242805 | 1.17e-09 | 0.181193 | 0.181223 | 3.02e-05 | 2.23e-04 | **FAIL** |
| exper | 0.223682 | 0.223682 | 3.06e-09 | 0.158668 | 0.158694 | 2.64e-05 | 2.35e-04 | **FAIL** |
| expersq | -0.002491 | -0.002491 | 2.67e-09 | 0.000995 | 0.000995 | 1.66e-07 | 4.17e-04 | **FAIL** |
| black | -0.127378 | -0.127378 | 4.66e-09 | 0.041803 | 0.041810 | 6.96e-06 | 5.07e-04 | **FAIL** |
| south | -0.096053 | -0.096053 | 3.72e-09 | 0.032778 | 0.032784 | 5.45e-06 | 4.88e-04 | **FAIL** |
| smsa | 0.138341 | 0.138341 | 2.29e-09 | 0.028098 | 0.028103 | 4.68e-06 | 8.20e-04 | **FAIL** |

- **Betas**: Perfect match.
- **SEs**: Very close (~3e-5 relative diff) but just outside the 1e-6 tolerance. This is likely a small-sample adjustment difference in the cluster-robust VCE denominator.
- **Fit stats**: `nobs`, `df_model`, `df_resid`, `rmse`, `r2`, `r2_adj` all **PASS**.

> Note: Stata reports `df_a = 0` because `age_group` (3 categories) is nested within the cluster variable and treated as redundant. Python also computes `df_a = 0`.

---

### 3.6 ivreghdfe — 2-way cluster (age_group + south)

| var | Python beta | Stata beta | beta diff | Python SE | Stata SE | SE diff | stat diff | status |
|-----|-------------|------------|-----------|-----------|----------|---------|-----------|--------|
| educ | 0.242805 | 0.242805 | 1.17e-09 | 0.235692 | 0.181223 | 5.45e-02 | 3.10e-01 | **FAIL** |
| exper | 0.223682 | 0.223682 | 3.06e-09 | 0.188690 | 0.158694 | 3.00e-02 | 2.24e-01 | **FAIL** |
| expersq | -0.002491 | -0.002491 | 2.67e-09 | 0.000748 | 0.000995 | 2.47e-04 | 8.28e-01 | **FAIL** |
| black | -0.127378 | -0.127378 | 4.66e-09 | 0.058179 | 0.041810 | 1.64e-02 | 8.57e-01 | **FAIL** |
| south | -0.096053 | -0.096053 | 3.72e-09 | 0.045507 | 0.032784 | 1.27e-02 | 8.19e-01 | **FAIL** |
| smsa | 0.138341 | 0.138341 | 2.29e-09 | 0.045734 | 0.028103 | 1.76e-02 | 1.90e+00 | **FAIL** |

- **Betas**: Perfect match.
- **SEs**: Large divergence. Python computes substantially larger SEs (e.g., educ SE = 0.236 vs Stata 0.181).
- **df_resid**: Python = 1.0, Stata = 2.0 → **FAIL**.

> **Root cause analysis**: Stata `ivreghdfe` emits a warning:
> ```
> Warning: estimated covariance matrix of moment conditions not of full rank.
>          overidentification statistic not reported, and standard errors and
>          model tests should be interpreted with caution.
> Possible causes:
>          number of clusters insufficient to calculate robust covariance matrix
> ```
> With only 3 clusters in `age_group`, the 2-way cluster covariance matrix is rank-deficient. Stata appears to fall back to 1-way cluster SEs (identical to the 1-way cluster scenario). Python’s `_compute_multiway_cluster_vce` applies the standard Cameron-Gelbach-Miller inclusion-exclusion formula unconditionally and does not detect or handle rank deficiency, producing inflated SEs.

---

## 4. First-Stage F Statistics

### 4.1 ivregress 2sls, first

Python `IV2SLS` does **not** implement `first=True`; no first-stage diagnostics are available.

Stata results:

| VCE | First-stage F | Prob > F | First-stage R² |
|-----|--------------|----------|----------------|
| Conventional | F(6, 3003) = 451.87 | 0.0000 | 0.4745 |
| Robust | F(6, 3003) = 608.02 | 0.0000 | 0.4745 |
| Cluster (age) | F(6, 3003) = 389.34 | 0.0000 | 0.4745 |

> **Gap**: Python has no first-stage F for `ivregress_2sls`.

### 4.2 ivreghdfe, first

| Metric | Python (1-way cluster) | Stata (1-way cluster) | Python (2-way cluster) | Stata (2-way cluster) |
|--------|------------------------|----------------------|------------------------|----------------------|
| First-stage F | 2.106 | 2.10 | 4.886 | 2.10 |
| First-stage p | 0.1467 | 0.2842 | 0.0271 | 0.2842 |
| WeakIV KP F | 2.102 | 2.10 | 4.877 | 2.10 |
| WeakIV CD F | — | 5.83 | — | 5.83 |
| Underid LM | 1.649 | 1.65 | 1.325 | 1.65 |
| Underid p | 0.1991 | 0.1991 | 0.2497 | 0.1991 |

**Observations**:
- **WeakIV KP F** matches well (2.102 vs 2.10).
- **Underid LM** matches for 1-way cluster (1.649 vs 1.65) but diverges for 2-way (1.325 vs 1.65).
- **First-stage p-value** diverges because Python uses `df_r = 3001` (observation-based) while Stata uses cluster degrees of freedom (`G - 1 = 2`).
- **2-way cluster**: Python first-stage F (4.886) differs from Stata (2.10), consistent with the VCE divergence noted in §3.6.

---

## 5. Assessment of Phase 1 Known Issues

| Issue | Status | Evidence |
|-------|--------|----------|
| **IV-01** ivreghdfe GMM2S cluster VCE main/fallback path inconsistency | **Not tested** | This validation used `estimator="2sls"`. GMM2S path (`estimator="gmm2s"`) requires a separate dual-run. |
| **IV-02** fix_psd_reghdfe wrong `_cons` assumption | **Observed** | In `ivreghdfe` 2-way cluster, `fix_psd_reghdfe` is called on `cov_reported`. The matrix has no `_cons` row (ivreghdfe partials it out), so `k-1` backup logic is operating on the last slope coefficient instead of the constant. This needs Codex escalation for ADR-0004 amendment. |
| **IV-03** ivregress 2sls uses z-stats for vce(ols) | **Confirmed** | Python `IV2SLS.fit(vce="ols")` uses `norm.cdf` for p-values. Stata `ivregress 2sls` conventional reports t-stats. The `beta/se` ratio is identical, so coefficient table numbers match, but inference differs. With N=3,010 the t vs z difference is <0.01% and does not trigger the 1e-6 field-level tolerance. |
| **IV-04** X/Z independent collinearity detection | **Not triggered** | No collinear variables were present in the Card data used for IV regression. The `exper`/`expersq` pair is not perfectly collinear. A dedicated collinearity test case is needed. |
| **IV-05** Multi-endogenous weakiv not implemented | **Confirmed** | `_compute_weakiv_stats` has `if k_endog == 1:` branch but `else: idstat = np.nan`. Multi-endogenous weak instrument diagnostics are stubbed out. |

---

## 6. New Issues Discovered (Detailed in NEW-IV.md)

1. **Runtime crash in 2-way cluster weakiv** (`iv.py:1555`) — numpy string-array concatenation bug. **Fixed** during this validation.
2. **Nonsensical F-stat for ivreghdfe cluster VCE** — Python produces `f_stat = -2.02e14` (1-way) and `+4.25e11` (2-way). The F-stat formula in `IVAbsorbingOLS.fit` is numerically unstable when `cov_slopes` is near-singular.
3. **First-stage F uses wrong df_r under cluster VCE** — Python uses `n - k_z_full` instead of `G - 1` (or the appropriate cluster-based df).
4. **2-way cluster VCE not rank-deficiency aware** — Python inclusion-exclusion formula does not check for rank deficiency, leading to divergent SEs vs Stata’s fallback behavior.

---

## 7. Files and Artifacts

| File | Location |
|------|----------|
| Python results JSON | `stata/output/phase2/phase2_iv_python_results.json` |
| Stata results JSON | `stata/output/phase2/phase2_iv_stata_results.json` |
| Stata logs (per scenario) | `stata/output/phase2/stata_ivregress_*.log` |
| Stata logs (ivreghdfe) | `stata/output/phase2/stata_ivreghdfe_*.log` |
| Validation script | `scripts/phase2_iv_validation.py` |
| This report | `docs/audit/revalidation-v1.1/phase2-evidence/VAL-IV.md` |
| New issues report | `docs/audit/revalidation-v1.1/phase2-evidence/NEW-IV.md` |

---

## 8. Summary

- **ivregress 2sls** (scenarios 1–4): **FULLY ALIGNED** with Stata 17. All coefficients, SEs, and fit statistics pass 1e-6 tolerance.
- **ivreghdfe 1-way cluster** (scenario 5): **Mostly aligned**. Coefficients match; SEs differ at ~3e-5 relative (just outside tolerance). F-stat computation is numerically unstable.
- **ivreghdfe 2-way cluster** (scenario 6): **DIVERGENT**. SEs differ materially because Stata detects rank deficiency and issues a warning, while Python applies inclusion-exclusion unconditionally. This is a **real algorithmic gap**.
- **First-stage / weakiv**: WeakIV KP F matches well for 1-way cluster. First-stage p-values use wrong DoF. Multi-endogenous weakiv is not implemented.

**Recommendation**: Escalate IV-02 (fix_psd_reghdfe) and the 2-way cluster rank-deficiency issue to Codex for ADR-0004 amendment and algorithmic arbitration.
