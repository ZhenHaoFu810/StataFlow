# Support Matrix: `ivreghdfe`

## Completeness Status

**Phase B+ / IV Completion** — 2SLS + GMM2S + LIML (including Fuller and k-class) + multiple FE (1+ FEs dual-run verified; 3+ FE covered in synthetic tests) + robust/cluster VCE + `noconstant` + `keepsingletons` + predict (`xb`/`xbd`/`residuals`/`d`/`dresiduals`/`stdp`) + first-stage diagnostics + weak-instrument diagnostics are implemented and verified. Wave 11 added `predict(type="stdp")` for OLS, robust, and cluster VCE. Multi-way clustering beyond 2-way and broader command options are missing.

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
| `cluster` | `str \| list[str]` | Cluster variable(s); pass a list for 2-way cluster-robust VCE (required when `vce="cluster"`) |
| `noconstant` | `bool` | Omit constant term |
| `keepsingletons` | `bool` | Retain singleton observations |
| `first` | `bool` | If `True`, compute and return first-stage diagnostics in `result.first_stage` |
| `estimator` | `str` | `"2sls"` (default), `"gmm2s"`, `"liml"` |
| `fuller` | `float` | Fuller adjustment for LIML (e.g. `fuller=1`); only valid with `estimator="liml"` |
| `kclass` | `float` | User-specified k-class parameter; only valid with `estimator="liml"` |
| `missing` | `str` | `"drop"` only |

## Supported Result Fields

Coefficients, standard errors, t-statistics, p-values, confidence intervals, R-squared, adjusted R-squared, RMSE, absorbed degrees of freedom (`df_a`).

When `estimator="gmm2s"`, `result.hansen_j` and `result.hansen_j_df` contain the Hansen J overidentification statistic and its degrees of freedom.

When `estimator="liml"`, `result.liml_k` and `result.liml_lambda` contain the k-class parameter and the minimum eigenvalue.

When `first=True`, `result.first_stage` contains per-endogenous-variable diagnostics:
- `r2` — first-stage R-squared
- `partial_r2` — partial R-squared (after partialling out included exogenous)
- `shea_r2` — Shea partial R-squared (equals `partial_r2` for single endogenous variable)
- `f_stat` — F-statistic of excluded instruments
- `f_pvalue` — p-value of F-statistic
- `df` — numerator degrees of freedom (number of excluded instruments)
- `df_r` — denominator degrees of freedom

Weak-instrument diagnostics are always computed and attached to the result:
- `idstat` — Kleibergen-Paap rk LM statistic (underidentification test)
- `iddf` — degrees of freedom for underidentification test
- `idp` — p-value for underidentification test
- `widstat` — Kleibergen-Paap rk Wald F statistic (weak identification test)
- `sy_10pct`, `sy_15pct`, `sy_20pct`, `sy_25pct` — Stock-Yogo critical values for maximal IV sizes of 10%, 15%, 20%, and 25%

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
- `predict(type="stdp")` — standard error of the linear prediction; OLS, robust, and cluster VCE verified

## Planned Parameters

- `ffirst` compact first-stage diagnostics
- 3-way and higher multi-way clustering

## Explicitly Unsupported Parameters

`fstage`, `savefirst`, `savetf`, `replace`, `compact`, `pool`, `dfadj`, and all other ivreghdfe-specific options are hard-rejected via `ValueError`.

## Alignment Evidence


- Synthetic cases: `tests/golden/test_w2_ivreghdfe_basic.py`, `tests/golden/test_w2_ivreghdfe_cluster.py`
- Real-data cases: `tests/golden/test_w2_ivreghdfe_real_panel.py`
- Factor-syntax case: `tests/golden/test_a2_factor_ivreghdfe_basic.py` — `ivreghdfe y c.x1##i.g (x_endog = z1 z2), absorb(firm year)`
- **First-stage diagnostics case**: `tests/golden/test_w7_ivreghdfe_first_basic.py` — `ivreghdfe y x1 (x2 = z1 z2), absorb(entity_id) first`; verifies F-statistic, partial R², and Shea R² field-level alignment
- **2-way cluster case**: `tests/golden/test_w7_ivreghdfe_2way_cluster.py` — IV + 2 FE + 2-way cluster; slope SEs < 1e-6, _cons SE known limitation
- **GMM2S case**: `tests/golden/test_w10_gmm2s_overid.py` — GMM2S with ols VCE; beta, SE, Hansen J < 1e-6
- **GMM2S cluster case**: `tests/golden/test_w10_gmm2s_cluster.py` — GMM2S with cluster VCE; beta, SE, Hansen J < 1e-6
- **LIML case**: `tests/golden/test_w10_liml_weak.py` — LIML with one absorbed FE; beta, SE, k-class < 1e-6
- **LIML Fuller case**: `tests/golden/test_w10_fuller_adjust.py` — LIML with `fuller(1)`; beta, SE, k-class < 1e-6
- **LIML k-class case**: `tests/golden/test_w10_kclass_basic.py` — LIML with `kclass(0.5)`; beta, SE, k-class < 1e-6
- **Real-data GMM2S case**: `tests/golden/test_w10_card_gmm2s.py` — Card returns-to-schooling data with `absorb(south)`; beta, SE, Hansen J < 1e-6
- **Real-data LIML case**: `tests/golden/test_w10_card_liml.py` — Card data with `absorb(south)`; beta, SE, k-class < 1e-6
- **Weakiv synthetic case**: `tests/golden/test_w10_weakiv_test.py` — `ivreghdfe y x1 (x2 = z1 z2), absorb(entity_id)`; OLS/robust/cluster VCE; idstat, widstat, Stock-Yogo critical values < 1e-4
- **Weakiv real-data case**: `tests/golden/test_w10_card_weakiv.py` — Card data with `absorb(south)`; idstat, widstat, Stock-Yogo critical values < 1e-4
- **Postestimation stdp case**: `tests/golden/test_w11_reghdfe_stdp.py` — `predict(type="stdp")` for IV with OLS, robust, and cluster VCE; OLS/robust < 1e-6, cluster < 5e-3
- Phase B synthetic behavior: `tests/test_hdfe_synthetic.py` (noconstant, keepsingletons, predict consistency)
- Local source mirror: `research/vendor/stata_community/ivreghdfe/`
- Stata 17 dual-run verified for 2SLS, GMM2S, and LIML with 1+ absorbed FEs, single cluster, 2-way cluster VCE, and first-stage diagnostics

## Core Implementation

`src/stataflow/estimators/iv.py` (`IVAbsorbingOLS`)
