# Wave 1 Task 001：HDFE 研究基础建设

## 基本信息

- 任务名称：`areg` / `reghdfe` 研究基础建设
- 所属命令族：`Panel / FE / HDFE`
- 对应 backlog 条目：`areg`、`reghdfe`
- 优先级：P1
- 执行人：Claude Code
- 审查人：Codex

## 任务目标

本轮只做研究与设计，不做实现。

需要交付：

1. 把 `docs/research/areg.md` 补成可执行研究档案。
2. 把 `docs/research/reghdfe.md` 补成可执行研究档案。
3. 利用本地源码镜像，定位 `reghdfe` 的核心 `ado` / `mata` 入口、依赖与关键选项。
4. 为 `areg` 和 `reghdfe` 分别设计：
   - synthetic 黄金样例
   - real-data 样例
5. 将对应样例预登记到 `docs/testing/test-case-catalog.md`。
6. 形成一份结构化研究回报，供 Codex 决定下一轮是否开放实现任务。

## 必读文档

1. `docs/operations/executor-playbook.md`
2. `docs/project-charter.md`
3. `docs/roadmap.md`
4. `docs/research/stata-source-inventory.md`
5. `docs/research/public-datasets.md`
6. `docs/research/areg.md`
7. `docs/research/reghdfe.md`

## 本轮允许修改的文件

- `docs/research/areg.md`
- `docs/research/reghdfe.md`
- `docs/research/stata-source-inventory.md`
- `docs/testing/test-case-catalog.md`
- `workspace/current-task/` 下的回报文件

如确有必要，可新增：

- `docs/research/hdfe-notes.md`

## 本轮禁止事项

- 不得修改 `src/statapy/` 下任何实现代码
- 不得新增 `docs/tasks/` 中的实现型任务卡
- 不得改动项目章程、公共 API 原则和统计等价结论
- 不得把“阅读源码得到初步理解”直接写成“已完成实现”

## 需要完成的研究内容

### A. `areg`

至少补齐：

- 命令用途与典型研究场景
- 与 `xtreg, fe` 的关系与差异
- 关键返回值
- 自由度与整体检验统计量需要重点比对的字段
- synthetic 样例设计
- real-data 样例设计
- 最小实现子集建议

### B. `reghdfe`

至少补齐：

- 本地镜像目录中的核心源码入口
- 依赖的其他命令或模块
- 关键选项：
  - `absorb()`
  - `vce(robust)`
  - `vce(cluster)`
  - singleton 处理
  - DoF 修正
- 输出字段与应重点比对的 `e()` 结果
- synthetic 样例设计
- real-data 样例设计
- 最小兼容子集建议

## 样例登记要求

在 `docs/testing/test-case-catalog.md` 中至少预登记以下条目：

- `p3_areg_basic`
- `p3_areg_real_panel`
- `p3_reghdfe_basic`
- `p3_reghdfe_real_panel`

这些条目当前状态应为 `ready`，不是 `done`。

## 建议使用的真实数据

- `areg`
  - `wagepan`
  - `Grunfeld`
- `reghdfe`
  - 先用本地 `wagepan` 或 `Grunfeld` 设计最小真实样例
  - 如果需要更适合的高维 FE 数据，在回报中提出候选，但本轮不强制下载更多数据

## 回报要求

回报必须至少包含：

- 修改文件清单
- `areg` 研究结论摘要
- `reghdfe` 研究结论摘要
- `reghdfe` 本地源码入口路径
- 建议的最小实现子集
- 预登记样例清单
- 是否建议下一轮开放实现任务

## 验收标准

- `docs/research/areg.md` 已从占位升级为可执行研究档案
- `docs/research/reghdfe.md` 已从占位升级为可执行研究档案
- `docs/testing/test-case-catalog.md` 已登记 `areg` / `reghdfe` 的 synthetic 和 real-data 条目
- 回报中明确写出 `reghdfe` 的本地源码入口与依赖
- 本轮没有触碰任何实现代码
