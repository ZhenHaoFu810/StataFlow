# StataFlow User Guide

## 1. What is StataFlow?

StataFlow (`stataflow`) is a Python econometrics toolkit that reproduces **Stata 17** estimation results with high precision. It is designed for researchers, data scientists, and economists who want to run Stata-equivalent regressions in Python.

StataFlow provides **two usage layers**:

- **`stataflow.compat.stata`** — Stata-compatible command functions (`regress()`, `reghdfe()`, `logit()`, etc.). Recommended for most users. The syntax closely mirrors Stata.
- **`stataflow` (core estimators)** — Python-native estimator classes (`OLS`, `Logit`, `PPMLHDFE`, etc.). For advanced users who need programmatic control, post-estimation, and integration with Python data pipelines.

Every public command is validated against Stata 17 through **dual-run testing**: identical synthetic and real datasets are run in both Stata and Python, with field-level comparison of coefficients, standard errors, t-statistics, and fit statistics.

## 2. Installation

**Requirements:** Python 3.10+, NumPy, pandas, SciPy, scikit-learn, PyYAML.

```bash
pip install StataFlow
```

For development (editable install from source):

```bash
git clone https://github.com/ZhenHaoFu810/StataFlow.git
cd StataFlow
pip install -e .
```

**Verify installation:**

```python
import stataflow
print(stataflow.__version__)  # e.g., "1.1.0"
```

> **Note:** A local Stata 17 installation is only needed if you want to run the golden dual-run tests. The package itself does not require Stata for normal use.

## 3. Core Concepts: From Stata to Python

### 3.1 DataFrames replace Stata's in-memory data

In Stata, data lives in memory after `use`. In Python, data lives in a `pandas.DataFrame`:

```python
import pandas as pd

# Read Stata .dta
df = pd.read_stata("mydata.dta")

# Read CSV
df = pd.read_csv("mydata.csv")

# Inspect
df.head(10)       # First 10 rows (like browse)
df.describe()     # Summary statistics (like summarize)
```

### 3.2 Command parameter mapping

| Stata syntax | StataFlow (Python) | Notes |
|---|---|---|
| `reg y x1 x2` | `regress(df, y="y", x=["x1", "x2"])` | `x` must be a list |
| `reg y x1 x2, robust` | `regress(df, y="y", x=["x1", "x2"], vce="robust")` | |
| `reg y x1 x2, cluster(id)` | `regress(df, y="y", x=["x1", "x2"], vce="cluster", cluster="id")` | |
| `absorb(firm year)` | `absorb="firm year"` or `absorb=["firm", "year"]` | Both forms work |
| `i.group##c.x` | `x=["i.group##c.x"]` | Factor syntax supported |
| `[aw=w]` | `aweight="w"` | Analytic weights only |

### 3.3 Reading results

All commands return a `ResultSchema` object. The easiest way to see results:

```python
result = regress(df, y="wage", x=["edu", "exper"], vce="robust")

# Stata-style regression table
result.display()

# With confidence intervals
result.display(show_ci=True)

# Get as string
text = result.summary()
```

For programmatic access:

```python
for c in result.coefficients:
    print(f"{c.name}: b={c.beta:.6f}, se={c.std_err:.6f}, t={c.t_stat:.2f}, p={c.p_value:.3f}")

print(f"R2 = {result.fit.r2:.4f}")
print(f"N = {result.sample.nobs}")

# In Jupyter/IPython, just type the variable name
result  # calls __repr__ -> shows summary table
```

## 4. Your First Model (5-Minute Walkthrough)

```python
import pandas as pd
import numpy as np
from stataflow.compat.stata import regress

# 1. Create some data
rng = np.random.default_rng(42)
df = pd.DataFrame({
    "wage": 5 + 1.5 * rng.normal(0, 1, 500) + rng.normal(0, 0.5, 500),
    "edu": rng.normal(12, 3, 500),
    "exper": rng.normal(10, 5, 500),
    "state": rng.choice(["CA", "TX", "NY", "FL"], 500),
})
df.loc[rng.choice(500, 20, replace=False), "wage"] = np.nan  # Some missing

# 2. Simple OLS
result = regress(df, y="wage", x=["edu", "exper"])
print(result.summary())

# 3. OLS with robust SE
result_robust = regress(df, y="wage", x=["edu", "exper"], vce="robust")

# 4. OLS with cluster SE
result_cluster = regress(df, y="wage", x=["edu", "exper"],
                         vce="cluster", cluster="state")

# 5. Extract to pandas DataFrame
coef_df = pd.DataFrame([
    {"var": c.name, "beta": c.beta, "se": c.std_err,
     "t": c.t_stat, "p": c.p_value}
    for c in result_robust.coefficients
])
print(coef_df)

# 6. Export to CSV
coef_df.to_csv("results.csv", index=False)
```

## 5. Choosing the Right Command

| I want to... | Use this command | Status |
|---|---|---|
| Run a simple OLS regression | `regress()` | Stable |
| Control for one fixed effect | `areg()` or `xtreg_fe()` | Stable |
| Control for multiple fixed effects (HDFE) | `reghdfe()` | Beta |
| Run 2SLS with IV | `ivregress_2sls()` | Stable |
| Run IV + multiple fixed effects | `ivreghdfe()` | Beta |
| Model a binary outcome (0/1) | `logit()` or `probit()` | Stable |
| Model count data | `poisson()` | Stable |
| Count data + multiple fixed effects | `ppmlhdfe()` | Beta |
| Estimate treatment effects with staggered adoption (DID) | `did_imputation()`, `csdid()`, `eventstudyinteract()` | Beta |
| Run a regression discontinuity design | `rdrobust()` | Beta |

See the [Command Support Matrix](./command-support-matrix/README.md) for exact supported parameters per command.

## 6. The Two API Layers

### 6.1 Stata-compatible command layer (recommended)

Import from `stataflow.compat.stata`:

```python
from stataflow.compat.stata import regress, reghdfe, logit, ivregress_2sls

result = regress(df, y="wage", x=["edu", "exper"], vce="robust")
result = reghdfe(df, y="wage", x=["edu", "exper"],
                 absorb="firm_id year", vce="cluster", cluster="state")
result = logit(df, y="inlf", x=["nwifeinc", "educ", "exper"])
result = ivregress_2sls(df, y="lwage", x_exog=["edu"],
                         x_endog=["exper"], instruments=["age", "kidslt6"],
                         vce="robust")
```

Returns a `ResultSchema` with `.coefficients`, `.fit`, `.sample`, `.summary()`.

For IV commands, you can request first-stage diagnostics with `first=True`. The result object exposes a `first_stage` dict structured like this:

```python
result = ivregress_2sls(
    df, y="lwage", x_exog=["edu"], x_endog=["exper"],
    instruments=["age", "kidslt6"], vce="robust", first=True
)
for endog_var, stats in result.first_stage.items():
    print(f"{endog_var}: R2={stats['r2']:.4f}, "
          f"partial R2={stats['partial_r2']:.4f}, "
          f"F={stats['f_stat']:.2f}")
```

Weak-instrument diagnostics (`idstat`, `widstat`, `widstat_cv`) and overidentification tests (`hansen_j` / Sargan) are also attached automatically when applicable.

### 6.2 Core estimator layer (advanced)

Import from `stataflow`:

```python
from stataflow import OLS, AbsorbingOLS, Logit, PPMLHDFE

model = OLS(data=df, y="wage", x=["edu", "exper"])
result = model.fit(vce="robust")
predictions = model.predict(type="xb")

model = AbsorbingOLS(data=df, y="wage", x=["edu"], absorb="firm_id")
result = model.fit(vce="cluster", cluster="state")
```

Use this layer when you need:
- `predict()` with multiple types (`xb`, `mu`, `pr`, `residuals`, `stdp`)
- `margins()` for AME and MEM
- Programmatic iteration over models
- Direct integration with Python ML pipelines

## 7. Factor Variables

StataFlow supports Stata-style factor variable notation in all `x` arguments:

| Pattern | Meaning | Example |
|---|---|---|
| `i.var` | Create dummy variables from categorical | `i.state` |
| `ibN.var` | Set base category to N | `ib2.state` |
| `oN.var` | Omit category N | `o3.state` |
| `c.var` | Explicitly treat as continuous | `c.age` |
| `var1#var2` | Interaction only | `state#post` |
| `var1##var2` | Main effects + interaction | `state##post` |

**Important defaults:**
- Bare variables (without `i.` or `c.` prefix) inside `#` / `##` are treated as **continuous**, matching common Stata usage.
- A bare variable as a main effect (e.g., `x=["x1"]`) is treated according to its dtype.

**Not supported:** `L.x` / `F.x` time-series operators, `ib.` without a level. Three-way and higher-order interactions (e.g., `i.g1#i.g2#c.x3`) are supported.

## 8. Post-Estimation

### 8.1 Prediction (core estimator layer)

```python
from stataflow import OLS, Logit, PPMLHDFE

# OLS
model = OLS(data=df, y="y", x=["x1", "x2"])
result = model.fit()
xb = model.predict(type="xb")          # Linear predictor
residuals = model.predict(type="residuals")

# Logit
model = Logit(data=df, y="y_bin", x=["x1", "x2"])
result = model.fit()
pr = model.predict(type="pr")          # Predicted probability
mu = model.predict(type="mu")          # Same as pr for logit

# PPMLHDFE
model = PPMLHDFE(data=df, y="count_y", x=["x1"], absorb="firm_id")
result = model.fit()
mu = model.predict(type="mu")          # Expected count
pearson = model.predict(type="pearson")  # Pearson residuals
```

### 8.2 Fit statistics

All `ResultSchema` objects contain fit statistics accessible via `result.fit`:

```python
print(result.fit.r2)           # R-squared
print(result.fit.r2_adj)       # Adjusted R-squared
print(result.fit.rmse)         # Root MSE
print(result.fit.f_stat)       # F-statistic
print(result.fit.ll)           # Log-likelihood (ML models)
print(result.fit.deviance)     # Deviance (Poisson/PPML)
```

### 8.3 Known alignment residuals

A small number of StataFlow outputs are expected to differ from Stata 17 within documented tolerances. These are **not bugs**; they are structural consequences of implementation choices and are governed by ADRs.

| Area | Residual | Tolerance | Explanation |
|------|----------|-----------|-------------|
| 2-way cluster `_cons` SE (`reghdfe`, `ivreghdfe`, `ppmlhdfe`) | ~2–16% | Documented | [ADR-0003](../adr/ADR-0003-lsdv-cons-se-under-multiway-cluster.md): LSDV vs iterative-demeaning structural difference. **Slope SEs remain aligned to `< 1e-6`.** |
| 2-way cluster rank-deficiency fallback | RuntimeWarning | Documented | When the Cameron-Gelbach-Miller meat matrix is not positive semi-definite, a PSD fix is applied. Slope SEs in non-rank-deficient cases remain exact. |
| `ivreghdfe` cluster `stdp` when cluster nests all FEs | ~0.28% | `rtol=5e-3` | Known small-sample factor difference |
| `ppmlhdfe` residuals | ~0.35% | `rtol=5e-3` | IRLS/HDFE convergence precision difference |

### 8.4 estat commands

```python
from stataflow.postestimation import estat_summarize, estat_ic

# Descriptive statistics for estimation sample
summary = estat_summarize(result, data=df,
                          variables=["y", "x1", "x2"],
                          dep_var="y")

# Information criteria (logit, probit, poisson, ppmlhdfe)
result = logit(df, y="y_bin", x=["x1", "x2"])
ic = estat_ic(result)
print(f"AIC = {ic['aic']:.2f}, BIC = {ic['bic']:.2f}")
```

## 9. FAQ / Stata Migration Troubleshooting

### Q1: Where is `_cons`?
The constant term is included by default (equivalent to Stata's behavior). It appears as `_cons` in the coefficient table. Use `noconstant=True` to suppress it.

### Q2: How does StataFlow handle missing values?
By default, any row with a missing value in `y`, `x`, weights, cluster, FE, or IV variables is dropped before estimation. This matches Stata's default listwise deletion.

### Q3: Why does StataFlow hard-reject unknown parameters instead of warning?
StataFlow never silently ignores options. If a parameter is not explicitly supported, you get a `ValueError` or `NotImplementedError`. This is a design choice: you should always know exactly what the package is doing. Check the [Command Support Matrix](./command-support-matrix/README.md) for what's supported.

### Q4: How do I get cluster-robust standard errors?
Pass `vce="cluster"` and `cluster="variable"`. For two-way clustering, pass `cluster=["var1", "var2"]`. Two-way clustering is supported on `regress`, `reghdfe`, `ivreghdfe`, and `ppmlhdfe`.

> **Note:** In 2-way cluster HDFE/IV/PPML models, you may see a `RuntimeWarning` if the moment matrix is rank-deficient (for example, when one cluster dimension is small or nested within fixed effects). This is a documented fallback; slope SEs in non-rank-deficient cases remain aligned to `< 1e-6`. The constant-term SE under 2-way clustering may deviate from Stata by up to ~3% on synthetic data and ~16% on real data; see [ADR-0003](../adr/ADR-0003-lsdv-cons-se-under-multiway-cluster.md).

### Q5: What weight types are supported?
Only `aweight` (analytic weights) is supported. `fweight`, `pweight`, and `iweight` are not yet available.

### Q6: Can I use factor variables with HDFE commands?
Yes. Factor variable syntax works in all commands:
```python
reghdfe(df, y="wage", x=["i.industry##c.post"], absorb="firm_id year")
```

### Q7: Does StataFlow support multi-way (3+) clustering?
No. Two-way clustering is supported on `regress`, `reghdfe`, `ivreghdfe`, and `ppmlhdfe`. Three-way and higher is planned but not yet implemented.

### Q8: How do I reproduce a Stata `.do` file in StataFlow?
Map each Stata command to its Python equivalent. See the [Cookbook](./cookbook.md) for copy-paste recipes with Stata equivalents side by side.

### Q9: What's the difference between `xtreg_fe` and `reghdfe`?
`xtreg_fe` is for one FE (the "panel" variable). `reghdfe` supports multiple FEs + advanced features like MAP, slopes, and Driscoll-Kraay VCE. For simple panel models with one FE, both work. For anything with 2+ FEs, use `reghdfe`.

### Q10: Are the Stata community commands fully replicated?
No. Commands like `reghdfe`, `ivreghdfe`, `ppmlhdfe`, `did_imputation`, `eventstudyinteract`, `csdid`, and `rdrobust` are implemented as **verified high-frequency subsets** — the most commonly used paths are available and verified. Uncommon options are hard-rejected. See the per-command matrices for exact coverage.

## 10. Where to Go Next

- **[Cookbook](./cookbook.md)** — Copy-paste recipes for every command with Stata equivalents
- **[Command Support Matrices](./command-support-matrix/README.md)** — Exact parameter coverage per command
- **[Examples](../examples/)** — Runnable demo scripts
- **[Validation Evidence](./validation/)** — Dual-run verification results
- **[README](../README.md)** — Project overview and installation

---

*Last updated: 2026-06-04*
