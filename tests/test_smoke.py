"""Smoke test - verify package can be imported."""


def test_import_statapy():
    """Verify statapy package is importable."""
    import statapy
    assert statapy.__version__ == "0.1.0"


def test_import_results_module():
    """Verify results module is importable."""
    from statapy.results import ResultSchema
    assert ResultSchema is not None


def test_import_stata_runner():
    """Verify stata_runner module is importable."""
    from statapy.stata_runner import StataRunner
    assert StataRunner is not None
