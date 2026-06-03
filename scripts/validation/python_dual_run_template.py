"""
Python dual-run template for revalidation.
Usage: python python_dual_run_template.py <command_family> <scenario_id>
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path("D:/OneDrive - SAIF/PhD3/StataFlow")
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from stataflow.compat.stata import (
    regress, xtreg_fe, areg, reghdfe,
    ivregress_2sls, ivreghdfe,
    logit, probit, poisson, ppmlhdfe,
    did_imputation, eventstudyinteract, csdid,
    rdrobust, rdplot,
)
from tests.golden.test_utils import tolerance_close


def compare_with_stata(result, stata_log_path, rtol=1e-6):
    """Compare Python ResultSchema with Stata log output."""
    # TODO: parse stata log and compare field by field
    pass


def run_scenario(scenario_id: str):
    """Run a specific validation scenario."""
    scenarios = {
        # DID scenarios
        "c2.16_csdid_reg_ezunem": lambda: _run_csdid_reg_ezunem(),
        "c2.17_csdid_dr_ezunem": lambda: _run_csdid_dr_ezunem(),
        # Add more scenarios here
    }

    if scenario_id not in scenarios:
        raise ValueError(f"Unknown scenario: {scenario_id}")

    return scenarios[scenario_id]()


def _run_csdid_reg_ezunem():
    """CSDID reg on ezunem data."""
    df = pd.read_stata(PROJECT_ROOT / "research" / "data" / "public" / "did" / "ezunem_prepared.dta")
    result = csdid(
        df, y="uclms", id="city", time="year",
        first_treat="first_treat", method="reg",
        cluster="city", aggtype="event"
    )
    return result


def _run_csdid_dr_ezunem():
    """CSDID DR on ezunem data with controls."""
    df = pd.read_stata(PROJECT_ROOT / "research" / "data" / "public" / "did" / "ezunem_prepared.dta")
    result = csdid(
        df, y="uclms", id="city", time="year",
        first_treat="first_treat", method="drimp",
        cluster="city", xvars=["luclms"], aggtype="event"
    )
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python python_dual_run_template.py <scenario_id>")
        print("Available scenarios: c2.16_csdid_reg_ezunem, c2.17_csdid_dr_ezunem")
        sys.exit(1)

    scenario_id = sys.argv[1]
    result = run_scenario(scenario_id)
    print(f"Scenario {scenario_id} completed.")
    print(f"N obs: {result.sample.nobs}")
    print(f"N coefficients: {len(result.coefficients)}")
    for c in result.coefficients[:5]:
        print(f"  {c.name}: beta={c.beta:.4f}, se={c.std_err:.4f}")
