"""M07 metamorphic/property tests (P1-P3) for DID / Event Study audit v1.3.

All Python-vs-Stata comparisons below use panels with no never-treated units
so that Stata's ``did_imputation`` and Python share the same control-group
semantics.  The internal Python properties are checked first, followed by a
field-level Stata dual run on the transformed data set.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from stataflow import DIDImputation
from tests.audit_v1_3.m07_did_event_study.m07_audit_utils import (
    did_imputation_stata_do,
    run_stata_did,
    compare_python_to_stata,
    save_evidence,
)
from tests.audit_v1_3.m07_did_event_study.test_m07_synthetic import _make_panel


def _make_no_never_data(seed: int) -> pd.DataFrame:
    """Return a 60x10 panel where every unit belongs to a positive cohort."""
    return _make_panel(
        seed=seed, n_units=60, n_periods=10, cohorts=[6, 8, 10], include_never=False
    )


def _run_python_didimp(df: pd.DataFrame) -> object:
    return DIDImputation(
        data=df, y="y", id="id", time="time", first_treat="first_treat"
    ).fit(cluster="id", autosample=True, minn=0)


class TestM07P1RowOrderInvariance:
    """P1: shuffling rows should not change DID imputation results."""

    def test_p1(self):
        prefix = "P1_ROW_ORDER_INVARIANCE"
        df = _make_no_never_data(20260628)
        rng = np.random.default_rng(20260628)
        shuffled = df.sample(frac=1.0, random_state=rng).reset_index(drop=True)

        py_base = _run_python_didimp(df)
        py_shuf = _run_python_didimp(shuffled)

        do = did_imputation_stata_do(
            "{dta}", "y", "id", "time", "first_treat",
            options="cluster(id) autosample minn(0)",
        )
        st = run_stata_did(shuffled, prefix, do)

        diffs = compare_python_to_stata(py_shuf, st, fields=["nobs", "n_clust"])
        prop_msg = (
            f"Python base tau beta={py_base.coefficients[0].beta:.6g} "
            f"vs shuffled={py_shuf.coefficients[0].beta:.6g}"
        )
        diffs["messages"].append(prop_msg)
        save_evidence(prefix, py_shuf, st, diffs)
        assert py_base.coefficients[0].beta == pytest.approx(
            py_shuf.coefficients[0].beta, rel=1e-12
        ), prop_msg
        assert diffs["passed"], "\n".join(diffs["messages"])


class TestM07P2IrrelevantColumn:
    """P2: adding an unused random column should not change results."""

    def test_p2(self):
        prefix = "P2_IRRELEVANT_COLUMN"
        df = _make_no_never_data(20260629)
        rng = np.random.default_rng(20260629)
        df_extra = df.copy()
        df_extra["noise"] = rng.normal(0, 1, len(df_extra))

        py_base = _run_python_didimp(df)
        py_extra = _run_python_didimp(df_extra)

        do = did_imputation_stata_do(
            "{dta}", "y", "id", "time", "first_treat",
            options="cluster(id) autosample minn(0)",
        )
        st = run_stata_did(df_extra, prefix, do)

        diffs = compare_python_to_stata(py_extra, st, fields=["nobs", "n_clust"])
        prop_msg = (
            f"Python base tau beta={py_base.coefficients[0].beta:.6g} "
            f"vs extra={py_extra.coefficients[0].beta:.6g}"
        )
        diffs["messages"].append(prop_msg)
        save_evidence(prefix, py_extra, st, diffs)
        assert py_base.coefficients[0].beta == pytest.approx(
            py_extra.coefficients[0].beta, rel=1e-12
        ), prop_msg
        assert diffs["passed"], "\n".join(diffs["messages"])


class TestM07P3OutcomeScaling:
    """P3: scaling the outcome by a constant scales tau and SE by the same constant."""

    def test_p3(self):
        prefix = "P3_OUTCOME_SCALING"
        df = _make_no_never_data(20260630)
        scale = 2.5
        df_scaled = df.copy()
        df_scaled["y"] = df_scaled["y"] * scale

        py_base = _run_python_didimp(df)
        py_scaled = _run_python_didimp(df_scaled)

        do = did_imputation_stata_do(
            "{dta}", "y", "id", "time", "first_treat",
            options="cluster(id) autosample minn(0)",
        )
        st = run_stata_did(df_scaled, prefix, do)

        diffs = compare_python_to_stata(py_scaled, st, fields=["nobs", "n_clust"])
        base_beta = py_base.coefficients[0].beta
        scaled_beta = py_scaled.coefficients[0].beta
        base_se = py_base.coefficients[0].std_err
        scaled_se = py_scaled.coefficients[0].std_err
        prop_msg = (
            f"Python base tau beta={base_beta:.6g}/SE={base_se:.6g} "
            f"vs scaled beta={scaled_beta:.6g}/SE={scaled_se:.6g} (scale={scale})"
        )
        diffs["messages"].append(prop_msg)
        save_evidence(prefix, py_scaled, st, diffs)
        assert scaled_beta == pytest.approx(base_beta * scale, rel=1e-10), prop_msg
        assert scaled_se == pytest.approx(base_se * scale, rel=1e-10), prop_msg
        assert diffs["passed"], "\n".join(diffs["messages"])
