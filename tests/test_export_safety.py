"""Safety tests for the open-source export script."""

import subprocess
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "release" / "export_open_source.py"


def _run_export(*extra_args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *extra_args],
        capture_output=True,
        text=True,
    )


def test_rejects_target_same_as_source():
    result = _run_export("--dry-run", "--target-root", str(REPO_ROOT))
    assert result.returncode != 0
    assert "cannot be the source repository" in result.stderr


def test_rejects_target_inside_source():
    result = _run_export("--dry-run", "--target-root", str(REPO_ROOT / "src"))
    assert result.returncode != 0
    assert "cannot be inside the source repository" in result.stderr


def test_rejects_target_parent_of_source():
    result = _run_export("--dry-run", "--target-root", str(REPO_ROOT.parent))
    assert result.returncode != 0
    assert "cannot be a parent of the source repository" in result.stderr


def test_dry_run_does_not_create_directories():
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "deeply" / "nested" / "StataFlow_open_source"
        result = _run_export("--dry-run", "--target-root", str(target))
        assert result.returncode == 0
        assert not target.exists()
        assert not target.parent.exists()
        assert not target.parent.parent.exists()
