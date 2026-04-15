"""
Test utilities for Phase 1 golden tests.

Provides common fixtures and helper functions for Stata-Python dual-run tests.
"""

import re
import numpy as np
import pandas as pd
from pathlib import Path
from statapy import OLS, IV2SLS, IVAbsorbingOLS
from statapy.stata_runner import StataRunner

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
PROJECT_STATA_OUTPUT = PROJECT_ROOT / "stata" / "output"
PROJECT_STATA_CASES = PROJECT_ROOT / "stata" / "cases"

# Ensure output directory exists
PROJECT_STATA_OUTPUT.mkdir(parents=True, exist_ok=True)


def parse_stata_log_with_precise_coefs(log_content: str, coef_names=None) -> dict:
    """Parse Stata log with precise _b[] and _se[] outputs."""
    result = {}

    e_patterns = {
        'nobs': r'E_N=([\d]+)',
        'df_model': r'E_DF_M=([\d]+)',
        'df_resid': r'E_DF_R=([\d]+)',
        'df_a': r'E_DF_A=([\d]+)',
        'r2': r'E_R2=([\d.]+)',
        'r2_adj': r'E_R2_A=([\d.]+)',
        'rmse': r'E_RMSE=([\d.]+)',
        'f_stat': r'E_F=([\d.]+)',
        'n_clust': r'E_N_CLUST=([\d]+)',
    }

    for key, pattern in e_patterns.items():
        match = re.search(pattern, log_content)
        if match:
            val_str = match.group(1)
            if val_str == '.' or val_str == '-.':
                continue  # Stata missing value
            if val_str.startswith('.'):
                val_str = '0' + val_str
            result[key] = float(val_str)

    coefficients = []
    b_matches = {k.lower(): v for k, v in re.findall(r'B_(\w+)=(-?[\d.]+)', log_content)}
    se_matches = {k.lower(): v for k, v in re.findall(r'SE_(\w+)=(-?[\d.]+)', log_content)}

    if coef_names is None:
        coef_names = ['x1', 'x2', '_cons']

    for name in coef_names:
        if name in b_matches and name in se_matches:
            beta = float(b_matches[name])
            if name != '_cons' and abs(beta) < 1e-15:
                continue  # Skip omitted coefficient
            coefficients.append({
                'name': name,
                'beta': beta,
                'std_err': float(se_matches[name]),
            })

    result['coefficients'] = coefficients
    return result


def parse_stata_log(log_content: str) -> dict:
    """
    Parse Stata log file to extract regression results.
    Uses e() display values for precision.
    """
    result = {}

    # Parse precise e() values
    # Note: Stata displays numbers < 1 as ".9318" not "0.9318"
    e_patterns = {
        'nobs': r'E_N=([\d]+)',
        'n_g': r'E_N_g=([\d]+)',
        'df_model': r'E_DF_M=([\d]+)',
        'df_resid': r'E_DF_R=([\d]+)',
        'df_a': r'E_DF_A=([\d]+)',
        'r2': r'E_R2=([\d.]+)',
        'r2_w': r'E_R2_W=([\d.]+)',
        'r2_adj': r'E_R2_A=([\d.]+)',
        'rmse': r'E_RMSE=([\d.]+)',
        'f_stat': r'E_F=([\d.]+)',
        'f_pvalue': r'E_F_P=([\d.]+)',
        'rss': r'E_RSS=([\d.]+)',
        'tss': r'E_TSS=([\d.]+)',
        'n_clust': r'E_N_CLUST=([\d]+)',
    }

    for key, pattern in e_patterns.items():
        match = re.search(pattern, log_content)
        if match:
            val_str = match.group(1)
            if val_str == '.' or val_str == '-.':
                continue  # Stata missing value
            # Stata shows ".9318" for numbers < 1, add leading zero
            if val_str.startswith('.'):
                val_str = '0' + val_str
            result[key] = float(val_str)

    # Extract coefficients from coefficient table
    coef_pattern = r'^\s+(\w+)\s+\|\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s+([\d.]+)'
    coefficients = []

    coef_section = False
    for line in log_content.split('\n'):
        if '-------------+----------------------------------------------------------------' in line:
            coef_section = True
            continue
        if coef_section and line.strip() == '':
            coef_section = False
            continue
        if coef_section:
            match = re.match(coef_pattern, line)
            if match:
                name = match.group(1)
                beta = float(match.group(2))
                std_err = float(match.group(3))
                coefficients.append({
                    'name': name,
                    'beta': beta,
                    'std_err': std_err,
                })

    result['coefficients'] = coefficients
    return result


def run_stata_ols(do_content: str, output_dir: str = None) -> dict:
    """
    Run Stata regress and return parsed results.
    """
    runner = StataRunner()

    if output_dir is None:
        output_dir = str(PROJECT_STATA_OUTPUT)

    result = runner.run_do_file(do_content, output_dir=output_dir)

    if result.exit_code != 0:
        raise RuntimeError(f"Stata failed: {result.error_message}")

    if not result.output_content:
        raise RuntimeError("Stata produced no output")

    return parse_stata_log(result.output_content)


def run_stata_ivregress(do_content: str, output_dir: str = None, coef_names=None) -> dict:
    """
    Run Stata ivregress 2sls and return parsed results.
    """
    runner = StataRunner()

    if output_dir is None:
        output_dir = str(PROJECT_STATA_OUTPUT)

    result = runner.run_do_file(do_content, output_dir=output_dir)

    if result.exit_code != 0:
        raise RuntimeError(f"Stata failed: {result.error_message}")

    if not result.output_content:
        raise RuntimeError("Stata produced no output")

    return parse_stata_log_with_precise_coefs(result.output_content, coef_names=coef_names)


def run_python_ols(data, y, x, add_constant=True):
    """Run Python OLS and return result object."""
    model = OLS(data=data, y=y, x=x, add_constant=add_constant)
    return model.fit(vce="ols")


def run_python_iv2sls(data, y, x_exog, x_endog, instruments, add_constant=True, vce="ols", cluster=None):
    """Run Python IV2SLS and return result object."""
    model = IV2SLS(data=data, y=y, x_exog=x_exog, x_endog=x_endog, instruments=instruments, add_constant=add_constant)
    if cluster is not None:
        return model.fit(vce=vce, cluster=cluster)
    return model.fit(vce=vce)


def run_python_ivabsorb(data, y, x_exog, x_endog, instruments, absorb, add_constant=True, vce="ols", cluster=None):
    """Run Python IVAbsorbingOLS and return result object."""
    model = IVAbsorbingOLS(data=data, y=y, x_exog=x_exog, x_endog=x_endog, instruments=instruments, absorb=absorb, add_constant=add_constant)
    if cluster is not None:
        return model.fit(vce=vce, cluster=cluster)
    return model.fit(vce=vce)


def tolerance_close(a, b, rtol=1e-6, atol=1e-8, name="value"):
    """Check if two values are within tolerance."""
    if a is None or b is None:
        return a == b, f"{name}: Python={a}, Stata={b}"

    diff = abs(a - b)
    rel_diff = diff / (abs(b) + 1e-15)

    passed = diff < atol or rel_diff < rtol
    msg = (
        f"{name}: Python={a:.15f}, Stata={b:.15f}, "
        f"abs_diff={diff:.2e}, rel_diff={rel_diff:.2e}, "
        f"{'PASS' if passed else 'FAIL'}"
    )
    return passed, msg
