"""Demo: Panel fixed effects with xtreg_fe and areg."""

import numpy as np
import pandas as pd
from stataflow.compat.stata import areg, xtreg_fe

# Synthetic panel data
rng = np.random.default_rng(42)
n_units = 100
n_periods = 5
n = n_units * n_periods

units = np.repeat(np.arange(n_units), n_periods)
periods = np.tile(np.arange(n_periods), n_units)

fe_u = np.repeat(rng.normal(0, 1, n_units), n_periods)
x1 = rng.normal(0, 1, n)
x2 = rng.normal(0, 1, n)
y = fe_u + 0.8 * x1 - 0.4 * x2 + rng.normal(0, 1, n)

df = pd.DataFrame({
    "y": y,
    "x1": x1,
    "x2": x2,
    "unit_id": units,
    "period": periods,
})

# Within (fixed effects) estimator with cluster VCE
print("xtreg_fe: unit fixed effects with cluster VCE")
result_xt = xtreg_fe(df, y="y", x=["x1", "x2"], fe="unit_id", vce="cluster", cluster="unit_id")
result_xt.display()

# Absorbed OLS with robust VCE
print("\nareg: absorbed unit effects with robust VCE")
result_areg = areg(df, y="y", x=["x1", "x2"], absorb="unit_id", vce="robust")
result_areg.display()
