"""Tests for StataRunner - smoke tests for Stata execution."""

import os
from types import SimpleNamespace

import pytest
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


def test_stata_runner_build_cmd_command():
    """Test cmd command generation for non-interactive execution."""
    runner = StataRunner()
    command = runner._build_cmd_command(
        r"D:\tmp\out",
        r"D:\tmp\out\run_123.do",
    )

    assert 'cd /d "D:\\tmp\\out"' in command
    assert f'"{runner.resolved_stata_path}" /e do run_123.do' in command


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
    assert f'cd /d "{expected}"' in captured["command"]


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
