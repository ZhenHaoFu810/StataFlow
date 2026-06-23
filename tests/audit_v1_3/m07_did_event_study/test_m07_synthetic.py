"""M07 synthetic dual-run tests (S1-S8) for DID / Event Study audit v1.3.

Design note: ``did_imputation`` (Borusyak et al. 2023) encodes never-treated
units as *missing* values of ``first_treat``.  Using ``first_treat=0`` for
never-treated units causes Stata to treat those units as treated in period 0,
which is not the intended comparison.  Therefore all ``did_imputation`` specs
below use synthetic panels with *no never-treated units* (every unit is in a
positive cohort), so Stata and Python are operating on the same control-group
definition.  S7 is kept as an xfail test that documents the encoding mismatch
when 0 / negative / missing values are used.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from stataflow import DIDImputation, EventStudyInteract, csdid
from tests.audit_v1_3.m07_did_event_study.m07_audit_utils import (
    did_imputation_stata_do,
    csdid_stata_do,
    eventstudyinteract_stata_do,
    run_stata_did,
    compare_python_to_stata,
    save_evidence,
)


def _make_panel(
    seed: int,
    n_units: int,
    n_periods: int,
    cohorts: list[int],
    att: float = 2.0,
    sigma: float = 0.5,
    controls: bool = False,
    pretrend: bool = False,
    include_never: bool = True,
) -> pd.DataFrame:
    """Generic staggered adoption panel.

    If ``include_never=False``, ``n_units`` must be divisible by
    ``len(cohorts)`` and every unit is assigned to one of the positive
    cohorts.  This avoids the ``did_imputation`` first_treat encoding
    discrepancy between Python (0/negative = never-treated) and Stata
    (missing = never-treated).
    """
    rng = np.random.default_rng(seed)
    ids = np.repeat(np.arange(1, n_units + 1), n_periods)
    times = np.tile(np.arange(1, n_periods + 1), n_units)
    n_cohorts = len(cohorts)

    if include_never:
        unit_cohorts = np.zeros(n_units, dtype=int)
        per = n_units // (n_cohorts + 1)
        for i, g in enumerate(cohorts):
            unit_cohorts[i * per : (i + 1) * per] = g
    else:
        if n_units % n_cohorts != 0:
            raise ValueError(
                f"n_units={n_units} must be divisible by n_cohorts={n_cohorts} "
                "when include_never=False"
            )
        per = n_units // n_cohorts
        unit_cohorts = np.zeros(n_units, dtype=int)
        for i, g in enumerate(cohorts):
            unit_cohorts[i * per : (i + 1) * per] = g

    first_treat = np.repeat(unit_cohorts, n_periods)
    treat = ((times >= first_treat) & (first_treat > 0)).astype(int)
    fe_i = np.repeat(rng.normal(0, 1, n_units), n_periods)
    fe_t = np.array([rng.normal(0, 1) for _ in range(n_periods)])[
        np.tile(np.arange(n_periods), n_units)
    ]
    y = fe_i + fe_t + att * treat + rng.normal(0, sigma, len(ids))
    df = pd.DataFrame({"id": ids, "time": times, "first_treat": first_treat, "y": y})
    if controls:
        x = rng.normal(0, 1, len(ids))
        y = y + 0.3 * x
        df["y"] = y
        df["x"] = x
    if pretrend:
        pre = np.where((times == first_treat - 1) & (first_treat > 0), 0.5, 0.0)
        df["y"] = y + pre
    return df


def _make_event_dummies(
    df: pd.DataFrame, horizons: list[int], omit: int = -1
) -> tuple[pd.DataFrame, list[str]]:
    """Generate relative-time dummies for EventStudyInteract."""
    df = df.copy()
    df["rel_time"] = np.where(
        df["first_treat"] > 0, df["time"] - df["first_treat"], np.nan
    )
    dummies = []
    for h in horizons:
        if h == omit:
            continue
        if h < 0:
            col = f"Dm{abs(h)}"
        elif h == 0:
            col = "D0"
        else:
            col = f"Dp{h}"
        df[col] = ((df["rel_time"] == h) & (df["first_treat"] > 0)).astype(float)
        df.loc[df["first_treat"] <= 0, col] = 0.0
        dummies.append(col)
    return df, dummies


def _make_s1_data(seed: int = 20260620) -> pd.DataFrame:
    """S1: basic staggered adoption, 60 units x 10 periods, no never-treated."""
    return _make_panel(
        seed=seed, n_units=60, n_periods=10, cohorts=[6, 8, 10], include_never=False
    )


def _make_s2_data(seed: int = 20260621) -> pd.DataFrame:
    """S2: longer panel for allhorizons, no never-treated.

    Cohort 11 is beyond the last observed period, so it acts as a
    never-treated control for the observed calendar years while avoiding the
    ``first_treat=0`` encoding mismatch between Python and Stata.
    """
    return _make_panel(
        seed=seed, n_units=60, n_periods=10, cohorts=[6, 8, 11], include_never=False
    )


def _make_s3_data(seed: int = 20260622) -> pd.DataFrame:
    """S3: controls + pretrends, no never-treated."""
    return _make_panel(
        seed=seed,
        n_units=60,
        n_periods=10,
        cohorts=[6, 8, 10],
        controls=True,
        pretrend=True,
        include_never=False,
    )


def _make_s6_data(seed: int = 20260625) -> pd.DataFrame:
    """S6: EventStudyInteract data with a real never-treated control group."""
    df = _make_panel(
        seed=seed, n_units=60, n_periods=10, cohorts=[6, 8], include_never=True
    )
    df, dummies = _make_event_dummies(df, horizons=[-2, -1, 0, 1, 2], omit=-1)
    df["never"] = (df["first_treat"] == 0).astype(int)
    return df, dummies


class TestM07S1DidImputationBasic:
    """S1: DID imputation basic staggered adoption (no never-treated)."""

    @pytest.fixture(scope="class")
    def data(self):
        return _make_s1_data()

    def test_s1(self, data):
        prefix = "S1_DIDIMP_BASIC"
        do = did_imputation_stata_do(
            "{dta}", "y", "id", "time", "first_treat",
            options="cluster(id) autosample minn(0)",
        )
        st = run_stata_did(data, prefix, do)
        py = DIDImputation(
            data=data, y="y", id="id", time="time", first_treat="first_treat"
        ).fit(cluster="id", autosample=True, minn=0)
        diffs = compare_python_to_stata(py, st, fields=["nobs", "n_clust"])
        save_evidence(prefix, py, st, diffs)
        assert diffs["passed"], "\n".join(diffs["messages"])


class TestM07S2DidImputationAllhorizonsWindow:
    """S2: DID imputation allhorizons + autosample (window() not supported by ado)."""

    @pytest.fixture(scope="class")
    def data(self):
        return _make_s2_data()

    def test_s2(self, data):
        prefix = "S2_DIDIMP_ALLHORIZONS_WINDOW"
        do = did_imputation_stata_do(
            "{dta}", "y", "id", "time", "first_treat",
            options="cluster(id) allhorizons autosample minn(0)",
        )
        st = run_stata_did(data, prefix, do)
        py = DIDImputation(
            data=data, y="y", id="id", time="time", first_treat="first_treat"
        ).fit(cluster="id", allhorizons=True, autosample=True, minn=0)
        diffs = compare_python_to_stata(py, st, fields=["nobs", "n_clust"])
        save_evidence(prefix, py, st, diffs)
        assert diffs["passed"], "\n".join(diffs["messages"])


class TestM07S3DidImputationControlsPretrends:
    """S3: DID imputation controls + pretrends."""

    @pytest.fixture(scope="class")
    def data(self):
        return _make_s3_data()

    def test_s3(self, data):
        prefix = "S3_DIDIMP_CONTROLS_PRETRENDS"
        do = did_imputation_stata_do(
            "{dta}", "y", "id", "time", "first_treat",
            options="cluster(id) controls(x) pretrends(2) autosample minn(0)",
        )
        st = run_stata_did(data, prefix, do)
        py = DIDImputation(
            data=data, y="y", id="id", time="time", first_treat="first_treat"
        ).fit(cluster="id", controls=["x"], pretrends=2, autosample=True, minn=0)
        diffs = compare_python_to_stata(py, st, fields=["nobs", "n_clust"])
        if py.diagnostics.warnings:
            diffs["messages"].append(
                f"Python pretrend warnings: {py.diagnostics.warnings}"
            )
        save_evidence(prefix, py, st, diffs)
        assert diffs["passed"], "\n".join(diffs["messages"])


class TestM07S4CsdidRegEvent:
    """S4: CSDID reg event aggregation (default never-treated controls)."""

    @pytest.fixture(scope="class")
    def data(self):
        # CSDID uses 0 for never-treated, so include the default never-treated group.
        return _make_panel(
            seed=20260623, n_units=60, n_periods=10, cohorts=[6, 8], include_never=True
        )

    def test_s4(self, data):
        prefix = "S4_CSDID_REG_EVENT"
        do = csdid_stata_do(
            "{dta}", "y", "id", "time", "first_treat",
            options="method(reg) vce(cluster id)", agg="event",
        )
        st = run_stata_did(data, prefix, do)
        model = csdid(
            data=data, y="y", id="id", time="time", first_treat="first_treat",
            method="reg", cluster="id",
        )
        py = model.estat_event()
        diffs = compare_python_to_stata(py, st, fields=["nobs"])
        save_evidence(prefix, py, st, diffs)
        assert diffs["passed"], "\n".join(diffs["messages"])


class TestM07S5CsdidNotyet:
    """S5: CSDID with not-yet-treated controls, no never-treated."""

    @pytest.fixture(scope="class")
    def data(self):
        df = _make_panel(
            seed=20260624, n_units=60, n_periods=10, cohorts=[6, 8], include_never=True
        )
        df = df[df["first_treat"] > 0].copy()
        return df

    def test_s5(self, data):
        prefix = "S5_CSDID_NOTYET"
        do = csdid_stata_do(
            "{dta}", "y", "id", "time", "first_treat",
            options="method(reg) vce(cluster id) notyet", agg="event",
        )
        st = run_stata_did(data, prefix, do)
        model = csdid(
            data=data, y="y", id="id", time="time", first_treat="first_treat",
            method="reg", cluster="id", notyet=True,
        )
        py = model.estat_event()
        diffs = compare_python_to_stata(py, st, fields=["nobs"])
        save_evidence(prefix, py, st, diffs)
        assert diffs["passed"], "\n".join(diffs["messages"])


class TestM07S6EventStudyInteract:
    """S6: EventStudyInteract Sun-Abraham."""

    @pytest.fixture(scope="class")
    def data(self):
        return _make_s6_data()

    def test_s6(self, data):
        df, dummies = data
        prefix = "S6_EVENTSTUDYINTERACT"
        do = eventstudyinteract_stata_do(
            "{dta}", "y", dummies, "first_treat", "never", ["id", "time"], "id"
        )
        st = run_stata_did(df, prefix, do)
        py = EventStudyInteract(
            data=df,
            y="y",
            event_dummies=dummies,
            cohort="first_treat",
            control_cohort="never",
            absorb=["id", "time"],
        ).fit(vce="cluster", cluster="id")
        diffs = compare_python_to_stata(py, st, fields=["nobs"])
        save_evidence(prefix, py, st, diffs)
        assert diffs["passed"], "\n".join(diffs["messages"])


class TestM07S7FirstTreatSemantics:
    """S7: first_treat semantics with 0, negative, and missing values.

    Missing denotes never-treated; finite zero and negative values are cohorts.
    """

    @pytest.fixture(scope="class")
    def data(self):
        df = _make_panel(
            seed=20260626, n_units=60, n_periods=10, cohorts=[6, 8], include_never=True
        )
        unit_ids = sorted(df["id"].unique())
        df.loc[df["id"] == unit_ids[0], "first_treat"] = 0
        df.loc[df["id"] == unit_ids[1], "first_treat"] = -1
        df.loc[df["id"] == unit_ids[2], "first_treat"] = np.nan
        return df

    def test_s7(self, data):
        prefix = "S7_FIRST_TREAT_SEMANTICS"
        do = did_imputation_stata_do(
            "{dta}", "y", "id", "time", "first_treat",
            options="cluster(id) autosample minn(0)",
        )
        st = run_stata_did(data, prefix, do)
        py = DIDImputation(
            data=data, y="y", id="id", time="time", first_treat="first_treat"
        ).fit(cluster="id", autosample=True, minn=0)
        diffs = compare_python_to_stata(py, st, fields=["nobs", "n_clust"])
        save_evidence(prefix, py, st, diffs)
        assert diffs["passed"], "\n".join(diffs["messages"])


class TestM07S8CustomCluster:
    """S8: custom cluster variable, cluster != id."""

    @pytest.fixture(scope="class")
    def data(self):
        df = _make_s1_data()
        cluster_map = {i: (i + 1) // 2 for i in df["id"].unique()}
        df["cl"] = df["id"].map(cluster_map)
        return df

    def test_s8(self, data):
        prefix = "S8_CUSTOM_CLUSTER"
        do = did_imputation_stata_do(
            "{dta}", "y", "id", "time", "first_treat",
            options="cluster(cl) autosample minn(0)",
        )
        st = run_stata_did(data, prefix, do)
        py = DIDImputation(
            data=data, y="y", id="id", time="time", first_treat="first_treat"
        ).fit(cluster="cl", autosample=True, minn=0)
        diffs = compare_python_to_stata(py, st, fields=["nobs", "n_clust"])
        save_evidence(prefix, py, st, diffs)
        assert diffs["passed"], "\n".join(diffs["messages"])
