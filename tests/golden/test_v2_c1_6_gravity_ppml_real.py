"""
C1.6 Gravity trade PPMLHDFE real-data golden test.

Stata ppmlhdfe example data: trade flows ~ distance + contiguity + FTA
with exporter, importer, year fixed effects (N=17,850).

NOTE: Stata ppmlhdfe always uses robust (sandwich) VCE by default.
Even specifying vce(ols) still reports vcetype=Robust. Python's vce="ols"
(Fisher information) cannot be directly compared to Stata's ppmlhdfe
output because Stata does not have a pure OLS VCE for PPML models.
Python vce="robust" and vce="cluster" match Stata correctly.
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from tests.golden.test_utils import (
    PROJECT_STATA_OUTPUT, PROJECT_STATA_CASES, StataRunner,
    tolerance_close, parse_stata_log_with_precise_coefs,
)
from stataflow import PPMLHDFE

PROJECT_ROOT = Path(__file__).parent.parent.parent
TRADE_DTA = PROJECT_ROOT / "research" / "vendor" / "stata_community" / "ppmlhdfe" / "ppmlhdfe-master" / "examples" / "EXAMPLE_TRADE_FTA_DATA.dta"


def _load_data():
    return pd.read_stata(TRADE_DTA)


def _run_stata(data: pd.DataFrame, vce_spec: str) -> dict:
    dta_file = PROJECT_STATA_CASES / f"c1_6_gravity_{vce_spec}_data.dta"
    data.to_stata(str(dta_file), write_index=False)

    if vce_spec == "cluster":
        vce_line = ", vce(cluster isoexp)"
    else:
        vce_line = ""  # Stata default = robust VCE

    do_template = f'''
clear all
set more off
use "{dta_file}", clear
ppmlhdfe trade ln_distw contig fta, absorb(isoexp isoimp year){vce_line}
display "E_N=" e(N)
display "B_LN_DISTW=" _b[ln_distw]
display "B_CONTIG=" _b[contig]
display "B_FTA=" _b[fta]
display "SE_LN_DISTW=" _se[ln_distw]
display "SE_CONTIG=" _se[contig]
display "SE_FTA=" _se[fta]
display "C1_6_GRAVITY_{vce_spec.upper()} completed"
'''
    runner = StataRunner()
    result = runner.run_do_file(do_template, output_dir=str(PROJECT_STATA_OUTPUT))
    if result.exit_code != 0:
        raise RuntimeError(f"Stata failed ({vce_spec}): {result.error_message}")
    return parse_stata_log_with_precise_coefs(result.output_content, coef_names=['ln_distw', 'contig', 'fta'])


class TestC16GravityPPML:
    @pytest.fixture(scope="class")
    def data(self):
        return _load_data()

    # Default VCE: Stata uses robust, Python uses robust
    @pytest.fixture(scope="class")
    def py_robust(self, data):
        return PPMLHDFE(data=data, y="trade", x=["ln_distw", "contig", "fta"],
                        absorb=["isoexp", "isoimp", "year"]).fit(vce="robust")

    @pytest.fixture(scope="class")
    def st_default(self, data):
        return _run_stata(data, "default")

    def test_default_beta(self, py_robust, st_default):
        for pc, sc in zip(py_robust.coefficients, st_default["coefficients"]):
            assert tolerance_close(pc.beta, sc["beta"], name=f"beta[{pc.name}]")[0]

    def test_default_se(self, py_robust, st_default):
        for pc, sc in zip(py_robust.coefficients, st_default["coefficients"]):
            assert tolerance_close(pc.std_err, sc["std_err"],
                                   name=f"se[{pc.name}]", rtol=1e-4)[0]

    # Cluster VCE
    @pytest.fixture(scope="class")
    def py_cluster(self, data):
        return PPMLHDFE(data=data, y="trade", x=["ln_distw", "contig", "fta"],
                        absorb=["isoexp", "isoimp", "year"]).fit(vce="cluster", cluster="isoexp")

    @pytest.fixture(scope="class")
    def st_cluster(self, data):
        return _run_stata(data, "cluster")

    def test_cluster_beta(self, py_cluster, st_cluster):
        for pc, sc in zip(py_cluster.coefficients, st_cluster["coefficients"]):
            assert tolerance_close(pc.beta, sc["beta"], name=f"beta[{pc.name}]")[0]

    def test_cluster_se(self, py_cluster, st_cluster):
        for pc, sc in zip(py_cluster.coefficients, st_cluster["coefficients"]):
            assert tolerance_close(pc.std_err, sc["std_err"],
                                   name=f"se[{pc.name}]", rtol=1e-4)[0]
