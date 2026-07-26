"""Demo: IV 2SLS with high-dimensional fixed effects (ivreghdfe)."""

import numpy as np
import pandas as pd
from stataflow.compat.stata import ivreghdfe

# Synthetic panel data with an endogenous regressor
rng = np.random.default_rng(42)
n_units = 120
n_periods = 5
n = n_units * n_periods

units = np.repeat(np.arange(n_units), n_periods)
periods = np.tile(np.arange(n_periods), n_units)

fe_u = np.repeat(rng.normal(0, 1, n_units), n_periods)
fe_t = np.tile(rng.normal(0, 0.5, n_periods), n_units)

z = rng.normal(0, 1, n)  # instrument
u = rng.normal(0, 1, n)  # structural error correlated with x_endog
x_endog = 0.6 * z + u + rng.normal(0, 0.5, n)
x_exog = rng.normal(0, 1, n)
y = fe_u + fe_t + 0.8 * x_endog + 0.3 * x_exog + u

df = pd.DataFrame({
    "y": y,
    "x_exog": x_exog,
    "x_endog": x_endog,
    "z1": z,
    "z2": z + rng.normal(0, 0.3, n),  # second instrument
    "unit_id": units,
    "period": periods,
})

result = ivreghdfe(
    df,
    y="y",
    x_exog=["x_exog"],
    x_endog=["x_endog"],
    instruments=["z1", "z2"],
    absorb=["unit_id", "period"],
    vce="cluster",
    cluster="unit_id",
)

print("ivreghdfe: 2SLS with two-way FE and cluster VCE")
result.display()
