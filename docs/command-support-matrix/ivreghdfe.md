# Support Matrix: `ivreghdfe`

## Completeness Status

**Partial / Phase B Subset** — 2SLS + multiple FE (1–2 FE path dual-run verified, 3+ FE covered in synthetic tests) + robust/cluster VCE + `noconstant` + `keepsingletons` + predict (`xb`/`xbd`/`residuals`/`d`/`dresiduals`) is implemented and verified. First-stage diagnostics, weak-instrument tests, LIML/GMM, multi-way clustering, and broader command options are missing.

## Command Target

Two-stage least squares with high-dimensional fixed effects, aligned with Stata community command `ivreghdfe`.

## Python Entry

```python
from stataflow.compat.stata import ivreghdfe

result = ivreghdfe(
    data, y="depvar",
    x_exog=["x1"], x_endog=["x2"], instruments=["z1", "z2"],
    absorb=["firm_id", "year_id"], vce="cluster", cluster="industry"
)
```

## Supported Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `pd.DataFrame` | Input data |
| `y` | `str` | Dependent variable |
| `x_exog` | `list[str]` | Exogenous regressors |
| `x_endog` | `list[str]` | Endogenous regressors |
| `instruments` | `list[str]` | Excluded instruments |
| `absorb` | `str \| list[str]` | Categorical variables to absorb (1+ supported) |
| `vce` | `str` | `"ols"`, `"robust"`, `"cluster"` |
| `cluster` | `str` | Cluster variable (required when `vce="cluster"`) |
| `noconstant` | `bool` | Omit constant term |
| `keepsingletons` | `bool` | Retain singleton observations |
| `missing` | `str` | `"drop"` only |

## Supported Result Fields

Coefficients, standard errors, t-statistics, p-values, confidence intervals, R-squared, adjusted R-squared, RMSE, absorbed degrees of freedom (`df_a`).

## Factor Variable Support

The wrapper layer automatically expands Stata-style factor terms in `x_exog`, `x_endog`, and `instruments`:

- `c.x1`, `i.g`
- `ib2.g`, `b2.g` (explicit base level)
- `o2.g` (explicit omitted level)
- `c.x1#c.x2`, `c.x1##c.x2`
- `i.g1#i.g2`, `i.g1##i.g2`
- `i.g1#c.x1`, `i.g1##c.x1`
- `c.x1#i.g1`, `c.x1##i.g1` (mixed-order symmetry, equivalent to `i.g1#c.x1` / `i.g1##c.x1`)
- `x1#x2`, `x1##x2` (bare variables inside `#` / `##` are treated as continuous)
- `x1##i.g`, `i.g##x1` (mixed bare continuous and categorical)

`absorb` also accepts Stata-style space-separated strings (e.g., `absorb="firm year"`) in addition to Python lists.

Unsupported factor syntax (`ib.` without level, `o.` without level, `b.` without level, time-series operators, three-way+ interactions) is hard-rejected with `ValueError`.

## Postestimation (Core Estimator Layer Only)

The `compat.stata` wrapper returns a `ResultSchema` object. To use `predict()`, call the core estimator (`stataflow.estimators.IVAbsorbingOLS`) directly.

- `predict(type="xb")`
- `predict(type="xbd")`
- `predict(type="residuals")`
- `predict(type="d")`
- `predict(type="dresiduals")`

## Planned Parameters

- First-stage diagnostics (`first`, `ffirst`)
- Weak-instrument tests (`weakiv`)
- LIML / GMM estimators
- Multi-way clustering

## Explicitly Unsupported Parameters

`gmm2s`, `liml`, `kclass`, `fstage`, `savefirst`, `savetf`, `replace`, `compact`, `pool`, `dfadj`, and all other ivreghdfe-specific options are hard-rejected via `ValueError`.

## Alignment Evidence


- Synthetic cases: `tests/golden/test_w2_ivreghdfe_basic.py`, `tests/golden/test_w2_ivreghdfe_cluster.py`
- Real-data cases: `tests/golden/test_w2_ivreghdfe_real_panel.py`
- Factor-syntax case: `tests/golden/test_a2_factor_ivreghdfe_basic.py` — `ivreghdfe y c.x1##i.g (x_endog = z1 z2), absorb(firm year)`
- Phase B synthetic behavior: `tests/test_hdfe_synthetic.py` (noconstant, keepsingletons, predict consistency)
- Local source mirror: `research/vendor/stata_community/ivreghdfe/`
- Stata 17 dual-run verified for 2SLS with 1+ absorbed FEs and cluster VCE

## Core Implementation

`src/stataflow/estimators/iv.py` (`IVAbsorbingOLS`)
