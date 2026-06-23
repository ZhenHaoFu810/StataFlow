# Support Matrix: `logit`

## Command Target

Logistic regression (MLE), aligned with Stata 17 `logit`.

## Python Entry

```python
from stataflow.compat.stata import logit

result = logit(data, y="depvar", x=["x1", "x2"], vce="robust")
```

## Supported Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `pd.DataFrame` | Input data |
| `y` | `str` | Dependent variable (binary 0/1) |
| `x` | `list[str]` | Independent variables |
| `vce` | `str` | `"ols"`, `"robust"`, `"cluster"` |
| `cluster` | `str` | Cluster variable (required when `vce="cluster"`) |
| `noconstant` | `bool` | Drop constant term |
| `eform` | `bool` | Report exponentiated coefficients (odds ratios) |
| `or_` | `bool` | Alias for `eform` (matches Stata `or`) |
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

Unsupported factor syntax (`ib.` without level, `o.` without level, `b.` without level, time-series operators) remain hard-rejected with `ValueError`.

## Postestimation (Core Estimator Layer Only)

The `compat.stata` wrapper returns a `ResultSchema` object. To use `predict()` or `margins()`, call the core estimator (`stataflow.estimators.Logit`) directly.

- `predict(type="xb")`
- `predict(type="pr")`
- `margins(type="dydx")`
- `margins(type="atmeans")`

## Planned Parameters

- `offset`, `exposure`
- `asis` (perfect prediction handling)
- `nonrtolerance`, `difficult`
- `from` (starting values)

## Explicitly Unsupported Parameters

All other Stata `logit` options are hard-rejected via `ValueError`.

## Alignment Evidence


- Synthetic cases: `tests/golden/test_w3_logit_basic.py`
- Real-data cases: `tests/golden/test_w3_logit_real.py`
- Factor-syntax cases: `tests/golden/test_a2_factor_logit_basic.py` — `logit y_bin c.x1##c.x2`; `tests/golden/test_a2_factor_logit_base.py` — `logit y_bin ib2.g##c.x1`
- Margins cases: `tests/golden/test_w5_margins_logit_basic.py`, `tests/golden/test_w5_margins_real_mroz.py`
- Stata 17 dual-run verified for MLE with conventional, robust, and cluster-robust VCE

## Core Implementation

`src/stataflow/estimators/glm.py` (`Logit`)
