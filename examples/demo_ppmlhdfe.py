"""Demo: Poisson PML with high-dimensional fixed effects (ppmlhdfe)."""

import numpy as np
import pandas as pd
from statapy.compat.stata import ppmlhdfe

# Synthetic count panel data
rng = np.random.default_rng(42)
n_units = 80
n_periods = 4
n = n_units * n_periods

units = np.repeat(np.arange(n_units), n_periods)
periods = np.tile(np.arange(n_periods), n_units)

fe_u = np.repeat(rng.normal(0, 0.5, n_units), n_periods)
fe_t = np.tile(rng.normal(0, 0.5, n_periods), n_units)

x1 = rng.normal(0, 1, n)
log_mu = fe_u + fe_t + 0.3 * x1
y = rng.poisson(np.exp(log_mu))

df = pd.DataFrame({
    "y": y,
    "x1": x1,
    "unit_id": units,
    "period": periods,
    "cluster_id": np.repeat(rng.integers(1, 11, size=n_units), n_periods),
})

result = ppmlhdfe(
    df,
    y="y",
    x=["x1"],
    absorb=["unit_id", "period"],
    vce="cluster",
    cluster="cluster_id",
)

print("=== ppmlhdfe: Poisson PML with two-way FE ===")
for c in result.coefficients:
    print(f"{c.name:12s}  beta={c.beta: .4f}  se={c.std_err:.4f}  z={c.t_stat:.4f}")
