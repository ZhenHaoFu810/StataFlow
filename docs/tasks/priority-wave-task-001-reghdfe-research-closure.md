# Priority Wave Task 001：`reghdfe` 研究收束与实现边界确认

## 基本信息

- 任务名称：`reghdfe` 研究收束与实现边界确认
- 所属命令族：`Panel / FE / HDFE`
- 对应 backlog 条目：`reghdfe`
- 优先级：P1
- 执行人：Claude Code
- 审查人：Codex

## 任务目标

本轮是 `Priority Wave: reghdfe` 的 Round 1，只做研究收束，不做实现。

需要交付：

1. 将现有 `reghdfe` 研究档案收束为可直接进入最小实现的规格说明。
2. 基于本地源码镜像，明确：
   - 最小实现的 `ado` / `mata` 入口
   - 需要优先模仿的算法路径
   - 暂不支持的选项面
3. 将 `reghdfe Phase A` 的最小兼容子集写清楚：
   - `absorb()` 支持 1-2 组 FE
   - `vce(ols)`
   - 单 `cluster`
   - singleton 默认 drop 的口径
   - `df_a`、`df_r`、`F` 的重点对齐字段
4. 检查并补齐 `synthetic` 与 `real_data` 样例设计，使其足以支撑下一轮最小实现。
5. 形成一份结构化研究回报，明确是否可以开放 `reghdfe` 最小实现。

## 必读文档

1. `docs/operations/executor-playbook.md`
2. `docs/project-charter.md`
3. `docs/roadmap.md`
4. `docs/roadmap-execution-rounds.md`
5. `docs/research/reghdfe.md`
6. `docs/research/stata-source-inventory.md`
7. `docs/research/public-datasets.md`
8. 本任务卡

## 本轮允许修改的文件

- `docs/research/reghdfe.md`
- `docs/research/stata-source-inventory.md`
- `docs/testing/test-case-catalog.md`
- `workspace/current-task/REPORT.md`

如确有必要，可新增：

- `docs/research/reghdfe-phase-a-notes.md`

## 本轮禁止事项

- 不得修改 `src/statapy/` 下任何实现代码
- 不得新增 `reghdfe` 的 Python API 实现
- 不得顺势扩展到 `ivreghdfe`、`ppmlhdfe` 或多向 cluster
- 不得把研究结论直接写成“已完成实现”
- 不得把未验证的统计差异提前认定为“可接受”

## 需要完成的研究内容

### A. 本地源码入口收束

至少明确：

- `reghdfe.ado` 的主命令入口
- 关键 `mata` 文件与职责划分
- 哪条算法路径最适合作为 Python `Phase A` 的最小参考实现
- 是否依赖 `ftools` 的特定行为，若依赖，如何在 Python 中抽象替代

### B. `Phase A` 最小实现边界

至少写清：

- 支持哪些 `absorb()` 形态
- 单 `cluster` 的最小语义
- singleton 处理口径
- `df_a`、`df_r`、`N_clust`、`F` 的验收字段
- `_cons`、系数命名、结果对象元数据如何表达

### C. 测试设计收束

至少确认或补齐：

- `p3_reghdfe_basic`
- `p3_reghdfe_cluster`
- `p3_reghdfe_real_panel`

每个样例都要写明：

- 使用哪组数据
- Stata 命令
- 预期 Python API
- 主要风险点
- 本轮之后是 `ready` 还是仍应 `planned`

## 回报要求

回报必须至少包含：

- 修改文件清单
- `reghdfe Phase A` 的明确功能边界
- 本地源码入口与优先参考路径
- 建议的最小测试矩阵
- 尚未解决的统计风险
- 是否建议开放 `Priority Wave Task 002 - reghdfe 最小实现`

## 验收标准

- `docs/research/reghdfe.md` 已能直接支撑实现轮
- 本地源码入口、依赖和算法优先路径已明确
- `docs/testing/test-case-catalog.md` 中 `reghdfe` 样例登记完整且状态合理
- 本轮未触碰任何实现代码
- 回报中无“研究代替实现完成”的表述
