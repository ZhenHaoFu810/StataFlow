"""Smoke test - verify package can be imported."""


def test_import_stataflow():
    """Verify stataflow package is importable and version matches pyproject."""
    import re
    from pathlib import Path

    import stataflow

    pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
    match = re.search(r'^version = "([^"]+)"', pyproject.read_text(encoding="utf-8"), re.M)
    assert match is not None, "version not found in pyproject.toml"
    assert stataflow.__version__ == match.group(1)


def test_import_results_module():
    """Verify results module is importable."""
    from stataflow.results import ResultSchema
    assert ResultSchema is not None


def test_import_stata_runner():
    """Verify stata_runner module is importable."""
    from stataflow.stata_runner import StataRunner
    assert StataRunner is not None
