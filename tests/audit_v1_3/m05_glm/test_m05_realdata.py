"""M05 GLM: real-data dual-run experiments."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent))
from m05_audit_utils import (
    STATA_CASES,
    glm_stata_do_webuse_template,
    run_stata_do,
    python_result_to_dict,
    compare_scalars,
    compare_coefficients,
    compare_vce,
    save_evidence,
)

from stataflow.compat.stata import logit, probit, poisson


def _run_webuse(
    test_id: str,
    dataset_load: str,
    command: str,
    y: str,
    x: list[str],
    py_func,
    vce: str = "ols",
    cluster: str | None = None,
    include_deviance: bool = True,
    rtol: float = 1e-6,
    atol: float = 1e-6,
):
    csv_out = STATA_CASES / f"{test_id}.csv"
    st_result = run_stata_do(
        glm_stata_do_webuse_template(
            dataset_load, command, y_var=y, include_deviance=include_deviance, export_csv=str(csv_out)
        ),
        test_id,
    )

    df = pd.read_csv(csv_out)
    # Preserve Stata missing codes if any; drop rows with missing in y/x/cluster.
    py_result = py_func(df, y=y, x=x, vce=vce, cluster=cluster)
    py_dict = python_result_to_dict(py_result)

    comparisons = []
    comparisons.extend(compare_coefficients(py_dict["coefficients"], st_result.get("coefficients", []), rtol=rtol, atol=atol))
    scalar_fields = ["nobs", "df_model", "ll", "pseudo_r2"]
    if cluster is None:
        scalar_fields.append("df_resid")
    if vce == "ols":
        scalar_fields.extend(["chi2", "chi2_pvalue"])
    for field in scalar_fields:
        comparisons.append(compare_scalars(py_dict[field], st_result.get(field), field, rtol=rtol, atol=atol))
    if include_deviance and py_dict.get("deviance") is not None:
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


def test_r1_mroz_logit_robust():
    """R1: Mroz data logit with robust VCE."""
    test_id = "R1_mroz_logit_robust"
    passed, comparisons = _run_webuse(
        test_id,
        dataset_load="mroz",
        command="logit inlf age educ kidslt6 kidsge6, vce(robust)",
        y="inlf",
        x=["age", "educ", "kidslt6", "kidsge6"],
        py_func=logit,
        vce="robust",
        include_deviance=True,
    )
    assert passed, "\n".join(m for _, m in comparisons if not _)


def test_r1_mroz_probit_robust():
    """R1: Mroz data probit with robust VCE."""
    test_id = "R1_mroz_probit_robust"
    passed, comparisons = _run_webuse(
        test_id,
        dataset_load="mroz",
        command="probit inlf age educ kidslt6 kidsge6, vce(robust)",
        y="inlf",
        x=["age", "educ", "kidslt6", "kidsge6"],
        py_func=probit,
        vce="robust",
        include_deviance=False,
    )
    assert passed, "\n".join(m for _, m in comparisons if not _)


def test_r2_fish_poisson_robust():
    """R2: Fish data Poisson with robust VCE (overdispersion)."""
    test_id = "R2_fish_poisson_robust"
    passed, comparisons = _run_webuse(
        test_id,
        dataset_load="fish",
        command="poisson count livebait camper persons child, vce(robust)",
        y="count",
        x=["livebait", "camper", "persons", "child"],
        py_func=poisson,
        vce="robust",
        include_deviance=True,
    )
    assert passed, "\n".join(m for _, m in comparisons if not _)


def test_r3_nlsw88_logit_cluster():
    """R3: NLSW88 logit with industry cluster."""
    test_id = "R3_nlsw88_logit_cluster"
    passed, comparisons = _run_webuse(
        test_id,
        dataset_load="sysuse nlsw88",
        command="logit collgrad age grade tenure married smsa, vce(cluster industry)",
        y="collgrad",
        x=["age", "grade", "tenure", "married", "smsa"],
        py_func=logit,
        vce="cluster",
        cluster="industry",
        include_deviance=True,
        rtol=1e-4,
        atol=1e-4,
    )
    assert passed, "\n".join(m for _, m in comparisons if not _)


def test_r4_ovary_poisson_cluster():
    """R4: Ovary data Poisson with mare cluster."""
    test_id = "R4_ovary_poisson_cluster"
    passed, comparisons = _run_webuse(
        test_id,
        dataset_load="ovary",
        command="poisson follicles sin1 cos1 stime, vce(cluster mare)",
        y="follicles",
        x=["sin1", "cos1", "stime"],
        py_func=poisson,
        vce="cluster",
        cluster="mare",
        include_deviance=True,
    )
    assert passed, "\n".join(m for _, m in comparisons if not _)
