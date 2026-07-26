"""Shared fixtures for reproducible Stata validation cases and
community-ado probes.

Prerequisite and skip semantics:
- No local Stata 17 executable -> collection fails with the precise reason.
- Stata present but a community ado missing -> only that command's case
  skips, with the ``ssc install`` hint.
"""

from __future__ import annotations

import pytest

from stataflow.stata_runner import StataRunner
from stataflow.stata_runner.runner import find_stata_executable

from tests.stata_validation.test_utils import PROJECT_STATA_OUTPUT, parse_stata_major_version


@pytest.fixture(scope="session")
def stata_path() -> str:
    """Locate Stata and fail clearly unless the executable reports release 17."""
    try:
        path = find_stata_executable()
    except FileNotFoundError as exc:
        pytest.fail(f"local Stata 17 executable is required: {exc}")

    probe = 'display "STATAFLOW_STATA_VERSION " c(stata_version)\n'
    PROJECT_STATA_OUTPUT.mkdir(parents=True, exist_ok=True)
    result = StataRunner(stata_path=path).run_do_file(
        probe,
        output_dir=str(PROJECT_STATA_OUTPUT),
        raise_on_stata_error=True,
    )
    major_version = parse_stata_major_version(result.output_content or "")
    if major_version != 17:
        reported = "unknown" if major_version is None else str(major_version)
        pytest.fail(
            f"reproducible validation requires Stata 17; executable reported {reported}: {path}"
        )
    return path


@pytest.fixture(scope="session")
def require_ado(stata_path):
    """Return a checker that skips a test when a community ado is missing.

    The probe runs ``which <command>`` inside Stata once per command and
    caches the result for the session.
    """
    cache: dict[str, bool] = {}

    def _probe(command: str) -> bool:
        do = (
            f"capture which {command}\n"
            "if _rc == 0 {\n"
            f'    display "STATA_VALIDATION_ADO_OK {command}"\n'
            "}\n"
            "else {\n"
            f'    display "STATA_VALIDATION_ADO_MISSING {command}"\n'
            "}\n"
        )
        PROJECT_STATA_OUTPUT.mkdir(parents=True, exist_ok=True)
        result = StataRunner().run_do_file(do, output_dir=str(PROJECT_STATA_OUTPUT))
        log = result.output_content or ""
        return f"STATA_VALIDATION_ADO_OK {command}" in log

    def _require(command: str) -> None:
        if command not in cache:
            cache[command] = _probe(command)
        if not cache[command]:
            pytest.skip(
                f"community command '{command}' is not installed in the local Stata "
                f"(install with: ssc install {command})"
            )

    return _require
