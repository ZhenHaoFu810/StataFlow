# Support Matrix: `ivregress 2sls`

## Command Target

Two-stage least squares instrumental-variables regression, aligned with Stata 17 `ivregress 2sls`.

## Python Entry

```python
from statapy.compat.stata import ivregress_2sls

result = ivregress_2sls(
    data, y="depvar",
    x_exog=["x1"], x_endog=["x2"], instruments=["z1", "z2"],
    vce="robust"
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
| `vce` | `str` | `"ols"`, `"robust"`, `"cluster"` |
| `cluster` | `str` | Cluster variable (required when `vce="cluster"`) |
| `missing` | `str` | `"drop"` only |

## Supported Result Fields

Coefficients, standard errors, z-statistics, p-values, confidence intervals, R-squared, adjusted R-squared, RMSE.

## Factor Variable Support

The wrapper layer automatically expands Stata-style factor terms in `x_exog`, `x_endog`, and `instruments`:

- `c.x1`, `i.g`
- `c.x1#c.x2`, `c.x1##c.x2`
- `i.g1#i.g2`, `i.g1##i.g2`
- `i.g1#c.x1`, `i.g1##c.x1`
- `c.x1#i.g1`, `c.x1##i.g1` (mixed-order symmetry, equivalent to `i.g1#c.x1` / `i.g1##c.x1`)

Unsupported factor syntax (`ib#.`, `o.`, `b.`, time-series operators, three-way+ interactions) is hard-rejected with `ValueError`.

## Planned Parameters

- First-stage and weak-IV diagnostics (`first`, `ffirst`, `estat firststage`)
- Overidentification tests (`estat overid`)
- `noconstant`, `beta`, `hascons`, `tsscons`, `level`

## Explicitly Unsupported Parameters

`gmm`, `liml`, `kclass`, `fwl`, `noid`, `partial`, `estimator`, `wmatrix`, and all other IV-specific options are hard-rejected via `ValueError`.

## Alignment Evidence

Validation evidence book entry: [`docs/validation/evidence-matrix.md#ivregress-2sls`](../validation/evidence-matrix.md#ivregress-2sls)

- Synthetic cases: `tests/golden/test_w2_ivregress_basic.py`, `tests/golden/test_w2_ivregress_cluster.py`
- Real-data cases: `tests/golden/test_w2_ivregress_real_card.py`
- Stata 17 dual-run verified for 2SLS with conventional, robust, and cluster-robust VCE

## Core Implementation

`src/statapy/estimators/iv.py` (`IV2SLS`)
