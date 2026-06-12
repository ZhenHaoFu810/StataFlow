# 本地 Stata 17 调用手册

> 本文面向在 Windows 本机参与 StataFlow 开发和验证的 AI Agent。执行任何 golden dual-run、Stata 对照或 `.do` 文件诊断前，先阅读本文。

最后验证：2026-06-12  
项目根目录：`D:/OneDrive - SAIF/PhD3/StataFlow`  
本机 Stata：`D:/Software/Stata17/StataMP-64.exe`

---

## 1. 本机固定配置

本项目当前使用：

```text
D:\Software\Stata17\StataMP-64.exe
```

先在 PowerShell 中验证文件，而不是猜测安装位置：

```powershell
Test-Path -LiteralPath 'D:\Software\Stata17\StataMP-64.exe'
Get-Item -LiteralPath 'D:\Software\Stata17\StataMP-64.exe'
```

第一条必须返回 `True`。如果返回 `False`，停止执行 golden tests，先报告本机 Stata 不可用。

项目 Runner 的默认路径定义在：

```text
src/stataflow/stata_runner/runner.py
```

查找顺序是：

1. `StataRunner(stata_path=...)` 显式路径；
2. 固定默认路径 `D:\Software\Stata17\StataMP-64.exe`；
3. `D:\Software\Stata17` 下的常见 Stata 可执行文件名；
4. Windows `PATH`。

**重要：当前实现不会读取 `STATA_PATH` 环境变量。** 即使异常信息提到设置 `STATA_PATH`，也不要依赖它。需要覆盖路径时，显式传入 `stata_path`。

---

## 2. 推荐调用方式：项目 StataRunner

不要优先手写 `subprocess`。项目标准入口是：

```python
from stataflow.stata_runner import StataRunner
```

在项目根目录运行以下 smoke test：

```powershell
Set-Location 'D:\OneDrive - SAIF\PhD3\StataFlow'
$env:PYTHONPATH="$PWD\src"

@'
from pathlib import Path
from stataflow.stata_runner import StataRunner

output_dir = Path("stata/output/agent-smoke").resolve()
runner = StataRunner(
    stata_path=r"D:\Software\Stata17\StataMP-64.exe"
)

result = runner.run_do_file(
    """
clear all
set more off
display "STATAFLOW_STATA_SMOKE_OK"
exit, clear
""",
    output_dir=str(output_dir),
    timeout=120,
)

print("resolved_path:", runner.resolved_stata_path)
print("exit_code:", result.exit_code)
print("log_file:", result.log_file)
print("error_message:", result.error_message)
print(
    "marker_found:",
    "STATAFLOW_STATA_SMOKE_OK" in (result.output_content or ""),
)

if result.exit_code != 0:
    raise SystemExit("Stata process failed")
if result.log_file is None:
    raise SystemExit("Stata did not create a log file")
if "STATAFLOW_STATA_SMOKE_OK" not in (result.output_content or ""):
    raise SystemExit("Stata log does not contain the success marker")
'@ | python -
```

正确结果必须同时满足：

```text
resolved_path: D:\Software\Stata17\StataMP-64.exe
exit_code: 0
log_file: ...\stata\output\agent-smoke\run_<timestamp>.log
error_message: None
marker_found: True
```

2026-06-12 已在本机按上述方式实际运行成功。

---

## 3. Runner 实际如何启动 Stata

Runner 在输出目录中创建唯一名称：

```text
run_<timestamp>.do
run_<timestamp>.log
```

核心 Windows 命令结构是：

```text
cd /d "<output_dir>" && "D:\Software\Stata17\StataMP-64.exe" /e do <do_file_name>
```

关键规则：

- 使用 `/e do`，不要擅自改成图形界面启动。
- 先切换到 `.do` 文件所在目录。
- `/d` 必须保留，否则 `cmd.exe` 可能无法跨盘符切换目录。
- 可执行文件路径必须加引号。
- Runner 只把 `.do` 的文件名传给 Stata，不传另一套相对路径。
- Stata 自动把 `.log` 写在当前工作目录，因此错误工作目录经常表现为“找不到日志”。
- 项目路径含空格，任何手写命令都必须正确引用路径。

仅在排查 Runner 本身时，才手动执行：

```powershell
$out = 'D:\OneDrive - SAIF\PhD3\StataFlow\stata\output\manual-smoke'
New-Item -ItemType Directory -Force -Path $out | Out-Null

@'
clear all
set more off
display "STATAFLOW_MANUAL_SMOKE_OK"
exit, clear
'@ | Set-Content -Encoding ascii -LiteralPath "$out\manual_smoke.do"

cmd.exe /d /s /c "cd /d `"$out`" && `"D:\Software\Stata17\StataMP-64.exe`" /e do manual_smoke.do"
Get-Content -LiteralPath "$out\manual_smoke.log"
```

正常开发和 golden 测试仍应使用 `StataRunner`，避免不同 Agent 各自实现不一致的调用逻辑。

---

## 4. 运行项目测试

### 4.1 Runner 自检

```powershell
Set-Location 'D:\OneDrive - SAIF\PhD3\StataFlow'
$env:PYTHONPATH="$PWD\src"
pytest tests/test_stata_runner.py -v
```

### 4.2 单个 golden 测试

先运行单文件，不要一开始就运行整个 golden 套件：

```powershell
$env:PYTHONPATH="$PWD\src"
pytest tests/golden/test_p1_ols_basic.py -v -s
```

### 4.3 完整 golden 套件

```powershell
$env:PYTHONPATH="$PWD\src"
pytest tests/golden/ -v
```

完整套件耗时较长，并可能连续启动大量 Stata 进程。只有在单个 smoke test 和相关 golden 子集通过后才运行。

---

## 5. 输出目录规则

允许写入：

```text
stata/output/
stata/cases/
```

推荐每个诊断任务使用独立子目录：

```text
stata/output/agent-smoke/
stata/output/<issue-id>/
stata/output/<golden-case>/
```

不要使用：

- `C:\` 根目录；
- 系统临时目录；
- 项目外的随机目录；
- 另一个 worktree 的 `stata/output`；
- 包含用户隐私、license 或私有数据的目录。

运行前可以创建目录，但不要删除其他 Agent 已生成的证据。Runner 使用毫秒时间戳降低 OneDrive 锁冲突风险。

---

## 6. 如何判断真正成功

不能只看 `exit_code == 0`。Windows/Stata 某些错误仍可能留下进程级成功状态。

每次调用至少检查：

1. `result.exit_code == 0`；
2. `result.log_file` 不为 `None`；
3. 日志文件真实存在；
4. `result.output_content` 非空；
5. 日志包含预期 marker 或预期 `display` 输出；
6. 日志不含 Stata 错误码，例如 `r(199)`、`r(601)`；
7. 需要的结果文件或矩阵确实生成；
8. 测试解析到的字段不是空值或旧日志残留。

推荐在诊断 `.do` 文件结尾写入唯一 marker：

```stata
display "STATAFLOW_CASE_<ISSUE_ID>_OK"
exit, clear
```

如果调用社区命令，如 `reghdfe`、`ivreghdfe`、`ppmlhdfe`、`csdid`、`did_imputation` 或 `rdrobust`，还要检查日志中是否出现：

```text
command ... is unrecognized
r(199)
```

这通常表示 ado 包没有安装或 `adopath` 不正确，不是 Python estimator 的数值失败。

---

## 7. 常见失败与排查

### 7.1 `Cannot find Stata executable`

依次执行：

```powershell
Test-Path -LiteralPath 'D:\Software\Stata17\StataMP-64.exe'
$env:PYTHONPATH="$PWD\src"
python -c "from stataflow.stata_runner.runner import find_stata_executable; print(find_stata_executable())"
```

仍失败时显式使用：

```python
StataRunner(stata_path=r"D:\Software\Stata17\StataMP-64.exe")
```

不要只设置 `STATA_PATH`；当前 Runner 不读取它。

### 7.2 `exit_code=0` 但没有 `.log`

常见原因：

- Stata 启动时工作目录错误；
- `.do` 文件不在 `output_dir`；
- 手写命令没有先 `cd /d`；
- OneDrive 正在锁定文件；
- Agent 立即读取了错误的固定日志名；
- 多个进程同时覆盖同一 `.do/.log`。

优先改用 `StataRunner.run_do_file()`，并检查其返回的 `log_file`，不要自行猜日志路径。

### 7.3 Stata 进程超时

- 先把 `timeout` 提高到 `300` 或 `600` 秒；
- 查看是否有 Stata 窗口、许可提示或异常进程残留；
- 检查 `.do` 中是否有交互式命令、`pause`、`more` 或未终止循环；
- 确保开头有 `set more off`；
- 一次只运行一个诊断任务。

不要在同一机器上并发启动多个完整 golden 套件。并发 Stata 调用会增加 license、日志、OneDrive 锁和资源争用问题。

### 7.4 `r(601)` 或数据文件找不到

Stata 解析的是它自己的当前工作目录，不是 Python 文件所在目录。优先在 `.do` 中使用规范化绝对路径：

```stata
use "D:/OneDrive - SAIF/PhD3/StataFlow/stata/cases/example.dta", clear
```

Stata 路径推荐使用正斜杠 `/`。不要假定 pytest 当前目录与 Stata 当前目录相同。

### 7.5 `r(199)` 或社区命令未识别

这表示命令安装或 `adopath` 问题。先运行：

```stata
which reghdfe
which ivreghdfe
which ppmlhdfe
which csdid
which did_imputation
which eventstudyinteract
which rdrobust
adopath
```

把输出写入日志并保留。不要把“命令未安装”误判为 Python 与 Stata 数值不一致。

### 7.6 测试读取固定日志时报 `FileNotFoundError`

部分旧 golden 测试直接读取预生成的固定 `.log`，并不调用 Runner 生成日志。先阅读测试 fixture，确认它属于：

- 动态 dual-run；或
- 静态日志回放。

静态日志不存在时，应补齐可重复生成流程或验证资产，不能通过创建空文件、跳过测试或复制无关日志解决。

### 7.7 日志乱码

Runner 用 UTF-8 且 `errors="replace"` 读取日志。Stata 日志中的少量替换字符不一定表示执行失败。判断应基于错误码、marker 和数值字段，不要只凭终端显示。

---

## 8. Agent 强制规则

- 先验证固定路径，再运行 Stata。
- 优先使用项目 `StataRunner`。
- 显式设置 `PYTHONPATH=<repo>/src`。
- `.do` 开头使用 `clear all` 和 `set more off`。
- 使用 `/e do`，并确保 Stata 工作目录是输出目录。
- 每个诊断使用唯一 marker 和独立输出子目录。
- 检查日志内容，不以进程退出码作为唯一成功证据。
- 不并发运行多个 Stata/golden 任务。
- 不覆盖、删除或伪造现有 Stata 验证证据。
- 不提交 Stata license、私有数据和纯临时 smoke artifacts。
- 未实际运行 Stata 时，不得声称“Stata 双跑通过”。

遇到调用失败时，报告至少应包含：

```text
resolved executable
working directory
do-file path
log-file path
exit code
timeout
error message
log tail
expected marker
whether the marker was found
```

---

## 9. 最短可靠检查清单

```powershell
Set-Location 'D:\OneDrive - SAIF\PhD3\StataFlow'
Test-Path -LiteralPath 'D:\Software\Stata17\StataMP-64.exe'
$env:PYTHONPATH="$PWD\src"
python -c "from stataflow.stata_runner.runner import find_stata_executable; print(find_stata_executable())"
pytest tests/test_stata_runner.py -v
pytest tests/golden/test_p1_ols_basic.py -v -s
```

只有上述步骤依次成功后，才继续运行相关命令族或完整 golden 套件。
