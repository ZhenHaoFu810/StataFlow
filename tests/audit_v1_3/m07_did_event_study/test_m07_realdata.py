"""M07 real-data dual-run tests (R1-R2) for DID / Event Study audit v1.3."""

from __future__ import annotations

import os

import numpy as np
import pandas as pd
import pytest

from stataflow import DIDImputation, csdid
from tests.audit_v1_3.m07_did_event_study.m07_audit_utils import (
    did_imputation_stata_do,
    csdid_stata_do,
    run_stata_did,
    compare_python_to_stata,
    save_evidence,
)

# Resolve relative to this file so the test is independent of cwd
_HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
EZ_DIDIMP = os.path.join(PROJECT_ROOT, "research", "data", "public", "did", "ezunem_prepared_didimp.dta")
EZ_CSDID = os.path.join(PROJECT_ROOT, "research", "data", "public", "did", "ezunem_prepared.dta")


def _load_didimp() -> pd.DataFrame:
    df = pd.read_stata(EZ_DIDIMP)
    # The requested lnpop is absent; use an existing continuous control.
    if "lnpop" not in df.columns:
        df["control_x"] = df["guclms"]
    return df


def _load_csdid() -> pd.DataFrame:
    return pd.read_stata(EZ_CSDID)


class TestM07R1EzunemDidImputationControls:
    """R1: ezunem DID imputation with controls + allhorizons + autosample.

    Covers missing first_treat as never-treated and controls-adjusted SE weights.
    """

    @pytest.fixture(scope="class")
    def data(self):
        df = _load_didimp()
        # Stata did_imputation requires missing for never-treated.
        df["first_treat"] = df["first_treat"].replace(-1, np.nan).astype(float)
        return df

    def test_r1(self, data):
        prefix = "R1_EZUNEM_DIDIMP_CONTROLS"
        control_var = "control_x"
        do = did_imputation_stata_do(
            "{dta}",
            "uclms",
            "city",
            "year",
            "first_treat",
            options=f"cluster(city) controls({control_var}) allhorizons autosample minn(0)",
        )
        st = run_stata_did(data, prefix, do)
        py = DIDImputation(
            data=data, y="uclms", id="city", time="year", first_treat="first_treat"
        ).fit(
            cluster="city",
            controls=[control_var],
            allhorizons=True,
            autosample=True,
            minn=0,
        )
        diffs = compare_python_to_stata(py, st, fields=["nobs", "n_clust"])
        save_evidence(prefix, py, st, diffs)
        assert diffs["passed"], "\n".join(diffs["messages"])


class TestM07R2EzunemCsdidNotyetEvent:
    """R2: ezunem CSDID reg + notyet + event aggregation.

    Verifies that notyet uses never-treated and not-yet-treated controls.
    """

    @pytest.fixture(scope="class")
    def data(self):
        return _load_csdid()

    def test_r2(self, data):
        prefix = "R2_EZUNEM_CSDID_NOTYET"
        do = csdid_stata_do(
            "{dta}",
            "uclms",
            "city",
            "year",
            "first_treat",
            options="method(reg) vce(cluster city) notyet",
            agg="event",
        )
        st = run_stata_did(data, prefix, do)
        model = csdid(
            data=data, y="uclms", id="city", time="year", first_treat="first_treat",
            method="reg", cluster="city", notyet=True,
        )
        py = model.estat_event()
        diffs = compare_python_to_stata(py, st, fields=["nobs"])
        save_evidence(prefix, py, st, diffs)
        assert diffs["passed"], "\n".join(diffs["messages"])
