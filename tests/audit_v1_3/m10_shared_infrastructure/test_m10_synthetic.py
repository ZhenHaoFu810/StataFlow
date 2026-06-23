"""M10 Shared Infrastructure - synthetic dual-run experiments.

These tests exercise shared components (factor parser, VCE utilities, sample
mask, StataRunner, ResultSchema) through the linear-regression consumer.  They
are not a repetition of existing ``tests/golden`` designs; DGPs, seeds and
specifications are new for the v1.3 modular audit.
"""

from __future__ import annotations

import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from stataflow.compat.stata.linear import regress
from tests.audit_v1_3.m10_shared_infrastructure.m10_audit_utils import (
    build_regression_do,
    compare_coefficients,
    compare_dict_of_scalars,
    compare_vce,
    extract_python_result,
    hash_dataframe,
    parse_stata_log_fields,
    run_stata_do,
    save_evidence_json,
    STATA_OUTPUT_DIR,
)


RTOL = 1e-6
ATOL = 1e-8


def _make_factor_dgp(seed: int, n: int = 200) -> pd.DataFrame:
    """DGP with categorical-continuous interaction."""
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({
        "x": rng.normal(size=n),
        "g": rng.integers(1, 4, size=n),
    })
    df["y"] = (
        1.0
        + 2.0 * df["x"]
        + 3.0 * (df["g"] == 2)
        + 4.0 * (df["g"] == 3)
        + 5.0 * df["x"] * (df["g"] == 2)
        + 6.0 * df["x"] * (df["g"] == 3)
        + rng.normal(size=n)
    )
    return df


def _save_evidence(
    test_id: str,
    df: pd.DataFrame,
    stata_cmd: str,
    py_call: str,
    py: dict,
    st: dict,
    scalars: dict,
    coefs: dict,
    vce: dict,
    sample_equal: bool | None = None,
) -> None:
    save_evidence_json(
        {
            "test_id": test_id,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "data_hash": hash_dataframe(df),
            "stata_command": stata_cmd,
            "python_call": py_call,
            "stata_scalars": st.get("scalars", {}),
            "python_scalars": {k: v for k, v in py.items() if k not in ("vce", "coefficients", "sample_mask", "coef_names")},
            "scalars_comparison": scalars,
            "coefficients_comparison": coefs,
            "vce_comparison": vce,
            "sample_mask_equal": sample_equal,
        },
        category="synthetic",
        test_id=test_id,
    )


class TestS01FactorVariableExpansion:
    """Factor variable parser: base levels, interactions and coefficient names."""

    def test_s01_factor_interaction_matches_stata(self):
        df = _make_factor_dgp(seed=701, n=200)
        stata_cmd = "regress y i.g##c.x"
        log, _ = run_stata_do(df, "m10_s01", build_regression_do(stata_cmd))
        st = parse_stata_log_fields(log)
        py_res = regress(df, "y", ["i.g##c.x"])
        py = extract_python_result(py_res)

        scalars = compare_dict_of_scalars(
            py, st["scalars"], ["nobs", "df_model", "df_resid", "r2", "rss"], rtol=RTOL, atol=ATOL
        )
        coefs = compare_coefficients(py, st, rtol=RTOL, atol=ATOL)
        vce = compare_vce(py, st, rtol=RTOL, atol=ATOL)

        _save_evidence(
            "M10-S01", df, stata_cmd,
            "regress(df, 'y', ['i.g##c.x'])", py, st, scalars, coefs, vce
        )
        assert scalars["passed"], "\n".join(scalars["messages"])
        assert coefs["passed"], "\n".join(coefs["messages"])
        assert vce["passed"], "\n".join(vce["messages"])


class TestS02RobustVCE:
    """Shared robust (HC) VCE: complete matrix comparison under heteroskedasticity."""

    def test_s02_robust_vce_matrix(self):
        rng = np.random.default_rng(702)
        n = 120
        df = pd.DataFrame({
            "x": rng.normal(size=n),
            "z": rng.normal(size=n),
        })
        df["y"] = 1.0 + 2.0 * df["x"] + 1.5 * df["z"] + df["z"] * rng.normal(size=n)

        stata_cmd = "regress y x z, robust"
        log, _ = run_stata_do(df, "m10_s02", build_regression_do(stata_cmd))
        st = parse_stata_log_fields(log)
        py_res = regress(df, "y", ["x", "z"], vce="robust")
        py = extract_python_result(py_res)

        scalars = compare_dict_of_scalars(
            py, st["scalars"], ["nobs", "df_model", "df_resid", "r2"], rtol=RTOL, atol=ATOL
        )
        coefs = compare_coefficients(py, st, rtol=RTOL, atol=ATOL)
        vce = compare_vce(py, st, rtol=RTOL, atol=ATOL)

        _save_evidence(
            "M10-S02", df, stata_cmd,
            "regress(df, 'y', ['x','z'], vce='robust')", py, st, scalars, coefs, vce
        )
        assert scalars["passed"], "\n".join(scalars["messages"])
        assert coefs["passed"], "\n".join(coefs["messages"])
        assert vce["passed"], "\n".join(vce["messages"])


class TestS03ClusterVCESingleton:
    """Cluster VCE small-sample behaviour with a singleton cluster."""

    def test_s03_cluster_singleton_retained(self):
        rng = np.random.default_rng(703)
        n = 80
        df = pd.DataFrame({"x": rng.normal(size=n)})
        df["cid"] = rng.integers(1, 11, size=n)
        df.loc[0, "cid"] = 99  # singleton cluster
        df["y"] = (
            1.0
            + 2.0 * df["x"]
            + df.groupby("cid")["x"].transform(lambda s: rng.normal() * len(s))
            + rng.normal(size=n)
        )

        stata_cmd = "regress y x, cluster(cid)"
        log, _ = run_stata_do(df, "m10_s03", build_regression_do(stata_cmd))
        st = parse_stata_log_fields(log)
        py_res = regress(df, "y", ["x"], vce="cluster", cluster="cid")
        py = extract_python_result(py_res)

        scalars = compare_dict_of_scalars(
            py, st["scalars"], ["nobs", "df_model", "df_resid", "n_clust"], rtol=RTOL, atol=ATOL
        )
        coefs = compare_coefficients(py, st, rtol=RTOL, atol=ATOL)
        vce = compare_vce(py, st, rtol=RTOL, atol=ATOL)

        _save_evidence(
            "M10-S03", df, stata_cmd,
            "regress(df, 'y', ['x'], vce='cluster', cluster='cid')", py, st, scalars, coefs, vce
        )
        assert scalars["passed"], "\n".join(scalars["messages"])
        assert coefs["passed"], "\n".join(coefs["messages"])
        assert vce["passed"], "\n".join(vce["messages"])


class TestS04SampleMask:
    """Sample mask maps correctly to Stata ``e(sample)`` with missing values."""

    def test_s04_missing_screening_mask(self):
        rng = np.random.default_rng(704)
        n = 60
        df = pd.DataFrame({
            "x": rng.normal(size=n),
            "z": rng.normal(size=n),
            "cid": rng.integers(1, 6, size=n),
        })
        # Inject missing values in different rows.
        df.loc[5, "y"] = np.nan
        df.loc[10, "x"] = np.nan
        df.loc[15, "z"] = np.nan
        df["y"] = 1.0 + 2.0 * df["x"].fillna(0) + 3.0 * df["z"].fillna(0) + rng.normal(size=n)

        stata_cmd = "regress y x z, cluster(cid)"
        do = build_regression_do(stata_cmd, sample_dta="m10_s04_sample")
        log, _ = run_stata_do(df, "m10_s04", do)
        st = parse_stata_log_fields(log)
        sample_df = pd.read_stata(STATA_OUTPUT_DIR / "m10_s04_sample.dta")
        st_mask = [int(v) for v in sample_df["__sample"]]

        py_res = regress(df, "y", ["x", "z"], vce="cluster", cluster="cid")
        py = extract_python_result(py_res)
        py_mask = py["sample_mask"]

        scalars = compare_dict_of_scalars(
            py, st["scalars"], ["nobs", "df_model", "df_resid", "n_clust"], rtol=RTOL, atol=ATOL
        )
        coefs = compare_coefficients(py, st, rtol=RTOL, atol=ATOL)
        vce = compare_vce(py, st, rtol=RTOL, atol=ATOL)
        mask_ok = py_mask == st_mask and sum(py_mask) == py["nobs"]

        _save_evidence(
            "M10-S04", df, stata_cmd,
            "regress(df, 'y', ['x','z'], vce='cluster', cluster='cid')",
            py, st, scalars, coefs, vce, sample_equal=mask_ok
        )
        assert scalars["passed"], "\n".join(scalars["messages"])
        assert coefs["passed"], "\n".join(coefs["messages"])
        assert vce["passed"], "\n".join(vce["messages"])
        assert mask_ok, f"sample mask mismatch: py sum={sum(py_mask)}, st sum={sum(st_mask)}"


class TestS05StataRunner:
    """StataRunner handles non-ASCII paths and reports command errors."""

    def test_s05_path_with_spaces_and_unicode(self):
        rng = np.random.default_rng(705)
        n = 30
        df = pd.DataFrame({"y": rng.normal(size=n), "x": rng.normal(size=n)})
        output_dir = Path("stata/output/m10_audit/子目录 with spaces")
        output_dir.mkdir(parents=True, exist_ok=True)
        dta_path = (output_dir / "data.dta").resolve()
        df.to_stata(str(dta_path), write_index=False)

        do = (
            f'version 17\nset more off\nuse "{dta_path}" , clear\n'
            "regress y x\ndisplay \"E_N=\" e(N)"
        )
        from stataflow.stata_runner import StataRunner
        result = StataRunner().run_do_file(do, output_dir=str(output_dir), timeout=60)
        assert result.exit_code == 0
        assert result.output_content is not None
        assert "E_N=" in result.output_content

    def test_s05_invalid_command_logged(self):
        rng = np.random.default_rng(705)
        n = 30
        df = pd.DataFrame({"y": rng.normal(size=n), "x": rng.normal(size=n)})
        output_dir = Path("stata/output/m10_audit")
        dta_path = (output_dir / "s05_data.dta").resolve()
        df.to_stata(str(dta_path), write_index=False)

        do = (
            f'version 17\nset more off\nuse "{dta_path}" , clear\n'
            "regress y nonexistent_var"
        )
        from stataflow.stata_runner import StataRunner
        result = StataRunner().run_do_file(do, output_dir=str(output_dir), timeout=60)
        assert result.output_content is not None
        assert "not found" in result.output_content.lower() or "r(111)" in result.output_content


class TestS06Collinearity:
    """Collinearity screening drops redundant columns and preserves dimensions."""

    def test_s06_perfect_collinearity(self):
        rng = np.random.default_rng(706)
        n = 40
        df = pd.DataFrame({"x1": rng.normal(size=n)})
        df["x2"] = df["x1"]  # perfect collinearity
        df["y"] = 1.0 + 2.0 * df["x1"] + rng.normal(size=n)

        stata_cmd = "regress y x1 x2"
        log, _ = run_stata_do(df, "m10_s06", build_regression_do(stata_cmd))
        st = parse_stata_log_fields(log)
        py_res = regress(df, "y", ["x1", "x2"])
        py = extract_python_result(py_res)

        scalars = compare_dict_of_scalars(
            py, st["scalars"], ["nobs", "df_model", "df_resid", "r2"], rtol=RTOL, atol=ATOL
        )
        coefs = compare_coefficients(py, st, rtol=RTOL, atol=ATOL)
        vce = compare_vce(py, st, rtol=RTOL, atol=ATOL)

        _save_evidence(
            "M10-S06", df, stata_cmd,
            "regress(df, 'y', ['x1','x2'])", py, st, scalars, coefs, vce
        )
        assert scalars["passed"], "\n".join(scalars["messages"])
        assert coefs["passed"], "\n".join(coefs["messages"])
        assert vce["passed"], "\n".join(vce["messages"])


class TestS07ConstantOnly:
    """Empty regressor list produces a valid constant-only ResultSchema."""

    def test_s07_constant_only_model(self):
        rng = np.random.default_rng(707)
        n = 30
        df = pd.DataFrame({"y": rng.normal(size=n, loc=5.0, scale=2.0)})

        stata_cmd = "regress y"
        log, _ = run_stata_do(df, "m10_s07", build_regression_do(stata_cmd))
        st = parse_stata_log_fields(log)
        py_res = regress(df, "y", [])
        py = extract_python_result(py_res)

        scalars = compare_dict_of_scalars(
            py, st["scalars"], ["nobs", "df_model", "df_resid", "r2"], rtol=RTOL, atol=ATOL
        )
        coefs = compare_coefficients(py, st, rtol=RTOL, atol=ATOL)
        vce = compare_vce(py, st, rtol=RTOL, atol=ATOL)

        _save_evidence(
            "M10-S07", df, stata_cmd,
            "regress(df, 'y', [])", py, st, scalars, coefs, vce
        )
        assert scalars["passed"], "\n".join(scalars["messages"])
        assert coefs["passed"], "\n".join(coefs["messages"])
        assert vce["passed"], "\n".join(vce["messages"])
