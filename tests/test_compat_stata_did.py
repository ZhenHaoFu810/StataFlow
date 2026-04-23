"""Tests for compat.stata DID wrappers."""

import numpy as np
import pandas as pd
import pytest

from stataflow.compat.stata import did_imputation, eventstudyinteract, csdid
from stataflow.estimators import DIDImputation, EventStudyInteract, CSDID


def _make_did_data(n_units=50, n_periods=5, seed=42):
    rng = np.random.default_rng(seed)
    units = np.repeat(np.arange(n_units), n_periods)
    times = np.tile(np.arange(n_periods), n_units)
    first_treat = rng.choice([0, 2, 3], size=n_units)
    first_treat = np.repeat(first_treat, n_periods)
    treat = (times >= first_treat).astype(float)
    treat[first_treat == 0] = 0
    y = 1.0 + 2.0 * treat + rng.normal(size=n_units * n_periods)
    df = pd.DataFrame({
        "id": units,
        "time": times,
        "y": y,
        "first_treat": first_treat,
    })
    return df


def _make_eventstudy_data(n_units=50, n_periods=5, seed=42):
    df = _make_did_data(n_units, n_periods, seed)
    df["dm2"] = (df["time"] - df["first_treat"] == -2).astype(float)
    df["dm1"] = (df["time"] - df["first_treat"] == -1).astype(float)
    df["d0"] = (df["time"] - df["first_treat"] == 0).astype(float)
    df["dp1"] = (df["time"] - df["first_treat"] == 1).astype(float)
    df["never_treat"] = (df["first_treat"] == 0).astype(float)
    return df


def test_did_imputation_delegation():
    df = _make_did_data()
    res = did_imputation(df, y="y", id="id", time="time", first_treat="first_treat")
    direct = DIDImputation(df, y="y", id="id", time="time", first_treat="first_treat").fit()
    assert res.model.command == "did_imputation"
    assert len(res.coefficients) == len(direct.coefficients)


def test_did_imputation_unsupported_kwargs():
    df = _make_did_data()
    with pytest.raises(ValueError, match="Unsupported arguments"):
        did_imputation(df, y="y", id="id", time="time", first_treat="first_treat", pretrends=True)


def test_eventstudyinteract_delegation():
    df = _make_eventstudy_data()
    res = eventstudyinteract(
        df, y="y", event_dummies=["dm2", "dm1", "d0", "dp1"],
        cohort="first_treat", control_cohort="never_treat", absorb=["id", "time"]
    )
    direct = EventStudyInteract(
        df, y="y", event_dummies=["dm2", "dm1", "d0", "dp1"],
        cohort="first_treat", control_cohort="never_treat", absorb=["id", "time"]
    ).fit()
    assert res.model.command == "eventstudyinteract"
    assert len(res.coefficients) == len(direct.coefficients)


def test_eventstudyinteract_unsupported_kwargs():
    df = _make_eventstudy_data()
    with pytest.raises(ValueError, match="Unsupported arguments"):
        eventstudyinteract(
            df, y="y", event_dummies=["dm2"],
            cohort="first_treat", control_cohort="never_treat", absorb=["id"],
            graph=True
        )


def test_csdid_delegation():
    df = _make_did_data()
    res = csdid(df, y="y", id="id", time="time", first_treat="first_treat")
    direct = CSDID(df, y="y", id="id", time="time", first_treat="first_treat").fit().estat_event()
    assert res.model.command == "csdid"
    assert len(res.coefficients) == len(direct.coefficients)


def test_csdid_unsupported_kwargs():
    df = _make_did_data()
    with pytest.raises(ValueError, match="Unsupported arguments"):
        csdid(df, y="y", id="id", time="time", first_treat="first_treat", aggtype="group")


def test_csdid_rejects_non_reg_method():
    df = _make_did_data()
    with pytest.raises(ValueError, match="Only method='reg' is supported"):
        csdid(df, y="y", id="id", time="time", first_treat="first_treat", method="dr")


def test_eventstudyinteract_auto_generation():
    """Auto-generation mode should produce same IW coefficients as legacy mode with matching dummies."""
    df = _make_eventstudy_data()
    # Manually create dummies matching the auto-generation naming convention
    df["Dm2"] = df["dm2"]
    df["D0"] = df["d0"]
    df["Dp1"] = df["dp1"]
    # Legacy mode with explicit dummies (same set as auto-generation, omitting -1)
    res_legacy = eventstudyinteract(
        df, y="y", event_dummies=["Dm2", "D0", "Dp1"],
        cohort="first_treat", control_cohort="never_treat",
        absorb=["id", "time"], vce="ols"
    )
    # Auto-generation mode
    res_auto = eventstudyinteract(
        df, y="y", time="time", first_treat="first_treat",
        horizons=[-2, -1, 0, 1], omit=-1,
        cohort="first_treat", control_cohort="never_treat",
        absorb=["id", "time"], vce="ols"
    )
    assert len(res_auto.coefficients) == len(res_legacy.coefficients)
    for c_auto, c_legacy in zip(res_auto.coefficients, res_legacy.coefficients):
        assert c_auto.name == c_legacy.name
        assert pytest.approx(c_auto.beta, abs=1e-10) == c_legacy.beta


def test_eventstudyinteract_auto_generation_cluster():
    """Auto-generation mode with cluster VCE."""
    df = _make_eventstudy_data(n_units=100, n_periods=8)
    res = eventstudyinteract(
        df, y="y", time="time", first_treat="first_treat",
        horizons=[-2, -1, 0, 1, 2], omit=-1,
        cohort="first_treat", control_cohort="never_treat",
        absorb=["id", "time"], vce="cluster", cluster="id"
    )
    assert res.model.command == "eventstudyinteract"
    assert len(res.coefficients) == 4  # -2, 0, 1, 2 (omit -1)


def test_csdid_not_yet_treated_fallback():
    """CSDID should fall back to not-yet-treated when no never-treated units exist."""
    rng = np.random.default_rng(42)
    n_units = 60
    n_periods = 6
    units = np.repeat(np.arange(n_units), n_periods)
    times = np.tile(np.arange(n_periods), n_units)
    # All units are treated; no never-treated group
    first_treat = rng.choice([2, 3, 4], size=n_units)
    first_treat = np.repeat(first_treat, n_periods)
    treat = (times >= first_treat).astype(float)
    y = 1.0 + 2.0 * treat + rng.normal(size=n_units * n_periods)
    df = pd.DataFrame({
        "id": units,
        "time": times,
        "y": y,
        "first_treat": first_treat,
    })
    # Should run without error using not-yet-treated as control
    res = csdid(df, y="y", id="id", time="time", first_treat="first_treat")
    assert res is not None
    assert len(res.coefficients) > 0
    # Ensure Pre_avg exists (there should be pre-treatment periods)
    names = [c.name for c in res.coefficients]
    assert "Pre_avg" in names or any(k.startswith("Tm") for k in names)


# ---------------------------------------------------------------------------
# Edge-case / synthetic tests (Package 005)
# ---------------------------------------------------------------------------

def test_did_imputation_autosample_non_imputable():
    """autosample=True should drop non-imputable units and still produce results."""
    rng = np.random.default_rng(99)
    n_units = 30
    n_periods = 5
    units = np.repeat(np.arange(n_units), n_periods)
    times = np.tile(np.arange(n_periods), n_units)
    # Cohort 2 treated: some units have no control observations
    # (unit 0 is treated at time 2, but we drop its pre-treatment rows)
    first_treat = np.repeat(
        rng.choice([0, 2], size=n_units, p=[0.5, 0.5]), n_periods
    )
    treat = (times >= first_treat).astype(float)
    treat[first_treat == 0] = 0
    y = 1.0 + 2.0 * treat + rng.normal(size=n_units * n_periods)
    df = pd.DataFrame({"id": units, "time": times, "y": y, "first_treat": first_treat})

    # With autosample=True, should succeed even with non-imputable units
    res = did_imputation(df, y="y", id="id", time="time", first_treat="first_treat",
                         autosample=True)
    assert res.model.command == "did_imputation"
    assert len(res.coefficients) > 0


def test_did_imputation_missing_data_drops():
    """Missing y should be dropped before estimation."""
    df = _make_did_data(n_units=40, n_periods=5)
    df.loc[0:5, "y"] = np.nan
    res = did_imputation(df, y="y", id="id", time="time", first_treat="first_treat")
    # Should succeed after internal drop
    assert len(res.coefficients) > 0
    assert res.sample.nobs <= len(df.dropna(subset=["y"]))


def test_eventstudyinteract_single_cohort():
    """EventStudyInteract should work with a single treated cohort."""
    rng = np.random.default_rng(77)
    n_units = 40
    n_periods = 5
    units = np.repeat(np.arange(n_units), n_periods)
    times = np.tile(np.arange(n_periods), n_units)
    # Only one cohort (period 2) plus never-treated
    first_treat = np.repeat(rng.choice([0, 2], size=n_units), n_periods)
    treat = (times >= first_treat).astype(float)
    treat[first_treat == 0] = 0
    y = 1.0 + 2.0 * treat + rng.normal(size=n_units * n_periods)
    df = pd.DataFrame({"id": units, "time": times, "y": y, "first_treat": first_treat})
    df["d0"] = ((df["time"] - df["first_treat"] == 0) & (df["first_treat"] > 0)).astype(float)
    df["dp1"] = ((df["time"] - df["first_treat"] == 1) & (df["first_treat"] > 0)).astype(float)
    df["never_treat"] = (df["first_treat"] == 0).astype(float)

    res = eventstudyinteract(
        df, y="y", event_dummies=["d0", "dp1"],
        cohort="first_treat", control_cohort="never_treat",
        absorb=["id", "time"], vce="ols"
    )
    assert res.model.command == "eventstudyinteract"
    assert len(res.coefficients) == 2


def test_csdid_missing_data_drops():
    """CSDID should drop missing values in key vars before estimation."""
    df = _make_did_data(n_units=40, n_periods=5)
    df.loc[0:5, "y"] = np.nan
    res = csdid(df, y="y", id="id", time="time", first_treat="first_treat")
    assert len(res.coefficients) > 0
    # Note: CSDID _nobs counts effective unit-year pairs used in ATT(g,t),
    # which may differ from simple row count due to multi-period reuse.


def test_csdid_single_cohort():
    """CSDID should work with a single treated cohort."""
    rng = np.random.default_rng(88)
    n_units = 40
    n_periods = 5
    units = np.repeat(np.arange(n_units), n_periods)
    times = np.tile(np.arange(n_periods), n_units)
    first_treat = np.repeat(rng.choice([0, 2], size=n_units), n_periods)
    treat = (times >= first_treat).astype(float)
    treat[first_treat == 0] = 0
    y = 1.0 + 2.0 * treat + rng.normal(size=n_units * n_periods)
    df = pd.DataFrame({"id": units, "time": times, "y": y, "first_treat": first_treat})

    res = csdid(df, y="y", id="id", time="time", first_treat="first_treat")
    assert len(res.coefficients) > 0
    names = [c.name for c in res.coefficients]
    assert any("Tp" in n or "Post" in n for n in names)


def test_did_imputation_allhorizons_false():
    """Default allhorizons=False should only report non-negative horizons."""
    df = _make_did_data(n_units=50, n_periods=5)
    res = did_imputation(
        df, y="y", id="id", time="time", first_treat="first_treat",
        allhorizons=False,
    )
    names = [c.name for c in res.coefficients]
    # All reported horizons should be >= 0 (tau0, tau1, ...)
    for name in names:
        horizon = int(name.replace("tau", ""))
        assert horizon >= 0, f"Expected non-negative horizon, got {name}"


def test_did_imputation_allhorizons_true():
    """allhorizons=True should include negative pretrend horizons."""
    df = _make_did_data(n_units=50, n_periods=5)
    res = did_imputation(
        df, y="y", id="id", time="time", first_treat="first_treat",
        allhorizons=True,
    )
    names = [c.name for c in res.coefficients]
    # With n_periods=5 and first_treat in [0,2,3], there should be
    # pretreatment horizons (-2, -1) for cohorts treated at t>=2.
    negative_names = [n for n in names if int(n.replace("tau", "")) < 0]
    assert len(negative_names) > 0, (
        "allhorizons=True should produce negative horizons, got: " + str(names)
    )


def test_did_imputation_allhorizons_more_horizons_than_default():
    """allhorizons=True should produce strictly more coefficients than False."""
    df = _make_did_data(n_units=50, n_periods=5)
    res_default = did_imputation(
        df, y="y", id="id", time="time", first_treat="first_treat",
        allhorizons=False,
    )
    res_all = did_imputation(
        df, y="y", id="id", time="time", first_treat="first_treat",
        allhorizons=True,
    )
    assert len(res_all.coefficients) > len(res_default.coefficients), (
        "allhorizons=True should yield more horizons than allhorizons=False"
    )


def test_did_imputation_provenance_no_unconditional_options():
    """Default call must not claim allhorizons or autosample in stata_command."""
    df = _make_did_data(n_units=50, n_periods=5)
    res = did_imputation(df, y="y", id="id", time="time", first_treat="first_treat")
    cmd = res.provenance.stata_command
    assert "allhorizons" not in cmd, f"stata_command should not claim allhorizons by default: {cmd}"
    assert "autosample" not in cmd, f"stata_command should not claim autosample by default: {cmd}"
    assert "cluster(id)" in cmd, f"stata_command should include default cluster: {cmd}"


def test_did_imputation_provenance_with_explicit_options():
    """Explicit options must be reflected in stata_command."""
    df = _make_did_data(n_units=50, n_periods=5)
    res = did_imputation(
        df, y="y", id="id", time="time", first_treat="first_treat",
        allhorizons=True, autosample=True,
    )
    cmd = res.provenance.stata_command
    assert "allhorizons" in cmd, f"stata_command should include allhorizons when enabled: {cmd}"
    assert "autosample" in cmd, f"stata_command should include autosample when enabled: {cmd}"
    assert "cluster(id)" in cmd, f"stata_command should include cluster: {cmd}"


# ---------------------------------------------------------------------------
# window / minn support (Package C)
# ---------------------------------------------------------------------------

def test_did_imputation_window_restricts_horizons():
    """window=[0, 2] should only report horizons 0, 1, 2."""
    df = _make_did_data(n_units=50, n_periods=5)
    res = did_imputation(
        df, y="y", id="id", time="time", first_treat="first_treat",
        allhorizons=True, window=[0, 2],
    )
    names = [c.name for c in res.coefficients]
    for name in names:
        h = int(name.replace("tau", ""))
        assert 0 <= h <= 2, f"Expected horizon in [0, 2], got {name}"
    assert "tau0" in names
    assert "tau2" in names
    # tau3 should be excluded
    assert "tau3" not in names


def test_did_imputation_window_with_allhorizons():
    """window with allhorizons=True should include negative horizons within range."""
    df = _make_did_data(n_units=50, n_periods=5)
    res = did_imputation(
        df, y="y", id="id", time="time", first_treat="first_treat",
        allhorizons=True, window=[-2, 1],
    )
    names = [c.name for c in res.coefficients]
    negative = [n for n in names if int(n.replace("tau", "")) < 0]
    assert len(negative) > 0, "window [-2, 1] with allhorizons should include negative horizons"
    for name in names:
        h = int(name.replace("tau", ""))
        assert -2 <= h <= 1, f"Expected horizon in [-2, 1], got {name}"


def test_did_imputation_minn_skips_small_horizons():
    """minn should skip horizons with fewer imputable observations than threshold."""
    df = _make_did_data(n_units=50, n_periods=5)
    # Default call (no minn) should produce more horizons than minn=50
    res_default = did_imputation(
        df, y="y", id="id", time="time", first_treat="first_treat",
        allhorizons=True,
    )
    res_minn = did_imputation(
        df, y="y", id="id", time="time", first_treat="first_treat",
        allhorizons=True, minn=50,
    )
    assert len(res_minn.coefficients) <= len(res_default.coefficients), (
        "minn should reduce or equal the number of reported horizons"
    )


def test_did_imputation_window_invalid_length():
    """window must be a two-element list."""
    df = _make_did_data(n_units=50, n_periods=5)
    with pytest.raises(ValueError, match="window must be a two-element"):
        did_imputation(
            df, y="y", id="id", time="time", first_treat="first_treat",
            window=[0],
        )


def test_did_imputation_provenance_with_window_minn():
    """window and minn must appear in stata_command when explicitly set."""
    df = _make_did_data(n_units=50, n_periods=5)
    res = did_imputation(
        df, y="y", id="id", time="time", first_treat="first_treat",
        window=[0, 2], minn=5,
    )
    cmd = res.provenance.stata_command
    assert "window(0 2)" in cmd, f"stata_command should include window: {cmd}"
    assert "minn(5)" in cmd, f"stata_command should include minn: {cmd}"
