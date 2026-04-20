"""Run all validation family suites and regenerate summary artifacts."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.validation.collect_validation_summary import write_summary_artifacts
from scripts.validation.common import FAMILY_TESTS, run_family_suite


if __name__ == "__main__":
    codes = []
    for family in FAMILY_TESTS:
        codes.append(run_family_suite(family))
    write_summary_artifacts("research/results/validation")
    raise SystemExit(1 if any(code != 0 for code in codes) else 0)
