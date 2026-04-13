"""
Generate test data for p0_min_ols_auto and run Stata to export results.

This script:
1. Creates a minimal dataset
2. Saves it as .dta for Stata (in temp directory to avoid OneDrive sync issues)
3. Runs Stata .do file
4. Reads Stata's exported JSON results
"""

import os
import json
import tempfile
import numpy as np
import pandas as pd
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
CASES_DIR = PROJECT_ROOT / "stata" / "cases"
OUTPUT_DIR = PROJECT_ROOT / "stata" / "output"

# Use temp directory to avoid OneDrive file locking
TEMP_DIR = Path(tempfile.mkdtemp(prefix="statapy_p0_"))


def generate_data():
    """Generate minimal test dataset."""
    np.random.seed(12345)
    n = 100
    
    x1 = np.random.normal(0, 1, n)
    x2 = np.random.normal(0, 1, n)
    y = 1 + 2 * x1 + 3 * x2 + np.random.normal(0, 1, n)
    
    df = pd.DataFrame({
        "y": y,
        "x1": x1,
        "x2": x2,
    })
    
    # Save as .dta for Stata (in temp directory)
    dta_path = TEMP_DIR / "p0_min_ols_auto.dta"
    df.to_stata(str(dta_path), write_index=False)
    print(f"Data saved to: {dta_path}")
    
    return df


def run_stata():
    """Run Stata .do file and read exported results."""
    from statapy.stata_runner import StataRunner
    
    do_file = CASES_DIR / "p0_min_ols_auto.do"
    do_content = do_file.read_text(encoding="utf-8")
    
    runner = StataRunner()
    print(f"Running Stata with: {runner.resolved_stata_path}")
    
    # Run from project root
    orig_dir = os.getcwd()
    os.chdir(str(PROJECT_ROOT))
    
    try:
        result = runner.run_do_file(do_content)
        
        if result.exit_code != 0:
            print(f"Stata failed with exit code {result.exit_code}")
            print(f"Error: {result.error_message}")
            return None
        
        # Read exported results
        stata_json = OUTPUT_DIR / "p0_min_ols_auto_stata.json"
        if stata_json.exists():
            with open(stata_json, "r") as f:
                stata_results = json.load(f)
            print(f"Stata results loaded from: {stata_json}")
            return stata_results
        else:
            print(f"Stata JSON not found at: {stata_json}")
            return None
    finally:
        os.chdir(orig_dir)


if __name__ == "__main__":
    print("=== Generating test data ===")
    df = generate_data()
    print(df.describe())
    
    print("\n=== Running Stata ===")
    stata_results = run_stata()
    
    if stata_results:
        print("\n=== Stata Results ===")
        print(json.dumps(stata_results, indent=2))
