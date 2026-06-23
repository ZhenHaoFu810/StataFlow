"""M08 metamorphic/property tests (P1-P3) for RD audit v1.3.

Each test first checks an internal Python property, then runs a Stata dual-run
on the transformed data set to confirm Stata agrees with the transformed Python
result.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from stataflow.compat.stata import rdrobust
from tests.audit_v1_3.m08_rd.m08_audit_utils import (
    rdrobust_stata_do,
    run_stata_rd,
    compare_python_to_stata,
    save_evidence,
)
from tests.audit_v1_3.m08_rd.test_m08_synthetic import _make_s2_standard


def _run_python_rdrobust(df: pd.DataFrame) -> object:
    return rdrobust(df, y="y", x="x", c=0.0, bwselect="mserd")


class TestM08P1RowOrderInvariance:
    """P1: shuffling rows should not change rdrobust results."""

    def test_p1(self):
        prefix = "P1_ROW_ORDER_INVARIANCE"
        df = _make_s2_standard(seed=2026062008)
        rng = np.random.default_rng(2026062008)
        shuffled = df.sample(frac=1.0, random_state=rng).reset_index(drop=True)

        py_base = _run_python_rdrobust(df)
        py_shuf = _run_python_rdrobust(shuffled)

        do = rdrobust_stata_do("{dta}", "y", "x", c=0.0, bwselect="mserd")
        st = run_stata_rd(shuffled, prefix, do)

        diffs = compare_python_to_stata(py_shuf, st, fields=["nobs", "n_h_l", "n_h_r"])
        prop_msg = (
            f"Python base tau_cl={py_base._rd_extras['tau_cl']:.6g} "
            f"vs shuffled={py_shuf._rd_extras['tau_cl']:.6g}"
        )
        diffs["messages"].append(prop_msg)
        save_evidence(prefix, py_shuf, st, diffs)
        assert py_base._rd_extras["tau_cl"] == pytest.approx(
            py_shuf._rd_extras["tau_cl"], rel=1e-12
        ), prop_msg
        assert diffs["passed"], "\n".join(diffs["messages"])


class TestM08P2IrrelevantColumn:
    """P2: adding an unused random column should not change results."""

    def test_p2(self):
        prefix = "P2_IRRELEVANT_COLUMN"
        df = _make_s2_standard(seed=2026062009)
        rng = np.random.default_rng(2026062009)
        df_extra = df.copy()
        df_extra["noise"] = rng.normal(0, 1, len(df_extra))

        py_base = _run_python_rdrobust(df)
        py_extra = _run_python_rdrobust(df_extra)

        do = rdrobust_stata_do("{dta}", "y", "x", c=0.0, bwselect="mserd")
        st = run_stata_rd(df_extra, prefix, do)

        diffs = compare_python_to_stata(py_extra, st, fields=["nobs", "n_h_l", "n_h_r"])
        prop_msg = (
            f"Python base tau_cl={py_base._rd_extras['tau_cl']:.6g} "
            f"vs extra={py_extra._rd_extras['tau_cl']:.6g}"
        )
        diffs["messages"].append(prop_msg)
        save_evidence(prefix, py_extra, st, diffs)
        assert py_base._rd_extras["tau_cl"] == pytest.approx(
            py_extra._rd_extras["tau_cl"], rel=1e-12
        ), prop_msg
        assert diffs["passed"], "\n".join(diffs["messages"])


class TestM08P3OutcomeScaling:
    """P3: scaling the outcome by a constant scales tau and SE by the same constant."""

    def test_p3(self):
        prefix = "P3_OUTCOME_SCALING"
        df = _make_s2_standard(seed=2026062010)
        scale = 3.0
        df_scaled = df.copy()
        df_scaled["y"] = df_scaled["y"] * scale

        py_base = _run_python_rdrobust(df)
        py_scaled = _run_python_rdrobust(df_scaled)

        do = rdrobust_stata_do("{dta}", "y", "x", c=0.0, bwselect="mserd")
        st = run_stata_rd(df_scaled, prefix, do)

        diffs = compare_python_to_stata(py_scaled, st, fields=["nobs", "n_h_l", "n_h_r"])
        base_tau = py_base._rd_extras["tau_cl"]
        scaled_tau = py_scaled._rd_extras["tau_cl"]
        base_se = py_base.coefficients[0].std_err
        scaled_se = py_scaled.coefficients[0].std_err
        prop_msg = (
            f"Python base tau_cl={base_tau:.6g}/SE={base_se:.6g} "
            f"vs scaled tau_cl={scaled_tau:.6g}/SE={scaled_se:.6g} (scale={scale})"
        )
        diffs["messages"].append(prop_msg)
        save_evidence(prefix, py_scaled, st, diffs)
        assert scaled_tau == pytest.approx(base_tau * scale, rel=1e-10), prop_msg
        assert scaled_se == pytest.approx(base_se * scale, rel=1e-10), prop_msg
        assert diffs["passed"], "\n".join(diffs["messages"])
