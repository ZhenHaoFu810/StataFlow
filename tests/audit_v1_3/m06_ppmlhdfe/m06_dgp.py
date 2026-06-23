"""Reusable DGPs for the M06 PPMLHDFE modular audit v1.3.

All DGPs are intentionally new and use deterministic seeds. They are not
shared with existing golden tests.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def _make_entity_time(rng: np.random.Generator, n_entity: int, n_time: int) -> pd.DataFrame:
    """Create a balanced panel with entity and time identifiers."""
    rows = []
    for e in range(n_entity):
        for t in range(n_time):
            rows.append({"entity_id": e + 1, "time_id": t + 1})
    return pd.DataFrame(rows)


def dgp_s1_small_panel(seed: int = 20260612) -> pd.DataFrame:
    """S1: small panel with entity FE and time trend."""
    rng = np.random.default_rng(seed)
    n_entity, n_time = 12, 5
    df = _make_entity_time(rng, n_entity, n_time)
    n = len(df)
    df["x1"] = rng.normal(0, 1, size=n)
    df["x2"] = rng.normal(0, 1, size=n)
    # time trend variable (continuous)
    df["trend"] = df["time_id"].astype(float)
    # true linear predictor without FE
    eta = 0.5 + 0.4 * df["x1"] + -0.3 * df["x2"] + 0.1 * df["trend"]
    # add entity fixed effects
    entity_fe = rng.normal(0, 0.8, size=n_entity)
    df["eta"] = eta + entity_fe[df["entity_id"].values - 1].astype(float)
    df["y"] = rng.poisson(np.exp(df["eta"]))
    return df


def dgp_s2_two_way_fe(seed: int = 20260613) -> pd.DataFrame:
    """S2: two-way FE with zero-inflated Poisson."""
    rng = np.random.default_rng(seed)
    n_entity, n_time = 20, 10
    df = _make_entity_time(rng, n_entity, n_time)
    n = len(df)
    df["x1"] = rng.normal(0, 1, size=n)
    df["x2"] = rng.normal(0, 1, size=n)
    entity_fe = rng.normal(-0.5, 1.0, size=n_entity)
    time_fe = rng.normal(0, 0.5, size=n_time)
    eta = (
        0.3
        + 0.6 * df["x1"]
        + -0.4 * df["x2"]
        + entity_fe[df["entity_id"].values - 1]
        + time_fe[df["time_id"].values - 1]
    )
    df["eta"] = eta
    # zero-inflation: randomly set some latent rates to a very low value
    inflation = rng.random(n) < 0.15
    rate = np.exp(df["eta"])
    rate[inflation] *= 0.05
    df["y"] = rng.poisson(rate)
    return df


def dgp_s3_missing_screen(seed: int = 20260614) -> pd.DataFrame:
    """S3: S2 data with missing values in y, x, FE, and cluster."""
    rng = np.random.default_rng(seed)
    df = dgp_s2_two_way_fe(seed=seed + 1)
    n = len(df)
    # cluster id: independent of entity/time so it is not nested in the FE
    df["cl"] = rng.integers(1, 21, size=n)
    # introduce missing values deterministically by row index
    miss_y = rng.choice(n, size=int(0.05 * n), replace=False)
    miss_x1 = rng.choice(n, size=int(0.05 * n), replace=False)
    miss_entity = rng.choice(n, size=int(0.03 * n), replace=False)
    miss_cl = rng.choice(n, size=int(0.03 * n), replace=False)
    df.loc[miss_y, "y"] = np.nan
    df.loc[miss_x1, "x1"] = np.nan
    df.loc[miss_entity, "entity_id"] = np.nan
    df.loc[miss_cl, "cl"] = np.nan
    return df


def dgp_s4_collinear_within_fe(seed: int = 20260615) -> pd.DataFrame:
    """S4: variable that is constant within entity FE and should be dropped."""
    rng = np.random.default_rng(seed)
    n_entity, n_time = 20, 6
    df = _make_entity_time(rng, n_entity, n_time)
    n = len(df)
    df["x1"] = rng.normal(0, 1, size=n)
    # x_const equals entity identifier, fully explained by entity FE
    df["x_const"] = df["entity_id"].astype(float)
    entity_fe = rng.normal(0, 1.0, size=n_entity)
    eta = 0.2 + 0.5 * df["x1"] + entity_fe[df["entity_id"].values - 1]
    df["eta"] = eta
    df["y"] = rng.poisson(np.exp(df["eta"]))
    return df


def dgp_s5_separation_fe(seed: int = 20260616) -> pd.DataFrame:
    """S5: entities with all y=0 to trigger FE separation."""
    rng = np.random.default_rng(seed)
    n_entity, n_time = 15, 4
    df = _make_entity_time(rng, n_entity, n_time)
    n = len(df)
    df["x1"] = rng.normal(0, 1, size=n)
    df["x2"] = rng.normal(0, 1, size=n)
    entity_fe = rng.normal(0, 0.5, size=n_entity)
    eta = 0.1 + 0.4 * df["x1"] + -0.3 * df["x2"] + entity_fe[df["entity_id"].values - 1]
    df["eta"] = eta
    df["y"] = rng.poisson(np.exp(df["eta"]))
    # Force the first 3 entities to have y == 0
    zero_entities = [1, 2, 3]
    df.loc[df["entity_id"].isin(zero_entities), "y"] = 0
    return df


def dgp_s6_cluster_singleton(seed: int = 20260617) -> pd.DataFrame:
    """S6: cluster id different from entity with singleton clusters."""
    rng = np.random.default_rng(seed)
    n_entity, n_time = 10, 12
    df = _make_entity_time(rng, n_entity, n_time)
    n = len(df)
    df["x1"] = rng.normal(0, 1, size=n)
    df["x2"] = rng.normal(0, 1, size=n)
    entity_fe = rng.normal(0, 0.7, size=n_entity)
    eta = 0.3 + 0.5 * df["x1"] + -0.2 * df["x2"] + entity_fe[df["entity_id"].values - 1]
    df["eta"] = eta
    df["y"] = rng.poisson(np.exp(df["eta"]))
    # cluster id: mostly entity-level but split one entity into singletons
    df["cl"] = df["entity_id"].astype(float)
    single_entity = 1
    single_mask = df["entity_id"] == single_entity
    # give each observation in entity 1 its own cluster id (large values)
    df.loc[single_mask, "cl"] = 100.0 + np.arange(single_mask.sum(), dtype=float)
    return df


def dgp_s7_weights_offset(seed: int = 20260618) -> pd.DataFrame:
    """S7: entity FE, offset, and positive weights."""
    rng = np.random.default_rng(seed)
    n_entity, n_time = 15, 10
    df = _make_entity_time(rng, n_entity, n_time)
    n = len(df)
    df["x1"] = rng.normal(0, 1, size=n)
    df["x2"] = rng.normal(0, 1, size=n)
    entity_fe = rng.normal(0, 0.6, size=n_entity)
    # offset (log-scale effect)
    df["off"] = rng.uniform(0.3, 1.5, size=n)
    eta = (
        0.1
        + 0.4 * df["x1"]
        + -0.25 * df["x2"]
        + entity_fe[df["entity_id"].values - 1]
        + df["off"]
    )
    df["eta"] = eta
    df["y"] = rng.poisson(np.exp(df["eta"]))
    # positive aweight/pweight
    df["w"] = rng.uniform(0.5, 2.0, size=n)
    return df


def dgp_s8_eform_predict(seed: int = 20260619) -> pd.DataFrame:
    """S8: entity FE for eform and predict type checks."""
    rng = np.random.default_rng(seed)
    n_entity, n_time = 10, 10
    df = _make_entity_time(rng, n_entity, n_time)
    n = len(df)
    df["x1"] = rng.normal(0, 1, size=n)
    df["x2"] = rng.normal(0, 1, size=n)
    entity_fe = rng.normal(0, 0.5, size=n_entity)
    eta = 0.4 + 0.5 * df["x1"] + -0.35 * df["x2"] + entity_fe[df["entity_id"].values - 1]
    df["eta"] = eta
    df["y"] = rng.poisson(np.exp(df["eta"]))
    return df
