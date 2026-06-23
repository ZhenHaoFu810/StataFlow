from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from stataflow.stata_runner import StataRunner
runner=StataRunner()
res=runner.run_do_file((Path(__file__).parent/'probe_weight2.do').read_text(), output_dir=str(Path(__file__).parent/'..'/'..'/'output'/'audit_v1_3_m06'))
Path('stata/output/audit_v1_3_m06/probe_weight2.log').write_text(res.output_content or res.error_message or '', encoding='utf-8', errors='replace')
print('exit', res.exit_code)
