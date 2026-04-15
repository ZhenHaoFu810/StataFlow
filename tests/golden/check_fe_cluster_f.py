"""
Verify FE + cluster F-statistic calculation.
"""

import numpy as np

# Stata values
N = 120
G = 30
k = 2
rss = 97.504463
mss = 459.26546
F_stata = 195.39913
df_r_stata = 29

# Python calculation
# F = (MSS/k) / (RSS/df_resid)
# For cluster: df_resid = G - 1 = 29

# But what is MSS in FE context?
# MSS = TSS_within - RSS
# TSS_within = sum of (y_w)^2

# From the verify script, RSS (within) = 97.504463
# If MSS = 459.26546, then F = (459.26546/2) / (97.504463/29) = 229.63 / 3.36 = 68.32

# That doesn't match! Let me check if MSS/TSS calculation is different.

# Actually, Stata's F for FE cluster is the Wald F:
# F = (1/k) * beta' * V_rob^{-1} * beta

# Or maybe it's still the traditional F but with cluster df?
# F = (MSS/k) / (RSS/(G-1))

F_traditional = (mss / k) / (rss / (G - 1))
print(f"F (traditional, G-1) = {F_traditional:.6f}")
print(f"Stata F = {F_stata:.6f}")

# That's not right either. Let me check if MSS is computed differently.
# In FE, MSS = sum of (y_hat_w - y_bar_w)^2 but y_bar_w = 0 (demeaned)
# So MSS = sum(y_hat_w^2)

# Actually, the issue might be that Stata's MSS in e(mss) is from a different calculation.
# Let me check: F = 195.40, df1=2, df2=29
# RSS = 97.504463
# If F = (MSS/2)/(RSS/29), then MSS = F * 2 * RSS/29 = 195.40 * 2 * 97.504463/29 = 1312.5

implied_mss = F_stata * k * rss / (G - 1)
print(f"Implied MSS from F = {implied_mss:.6f}")
print(f"Stata e(mss) = {mss:.6f}")

# They don't match! This means Stata's e(mss) and e(F) come from different calculations.
# The F-statistic in FE cluster is likely the Wald F, not the traditional F.

# For the Wald F:
# F = (1/k) * beta' * V^{-1} * beta
# where V is the cluster-robust covariance matrix

# Since I don't have the actual beta and V, let me just check if Python's formula is close.
# The key is: what df does Stata use for RMSE?

# From earlier: RSS/RMSE^2 = 117.0
# 117 = N - k - 1 = 120 - 2 - 1 = 117 ✓

rmse_check = np.sqrt(rss / (N - k - 1))
print(f"\nRMSE = sqrt(RSS/(N-k-1)) = {rmse_check:.8f}")
print(f"Stata RMSE = 0.91289182")
