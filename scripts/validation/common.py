"""Shared helpers for validation runner scripts."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


FAMILY_TESTS = {
    "linear": [
        "tests/golden/test_p1_ols_basic.py",
        "tests/golden/test_v1_regress_real_grunfeld.py",
        "tests/golden/test_p2_fe_basic.py",
        "tests/golden/test_v1_xtreg_fe_real_grunfeld.py",
        "tests/golden/test_p3_areg_basic.py",
        "tests/golden/test_p3_areg_real_panel.py",
    ],
    "hdfe": [
        "tests/golden/test_p3_reghdfe_basic.py",
        "tests/golden/test_p3_reghdfe_cluster.py",
        "tests/golden/test_p3_reghdfe_two_fe.py",
        "tests/golden/test_p3_reghdfe_real_panel.py",
    ],
    "iv": [
        "tests/golden/test_w2_ivregress_basic.py",
        "tests/golden/test_w2_ivregress_real_card.py",
        "tests/golden/test_w2_ivreghdfe_basic.py",
        "tests/golden/test_w2_ivreghdfe_real_panel.py",
    ],
    "glm": [
        "tests/golden/test_w3_logit_real.py",
        "tests/golden/test_w3_probit_real.py",
        "tests/golden/test_w3_poisson_real.py",
        "tests/golden/test_w3_ppmlhdfe_real_gravity.py",
        "tests/golden/test_p3_ppmlhdfe_fit_stats.py",
    ],
    "did": [
        "tests/golden/test_w4_did_imputation_real_ezunem.py",
        "tests/golden/test_w4_eventstudyinteract_real_ezunem.py",
        "tests/golden/test_w4_csdid_real_ezunem.py",
    ],
    "rd": [
        "tests/test_rdrobust.py",
    ],
}


def run_family_suite(family: str) -> int:
    if family not in FAMILY_TESTS:
        raise ValueError(f"Unknown validation family: {family}")

    cmd = [sys.executable, "-m", "pytest", *FAMILY_TESTS[family], "-v"]
    result = subprocess.run(cmd, check=False)

    output_dir = Path("research/results/validation")
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / f"{family}-runner.json"
    summary_path.write_text(
        json.dumps(
            {
                "family": family,
                "command": cmd,
                "returncode": result.returncode,
                "tests": FAMILY_TESTS[family],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return result.returncode
