# Support Matrix: `reghdfe`

## Completeness Status

**Beta** — multiple categorical FE absorption (1+ FEs) is implemented, tested, and validated by Stata 17 comparison with expanded synthetic coverage. Supported postestimation includes `keepsingletons`, `noconstant`, `predict` (`xb`, `xbd`, `d`, `residuals`, `dresiduals`, `stdp`), and `estat_summarize`. The MAP (Method of Alternating Projections) kernel supports models with more than 10K FE levels that previously caused OOM under LSDV. Individual slope absorption (`absorb(var##c.slope)`) and Driscoll-Kraay panel HAC standard errors (`vce(dkraay)`) are also supported. This is still **not** a full reproduction of `reghdfe`: mobility-group DoF, individual/team FEs, and the broader `estat` ecosystem remain missing.

## Command Target

High-dimensional fixed-effects regression, aligned with Stata community command `reghdfe`.

## Python Entry

```python
from stataflow.compat.stata import reghdfe

result = reghdfe(
    data, y="depvar", x=["x1", "x2"],
    absorb=["firm_id", "year_id"], vce="cluster", cluster="industry"
)
```

## Supported Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `pd.DataFrame` | Input data |
| `y` | `str` | Dependent variable |
| `x` | `list[str]` | Independent variables |
| `absorb` | `str \| list[str] \| list[tuple]` | Categorical variables to absorb (1+ supported). Supports slope absorption via tuples: `[("firm_id", "time_trend")]` for intercept+slope (`##c.`), `[("firm_id", "time_trend", False)]` for slope-only (`#c.`), or `[("firm_id", ["x1", "x2"])]` / `[("firm_id", ["x1", "x2"], False)]` for multiple slopes. |
| `vce` | `str` | `"ols"`, `"robust"`, `"cluster"`, `"dkraay"` (Driscoll-Kraay panel HAC with Bartlett kernel). Use `"dkraay_<bw>"` for custom bandwidth (e.g. `"dkraay_5"`). |
| `cluster` | `str \| list[str]` | Cluster variable(s); pass a list for 2-way cluster-robust VCE (required when `vce="cluster"`) |
| `keepsingletons` | `bool` | If `True`, do not drop singleton observations (default `False`) |
| `noconstant` | `bool` | If `True`, omit the constant term (default `False`) |
| `savefe` | `bool` | If `True`, return fixed-effect alpha estimates in `result.fixed_effects` (default `False`). Incompatible with `technique="map"` and `vce="dkraay"` (which forces MAP). |
| `missing` | `str` | `"drop"` only |

## Supported Result Fields

Coefficients, standard errors, t-statistics, p-values, confidence intervals, R-squared, adjusted R-squared, RMSE, F-statistic, absorbed degrees of freedom (`df_a`).

## Factor Variable Support

The wrapper layer automatically expands Stata-style factor terms in `x`:

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

Unsupported factor syntax (`ib.` without level, `o.` without level, `b.` without level, time-series operators) remain hard-rejected with `ValueError`.

## Predict Post-estimation

`AbsorbingOLS.predict()` supports the following `type` values (mapped from `reghdfe_p.ado`):

- `"xb"` — linear prediction from reported coefficients (excludes FE dummies)
- `"xbd"` — full prediction including absorbed FE contributions
- `"d"` — sum of fixed-effects contributions (`xbd - xb`)
- `"residuals"` — `y - xbd`
- `"dresiduals"` — `y - xb`

- `stdp` — standard error of the linear prediction (`sqrt(diag(X_reported @ cov_reported @ X_reported.T))`); OLS, robust, and cluster VCE verified

`estat_summarize` is available via `stataflow.postestimation.estat_summarize()`.

## Planned Parameters

- `group` / `individual` FE absorption
- Partialing-out diagnostics (F-statistics for absorbed FEs)
- 3-way and higher multi-way clustering

## Explicitly Unsupported Parameters

`vce(bootstrap)`, `vce(jackknife)`, `mmap`, `fast`, `compress`, `verbose`, and all other reghdfe-specific options not listed above are hard-rejected via `ValueError`.

## Alignment Evidence


- Synthetic cases: Stata validation case `p3_reghdfe_basic`, Stata validation case `p3_reghdfe_cluster`, Stata validation case `p3_reghdfe_two_fe`, Stata validation case `p3_reghdfe_keepsingletons`
- Real-data cases: Stata validation case `p3_reghdfe_real_panel`
- Factor-syntax cases: Stata validation case `a2_factor_reghdfe_basic` — `reghdfe y i.g##c.x1, absorb(firm year)`; Stata validation case `a2_factor_reghdfe_mixed` — `reghdfe y c.x1##i.g, absorb(firm year)`; Stata validation case `a2_factor_reghdfe_bare` — `reghdfe y x1##x2, absorb(firm year)` mapped to Stata `c.x1##c.x2`; Stata validation case `a2_factor_reghdfe_base` — `reghdfe y ib2.g##c.x1, absorb(firm year)`
- **2-way cluster case**: Stata validation case `w7_reghdfe_2way_cluster` — synthetic 2 FE + 2-way cluster; slope SEs < 1e-6, _cons SE known limitation (~2–16%)
- **2-way cluster real-data case**: Stata validation case `w7_reghdfe_2way_cluster_real` — `wagepan` real data; slope SEs < 1e-6
- **savefe case**: Stata validation case `w7_reghdfe_savefe` — FE estimates field-level aligned with Stata
- **Postestimation stdp case**: Stata validation case `w11_reghdfe_stdp` — `predict(type="stdp")` for OLS, robust, and cluster VCE; OLS/robust < 1e-6, cluster < 1e-6
- **Slope absorption case**: Stata validation case `w12_slopes_basic` — `absorb(firm_id##c.time)` intercept+slope; coefficients/SEs < 1e-6
- **Multi-slope case**: Stata validation case `w12_slopes_multi` — `absorb(firm_id##c.(x1 x2))`; coefficients/SEs < 1e-6
- **Slope-only case**: Stata validation case `w12_slopes_only` — `absorb(firm_id#c.time)` pure slope; coefficients/SEs < 1e-6
- **Slope boundary case**: Stata validation case `w12_slopes_zero` — zero-slope group handled without error
- **Driscoll-Kraay case**: Stata validation case `w12_dkraay_basic` — `vce(dkraay)`; coefficients < 1e-6, SEs < 1e-4
- **DK bandwidth truncation**: Stata validation case `w12_dkraay_truncate` — `T=3` panel forces bw truncation to `T-1`
- **DK bw=1 degeneration**: Stata validation case `w12_dkraay_bw1` — `vce(dkraay 1)` equivalent to `cluster(time)`
- Source basis: public `reghdfe` release and published methodology
- Validated by Stata 17 comparison for 1+ absorbed FEs with OLS, single cluster, 2-way cluster, slope absorption, and Driscoll-Kraay VCE

## Core Implementation

`src/stataflow/estimators/absorbing_ols.py`
