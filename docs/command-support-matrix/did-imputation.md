# Support Matrix: `did_imputation`

## Completeness Status

**Beta — Core Estimator** — the Borusyak-Jaravel-Spiess DID imputation estimator with TWFE-on-controls, imputation, cluster-robust standard errors, `window`, `minn`, `controls`, `unitcontrols`, and `timecontrols` is implemented and verified. repeated cross-section is missing.

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
| `allhorizons` | `bool` | Compute all event-time horizons, including pre-treatment (negative) horizons |
| `autosample` | `bool` | Automatically drop non-imputable observations |
| `window` | `list[int]` | Two-element list `[min, max]` restricting relative-time horizons |
| `minn` | `int` | Minimum imputable observations required per horizon |
| `controls` | `list[str]` | Control covariates (global slopes, applied to Y0) |
| `unitcontrols` | `list[str]` | Unit-specific control slopes (interacted with unit FE) |
| `timecontrols` | `list[str]` | Time-specific control slopes (interacted with time FE) |
| `pretrends` | `int` | Number of pretreatment periods to test for parallel trends |
| `wtr` | `str` or `list[str]` | Custom weight variable(s) for weighted average treatment effects |
| `hetby` | `str` | Group variable for heterogeneous effects (splits each `wtr` by group) |
| `saveestimates` | `str` | Save `effect = Y - Y0` as a pandas Series on the fitted model instance |
| `saveweights` | `bool` | Save imputation weights as a pandas DataFrame on the fitted model instance |
| `sum` | `bool` | Compute weighted sums instead of weighted averages (no normalization) |

## Supported Result Fields

Event-study horizon coefficients (`tau0`, `tau1`, ...), standard errors, z-statistics, p-values, confidence intervals. Returned as `ResultSchema`.

## Planned Parameters

- `horizons` (explicit horizon subsetting)
- `hbalance` (balanced panel constraint)
- `project` (projection to covariate space)
- `saveresid` (save regression residuals)
- Repeated cross-section support

## Explicitly Unsupported Parameters

`horizons`, `hbalance`, `project`, `saveresid`, and all other did_imputation-specific options are hard-rejected via `ValueError`.

## Alignment Evidence


- Synthetic cases: `tests/golden/test_w4_did_imputation_basic.py` (basic), `tests/golden/test_w9_di_controls_basic.py` (controls), `tests/golden/test_w9_di_pretrends_basic.py` (pretrends), `tests/golden/test_w9_di_controls_pretrends_combo.py` (controls + pretrends)
- Real-data cases: `tests/golden/test_w4_did_imputation_real_ezunem.py`
- Local source mirror: `research/vendor/stata_community/did_imputation/`
- Stata 17 dual-run verified for TWFE-imputation event-study coefficients with cluster-robust SEs, controls, and pretrends

## Core Implementation

`src/stataflow/estimators/did_imputation.py`
