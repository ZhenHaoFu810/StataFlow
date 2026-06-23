"""M08 real-data dual-run tests (R1-R2) for RD audit v1.3.

Uses the public rdrobust Senate data.  Specifications are chosen to avoid
repeating exact existing golden-test designs.
"""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import pytest

from stataflow import RDRobust
from stataflow.compat.stata import rdrobust
from tests.audit_v1_3.m08_rd.m08_audit_utils import (
    rdrobust_stata_do,
    run_stata_rd,
    compare_python_to_stata,
    save_evidence,
)

_HERE = Path(__file__).resolve().parent
PROJECT_ROOT = _HERE.parents[2]
SENATE_DTA = PROJECT_ROOT / "tests" / "data" / "rdrobust_senate.dta"
SENATE_Z_DTA = PROJECT_ROOT / "research" / "data" / "public" / "rdrobust_senate_with_z.dta"


def _load_senate() -> pd.DataFrame:
    return pd.read_stata(SENATE_DTA)


def _load_senate_with_z() -> pd.DataFrame:
    return pd.read_stata(SENATE_Z_DTA)


class TestM08R1SenateCersumCovsHC0:
    """R1: Senate data with CER-SUM selector, covariates, and HC0 VCE.

    This specification differs from existing golden tests that use
    bwselect(mserd), h(15), or cluster VCE.
    """

    @pytest.fixture(scope="class")
    def data(self):
        return _load_senate_with_z()

    def test_r1(self, data):
        prefix = "R1_SENATE_CERSUM_COVS_HC0"
        do = rdrobust_stata_do(
            "{dta}",
            "vote",
            "margin",
            c=0.0,
            bwselect="cersum",
            covs="z",
            vce="hc0",
            kernel="epanechnikov",
        )
        st = run_stata_rd(data, prefix, do)
        py = rdrobust(
            data,
            y="vote",
            x="margin",
            c=0.0,
            bwselect="cersum",
            covs="z",
            vce="hc0",
            kernel="epanechnikov",
        )
        diffs = compare_python_to_stata(
            py,
            st,
            fields=["nobs", "n_l", "n_r", "n_h_l", "n_h_r", "h_l", "h_r", "b_l", "b_r"],
        )
        save_evidence(prefix, py, st, diffs)
        assert diffs["passed"], "\n".join(diffs["messages"])


class TestM08R2SenateSwappedAxesMsetwo:
    """R2: Senate data with swapped outcome/running variable and MSE-TWO selector.

    Uses `margin` as outcome and `vote` as running variable with cutoff 50.
    This design is not covered by existing rdrobust golden tests.
    """

    @pytest.fixture(scope="class")
    def data(self):
        return _load_senate_with_z()

    def test_r2(self, data):
        prefix = "R2_SENATE_SWAPPED_MSETWO"
        do = rdrobust_stata_do(
            "{dta}",
            "margin",
            "vote",
            c=50.0,
            bwselect="msetwo",
            vce="nn",
            kernel="triangular",
        )
        st = run_stata_rd(data, prefix, do)
        py = rdrobust(
            data,
            y="margin",
            x="vote",
            c=50.0,
            bwselect="msetwo",
            vce="nn",
            kernel="triangular",
        )
        diffs = compare_python_to_stata(
            py,
            st,
            fields=["nobs", "n_l", "n_r", "n_h_l", "n_h_r", "h_l", "h_r", "b_l", "b_r"],
        )
        save_evidence(prefix, py, st, diffs)
        assert diffs["passed"], "\n".join(diffs["messages"])
