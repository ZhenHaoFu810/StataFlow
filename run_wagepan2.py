from statapy.stata_runner import StataRunner
import os
import time

runner = StataRunner()
output_dir = "stata/output"
os.makedirs(output_dir, exist_ok=True)

with open("stata/cases/check_wagepan.do", "r", encoding="utf-8") as f:
    do_content = f.read()

ts = int(time.time() * 1000)
result = runner.run_do_file(do_content, output_dir=output_dir)

log_path = result.log_file
if not log_path or not os.path.exists(log_path):
    logs = [f for f in os.listdir(output_dir) if f.endswith(".log")]
    latest = sorted(logs, key=lambda f: os.path.getmtime(os.path.join(output_dir, f)))[-1]
    log_path = os.path.join(output_dir, latest)

with open(log_path, "r", encoding="utf-8", errors="replace") as f:
    txt = f.read()

with open("stata/output/wagepan_log2.txt", "w", encoding="utf-8") as out:
    out.write(txt)

with open("stata/output/wagepan_meta2.txt", "w", encoding="utf-8") as f:
    f.write(f"exit_code: {result.exit_code}\n")
    f.write(f"log_path: {log_path}\n")
    f.write(f"error_repr: {repr(result.error_message)}\n")
