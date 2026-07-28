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
print("regress, vce(robust)")
result = regress(df, y="y", x=["x1", "x2"], vce="robust")
result.display()

# The same result can be rendered compactly or returned as escaped HTML.
print("\nregress, compact output without confidence intervals")
result.display(detail="compact", show_ci=False)
html = result.to_html()
assert 'class="stataflow-result"' in html

# OLS with cluster SE
print("\nregress, vce(cluster cluster_id)")
result_cluster = regress(df, y="y", x=["x1", "x2"], vce="cluster", cluster="cluster_id")
result_cluster.display()
