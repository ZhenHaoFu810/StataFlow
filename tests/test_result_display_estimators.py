"""Integration tests for estimator-produced display metadata."""

from __future__ import annotations

import numpy as np
import pandas as pd

from stataflow.compat.stata import (
    areg,
    csdid,
    did_imputation,
    eventstudyinteract,
    ivregress_2sls,
    ivreghdfe,
    logit,
    ppmlhdfe,
    rdrobust,
    regress,
    reghdfe,
    xtreg_fe,
)
from stataflow.results.result import ResultSchema


def _data() -> pd.DataFrame:
    rng = np.random.default_rng(130)
    firms = np.repeat(np.arange(30), 5)
    years = np.tile(np.arange(5), 30)
    z = rng.normal(size=len(firms))
    x = rng.normal(size=len(firms))
    endog = 0.8 * z + 0.3 * x + rng.normal(scale=0.4, size=len(firms))
    y = 1.0 + 0.7 * x + 1.4 * endog + firms / 30 + rng.normal(size=len(firms))
    linear_index = -0.2 + 0.5 * x
    return pd.DataFrame(
        {
            "y": y,
            "x": x,
            "endog": endog,
            "z": z,
            "firm": firms,
            "year": years,
            "binary": (linear_index + rng.logistic(size=len(firms)) > 0).astype(float),
            "count": rng.poisson(np.exp(0.2 + 0.15 * x)),
        }
    )


def test_linear_and_fixed_effects_results_populate_display_contract() -> None:
    data = _data()
    ols = regress(data, y="y", x=["x"])
    panel = xtreg_fe(data, y="y", x=["x"], fe="firm")
    absorbed = areg(data, y="y", x=["x"], absorb="firm")
    hdfe = reghdfe(data, y="y", x=["x"], absorb=["firm", "year"])

    assert ols.model.dependent_variable == "y"
    assert ols.model.regressors == ["x"]
    assert ols.fit.model_test == "F"
    assert ols.fit.model_stat == ols.fit.f_stat
    assert panel.sample.group_count == data["firm"].nunique()
    assert panel.model.dependent_variable == "y"
    assert absorbed.sample.group_count == data["firm"].nunique()
    assert hdfe.model.dependent_variable == "y"
    assert hdfe.model.regressors == ["x"]
    assert "Fixed effects" in hdfe.summary()


def test_iv_results_use_typed_diagnostics_and_round_trip() -> None:
    data = _data()
    iv = ivregress_2sls(
        data,
        y="y",
        x_exog=["x"],
        x_endog=["endog"],
        instruments=["z"],
        first=True,
    )
    hdfe = ivreghdfe(
        data,
        y="y",
        x_exog=["x"],
        x_endog=["endog"],
        instruments=["z"],
        absorb=["firm", "year"],
        first=True,
    )

    for result in (iv, hdfe):
        assert result.model.dependent_variable == "y"
        assert result.iv.endogenous == ["endog"]
        assert result.iv.instruments == ["z"]
        assert result.iv.estimator
        assert result.iv.first_stage
        restored = ResultSchema.from_json(result.to_json())
        assert restored.iv == result.iv
        assert restored.diagnostics.widstat == result.diagnostics.widstat
        assert "Instrumental variables" in restored.summary()


def test_glm_and_ppml_results_populate_test_and_convergence_metadata() -> None:
    data = _data()
    binary = logit(data, y="binary", x=["x"])
    count = ppmlhdfe(data, y="count", x=["x"], absorb=["firm"])

    assert binary.model.dependent_variable == "binary"
    assert binary.fit.model_test == "Wald chi2"
    assert binary.fit.iterations is not None
    assert binary.fit.converged is True
    assert count.model.dependent_variable == "count"
    assert count.fit.model_test == "Wald chi2"
    assert count.fit.model_stat is not None
    assert count.fit.model_pvalue is not None
    assert count.fit.iterations is not None
    assert count.fit.converged is True
    assert "Log likelihood" in binary.summary()
    assert "Deviance" in count.summary()


def _did_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(131)
    n_units = 72
    years = np.arange(2000, 2006)
    units = np.repeat(np.arange(n_units), len(years))
    time = np.tile(years, n_units)
    cohorts = np.full(n_units, np.nan)
    cohorts[n_units // 3 : 2 * n_units // 3] = 2003
    cohorts[2 * n_units // 3 :] = 2004
    first_treat = np.repeat(cohorts, len(years))
    treated = np.isfinite(first_treat) & (time >= first_treat)
    y = (
        np.repeat(rng.normal(size=n_units), len(years))
        + np.tile(rng.normal(scale=0.3, size=len(years)), n_units)
        + 1.2 * treated
        + rng.normal(scale=0.5, size=len(units))
    )
    missing_control = pd.DataFrame({"y": y, "id": units, "year": time, "first_treat": first_treat})
    zero_control = missing_control.assign(
        first_treat=missing_control["first_treat"].fillna(0).astype(int),
        never_treat=missing_control["first_treat"].isna().astype(float),
    )
    relative_time = zero_control["year"] - zero_control["first_treat"]
    zero_control["Dm2"] = (relative_time <= -2).astype(float)
    zero_control["D0"] = (relative_time == 0).astype(float)
    zero_control["Dp1"] = (relative_time == 1).astype(float)
    return missing_control, zero_control


def test_did_results_populate_panel_design_metadata() -> None:
    missing_control, zero_control = _did_data()
    imputation = did_imputation(
        missing_control,
        y="y",
        id="id",
        time="year",
        first_treat="first_treat",
        allhorizons=True,
        pretrends=1,
    )
    interaction = eventstudyinteract(
        zero_control,
        y="y",
        event_dummies=["Dm2", "D0", "Dp1"],
        cohort="first_treat",
        control_cohort="never_treat",
        absorb=["id", "year"],
        vce="cluster",
        cluster="id",
    )
    cs = csdid(
        zero_control,
        y="y",
        id="id",
        time="year",
        first_treat="first_treat",
    )

    assert imputation.model.dependent_variable == "y"
    assert imputation.sample.group_count == missing_control["id"].nunique()
    assert imputation.did.id_variable == "id"
    assert imputation.did.time_variable == "year"
    assert imputation.did.event_window is not None
    assert imputation.did.pretrend_stat is not None
    assert imputation.did.pretrend_pvalue is not None
    assert interaction.did.aggregation == "event"
    assert interaction.did.cohort_variable == "first_treat"
    assert cs.result.did.aggregation == "event"
    assert cs.result.did.id_variable == "id"
    assert "DID design" in cs.summary()
    assert "DID design" not in cs.summary(detail="compact")


def test_rd_result_populates_typed_design_and_preserves_kernel() -> None:
    rng = np.random.default_rng(132)
    running = rng.uniform(-1, 1, 500)
    data = pd.DataFrame(
        {
            "running": running,
            "y": 0.4 + running + 1.5 * (running >= 0) + rng.normal(size=500),
        }
    )

    result = rdrobust(
        data,
        y="y",
        x="running",
        c=0.0,
        h=0.8,
        b=0.9,
        kernel="uniform",
    )
    restored = ResultSchema.from_json(result.to_json())
    text = restored.summary()

    assert result.model.dependent_variable == "y"
    assert result.rd.outcome_variable == "y"
    assert result.rd.running_variable == "running"
    assert result.rd.kernel == "uniform"
    assert result.rd.n_eff_left is not None
    assert result.rd.h_left == 0.8
    assert "uniform" in text
    assert "triangular" not in text
