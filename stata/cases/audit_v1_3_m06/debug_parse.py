import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
log = Path('stata/output/audit_v1_3_m06/probe_S1.log').read_text(encoding='utf-8')
print('found COEF matches:')
for m in re.finditer(r'COEF_(\S+)=(-?[\d.eE+]+)', log):
    print(m.group(1), m.group(2))
print('found SE matches:')
for m in re.finditer(r'SE_(\S+)=(-?[\d.eE+]+)', log):
    print(m.group(1), m.group(2))
