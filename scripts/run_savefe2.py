import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from stataflow.stata_runner.runner import StataRunner

with open("D:/OneDrive - SAIF/PhD3/StataFlow/stata/output/phase2/test_savefe2.do", "r", encoding="utf-8") as f:
    content = f.read()

runner = StataRunner()
result = runner.run_do_file(content, output_dir="D:/OneDrive - SAIF/PhD3/StataFlow/stata/output/phase2")
print("exit_code:", result.exit_code)
print("error:", result.error_message)
if result.output_content:
    with open("D:/OneDrive - SAIF/PhD3/StataFlow/stata/output/phase2/test_savefe2.log", "w", encoding="utf-8") as f:
        f.write(result.output_content)
    print("log saved")
