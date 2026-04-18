# Support Matrix: `areg`

## Command Target

Linear regression with a single absorbed fixed effect, aligned with Stata 17 `areg`.

## Python Entry

```python
from statapy.compat.stata import areg

result = areg(data, y="depvar", x=["x1", "x2"], absorb="firm_id")
```

## Supported Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `pd.DataFrame` | Input data |
| `y` | `str` | Dependent variable |
| `x` | `list[str]` | Independent variables |
| `absorb` | `str` | Single categorical variable to absorb |
| `vce` | `str` | `"ols"`, `"cluster"` |
| `cluster` | `str` | Cluster variable (required when `vce="cluster"`) |
| `missing` | `str` | `"drop"` only |

## Supported Result Fields

Coefficients, standard errors, t-statistics, p-values, confidence intervals, R-squared, adjusted R-squared, RMSE, F-statistic, absorbed degrees of freedom.

## Factor Variable Support

The wrapper layer automatically expands Stata-style factor terms in `x`:

- `c.x1`, `i.g`
- `c.x1#c.x2`, `c.x1##c.x2`
- `i.g1#i.g2`, `i.g1##i.g2`
- `i.g1#c.x1`, `i.g1##c.x1`

Unsupported factor syntax (`ib#.`, `o.`, `b.`, time-series operators, three-way+ interactions) is hard-rejected with `ValueError`.

## Planned Parameters

- `robust` as an explicit option
- `absorb` with multiple variables (use `reghdfe` for multi-way)
- `generate` (save residuals)

## Explicitly Unsupported Parameters

All other Stata options are hard-rejected via `ValueError`.

## Alignment Evidence

- Synthetic cases: `tests/golden/test_p3_areg_basic.py`
- Real-data cases: `tests/golden/test_p3_areg_real_panel.py`
- Stata 17 dual-run verified for conventional and cluster-robust VCE

## Core Implementation

`src/statapy/estimators/absorbing_ols.py` (single-absorb path)
