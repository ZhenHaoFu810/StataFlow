"""Demo: Binary and count models (logit, probit, poisson)."""

import numpy as np
import pandas as pd
from stataflow.compat.stata import logit, poisson, probit

# Synthetic data
rng = np.random.default_rng(42)
n = 400

x1 = rng.normal(0, 1, n)
x2 = rng.normal(0, 1, n)
latent = -0.5 + 0.9 * x1 + 0.5 * x2
y_binary = (latent + rng.normal(0, 1, n) > 0).astype(int)
y_count = rng.poisson(np.exp(0.2 + 0.4 * x1 - 0.2 * x2))

df = pd.DataFrame({
    "y_binary": y_binary,
    "y_count": y_count,
    "x1": x1,
    "x2": x2,
})

# Logit with robust SE
print("logit, vce(robust)")
result_logit = logit(df, y="y_binary", x=["x1", "x2"], vce="robust")
result_logit.display()

# Probit
print("\nprobit")
result_probit = probit(df, y="y_binary", x=["x1", "x2"])
result_probit.display()

# Poisson with robust SE
print("\npoisson, vce(robust)")
result_poisson = poisson(df, y="y_count", x=["x1", "x2"], vce="robust")
result_poisson.display()
