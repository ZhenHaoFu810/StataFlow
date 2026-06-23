# M10-RUNNER-001 最小复现

## 问题

`StataRunner.run_do_file` 在 Stata 命令出现运行时错误时仍返回 `exit_code=0`。

## 复现步骤

```python
from stataflow.stata_runner import StataRunner
import pandas as pd

df = pd.DataFrame({"y": [1, 2, 3], "x": [1, 2, 3]})
df.to_stata("stata/output/m10_audit/runner_repro.dta", write_index=False)

do = '''
version 17
set more off
use "stata/output/m10_audit/runner_repro.dta", clear
regress y nonexistent_var
'''

result = StataRunner().run_do_file(do, output_dir="stata/output/m10_audit")
print(result.exit_code)          # 0
print("r(111)" in result.output_content or "not found" in result.output_content.lower())  # True
```

## 预期行为

调用方通常期望 `exit_code != 0` 来表示 Stata 执行失败；当前实现需要额外解析 log。

## 证据文件

- `tests/audit_v1_3/m10_shared_infrastructure/test_m10_synthetic.py::TestS05StataRunner::test_s05_invalid_command_logged`
