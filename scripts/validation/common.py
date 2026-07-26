"""Shared helpers for validation runner scripts."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


FAMILY_TESTS = {
    "linear": [
        "tests/stata_validation/test_builtin_commands.py::test_regress_robust",
        "tests/stata_validation/test_builtin_commands.py::test_xtreg_fe_robust",
        "tests/stata_validation/test_builtin_commands.py::test_areg_cluster",
    ],
    "hdfe": [
        "tests/stata_validation/test_community_commands.py::test_reghdfe_cluster",
    ],
    "iv": [
        "tests/stata_validation/test_builtin_commands.py::test_ivregress_2sls_robust",
    ],
    "glm": [
        "tests/stata_validation/test_builtin_commands.py::test_logit_robust",
        "tests/stata_validation/test_builtin_commands.py::test_poisson_robust",
    ],
    "did": [
        "tests/stata_validation/test_community_commands.py::test_did_imputation_calendar_cohort",
        "tests/stata_validation/test_community_commands.py::test_csdid_calendar_cohort",
    ],
    "rd": [
        "tests/stata_validation/test_community_commands.py::test_rdrobust_fixed_bandwidth",
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
