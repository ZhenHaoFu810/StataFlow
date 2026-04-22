"""
Pytest configuration and common fixtures for StataFlow tests.
"""

import os
import pytest
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.parent
TEST_DATA_DIR = PROJECT_ROOT / "tests" / "data"
GOLDEN_DIR = PROJECT_ROOT / "tests" / "golden"
STATA_CASES_DIR = PROJECT_ROOT / "stata" / "cases"
STATA_OUTPUT_DIR = PROJECT_ROOT / "stata" / "output"


@pytest.fixture
def project_root():
    """Return project root directory."""
    return PROJECT_ROOT


@pytest.fixture
def stata_output_dir():
    """Return Stata output directory, creating it if needed."""
    STATA_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return str(STATA_OUTPUT_DIR)
