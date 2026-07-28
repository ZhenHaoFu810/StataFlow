# Examples

This directory contains the nine self-contained demos for StataFlow 1.3.0.
Each script creates synthetic data, runs one or more commands, and prints the
results. Together they exercise all 14 public Stata-compatible commands. The
demos are deterministic, require no network access, and do not require Stata.
`demo_regress.py` also demonstrates full, compact, no-CI, and HTML rendering.

## Running the examples

```bash
python examples/demo_regress.py
python examples/demo_panel_fe.py
python examples/demo_reghdfe.py
python examples/demo_ivregress_2sls.py
python examples/demo_ivreghdfe.py
python examples/demo_glm.py
python examples/demo_ppmlhdfe.py
python examples/demo_did.py
python examples/demo_rdrobust.py
```

## Available demos

| Script | Commands demonstrated | Description | Status |
|--------|----------------------|-------------|--------|
| [`demo_regress.py`](./demo_regress.py) | `regress` | OLS with robust SE and cluster SE | Stable |
| [`demo_panel_fe.py`](./demo_panel_fe.py) | `xtreg_fe`, `areg` | Panel fixed effects: within estimator and absorbed OLS | Stable |
| [`demo_reghdfe.py`](./demo_reghdfe.py) | `reghdfe` | Two-way fixed effects regression with cluster VCE | Beta |
| [`demo_ivregress_2sls.py`](./demo_ivregress_2sls.py) | `ivregress_2sls` | Two-stage least squares with robust VCE and two instruments | Stable |
| [`demo_ivreghdfe.py`](./demo_ivreghdfe.py) | `ivreghdfe` | 2SLS with two-way fixed effects and cluster VCE | Beta |
| [`demo_glm.py`](./demo_glm.py) | `logit`, `probit`, `poisson` | Binary and count models with robust SE | Stable |
| [`demo_ppmlhdfe.py`](./demo_ppmlhdfe.py) | `ppmlhdfe` | Poisson pseudo-maximum-likelihood with two-way FE and cluster VCE | Beta |
| [`demo_did.py`](./demo_did.py) | `did_imputation`, `eventstudyinteract`, `csdid` | Staggered-adoption DID: BJS imputation, Sun-Abraham event study, Callaway-Sant'Anna ATT | Beta |
| [`demo_rdrobust.py`](./demo_rdrobust.py) | `rdrobust` | Sharp regression discontinuity with data-driven bandwidth | Beta |

## More examples

For comprehensive copy-paste recipes with Stata equivalents, see the **[Cookbook](../docs/cookbook.md)** and **[User Guide](../docs/USER_GUIDE.md)**.
