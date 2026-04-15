"""
Test if Stata uses G/(G-1) * (N-1)/(N-k-G+1) for FE cluster correction.
Also test using the exact correction from Stata's output.
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
G = n_entities
beta = np.linalg.solve(X_w.T @ X_w, X_w.T @ y_w)
residuals_w = y_w - X_w @ beta
rss = np.sum(residuals_w ** 2)

XtX = X_w.T @ X_w
XtX_inv = np.linalg.inv(XtX)

# Meat
meat = np.zeros((k, k))
for g in range(G):
    mask_g = entity_id == g
    X_w_g = X_w[mask_g]
    e_g = residuals_w[mask_g]
    Xe_g = X_w_g.T @ e_g
    meat += np.outer(Xe_g, Xe_g)

V_raw = XtX_inv @ meat @ XtX_inv

# Try: correction = (G/(G-1)) * ((N-1)/(N-k-G+1))
# where N-k-G+1 = N-G-k+1
correction1 = (G / (G - 1)) * ((n - 1) / (n - k - G + 1))
V1 = correction1 * V_raw
print(f"Correction G/(G-1) * (N-1)/(N-k-G+1):")
print(f"  correction = {correction1:.10f}")
print(f"  V[0,0] = {V1[0,0]:.10f}")
print(f"  Stata V[0,0] = 0.01151575")

# Try: correction = (G/(G-1)) * ((N-1)/(N-G))
correction2 = (G / (G - 1)) * ((n - 1) / (n - G))
V2 = correction2 * V_raw
print(f"\nCorrection G/(G-1) * (N-1)/(N-G):")
print(f"  correction = {correction2:.10f}")
print(f"  V[0,0] = {V2[0,0]:.10f}")

# Try: correction = G/(G-1) * (N)/(N-k)
correction3 = (G / (G - 1)) * (n / (n - k))
V3 = correction3 * V_raw
print(f"\nCorrection G/(G-1) * N/(N-k):")
print(f"  correction = {correction3:.10f}")
print(f"  V[0,0] = {V3[0,0]:.10f}")

# The required correction is 1.05216609
# My current correction (N-1)/(N-k) * G/(G-1) = 1.04324956
# Ratio: 1.05216609 / 1.04324956 = 1.00855

# This is very close to (N-1)/(N-k) = 1.00847458
# So maybe: correction = [(N-1)/(N-k)]^2 * G/(G-1)?
correction4 = ((n - 1) / (n - k)) ** 2 * (G / (G - 1))
V4 = correction4 * V_raw
print(f"\nCorrection [(N-1)/(N-k)]^2 * G/(G-1):")
print(f"  correction = {correction4:.10f}")
print(f"  V[0,0] = {V4[0,0]:.10f}")

# Or maybe: correction = (N-1)/(N-k) * G/(G-1) * (N-1)/(N-G)?
correction5 = ((n - 1) / (n - k)) * (G / (G - 1)) * ((n - 1) / (n - G))
V5 = correction5 * V_raw
print(f"\nCorrection (N-1)/(N-k) * G/(G-1) * (N-1)/(N-G):")
print(f"  correction = {correction5:.10f}")
print(f"  V[0,0] = {V5[0,0]:.10f}")

# What about: correction = (N-1)/(N-k) * G/(G-1) * (N-k)/(N-G)?
correction6 = ((n - 1) / (n - k)) * (G / (G - 1)) * ((n - k) / (n - G))
V6 = correction6 * V_raw
print(f"\nCorrection (N-1)/(N-k) * G/(G-1) * (N-k)/(N-G):")
print(f"  correction = {correction6:.10f}")
print(f"  V[0,0] = {V6[0,0]:.10f}")

# The answer must be 1.05216609
# Let me try to factorize it differently
# 1.05216609 / (G/(G-1)) = 1.05216609 / 1.03448276 = 1.01708955
# 1.01708955 is close to... (N-1)/(N-17)? N/(N-17)?

needed_after_g = 1.05216609 / (G / (G - 1))
print(f"\nAfter removing G/(G-1), needed n_adj-like factor: {needed_after_g:.10f}")

# Try (N-1)/(N-k-1) = 119/117 = 1.01709402
print(f"  (N-1)/(N-k-1) = {(n-1)/(n-k-1):.10f}")
print(f"  (N)/(N-k-1) = {n/(n-k-1):.10f}")
print(f"  (N-1)/(N-k-2) = {(n-1)/(n-k-2):.10f}")

# Bingo? (N-1)/(N-k-1) = 1.01709402
# Compare to needed: 1.01708955
# Very close!

correction7 = (G / (G - 1)) * ((n - 1) / (n - k - 1))
V7 = correction7 * V_raw
print(f"\nCorrection G/(G-1) * (N-1)/(N-k-1):")
print(f"  correction = {correction7:.10f}")
print(f"  V[0,0] = {V7[0,0]:.10f}")
print(f"  Stata V[0,0] = 0.01151575")
print(f"  Diff = {abs(V7[0,0] - 0.01151575):.2e}")
