"""Standalone reproduction script for confirmed M08 RD audit findings.

Run with:
    python tests/audit_v1_3/m08_rd/repro_m08_rd_findings.py

The script re-runs the minimal dual-run experiments that produced confirmed
findings and writes JSON evidence to
`docs/audit/modular-revalidation-v1.3/M08-rd/evidence/minimal-reproductions/`.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

# Allow running this script directly from repo root.
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from stataflow.compat.stata import rdrobust
from tests.audit_v1_3.m08_rd.m08_audit_utils import (
    rdrobust_stata_do,
    run_stata_rd,
    compare_python_to_stata,
    save_evidence,
)
from tests.audit_v1_3.m08_rd.test_m08_synthetic import _make_s3_covariates


def reproduce_finding_covariate_bandwidth():
    """Re-run S3 covariate-adjusted RD to demonstrate Stata-vs-Python alignment."""
    data = _make_s3_covariates(seed=2026062003)
    prefix = "REPRO_S3_COVARIATES"
    do = rdrobust_stata_do("{dta}", "y", "x", c=0.0, bwselect="mserd", covs="z")
    st = run_stata_rd(data, prefix, do)
    py = rdrobust(data, y="y", x="x", c=0.0, bwselect="mserd", covs="z")
    diffs = compare_python_to_stata(
        py,
        st,
        fields=["nobs", "n_l", "n_r", "n_h_l", "n_h_r", "h_l", "h_r"],
    )
    save_evidence(prefix, py, st, diffs)
    print(f"{prefix}: passed={diffs['passed']}")
    for msg in diffs["messages"]:
        print("  ", msg)


def reproduce_finding_cluster_vce():
    """Re-run S4 cluster VCE to demonstrate Stata-vs-Python alignment."""
    from tests.audit_v1_3.m08_rd.test_m08_synthetic import _make_s4_cluster

    data = _make_s4_cluster(seed=2026062004)
    prefix = "REPRO_S4_CLUSTER_VCE"
    do = rdrobust_stata_do(
        "{dta}", "y", "x", c=0.0, bwselect="mserd", vce="cluster", cluster="g"
    )
    st = run_stata_rd(data, prefix, do)
    py = rdrobust(
        data, y="y", x="x", c=0.0, bwselect="mserd", vce="cluster", cluster="g"
    )
    diffs = compare_python_to_stata(
        py,
        st,
        fields=["nobs", "n_l", "n_r", "n_h_l", "n_h_r", "h_l", "h_r"],
    )
    save_evidence(prefix, py, st, diffs)
    print(f"{prefix}: passed={diffs['passed']}")
    for msg in diffs["messages"]:
        print("  ", msg)


if __name__ == "__main__":
    reproduce_finding_covariate_bandwidth()
    reproduce_finding_cluster_vce()
