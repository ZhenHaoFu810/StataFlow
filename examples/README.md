# Examples

This directory contains self-contained demo scripts that demonstrate StataFlow usage on synthetic data. Each script creates its own dataset, runs one or more commands, and prints the results.

## Running the examples

```bash
python examples/demo_regress.py
python examples/demo_ivregress_2sls.py
python examples/demo_reghdfe.py
python examples/demo_ppmlhdfe.py
```

## Available demos

| Script | Demonstrates | Status |
|--------|-------------|--------|
| [`demo_regress.py`](./demo_regress.py) | OLS with robust SE and cluster SE | Stable |
| [`demo_ivregress_2sls.py`](./demo_ivregress_2sls.py) | Two-stage least squares with robust VCE and two instruments | Stable |
| [`demo_reghdfe.py`](./demo_reghdfe.py) | Two-way fixed effects regression with cluster VCE | Beta |
| [`demo_ppmlhdfe.py`](./demo_ppmlhdfe.py) | Poisson pseudo-maximum-likelihood with two-way FE and cluster VCE | Beta |

## More examples

For comprehensive copy-paste recipes with Stata equivalents, see the **[Cookbook](../docs/cookbook.md)** and **[User Guide](../docs/USER_GUIDE.md)**.
