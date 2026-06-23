"""M10 Shared Infrastructure - metamorphic / property tests.

These tests check invariants that shared infrastructure should satisfy,
using both Python results and a Stata reference where practical.
"""

from __future__ import annotations

import datetime

import numpy as np
import pandas as pd
import pytest

from stataflow.compat.stata.linear import regress
from tests.audit_v1_3.m10_shared_infrastructure.m10_audit_utils import (
    build_regression_do,
    extract_python_result,
    hash_dataframe,
    parse_stata_log_fields,
    run_stata_do,
    save_evidence_json,
)

RTOL = 1e-6
ATOL = 1e-8


def _close(a: float, b: float, name: str = "value") -> None:
    diff = abs(a - b)
    rel = diff / max(abs(b), 1e-12)
    assert diff <= ATOL or rel <= RTOL, f"{name}: {a} vs {b} (rel={rel:.2e})"


def _run_python_reference(seed: int) -> dict:
    rng = np.random.default_rng(seed)
    n = 100
    df = pd.DataFrame({
        "x": rng.normal(size=n),
        "z": rng.normal(size=n),
        "g": rng.integers(1, 4, size=n),
        "cid": rng.integers(1, 8, size=n),
    })
    df["y"] = (
        1.0
        + 2.0 * df["x"]
        + 1.5 * df["z"]
        + 3.0 * (df["g"] == 2)
        + df.groupby("cid")["x"].transform(lambda s: rng.normal() * len(s))
        + rng.normal(size=n)
    )
    result = regress(df, "y", ["i.g##c.x", "z"], vce="cluster", cluster="cid")
    return extract_python_result(result), df


class TestP01RowOrderInvariance:
    """Shuffling input rows must not change estimation results."""

    def test_p01_shuffle_rows(self):
        py_base, df = _run_python_reference(801)
        df_shuffled = df.sample(frac=1.0, random_state=123).reset_index(drop=True)
        result_shuffled = regress(
            df_shuffled, "y", ["i.g##c.x", "z"], vce="cluster", cluster="cid"
        )
        py_shuffled = extract_python_result(result_shuffled)

        # Coefficients and VCE must be identical after row shuffling.
        assert py_base["coef_names"] == py_shuffled["coef_names"]
        for name in py_base["coef_names"]:
            _close(py_base["coefficients"][name]["beta"], py_shuffled["coefficients"][name]["beta"], name)
            _close(py_base["coefficients"][name]["std_err"], py_shuffled["coefficients"][name]["std_err"], name)
        for key in py_base["vce"]:
            _close(py_base["vce"][key], py_shuffled["vce"][key], f"vce{key}")

        save_evidence_json(
            {
                "test_id": "M10-P01",
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "property": "row order invariance",
                "data_hash_base": hash_dataframe(df),
                "data_hash_shuffled": hash_dataframe(df_shuffled),
                "max_abs_diff_beta": max(
                    abs(py_base["coefficients"][n]["beta"] - py_shuffled["coefficients"][n]["beta"])
                    for n in py_base["coef_names"]
                ),
                "max_abs_diff_vce": max(
                    abs(py_base["vce"][k] - py_shuffled["vce"][k])
                    for k in py_base["vce"]
                ),
            },
            category="property",
            test_id="M10-P01",
        )


class TestP02IrrelevantColumnInvariance:
    """Adding an unused column must not change estimation results."""

    def test_p02_irrelevant_column(self):
        py_base, df = _run_python_reference(802)
        df_extra = df.copy()
        df_extra["noise"] = np.random.default_rng(802).normal(size=len(df_extra))
        result_extra = regress(
            df_extra, "y", ["i.g##c.x", "z"], vce="cluster", cluster="cid"
        )
        py_extra = extract_python_result(result_extra)

        assert py_base["nobs"] == py_extra["nobs"]
        assert py_base["coef_names"] == py_extra["coef_names"]
        for name in py_base["coef_names"]:
            _close(py_base["coefficients"][name]["beta"], py_extra["coefficients"][name]["beta"], name)
            _close(py_base["coefficients"][name]["std_err"], py_extra["coefficients"][name]["std_err"], name)

        save_evidence_json(
            {
                "test_id": "M10-P02",
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "property": "irrelevant column invariance",
                "data_hash_base": hash_dataframe(df),
                "data_hash_with_noise": hash_dataframe(df_extra),
                "max_abs_diff_beta": max(
                    abs(py_base["coefficients"][n]["beta"] - py_extra["coefficients"][n]["beta"])
                    for n in py_base["coef_names"]
                ),
            },
            category="property",
            test_id="M10-P02",
        )


class TestP03ClusterLabelPermutation:
    """Consistently permuting cluster labels must not change cluster VCE."""

    def test_p03_cluster_label_permutation(self):
        rng = np.random.default_rng(803)
        n = 100
        df = pd.DataFrame({
            "x": rng.normal(size=n),
            "cid": rng.integers(1, 10, size=n),
        })
        df["y"] = 1.0 + 2.0 * df["x"] + df.groupby("cid")["x"].transform(lambda s: rng.normal() * len(s)) + rng.normal(size=n)

        result = regress(df, "y", ["x"], vce="cluster", cluster="cid")
        py_base = extract_python_result(result)

        # Deterministic permutation of cluster labels.
        unique_cids = sorted(df["cid"].unique())
        perm = {c: i + 1000 for i, c in enumerate(unique_cids)}
        df_perm = df.copy()
        df_perm["cid"] = df_perm["cid"].map(perm)
        result_perm = regress(df_perm, "y", ["x"], vce="cluster", cluster="cid")
        py_perm = extract_python_result(result_perm)

        assert py_base["coef_names"] == py_perm["coef_names"]
        for name in py_base["coef_names"]:
            _close(py_base["coefficients"][name]["beta"], py_perm["coefficients"][name]["beta"], name)
            _close(py_base["coefficients"][name]["std_err"], py_perm["coefficients"][name]["std_err"], name)

        # Also confirm Stata produces identical results under the same permutation.
        log_orig, _ = run_stata_do(df, "m10_p03_orig", build_regression_do("regress y x, cluster(cid)"))
        st_orig = parse_stata_log_fields(log_orig)
        log_perm, _ = run_stata_do(df_perm, "m10_p03_perm", build_regression_do("regress y x, cluster(cid_perm)").replace("cid_perm", "cid"))
        st_perm = parse_stata_log_fields(log_perm)
        _close(st_orig["coefficients"]["x"]["beta"], st_perm["coefficients"]["x"]["beta"], "stata_x_beta")
        _close(st_orig["coefficients"]["x"]["std_err"], st_perm["coefficients"]["x"]["std_err"], "stata_x_se")

        save_evidence_json(
            {
                "test_id": "M10-P03",
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "property": "cluster label permutation invariance",
                "data_hash_base": hash_dataframe(df),
                "data_hash_permuted": hash_dataframe(df_perm),
                "python_x_se_base": py_base["coefficients"]["x"]["std_err"],
                "python_x_se_perm": py_perm["coefficients"]["x"]["std_err"],
                "stata_x_se_base": st_orig["coefficients"]["x"]["std_err"],
                "stata_x_se_perm": st_perm["coefficients"]["x"]["std_err"],
            },
            category="property",
            test_id="M10-P03",
        )
