# 任务卡：Package A - Correctness and Release Hygiene

## 背景

根据最新审计，`StataFlow` 当前最需要的不是继续快速扩命令数量，而是先清理已经确认的正确性问题、元数据漂移、文档冲突、编码问题和发布级基础卫生问题。

这一步的作用是为后续功能补全建立干净、可信、可持续的基线。

本任务卡对应总计划中的：

- `Phase 0：正确性与发布清障`
- 以及后续所有包的共同前置条件

## 总目标

在 `D:\OneDrive - SAIF\PhD3\StataFlow` 中完成一轮 **不扩功能范围、但显著提升正确性与发布质量** 的修复。

这轮的目标不是“做更多命令”，而是：

1. 修掉已确认的实现层问题
2. 修掉版本号和公开说明漂移
3. 修掉 support matrix 与实现不一致的问题
4. 修掉中文 Markdown 编码/乱码问题
5. 建立后续开发可依赖的干净基线

## 本轮必须完成的任务

## A1. 复核并修复已确认的实现层问题

### A1.1 `did_imputation(..., allhorizons=...)` 当前无效

已知审计发现：

- `src/stataflow/estimators/did_imputation.py` 中
- `if allhorizons:` 与 `else:` 分支计算逻辑相同
- 导致 `allhorizons` 当前实际是 no-op

你必须：

- 先确认该问题仍然存在
- 明确该参数按当前项目语义本应如何工作
- 做出正确修复
- 补充回归测试
- 更新相关文档

不允许：

- 通过删参数、绕过参数、或仅改文档来规避

## A1.2 复核其他显式可疑的一致性问题

已知审计还发现：

- `src/stataflow/__init__.py` 版本号与 `pyproject.toml` 不一致
- `AbsorbingOLS` 内部存在 `_collinear_dropped` / `_colinear_dropped` 拼写漂移

你必须：

- 判断这些问题是否真实存在
- 修复真正的问题
- 若只是冗余或历史残留，也要明确清理策略

## A2. 修复版本元数据与公开信息漂移

### 已知问题

- `pyproject.toml` 当前版本是 `0.1.4`
- `src/stataflow/__init__.py` 仍暴露 `0.1.0`

你必须：

- 统一版本号来源
- 确保用户从包接口读取到的版本与发布元数据一致
- 检查是否还有其他版本号或项目名漂移

如果你发现更好的长期方案，例如从单一源自动读取版本，也可以实现，但不要做无关重构。

## A3. 修复 support matrix / 实现 / 示例之间的明显冲突

### 已知问题 1：`ppmlhdfe` 文档自相矛盾

已知审计发现：

- `docs/command-support-matrix/ppmlhdfe.md` 示例使用了 3 个 absorbed FE
- 但同页又写只支持 1-2 个 FE

你必须：

- 修正这一冲突
- 检查是否还有类似的同页或跨页冲突

### 已知问题 2：`rdrobust` 说明漂移

已知审计发现：

- `src/stataflow/estimators/rdrobust.py` 顶部说明仍把 `bwselect` / `covs` 写成不支持
- 但实现、测试和 support matrix 已支持 `bwselect="mserd"` 与 `covs`

你必须：

- 统一注释、实现、测试、support matrix 的表述

### A3 的总体要求

请至少全面复查这些位置：

- `docs/command-support-matrix/*`
- `README.md`
- 对应 estimator / wrapper 文件头部注释
- 与这些命令相关的 examples

目标不是重写全部文档，而是清理那些会直接误导外部用户的公开冲突。

## A4. 中文 Markdown 编码与乱码修复

### 背景

仓库内已有多份中文 Markdown 文件存在编码不稳定、终端显示乱码、或文件本身已损坏的情况。

本轮至少要处理：

- `docs/audit/next-development-plan.md`
- `docs/audit/project-gaps.md`
- `docs/audit/audit-findings.md`
- 以及你在排查中发现的其他中文 Markdown 文件

### 目标

确保这些文档：

- 文件本身采用稳定编码
- 内容实际可读
- 后续导出、开源、协作时不会继续出现乱码

### 要求

- 不只看 PowerShell 显示结果
- 需要判断是终端显示问题，还是文件本身编码/内容已损坏
- 对文件本身已损坏的情况，要明确修复方式
- 统一推荐编码方案，并落实到受影响文件

### 验证要求

你必须给出可复核的验证方式，例如：

- Python 按 UTF-8 读取成功
- 关键文档人工抽样核读正常
- 再次打开文件不会出现内容级乱码

## A5. 做一轮 release hygiene 排查

这部分不要求做“开源导出机制”，但要求你清理当前仓库中明显影响发布可信度的问题。

至少检查：

- 公开文档中的项目名是否一致
- support matrix 中是否仍有明显过期表述
- examples 是否与当前公开 API 一致
- 是否存在会误导发布状态的说明

如果发现问题，能顺手修的就在本轮修；不能修完的写进 `REPORT.md`。

## 不在本轮范围内的事项

以下内容**不是本轮 Package A 的任务**，不要提前扩张：

- `reghdfe` 多维 FE 正式扩展
- `ppmlhdfe` separation 新功能实现
- `ivreghdfe` first-stage / weak-IV / overid diagnostics 新功能实现
- `did_imputation` 的 `window/minn/pretrends` 正式补全
- `eventstudyinteract` / `csdid` 大规模命令面扩展
- `rdrobust` fuzzy / kink / cluster / weights 新功能实现
- open-source export 机制重做

如果你在本轮发现这些问题的证据，可以记到报告里，但不要把本轮做成功能大包。

## 推荐执行顺序

1. 先逐项复核已知问题是否仍存在
2. 修实现层问题并补测试
3. 修版本号与元数据漂移
4. 修 support matrix / README / 注释冲突
5. 修中文 Markdown 编码与乱码问题
6. 跑测试和 examples
7. 完成 `REPORT.md`

## 最低交付物

完成后至少应交付：

- 已修复的代码文件
- 对应新增或更新的测试
- 已修复的 support matrix / README / 注释
- 已修复的中文 Markdown 文件
- 完整的 [REPORT.md](</D:/OneDrive - SAIF/PhD3/StataFlow/workspace/current-task/REPORT.md>)

## 必须在报告中回答的问题

完成后在 `REPORT.md` 中必须明确回答：

1. `allhorizons` 的根因是什么，如何修复，如何验证
2. 版本号漂移出现在什么位置，如何统一
3. 哪些 support matrix / 示例 / 注释存在对外冲突，具体改了什么
4. 哪些中文 Markdown 文件有编码或内容级乱码问题，分别如何处理
5. 本轮本地测试和 example 验证结果是什么
6. 哪些问题仍然存在，但被明确留给 `Package B / C / D`

## 成功标准

只有当以下条件全部满足时，本轮任务才算完成：

- `allhorizons` 问题已修复且有回归测试
- 版本号对外一致
- 已知文档冲突已清理
- 中文 Markdown 编码问题已完成排查和修复
- 测试与 examples 已重新验证
- `REPORT.md` 可供后续审查直接使用

## 协作说明

本轮模式是：

- Claude Code 负责实现和报告
- Codex 后续负责审查

因此你的输出必须做到：

- 变更边界清楚
- 根因解释明确
- 验证证据完整
- 报告可审计
