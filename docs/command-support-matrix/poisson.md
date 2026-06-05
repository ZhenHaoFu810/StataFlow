# Support Matrix: `poisson`

## Command Target

Poisson regression (MLE), aligned with Stata 17 `poisson`.

## Python Entry

```python
from stataflow.compat.stata import poisson

result = poisson(data, y="depvar", x=["x1", "x2"], vce="robust")
```

## Supported Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `pd.DataFrame` | Input data |
| `y` | `str` | Dependent variable (count) |
| `x` | `list[str]` | Independent variables |
| `vce` | `str` | `"ols"`, `"robust"`, `"cluster"` |
| `cluster` | `str` | Cluster variable (required when `vce="cluster"`) |
| `noconstant` | `bool` | Drop constant term |
| `eform` | `bool` | Report exponentiated coefficients |
| `irr` | `bool` | Alias for `eform` (matches Stata `irr`) |
| `missing` | `str` | `"drop"` only |

## Supported Result Fields

Coefficients, standard errors, z-statistics, p-values, confidence intervals, pseudo R-squared, log-likelihood, LR chi2, deviance.

## Factor Variable Support

The wrapper layer automatically expands Stata-style factor terms in `x`:

- `c.x1`, `i.g`
- `ib2.g`, `b2.g` (explicit base level)
- `o2.g` (explicit omitted level)
- `c.x1#c.x2`, `c.x1##c.x2`
- `i.g1#i.g2`, `i.g1##i.g2`
- `i.g1#c.x1`, `i.g1##c.x1`

Unsupported factor syntax (`ib.` without level, `o.` without level, `b.` without level, time-series operators, three-way+ interactions) is hard-rejected with `ValueError`.

## Postestimation (Core Estimator Layer Only)

The `compat.stata` wrapper returns a `ResultSchema` object. To use `predict()` or `margins()`, call the core estimator (`stataflow.estimators.Poisson`) directly.

- `predict(type="xb")`
- `predict(type="mu")`
- `margins(type="dydx")`
- `margins(type="atmeans")`

## Planned Parameters

- `offset`, `exposure` (currently hard-rejected with `NotImplementedError`)
- `nonrtolerance`, `difficult`
- `from` (starting values)

## Explicitly Unsupported Parameters

`exposure` and `offset` are explicitly recognized but raise `NotImplementedError`. All other unsupported Stata `poisson` options are hard-rejected via `ValueError`.

## Alignment Evidence


- Synthetic cases: `tests/golden/test_w3_poisson_basic.py`
- Real-data cases: `tests/golden/test_w3_poisson_real.py`
- Margins cases: `tests/golden/test_w5_margins_real_crime1.py`
- Stata 17 dual-run verified for MLE with conventional, robust, and cluster-robust VCE

## Core Implementation

`src/stataflow/estimators/glm.py` (`Poisson`)
