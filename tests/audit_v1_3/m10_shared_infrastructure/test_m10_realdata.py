"""M10 Shared Infrastructure - real-data experiments.

Both experiments use publicly redistributable datasets already present in the
repository's ``research/data/public`` directory.
"""

from __future__ import annotations

import datetime

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


class TestR01Vote1FactorInteraction:
    """Factor variables on a real electoral dataset."""

    def test_r01_factor_on_vote1(self):
        df = pd.read_csv("research/data/public/binary/oos/vote1.csv")
        stata_cmd = "regress voteA i.democA##c.lexpendA"
        log, _ = run_stata_do(df, "m10_r01", build_regression_do(stata_cmd))
        st = parse_stata_log_fields(log)
        py_res = regress(df, "voteA", ["i.democA##c.lexpendA"])
        py = extract_python_result(py_res)

        scalars = compare_dict_of_scalars(
            py, st["scalars"], ["nobs", "df_model", "df_resid", "r2", "rss"], rtol=RTOL, atol=ATOL
        )
        coefs = compare_coefficients(py, st, rtol=RTOL, atol=ATOL)
        vce = compare_vce(py, st, rtol=RTOL, atol=ATOL)

        save_evidence_json(
            {
                "test_id": "M10-R01",
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "data_source": "research/data/public/binary/oos/vote1.csv",
                "data_hash": hash_dataframe(df),
                "stata_command": stata_cmd,
                "python_call": "regress(df, 'voteA', ['i.democA##c.lexpendA'])",
                "scalars_comparison": scalars,
                "coefficients_comparison": coefs,
                "vce_comparison": vce,
            },
            category="real-data",
            test_id="M10-R01",
        )
        assert scalars["passed"], "\n".join(scalars["messages"])
        assert coefs["passed"], "\n".join(coefs["messages"])
        assert vce["passed"], "\n".join(vce["messages"])


class TestR02JTrainSampleMask:
    """Missing-value sample mask on a real panel with many missing outcomes."""

    def test_r02_jtrain_mask(self):
        df = pd.read_stata("research/data/public/did/jtrain_prepared.dta")
        stata_cmd = "regress lscrap grant i.year, cluster(fcode)"
        do = build_regression_do(stata_cmd, sample_dta="m10_r02_sample")
        log, _ = run_stata_do(df, "m10_r02", do)
        st = parse_stata_log_fields(log)
        sample_df = pd.read_stata(STATA_OUTPUT_DIR / "m10_r02_sample.dta")
        st_mask = [int(v) for v in sample_df["__sample"]]

        py_res = regress(df, "lscrap", ["grant", "i.year"], vce="cluster", cluster="fcode")
        py = extract_python_result(py_res)
        py_mask = py["sample_mask"]

        scalars = compare_dict_of_scalars(
            py, st["scalars"], ["nobs", "df_model", "df_resid", "n_clust"], rtol=RTOL, atol=ATOL
        )
        coefs = compare_coefficients(py, st, rtol=RTOL, atol=ATOL)
        vce = compare_vce(py, st, rtol=RTOL, atol=ATOL)
        mask_ok = py_mask == st_mask and sum(py_mask) == py["nobs"]

        save_evidence_json(
            {
                "test_id": "M10-R02",
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "data_source": "research/data/public/did/jtrain_prepared.dta",
                "data_hash": hash_dataframe(df),
                "stata_command": stata_cmd,
                "python_call": "regress(df, 'lscrap', ['grant','i.year'], vce='cluster', cluster='fcode')",
                "scalars_comparison": scalars,
                "coefficients_comparison": coefs,
                "vce_comparison": vce,
                "sample_mask_equal": mask_ok,
            },
            category="real-data",
            test_id="M10-R02",
        )
        assert scalars["passed"], "\n".join(scalars["messages"])
        assert coefs["passed"], "\n".join(coefs["messages"])
        assert vce["passed"], "\n".join(vce["messages"])
        assert mask_ok, f"sample mask mismatch: py sum={sum(py_mask)}, st sum={sum(st_mask)}"
