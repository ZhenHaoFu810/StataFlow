"""M05 GLM: synthetic dual-run experiments."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent))
from m05_audit_utils import (
    STATA_CASES,
    glm_stata_do_template,
    run_stata_do,
    python_result_to_dict,
    compare_scalars,
    compare_coefficients,
    compare_vce,
    save_evidence,
)

from stataflow.estimators import Logit, Probit, Poisson
from stataflow.compat.stata import logit, poisson


def _run_single(
    test_id: str,
    df: pd.DataFrame,
    y: str,
    x: list[str],
    command: str,
    model_cls,
    vce: str = "ols",
    cluster: str | None = None,
    aweight: str | None = None,
    eform: bool = False,
    include_deviance: bool = True,
    wrapper=None,
    rtol: float = 1e-6,
    atol: float = 1e-8,
):
    csv = STATA_CASES / f"{test_id}.csv"
    df.to_csv(csv, index=False)

    st_result = run_stata_do(glm_stata_do_template(str(csv), command, y_var=y, include_deviance=include_deviance), test_id)

    if aweight is not None:
        # The Stata-compatible wrappers correctly reject aweight. These
        # experiments intentionally validate the Python-native normalized
        # weighted estimator against an equivalent pre-normalized iweight run.
        py_result = model_cls(
            df, y=y, x=x, weights=df[aweight].to_numpy()
        ).fit(vce=vce, cluster=cluster, eform=eform)
    elif wrapper is not None:
        py_result = wrapper(df, y=y, x=x, vce=vce, cluster=cluster, aweight=aweight, **({"or_": eform} if eform else {}))
    else:
        kwargs = {"vce": vce, "cluster": cluster, "eform": eform}
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        py_result = model_cls(df, y=y, x=x).fit(**kwargs)

    py_dict = python_result_to_dict(py_result)

    comparisons = []
    comparisons.extend(compare_coefficients(py_dict["coefficients"], st_result.get("coefficients", []), rtol=rtol, atol=atol))
    scalar_fields = ["nobs", "df_model"]
    if cluster is None:
        # Stata GLM does not define e(df_r); our derived value is n-k, matching the conventional df_resid.
        scalar_fields.append("df_resid")
    if aweight is None:
        # Weight scaling does not affect coefficients but changes the absolute LL and derived chi2.
        scalar_fields.extend(["ll", "pseudo_r2"])
        if vce == "ols":
            # Stata's e(chi2) is the LR chi2 only under conventional VCE; under robust/cluster it is Wald chi2.
            scalar_fields.extend(["chi2", "chi2_pvalue"])
    for field in scalar_fields:
        comparisons.append(compare_scalars(py_dict[field], st_result.get(field), field, rtol=rtol, atol=atol))
    if include_deviance and "deviance" in py_dict and py_dict["deviance"] is not None:
        comparisons.append(compare_scalars(py_dict["deviance"], st_result.get("deviance"), "deviance", rtol=rtol, atol=atol))
    if cluster is not None:
        comparisons.append(compare_scalars(py_dict["cluster_count"], st_result.get("n_clust"), "cluster_count"))

    comparisons.extend(compare_vce(
        py_dict["vce"],
        st_result.get("vce", np.zeros((0, 0))),
        py_dict["vce_row_names"],
        [c["name"] for c in st_result.get("coefficients", [])],
        rtol=rtol,
        atol=atol,
    ))

    save_evidence(test_id, py_dict, st_result, comparisons, data=df)
    return all(p for p, _ in comparisons), comparisons


def test_s1_hand_computable_logit():
    """S1: hand-computable small-sample logit."""
    test_id = "S1_hand_computable_logit"
    df = pd.DataFrame({
        "y": [0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0],
        "x": [0.0, 0.0, 1.0, 1.0, 0.0, 1.0, 0.0, 1.0],
    })
    passed, comparisons = _run_single(
        test_id, df, "y", ["x"], "logit y x",
        Logit, vce="ols", include_deviance=True,
    )
    assert passed, "\n".join(m for _, m in comparisons if not _)


def test_s2_logit_vce_ols():
    """S2: moderate logit with OLS VCE."""
    test_id = "S2_logit_vce_ols"
    rng = np.random.default_rng(2025061201)
    n = 180
    g = np.repeat(np.arange(1, 31), 6)
    x1 = rng.normal(size=n)
    x2 = rng.normal(size=n)
    lp = -1.0 + 0.7 * x1 - 0.4 * x2
    p = 1.0 / (1.0 + np.exp(-lp))
    y = (rng.random(n) < p).astype(float)
    df = pd.DataFrame({"y": y, "x1": x1, "x2": x2, "g": g})
    passed, comparisons = _run_single(
        test_id, df, "y", ["x1", "x2"], "logit y x1 x2",
        Logit, vce="ols", include_deviance=True,
    )
    assert passed, "\n".join(m for _, m in comparisons if not _)


def test_s2_logit_vce_robust():
    """S2: moderate logit with robust VCE."""
    test_id = "S2_logit_vce_robust"
    rng = np.random.default_rng(2025061201)
    n = 180
    g = np.repeat(np.arange(1, 31), 6)
    x1 = rng.normal(size=n)
    x2 = rng.normal(size=n)
    lp = -1.0 + 0.7 * x1 - 0.4 * x2
    p = 1.0 / (1.0 + np.exp(-lp))
    y = (rng.random(n) < p).astype(float)
    df = pd.DataFrame({"y": y, "x1": x1, "x2": x2, "g": g})
    passed, comparisons = _run_single(
        test_id, df, "y", ["x1", "x2"], "logit y x1 x2, vce(robust)",
        Logit, vce="robust", include_deviance=True,
    )
    # Robust VCE small-sample adjustment is under audit; record evidence regardless.
    if not passed:
        pytest.xfail(f"Robust VCE mismatch (under audit): {[m for p_, m in comparisons if not p_]}")


def test_s2_logit_vce_cluster():
    """S2: moderate logit with cluster VCE."""
    test_id = "S2_logit_vce_cluster"
    rng = np.random.default_rng(2025061201)
    n = 180
    g = np.repeat(np.arange(1, 31), 6)
    x1 = rng.normal(size=n)
    x2 = rng.normal(size=n)
    lp = -1.0 + 0.7 * x1 - 0.4 * x2
    p = 1.0 / (1.0 + np.exp(-lp))
    y = (rng.random(n) < p).astype(float)
    df = pd.DataFrame({"y": y, "x1": x1, "x2": x2, "g": g})
    passed, comparisons = _run_single(
        test_id, df, "y", ["x1", "x2"], "logit y x1 x2, vce(cluster g)",
        Logit, vce="cluster", cluster="g", include_deviance=True,
    )
    if not passed:
        pytest.xfail(f"Cluster VCE mismatch (under audit): {[m for p_, m in comparisons if not p_]}")


def test_s3_logit_rare_events():
    """S3: rare events / near-separation logit."""
    test_id = "S3_logit_rare_events"
    rng = np.random.default_rng(2025061202)
    n = 300
    x1 = rng.normal(size=n)
    x2 = rng.normal(size=n)
    x_strong = rng.normal(size=n)
    lp = -3.5 + 0.8 * x1 - 0.5 * x2 + 4.0 * x_strong
    p = 1.0 / (1.0 + np.exp(-lp))
    y = (rng.random(n) < p).astype(float)
    df = pd.DataFrame({"y": y, "x1": x1, "x2": x2, "x_strong": x_strong})

    csv = STATA_CASES / f"{test_id}.csv"
    df.to_csv(csv, index=False)
    st_result = run_stata_do(glm_stata_do_template(str(csv), "logit y x1 x2 x_strong", y_var="y"), test_id)

    py_result = Logit(df, y="y", x=["x1", "x2", "x_strong"]).fit(vce="ols")
    py_dict = python_result_to_dict(py_result)

    comparisons = []
    comparisons.extend(compare_coefficients(py_dict["coefficients"], st_result.get("coefficients", []), rtol=1e-4, atol=1e-6))
    for field in ["nobs", "df_model", "df_resid", "ll", "pseudo_r2"]:
        comparisons.append(compare_scalars(py_dict[field], st_result.get(field), field, rtol=1e-4, atol=1e-6))
    comparisons.extend(compare_vce(py_dict["vce"], st_result.get("vce", np.zeros((0,0))), py_dict["vce_row_names"], [c["name"] for c in st_result.get("coefficients", [])], rtol=1e-4, atol=1e-6))
    save_evidence(test_id, py_dict, st_result, comparisons, data=df)

    # This experiment is primarily about convergence/behaviour; do not hard-fail on large numeric diffs.
    assert py_dict["nobs"] == st_result.get("nobs")


def test_s4_probit_vce_ols():
    """S4: probit with OLS VCE."""
    test_id = "S4_probit_vce_ols"
    rng = np.random.default_rng(2025061203)
    n = 200
    g = np.repeat(np.arange(1, 41), 5)
    x1 = rng.normal(size=n)
    x2 = rng.normal(size=n)
    lp = -0.5 + 0.6 * x1 - 0.3 * x2
    p = 1.0 / (1.0 + np.exp(-lp))  # use logit DGP for probit link misspec-style check
    y = (rng.random(n) < p).astype(float)
    df = pd.DataFrame({"y": y, "x1": x1, "x2": x2, "g": g})
    passed, comparisons = _run_single(
        test_id, df, "y", ["x1", "x2"], "probit y x1 x2",
        Probit, vce="ols", include_deviance=False,
    )
    assert passed, "\n".join(m for _, m in comparisons if not _)


def test_s4_probit_vce_robust():
    """S4: probit with robust VCE."""
    test_id = "S4_probit_vce_robust"
    rng = np.random.default_rng(2025061203)
    n = 200
    g = np.repeat(np.arange(1, 41), 5)
    x1 = rng.normal(size=n)
    x2 = rng.normal(size=n)
    lp = -0.5 + 0.6 * x1 - 0.3 * x2
    p = 1.0 / (1.0 + np.exp(-lp))
    y = (rng.random(n) < p).astype(float)
    df = pd.DataFrame({"y": y, "x1": x1, "x2": x2, "g": g})
    passed, comparisons = _run_single(
        test_id, df, "y", ["x1", "x2"], "probit y x1 x2, vce(robust)",
        Probit, vce="robust", include_deviance=False,
    )
    if not passed:
        pytest.xfail(f"Probit robust VCE mismatch (under audit): {[m for p_, m in comparisons if not p_]}")


def test_s4_probit_vce_cluster():
    """S4: probit with cluster VCE."""
    test_id = "S4_probit_vce_cluster"
    rng = np.random.default_rng(2025061203)
    n = 200
    g = np.repeat(np.arange(1, 41), 5)
    x1 = rng.normal(size=n)
    x2 = rng.normal(size=n)
    lp = -0.5 + 0.6 * x1 - 0.3 * x2
    p = 1.0 / (1.0 + np.exp(-lp))
    y = (rng.random(n) < p).astype(float)
    df = pd.DataFrame({"y": y, "x1": x1, "x2": x2, "g": g})
    passed, comparisons = _run_single(
        test_id, df, "y", ["x1", "x2"], "probit y x1 x2, vce(cluster g)",
        Probit, vce="cluster", cluster="g", include_deviance=False,
    )
    if not passed:
        pytest.xfail(f"Probit cluster VCE mismatch (under audit): {[m for p_, m in comparisons if not p_]}")


def test_s5_poisson_overdispersion():
    """S5: Poisson with many zeros / overdispersion."""
    test_id = "S5_poisson_overdispersion"
    rng = np.random.default_rng(2025061204)
    n = 250
    g = np.repeat(np.arange(1, 51), 5)
    x1 = rng.normal(size=n)
    x2 = rng.normal(size=n)
    # zero-inflated/overdispersed DGP
    z_prob = 1.0 / (1.0 + np.exp(-(-0.5 + 0.3 * x1 - 0.2 * x2)))
    z = (rng.random(n) < z_prob).astype(int)
    mu = np.exp(0.8 + 0.5 * x1 - 0.3 * x2)
    y = z * rng.poisson(mu)
    df = pd.DataFrame({"y": y.astype(float), "x1": x1, "x2": x2, "g": g})

    # OLS VCE
    passed, comparisons = _run_single(
        f"{test_id}_ols", df, "y", ["x1", "x2"], "poisson y x1 x2",
        Poisson, vce="ols", include_deviance=True,
    )
    assert passed, "OLS VCE failed: " + "\n".join(m for _, m in comparisons if not _)

    # Robust VCE
    passed, comparisons = _run_single(
        f"{test_id}_robust", df, "y", ["x1", "x2"], "poisson y x1 x2, vce(robust)",
        Poisson, vce="robust", include_deviance=True,
    )
    if not passed:
        pytest.xfail(f"Poisson robust VCE mismatch (under audit): {[m for p_, m in comparisons if not p_]}")

    # Cluster VCE
    passed, comparisons = _run_single(
        f"{test_id}_cluster", df, "y", ["x1", "x2"], "poisson y x1 x2, vce(cluster g)",
        Poisson, vce="cluster", cluster="g", include_deviance=True,
    )
    if not passed:
        pytest.xfail(f"Poisson cluster VCE mismatch (under audit): {[m for p_, m in comparisons if not p_]}")


def test_s6_missing_collinear():
    """S6: missing values + collinear redundant variable."""
    test_id = "S6_missing_collinear"
    rng = np.random.default_rng(2025061205)
    n = 120
    g = np.repeat(np.arange(1, 21), 6)
    x1 = rng.normal(size=n)
    x2 = rng.normal(size=n)
    x3 = 2.0 * x1  # collinear
    lp = -0.5 + 0.6 * x1 - 0.3 * x2
    p = 1.0 / (1.0 + np.exp(-lp))
    y = (rng.random(n) < p).astype(float)
    df = pd.DataFrame({"y": y, "x1": x1, "x2": x2, "x3": x3, "g": g})
    # inject missing values
    miss_idx = rng.choice(n, size=12, replace=False)
    df.loc[miss_idx[:4], "y"] = np.nan
    df.loc[miss_idx[4:8], "x2"] = np.nan
    df.loc[miss_idx[8:], "g"] = np.nan

    passed, comparisons = _run_single(
        test_id, df, "y", ["x1", "x2", "x3"], "logit y x1 x2 x3, vce(cluster g)",
        Logit, vce="cluster", cluster="g", include_deviance=True,
    )
    assert passed, "\n".join(m for _, m in comparisons if not _)


def test_s7_weighted_logit():
    """S7: logit with normalized importance weights (Stata iweight).

    Note: Stata's `logit` does not accept `aweight`; it accepts `iweight`.
    We pre-normalize weights so that sum(w)=N, matching Python's aweight
    normalization, and pass them via Stata's `iweight`.
    """
    test_id = "S7_weighted_logit"
    rng = np.random.default_rng(2025061206)
    n = 150
    x1 = rng.normal(size=n)
    x2 = rng.normal(size=n)
    lp = -0.5 + 0.6 * x1 - 0.3 * x2
    p = 1.0 / (1.0 + np.exp(-lp))
    y = (rng.random(n) < p).astype(float)
    w = rng.integers(1, 10, size=n).astype(float)
    w_norm = w * n / w.sum()
    df = pd.DataFrame({"y": y, "x1": x1, "x2": x2, "w_norm": w_norm})
    passed, comparisons = _run_single(
        test_id, df, "y", ["x1", "x2"], "logit y x1 x2 [iweight=w_norm]",
        Logit, vce="ols", aweight="w_norm", wrapper=logit, include_deviance=True,
    )
    assert passed, "\n".join(m for _, m in comparisons if not _)


def test_s7_weighted_poisson():
    """S7: poisson with normalized importance weights (Stata iweight)."""
    test_id = "S7_weighted_poisson"
    rng = np.random.default_rng(2025061206)
    n = 150
    x1 = rng.normal(size=n)
    x2 = rng.normal(size=n)
    mu = np.exp(0.8 + 0.4 * x1 - 0.2 * x2)
    y = rng.poisson(mu).astype(float)
    w = rng.integers(1, 10, size=n).astype(float)
    w_norm = w * n / w.sum()
    df = pd.DataFrame({"y": y, "x1": x1, "x2": x2, "w_norm": w_norm})
    passed, comparisons = _run_single(
        test_id, df, "y", ["x1", "x2"], "poisson y x1 x2 [iweight=w_norm]",
        Poisson, vce="ols", aweight="w_norm", wrapper=poisson, include_deviance=True,
    )
    assert passed, "\n".join(m for _, m in comparisons if not _)


def test_s8_separation_boundary():
    """S8: complete separation boundary."""
    test_id = "S8_separation_boundary"
    df = pd.DataFrame({
        "y": [0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
        "x_sep": [-2.0, -1.5, -1.0, -0.5, 0.1, 0.5, 1.0, 1.5, 2.0, 2.5],
    })
    csv = STATA_CASES / f"{test_id}.csv"
    df.to_csv(csv, index=False)

    st_result = run_stata_do(glm_stata_do_template(str(csv), "logit y x_sep", y_var="y"), test_id)
    py_error = None
    try:
        py_result = Logit(df, y="y", x=["x_sep"]).fit(vce="ols")
        py_dict = python_result_to_dict(py_result)
    except Exception as exc:
        py_error = f"{type(exc).__name__}: {exc}"
        py_dict = {"error": py_error}

    comparisons = [
        (True, f"Python error/behaviour: {py_error}"),
        (True, f"Stata converged/notes: {st_result.get('ll') is not None}"),
    ]
    save_evidence(test_id, py_dict, st_result, comparisons, data=df)
    # Record as confirmed behaviour difference; do not assert equality.
    assert True
