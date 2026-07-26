"""Reproducible Stata validation cases for built-in command families.

Each case generates its own synthetic data, runs the identical estimation in
local Stata 17 and in Python, and compares coefficients, standard errors,
and (where applicable) degrees of freedom at relative tolerance < 1e-6.
Every Stata run must emit its unique completion marker; a missing marker is
a hard failure, not a pass.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from stataflow.compat.stata import (
    areg,
    ivregress_2sls,
    logit,
    poisson,
    regress,
    xtreg_fe,
)
from tests.stata_validation.test_utils import (
    assert_coef_alignment,
    run_stata_case,
    stata_coef_dump,
    tolerance_close,
    write_case_data,
)

pytestmark = pytest.mark.stata


def _make_cross_section(seed: int = 20260724, n: int = 500) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    x1 = rng.normal(size=n)
    x2 = rng.normal(size=n)
    y = 1.0 + 1.5 * x1 - 0.8 * x2 + rng.normal(size=n)
    return pd.DataFrame({"y": y, "x1": x1, "x2": x2})


def _make_panel(seed: int = 20260725, n_entities: int = 40, n_periods: int = 6) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    n = n_entities * n_periods
    panel_id = np.repeat(np.arange(1, n_entities + 1), n_periods)
    time_id = np.tile(np.arange(1, n_periods + 1), n_entities)
    x1 = rng.normal(size=n)
    entity_fe = np.repeat(rng.normal(scale=1.5, size=n_entities), n_periods)
    y = 1.0 + 0.8 * x1 + entity_fe + rng.normal(size=n)
    return pd.DataFrame(
        {
            "y": y,
            "x1": x1,
            "panel_id": panel_id.astype(int),
            "time_id": time_id.astype(int),
        }
    )


def _make_absorb_data(seed: int = 20260726, n_groups: int = 30, per_group: int = 8) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    n = n_groups * per_group
    g = np.repeat(np.arange(1, n_groups + 1), per_group)
    x1 = rng.normal(size=n)
    x2 = rng.normal(size=n)
    group_fe = np.repeat(rng.normal(scale=2.0, size=n_groups), per_group)
    y = 0.5 + 1.2 * x1 - 0.6 * x2 + group_fe + rng.normal(size=n)
    return pd.DataFrame({"y": y, "x1": x1, "x2": x2, "g": g.astype(int)})


def _make_iv_data(seed: int = 20260727, n: int = 600) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    z1 = rng.normal(size=n)
    z2 = rng.normal(size=n)
    u = rng.normal(size=n)
    e = 0.6 * u + rng.normal(scale=0.8, size=n)
    x_end = 0.8 * z1 + 0.5 * z2 + u
    x1 = rng.normal(size=n)
    y = 1.0 + 0.7 * x1 + 1.5 * x_end + e
    return pd.DataFrame({"y": y, "x1": x1, "x_end": x_end, "z1": z1, "z2": z2})


def _make_binary_data(seed: int = 20260728, n: int = 800) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    x1 = rng.normal(size=n)
    x2 = rng.normal(size=n)
    eta = 0.2 + 0.9 * x1 - 0.7 * x2
    prob = 1.0 / (1.0 + np.exp(-eta))
    y = (rng.random(n) < prob).astype(int)
    return pd.DataFrame({"y": y, "x1": x1, "x2": x2})


def _make_count_data(seed: int = 20260729, n: int = 800) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    x1 = rng.normal(size=n)
    x2 = rng.normal(size=n)
    mu = np.exp(0.3 + 0.6 * x1 - 0.5 * x2)
    y = rng.poisson(mu)
    return pd.DataFrame({"y": y, "x1": x1, "x2": x2})


def test_regress_robust(stata_path):
    """regress y x1 x2, vce(robust): coefs, robust SEs, df_resid."""
    data = _make_cross_section()
    dta = write_case_data(data, "public_regress_robust")
    do = f"""
version 17.0
clear all
set more off
use "{dta.as_posix()}", clear
regress y x1 x2, vce(robust)
di as txt "E_N=" e(N)
di as txt "E_DF_R=" e(df_r)
{stata_coef_dump(["x1", "x2", "_cons"])}
di as txt "STATAFLOW_PUBLIC_REGRESS_ROBUST_OK"
"""
    st = run_stata_case(do, "STATAFLOW_PUBLIC_REGRESS_ROBUST_OK")
    py = regress(data, y="y", x=["x1", "x2"], vce="robust")
    assert py.sample.nobs == int(st["e"]["N"])
    ok, msg = tolerance_close(py.fit.df_resid, st["e"]["DF_R"], name="df_resid")
    assert ok, msg
    assert_coef_alignment(py.coefficients, st)


def test_xtreg_fe_robust(stata_path):
    """xtreg y x1, fe vce(robust): coefs, robust SEs, df_resid."""
    data = _make_panel()
    dta = write_case_data(data, "public_xtreg_fe_robust")
    do = f"""
version 17.0
clear all
set more off
use "{dta.as_posix()}", clear
xtset panel_id time_id
xtreg y x1, fe vce(robust)
di as txt "E_N=" e(N)
di as txt "E_DF_R=" e(df_r)
{stata_coef_dump(["x1", "_cons"])}
di as txt "STATAFLOW_PUBLIC_XTREG_FE_ROBUST_OK"
"""
    st = run_stata_case(do, "STATAFLOW_PUBLIC_XTREG_FE_ROBUST_OK")
    py = xtreg_fe(data, y="y", x=["x1"], fe="panel_id", vce="robust")
    assert py.sample.nobs == int(st["e"]["N"])
    ok, msg = tolerance_close(py.fit.df_resid, st["e"]["DF_R"], name="df_resid")
    assert ok, msg
    assert_coef_alignment(py.coefficients, st)


def test_areg_cluster(stata_path):
    """areg y x1 x2, absorb(g) vce(cluster g): coefs and cluster SEs."""
    data = _make_absorb_data()
    dta = write_case_data(data, "public_areg_cluster")
    do = f"""
version 17.0
clear all
set more off
use "{dta.as_posix()}", clear
areg y x1 x2, absorb(g) vce(cluster g)
di as txt "E_N=" e(N)
di as txt "E_N_CLUST=" e(N_clust)
{stata_coef_dump(["x1", "x2", "_cons"])}
di as txt "STATAFLOW_PUBLIC_AREG_CLUSTER_OK"
"""
    st = run_stata_case(do, "STATAFLOW_PUBLIC_AREG_CLUSTER_OK")
    py = areg(data, y="y", x=["x1", "x2"], absorb="g", vce="cluster", cluster="g")
    assert py.sample.nobs == int(st["e"]["N"])
    assert_coef_alignment(py.coefficients, st)


def test_ivregress_2sls_robust(stata_path):
    """ivregress 2sls y x1 (x_end = z1 z2), vce(robust)."""
    data = _make_iv_data()
    dta = write_case_data(data, "public_ivregress_2sls_robust")
    do = f"""
version 17.0
clear all
set more off
use "{dta.as_posix()}", clear
ivregress 2sls y x1 (x_end = z1 z2), vce(robust)
di as txt "E_N=" e(N)
{stata_coef_dump(["x_end", "x1", "_cons"])}
di as txt "STATAFLOW_PUBLIC_IVREGRESS_2SLS_ROBUST_OK"
"""
    st = run_stata_case(do, "STATAFLOW_PUBLIC_IVREGRESS_2SLS_ROBUST_OK")
    py = ivregress_2sls(
        data,
        y="y",
        x_exog=["x1"],
        x_endog=["x_end"],
        instruments=["z1", "z2"],
        vce="robust",
    )
    assert py.sample.nobs == int(st["e"]["N"])
    assert_coef_alignment(py.coefficients, st)


def test_logit_robust(stata_path):
    """logit y x1 x2, vce(robust): coefs and robust SEs."""
    data = _make_binary_data()
    dta = write_case_data(data, "public_logit_robust")
    do = f"""
version 17.0
clear all
set more off
use "{dta.as_posix()}", clear
logit y x1 x2, vce(robust)
di as txt "E_N=" e(N)
{stata_coef_dump(["x1", "x2", "_cons"])}
di as txt "STATAFLOW_PUBLIC_LOGIT_ROBUST_OK"
"""
    st = run_stata_case(do, "STATAFLOW_PUBLIC_LOGIT_ROBUST_OK")
    py = logit(data, y="y", x=["x1", "x2"], vce="robust")
    assert py.sample.nobs == int(st["e"]["N"])
    assert_coef_alignment(py.coefficients, st)


def test_poisson_robust(stata_path):
    """poisson y x1 x2, vce(robust): coefs and robust SEs."""
    data = _make_count_data()
    dta = write_case_data(data, "public_poisson_robust")
    do = f"""
version 17.0
clear all
set more off
use "{dta.as_posix()}", clear
poisson y x1 x2, vce(robust)
di as txt "E_N=" e(N)
{stata_coef_dump(["x1", "x2", "_cons"])}
di as txt "STATAFLOW_PUBLIC_POISSON_ROBUST_OK"
"""
    st = run_stata_case(do, "STATAFLOW_PUBLIC_POISSON_ROBUST_OK")
    py = poisson(data, y="y", x=["x1", "x2"], vce="robust")
    assert py.sample.nobs == int(st["e"]["N"])
    assert_coef_alignment(py.coefficients, st)
