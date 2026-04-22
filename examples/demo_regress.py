"""Demo: Stata-compatible OLS with robust and cluster standard errors."""

import numpy as np
import pandas as pd
from stataflow.compat.stata import regress

# Synthetic data
rng = np.random.default_rng(42)
n = 200

df = pd.DataFrame({
    "y": rng.normal(0, 1, n),
    "x1": rng.normal(0, 1, n),
    "x2": rng.normal(0, 1, n),
    "cluster_id": rng.integers(1, 21, size=n),
})

# OLS with robust SE
result = regress(df, y="y", x=["x1", "x2"], vce="robust")
print("=== OLS with robust SE ===")
for c in result.coefficients:
    print(f"{c.name:12s}  beta={c.beta: .4f}  se={c.std_err:.4f}  t={c.t_stat:.4f}")

# OLS with cluster SE
result_cluster = regress(df, y="y", x=["x1", "x2"], vce="cluster", cluster="cluster_id")
print("\n=== OLS with cluster SE ===")
for c in result_cluster.coefficients:
    print(f"{c.name:12s}  beta={c.beta: .4f}  se={c.std_err:.4f}  t={c.t_stat:.4f}")
