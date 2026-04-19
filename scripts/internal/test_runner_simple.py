from statapy.stata_runner import StataRunner
from pathlib import Path

runner = StataRunner()
do = """
clear all
set more off
display "HELLO"
"""
result = runner.run_do_file(do, output_dir='stata/output', timeout=120)
print(f"exit={result.exit_code}")
if result.log_file:
    print(f"log_file={result.log_file}")
    if Path(result.log_file).exists():
        with open(result.log_file, 'r', encoding='utf-8', errors='replace') as f:
            print(f.read())
else:
    print("No log file")
