# StataFlow Cookbook

[简体中文](./cookbook.zh-CN.md)

This cookbook provides short, copy-pasteable recipes for common econometric tasks in StataFlow. Each recipe shows the Python code alongside the equivalent Stata command.

> **Status legend:** **Stable** = synthetic + real-data verified against Stata 17; core API unlikely to change. **Beta** = high-frequency paths are verified, most major functional blocks are covered. Unsupported parameters are hard-rejected.

---

## Table of Contents

- [Linear Models](#linear-models)
- [Instrumental Variables](#instrumental-variables)
- [Generalized Linear Models](#generalized-linear-models)
- [Difference-in-Differences](#difference-in-differences)
- [Regression Discontinuity](#regression-discontinuity)
- [Factor Variables](#factor-variables)
- [Working with Results](#working-with-results)

---

## Linear Models

### OLS with robust standard errors

```python
from stataflow.compat.stata import regress

result = regress(df, y="y", x=["x1", "x2"], vce="robust")
```

**Stata equivalent:**
```stata
reg y x1 x2, robust
```

### OLS with clustered standard errors

```python
result = regress(df, y="y", x=["x1", "x2"], vce="cluster", cluster="state")
```

**Stata equivalent:**
```stata
reg y x1 x2, cluster(state)
```

### OLS without a constant

```python
result = regress(df, y="y", x=["x1", "x2"], noconstant=True)
```

**Stata equivalent:**
```stata
reg y x1 x2, noconstant
```

### Weighted regression (analytic weights)

```python
result = regress(df, y="y", x=["x1", "x2"], aweight="w")
```

**Stata equivalent:**
```stata
reg y x1 x2 [aw=w]
```

### Single fixed effects (within estimator)

```python
from stataflow.compat.stata import xtreg_fe

result = xtreg_fe(df, y="y", x=["x1", "x2"], fe="firm_id", vce="robust")
```

**Stata equivalent:**
```stata
xtreg y x1 x2, fe robust
```

### Single absorbed variable (areg-style)

```python
from stataflow.compat.stata import areg

result = areg(
    df, y="y", x=["x1", "x2"],
    absorb="firm_id", vce="cluster", cluster="state"
)
```

**Stata equivalent:**
```stata
areg y x1 x2, absorb(firm_id) cluster(state)
```

### Two-way fixed effects with reghdfe

```python
from stataflow.compat.stata import reghdfe

result = reghdfe(
    df,
    y="y",
    x=["x1", "x2", "treat"],
    absorb="firm_id year",
    vce="cluster",
    cluster="state",
)
```

**Stata equivalent:**
```stata
reghdfe y x1 x2 treat, absorb(firm_id year) vce(cluster state)
```

> `absorb` accepts either a space-separated string or a list: `absorb=["firm_id", "year"]`.

### Keep singleton observations in reghdfe

```python
result = reghdfe(df, y="y", x=["x1"], absorb="firm_id", keepsingletons=True)
```

**Stata equivalent:**
```stata
reghdfe y x1, absorb(firm_id) keepsingletons
```

### Two-way clustered standard errors in HDFE

```python
result = reghdfe(
    df, y="y", x=["x1", "x2"],
    absorb="firm_id year",
    vce="cluster", cluster=["state", "year"],
)
```

**Stata equivalent:**
```stata
reghdfe y x1 x2, absorb(firm_id year) vce(cluster state year)
```

> Two-way clustering is also available on `ivreghdfe` and `ppmlhdfe`.

### Save fixed effects estimates

```python
result = reghdfe(df, y="y", x=["x1"], absorb="firm_id", savefe=True)
fe_df = result.fixed_effects  # pd.DataFrame with columns: absorb_var, level, fe_estimate
```

**Stata equivalent:**
```stata
reghdfe y x1, absorb(firm_id) savefe
```

### Individual slope absorption (group-specific trends)

```python
from stataflow.compat.stata import reghdfe

# Intercept + slope: var##c.time_trend
result = reghdfe(
    df, y="y", x=["x1"],
    absorb="firm_id##c.time",
    vce="cluster", cluster="firm_id",
)
```

**Stata equivalent:**
```stata
reghdfe y x1, absorb(firm_id##c.time) vce(cluster firm_id)
```

> `var##c.slope` adds both a group-specific intercept and a group-specific slope. Use `var#c.slope` for slope-only (no intercept).

### Advanced absorb API (tuples and lists)

```python
# List of tuples: (FE var, slope var(s), has_intercept)
result = reghdfe(
    df, y="y", x=["x1"],
    absorb=[("firm_id", "time_trend")],
    vce="cluster", cluster="firm_id",
)

# Multiple slopes, no intercept for this FE
result = reghdfe(
    df, y="y", x=["x1"],
    absorb=[("firm_id", ["x2", "x3"], False)],
    vce="cluster", cluster="firm_id",
)
```

**Stata equivalent:**
```stata
reghdfe y x1, absorb(firm_id##c.time_trend) vce(cluster firm_id)
reghdfe y x1, absorb(firm_id#c.x2 firm_id#c.x3) vce(cluster firm_id)
```

> The `absorb` argument accepts a space-separated string, a list of strings, or a list of tuples. Each tuple has the form `(fe_var, slope_var or list of slope_vars, has_intercept)`.

### MAP iterative absorption (large-scale FE)

```python
# Automatically switches to MAP when FE levels > 5000
result = reghdfe(df, y="y", x=["x1"], absorb="firm_id year", technique="auto")

# Or force MAP explicitly
result = reghdfe(df, y="y", x=["x1"], absorb="firm_id year", technique="map")
```

**Stata equivalent:**
```stata
reghdfe y x1, absorb(firm_id year) technique(map)
```

### Driscoll-Kraay panel HAC standard errors

```python
result = reghdfe(
    df, y="y", x=["x1", "x2"],
    absorb="firm_id",
    vce="dkraay", timevar="year",
)
```

**Stata equivalent:**
```stata
reghdfe y x1 x2, absorb(firm_id) vce(dkraay year)
```

> Driscoll-Kraay requires a `timevar` parameter to identify the time dimension. Bandwidth is auto-selected and truncated at T-1.

### Predict stdp (standard error of prediction) for HDFE

```python
from stataflow import AbsorbingOLS

model = AbsorbingOLS(data=df, y="y", x=["x1"], absorb="firm_id")
result = model.fit(vce="robust")
stdp = model.predict(type="stdp")  # standard error of the linear predictor
```

**Stata equivalent:**
```stata
reghdfe y x1, absorb(firm_id) robust
predict stdp_var, stdp
```

### estat summarize for HDFE

```python
from stataflow.postestimation import estat_summarize

result = reghdfe(df, y="y", x=["x1", "x2"], absorb="firm_id")
summary = estat_summarize(result, data=df, variables=["y", "x1", "x2"], dep_var="y")
# Returns dict with per-variable N, mean, sd, min, max
```

**Stata equivalent:**
```stata
estat summarize
```

---

## Instrumental Variables

### 2SLS with robust standard errors

```python
from stataflow.compat.stata import ivregress_2sls

result = ivregress_2sls(
    df,
    y="y",
    x_exog=["x1"],
    x_endog=["x2"],
    instruments=["z1", "z2"],
    vce="robust",
)
```

**Stata equivalent:**
```stata
ivregress 2sls y x1 (x2 = z1 z2), robust
```

### 2SLS first-stage diagnostics

```python
result = ivregress_2sls(
    df, y="y", x_exog=["x1"], x_endog=["x2"],
    instruments=["z1", "z2"], vce="robust", first=True,
)

first = result.first_stage
for endog_var, stats in first.items():
    print(f"{endog_var}: R2={stats['r2']:.4f}, "
          f"partial R2={stats['partial_r2']:.4f}, "
          f"Shea R2={stats['shea_r2']:.4f}, "
          f"F={stats['f_stat']:.2f}")
```

**Stata equivalent:**
```stata
ivregress 2sls y x1 (x2 = z1 z2), robust first
```

### 2SLS weak-instrument diagnostics

```python
result = ivregress_2sls(
    df, y="y", x_exog=["x1"], x_endog=["x2"],
    instruments=["z1", "z2"], vce="robust",
)

print(f"Kleibergen-Paap LM: {result.idstat:.3f}")
print(f"Cragg-Donald Wald F: {result.widstat:.3f}")
print(f"Stock-Yogo 10% critical: {result.widstat_cv:.1f}")
```

**Stata equivalent:**
```stata
ivregress 2sls y x1 (x2 = z1 z2), robust
estat firststage
```

### 2SLS overidentification test (Sargan)

```python
result = ivregress_2sls(
    df, y="y", x_exog=["x1"], x_endog=["x2"],
    instruments=["z1", "z2", "z3"], vce="robust",
)
print(f"Sargan statistic: {result.hansen_j:.3f}")
```

**Stata equivalent:**
```stata
ivregress 2sls y x1 (x2 = z1 z2 z3), robust
estat overid
```

> The Sargan statistic is available when the model is overidentified (more instruments than endogenous variables).

### IV with high-dimensional fixed effects

```python
from stataflow.compat.stata import ivreghdfe

result = ivreghdfe(
    df,
    y="y",
    x_exog=["x1"],
    x_endog=["x2"],
    instruments=["z1"],
    absorb="firm_id year",
    vce="cluster",
    cluster="state",
)
```

**Stata equivalent:**
```stata
ivreghdfe y x1 (x2 = z1), absorb(firm_id year) cluster(state)
```

> **Status:** Beta. Validated for common 2SLS + FE paths. GMM2S and LIML are also supported.

### IV with GMM2S estimator

```python
result = ivreghdfe(
    df,
    y="y",
    x_exog=["x1"],
    x_endog=["x2"],
    instruments=["z1", "z2"],
    absorb="firm_id",
    estimator="gmm2s",
    vce="robust",
)
print(f"Hansen J statistic: {result.hansen_j:.3f}")
```

**Stata equivalent:**
```stata
ivreghdfe y x1 (x2 = z1 z2), absorb(firm_id) gmm2s robust
```

> GMM2S reports the Hansen J statistic for overidentification testing. Access it via `result.hansen_j`.

### IV with LIML estimator and Fuller adjustment

```python
# LIML with default Fuller (k=1)
result = ivreghdfe(
    df, y="y", x_exog=["x1"], x_endog=["x2"],
    instruments=["z1", "z2"], absorb="firm_id",
    estimator="liml", vce="robust",
)

# LIML with custom Fuller parameter
result = ivreghdfe(
    df, y="y", x_exog=["x1"], x_endog=["x2"],
    instruments=["z1", "z2"], absorb="firm_id",
    estimator="liml", fuller=4, vce="robust",
)

# LIML with custom k-class value
result = ivreghdfe(
    df, y="y", x_exog=["x1"], x_endog=["x2"],
    instruments=["z1", "z2"], absorb="firm_id",
    estimator="liml", kclass=0.8, vce="robust",
)
```

**Stata equivalent:**
```stata
ivreghdfe y x1 (x2 = z1 z2), absorb(firm_id) liml robust
ivreghdfe y x1 (x2 = z1 z2), absorb(firm_id) fuller(4) robust
```

### First-stage diagnostics

```python
result = ivreghdfe(
    df, y="y", x_exog=["x1"], x_endog=["x2"],
    instruments=["z1", "z2"], absorb="firm_id",
    first=True, vce="robust",
)

first = result.first_stage
for endog_var, stats in first.items():
    print(f"{endog_var}: R2={stats['r2']:.4f}, "
          f"Partial R2={stats['partial_r2']:.4f}, "
          f"Shea R2={stats['shea_r2']:.4f}, "
          f"F={stats['f_stat']:.2f}")
```

**Stata equivalent:**
```stata
ivreghdfe y x1 (x2 = z1 z2), absorb(firm_id) first robust
```

### Weak instrument diagnostics

```python
result = ivreghdfe(
    df, y="y", x_exog=["x1"], x_endog=["x2"],
    instruments=["z1", "z2"], absorb="firm_id",
    vce="robust",
)

print(f"Kleibergen-Paap LM: {result.idstat:.3f}")
print(f"Cragg-Donald Wald F: {result.widstat:.3f}")
print(f"Stock-Yogo 10% critical: {result.widstat_cv:.1f}")
```

**Stata equivalent:**
```stata
ivreghdfe y x1 (x2 = z1 z2), absorb(firm_id) robust
```

> Weak instrument tests are always computed and attached to the result object.

### Predict stdp for IV HDFE

```python
from stataflow import IVAbsorbingOLS

model = IVAbsorbingOLS(
    data=df, y="y", x_exog=["x1"], x_endog=["x2"],
    instruments=["z1", "z2"], absorb="firm_id",
)
result = model.fit(vce="robust")
stdp = model.predict(type="stdp")
```

**Stata equivalent:**
```stata
ivreghdfe y x1 (x2 = z1 z2), absorb(firm_id) robust
predict stdp_var, stdp
```

---

## Generalized Linear Models

### Logistic regression

```python
from stataflow.compat.stata import logit

result = logit(df, y="y_binary", x=["x1", "x2"], vce="robust")
```

**Stata equivalent:**
```stata
logit y_binary x1 x2, robust
```

### Probit regression

```python
from stataflow.compat.stata import probit

result = probit(df, y="y_binary", x=["x1", "x2"], vce="cluster", cluster="firm_id")
```

**Stata equivalent:**
```stata
probit y_binary x1 x2, cluster(firm_id)
```

### Poisson regression

```python
from stataflow.compat.stata import poisson

result = poisson(df, y="count_y", x=["x1", "x2"], vce="robust")
```

**Stata equivalent:**
```stata
poisson count_y x1 x2, robust
```

> `offset` and `exposure` are supported for `ppmlhdfe` (see PPML section below). They are not yet available for the `poisson` wrapper.

### Logit odds ratios and Poisson incidence-rate ratios

```python
# Logit with odds ratios
result = logit(df, y="y_binary", x=["x1", "x2"], vce="robust", or_=True)

# Poisson with incidence-rate ratios
result = poisson(df, y="count_y", x=["x1", "x2"], vce="robust", irr=True)
```

**Stata equivalent:**
```stata
logit y_binary x1 x2, robust or
poisson count_y x1 x2, robust irr
```

> Use `or_` for logit odds ratios and `irr` for Poisson incidence-rate ratios.
> Probit coefficients remain on the latent-index scale. z-statistics and
> p-values remain on the original coefficient scale.

### PPML with high-dimensional fixed effects

```python
from stataflow.compat.stata import ppmlhdfe

result = ppmlhdfe(
    df,
    y="count_y",
    x=["x1", "x2"],
    absorb="firm_id year",
    vce="cluster",
    cluster="state",
)
```

**Stata equivalent:**
```stata
ppmlhdfe count_y x1 x2, absorb(firm_id year) vce(cluster state)
```

> **Status:** Beta. Convergence can be controlled with `maxiter` and `tolerance`. eform, separation, and residuals are also supported.

### PPML with offset or exposure

```python
# Offset (already in log form)
result = ppmlhdfe(
    df, y="count_y", x=["x1", "x2"],
    absorb="firm_id year",
    offset="ln_population",
)

# Exposure (automatically logged)
result = ppmlhdfe(
    df, y="count_y", x=["x1", "x2"],
    absorb="firm_id year",
    exposure="population",
)
```

**Stata equivalent:**
```stata
ppmlhdfe count_y x1 x2, absorb(firm_id year) offset(ln_population)
ppmlhdfe count_y x1 x2, absorb(firm_id year) exposure(population)
```

### PPML eform — incidence-rate ratios

```python
result = ppmlhdfe(
    df, y="count_y", x=["x1", "x2"],
    absorb="firm_id",
    eform=True,
)
# Coefficients and CIs are exponentiated
```

**Stata equivalent:**
```stata
ppmlhdfe count_y x1 x2, absorb(firm_id) eform
```

### PPML separation detection

```python
result = ppmlhdfe(
    df, y="count_y", x=["x1", "x2"],
    absorb="firm_id year",
    separation="fe",
)
# Verbose output includes separated FE groups and dropped observations
```

**Stata equivalent:**
```stata
ppmlhdfe count_y x1 x2, absorb(firm_id year) separation(fe)
```

### PPML residual types

```python
from stataflow import PPMLHDFE

model = PPMLHDFE(data=df, y="count_y", x=["x1"], absorb="firm_id")
result = model.fit()

pearson = model.predict(type="pearson")    # Pearson residuals
deviance = model.predict(type="deviance")  # Deviance residuals
working = model.predict(type="working")    # Working residuals
```

**Stata equivalent:**
```stata
ppmlhdfe count_y x1, absorb(firm_id)
predict pearson_res, pearson
predict deviance_res, deviance
predict working_res, working
```

### PPML estat ic (AIC / BIC)

```python
from stataflow.postestimation import estat_ic

result = ppmlhdfe(df, y="count_y", x=["x1", "x2"], absorb="firm_id")
ic = estat_ic(result)
print(f"N={ic['N']}, ll={ic['ll']:.2f}, k={ic['k']}, AIC={ic['aic']:.2f}, BIC={ic['bic']:.2f}")
```

**Stata equivalent:**
```stata
estat ic
```

> `estat_ic` also works with `result` objects from `logit`, `probit`, and `poisson`.

---

## Difference-in-Differences

### BJS imputation estimator

```python
from stataflow.compat.stata import did_imputation

result = did_imputation(
    df,
    y="y",
    id="unit_id",
    time="year",
    first_treat="first_treat_year",
    cluster="state",
    allhorizons=True,
    autosample=True,
)
```

**Stata equivalent:**
```stata
did_imputation y unit_id year first_treat_year, cluster(state) allhorizons autosample
```

> `allhorizons=True` now includes both post-treatment and pre-treatment horizons (e.g. `tau1980`, `tau1981`, ...), matching Stata's output.

> **Status:** Beta. Controls, pretrends, and heterogeneous effects are supported.

### Sun-Abraham event study (auto-generated dummies)

```python
from stataflow.compat.stata import eventstudyinteract

result = eventstudyinteract(
    df,
    y="y",
    cohort="treat_group",
    control_cohort="control_group",
    time="year",
    first_treat="first_treat",
    horizons=[-3, -2, -1, 0, 1, 2, 3],
    omit=-1,
    absorb=["unit_id", "year"],
    vce="cluster",
    cluster="state",
)
```

**Stata equivalent:**
```stata
eventstudyinteract y cohort control_cohort, cohort(first_treat) control_cohort(never_treat) absorb(unit_id year) cluster(state)
```

### Sun-Abraham event study (pre-generated dummies)

```python
df["Dm3"] = (df["rel_time"] == -3).astype(float)
df["Dm2"] = (df["rel_time"] == -2).astype(float)
df["D0"]  = (df["rel_time"] == 0).astype(float)
df["Dp1"] = (df["rel_time"] == 1).astype(float)
# ... etc

result = eventstudyinteract(
    df,
    y="y",
    cohort="treat_group",
    control_cohort="control_group",
    event_dummies=["Dm3", "Dm2", "D0", "Dp1"],
    absorb=["unit_id", "year"],
    vce="cluster",
    cluster="state",
)
```

### Callaway-Sant'Anna DID

```python
from stataflow.compat.stata import csdid

result = csdid(
    df,
    y="y",
    id="unit_id",
    time="year",
    first_treat="first_treat_year",
    method="reg",
    cluster="state",
)
```

**Stata equivalent:**
```stata
csdid y, ivar(unit_id) time(year) gvar(first_treat_year) method(drimp)
csdid_estat event
```

> **Status:** Beta. `method="reg"`, `"drimp"`, and `"dripw"` are supported.

### CSDID with not-yet-treated control group

```python
result = csdid(
    df, y="y", id="unit_id", time="year",
    first_treat="first_treat_year",
    method="reg",
    notyet=True,
    cluster="state",
)
```

**Stata equivalent:**
```stata
csdid y, ivar(unit_id) time(year) gvar(first_treat_year) method(reg) notyet cluster(state)
```

> `notyet=True` uses units that have not yet been treated at time `t` as the control group. Supported for `method="reg"`.

### CSDID with doubly-robust method

```python
# Doubly-robust (requires never-treated units)
result = csdid(
    df, y="y", id="unit_id", time="year",
    first_treat="first_treat_year",
    method="drimp",
    cluster="state",
)
```

**Stata equivalent:**
```stata
csdid y, ivar(unit_id) time(year) gvar(first_treat_year) method(drimp)
```

### CSDID aggregation types

```python
# The estat() method returns different aggregation views
result = csdid(df, y="y", id="unit_id", time="year",
               first_treat="first_treat_year", method="reg")

event_agg = result.estat(aggtype="event")     # Event-study view
group_agg = result.estat(aggtype="group")     # By treatment cohort
simple_agg = result.estat(aggtype="simple")   # Single ATT
calendar_agg = result.estat(aggtype="calendar")  # By calendar time
pretrend_agg = result.estat(aggtype="pretrend")  # Joint F-test of pre-trends
```

**Stata equivalent:**
```stata
csdid_estat event
csdid_estat simple
csdid_estat group
csdid_estat calendar
csdid_estat pretrend
```

### DID imputation with controls and pretrends

```python
result = did_imputation(
    df, y="y", id="unit_id", time="year",
    first_treat="first_treat_year",
    controls=["x1", "x2"],
    unitcontrols=["unit_char"],   # Time-invariant unit characteristics
    timecontrols=["gdp_growth"],  # Common time-varying controls
    pretrends=3,                  # Test pre-treatment trend significance
    cluster="state",
)
# result._event_horizons includes pre-trend F-test p-value
```

**Stata equivalent:**
```stata
did_imputation y unit_id year first_treat_year, controls(x1 x2) unitcontrols(unit_char) timecontrols(gdp_growth) pretrends(3) cluster(state)
```

### DID imputation — save estimates and weights

```python
result = did_imputation(
    df, y="y", id="unit_id", time="year",
    first_treat="first_treat_year",
    saveestimates="estimates_file",  # Saves to named file
    saveweights=True,                # Attach weights to result
)
```

**Stata equivalent:**
```stata
did_imputation y unit_id year first_treat_year, saveestimates(estimates_file) saveweights
```

### DID imputation — heterogeneous effects

```python
result = did_imputation(
    df, y="y", id="unit_id", time="year",
    first_treat="first_treat_year",
    hetby="industry",   # Heterogeneous effects by group
    cluster="state",
)
```

**Stata equivalent:**
```stata
did_imputation y unit_id year first_treat_year, hetby(industry) cluster(state)
```

---

## Regression Discontinuity

### Sharp RD with explicit bandwidth

```python
from stataflow.compat.stata import rdrobust

result = rdrobust(df, y="vote", x="margin", c=0.0, h=15.0)
```

**Stata equivalent:**
```stata
rdrobust vote margin, c(0) h(15)
```

### Automatic bandwidth selection

```python
result = rdrobust(df, y="vote", x="margin", c=0.0, bwselect="mserd")
```

**Stata equivalent:**
```stata
rdrobust vote margin, c(0) bwselect(mserd)
```

### RD with covariates

```python
result = rdrobust(
    df, y="vote", x="margin", c=0.0,
    bwselect="mserd", covs="z",
)
```

**Stata equivalent:**
```stata
rdrobust vote margin, c(0) covs(z)
```

> **Status:** Beta. Sharp and fuzzy RD with 9 bandwidth selectors, covariates, and cluster VCE are supported.

### RD with MSE-optimal bandwidth families

```python
# Default MSE-optimal, one bandwidth each side
result = rdrobust(df, y="vote", x="margin", c=0.0, bwselect="mserd")

# Two distinct bandwidths (one per side)
result = rdrobust(df, y="vote", x="margin", c=0.0, bwselect="msetwo")

# Sum of bandwidths (same bandwidth both sides)
result = rdrobust(df, y="vote", x="margin", c=0.0, bwselect="msesum")

# Combined selectors
result = rdrobust(df, y="vote", x="margin", c=0.0, bwselect="msecomb1")
result = rdrobust(df, y="vote", x="margin", c=0.0, bwselect="msecomb2")

# Coverage-error-optimal selectors
result = rdrobust(df, y="vote", x="margin", c=0.0, bwselect="cerrd")
result = rdrobust(df, y="vote", x="margin", c=0.0, bwselect="certwo")
result = rdrobust(df, y="vote", x="margin", c=0.0, bwselect="cersum")
result = rdrobust(df, y="vote", x="margin", c=0.0, bwselect="cercomb1")
result = rdrobust(df, y="vote", x="margin", c=0.0, bwselect="cercomb2")
```

**Stata equivalent:**
```stata
rdrobust vote margin, c(0) bwselect(mserd)
```

> All 9 MSE-optimal and CER-optimal bandwidth selectors from `rdrobust` are supported.

### Fuzzy RD

```python
result = rdrobust(
    df, y="vote", x="margin", c=0.0,
    fuzzy="treatment",  # Treatment take-up variable for fuzzy design
    bwselect="mserd",
)
# Result coefficients report the Wald ratio estimate
```

**Stata equivalent:**
```stata
rdrobust vote margin, c(0) fuzzy(treatment) bwselect(mserd)
```

### RD with cluster-robust VCE

```python
# Cluster-robust VCE
result = rdrobust(
    df, y="vote", x="margin", c=0.0,
    vce="cluster", cluster="state",
    bwselect="mserd",
)

# Nearest-neighbor cluster VCE
result = rdrobust(
    df, y="vote", x="margin", c=0.0,
    vce="nncluster", cluster="state",
    bwselect="mserd",
)
```

**Stata equivalent:**
```stata
rdrobust vote margin, c(0) vce(cluster state) bwselect(mserd)
rdrobust vote margin, c(0) vce(nncluster state) bwselect(mserd)
```

### RD with mass points and frequency weights

```python
result = rdrobust(
    df, y="vote", x="margin", c=0.0,
    masspoints="adjust",  # "adjust" (default) or "check"
    bwcheck=10,           # Number of masspoints checks
    weights="pop_weight",  # Frequency weights
    bwselect="mserd",
)
```

**Stata equivalent:**
```stata
rdrobust vote margin, c(0) masspoints(adjust) bwselect(mserd) [fw=pop_weight]
```

### rdplot — RD visualization

```python
from stataflow.compat.stata import rdplot

plot_result = rdplot(
    df, y="vote", x="margin", c=0.0,
    nbins=20,                    # Number of bins or IMSE-optimal
    binselect="esmv",            # Evenly-spaced mimicking variance
    p=4,                         # Polynomial order for fit overlay
)
# plot_result["bins"]  -> DataFrame of bin statistics
# plot_result["fit"]   -> DataFrame of polynomial fit coordinates
# plot_result["info"]  -> metadata dict
```

**Stata equivalent:**
```stata
rdplot vote margin, c(0) nbins(20) binselect(esmv)
```

---

## Factor Variables

All recipes below use `regress`, but factor syntax works across every command that accepts an `x` argument.

### Create dummy variables from a categorical

```python
result = regress(df, y="y", x=["x1", "i.group"])
```

**Stata equivalent:**
```stata
reg y x1 i.group
```

### Change the base category

```python
result = regress(df, y="y", x=["x1", "ib2.group"])
```

**Stata equivalent:**
```stata
reg y x1 ib2.group
```

### Omit a specific category

```python
result = regress(df, y="y", x=["x1", "o3.group"])
```

**Stata equivalent:**
```stata
reg y x1 o3.group
```

### Continuous × continuous interaction

```python
# Interaction only
result = regress(df, y="y", x=["x1", "x2", "c.x1#c.x2"])

# Main effects + interaction
result = regress(df, y="y", x=["c.x1##c.x2"])
```

**Stata equivalent:**
```stata
reg y x1 x2 c.x1#c.x2
reg y c.x1##c.x2
```

### Categorical × categorical interaction

```python
result = regress(df, y="y", x=["i.group1##i.group2"])
```

**Stata equivalent:**
```stata
reg y i.group1##i.group2
```

### Categorical × continuous interaction

```python
result = regress(df, y="y", x=["i.group##c.x1"])
```

**Stata equivalent:**
```stata
reg y i.group##c.x1
```

### Naked variables inside `#` / `##` are treated as continuous

```python
# Equivalent
result = regress(df, y="y", x=["c.x1##c.x2"])
result = regress(df, y="y", x=["x1##x2"])
```

> **Not supported** (raises `ValueError`): `ib.group` without a base level, `L.x` / `F.x` time-series operators. Three-way and higher-order interactions (e.g., `i.g1#i.g2#c.x3`) are supported.

---

## Working with Results

### Print a formatted regression table

```python
result = regress(df, y="y", x=["x1", "x2"], vce="robust")

# Stata-style regression table
result.display()

# With confidence intervals
result.display(show_ci=True)

# Get as string (for logging, saving)
text = result.summary()
```

For programmatic access:

```python
for c in result.coefficients:
    print(f"{c.name:<15} {c.beta:>10.6f} {c.std_err:>10.6f} "
          f"{c.t_stat:>8.2f} {c.p_value:>8.3f}")
```

### Extract coefficients to a pandas DataFrame

```python
import pandas as pd

coef_df = pd.DataFrame([
    {
        "var": c.name,
        "beta": c.beta,
        "se": c.std_err,
        "t": c.t_stat,
        "p": c.p_value,
        "ci_low": c.ci_low,
        "ci_high": c.ci_high,
    }
    for c in result.coefficients
])
```

### Access fit statistics

```python
print(f"R-squared:          {result.fit.r2:.4f}")
print(f"Adjusted R-squared: {result.fit.r2_adj:.4f}")
print(f"F statistic:        {result.fit.f_stat:.2f}")
print(f"F p-value:          {result.fit.f_pvalue:.4f}")
print(f"Model df:           {result.fit.df_model:.0f}")
print(f"Residual df:        {result.fit.df_resid:.0f}")
print(f"Observations:       {result.sample.nobs}")
print(f"RMSE:               {result.fit.rmse:.4f}")
if result.fit.df_a:
    print(f"Absorbed df:        {result.fit.df_a:.0f}")
```

### Save results to CSV or Stata format

```python
# CSV
coef_df.to_csv("regression_results.csv", index=False)

# Stata .dta
coef_df.to_stata("regression_results.dta", write_index=False)
```

### Access RD-specific extras

```python
result = rdrobust(df, y="vote", x="margin", c=0.0, bwselect="mserd")

extra = result._rd_extras
print(f"Bandwidth h = {extra['h_l']:.3f}")
print(f"Bias bandwidth b = {extra['b_l']:.3f}")
print(f"Effective sample left = {extra['N_h_l']}")
print(f"Effective sample right = {extra['N_h_r']}")
```

### Access event-study horizons

```python
result = did_imputation(...)
print(result._event_horizons)
```

### Access fixed effects estimates

```python
result = reghdfe(df, y="y", x=["x1"], absorb="firm_id year", savefe=True)
fe_df = result.fixed_effects  # pd.DataFrame
for absorb_var in fe_df["absorb_var"].unique():
    subset = fe_df[fe_df["absorb_var"] == absorb_var]
    print(f"{absorb_var}: {len(subset)} levels")
```

### Access first-stage statistics (IV HDFE)

```python
result = ivreghdfe(..., first=True)
first = result.first_stage  # dict keyed by endogenous variable name
for var, stats in first.items():
    print(f"{var}: R2={stats['r2']:.4f}, Partial R2={stats['partial_r2']:.4f}")
```

### Access weak instrument diagnostics

```python
result = ivreghdfe(..., vce="robust")
print(f"KP LM stat:    {result.idstat:.3f}")   # Kleibergen-Paap underidentification
print(f"CD Wald F:     {result.widstat:.3f}")  # Cragg-Donald weak identification
print(f"Stock-Yogo 10%: {result.widstat_cv:.1f}")  # Critical value at 10%
```

### Access Hansen J overidentification test (GMM2S)

```python
result = ivreghdfe(..., estimator="gmm2s")
print(f"Hansen J: {result.hansen_j:.3f}")
```

### Use estat_summarize and estat_ic

```python
from stataflow.postestimation import estat_summarize, estat_ic

result = reghdfe(df, y="y", x=["x1", "x2"], absorb="firm_id")

# estat summarize
summary = estat_summarize(result, data=df, variables=["y", "x1", "x2"], dep_var="y")

# estat ic (for ML models: logit, probit, poisson, ppmlhdfe)
result = ppmlhdfe(df, y="count_y", x=["x1", "x2"], absorb="firm_id")
ic = estat_ic(result)
print(f"AIC={ic['aic']:.2f}, BIC={ic['bic']:.2f}")
```

### Access PPMLHDFE-specific fit statistics

```python
result = ppmlhdfe(df, y="count_y", x=["x1"], absorb="firm_id")
print(f"Deviance:    {result.fit.deviance:.2f}")
print(f"Pseudo R2:   {result.fit.pseudo_r2:.4f}")
print(f"Log-likelihood: {result.fit.ll:.2f}")
```

---

## Common Gotchas

### `x` must always be a list

```python
# Wrong
result = regress(df, y="y", x="x1")

# Correct
result = regress(df, y="y", x=["x1"])
```

### Unsupported parameters are hard-rejected

StataFlow raises `ValueError` or `NotImplementedError` for any parameter that is not explicitly supported. It never silently ignores options. Check `command-support-matrix/` for the exact supported subset of each command.

### Clustering

Two-way clustering (Cameron-Gelbach-Miller 2011) is supported on `regress`, `reghdfe`, `ivreghdfe`, and `ppmlhdfe` via `cluster=["var1", "var2"]`. All commands support single-cluster robust inference. Three-way and higher clustering is not yet available.

Driscoll-Kraay panel HAC standard errors are available on `reghdfe` via `vce="dkraay"` with a required `timevar` parameter.

### Post-estimation

Most `compat.stata` estimation wrappers return a `ResultSchema` with
coefficients, standard errors, and fit statistics. `csdid()` returns a fitted
`CSDID` model; use its `.result` or display methods for the default event
aggregation. For `predict` and `margins`, use the core estimator layer
(`stataflow` namespace) directly.

Post-estimation utilities `estat_summarize` and `estat_ic` are available in `stataflow.postestimation` and accept `ResultSchema` from either layer.

### Driscoll-Kraay VCE requires a time variable

```python
# Wrong — missing timevar
result = reghdfe(df, y="y", x=["x1"], absorb="firm_id", vce="dkraay")

# Correct
result = reghdfe(df, y="y", x=["x1"], absorb="firm_id", vce="dkraay", timevar="year")
```

---

*Last updated: July 2026. For per-command support matrices, see
[`command-support-matrix/`](./command-support-matrix/README.md).*
