"""Tests for StataRunner - smoke tests for Stata execution."""

import os
from types import SimpleNamespace

import pytest
import stataflow.stata_runner.runner as runner_module
from stataflow.stata_runner.runner import (
    StataRunner,
    find_stata_executable,
    DEFAULT_STATA_PATH,
)


def test_find_stata_executable():
    """Test that we can find Stata executable."""
    try:
        path = find_stata_executable()
        assert os.path.isfile(path)
        assert path.endswith(".exe")
    except FileNotFoundError:
        pytest.skip("Stata executable not found on this machine")


def test_find_stata_with_custom_path():
    """Test finding Stata with custom path."""
    # If default path exists, use it
    if os.path.isfile(DEFAULT_STATA_PATH):
        path = find_stata_executable(custom_path=DEFAULT_STATA_PATH)
        assert path == DEFAULT_STATA_PATH


def test_stata_runner_init():
    """Test StataRunner initialization."""
    runner = StataRunner()
    assert runner.stata_path is None
    
    runner2 = StataRunner(stata_path="/custom/path/stata.exe")
    assert runner2.stata_path == "/custom/path/stata.exe"


def test_stata_runner_resolved_path():
    """Test that resolved path finds Stata."""
    runner = StataRunner()
    try:
        path = runner.resolved_stata_path
        assert os.path.isfile(path)
    except FileNotFoundError:
        pytest.skip("Stata executable not found on this machine")


def test_stata_runner_generate_min_do():
    """Test generating minimal .do file."""
    runner = StataRunner()
    do_content = runner.generate_min_do()
    
    assert isinstance(do_content, str)
    assert "regress" in do_content
    assert "clear all" in do_content


def test_stata_runner_build_stata_args():
    """Test Stata argument list generation for non-interactive execution."""
    runner = StataRunner()
    args = runner._build_stata_args(r"D:\tmp\out\run_123.do")

    assert args[0] == runner.resolved_stata_path
    assert args[1:] == ["/e", "do", "run_123.do"]


def test_stata_runner_resolves_relative_output_dir(monkeypatch, tmp_path):
    """Relative output paths must not be interpreted twice after changing cwd."""
    monkeypatch.chdir(tmp_path)
    captured = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["cwd"] = kwargs["cwd"]
        return SimpleNamespace(returncode=0, stderr="")

    monkeypatch.setattr("stataflow.stata_runner.runner.subprocess.run", fake_run)
    runner = StataRunner()
    runner._resolved_path = DEFAULT_STATA_PATH
    result = runner.run_do_file("display 1", output_dir="relative-output")

    expected = str(tmp_path / "relative-output")
    assert result.exit_code == 0
    assert captured["cwd"] == expected
    assert isinstance(captured["command"], list)
    assert captured["command"][0] == DEFAULT_STATA_PATH
    assert captured["command"][1:3] == ["/e", "do"]
    assert captured["command"][-1].endswith(".do")


def test_parse_stata_return_code_only_uses_terminal_status():
    """Historical or captured error text must not be treated as failure."""
    successful_log = """
. display "historical r(111); text only"
historical r(111); text only
. capture noisily regress y missing_var
. display 1
1
end of do-file
"""
    failed_log = """
. regress y missing_var
variable missing_var not found
r(111);
end of do-file
r(111);
"""

    assert runner_module._parse_stata_return_code(successful_log) is None
    assert runner_module._parse_stata_return_code(failed_log) == 111


def test_stata_runner_reports_terminal_stata_error():
    """A Stata runtime error must be visible independently of the OS code."""
    runner = StataRunner()
    try:
        runner.resolved_stata_path
    except FileNotFoundError:
        pytest.skip("Stata executable not found on this machine")

    result = runner.run_do_file(
        "version 17\nset more off\nclear\nregress y missing_var\n",
        timeout=60,
    )

    assert result.exit_code == 0
    assert result.process_exit_code == 0
    assert result.stata_return_code == 111
    assert result.succeeded is False
    assert "r(111)" in (result.error_message or "")


def test_stata_runner_can_raise_on_terminal_stata_error():
    """Callers may request an exception for a terminal Stata return code."""
    runner = StataRunner()
    try:
        runner.resolved_stata_path
    except FileNotFoundError:
        pytest.skip("Stata executable not found on this machine")

    with pytest.raises(RuntimeError, match=r"r\(9\)"):
        runner.run_do_file(
            "version 17\nset more off\nexit 9\n",
            timeout=60,
            raise_on_stata_error=True,
        )


def test_stata_runner_run_min_do():
    """Test running minimal .do file through Stata."""
    runner = StataRunner()
    
    try:
        # Verify Stata can be found
        runner.resolved_stata_path
    except FileNotFoundError:
        pytest.skip("Stata executable not found on this machine")
    
    do_content = runner.generate_min_do()
    result = runner.run_do_file(do_content)
    
    # Stata should have executed (exit code 0 means success)
    # Note: On Windows, Stata might return 0 even with display output
    assert result.exit_code == 0, f"Stata failed with: {result.error_message}"
    assert result.log_file is not None


def test_stata_runner_run_custom_do():
    """Test running custom .do content."""
    runner = StataRunner()
    
    try:
        runner.resolved_stata_path
    except FileNotFoundError:
        pytest.skip("Stata executable not found on this machine")
    
    # Simple .do file that creates and exports data
    do_content = """
clear all
set more off
set obs 5
gen x = _n
gen y = 2 * x + 1
display "Custom do file executed successfully"
"""
    
    result = runner.run_do_file(do_content)
    assert result.exit_code == 0, f"Stata failed with: {result.error_message}"
