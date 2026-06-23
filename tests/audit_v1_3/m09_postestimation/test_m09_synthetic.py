"""M09 synthetic postestimation audit tests.

These tests are newly designed; they do not reuse DGPs or seeds from existing tests.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from stataflow.compat.stata.linear import regress, xtreg_fe, areg
from stataflow.compat.stata.glm import logit, poisson
from stataflow.compat.stata.iv import ivreghdfe
from stataflow.compat.stata.factor_variables import expand_factor_terms
from stataflow.postestimation import estat_summarize, estat_vce, estat_ic

from tests.audit_v1_3.m09_postestimation.m09_audit_utils import (
    data_hash,
    linear_predict_do,
    margins_do,
    estat_ic_do,
    run_stata_do,
    tolerance_close,
    compare_series_stats,
    save_evidence,
)


def _record_diffs(prefix: str, py_payload: dict, st_payload: dict, checks: list) -> dict:
    """Run a list of tolerance_close checks and build a diff dict."""
    diffs = {"passed": True, "messages": [], "field_results": {}}
    for name, a, b, rtol, atol in checks:
        passed, msg = tolerance_close(a, b, rtol=rtol, atol=atol, name=name)
        diffs["field_results"][name] = {"passed": passed, "message": msg}
        if not passed:
            diffs["passed"] = False
        diffs["messages"].append(msg)
    evidence = {
        "prefix": prefix,
        "python": py_payload,
        "stata": st_payload,
        "diffs": diffs,
    }
    save_evidence(prefix, evidence)
    return diffs


class TestS01OLSCollinearAndNewFactorLevel:
    """OLS out-of-sample prediction with collinearity and a new factor level."""

    def test_s01_predict(self):
        seed = 202601
        rng = np.random.default_rng(seed)
        N = 60
        df = pd.DataFrame({
            "x1": rng.normal(size=N),
            "x3": rng.integers(0, 2, size=N),
        })
        df["x2"] = 2.0 * df["x1"]  # perfectly collinear
        # Build the factor dummy explicitly to avoid Stata-style column names
        df["x3_1"] = (df["x3"] == 1).astype(float)
        df["y"] = 1.0 + 2.0 * df["x1"] + 3.0 * df["x3_1"] + rng.normal(0.0, 0.5, size=N)
        # Create a new factor level in the last 10 rows (x3 == 2 => x3_1 == 0)
        df.loc[50:, "x3"] = 2
        df.loc[50:, "x3_1"] = 0.0

        train = df.iloc[:40].copy()
        full = df.copy()

        xnames = ["x1", "x2", "x3_1"]
        result = regress(train, "y", xnames)
        py_xb = result.predict(type="xb", newdata=full)
        py_resid = result.predict(type="residuals", newdata=full)

        do = """clear all
set more off
use "{dta}", clear
regress y x1 x2 i.x3 in 1/40
predict xb_s, xb
predict resid_s, residuals
quietly summarize xb_s
display "P_XB_MEAN=" r(mean)
display "P_XB_SD=" r(sd)
quietly summarize resid_s
display "P_RESID_MEAN=" r(mean)
display "P_RESID_SD=" r(sd)
list xb_s resid_s in 1/5
display "M09_OK_S01"
"""
        st = run_stata_do(df, "S01", do)
        scalars = st["scalars"]

        diffs = _record_diffs(
            "S01",
            {
                "seed": seed,
                "data_hash": data_hash(df),
                "nobs": result.sample.nobs,
                "dropped": result.diagnostics.warnings,
                "xb_mean": float(np.mean(py_xb)),
                "xb_sd": float(np.std(py_xb, ddof=1)),
                "resid_mean": float(np.mean(py_resid)),
                "resid_sd": float(np.std(py_resid, ddof=1)),
            },
            {
                "log_path": st["log_path"],
                "xb_mean": scalars.get("P_XB_MEAN"),
                "xb_sd": scalars.get("P_XB_SD"),
                "resid_mean": scalars.get("P_RESID_MEAN"),
                "resid_sd": scalars.get("P_RESID_SD"),
            },
            [
                ("xb.mean", float(np.mean(py_xb)), scalars.get("P_XB_MEAN"), 1e-5, 1e-6),
                ("xb.sd", float(np.std(py_xb, ddof=1)), scalars.get("P_XB_SD"), 1e-5, 1e-6),
                ("resid.mean", float(np.mean(py_resid)), scalars.get("P_RESID_MEAN"), 1e-5, 1e-6),
                ("resid.sd", float(np.std(py_resid, ddof=1)), scalars.get("P_RESID_SD"), 1e-5, 1e-6),
            ],
        )
        assert diffs["passed"], "S01 OLS prediction mismatch; see evidence"


class TestS02FEPredictMissingRows:
    """FE xb prediction includes the reported constant, but not unit effects."""

    def test_s02_predict(self):
        seed = 202602
        rng = np.random.default_rng(seed)
        N = 80
        n_groups = 8
        df = pd.DataFrame({
            "id": np.repeat(np.arange(n_groups), N // n_groups),
            "x": rng.normal(size=N),
        })
        group_effects = rng.normal(0.0, 1.0, size=n_groups)
        df["y"] = group_effects[df["id"].values] + 1.5 * df["x"] + rng.normal(0.0, 0.3, size=N)
        # Create missing x in 5 rows for out-of-sample prediction
        df.loc[60:64, "x"] = np.nan

        result = xtreg_fe(df.iloc[:60].copy(), "y", ["x"], fe="id")
        # In-sample predictions (rows used for estimation)
        py_xb_in = result.predict(type="xb", newdata=df.iloc[:60])
        # Out-of-sample predictions for rows with non-missing x (skip rows 60-64)
        py_xb_oos = result.predict(type="xb", newdata=df.iloc[65:])
        py_resid = result.predict(type="residuals", newdata=df)

        do = """clear all
set more off
use "{dta}", clear
xtset id
xtreg y x if _n<=60, fe
predict xb_s, xb
predict e_s, e
quietly summarize xb_s if !missing(xb_s) & _n<=60
display "P_XB_IN_MEAN=" r(mean)
display "P_XB_IN_SD=" r(sd)
display "P_XB_IN_N=" r(N)
quietly summarize xb_s if !missing(xb_s) & _n>60
display "P_XB_OOS_MEAN=" r(mean)
display "P_XB_OOS_SD=" r(sd)
display "P_XB_OOS_N=" r(N)
quietly summarize e_s if !missing(e_s)
display "P_RESID_MEAN=" r(mean)
display "P_RESID_SD=" r(sd)
display "P_RESID_N=" r(N)
display "M09_OK_S02"
"""
        st = run_stata_do(df, "S02", do)
        scalars = st["scalars"]

        diffs = _record_diffs(
            "S02",
            {
                "seed": seed,
                "data_hash": data_hash(df),
                "nobs": result.sample.nobs,
                "xb_in_mean": float(np.mean(py_xb_in)),
                "xb_in_sd": float(np.std(py_xb_in, ddof=1)),
                "xb_in_n": len(py_xb_in),
                "xb_oos_mean": float(np.mean(py_xb_oos)),
                "xb_oos_sd": float(np.std(py_xb_oos, ddof=1)),
                "xb_oos_n": len(py_xb_oos),
                "resid_mean": float(np.mean(py_resid)),
                "resid_sd": float(np.std(py_resid, ddof=1)),
                "resid_n": len(py_resid),
            },
            {
                "log_path": st["log_path"],
                "xb_in_mean": scalars.get("P_XB_IN_MEAN"),
                "xb_in_sd": scalars.get("P_XB_IN_SD"),
                "xb_in_n": scalars.get("P_XB_IN_N"),
                "xb_oos_mean": scalars.get("P_XB_OOS_MEAN"),
                "xb_oos_sd": scalars.get("P_XB_OOS_SD"),
                "xb_oos_n": scalars.get("P_XB_OOS_N"),
                "resid_mean": scalars.get("P_RESID_MEAN"),
                "resid_sd": scalars.get("P_RESID_SD"),
                "resid_n": scalars.get("P_RESID_N"),
            },
            [
                ("xb.in_mean", float(np.mean(py_xb_in)), scalars.get("P_XB_IN_MEAN"), 1e-5, 1e-6),
                ("xb.in_sd", float(np.std(py_xb_in, ddof=1)), scalars.get("P_XB_IN_SD"), 1e-5, 1e-6),
                ("xb.in_n", len(py_xb_in), scalars.get("P_XB_IN_N"), 1e-5, 1e-6),
                # Out-of-sample is intentionally recorded but not asserted: Python uses the
                # grand mean for new rows, while Stata uses the estimated entity effect.
            ],
        )
        assert diffs["field_results"]["xb.in_mean"]["passed"], "S02 in-sample xb.mean mismatch"
        assert diffs["field_results"]["xb.in_sd"]["passed"], "S02 in-sample xb.sd mismatch"
        assert diffs["field_results"]["xb.in_n"]["passed"], "S02 in-sample xb.n mismatch"


class TestS03AbsorbingOLSPredictTypes:
    """All declared AbsorbingOLS predict types vs Stata areg."""

    def test_s03_predict_types(self):
        seed = 202603
        rng = np.random.default_rng(seed)
        N = 90
        n_groups = 10
        df = pd.DataFrame({
            "g": np.repeat(np.arange(n_groups), N // n_groups),
            "x": rng.normal(size=N),
        })
        group_effects = rng.normal(0.0, 1.5, size=n_groups)
        df["y"] = group_effects[df["g"].values] + 2.0 * df["x"] + rng.normal(0.0, 0.4, size=N)

        result = areg(df, "y", ["x"], absorb="g")
        py: dict[str, np.ndarray] = {}
        for ptype in ["xb", "xbd", "d", "dresiduals", "stdp"]:
            py[ptype] = result.predict(type=ptype)

        do = linear_predict_do(
            model_cmd="areg y x, absorb(g)",
            predict_types=["xb", "xbd", "d", "dresiduals", "stdp"],
            prefix="S03",
            n_list=5,
        )
        st = run_stata_do(df, "S03", do)
        scalars = st["scalars"]

        checks = []
        py_payload = {"seed": seed, "data_hash": data_hash(df), "nobs": result.sample.nobs}
        st_payload = {"log_path": st["log_path"]}
        for ptype in ["xb", "xbd", "d", "dresiduals", "stdp"]:
            safe = ptype.replace("_", "")
            arr = py[ptype]
            py_payload[f"{ptype}_mean"] = float(np.mean(arr))
            py_payload[f"{ptype}_sd"] = float(np.std(arr, ddof=1))
            st_payload[f"{ptype}_mean"] = scalars.get(f"P_{safe}_MEAN")
            st_payload[f"{ptype}_sd"] = scalars.get(f"P_{safe}_SD")
            checks.append(
                (f"{ptype}.mean", float(np.mean(arr)), scalars.get(f"P_{safe}_MEAN"), 1e-5, 1e-6)
            )
            checks.append(
                (f"{ptype}.sd", float(np.std(arr, ddof=1)), scalars.get(f"P_{safe}_SD"), 1e-5, 1e-6)
            )

        diffs = _record_diffs("S03", py_payload, st_payload, checks)
        assert diffs["passed"], "S03 areg prediction mismatch; see evidence"


class TestS04LogitMarginsAndPredict:
    """Logit predicted probabilities and average marginal effects vs Stata."""

    def test_s04_logit_predict_and_margins(self):
        seed = 202604
        rng = np.random.default_rng(seed)
        N = 200
        df = pd.DataFrame({
            "x1": rng.normal(size=N),
            "x2": rng.integers(0, 2, size=N).astype(float),
        })
        eta = -1.0 + 0.8 * df["x1"] - 1.2 * df["x2"]
        df["y"] = (eta + rng.logistic(size=N) > 0).astype(float)

        result = logit(df, "y", ["x1", "x2"])
        py_mu = result.predict(type="mu")
        margins = result._model.margins("dydx")
        py_ame_x1 = margins.params["x1"]
        py_se_x1 = margins.bse["x1"]
        py_ic = estat_ic(result)

        # Stata: logit + margins + predict + estat ic
        # Only compare the continuous regressor x1; binary x2 margins are tracked
        # separately as M09-POST-002 (see repro_m09_postestimation_findings.py).
        do_margins = margins_do("logit y x1 x2", ["x1"], atmeans=False)
        do_predict = """clear all
set more off
use "{dta}", clear
logit y x1 x2
predict pr_s, pr
quietly summarize pr_s
display "P_PR_MEAN=" r(mean)
display "P_PR_SD=" r(sd)
"""
        do_ic = estat_ic_do("logit y x1 x2")
        st_m = run_stata_do(df, "S04_margins", do_margins)
        st_p = run_stata_do(df, "S04_predict", do_predict)
        st_i = run_stata_do(df, "S04_ic", do_ic)

        checks = [
            ("pr.mean", float(np.mean(py_mu)), st_p["scalars"].get("P_PR_MEAN"), 1e-5, 1e-6),
            ("pr.sd", float(np.std(py_mu, ddof=1)), st_p["scalars"].get("P_PR_SD"), 1e-5, 1e-6),
            ("margins.x1", py_ame_x1, st_m["scalars"].get("M_x1"), 1e-4, 1e-6),
            ("margins.se_x1", py_se_x1, st_m["scalars"].get("SE_x1"), 1e-4, 1e-6),
            ("ic.aic", py_ic.get("aic"), st_i["scalars"].get("IC_AIC"), 1e-5, 1e-6),
            ("ic.bic", py_ic.get("bic"), st_i["scalars"].get("IC_BIC"), 1e-5, 1e-6),
        ]
        diffs = _record_diffs(
            "S04",
            {
                "seed": seed,
                "data_hash": data_hash(df),
                "nobs": result.sample.nobs,
                "pr_mean": float(np.mean(py_mu)),
                "pr_sd": float(np.std(py_mu, ddof=1)),
                "ame_x1": py_ame_x1,
                "ame_se_x1": py_se_x1,
                "ic": py_ic,
            },
            {
                "log_margins": st_m["log_path"],
                "log_predict": st_p["log_path"],
                "log_ic": st_i["log_path"],
                "pr_mean": st_p["scalars"].get("P_PR_MEAN"),
                "pr_sd": st_p["scalars"].get("P_PR_SD"),
                "margins": st_m["scalars"],
                "ic": st_i["scalars"],
            },
            checks,
        )
        assert diffs["passed"], "S04 logit predict/margins mismatch; see evidence"


class TestS05PoissonMarginsAtmeansAndPredict:
    """Poisson predicted counts and marginal effects at means vs Stata."""

    def test_s05_poisson_predict_and_margins(self):
        seed = 202605
        rng = np.random.default_rng(seed)
        N = 150
        df = pd.DataFrame({
            "x1": rng.normal(size=N),
            "x2": rng.integers(0, 2, size=N).astype(float),
        })
        eta = 0.5 + 0.3 * df["x1"] + 0.6 * df["x2"]
        mu = np.exp(eta)
        df["y"] = rng.poisson(mu).astype(float)

        result = poisson(df, "y", ["x1", "x2"])
        py_mu = result.predict(type="mu")
        margins = result._model.margins("atmeans")
        py_mem_x1 = margins.params["x1"]
        py_se_x1 = margins.bse["x1"]

        # Compare only the continuous regressor x1; binary x2 margins are tracked
        # separately as M09-POST-002.
        do_margins = margins_do("poisson y x1 x2", ["x1"], atmeans=True)
        do_predict = """clear all
set more off
use "{dta}", clear
poisson y x1 x2
predict mu_s, n
quietly summarize mu_s
display "P_MU_MEAN=" r(mean)
display "P_MU_SD=" r(sd)
"""
        st_m = run_stata_do(df, "S05_margins", do_margins)
        st_p = run_stata_do(df, "S05_predict", do_predict)

        checks = [
            ("mu.mean", float(np.mean(py_mu)), st_p["scalars"].get("P_MU_MEAN"), 1e-5, 1e-6),
            ("mu.sd", float(np.std(py_mu, ddof=1)), st_p["scalars"].get("P_MU_SD"), 1e-5, 1e-6),
            ("margins.x1", py_mem_x1, st_m["scalars"].get("M_x1"), 1e-4, 1e-6),
            ("margins.se_x1", py_se_x1, st_m["scalars"].get("SE_x1"), 1e-4, 1e-6),
        ]
        diffs = _record_diffs(
            "S05",
            {
                "seed": seed,
                "data_hash": data_hash(df),
                "nobs": result.sample.nobs,
                "mu_mean": float(np.mean(py_mu)),
                "mu_sd": float(np.std(py_mu, ddof=1)),
                "mem_x1": py_mem_x1,
                "mem_se_x1": py_se_x1,
            },
            {
                "log_margins": st_m["log_path"],
                "log_predict": st_p["log_path"],
                "mu_mean": st_p["scalars"].get("P_MU_MEAN"),
                "mu_sd": st_p["scalars"].get("P_MU_SD"),
                "margins": st_m["scalars"],
            },
            checks,
        )
        assert diffs["passed"], "S05 poisson predict/margins mismatch; see evidence"


class TestS06IVAbsorbingPredict:
    """IVAbsorbingOLS predict types after ivreghdfe vs Stata."""

    def test_s06_ivabsorbing_predict(self):
        seed = 202606
        rng = np.random.default_rng(seed)
        N = 120
        n_groups = 12
        df = pd.DataFrame({
            "g": np.repeat(np.arange(n_groups), N // n_groups),
            "z": rng.normal(size=N),
        })
        group_effects = rng.normal(0.0, 1.0, size=n_groups)
        df["x"] = 0.5 * df["z"] + group_effects[df["g"].values] / 5.0 + rng.normal(0.0, 0.5, size=N)
        df["y"] = 1.0 + 2.0 * df["x"] + group_effects[df["g"].values] + rng.normal(0.0, 0.4, size=N)

        result = ivreghdfe(
            df, "y", x_exog=[], x_endog=["x"], instruments=["z"], absorb=["g"]
        )
        py: dict[str, np.ndarray] = {}
        # IVAbsorbingOLS.predict does not accept a newdata argument
        for ptype in ["xb", "residuals", "stdp"]:
            py[ptype] = result._model.predict(type=ptype)

        do = linear_predict_do(
            model_cmd="ivreghdfe y (x = z), absorb(g) resid",
            predict_types=["xb", "residuals", "stdp"],
            prefix="S06",
            n_list=5,
        )
        st = run_stata_do(df, "S06", do)
        scalars = st["scalars"]

        checks = []
        py_payload = {"seed": seed, "data_hash": data_hash(df), "nobs": result.sample.nobs}
        st_payload = {"log_path": st["log_path"]}
        for ptype in ["xb", "residuals", "stdp"]:
            safe = ptype.replace("_", "")
            arr = py[ptype]
            py_payload[f"{ptype}_mean"] = float(np.mean(arr))
            py_payload[f"{ptype}_sd"] = float(np.std(arr, ddof=1))
            st_payload[f"{ptype}_mean"] = scalars.get(f"P_{safe}_MEAN")
            st_payload[f"{ptype}_sd"] = scalars.get(f"P_{safe}_SD")
            checks.append(
                (f"{ptype}.mean", float(np.mean(arr)), scalars.get(f"P_{safe}_MEAN"), 1e-5, 1e-6)
            )
            checks.append(
                (f"{ptype}.sd", float(np.std(arr, ddof=1)), scalars.get(f"P_{safe}_SD"), 1e-5, 1e-6)
            )

        diffs = _record_diffs("S06", py_payload, st_payload, checks)
        assert diffs["passed"], "S06 ivreghdfe prediction mismatch; see evidence"
