import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from stataflow.stata_runner.runner import StataRunner

with open("D:/OneDrive - SAIF/PhD3/StataFlow/stata/output/phase2/panel_validation.do", "r", encoding="utf-8") as f:
    content = f.read()

runner = StataRunner()
result = runner.run_do_file(content, output_dir="D:/OneDrive - SAIF/PhD3/StataFlow/stata/output/phase2")
print("exit_code:", result.exit_code)
print("log_file:", result.log_file)
print("error:", result.error_message)
if result.output_content:
    # Write log to a known file for inspection
    with open("D:/OneDrive - SAIF/PhD3/StataFlow/stata/output/phase2/panel_validation.log", "w", encoding="utf-8") as f:
        f.write(result.output_content)
    print("Log written to panel_validation.log")
