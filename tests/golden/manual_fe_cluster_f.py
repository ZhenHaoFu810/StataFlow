"""
Manual verification of FE + cluster Wald F.
"""

import numpy as np
import pandas as pd

np.random.seed(66666)
n_entities = 30
n_periods = 4
n = n_entities * n_periods

entity_id = np.repeat(np.arange(n_entities), n_periods)
time_id = np.tile(np.arange(n_periods), n_entities)
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

# OLS
k = 2
beta = np.linalg.solve(X_w.T @ X_w, X_w.T @ y_w)
residuals_w = y_w - X_w @ beta
rss = np.sum(residuals_w ** 2)

# Cluster-robust VCE
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

# Small sample corrections
n_adj = (n - 1) / (n - k)
g_adj = G / (G - 1)

cov_beta = n_adj * g_adj * XtX_inv @ meat @ XtX_inv

# Wald F
cov_inv = np.linalg.inv(cov_beta)
wald_stat = float(beta @ cov_inv @ beta)
F_wald = wald_stat / k

print(f"beta = {beta}")
print(f"RSS = {rss:.8f}")
print(f"n_adj = {n_adj:.8f}")
print(f"g_adj = {g_adj:.8f}")
print(f"cov_beta = \n{cov_beta}")
print(f"Wald statistic = {wald_stat:.6f}")
print(f"F_wald = {F_wald:.6f}")
print(f"Stata F = 195.399130")

# Check if Stata uses different correction
# Maybe (N-k)/(N-1) instead?
n_adj2 = (n - k) / (n - 1)
cov_beta2 = n_adj2 * g_adj * XtX_inv @ meat @ XtX_inv
cov_inv2 = np.linalg.inv(cov_beta2)
wald_stat2 = float(beta @ cov_inv2 @ beta)
F_wald2 = wald_stat2 / k
print(f"\nWith n_adj2 = (n-k)/(n-1):")
print(f"F_wald2 = {F_wald2:.6f}")

# Or maybe no n_adj at all?
cov_beta3 = g_adj * XtX_inv @ meat @ XtX_inv
cov_inv3 = np.linalg.inv(cov_beta3)
wald_stat3 = float(beta @ cov_inv3 @ beta)
F_wald3 = wald_stat3 / k
print(f"\nWith no n_adj (only g_adj):")
print(f"F_wald3 = {F_wald3:.6f}")
