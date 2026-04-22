"""
Generate test data and run Stata for p0_min_ols_auto dual-run test.

This script:
1. Generates a test dataset with known seed
2. Runs Python OLS
3. Runs Stata regress via StataRunner
4. Saves both results for comparison

All output files are kept within the project directory.
"""

import json
import re
import numpy as np
import pandas as pd
from pathlib import Path
from stataflow import OLS
from stataflow.stata_runner import StataRunner
from stataflow.results import ResultSchema

# Project paths - ALL outputs stay here
PROJECT_ROOT = Path(__file__).parent.parent.parent
PROJECT_STATA_OUTPUT = PROJECT_ROOT / "stata" / "output"
PROJECT_STATA_CASES = PROJECT_ROOT / "stata" / "cases"

# Ensure output directory exists
PROJECT_STATA_OUTPUT.mkdir(parents=True, exist_ok=True)


def parse_stata_log(log_content: str) -> dict:
    """
    Parse Stata log file to extract regression results.
    
    Returns dict with:
    - nobs, df_model, df_resid, r2, r2_adj, rmse, f_stat, f_pvalue, rss
    - coefficients: list of {name, beta, std_err}
    """
    result = {}
    
    # First try to parse precise e() values
    # Note: Stata displays numbers < 1 as ".9318" not "0.9318"
    e_patterns = {
        'nobs': r'E_N=([\d]+)',
        'df_model': r'E_DF_M=([\d]+)',
        'df_resid': r'E_DF_R=([\d]+)',
        'r2': r'E_R2=([\d.]+)',
        'r2_adj': r'E_R2_A=([\d.]+)',
        'rmse': r'E_RMSE=([\d.]+)',
        'f_stat': r'E_F=([\d.]+)',
        'f_pvalue': r'E_F_P=([\d.]+)',
        'rss': r'E_RSS=([\d.]+)',
    }
    
    for key, pattern in e_patterns.items():
        match = re.search(pattern, log_content)
        if match:
            val_str = match.group(1)
            # Stata shows ".9318" for numbers < 1, add leading zero
            if val_str.startswith('.'):
                val_str = '0' + val_str
            result[key] = float(val_str)
    
    # If e() values not found, fall back to parsing display output
    if 'nobs' not in result:
        match = re.search(r'Number of obs\s+=\s+(\d+)', log_content)
        if match:
            result['nobs'] = float(match.group(1))
    
    if 'df_model' not in result:
        model_match = re.search(r'\s+Model\s+\|\s+[\d.]+\s+(\d+)\s+[\d.]+', log_content)
        if model_match:
            result['df_model'] = float(model_match.group(1))
    
    if 'df_resid' not in result:
        resid_match = re.search(r'\s+Residual\s+\|\s+[\d.]+\s+(\d+)\s+[\d.]+', log_content)
        if resid_match:
            result['df_resid'] = float(resid_match.group(1))
    
    # Extract coefficients
    # Match lines like: "          x1 |   1.829243   .1056734    17.31   0.000"
    coef_pattern = r'^\s+(\w+)\s+\|\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s+([\d.]+)'
    coefficients = []
    
    # Find the coefficient table section (after the dashed line)
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


def generate_test_data():
    """Generate test dataset with known seed."""
    np.random.seed(12345)
    n = 100
    
    x1 = np.random.normal(0, 1, n)
    x2 = np.random.normal(0, 1, n)
    y = 1 + 2 * x1 + 3 * x2 + np.random.normal(0, 1, n)
    
    return pd.DataFrame({"y": y, "x1": x1, "x2": x2})


def run_python_ols(data):
    """Run Python OLS and return result object."""
    model = OLS(data=data, y="y", x=["x1", "x2"], add_constant=True)
    return model.fit(vce="ols")


def run_stata_ols(data):
    """
    Run Stata regress and return parsed results.

    Creates a .do file that:
    1. Inputs the data from project directory
    2. Runs regress
    3. Results are in the log file in project directory
    """
    runner = StataRunner()

    # Save data to project directory
    dta_file = PROJECT_STATA_CASES / "p0_dual_test_data.dta"
    data.to_stata(str(dta_file), write_index=False)

    # Create .do file that also outputs e() values for precise parsing
    do_template = '''
clear all
set more off

// Read data
use "$DATA_FILE", clear

// Run regression
regress y x1 x2

// Output precise e() values for parsing
display "E_N=" e(N)
display "E_DF_M=" e(df_m)
display "E_DF_R=" e(df_r)
display "E_R2=" e(r2)
display "E_R2_A=" e(r2_a)
display "E_RMSE=" e(rmse)
display "E_F=" e(F)
display "E_F_P=" e(F_p)
display "E_RSS=" e(rss)

display "Stata regress completed successfully"
'''
    do_content = do_template.replace("$DATA_FILE", str(dta_file))

    # Run Stata with output in project directory
    output_dir = str(PROJECT_STATA_OUTPUT)
    print(f"Running Stata, output in: {output_dir}")
    result = runner.run_do_file(do_content, output_dir=output_dir)

    if result.exit_code != 0:
        raise RuntimeError(f"Stata failed with exit code {result.exit_code}: {result.error_message}")

    if not result.output_content:
        raise RuntimeError("Stata produced no output")

    # Parse the log
    return parse_stata_log(result.output_content)


def compare_results(py_result, st_result):
    """Compare Python and Stata results."""
    print("\n" + "=" * 80)
    print("DUAL-RUN COMPARISON: Python vs Stata")
    print("=" * 80)
    
    all_passed = True
    
    # Compare scalar fields
    fields = [
        ('sample', 'nobs', 'nobs'),
        ('fit', 'df_model', 'df_model'),
        ('fit', 'df_resid', 'df_resid'),
        ('fit', 'r2', 'r2'),
        ('fit', 'rmse', 'rmse'),
        ('fit', 'f_stat', 'f_stat'),
    ]
    
    for py_section, py_field, st_field in fields:
        py_val = getattr(getattr(py_result, py_section), py_field)
        st_val = st_result.get(st_field)
        
        if py_val is None or st_val is None:
            print(f"[WARN] {py_field}: Python={py_val}, Stata={st_val}")
            continue

        diff = abs(py_val - st_val)
        rel_diff = diff / (abs(st_val) + 1e-15)
        passed = rel_diff < 1e-6

        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {py_field}: Python={py_val:.10f}, Stata={st_val:.10f}, rel_diff={rel_diff:.2e}")
        
        if not passed:
            all_passed = False
    
    # Compare coefficients
    print("\nCoefficients:")
    for py_coef in py_result.coefficients:
        # Find matching Stata coefficient
        st_coef = None
        for c in st_result.get('coefficients', []):
            if c['name'] == py_coef.name:
                st_coef = c
                break
        
        if st_coef is None:
            print(f"[WARN] {py_coef.name}: not found in Stata results")
            continue

        for attr, label in [('beta', 'beta'), ('std_err', 'std_err')]:
            py_val = getattr(py_coef, attr)
            st_val = st_coef[attr]

            diff = abs(py_val - st_val)
            rel_diff = diff / (abs(st_val) + 1e-15)
            passed = rel_diff < 1e-6

            status = "[PASS]" if passed else "[FAIL]"
            print(f"  {status} {py_coef.name}.{label}: Python={py_val:.10f}, Stata={st_val:.10f}, rel_diff={rel_diff:.2e}")
            
            if not passed:
                all_passed = False
    
    print("\n" + "=" * 80)
    if all_passed:
        print("[PASS] ALL COMPARISONS PASSED")
    else:
        print("[FAIL] SOME COMPARISONS FAILED")
    print("=" * 80)

    return all_passed


if __name__ == "__main__":
    print("Generating test data...")
    data = generate_test_data()
    print(f"Data shape: {data.shape}")

    print("\nRunning Python OLS...")
    py_result = run_python_ols(data)
    print(f"Python R2: {py_result.fit.r2:.10f}")
    print(f"Python coefficients: {[c.name for c in py_result.coefficients]}")

    print("\nRunning Stata regress...")
    st_result = run_stata_ols(data)
    print(f"Stata R2: {st_result.get('r2', 'N/A')}")
    print(f"Stata df_model: {st_result.get('df_model', 'N/A')}")
    print(f"Stata df_resid: {st_result.get('df_resid', 'N/A')}")
    print(f"Stata coefficients: {[c['name'] for c in st_result.get('coefficients', [])]}")

    print("\nComparing results...")
    passed = compare_results(py_result, st_result)

    if not passed:
        print("\n[WARN] Comparison failed - check differences above")
        exit(1)
    else:
        print("\n[PASS] Dual-run test passed!")
