"""
Pytest configuration for golden dual-run tests.

All tests in this directory require a local Stata 17 installation.
If Stata is not available, the entire golden test suite is skipped.
"""

import pytest
from pathlib import Path


def _stata_available() -> bool:
    """Check whether a local Stata executable can be resolved."""
    try:
        from stataflow.stata_runner.runner import find_stata_executable

        find_stata_executable()
        return True
    except Exception:
        return False


STATA_AVAILABLE = _stata_available()


def pytest_collection_modifyitems(config, items):
    """Skip all golden tests when Stata 17 is not available."""
    if STATA_AVAILABLE:
        return
    skip_reason = "Stata 17 executable not found; golden dual-run tests skipped"
    skip_marker = pytest.mark.skip(reason=skip_reason)
    for item in items:
        item.add_marker(skip_marker)
