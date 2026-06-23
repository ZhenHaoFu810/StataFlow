"""
Stata runner - calls local Stata 17 executable.

Responsibilities:
- Locate Stata 17 executable
- Generate temporary .do files
- Execute Stata in non-interactive mode
- Collect exit status and output files

Does NOT:
- Contain estimation algorithms
- Embed result comparison logic
- Serve as end-user entry point
"""

from __future__ import annotations

import os
import re
import subprocess
import shutil
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


# Default Stata 17 executable path
DEFAULT_STATA_PATH = r"D:\Software\Stata17\StataMP-64.exe"

# Common installation directories to search
FALLBACK_STATA_DIRS = [
    r"D:\Software\Stata17",
]

# Fallback paths to try if default is not found
FALLBACK_STATA_NAMES = [
    "StataMP-64.exe",
    "StataSE-64.exe",
    "Stata-64.exe",
    "StataMP.exe",
    "StataSE.exe",
    "Stata.exe",
]


@dataclass
class StataResult:
    """Result from a Stata execution."""
    exit_code: int
    stata_return_code: Optional[int] = None
    log_file: Optional[str] = None
    output_file: Optional[str] = None
    output_content: Optional[str] = None
    error_message: Optional[str] = None

    @property
    def process_exit_code(self) -> int:
        """Return the raw operating-system process exit code."""
        return self.exit_code

    @property
    def succeeded(self) -> bool:
        """Whether both the process and the Stata do-file completed normally."""
        return self.exit_code == 0 and self.stata_return_code is None


_STATA_TERMINAL_RETURN_CODE = re.compile(r"^r\((\d+)\);$")


class StataExecutionError(RuntimeError):
    """Raised when a Stata do-file terminates with a Stata return code."""


def _parse_stata_return_code(log_content: Optional[str]) -> Optional[int]:
    """Parse a terminal Stata return code from the end of a batch log.

    Stata's ``/e do`` mode can return an OS exit code of zero even when the
    do-file terminates with ``r(<number>);``. Only the final non-empty log
    line is considered so captured errors and ordinary displayed text do not
    become false failures.
    """
    if not log_content:
        return None
    for line in reversed(log_content.splitlines()):
        stripped = line.strip()
        if not stripped:
            continue
        match = _STATA_TERMINAL_RETURN_CODE.fullmatch(stripped)
        return int(match.group(1)) if match else None
    return None


def find_stata_executable(custom_path: Optional[str] = None) -> str:
    """
    Find Stata 17 executable.
    
    Args:
        custom_path: Optional custom path to Stata executable.
        
    Returns:
        Path to Stata executable.
        
    Raises:
        FileNotFoundError: If Stata executable cannot be found.
    """
    # Try custom path first
    if custom_path and os.path.isfile(custom_path):
        return custom_path
    
    # Try default path
    if os.path.isfile(DEFAULT_STATA_PATH):
        return DEFAULT_STATA_PATH
    
    # Try common Stata installation directories
    searched_dirs = []
    for stata_base in FALLBACK_STATA_DIRS:
        searched_dirs.append(stata_base)
        if os.path.isdir(stata_base):
            for name in FALLBACK_STATA_NAMES:
                candidate = os.path.join(stata_base, name)
                if os.path.isfile(candidate):
                    return candidate
    
    # Try PATH
    for name in FALLBACK_STATA_NAMES:
        path = shutil.which(name)
        if path:
            return path
    
    raise FileNotFoundError(
        f"Cannot find Stata executable. "
        f"Tried: {DEFAULT_STATA_PATH}, "
        f"fallbacks in {searched_dirs}, and PATH. "
        f"Please set STATA_PATH environment variable or pass custom_path."
    )


class StataRunner:
    """
    Minimal Stata runner for Phase 0.
    
    Generates .do files, executes them, and collects output.
    """

    def __init__(self, stata_path: Optional[str] = None):
        """
        Initialize StataRunner.
        
        Args:
            stata_path: Optional path to Stata executable.
        """
        self.stata_path = stata_path
        self._resolved_path: Optional[str] = None

    @property
    def resolved_stata_path(self) -> str:
        """Get resolved Stata executable path."""
        if self._resolved_path is None:
            self._resolved_path = find_stata_executable(self.stata_path)
        return self._resolved_path

    def _build_stata_args(self, do_file: str) -> list[str]:
        """
        Build the argument list for non-interactive Stata execution.

        `/e do` avoids the final confirmation dialog shown by `/b do`. The
        caller must set ``cwd`` to the directory containing the `.do` file so
        that Stata writes its auto-generated `.log` alongside it.
        """
        do_name = os.path.basename(do_file)
        return [self.resolved_stata_path, "/e", "do", do_name]

    def run_do_file(
        self,
        do_content: str,
        output_dir: Optional[str] = None,
        timeout: int = 300,
        raise_on_stata_error: bool = False,
    ) -> StataResult:
        """
        Run a Stata .do file using non-interactive mode.

        Uses: cmd /c "cd /d <output_dir> && StataMP-64.exe /e do <do_file>"
        Output files (.log) are written automatically by Stata in output_dir.

        Args:
            do_content: Content of the .do file.
            output_dir: Directory for .do and output files. Uses project stata/output if None.
            timeout: Timeout in seconds.
            raise_on_stata_error: Raise ``RuntimeError`` when the Stata log
                ends with a nonzero ``r(<number>);`` status.

        Returns:
            StataResult with exit code and log content.
        """
        import time

        if output_dir:
            output_dir = os.path.abspath(output_dir)
            os.makedirs(output_dir, exist_ok=True)
        else:
            # Default to project stata/output directory
            output_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
                "stata", "output"
            )
            os.makedirs(output_dir, exist_ok=True)

        # Use unique filenames to avoid OneDrive file locking issues
        timestamp = int(time.time() * 1000)
        do_file = os.path.join(output_dir, f"run_{timestamp}.do")
        with open(do_file, "w", encoding="utf-8") as f:
            f.write(do_content)

        stata_log_file = do_file.replace(".do", ".log")
        stata_args = self._build_stata_args(do_file)

        try:
            startupinfo = None
            if os.name == "nt":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 0

            result = subprocess.run(
                stata_args,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding="utf-8",
                errors="replace",
                cwd=output_dir,
                startupinfo=startupinfo,
                shell=False,
            )

            log_content = None
            if os.path.exists(stata_log_file):
                with open(stata_log_file, "r", encoding="utf-8", errors="replace") as f:
                    log_content = f.read()

            stata_return_code = _parse_stata_return_code(log_content)
            error_message = result.stderr if result.returncode != 0 else None
            if stata_return_code is not None:
                error_message = (
                    f"Stata do-file terminated with r({stata_return_code}); "
                    f"process exit code was {result.returncode}."
                )
                if raise_on_stata_error:
                    raise StataExecutionError(error_message)

            return StataResult(
                exit_code=result.returncode,
                stata_return_code=stata_return_code,
                log_file=stata_log_file if os.path.exists(stata_log_file) else None,
                output_content=log_content,
                error_message=error_message,
            )
        except subprocess.TimeoutExpired as exc:
            raise StataExecutionError(
                f"Stata execution timed out after {timeout}s"
            ) from exc
        except StataExecutionError:
            raise
        except Exception as exc:
            raise StataExecutionError(
                f"Unexpected error while running Stata: {exc}"
            ) from exc

    def generate_min_do(self) -> str:
        """Generate a minimal .do file for smoke testing."""
        return """
// Minimal Stata smoke test
clear all
set more off

// Create minimal data
set obs 10
gen x = _n
gen y = 2 * x + rnormal()

// Run minimal regression
regress y x

// Display results
display "Exit code test passed"
"""
