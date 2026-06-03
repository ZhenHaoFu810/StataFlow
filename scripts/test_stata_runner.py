import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from stataflow.stata_runner.runner import StataRunner

runner = StataRunner()
with open("D:/OneDrive - SAIF/PhD3/StataFlow/stata/output/phase2/test_reghdfe_avail.do", "r") as f:
    content = f.read()

result = runner.run_do_file(content, output_dir="D:/OneDrive - SAIF/PhD3/StataFlow/stata/output/phase2")
print("exit_code:", result.exit_code)
print("log_file:", result.log_file)
print("error:", result.error_message)
if result.output_content:
    print("--- LOG ---")
    print(result.output_content)
