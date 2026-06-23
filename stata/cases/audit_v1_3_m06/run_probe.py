from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from stataflow.stata_runner import StataRunner

runner = StataRunner()
result = runner.run_do_file(
    (Path(__file__).parent / 'probe_ppmlhdfe.do').read_text(),
    output_dir=str(Path(__file__).parent / '..' / '..' / 'output' / 'audit_v1_3_m06')
)
print('exit_code:', result.exit_code)
print(result.output_content or result.error_message)
