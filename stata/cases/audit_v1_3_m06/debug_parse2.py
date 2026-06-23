import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
log = Path('stata/output/audit_v1_3_m06/probe_S1.log').read_text(encoding='utf-8')
for m in re.finditer(r'COEF_(\S+)=(\S+)', log):
    start = max(0, m.start()-50)
    end = min(len(log), m.end()+20)
    print(repr(log[start:end]))
