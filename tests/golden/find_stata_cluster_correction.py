"""
Find the exact cluster correction factor Stata uses for FE.
"""

import numpy as np
import pandas as pd

np.random.seed(66666)
n_entities = 30
n_periods = 4
n = n_entities * n_periods

entity_id = np.repeat(np.arange(n_entities), n_periods)
x1 = np.random.normal(0, 1, n)
x2 = np.random.normal(0, 1, n)
entity_fe = np.repeat(np.random.normal(0, 2, n_entities), n_periods)
error = np.random.normal(0, 1, n)
y = 1 + 1.5 * x1 - 2 * x2 + entity_fe + error

data = pd.DataFrame({"y": y, "x1": x1, "x2": x2, "entity_id": entity_id})

# Within transformation
df_temp = data.copy()
df_temp['_y'] = y
df_temp['_x1'] = x1
df_temp['_x2'] = x2

entity_means = df_temp.groupby('entity_id').transform('mean')
y_w = y - entity_means['_y'].values
X_w = np.column_stack([
    x1 - entity_means['_x1'].values,
    x2 - entity_means['_x2'].values,
])

k = 2
beta = np.linalg.solve(X_w.T @ X_w, X_w.T @ y_w)
residuals_w = y_w - X_w @ beta
rss = np.sum(residuals_w ** 2)

XtX = X_w.T @ X_w
XtX_inv = np.linalg.inv(XtX)

unique_clusters = np.unique(entity_id)
G = len(unique_clusters)

meat = np.zeros((k, k))
for g in unique_clusters:
    mask_g = entity_id == g
    X_w_g = X_w[mask_g]
    e_g = residuals_w[mask_g]
    Xe_g = X_w_g.T @ e_g
    meat += np.outer(Xe_g, Xe_g)

# Stata V[0,0] = 0.01151575
# My cov_beta[0,0] with n_adj*g_adj = 0.01141816

# Try: no correction at all
cov_raw = XtX_inv @ meat @ XtX_inv
print(f"No correction: V[0,0] = {cov_raw[0,0]:.8f}")

# Try: only g_adj
cov_g = (G / (G - 1)) * cov_raw
print(f"Only g_adj: V[0,0] = {cov_g[0,0]:.8f}")

# Try: n_adj * g_adj
cov_ng = ((n - 1) / (n - k)) * (G / (G - 1)) * cov_raw
print(f"n_adj * g_adj: V[0,0] = {cov_ng[0,0]:.8f}")

# Stata value
print(f"Stata V[0,0] = 0.01151575")

# The ratio
ratio = 0.01151575 / cov_raw[0,0]
print(f"\nRequired correction factor: {ratio:.8f}")
print(f"g_adj = {G / (G - 1):.8f}")
print(f"n_adj = {(n - 1) / (n - k):.8f}")
print(f"n_adj * g_adj = {((n - 1) / (n - k)) * (G / (G - 1)):.8f}")

# Maybe Stata uses (G/(G-1)) * ((N-k)/(N-1))?
alt_correction = (G / (G - 1)) * ((n - k) / (n - 1))
cov_alt = alt_correction * cov_raw
print(f"\nWith (G/(G-1)) * ((N-k)/(N-1)): V[0,0] = {cov_alt[0,0]:.8f}")

# Or maybe for FE, Stata uses different N in the correction?
# In FE, effective N is N - G (after within transformation)
n_eff = n - n_entities
n_adj_fe = (n_eff - 1) / (n_eff - k)
cov_fe = n_adj_fe * (G / (G - 1)) * cov_raw
print(f"\nWith n_eff = N - G:")
print(f"n_adj_fe = {n_adj_fe:.8f}")
print(f"V[0,0] = {cov_fe[0,0]:.8f}")
