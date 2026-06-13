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
    log_file: Optional[str] = None
    output_file: Optional[str] = None
    output_content: Optional[str] = None
    error_message: Optional[str] = None


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

    def _build_cmd_command(self, output_dir: str, do_file: str) -> str:
        """
        Build the Windows cmd command used for non-interactive Stata execution.

        `/e do` avoids the final confirmation dialog shown by `/b do`, but it
        expects the process to start in the directory where the `.do` file
        lives so that Stata writes its auto-generated `.log` alongside it.
        """
        do_name = os.path.basename(do_file)
        return f'cd /d "{output_dir}" && "{self.resolved_stata_path}" /e do {do_name}'

    def run_do_file(
        self,
        do_content: str,
        output_dir: Optional[str] = None,
        timeout: int = 300,
    ) -> StataResult:
        """
        Run a Stata .do file using non-interactive mode.

        Uses: cmd /c "cd /d <output_dir> && StataMP-64.exe /e do <do_file>"
        Output files (.log) are written automatically by Stata in output_dir.

        Args:
            do_content: Content of the .do file.
            output_dir: Directory for .do and output files. Uses project stata/output if None.
            timeout: Timeout in seconds.

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
        cmd_command = self._build_cmd_command(output_dir, do_file)

        try:
            startupinfo = None
            if os.name == "nt":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 0

            result = subprocess.run(
                cmd_command,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding="utf-8",
                errors="replace",
                cwd=output_dir,
                startupinfo=startupinfo,
                shell=True,
            )

            log_content = None
            if os.path.exists(stata_log_file):
                with open(stata_log_file, "r", encoding="utf-8", errors="replace") as f:
                    log_content = f.read()

            return StataResult(
                exit_code=result.returncode,
                log_file=stata_log_file if os.path.exists(stata_log_file) else None,
                output_content=log_content,
                error_message=result.stderr if result.returncode != 0 else None,
            )
        except subprocess.TimeoutExpired:
            return StataResult(
                exit_code=-1,
                error_message=f"Stata execution timed out after {timeout}s",
            )
        except Exception as e:
            return StataResult(
                exit_code=-1,
                error_message=str(e),
            )

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
