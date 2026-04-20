# Support Matrix: `probit`

## Command Target

Probit regression (MLE), aligned with Stata 17 `probit`.

## Python Entry

```python
from stataflow.compat.stata import probit

result = probit(data, y="depvar", x=["x1", "x2"], vce="robust")
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
| `missing` | `str` | `"drop"` only |

## Supported Result Fields

Coefficients, standard errors, z-statistics, p-values, confidence intervals, pseudo R-squared, log-likelihood, LR chi2.

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

The `compat.stata` wrapper returns a `ResultSchema` object. To use `predict()` or `margins()`, call the core estimator (`stataflow.estimators.Probit`) directly.

- `predict(type="xb")`
- `predict(type="pr")`
- `margins(type="dydx")`
- `margins(type="atmeans")`

## Planned Parameters

- `offset`, `exposure`
- `asis` (perfect prediction handling)
- `nonrtolerance`, `difficult`
- `from` (starting values)
- `scores`

## Explicitly Unsupported Parameters

All other Stata `probit` options are hard-rejected via `ValueError`.

## Alignment Evidence

Validation evidence book entry: [`docs/validation/evidence-matrix.md#probit`](../validation/evidence-matrix.md#probit)

- Synthetic cases: `tests/golden/test_w3_probit_basic.py`, `tests/golden/test_w3_probit_robust.py`
- Real-data cases: `tests/golden/test_w3_probit_real.py`
- Stata 17 dual-run verified for MLE with conventional, robust, and cluster-robust VCE

## Core Implementation

`src/stataflow/estimators/glm.py` (`Probit`)
