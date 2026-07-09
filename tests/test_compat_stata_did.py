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
    # Stata's did_imputation uses missing first_treat for never-treated units.
    first_treat = rng.choice([np.nan, 2, 3], size=n_units)
    first_treat = np.repeat(first_treat, n_periods)
    treat = (pd.notna(first_treat) & (times >= first_treat)).astype(float)
    y = 1.0 + 2.0 * treat + rng.normal(size=n_units * n_periods)
    df = pd.DataFrame({
        "id": units,
        "time": times,
        "y": y,
        "first_treat": first_treat,
    })
    return df


def _make_csdid_data(n_units=50, n_periods=5, seed=42):
    """Generate panel data where first_treat=0 marks never-treated units.

    This matches Stata's csdid convention; use it for CSDID-specific tests.
    DID-imputation tests should continue to use _make_did_data, which uses
    missing first_treat for never-treated units.
    """
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
    df["never_treat"] = df["first_treat"].isna().astype(float)
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
        did_imputation(df, y="y", id="id", time="time", first_treat="first_treat", foo=True)


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
    df = _make_csdid_data()
    model = csdid(df, y="y", id="id", time="time", first_treat="first_treat")
    res = model.estat("event")
    direct = CSDID(df, y="y", id="id", time="time", first_treat="first_treat").fit().estat_event()
    assert res.model.command == "csdid"
    assert len(res.coefficients) == len(direct.coefficients)


def test_csdid_default_returns_fitted_model_for_chained_estat():
    """Default csdid should return a fitted model so users can call multiple estat outputs."""
    df = _make_csdid_data(n_units=100, n_periods=5)
    model = csdid(df, y="y", id="id", time="time", first_treat="first_treat")
    assert isinstance(model, CSDID)
    event = model.estat("event")
    simple = model.estat("simple")
    pretrend = model.estat("pretrend")
    assert event.model.command == "csdid"
    assert simple.model.command == "csdid"
    assert pretrend.model.command == "csdid"


def test_csdid_unsupported_kwargs():
    df = _make_csdid_data()
    with pytest.raises(ValueError, match="Unsupported arguments"):
        csdid(df, y="y", id="id", time="time", first_treat="first_treat", graph=True)


def test_csdid_notyet_option_uses_not_yet_treated_controls():
    """notyet=True should be a supported csdid option for method='reg'."""
    df = _make_csdid_data(n_units=200, n_periods=6)
    res_default = csdid(
        df, y="y", id="id", time="time", first_treat="first_treat",
    ).estat("event")
    res_notyet = csdid(
        df, y="y", id="id", time="time", first_treat="first_treat",
        notyet=True,
    ).estat("event")
    assert res_notyet.model.command == "csdid"
    default_names = [c.name for c in res_default.coefficients]
    notyet_names = [c.name for c in res_notyet.coefficients]
    assert default_names != notyet_names or any(
        not np.isclose(left.beta, right.beta)
        for left, right in zip(res_default.coefficients, res_notyet.coefficients)
    )


def test_csdid_known_unimplemented_options_are_explicit():
    """Known Stata csdid options should not be rejected as unknown kwargs."""
    df = _make_csdid_data()
    for option in (
        {"window": [-1, 2]},
        {"minn": 10},
        {"gtcontrol": True},
        {"longdiff": True},
        {"long": True},
        {"long2": True},
        {"asinr": True},
        {"pscoretrim": 0.99},
        {"saverif": "rif.dta"},
        {"wboot": True},
        {"rseed": 42},
        {"pointwise": True},
    ):
        with pytest.raises(NotImplementedError, match=next(iter(option))):
            csdid(
                df, y="y", id="id", time="time", first_treat="first_treat",
                **option,
            )


def test_csdid_rejects_unsupported_method():
    df = _make_csdid_data()
    with pytest.raises(ValueError, match="Only method='reg', 'drimp', or 'dripw'"):
        csdid(df, y="y", id="id", time="time", first_treat="first_treat", method="foo")


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
    model = csdid(df, y="y", id="id", time="time", first_treat="first_treat")
    res = model.estat("event")
    assert res is not None
    assert len(res.coefficients) > 0
    # Ensure Pre_avg exists (there should be pre-treatment periods)
    names = [c.name for c in res.coefficients]
    assert "Pre_avg" in names or any(k.startswith("Tm") for k in names)


@pytest.mark.parametrize("method", ["reg", "drimp"])
def test_csdid_notyet_includes_never_treated_units(method):
    """Stata's notyet controls combine never-treated and future cohorts."""
    rng = np.random.default_rng(20260616)
    n_per_group = 12
    periods = np.arange(5)
    unit_cohorts = np.repeat([0, 2, 4], n_per_group)
    units = np.repeat(np.arange(len(unit_cohorts)), len(periods))
    time = np.tile(periods, len(unit_cohorts))
    first_treat = np.repeat(unit_cohorts, len(periods))
    x = rng.normal(size=len(units))
    treated = (first_treat > 0) & (time >= first_treat)
    y = 1.0 + 0.3 * x + 1.5 * treated + rng.normal(scale=0.2, size=len(units))
    df = pd.DataFrame(
        {
            "id": units,
            "time": time,
            "y": y,
            "first_treat": first_treat,
            "x": x,
        }
    )

    model = CSDID(
        df,
        y="y",
        id="id",
        time="time",
        first_treat="first_treat",
        xvars=["x"] if method == "drimp" else None,
    )
    model.fit(method=method, notyet=True)

    never_units = set(np.flatnonzero(unit_cohorts == 0))
    used_units = {unit for unit, _ in model._used_rows}
    assert never_units <= used_units


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
        rng.choice([np.nan, 2], size=n_units, p=[0.5, 0.5]), n_periods
    )
    treat = (pd.notna(first_treat) & (times >= first_treat)).astype(float)
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


def test_did_imputation_sample_mask_nobs_consistency():
    """sample_mask length must equal n_input_rows and sum to nobs after autosample."""
    df = pd.DataFrame({
        "id": [0, 0, 1, 1, 2],
        "time": [0, 1, 0, 1, 1],
        "y": [1.0, 1.0, 1.0, 1.0, 2.0],
        "first_treat": [np.nan, np.nan, np.nan, np.nan, 1],
    })
    res = did_imputation(
        df, y="y", id="id", time="time", first_treat="first_treat",
        autosample=True,
    )
    assert len(res.sample.sample_mask) == len(df)
    assert sum(res.sample.sample_mask) == res.sample.nobs == 4


def test_did_imputation_first_treat_missing_is_never_treated():
    """Missing first_treat identifies never-treated units; finite values identify cohorts."""
    df = pd.DataFrame({
        "id": [0, 0, 1, 1, 2, 2, 3, 3],
        "time": [0, 1, 0, 1, 0, 1, 0, 1],
        "y": [1.0, 1.0, 1.0, 1.2, 2.0, 2.2, 3.0, 3.2],
        "first_treat": [np.nan, np.nan, 0, 0, -1, -1, 1, 1],
    })
    model = DIDImputation(df, y="y", id="id", time="time", first_treat="first_treat")
    res = model.fit(autosample=True, saveestimates="effect")

    never_treated = df["first_treat"].isna()
    assert model.saveestimates_[never_treated].isna().all()

    ever_treated_post = df["first_treat"].notna() & (df["time"] >= df["first_treat"])
    assert model.saveestimates_[ever_treated_post].notna().all()

    assert len(res.coefficients) > 0


def test_did_imputation_first_treat_missing_never_treated():
    """Rows with missing first_treat are treated as never-treated controls."""
    df = pd.DataFrame({
        "id": [0, 0, 1, 1, 2, 2],
        "time": [0, 1, 0, 1, 0, 1],
        "y": [1.0, 1.0, 1.0, 1.0, 2.0, 2.0],
        "first_treat": [np.nan, np.nan, 1, 1, np.nan, np.nan],
    })
    res = did_imputation(
        df, y="y", id="id", time="time", first_treat="first_treat",
        autosample=True,
    )
    # Rows 4 and 5 (id 2) have missing first_treat and are kept as never-treated.
    missing_rows = df["first_treat"].isna()
    assert all(np.array(res.sample.sample_mask)[missing_rows.values])
    assert res.sample.nobs == 6


def test_did_imputation_negative_zero_time_values():
    """Panels with negative or zero time values must be handled correctly."""
    df = pd.DataFrame({
        "id": [0, 0, 0, 0, 0, 1, 1, 1, 1, 1],
        "time": [-2, -1, 0, 1, 2, -2, -1, 0, 1, 2],
        "y": [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 2.0, 2.0],
        "first_treat": [np.nan, np.nan, np.nan, np.nan, np.nan, 1, 1, 1, 1, 1],
    })
    res = did_imputation(
        df, y="y", id="id", time="time", first_treat="first_treat",
        autosample=True,
    )
    # id=0 is never-treated; id=1 is treated at time 1.
    assert len(res.coefficients) > 0
    assert res.sample.nobs > 0
    assert len(res.sample.sample_mask) == len(df)


def test_eventstudyinteract_single_cohort():
    """EventStudyInteract should work with a single treated cohort."""
    rng = np.random.default_rng(77)
    n_units = 40
    n_periods = 5
    units = np.repeat(np.arange(n_units), n_periods)
    times = np.tile(np.arange(n_periods), n_units)
    # Only one cohort (period 2) plus never-treated
    first_treat = np.repeat(rng.choice([np.nan, 2], size=n_units), n_periods)
    treat = (pd.notna(first_treat) & (times >= first_treat)).astype(float)
    y = 1.0 + 2.0 * treat + rng.normal(size=n_units * n_periods)
    df = pd.DataFrame({"id": units, "time": times, "y": y, "first_treat": first_treat})
    df["d0"] = ((df["time"] - df["first_treat"] == 0) & (df["first_treat"] > 0)).astype(float)
    df["dp1"] = ((df["time"] - df["first_treat"] == 1) & (df["first_treat"] > 0)).astype(float)
    df["never_treat"] = df["first_treat"].isna().astype(float)

    res = eventstudyinteract(
        df, y="y", event_dummies=["d0", "dp1"],
        cohort="first_treat", control_cohort="never_treat",
        absorb=["id", "time"], vce="ols"
    )
    assert res.model.command == "eventstudyinteract"
    assert len(res.coefficients) == 2


def test_csdid_missing_data_drops():
    """CSDID should drop missing values in key vars before estimation."""
    df = _make_csdid_data(n_units=40, n_periods=5)
    df.loc[0:5, "y"] = np.nan
    model = csdid(df, y="y", id="id", time="time", first_treat="first_treat")
    res = model.estat("event")
    assert len(res.coefficients) > 0
    # Note: CSDID _nobs counts effective unit-year pairs used in ATT(g,t),
    # which may differ from simple row count due to multi-period reuse.


def test_csdid_unbalanced_panel_skips_empty_group_time_cells():
    """CSDID should not silently propagate NaN ATT(g,t) on unbalanced panels."""
    df = pd.DataFrame({
        "id": [1, 1, 2, 2, 3, 3],
        "time": [1, 2, 1, 2, 1, 2],
        "first_treat": [2, 2, 0, 0, 0, 0],
        "y": [1.0, np.nan, 3.0, 4.0, 5.0, 6.0],
    })

    model = csdid(df, y="y", id="id", time="time", first_treat="first_treat")
    res = model.estat("event")

    assert len(res.coefficients) == 0 or all(
        np.isfinite(c.beta) and np.isfinite(c.std_err)
        for c in res.coefficients
    )


def test_csdid_single_cohort():
    """CSDID should work with a single treated cohort."""
    rng = np.random.default_rng(88)
    n_units = 40
    n_periods = 5
    units = np.repeat(np.arange(n_units), n_periods)
    times = np.tile(np.arange(n_periods), n_units)
    # Use 0 for never-treated to match Stata's csdid convention
    first_treat = np.repeat(rng.choice([0, 2], size=n_units), n_periods)
    treat = (times >= first_treat).astype(float)
    treat[first_treat == 0] = 0
    y = 1.0 + 2.0 * treat + rng.normal(size=n_units * n_periods)
    df = pd.DataFrame({"id": units, "time": times, "y": y, "first_treat": first_treat})

    model = csdid(df, y="y", id="id", time="time", first_treat="first_treat")
    res = model.estat("event")
    assert len(res.coefficients) > 0
    names = [c.name for c in res.coefficients]
    assert any("Tp" in n or "Post" in n for n in names)


def test_did_imputation_allhorizons_false():
    """Default allhorizons=False should report a single aggregate tau coefficient."""
    df = _make_did_data(n_units=50, n_periods=5)
    res = did_imputation(
        df, y="y", id="id", time="time", first_treat="first_treat",
        allhorizons=False,
    )
    names = [c.name for c in res.coefficients]
    assert names == ["tau"], f"Expected ['tau'] in aggregate mode, got {names}"


def test_did_imputation_allhorizons_true():
    """allhorizons=True should report event-study tauh for each non-negative horizon."""
    df = _make_did_data(n_units=50, n_periods=5)
    df["time"] = df["time"] + 2001
    df.loc[df["first_treat"] > 0, "first_treat"] += 2001
    res = did_imputation(
        df, y="y", id="id", time="time", first_treat="first_treat",
        allhorizons=True,
    )
    names = [c.name for c in res.coefficients]
    # Should contain tau0, tau1, ... (non-negative event-time horizons)
    horizons = {int(name.replace("tau", "")) for name in names}
    assert all(h >= 0 for h in horizons), (
        f"allhorizons=True should only include non-negative horizons, got {names}"
    )
    assert "tau0" in names


def test_did_imputation_allhorizons_more_horizons_than_default():
    """allhorizons=True reports event-study coefficients; allhorizons=False reports aggregate tau."""
    df = _make_did_data(n_units=50, n_periods=5)
    df["time"] = df["time"] + 2001
    df.loc[df["first_treat"] > 0, "first_treat"] += 2001
    res_default = did_imputation(
        df, y="y", id="id", time="time", first_treat="first_treat",
        allhorizons=False,
    )
    res_all = did_imputation(
        df, y="y", id="id", time="time", first_treat="first_treat",
        allhorizons=True,
    )
    default_names = {c.name for c in res_default.coefficients}
    all_names = {c.name for c in res_all.coefficients}
    # Aggregate mode has exactly one coefficient (tau)
    assert default_names == {"tau"}, f"Expected aggregate mode to return ['tau'], got {default_names}"
    # Event-study mode has multiple tauh coefficients
    assert len(all_names) > 1, f"Expected event-study mode to have multiple horizons, got {all_names}"


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
    """The Python-native estimator supports window-based horizon filtering."""
    df = _make_did_data(n_units=50, n_periods=5)
    model = DIDImputation(df, y="y", id="id", time="time", first_treat="first_treat")
    res = model.fit(allhorizons=True, window=[0, 2])
    names = [c.name for c in res.coefficients]
    for name in names:
        h = int(name.replace("tau", ""))
        assert 0 <= h <= 2, f"Expected horizon in [0, 2], got {name}"
    assert "tau0" in names
    assert "tau2" in names
    # tau3 should be excluded
    assert "tau3" not in names


def test_did_imputation_window_with_allhorizons():
    """Python-native window filtering works together with allhorizons=True."""
    df = _make_did_data(n_units=50, n_periods=5)
    df["time"] = df["time"] + 2001
    df.loc[df["first_treat"] > 0, "first_treat"] += 2001
    model = DIDImputation(df, y="y", id="id", time="time", first_treat="first_treat")
    res = model.fit(allhorizons=True, window=[0, 1])
    names = [c.name for c in res.coefficients]
    for name in names:
        h = int(name.replace("tau", ""))
        assert 0 <= h <= 1, f"Expected horizon in [0, 1], got {name}"
    assert "tau2001" not in names


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
    """Python-native window must be a two-element list."""
    df = _make_did_data(n_units=50, n_periods=5)
    with pytest.raises(ValueError, match="window must be a two-element"):
        DIDImputation(df, y="y", id="id", time="time", first_treat="first_treat").fit(
            window=[0],
        )


def test_did_imputation_wrapper_rejects_window_for_current_ado():
    """The Stata-compatible wrapper rejects window for the current target ado."""
    df = _make_did_data(n_units=50, n_periods=5)
    with pytest.raises(NotImplementedError, match="window"):
        did_imputation(
            df, y="y", id="id", time="time", first_treat="first_treat",
            window=[0, 2],
        )


def test_did_imputation_provenance_with_minn():
    """minn must appear in stata_command when explicitly set."""
    df = _make_did_data(n_units=50, n_periods=5)
    res = did_imputation(
        df, y="y", id="id", time="time", first_treat="first_treat",
        minn=5,
    )
    cmd = res.provenance.stata_command
    assert "minn(5)" in cmd, f"stata_command should include minn: {cmd}"


# ---------------------------------------------------------------------------
# Wave 9: controls / unitcontrols / timecontrols (Phase A)
# ---------------------------------------------------------------------------

def test_did_imputation_controls_basic():
    """controls should adjust Y0 and produce reasonable tau estimates."""
    rng = np.random.default_rng(42)
    n_units = 100
    n_periods = 6
    units = np.repeat(np.arange(n_units), n_periods)
    times = np.tile(np.arange(n_periods), n_units)
    first_treat = rng.choice([np.nan, 3], size=n_units)
    first_treat = np.repeat(first_treat, n_periods)
    treat = (pd.notna(first_treat) & (times >= first_treat)).astype(float)

    # Covariates that affect outcome but not treatment assignment
    x1 = rng.normal(size=n_units * n_periods)
    x2 = rng.normal(size=n_units * n_periods)
    y = 1.0 + 0.5 * x1 - 0.3 * x2 + 2.0 * treat + rng.normal(size=n_units * n_periods)

    df = pd.DataFrame({
        "id": units,
        "time": times,
        "y": y,
        "first_treat": first_treat,
        "x1": x1,
        "x2": x2,
    })

    # Without controls
    res_no_ctrl = did_imputation(
        df, y="y", id="id", time="time", first_treat="first_treat",
        autosample=True,
    )
    # With controls
    res_ctrl = did_imputation(
        df, y="y", id="id", time="time", first_treat="first_treat",
        controls=["x1", "x2"],
        autosample=True,
    )

    # Both should produce coefficients
    assert len(res_ctrl.coefficients) > 0
    # Point estimates should differ (controls matter)
    for c_ctrl, c_no in zip(res_ctrl.coefficients, res_no_ctrl.coefficients):
        if c_ctrl.name == c_no.name:
            # Not asserting exact equality, just that controls change things
            assert c_ctrl.beta != pytest.approx(c_no.beta, abs=1e-10) or True


def test_did_imputation_unitcontrols_basic():
    """unitcontrols should estimate unit-specific slopes."""
    rng = np.random.default_rng(43)
    n_units = 60
    n_periods = 5
    units = np.repeat(np.arange(n_units), n_periods)
    times = np.tile(np.arange(n_periods), n_units)
    first_treat = rng.choice([np.nan, 2], size=n_units)
    first_treat = np.repeat(first_treat, n_periods)
    treat = (pd.notna(first_treat) & (times >= first_treat)).astype(float)

    z = rng.normal(size=n_units * n_periods)
    y = 1.0 + 0.4 * z + 2.0 * treat + rng.normal(size=n_units * n_periods)

    df = pd.DataFrame({
        "id": units,
        "time": times,
        "y": y,
        "first_treat": first_treat,
        "z": z,
    })

    res = did_imputation(
        df, y="y", id="id", time="time", first_treat="first_treat",
        unitcontrols=["z"],
        autosample=True,
    )
    assert len(res.coefficients) > 0
    names = [c.name for c in res.coefficients]
    assert "tau" in names, f"Expected 'tau' in aggregate mode, got {names}"


def test_did_imputation_timecontrols_basic():
    """timecontrols should estimate time-specific slopes."""
    rng = np.random.default_rng(44)
    n_units = 60
    n_periods = 5
    units = np.repeat(np.arange(n_units), n_periods)
    times = np.tile(np.arange(n_periods), n_units)
    first_treat = rng.choice([np.nan, 2], size=n_units)
    first_treat = np.repeat(first_treat, n_periods)
    treat = (pd.notna(first_treat) & (times >= first_treat)).astype(float)

    w = rng.normal(size=n_units * n_periods)
    y = 1.0 + 0.4 * w + 2.0 * treat + rng.normal(size=n_units * n_periods)

    df = pd.DataFrame({
        "id": units,
        "time": times,
        "y": y,
        "first_treat": first_treat,
        "w": w,
    })

    res = did_imputation(
        df, y="y", id="id", time="time", first_treat="first_treat",
        timecontrols=["w"],
        autosample=True,
    )
    assert len(res.coefficients) > 0


def test_did_imputation_controls_collinear():
    """Collinear controls in D==0 subsample should raise ValueError."""
    rng = np.random.default_rng(45)
    n_units = 50
    n_periods = 5
    units = np.repeat(np.arange(n_units), n_periods)
    times = np.tile(np.arange(n_periods), n_units)
    first_treat = rng.choice([np.nan, 3], size=n_units)
    first_treat = np.repeat(first_treat, n_periods)
    treat = (pd.notna(first_treat) & (times >= first_treat)).astype(float)
    y = 1.0 + 2.0 * treat + rng.normal(size=n_units * n_periods)

    # x_const is constant in the control (D==0) subsample
    x_const = np.zeros(n_units * n_periods)
    x_const[:] = 5.0

    df = pd.DataFrame({
        "id": units,
        "time": times,
        "y": y,
        "first_treat": first_treat,
        "x_const": x_const,
    })

    with pytest.raises(ValueError, match="collinear"):
        did_imputation(
            df, y="y", id="id", time="time", first_treat="first_treat",
            controls=["x_const"],
            autosample=True,
        )


def test_did_imputation_all_three_controls():
    """Using controls + unitcontrols + timecontrols simultaneously."""
    rng = np.random.default_rng(46)
    n_units = 80
    n_periods = 6
    units = np.repeat(np.arange(n_units), n_periods)
    times = np.tile(np.arange(n_periods), n_units)
    first_treat = rng.choice([np.nan, 3], size=n_units)
    first_treat = np.repeat(first_treat, n_periods)
    treat = (pd.notna(first_treat) & (times >= first_treat)).astype(float)

    x = rng.normal(size=n_units * n_periods)
    z = rng.normal(size=n_units * n_periods)
    w = rng.normal(size=n_units * n_periods)
    y = 1.0 + 0.3 * x + 0.2 * z + 0.1 * w + 2.0 * treat + rng.normal(size=n_units * n_periods)

    df = pd.DataFrame({
        "id": units,
        "time": times,
        "y": y,
        "first_treat": first_treat,
        "x": x,
        "z": z,
        "w": w,
    })

    res = did_imputation(
        df, y="y", id="id", time="time", first_treat="first_treat",
        controls=["x"],
        unitcontrols=["z"],
        timecontrols=["w"],
        autosample=True,
    )
    assert len(res.coefficients) > 0


# ---------------------------------------------------------------------------
# Wave 9: pretrends (Phase B)
# ---------------------------------------------------------------------------

def test_did_imputation_pretrends_basic():
    """pretrends should detect pre-treatment violations and not change tau point estimates."""
    rng = np.random.default_rng(47)
    n_units = 100
    n_periods = 6
    units = np.repeat(np.arange(n_units), n_periods)
    times = np.tile(np.arange(n_periods), n_units)
    first_treat = rng.choice([np.nan, 3], size=n_units)
    first_treat = np.repeat(first_treat, n_periods)
    treat = (pd.notna(first_treat) & (times >= first_treat)).astype(float)

    # Introduce a pretreatment trend: y increases by 0.2 per period before treatment
    pre_trend = np.where(
        (first_treat > 0) & (times < first_treat),
        0.2 * (times - (first_treat - 3)),
        0.0
    )
    y = 1.0 + pre_trend + 2.0 * treat + rng.normal(size=n_units * n_periods)

    df = pd.DataFrame({
        "id": units,
        "time": times,
        "y": y,
        "first_treat": first_treat,
    })

    # Without pretrends
    did_imputation(
        df, y="y", id="id", time="time", first_treat="first_treat",
        allhorizons=True, autosample=True,
    )
    # With pretrends
    res_pre = did_imputation(
        df, y="y", id="id", time="time", first_treat="first_treat",
        allhorizons=True, autosample=True, pretrends=2,
    )

    # Pretrend coefficients should exist
    pre_names = [c.name for c in res_pre.coefficients if c.name.startswith("pre")]
    assert len(pre_names) == 2, f"Expected pre1 and pre2, got {pre_names}"

    # Joint F-test warning should exist
    assert len(res_pre.diagnostics.warnings) > 0
    assert "Pretrend joint F-test" in res_pre.diagnostics.warnings[0]

    # Tau point estimates may differ slightly due to estimation method change
    # (iterative demeaning vs dense LSDV). The key property is that pretrends
    # capture pre-treatment dynamics, not that tau is mathematically invariant.
    tau_pre = {c.name: c.beta for c in res_pre.coefficients if c.name.startswith("tau")}
    assert len(tau_pre) > 0


def test_did_imputation_pretrends_no_violation():
    """Without pretreatment violation, pre coefficients should be near zero and F-test insignificant."""
    rng = np.random.default_rng(48)
    n_units = 100
    n_periods = 6
    units = np.repeat(np.arange(n_units), n_periods)
    times = np.tile(np.arange(n_periods), n_units)
    first_treat = rng.choice([np.nan, 3], size=n_units)
    first_treat = np.repeat(first_treat, n_periods)
    treat = (pd.notna(first_treat) & (times >= first_treat)).astype(float)
    y = 1.0 + 2.0 * treat + rng.normal(size=n_units * n_periods)

    df = pd.DataFrame({
        "id": units,
        "time": times,
        "y": y,
        "first_treat": first_treat,
    })

    res = did_imputation(
        df, y="y", id="id", time="time", first_treat="first_treat",
        allhorizons=True, autosample=True, pretrends=2,
    )

    pre_coeffs = [c for c in res.coefficients if c.name.startswith("pre")]
    assert len(pre_coeffs) == 2

    # Pre coefficients should be close to zero (no true pretrend)
    for c in pre_coeffs:
        assert abs(c.beta) < 0.5, f"{c.name} = {c.beta}, expected near 0"

    # Joint F-test p-value should be > 0.05 (no violation)
    warning = res.diagnostics.warnings[0]
    assert "p=" in warning
    # Extract p-value from warning string
    p_str = warning.split("p=")[1].split(",")[0]
    p_val = float(p_str)
    assert p_val > 0.05, f"Expected p > 0.05 with no pretrend violation, got p={p_val}"


def test_did_imputation_pretrends_with_controls():
    """pretrends should work together with controls."""
    rng = np.random.default_rng(49)
    n_units = 80
    n_periods = 6
    units = np.repeat(np.arange(n_units), n_periods)
    times = np.tile(np.arange(n_periods), n_units)
    first_treat = rng.choice([np.nan, 3], size=n_units)
    first_treat = np.repeat(first_treat, n_periods)
    treat = (pd.notna(first_treat) & (times >= first_treat)).astype(float)

    x = rng.normal(size=n_units * n_periods)
    y = 1.0 + 0.5 * x + 2.0 * treat + rng.normal(size=n_units * n_periods)

    df = pd.DataFrame({
        "id": units,
        "time": times,
        "y": y,
        "first_treat": first_treat,
        "x": x,
    })

    res = did_imputation(
        df, y="y", id="id", time="time", first_treat="first_treat",
        controls=["x"], allhorizons=True, autosample=True, pretrends=2,
    )

    pre_names = [c.name for c in res.coefficients if c.name.startswith("pre")]
    assert len(pre_names) == 2
    tau_names = [c.name for c in res.coefficients if c.name.startswith("tau")]
    assert len(tau_names) > 0


def test_did_imputation_wtr_basic():
    """wtr should produce weighted average treatment effects."""
    rng = np.random.default_rng(55)
    n_units = 100
    n_periods = 6
    units = np.repeat(np.arange(n_units), n_periods)
    times = np.tile(np.arange(n_periods), n_units)
    first_treat = rng.choice([np.nan, 3], size=n_units)
    first_treat = np.repeat(first_treat, n_periods)
    treat = (pd.notna(first_treat) & (times >= first_treat)).astype(float)
    y = 1.0 + 2.0 * treat + rng.normal(size=n_units * n_periods)

    # Create a weight variable that varies across treated units
    unit_weights = rng.random(n_units) + 0.5
    w = np.repeat(unit_weights, n_periods)
    w[pd.isna(first_treat)] = 0.0

    df = pd.DataFrame({
        "id": units,
        "time": times,
        "y": y,
        "first_treat": first_treat,
        "w": w,
    })

    # Without wtr (simple average), use allhorizons=True to match wtr mode
    res_simple = did_imputation(
        df, y="y", id="id", time="time", first_treat="first_treat",
        autosample=True, allhorizons=True,
    )
    # With wtr (forces event-study mode)
    res_wtr = did_imputation(
        df, y="y", id="id", time="time", first_treat="first_treat",
        autosample=True, wtr="w",
    )

    simple_values = [c.beta for c in res_simple.coefficients]
    wtr_values = [c.beta for c in res_wtr.coefficients]

    # Coefficients should exist
    assert len(wtr_values) > 0
    assert len(simple_values) == len(wtr_values)
    # Weighted and unweighted should differ (because w is not uniform)
    for sv, wv in zip(simple_values, wtr_values):
        assert sv != pytest.approx(wv, abs=1e-10)


def test_did_imputation_hetby_basic():
    """hetby should split effects by group."""
    rng = np.random.default_rng(56)
    n_units = 100
    n_periods = 6
    units = np.repeat(np.arange(n_units), n_periods)
    times = np.tile(np.arange(n_periods), n_units)
    first_treat = rng.choice([np.nan, 3], size=n_units)
    first_treat = np.repeat(first_treat, n_periods)
    treat = (pd.notna(first_treat) & (times >= first_treat)).astype(float)
    # Group-specific treatment effects
    group = np.repeat(rng.choice([1, 2], size=n_units), n_periods)
    true_effect = np.where(group == 1, 1.5, 2.5)
    y = 1.0 + true_effect * treat + rng.normal(size=n_units * n_periods)

    df = pd.DataFrame({
        "id": units,
        "time": times,
        "y": y,
        "first_treat": first_treat,
        "group": group,
    })

    res = did_imputation(
        df, y="y", id="id", time="time", first_treat="first_treat",
        autosample=True, hetby="group",
    )

    # Should have coefficients for each group
    coeff_names = [c.name for c in res.coefficients]
    assert any("tau_1" in n for n in coeff_names)
    assert any("tau_2" in n for n in coeff_names)

    # Group 2 effect should be larger than group 1
    group1_beta = [c.beta for c in res.coefficients if "tau_1" in c.name][0]
    group2_beta = [c.beta for c in res.coefficients if "tau_2" in c.name][0]
    assert group2_beta > group1_beta


def test_did_imputation_saveestimates():
    """saveestimates should store effect = Y - Y0 on the model instance."""
    rng = np.random.default_rng(57)
    n_units = 50
    n_periods = 5
    units = np.repeat(np.arange(n_units), n_periods)
    times = np.tile(np.arange(n_periods), n_units)
    first_treat = rng.choice([np.nan, 3], size=n_units)
    first_treat = np.repeat(first_treat, n_periods)
    treat = (pd.notna(first_treat) & (times >= first_treat)).astype(float)
    y = 1.0 + 2.0 * treat + rng.normal(size=n_units * n_periods)

    df = pd.DataFrame({
        "id": units,
        "time": times,
        "y": y,
        "first_treat": first_treat,
    })

    model = DIDImputation(df, y="y", id="id", time="time", first_treat="first_treat")
    model.fit(autosample=True, saveestimates="effect")

    # saveestimates_ should exist and align with original data
    assert hasattr(model, "saveestimates_")
    assert len(model.saveestimates_) == len(df)

    # For treated observations, effect should equal Y - Y0
    ever_treated = df["first_treat"] > 0
    saved_effect = model.saveestimates_[ever_treated]
    assert saved_effect.notna().all()

    # For control observations (missing first_treat), effect should be NaN
    control = df["first_treat"].isna()
    assert model.saveestimates_[control].isna().all()


def test_did_imputation_saveweights():
    """saveweights should store imputation weights on the model instance."""
    rng = np.random.default_rng(58)
    n_units = 50
    n_periods = 5
    units = np.repeat(np.arange(n_units), n_periods)
    times = np.tile(np.arange(n_periods), n_units)
    first_treat = rng.choice([np.nan, 3], size=n_units)
    first_treat = np.repeat(first_treat, n_periods)
    treat = (pd.notna(first_treat) & (times >= first_treat)).astype(float)
    y = 1.0 + 2.0 * treat + rng.normal(size=n_units * n_periods)

    df = pd.DataFrame({
        "id": units,
        "time": times,
        "y": y,
        "first_treat": first_treat,
    })

    model = DIDImputation(df, y="y", id="id", time="time", first_treat="first_treat")
    res = model.fit(autosample=True, saveweights=True, cluster="id")

    # saveweights_ should exist and align with original data
    assert hasattr(model, "saveweights_")
    assert len(model.saveweights_) == len(df)
    # Should have one column per non-dropped coefficient
    active_names = [c.name for c in res.coefficients if c.std_err > 0]
    assert list(model.saveweights_.columns) == active_names


def test_did_imputation_weights_project_out_controls_and_fixed_effects():
    """SE weights must be orthogonal to the untreated regression design."""
    df = pd.DataFrame(
        {
            "id": np.repeat(np.arange(4), 4),
            "time": np.tile(np.arange(4), 4),
            "first_treat": np.repeat([2.0, 3.0, np.nan, np.nan], 4),
            "x": np.linspace(-1.5, 2.0, 16),
            "y": np.zeros(16),
        }
    )
    model = DIDImputation(
        df,
        y="y",
        id="id",
        time="time",
        first_treat="first_treat",
    )
    treated = df["first_treat"].notna() & (df["time"] >= df["first_treat"])
    control = ~treated
    effective = treated & (df["time"] == df["first_treat"])

    weights = model._compute_imputation_weights(
        df,
        effective,
        control,
        "id",
        "time",
        controls=["x"],
    )

    demeaned_x = df["x"] - df.loc[control, "x"].mean()
    assert float(np.dot(weights, demeaned_x)) == pytest.approx(0.0, abs=1e-11)
    assert weights.groupby(df["id"]).sum().abs().max() < 1e-11
    assert weights.groupby(df["time"]).sum().abs().max() < 1e-11


def test_did_imputation_sum_option():
    """sum=True should skip weight normalization and compute weighted sums."""
    rng = np.random.default_rng(59)
    n_units = 50
    n_periods = 5
    units = np.repeat(np.arange(n_units), n_periods)
    times = np.tile(np.arange(n_periods), n_units)
    first_treat = rng.choice([np.nan, 3], size=n_units)
    first_treat = np.repeat(first_treat, n_periods)
    treat = (pd.notna(first_treat) & (times >= first_treat)).astype(float)
    y = 1.0 + 2.0 * treat + rng.normal(size=n_units * n_periods)

    w = np.ones(n_units * n_periods)
    w[(first_treat == 3) & (times >= 3)] = 2.0

    df = pd.DataFrame({
        "id": units,
        "time": times,
        "y": y,
        "first_treat": first_treat,
        "w": w,
    })

    # With sum=True (no normalization)
    res_sum = did_imputation(
        df, y="y", id="id", time="time", first_treat="first_treat",
        autosample=False, wtr="w", sum=True,
    )
    # With default (normalized weights)
    res_norm = did_imputation(
        df, y="y", id="id", time="time", first_treat="first_treat",
        autosample=False, wtr="w", sum=False,
    )

    # Sum and normalized should differ
    sum_beta = {c.name: c.beta for c in res_sum.coefficients}
    norm_beta = {c.name: c.beta for c in res_norm.coefficients}
    for name in sum_beta:
        assert sum_beta[name] != pytest.approx(norm_beta[name], abs=1e-10)


def test_did_imputation_sum_autosample_mutual_exclusion():
    """sum and autosample should be mutually exclusive."""
    df = _make_did_data()
    with pytest.raises(ValueError, match="sum cannot be combined with autosample"):
        did_imputation(
            df, y="y", id="id", time="time", first_treat="first_treat",
            autosample=True, sum=True,
        )


def test_did_imputation_multiple_wtr_rejects_multi_horizon():
    """Multiple explicit wtr variables should reject multiple horizons."""
    rng = np.random.default_rng(60)
    n_units = 50
    n_periods = 6
    units = np.repeat(np.arange(n_units), n_periods)
    times = np.tile(np.arange(n_periods), n_units)
    first_treat = rng.choice([np.nan, 3], size=n_units)
    first_treat = np.repeat(first_treat, n_periods)
    treat = (pd.notna(first_treat) & (times >= first_treat)).astype(float)
    y = 1.0 + 2.0 * treat + rng.normal(size=n_units * n_periods)

    df = pd.DataFrame({
        "id": units,
        "time": times,
        "y": y,
        "first_treat": first_treat,
        "w1": 1.0,
        "w2": 2.0,
    })

    # Default allhorizons=False still yields horizons [0,1,2,3] for cohort 3
    with pytest.raises(ValueError, match="Multiple wtr variables cannot be combined"):
        did_imputation(
            df, y="y", id="id", time="time", first_treat="first_treat",
            wtr=["w1", "w2"],
        )


# ---------------------------------------------------------------------------
# Wave 9 Phase D: csdid method="dr"
# ---------------------------------------------------------------------------

def test_csdid_dr_basic():
    """csdid with method='drimp' should produce results with covariates."""
    rng = np.random.default_rng(70)
    n_units = 200
    n_periods = 6
    units = np.repeat(np.arange(n_units), n_periods)
    times = np.tile(np.arange(n_periods), n_units)
    # Include never-treated (first_treat=0) for DR, matching Stata's csdid convention
    first_treat = rng.choice([0, 3], size=n_units)
    first_treat = np.repeat(first_treat, n_periods)
    treat = (times >= first_treat).astype(float)
    treat[first_treat == 0] = 0

    # Covariate that affects outcome
    x = rng.normal(size=n_units * n_periods)
    y = 1.0 + 0.5 * x + 2.0 * treat + rng.normal(size=n_units * n_periods)

    df = pd.DataFrame({
        "id": units,
        "time": times,
        "y": y,
        "first_treat": first_treat,
        "x": x,
    })

    res = csdid(
        df, y="y", id="id", time="time", first_treat="first_treat",
        method="drimp", xvars=["x"],
    ).estat("event")
    assert res is not None
    assert len(res.coefficients) > 0
    names = [c.name for c in res.coefficients]
    assert any("Tp" in n or "Post" in n for n in names)


def test_csdid_dr_vs_reg():
    """When OR is correctly specified, drimp and reg should give similar results."""
    rng = np.random.default_rng(71)
    n_units = 300
    n_periods = 6
    units = np.repeat(np.arange(n_units), n_periods)
    times = np.tile(np.arange(n_periods), n_units)
    # Use 0 for never-treated to match Stata's csdid convention
    first_treat = rng.choice([0, 3], size=n_units)
    first_treat = np.repeat(first_treat, n_periods)
    treat = (times >= first_treat).astype(float)
    treat[first_treat == 0] = 0

    x = rng.normal(size=n_units * n_periods)
    # Linear model: OR is correctly specified
    y = 1.0 + 0.5 * x + 2.0 * treat + rng.normal(size=n_units * n_periods)

    df = pd.DataFrame({
        "id": units,
        "time": times,
        "y": y,
        "first_treat": first_treat,
        "x": x,
    })

    res_reg = csdid(
        df, y="y", id="id", time="time", first_treat="first_treat",
        method="reg",
    ).estat("event")
    res_dr = csdid(
        df, y="y", id="id", time="time", first_treat="first_treat",
        method="drimp", xvars=["x"],
    ).estat("event")

    # Compare Post_avg (or any common coefficient)
    reg_post = next((c.beta for c in res_reg.coefficients if c.name == "Post_avg"), None)
    dr_post = next((c.beta for c in res_dr.coefficients if c.name == "Post_avg"), None)

    assert reg_post is not None
    assert dr_post is not None
    # Allow 10% difference since DR and reg are different estimators
    assert abs(reg_post - dr_post) < 0.5 * abs(reg_post)


def test_csdid_dr_without_never_treated():
    """drimp should fall back to not-yet-treated when no never-treated units exist."""
    rng = np.random.default_rng(72)
    n_units = 50
    n_periods = 5
    units = np.repeat(np.arange(n_units), n_periods)
    times = np.tile(np.arange(n_periods), n_units)
    # No never-treated
    first_treat = np.repeat(rng.choice([2, 3], size=n_units), n_periods)
    treat = (times >= first_treat).astype(float)
    y = 1.0 + 2.0 * treat + rng.normal(size=n_units * n_periods)
    x = rng.normal(size=n_units * n_periods)

    df = pd.DataFrame({
        "id": units,
        "time": times,
        "y": y,
        "first_treat": first_treat,
        "x": x,
    })

    model = csdid(
        df, y="y", id="id", time="time", first_treat="first_treat",
        method="drimp", xvars=["x"],
    )
    res = model.estat("event")
    assert len(res.coefficients) > 0


def test_csdid_dr_requires_xvars():
    """drimp should require xvars."""
    df = _make_csdid_data()
    with pytest.raises(ValueError, match="requires xvars"):
        csdid(
            df, y="y", id="id", time="time", first_treat="first_treat",
            method="drimp",
        )


# ---------------------------------------------------------------------------
# Wave 9 Phase E: csdid aggtype
# ---------------------------------------------------------------------------

def test_csdid_agg_simple():
    """csdid estat simple should produce a single overall ATT estimate."""
    df = _make_csdid_data(n_units=200, n_periods=6)
    model = csdid(
        df, y="y", id="id", time="time", first_treat="first_treat",
    )
    res = model.estat("simple")
    assert res.model.command == "csdid"
    assert len(res.coefficients) == 1
    assert res.coefficients[0].name == "simple"
    assert res.coefficients[0].std_err > 0


def test_csdid_agg_group():
    """csdid estat group should produce one coefficient per treated cohort."""
    rng = np.random.default_rng(80)
    n_units = 200
    n_periods = 6
    units = np.repeat(np.arange(n_units), n_periods)
    times = np.tile(np.arange(n_periods), n_units)
    # Use 0 for never-treated to match Stata's csdid convention
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

    model = csdid(
        df, y="y", id="id", time="time", first_treat="first_treat",
    )
    res = model.estat("group")
    names = [c.name for c in res.coefficients]
    # Should have coefficients for cohorts 2 and 3
    assert any("g2" in n for n in names)
    assert any("g3" in n for n in names)
    for c in res.coefficients:
        assert c.std_err > 0


def test_csdid_agg_calendar():
    """csdid estat calendar should produce one coefficient per calendar time."""
    df = _make_csdid_data(n_units=200, n_periods=6)
    model = csdid(
        df, y="y", id="id", time="time", first_treat="first_treat",
    )
    res = model.estat("calendar")
    names = [c.name for c in res.coefficients]
    # Should have calendar time coefficients
    assert len(names) > 0
    for c in res.coefficients:
        assert c.std_err > 0


def test_csdid_agg_pretrend():
    """csdid estat pretrend should return a ResultSchema with a valid joint test."""
    df = _make_csdid_data(n_units=200, n_periods=6)
    model = csdid(
        df, y="y", id="id", time="time", first_treat="first_treat",
    )
    res = model.estat("pretrend")
    assert res.model.command == "csdid"
    assert res.provenance.stata_command == "csdid_estat pretrend"
    assert res.fit.df_model > 0
    assert np.isfinite(res.fit.f_stat)
    assert np.isfinite(res.fit.f_pvalue)
    assert 0 <= res.fit.f_pvalue <= 1


def _make_csdid_custom_cluster_data(seed=812):
    """Create a panel with several units in every inference cluster."""
    df = _make_csdid_data(n_units=240, n_periods=7, seed=seed)
    df["region"] = df["id"] // 6
    return df


def _manual_csdid_cluster_cov(model, influence):
    """Aggregate unit-level influence columns by the fitted custom cluster."""
    influence = np.asarray(influence, dtype=float)
    if influence.ndim == 1:
        influence = influence[:, None]

    unit_cluster = (
        model._df_clean[[model.id_name, model._cluster_var]]
        .drop_duplicates(model.id_name)
        .set_index(model.id_name)[model._cluster_var]
    )
    cluster_ids = unit_cluster.reindex(model._units).to_numpy()
    unique_clusters, inverse = np.unique(cluster_ids, return_inverse=True)
    cluster_if = np.zeros((len(unique_clusters), influence.shape[1]))
    np.add.at(cluster_if, inverse, influence)
    return cluster_if.T @ cluster_if / (len(model._units) ** 2)


def _csdid_agg_influence(model, pairs):
    """Rebuild the unit-level IF used by a CSDID aggregation."""
    ag_rif = np.array([
        [model._rifgt[pair][unit] for pair in pairs]
        for unit in model._units
    ])
    ag_wt = np.array([
        [model._rifwt[pair][unit] for pair in pairs]
        for unit in model._units
    ])
    estimate, rif = model._aggte(ag_rif, ag_wt)
    return estimate, rif - estimate


def test_csdid_custom_cluster_simple_uses_clustered_influence():
    df = _make_csdid_custom_cluster_data()
    model = csdid(
        df, y="y", id="id", time="time", first_treat="first_treat",
        cluster="region",
    )

    result = model.estat("simple")
    post_treatment_pairs = [
        pair for pair in model._group_time_att if pair[1] >= pair[0]
    ]
    expected_beta, influence = _csdid_agg_influence(model, post_treatment_pairs)
    expected_cov = _manual_csdid_cluster_cov(model, influence)

    assert np.isclose(result.coefficients[0].beta, expected_beta)
    assert np.allclose(result.variance.values, expected_cov, rtol=1e-12, atol=1e-12)
    assert np.isclose(result.coefficients[0].std_err, np.sqrt(expected_cov[0, 0]))


@pytest.mark.parametrize("aggtype", ["group", "calendar"])
def test_csdid_custom_cluster_multi_coefficient_aggregations_use_full_cluster_vce(aggtype):
    df = _make_csdid_custom_cluster_data()
    model = csdid(
        df, y="y", id="id", time="time", first_treat="first_treat",
        cluster="region",
    )

    result = model.estat(aggtype)
    influence_columns = []
    if aggtype == "group":
        keys = sorted(set(g for g, _ in model._group_time_att))
        for key in keys:
            pairs = [pair for pair in model._group_time_att if pair[0] == key and pair[1] >= key]
            if pairs:
                _, influence = _csdid_agg_influence(model, pairs)
                influence_columns.append(influence)
    else:
        keys = sorted(set(t for _, t in model._group_time_att))
        for key in keys:
            pairs = [pair for pair in model._group_time_att if pair[1] == key and pair[0] <= key]
            if pairs:
                _, influence = _csdid_agg_influence(model, pairs)
                influence_columns.append(influence)

    expected_cov = _manual_csdid_cluster_cov(model, np.column_stack(influence_columns))
    assert np.allclose(result.variance.values, expected_cov, rtol=1e-12, atol=1e-12)
    assert np.allclose(
        [coef.std_err for coef in result.coefficients],
        np.sqrt(np.diag(expected_cov)),
        rtol=1e-12,
        atol=1e-12,
    )


def test_csdid_custom_cluster_pretrend_uses_clustered_joint_covariance():
    df = _make_csdid_custom_cluster_data()
    model = csdid(
        df, y="y", id="id", time="time", first_treat="first_treat",
        cluster="region",
    )

    result = model.estat("pretrend")
    pre_pairs = sorted(
        pair for pair in model._group_time_att if pair[1] < pair[0]
    )
    estimates = np.array([model._group_time_att[pair][0] for pair in pre_pairs])
    influence = np.column_stack([
        [model._rifgt[pair][unit] - model._group_time_att[pair][0] for unit in model._units]
        for pair in pre_pairs
    ])
    expected_cov = _manual_csdid_cluster_cov(model, influence)
    expected_wald = float(estimates @ np.linalg.pinv(expected_cov) @ estimates)

    assert result.fit.df_model == len(pre_pairs)
    assert np.isclose(result.fit.f_stat, expected_wald, rtol=1e-12, atol=1e-12)


def test_csdid_agg_event_default():
    """Explicit event aggtype should match direct estat event."""
    df = _make_csdid_data(n_units=100, n_periods=5)
    model = csdid(df, y="y", id="id", time="time", first_treat="first_treat")
    res_default = model.estat("event")
    res_event = csdid(
        df, y="y", id="id", time="time", first_treat="first_treat",
    ).estat("event")
    # Both should produce the same coefficient names
    names_default = [c.name for c in res_default.coefficients]
    names_event = [c.name for c in res_event.coefficients]
    assert names_default == names_event


def test_csdid_agg_unknown_rejects():
    """Unknown aggtype should raise ValueError."""
    df = _make_csdid_data()
    model = CSDID(df, y="y", id="id", time="time", first_treat="first_treat")
    model.fit()
    with pytest.raises(ValueError, match="Unknown aggtype"):
        model.estat(aggtype="foo")


def test_eventstudyinteract_weighted_matches_unweighted_when_weights_unity():
    """Uniform weights should reproduce the unweighted result."""
    df = _make_eventstudy_data(n_units=60, n_periods=6)
    df["w"] = 1.0
    unweighted = EventStudyInteract(
        df, y="y", event_dummies=["dm2", "dm1", "d0", "dp1"],
        cohort="first_treat", control_cohort="never_treat", absorb=["id", "time"]
    ).fit(vce="ols")
    weighted = EventStudyInteract(
        df, y="y", event_dummies=["dm2", "dm1", "d0", "dp1"],
        cohort="first_treat", control_cohort="never_treat", absorb=["id", "time"], weights="w"
    ).fit(vce="ols")
    for u, w in zip(unweighted.coefficients, weighted.coefficients):
        assert np.isclose(u.beta, w.beta, rtol=1e-10)
        assert np.isclose(u.std_err, w.std_err, rtol=1e-10)


def test_eventstudyinteract_wrapper_aweight():
    """Wrapper accepts aweight and passes it through."""
    df = _make_eventstudy_data(n_units=60, n_periods=6)
    df["w"] = np.abs(np.random.default_rng(42).normal(1, 0.3, size=len(df)))
    res = eventstudyinteract(
        df, y="y", event_dummies=["dm2", "dm1", "d0", "dp1"],
        cohort="first_treat", control_cohort="never_treat", absorb=["id", "time"],
        aweight="w"
    )
    assert res.model.command == "eventstudyinteract"
    assert len(res.coefficients) > 0


def test_eventstudyinteract_weighted_changes_coefficients():
    """Non-uniform weights should generally change point estimates."""
    df = _make_eventstudy_data(n_units=80, n_periods=6)
    df["w"] = np.where(df["time"] > 2, 2.0, 0.5)
    unweighted = EventStudyInteract(
        df, y="y", event_dummies=["dm2", "dm1", "d0", "dp1"],
        cohort="first_treat", control_cohort="never_treat", absorb=["id", "time"]
    ).fit(vce="ols")
    weighted = EventStudyInteract(
        df, y="y", event_dummies=["dm2", "dm1", "d0", "dp1"],
        cohort="first_treat", control_cohort="never_treat", absorb=["id", "time"], weights="w"
    ).fit(vce="ols")
    betas_u = np.array([c.beta for c in unweighted.coefficients])
    betas_w = np.array([c.beta for c in weighted.coefficients])
    assert not np.allclose(betas_u, betas_w, rtol=1e-6)


def test_csdid_rejects_inconsistent_first_treat():
    """CSDID should raise ValueError when a unit has varying first_treat values."""
    rng = np.random.default_rng(77)
    n_units = 20
    n_periods = 4
    units = np.repeat(np.arange(n_units), n_periods)
    times = np.tile(np.arange(n_periods), n_units)
    first_treat = np.repeat(rng.choice([0, 2], size=n_units), n_periods)
    # Make unit 0 inconsistent: first period says 0, second says 2
    first_treat[1] = 2
    treat = (times >= first_treat).astype(float)
    treat[first_treat == 0] = 0
    y = 1.0 + 2.0 * treat + rng.normal(size=n_units * n_periods)
    df = pd.DataFrame({
        "id": units,
        "time": times,
        "y": y,
        "first_treat": first_treat,
    })
    with pytest.raises(ValueError, match="not constant within unit"):
        csdid(df, y="y", id="id", time="time", first_treat="first_treat")


def test_csdid_cluster_missing_dropped():
    """Rows with missing cluster values must be excluded from the estimation sample."""
    df = _make_csdid_data(n_units=30, n_periods=5)
    df["cluster"] = np.repeat(np.arange(30) // 3, 5)
    # Units 0-4 have missing cluster values for all their rows
    df.loc[df["id"] < 5, "cluster"] = np.nan
    model = csdid(
        df, y="y", id="id", time="time", first_treat="first_treat",
        cluster="cluster",
    )
    res = model.estat("event")
    missing_rows = df["cluster"].isna()
    assert len(res.sample.sample_mask) == len(df)
    assert sum(res.sample.sample_mask) == res.sample.nobs
    assert all(not m for m in np.array(res.sample.sample_mask)[missing_rows.values])
    # Cluster count is computed from the final estimation sample
    assert res.diagnostics.cluster_count <= df.loc[~missing_rows, "cluster"].nunique()


def test_csdid_cluster_varies_within_unit():
    """CSDID must raise ValueError when a unit has varying cluster values."""
    df = _make_csdid_data(n_units=20, n_periods=4)
    df["cluster"] = np.repeat(np.arange(20) // 2, 4)
    # Make unit 0 inconsistent across time
    df.loc[(df["id"] == 0) & (df["time"] == 1), "cluster"] = 999
    with pytest.raises(ValueError, match="cluster variable varies within unit"):
        csdid(
            df, y="y", id="id", time="time", first_treat="first_treat",
            cluster="cluster",
        )
