"""Smoke test - verify package can be imported."""


def test_import_stataflow():
    """Verify stataflow package is importable."""
    import stataflow
    assert stataflow.__version__ == "1.1.0"


def test_import_results_module():
    """Verify results module is importable."""
    from stataflow.results import ResultSchema
    assert ResultSchema is not None


def test_import_stata_runner():
    """Verify stata_runner module is importable."""
    from stataflow.stata_runner import StataRunner
    assert StataRunner is not None
