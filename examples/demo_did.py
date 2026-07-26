"""Demo: Difference-in-differences with staggered adoption.

Covers did_imputation (BJS), eventstudyinteract (Sun-Abraham), and
csdid (Callaway-Sant'Anna). Treatment cohorts (first_treat) are recorded
in calendar years, the same units as the time variable.
"""

import numpy as np
import pandas as pd
from stataflow.compat.stata import csdid, did_imputation, eventstudyinteract

# Synthetic staggered-adoption panel
rng = np.random.default_rng(40)
n_units = 160
years = np.arange(2000, 2008)
n_periods = len(years)
n = n_units * n_periods

units = np.repeat(np.arange(n_units), n_periods)
time = np.tile(years, n_units)

# Treatment cohorts in calendar-year units; one third of units adopt in
# 2004, one third in 2006, and one third are never treated.
unit_ft = np.full(n_units, np.nan)
unit_ft[n_units // 3 : 2 * n_units // 3] = 2004.0
unit_ft[2 * n_units // 3 :] = 2006.0
first_treat = np.repeat(unit_ft, n_periods)

treat = (pd.notna(first_treat)) & (time >= first_treat)
fe_u = np.repeat(rng.normal(0, 1, n_units), n_periods)
fe_t = np.tile(rng.normal(0, 0.5, n_periods), n_units)
y = fe_u + fe_t + 1.5 * treat.astype(float) + rng.normal(0, 1, n)

# BJS convention: never-treated units have missing first_treat.
df = pd.DataFrame({
    "y": y,
    "id": units,
    "year": time,
    "first_treat": first_treat,
})

# BJS imputation estimator with cluster VCE
print("did_imputation: BJS imputation with cluster VCE")
result_bjs = did_imputation(df, y="y", id="id", time="year", first_treat="first_treat", cluster="id")
result_bjs.display()

# csdid / eventstudyinteract convention: never-treated units have
# first_treat = 0, flagged by a control-cohort indicator.
df0 = df.assign(
    first_treat=df["first_treat"].fillna(0).astype(int),
    never_treat=df["first_treat"].isna().astype(float),
)

# Relative-time dummies with binned endpoints (standard event-study
# practice: observations beyond the reported window are grouped into the
# outermost bins rather than falling into the omitted reference cell).
rel_time = df0["year"] - df0["first_treat"]
df0["Dm2"] = (rel_time <= -2).astype(float)
df0["D0"] = (rel_time == 0).astype(float)
df0["Dp1"] = (rel_time == 1).astype(float)
df0["Dp2"] = (rel_time >= 2).astype(float)

# Sun-Abraham interaction-weighted event study
print("\neventstudyinteract: Sun-Abraham event study")
result_iw = eventstudyinteract(
    df0,
    y="y",
    event_dummies=["Dm2", "D0", "Dp1", "Dp2"],
    cohort="first_treat",
    control_cohort="never_treat",
    absorb=["id", "year"],
    vce="cluster",
    cluster="id",
)
result_iw.display()

# Callaway-Sant'Anna group-time ATT
model = csdid(df0, y="y", id="id", time="year", first_treat="first_treat")

# ADR-0005 display contract: model.result / model.summary() / model.display()
# delegate to the default (event) aggregation.
print("\ncsdid: Callaway-Sant'Anna, default (event) aggregation")
model.display()
