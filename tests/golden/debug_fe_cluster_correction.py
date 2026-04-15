"""
Reverse-engineer Stata's exact cluster correction for xtreg, fe vce(cluster).
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

# Uncorrected variance
V_raw = XtX_inv @ meat @ XtX_inv

# Stata V[0,0] = 0.01151575
# Required total correction = Stata_V / V_raw
required_total = 0.01151575 / V_raw[0, 0]
print(f"Required total correction: {required_total:.10f}")

# Now try many candidate corrections
candidates = {
    "G/(G-1)": G / (G - 1),
    "(N-1)/(N-k)": (n - 1) / (n - k),
    "(N-k)/(N-1)": (n - k) / (n - 1),
    "G/(G-1) * (N-1)/(N-k)": (G / (G - 1)) * ((n - 1) / (n - k)),
    "G/(G-1) * (N-k)/(N-1)": (G / (G - 1)) * ((n - k) / (n - 1)),
    "G/(G-k)": G / (G - k),
    "(G-1)/(G-k)": (G - 1) / (G - k),
    "(N-1)/(N-G-k)": (n - 1) / (n - G - k),
    "(N-G)/(N-G-k)": (n - G) / (n - G - k),
    "(N-G-1)/(N-G-k)": (n - G - 1) / (n - G - k),
    "(N-1)/(N-G)": (n - 1) / (n - G),
    "N/(N-k)": n / (n - k),
    "no correction": 1.0,
}

print(f"\nCandidate corrections:")
for name, val in sorted(candidates.items(), key=lambda x: abs(x[1] - required_total)):
    diff = abs(val - required_total)
    match = "CLOSE!" if diff < 0.01 else ""
    print(f"  {name:35s} = {val:.10f}  (diff={diff:.6f}) {match}")

# Try: maybe Stata uses different effective k for FE
# In FE, we estimate G-1 FE dummies + k slopes = G-1+k parameters
# But after within transformation, only k parameters remain
# Maybe Stata uses k_eff = k + (G-1)/T_avg or something?

# Actually, let me check if the issue is with the "meat" calculation
# Maybe Stata uses different residuals or different X for the meat

# Option: Stata might use the original (non-transformed) X but FE-adjusted residuals
# For xtreg, the residuals are: e_it = y_it - x_it*beta - alpha_i
# where alpha_i = y_bar_i - x_bar_i * beta

# Compute alpha_i and full residuals
alpha = np.zeros(G)
for g in range(G):
    mask_g = entity_id == g
    alpha[g] = np.mean(y[mask_g]) - np.mean(X_w[mask_g, :], axis=0) @ beta - np.mean(entity_means.loc[entity_id == g, '_y'].values - entity_means.loc[entity_id == g, ['_x1', '_x2']].values @ beta)

# Actually alpha_i = y_bar_i - x_bar_i * beta (the entity fixed effect)
# And the full residual is: e_it = y_it - x_it*beta - (alpha_i - alpha_bar)
# where alpha_bar = mean(alpha_i)

# Let me compute this more carefully
# The within residual is: y_it - y_bar_i - (x_it - x_bar_i)*beta
# = (y_it - x_it*beta) - (y_bar_i - x_bar_i*beta)
# = (y_it - x_it*beta) - alpha_i
# So the within residual IS the demeaned version of the full residual

# The full residual would be: y_it - x_it*beta - alpha_i + alpha_bar
# But alpha_bar is absorbed into _cons

# Hmm, actually for the cluster-robust SE in FE, Stata should use the within residuals
# Let me verify that my residuals are correct

print(f"\nResidual check:")
print(f"  sum(residuals_w) = {np.sum(residuals_w):.10f}")
print(f"  rss = {rss:.10f}")
print(f"  Stata rss = 97.504463")

# Check if Stata's meat uses a different formula
# Maybe: sum_g (X_g' * e_g / (T_g - 1)) * (X_g' * e_g / (T_g - 1))' * (T_g - 1)
# For balanced panel: T_g = T = 4 for all g

T = n_periods
meat_alt = np.zeros((k, k))
for g in range(G):
    mask_g = entity_id == g
    X_w_g = X_w[mask_g]
    e_g = residuals_w[mask_g]
    Xe_g = X_w_g.T @ e_g
    # Maybe Stata averages within cluster first?
    meat_alt += np.outer(Xe_g, Xe_g) / (T - 1)

V_alt = XtX_inv @ meat_alt @ XtX_inv
ratio_alt = 0.01151575 / V_alt[0, 0]
print(f"\nWith meat/(T-1): required correction = {ratio_alt:.10f}")

# Or maybe: meat * G/(G-1) only (no N adjustment)
V_g_only = (G / (G - 1)) * V_raw
print(f"\nWith G/(G-1) only: V[0,0] = {V_g_only[0,0]:.10f}")
print(f"Stata V[0,0] = 0.01151575")
print(f"Diff = {abs(V_g_only[0,0] - 0.01151575):.2e}")
