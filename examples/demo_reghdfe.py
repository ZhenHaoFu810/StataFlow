"""Demo: High-dimensional fixed effects (reghdfe) with cluster VCE."""

import numpy as np
import pandas as pd
from stataflow.compat.stata import reghdfe

# Synthetic panel data
rng = np.random.default_rng(42)
n_units = 100
n_periods = 5
n = n_units * n_periods

units = np.repeat(np.arange(n_units), n_periods)
periods = np.tile(np.arange(n_periods), n_units)

fe_u = np.repeat(rng.normal(0, 1, n_units), n_periods)
fe_t = np.tile(rng.normal(0, 1, n_periods), n_units)

treat = (periods >= 2).astype(float)
y = fe_u + fe_t + 1.5 * treat + rng.normal(0, 1, n)

df = pd.DataFrame({
    "y": y,
    "x1": rng.normal(0, 1, n),
    "treat": treat,
    "unit_id": units,
    "period": periods,
    "cluster_id": np.repeat(rng.integers(1, 21, size=n_units), n_periods),
})

result = reghdfe(
    df,
    y="y",
    x=["x1", "treat"],
    absorb=["unit_id", "period"],
    vce="cluster",
    cluster="cluster_id",
)

print("=== reghdfe: two-way FE with cluster VCE ===")
for c in result.coefficients:
    print(f"{c.name:12s}  beta={c.beta: .4f}  se={c.std_err:.4f}  t={c.t_stat:.4f}")
print(f"df_a={result.fit.df_a}")
