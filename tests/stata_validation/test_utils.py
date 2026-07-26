"""Utilities for reproducible Stata-Python validation cases.

This module is deliberately self-contained. The internal comparison archive
contains pre-generated Stata logs, vendor mirrors, and audit expectations, so
it is not part of the public repository. Everything here works from
self-generated synthetic data and ``.do`` text produced at run time.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from stataflow.stata_runner import StataRunner

# Project paths. Stata artifacts (.dta inputs, .do/.log outputs) stay under
# the project stata/ tree per project convention; directories are created on
# demand so the cases also work in a fresh checkout.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PROJECT_STATA_OUTPUT = PROJECT_ROOT / "stata" / "output" / "stata_validation"
PROJECT_STATA_CASES = PROJECT_ROOT / "stata" / "cases" / "stata_validation"

# Project-standard field-level tolerance.
DEFAULT_RTOL = 1e-6
DEFAULT_ATOL = 1e-8

_B_LINE = re.compile(r"^B_(\w+)=\s*(\S+)$")
_SE_LINE = re.compile(r"^SE_(\w+)=\s*(\S+)$")
_E_LINE = re.compile(r"^E_(\w+)=\s*(\S+)$")
_STATA_VERSION_LINE = re.compile(r"^STATAFLOW_STATA_VERSION\s+(\d+)(?:\.\d+)?$")


def stata_float(raw: str) -> float:
    """Convert a Stata display token to float, restoring the leading zero.

    Stata displays numbers below 1 as ``.9318`` (and negative ones as
    ``-.9318``); both forms are normalized before conversion.
    """
    raw = raw.strip()
    if raw.startswith("-."):
        raw = raw.replace("-.", "-0.", 1)
    elif raw.startswith("."):
        raw = "0" + raw
    return float(raw)


def tolerance_close(a, b, rtol: float = DEFAULT_RTOL, atol: float = DEFAULT_ATOL, name: str = "value"):
    """Check whether two scalars agree within relative/absolute tolerance."""
    if a is None or b is None:
        return a == b, f"{name}: Python={a}, Stata={b}"

    diff = abs(a - b)
    rel_diff = diff / max(abs(b), 1e-15)

    passed = diff < atol or rel_diff < rtol
    msg = (
        f"{name}: Python={a:.15f}, Stata={b:.15f}, "
        f"abs_diff={diff:.2e}, rel_diff={rel_diff:.2e}, "
        f"{'PASS' if passed else 'FAIL'}"
    )
    return passed, msg


def parse_stata_major_version(log: str) -> int | None:
    """Return the major Stata release reported by the validation probe."""
    for line in log.splitlines():
        match = _STATA_VERSION_LINE.fullmatch(line.strip())
        if match:
            return int(match.group(1))
    return None


def write_case_data(data: pd.DataFrame, name: str) -> Path:
    """Write a synthetic case dataset under stata/cases/stata_validation."""
    PROJECT_STATA_CASES.mkdir(parents=True, exist_ok=True)
    dta = PROJECT_STATA_CASES / f"{name}.dta"
    data.to_stata(dta, write_index=False, version=118)
    return dta


def stata_coef_dump(varnames: list[str]) -> str:
    """Do-file snippet that prints precise ``B_<name>=`` / ``SE_<name>=`` lines."""
    names = " ".join(varnames)
    return (
        f"foreach v in {names} {{\n"
        "    di as txt \"B_\" \"`v'\" \"=\" %24.16e _b[`v']\n"
        "    di as txt \"SE_\" \"`v'\" \"=\" %24.16e _se[`v']\n"
        "}\n"
    )


# Do-file snippet that dumps every column of e(b) / sqrt(diag(e(V))) with
# full precision. Used for matrix-results commands (did_imputation, csdid).
STATA_MATRIX_DUMP = """
matrix b = e(b)
matrix V = e(V)
local names : colfullnames b
local i = 1
foreach name of local names {
    di as txt "B_" "`name'" "=" %24.16e b[1, `i']
    di as txt "SE_" "`name'" "=" %24.16e sqrt(V[`i', `i'])
    local ++i
}
"""


def run_stata_case(do_content: str, marker: str) -> dict:
    """Run a do-file through local Stata and parse the emitted markers.

    The case is considered complete only when the unique completion marker
    appears in the log; anything else is a hard failure (never a silent
    pass). Returns ``{"b": {...}, "se": {...}, "e": {...}, "log": str}``.
    """
    PROJECT_STATA_OUTPUT.mkdir(parents=True, exist_ok=True)
    result = StataRunner().run_do_file(do_content, output_dir=str(PROJECT_STATA_OUTPUT))
    if result.exit_code != 0:
        raise RuntimeError(f"Stata failed: {result.error_message}")
    log = result.output_content or ""
    if not log:
        raise RuntimeError("Stata produced no output")
    if marker not in log:
        raise RuntimeError(
            f"Stata case did not complete: marker {marker!r} not found in log. "
            f"Inspect the log under {PROJECT_STATA_OUTPUT}."
        )

    parsed: dict = {"b": {}, "se": {}, "e": {}, "log": log}
    for line in log.splitlines():
        stripped = line.strip()
        m = _B_LINE.match(stripped)
        if m:
            parsed["b"][m.group(1)] = stata_float(m.group(2))
            continue
        m = _SE_LINE.match(stripped)
        if m:
            parsed["se"][m.group(1)] = stata_float(m.group(2))
            continue
        m = _E_LINE.match(stripped)
        if m:
            parsed["e"][m.group(1)] = stata_float(m.group(2))
    return parsed


def assert_coef_alignment(
    py_coefficients,
    st: dict,
    rtol: float = DEFAULT_RTOL,
    se_rtol: float | None = None,
) -> None:
    """Compare Python coefficient rows against parsed Stata values by name.

    Compares both point estimates and standard errors for every Python
    coefficient row; Stata-side values are looked up by coefficient name, so
    ordering differences between the two implementations do not matter.

    ``se_rtol`` overrides ``rtol`` for standard errors only; point estimates
    are always compared at ``rtol``.
    """
    failures = []
    for row in py_coefficients:
        if row.name not in st["b"]:
            failures.append(f"missing Stata coefficient: {row.name}")
            continue
        ok, msg = tolerance_close(row.beta, st["b"][row.name], rtol=rtol, name=f"beta[{row.name}]")
        if not ok:
            failures.append(msg)
        ok, msg = tolerance_close(
            row.std_err, st["se"][row.name], rtol=se_rtol or rtol, name=f"se[{row.name}]"
        )
        if not ok:
            failures.append(msg)
    assert not failures, "\n".join(failures)
