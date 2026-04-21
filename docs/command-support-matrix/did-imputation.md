# Support Matrix: `did_imputation`

## Completeness Status

**Partial / Core Estimator Subset** — the Borusyak-Jaravel-Spiess DID imputation estimator with TWFE-on-controls, imputation, and cluster-robust standard errors is implemented and verified, but `controls`, `window`, `minn`, `pretrends`, and repeated cross-section are missing.

## Command Target

Borusyak, Jaravel \& Spiess (2021) DID imputation estimator, aligned with Stata community command `did_imputation`.

## Python Entry

```python
from stataflow.compat.stata import did_imputation

result = did_imputation(
    data, y="y", id="unit_id", time="year",
    first_treat="first_treat",
    cluster="unit_id", allhorizons=True, autosample=False
)
```

## Supported Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `pd.DataFrame` | Input data |
| `y` | `str` | Dependent variable |
| `id` | `str` | Unit identifier |
| `time` | `str` | Time identifier |
| `first_treat` | `str` | First treatment period variable |
| `cluster` | `str` | Cluster variable for cluster-robust SEs (defaults to `id`) |
| `allhorizons` | `bool` | Compute all post-treatment event-time horizons |
| `autosample` | `bool` | Automatically drop non-imputable observations |

## Supported Result Fields

Event-study horizon coefficients (`tau0`, `tau1`, ...), standard errors, z-statistics, p-values, confidence intervals. Returned as `ResultSchema`.

## Planned Parameters

- `controls` (control covariates)
- `unitcontrols` / `timecontrols` (separate FE controls)
- `horizons` (explicit horizon subsetting)
- `minn` (minimum observations per horizon)
- `pretrends()` (pre-trend test)
- `wtr` (custom weighting)
- Repeated cross-section support

## Explicitly Unsupported Parameters

`horizons`, `minn`, `hbalance`, `project`, `hetby`, `saveestimates`, `saveweights`, `saveresid`, `pretrends`, and all other did_imputation-specific options are hard-rejected via `ValueError`.

## Alignment Evidence


- Synthetic cases: `tests/golden/test_w4_did_imputation_basic.py`
- Real-data cases: `tests/golden/test_w4_did_imputation_real_ezunem.py`
- Local source mirror: `research/vendor/stata_community/did_imputation/`
- Stata 17 dual-run verified for TWFE-imputation event-study coefficients with cluster-robust SEs

## Core Implementation

`src/stataflow/estimators/did_imputation.py`
