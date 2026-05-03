"""Demo: Two-stage least squares (ivregress 2sls) with robust VCE."""

import numpy as np
import pandas as pd
from stataflow.compat.stata import ivregress_2sls

# Synthetic data with endogeneity
rng = np.random.default_rng(42)
n = 300

z = rng.normal(0, 1, n)  # instrument
u = rng.normal(0, 1, n)  # error
x_endog = 0.5 * z + u + rng.normal(0, 0.5, n)  # endogenous regressor
x_exog = rng.normal(0, 1, n)  # exogenous regressor
y = 1.0 + 0.8 * x_endog + 0.3 * x_exog + u

df = pd.DataFrame({
    "y": y,
    "x_exog": x_exog,
    "x_endog": x_endog,
    "z1": z,
    "z2": z + rng.normal(0, 0.3, n),  # second instrument
})

result = ivregress_2sls(
    df,
    y="y",
    x_exog=["x_exog"],
    x_endog=["x_endog"],
    instruments=["z1", "z2"],
    vce="robust",
)

print("ivregress 2sls with robust VCE")
result.display()
