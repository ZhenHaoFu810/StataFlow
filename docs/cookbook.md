# StataFlow Cookbook

This cookbook provides short, copy-pasteable recipes for common econometric tasks in StataFlow. Each recipe shows the Python code alongside the equivalent Stata command.

> **Status legend:** **Stable** = synthetic + real-data verified against Stata 17; **Alpha** = validated subset, unsupported parameters are hard-rejected.

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

> **Status:** Alpha. Validated for common 2SLS + FE paths.

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

> `offset` and `exposure` are not yet supported and will raise `NotImplementedError`.

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

> **Status:** Alpha. Convergence can be controlled with `maxiter` and `tolerance`.

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

> **Status:** Alpha.

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

> **Status:** Alpha. Only `method="reg"` is currently supported.

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

> **Status:** Alpha — Partial. Automatic selectors may use documented numerical tolerances.

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

> **Not supported** (raises `ValueError`): `ib.group` without a base level, `L.x` / `F.x` time-series operators, and three-way interactions such as `i.g1#i.g2#c.x3`.

---

## Working with Results

### Print a formatted regression table

```python
result = regress(df, y="y", x=["x1", "x2"], vce="robust")

print(f"{'Variable':<15} {'Coef.':>10} {'Std.Err.':>10} {'t':>8} {'P>|t|':>8} {'[95% CI]':>20}")
print("-" * 75)
for c in result.coefficients:
    print(f"{c.name:<15} {c.beta:>10.4f} {c.std_err:>10.4f} "
          f"{c.t_stat:>8.2f} {c.p_value:>8.4f} [{c.ci_low:>8.4f}, {c.ci_high:>8.4f}]")
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
print(f"R-squared:         {result.fit.r2:.4f}")
print(f"Adjusted R-squared: {result.fit.r2_a:.4f}")
print(f"F statistic:        {result.fit.f_statistic:.2f}")
print(f"F p-value:          {result.fit.f_pvalue:.4f}")
print(f"Model df:           {result.fit.df_model:.0f}")
print(f"Residual df:        {result.fit.df_resid:.0f}")
print(f"Observations:       {result.sample.nobs}")
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

StataFlow raises `ValueError` or `NotImplementedError` for any parameter that is not explicitly supported. It never silently ignores options. Check `docs/command-support-matrix/` for the exact supported subset of each command.

### Clustering

`regress` supports two-way clustering (e.g., `cluster=["state", "year"]`). All other commands currently use single-cluster robust inference only.

### Post-estimation is on the core layer only

The `compat.stata` wrappers return a `ResultSchema`. For programmatic prediction or margins, use the underlying estimator classes in `stataflow.estimators` directly.

---

*Last updated: 2026-04-23. For per-command support matrices, see `docs/command-support-matrix/`.*
