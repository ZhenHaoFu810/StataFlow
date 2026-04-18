# 审计后任务包 001：`rdrobust` 最小可验证实现 + Vendor 命令完整度收口

## 1. 任务定位

这是审计后的第一张新任务卡。

目标不是继续零散补功能，而是同时完成两件事：

1. 把 `rdrobust` 从“仅有本地源码镜像、无 Python 实现”的状态，推进到**最小可验证实现**。
2. 把 `research/vendor/stata_community/` 下 6 个开源命令的**完整度状态、支持矩阵、source map、测试证据**全部收口到可供 Codex 严格审查的状态。

本轮是一个**大任务包**。允许改实现、测试、文档和示例，但不允许模糊边界。

## 2. 本轮必须完成的内容

### A. `rdrobust` 进入真实实现层

至少完成以下内容：

- 在 `src/statapy/estimators/` 中新增 `rdrobust` 的核心 estimator
- 在 `src/statapy/compat/stata/` 中新增 `rdrobust()` wrapper
- 在 `src/statapy/__init__.py` 与 `src/statapy/compat/stata/__init__.py` 中正确导出
- 在 `docs/command-support-matrix/` 中新增 `rdrobust.md`
- 在 `docs/research/` 中新增或补全 `rdrobust-source-map.md`
- 在 `tests/` 中新增 synthetic 测试与至少 1 个 real-data / official-example 风格测试

### B. `rdrobust` 的最小支持边界必须明确

本轮不要求完整覆盖 `rdrobust` 的全部历史选项，但最小实现必须有清楚的数学与命令语义边界。

最低要求：

- sharp RD 主路径
- 本地多项式回归核心估计
- 至少一种 kernel
- 至少一种 bandwidth 选择路径，或明确要求用户显式传带宽
- 与 Stata 命令/源码一致的点估计和关键推断对象
- 结果对象中核心字段的稳定语义

如果某些关键复杂功能本轮不做，例如：

- fuzzy RD
- covariate-adjusted RD
- cluster VCE
- 完整 bandwidth selector 家族
- rdplot / rdbwselect 全命令面

必须：

- 显式 hard-reject
- 写入 support matrix
- 写入 source map 的“未实现”部分
- 在报告里解释为什么没做

### C. Vendor 六命令完整度矩阵统一收口

必须重新核对并更新以下命令的 support matrix 和 source map：

- `reghdfe`
- `ivreghdfe`
- `ppmlhdfe`
- `did_imputation`
- `eventstudyinteract`
- `rdrobust`

每个命令都必须明确分成三类：

- 已实现并验证
- 已实现但只是子集 / Phase A
- 未实现或显式拒绝

不得继续出现“命令存在”但“完整度不清楚”的写法。

### D. 测试与证据链升级

本轮新增的测试不能只是“为了让数字过”。

必须同时包含：

- synthetic / controlled case
- real-data 或官方示例 case
- 至少一个直接针对数学过程的检查

`rdrobust` 至少需要：

- 1 个 synthetic case：检查 cutoff 两侧局部多项式估计与报告字段
- 1 个 real-data / official-example case：优先使用本地 `research/vendor/stata_community/rdrobust/` 中可复现数据或示例

另外，需要至少补 1 个“反凑数值”测试，例如：

- 错误参数必须显式报错
- 关键字段不能被跳过
- bandwidth / kernel / cutoff 变化会引起可解释的结果变化

## 3. 数学与源码对齐要求

### A. 禁止事项

以下任一做法都视为本轮失败：

- 通过调宽容差让 `rdrobust` 过测试
- 只对单一样例反推数值
- 无法说明估计量、偏差修正、标准误来自源码或手册何处
- wrapper 暴露了参数，但参数实际上未生效

### B. 必须可解释的问题

你在实现 `rdrobust` 后，必须能在报告中明确回答：

- Python 实现的估计对象是什么
- Stata 源码主入口是哪个 `.ado` / `.do` / `.mata` / 其他文件
- 带宽、kernel、局部多项式是如何对应到 Python 实现的
- 推断对象是什么，标准误如何构造
- 本轮做的是完整 `rdrobust`，还是最小子集；如果是子集，缺的具体是什么

### C. 若无法完整解释

如果在本轮中发现 `rdrobust` 某部分没法在源码/手册上说清楚，则：

- 可以保留最小实现
- 但必须把未解释部分列为未完成
- 不能因为测试过了就宣称“完整实现”

## 4. 允许修改的范围

本轮允许修改：

- `src/statapy/estimators/`
- `src/statapy/compat/stata/`
- `src/statapy/__init__.py`
- `src/statapy/compat/stata/__init__.py`
- `tests/`
- `docs/command-support-matrix/`
- `docs/research/`
- `docs/testing/test-case-catalog.md`
- `docs/backlog.md`
- `README.md`（如需新增 `rdrobust` 命令说明）
- `workspace/current-task/REPORT.md`

## 5. 不允许修改的范围

本轮不要擅自修改：

- `docs/project-charter.md`
- `docs/architecture/public-api.md` 的顶层原则
- `docs/operations/codex-review-protocol.md`

除非你发现这些文档与本轮实现直接矛盾，并在报告中明确说明原因。

## 6. 验证要求

本轮至少执行并回报以下验证：

### 全量基线

```powershell
python -m pytest tests -v
```

### `rdrobust` 专项

你新增的 `rdrobust` 测试文件必须单独 fresh run。

### Vendor 相关专项

至少重新跑一组与 vendor 命令相关的专项测试，确保本轮改动没有破坏已有命令：

- `tests/test_hdfe_synthetic.py`
- `tests/test_compat_stata_did.py`
- 至少一组 `reghdfe` / `ppmlhdfe` / `did_imputation` golden tests

### 运行时抽查

至少实际调用一次：

- `statapy.compat.stata.rdrobust(...)`
- 一个已有 vendor wrapper，例如 `reghdfe(...)` 或 `ppmlhdfe(...)`

确保 wrapper 语义、返回对象和文档一致。

## 7. 完成标准

本轮要被视为通过，至少需要满足：

1. `rdrobust` 已经不再是 “missing”
2. `rdrobust` 有真实 Python 实现、wrapper、support matrix、source map、测试
3. 六个 vendor 命令的完整度状态全部清楚
4. support matrix / source map / tests / report 不互相打架
5. 没有发现“为了过测试而凑数值”的证据

## 8. 报告格式要求

在 [workspace/current-task/REPORT.md](</D:/OneDrive - SAIF/PhD3/Stata2Python/workspace/current-task/REPORT.md>) 中按以下结构回报：

### 1. 本轮改动概览

### 2. `rdrobust` 实现说明

- 估计对象
- 源码入口
- 本轮支持参数
- 本轮明确不支持参数

### 3. Vendor 六命令完整度更新表

必须逐个写：

- `reghdfe`
- `ivreghdfe`
- `ppmlhdfe`
- `did_imputation`
- `eventstudyinteract`
- `rdrobust`

### 4. 验证结果

- 全量测试
- `rdrobust` 专项
- 其他专项

### 5. 已知剩余问题

### 6. 请求 Codex 重点审查的问题

如果你不确定某处是否达到了“数学过程对齐”的标准，必须点名让我重点审。

