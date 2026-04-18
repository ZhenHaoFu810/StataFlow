# Support Matrix: `reghdfe`

## Completeness Status

**Partial / Phase B Subset** — the core 1–2 categorical FE path is implemented, tested, and dual-run verified. Phase B added `keepsingletons`, `noconstant`, and expanded `predict` support (`xb`, `xbd`, `d`, `residuals`, `dresiduals`). This is still **not** a full reproduction of `reghdfe`: mobility-group DoF, slopes, individual/team FEs, multi-way clustering, and the `estat` ecosystem remain missing.

## Command Target

High-dimensional fixed-effects regression, aligned with Stata community command `reghdfe`.

## Python Entry

```python
from statapy.compat.stata import reghdfe

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
| `absorb` | `str \| list[str]` | 1-2 categorical variables to absorb |
| `vce` | `str` | `"ols"`, `"robust"`, `"cluster"` |
| `cluster` | `str` | Cluster variable (required when `vce="cluster"`) |
| `keepsingletons` | `bool` | If `True`, do not drop singleton observations (default `False`) |
| `noconstant` | `bool` | If `True`, omit the constant term (default `False`) |
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

`stdp` is not yet implemented.

## Planned Parameters

- `group` / `individual` FE absorption
- Partialing-out diagnostics (F-statistics for absorbed FEs)

## Explicitly Unsupported Parameters

`vce(bootstrap)`, `vce(jackknife)`, `mmap`, `fast`, `compress`, `verbose`, `stdp`, and all other reghdfe-specific options not listed above are hard-rejected via `ValueError`.

## Alignment Evidence

- Synthetic cases: `tests/golden/test_p3_reghdfe_basic.py`, `tests/golden/test_p3_reghdfe_cluster.py`, `tests/golden/test_p3_reghdfe_two_fe.py`, `tests/golden/test_p3_reghdfe_keepsingletons.py`
- Real-data cases: `tests/golden/test_p3_reghdfe_real_panel.py`
- Factor-syntax cases: `tests/golden/test_a2_factor_reghdfe_basic.py` — `reghdfe y i.g##c.x1, absorb(firm year)`; `tests/golden/test_a2_factor_reghdfe_mixed.py` — `reghdfe y c.x1##i.g, absorb(firm year)`; `tests/golden/test_a2_factor_reghdfe_bare.py` — `reghdfe y x1##x2, absorb(firm year)` mapped to Stata `c.x1##c.x2`; `tests/golden/test_a2_factor_reghdfe_base.py` — `reghdfe y ib2.g##c.x1, absorb(firm year)`
- Local source mirror: `research/vendor/stata_community/reghdfe/`
- Stata 17 dual-run verified for 1-2 absorbed FEs with OLS and cluster VCE

## Core Implementation

`src/statapy/estimators/absorbing_ols.py`
