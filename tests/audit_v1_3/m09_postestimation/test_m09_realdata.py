"""M09 real-data postestimation audit tests.

These tests use project public datasets with new specifications that do not
overlap with existing golden tests.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from stataflow.compat.stata.linear import regress, areg
from stataflow.postestimation import estat_summarize

from tests.audit_v1_3.m09_postestimation.m09_audit_utils import (
    data_hash,
    linear_predict_do,
    estat_summarize_do,
    run_stata_do,
    tolerance_close,
    save_evidence,
)


def _record_diffs(prefix: str, py_payload: dict, st_payload: dict, checks: list) -> dict:
    diffs = {"passed": True, "messages": [], "field_results": {}}
    for name, a, b, rtol, atol in checks:
        passed, msg = tolerance_close(a, b, rtol=rtol, atol=atol, name=name)
        diffs["field_results"][name] = {"passed": passed, "message": msg}
        if not passed:
            diffs["passed"] = False
        diffs["messages"].append(msg)
    save_evidence(prefix, {"prefix": prefix, "python": py_payload, "stata": st_payload, "diffs": diffs})
    return diffs


class TestR01SenateOLSPredictAndEstat:
    """R01: Senate data OLS predict + estat summarize (new spec)."""

    def test_r01(self):
        df = pd.read_stata("research/data/public/rdrobust_senate_with_z.dta")
        # New empirical question: predict vote share from margin and terms in house
        result = regress(df, "vote", ["margin", "termshouse"])
        py_xb = result.predict(type="xb")
        py_resid = result.predict(type="residuals")
        py_summary = estat_summarize(result, df, variables=["vote", "margin"])

        do = """clear all
set more off
use "{dta}", clear
regress vote margin termshouse
predict xb_s, xb
predict resid_s, residuals
quietly summarize xb_s
display "P_XB_MEAN=" r(mean)
display "P_XB_SD=" r(sd)
quietly summarize resid_s
display "P_RESID_MEAN=" r(mean)
display "P_RESID_SD=" r(sd)
quietly summarize vote if e(sample)
display "SUM_vote_N=" r(N)
display "SUM_vote_MEAN=" r(mean)
display "SUM_vote_SD=" r(sd)
quietly summarize margin if e(sample)
display "SUM_margin_N=" r(N)
display "SUM_margin_MEAN=" r(mean)
display "SUM_margin_SD=" r(sd)
display "M09_OK_R01"
"""
        st = run_stata_do(df, "R01", do)
        s = st["scalars"]

        checks = [
            ("xb.mean", float(np.mean(py_xb)), s.get("P_XB_MEAN"), 1e-5, 1e-6),
            ("xb.sd", float(np.std(py_xb, ddof=1)), s.get("P_XB_SD"), 1e-5, 1e-6),
            ("resid.mean", float(np.mean(py_resid)), s.get("P_RESID_MEAN"), 1e-5, 1e-6),
            ("resid.sd", float(np.std(py_resid, ddof=1)), s.get("P_RESID_SD"), 1e-5, 1e-6),
            ("sum.vote_N", py_summary["vote"]["N"], s.get("SUM_vote_N"), 1e-5, 1e-6),
            ("sum.vote_mean", py_summary["vote"]["mean"], s.get("SUM_vote_MEAN"), 1e-5, 1e-6),
            ("sum.vote_sd", py_summary["vote"]["sd"], s.get("SUM_vote_SD"), 1e-5, 1e-6),
            ("sum.margin_N", py_summary["margin"]["N"], s.get("SUM_margin_N"), 1e-5, 1e-6),
            ("sum.margin_mean", py_summary["margin"]["mean"], s.get("SUM_margin_MEAN"), 1e-5, 1e-6),
            ("sum.margin_sd", py_summary["margin"]["sd"], s.get("SUM_margin_SD"), 1e-5, 1e-6),
        ]
        diffs = _record_diffs(
            "R01",
            {
                "data_hash": data_hash(df),
                "nobs": result.sample.nobs,
                "xb_mean": float(np.mean(py_xb)),
                "xb_sd": float(np.std(py_xb, ddof=1)),
                "resid_mean": float(np.mean(py_resid)),
                "resid_sd": float(np.std(py_resid, ddof=1)),
                "summary": py_summary,
            },
            {"log_path": st["log_path"], **s},
            checks,
        )
        assert diffs["passed"], "R01 Senate OLS postestimation mismatch; see evidence"


class TestR02JtrainAbsorbingPredict:
    """R02: JTrain areg absorb predict + estat summarize."""

    def test_r02(self):
        df = pd.read_stata("research/data/public/did/jtrain_prepared.dta")
        # Drop rows with missing values in key variables
        sub = df[["lscrap", "grant", "d89", "d88", "fcode"]].dropna()
        result = areg(sub, "lscrap", ["grant", "d89", "d88"], absorb="fcode")
        py_xb = result.predict(type="xb")
        py_xbd = result.predict(type="xbd")
        py_resid = result.predict(type="residuals")
        py_summary = estat_summarize(result, sub, variables=["lscrap", "grant"])

        do = """clear all
set more off
use "{dta}", clear
areg lscrap grant d89 d88, absorb(fcode)
predict xb_s, xb
predict xbd_s, xbd
predict resid_s, residuals
quietly summarize xb_s
display "P_XB_MEAN=" r(mean)
display "P_XB_SD=" r(sd)
quietly summarize xbd_s
display "P_XBD_MEAN=" r(mean)
display "P_XBD_SD=" r(sd)
quietly summarize resid_s
display "P_RESID_MEAN=" r(mean)
display "P_RESID_SD=" r(sd)
quietly summarize lscrap if e(sample)
display "SUM_lscrap_N=" r(N)
display "SUM_lscrap_MEAN=" r(mean)
display "SUM_lscrap_SD=" r(sd)
display "M09_OK_R02"
"""
        st = run_stata_do(sub, "R02", do)
        s = st["scalars"]

        checks = [
            ("xb.mean", float(np.mean(py_xb)), s.get("P_XB_MEAN"), 1e-5, 1e-6),
            ("xb.sd", float(np.std(py_xb, ddof=1)), s.get("P_XB_SD"), 1e-5, 1e-6),
            ("xbd.mean", float(np.mean(py_xbd)), s.get("P_XBD_MEAN"), 1e-5, 1e-6),
            ("xbd.sd", float(np.std(py_xbd, ddof=1)), s.get("P_XBD_SD"), 1e-5, 1e-6),
            ("resid.mean", float(np.mean(py_resid)), s.get("P_RESID_MEAN"), 1e-5, 1e-6),
            ("resid.sd", float(np.std(py_resid, ddof=1)), s.get("P_RESID_SD"), 1e-5, 1e-6),
            ("sum.lscrap_N", py_summary["lscrap"]["N"], s.get("SUM_lscrap_N"), 1e-5, 1e-6),
            ("sum.lscrap_mean", py_summary["lscrap"]["mean"], s.get("SUM_lscrap_MEAN"), 1e-5, 1e-6),
            ("sum.lscrap_sd", py_summary["lscrap"]["sd"], s.get("SUM_lscrap_SD"), 1e-5, 1e-6),
        ]
        diffs = _record_diffs(
            "R02",
            {
                "data_hash": data_hash(sub),
                "nobs": result.sample.nobs,
                "xb_mean": float(np.mean(py_xb)),
                "xb_sd": float(np.std(py_xb, ddof=1)),
                "xbd_mean": float(np.mean(py_xbd)),
                "xbd_sd": float(np.std(py_xbd, ddof=1)),
                "resid_mean": float(np.mean(py_resid)),
                "resid_sd": float(np.std(py_resid, ddof=1)),
                "summary": py_summary,
            },
            {"log_path": st["log_path"], **s},
            checks,
        )
        assert diffs["passed"], "R02 JTrain areg postestimation mismatch; see evidence"
