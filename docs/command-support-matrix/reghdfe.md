# Support Matrix: `reghdfe`

## Completeness Status

**Partial / Phase B+ Subset** — multiple categorical FE absorption (1+ FEs) is implemented, tested, and dual-run verified with expanded synthetic coverage. Phase B added `keepsingletons`, `noconstant`, and expanded `predict` support (`xb`, `xbd`, `d`, `residuals`, `dresiduals`). Wave 11 added `predict(type="stdp")` for OLS, robust, and cluster VCE, plus `estat_summarize`. This is still **not** a full reproduction of `reghdfe`: the implementation uses LSDV (dummy-variable) demeaning rather than iterative within-transformation, so very high-dimensional FEs may encounter performance limits; mobility-group DoF, slopes, individual/team FEs, and broader `estat` ecosystem remain missing.

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
| `absorb` | `str \| list[str]` | Categorical variables to absorb (1+ supported) |
| `vce` | `str` | `"ols"`, `"robust"`, `"cluster"` |
| `cluster` | `str \| list[str]` | Cluster variable(s); pass a list for 2-way cluster-robust VCE (required when `vce="cluster"`) |
| `keepsingletons` | `bool` | If `True`, do not drop singleton observations (default `False`) |
| `noconstant` | `bool` | If `True`, omit the constant term (default `False`) |
| `savefe` | `bool` | If `True`, return fixed-effect alpha estimates in `result.fixed_effects` (default `False`) |
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

Unsupported factor syntax (`ib.` without level, `o.` without level, `b.` without level, time-series operators, three-way+ interactions) is hard-rejected with `ValueError`.

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


- Synthetic cases: `tests/golden/test_p3_reghdfe_basic.py`, `tests/golden/test_p3_reghdfe_cluster.py`, `tests/golden/test_p3_reghdfe_two_fe.py`, `tests/golden/test_p3_reghdfe_keepsingletons.py`
- Real-data cases: `tests/golden/test_p3_reghdfe_real_panel.py`
- Factor-syntax cases: `tests/golden/test_a2_factor_reghdfe_basic.py` — `reghdfe y i.g##c.x1, absorb(firm year)`; `tests/golden/test_a2_factor_reghdfe_mixed.py` — `reghdfe y c.x1##i.g, absorb(firm year)`; `tests/golden/test_a2_factor_reghdfe_bare.py` — `reghdfe y x1##x2, absorb(firm year)` mapped to Stata `c.x1##c.x2`; `tests/golden/test_a2_factor_reghdfe_base.py` — `reghdfe y ib2.g##c.x1, absorb(firm year)`
- **2-way cluster case**: `tests/golden/test_w7_reghdfe_2way_cluster.py` — synthetic 2 FE + 2-way cluster; slope SEs < 1e-6, _cons SE known limitation (~2–16%)
- **2-way cluster real-data case**: `tests/golden/test_w7_reghdfe_2way_cluster_real.py` — `wagepan` real data; slope SEs < 1e-6
- **savefe case**: `tests/golden/test_w7_reghdfe_savefe.py` — FE estimates field-level aligned with Stata
- **Postestimation stdp case**: `tests/golden/test_w11_reghdfe_stdp.py` — `predict(type="stdp")` for OLS, robust, and cluster VCE; OLS/robust < 1e-6, cluster < 1e-6
- Local source mirror: `research/vendor/stata_community/reghdfe/`
- Stata 17 dual-run verified for 1+ absorbed FEs with OLS, single cluster, and 2-way cluster VCE

## Core Implementation

`src/stataflow/estimators/absorbing_ols.py`
