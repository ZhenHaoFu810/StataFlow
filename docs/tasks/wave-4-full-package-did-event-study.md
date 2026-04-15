# Wave 4 Full Package: DID / Event Study Extensions

## 基本信息

- 任务名称：Wave 4 整包任务：DID / Event Study Extensions
- 所属命令族：`DID / Event Study Extensions`
- 优先级：P4
- 执行人：Claude Code
- 审查人：Codex

## 任务目标

一次性推进整个 Wave 4，但必须按内部阶段顺序完成，不能跳阶段宣称整包完成。

本 wave 的目标命令为：

- `did_imputation`
- `eventstudyinteract`
- `csdid`

目标不是复刻每个命令的全部历史选项，而是交付一个**最小但统计口径清楚、可双跑验证、能进入回归测试**的兼容子集。

## 内部阶段

### Stage A: Research Closure

必须先完成以下研究工作，再进入实现：

- 补齐或重写下列研究文档：
  - `docs/research/did_imputation.md`
  - `docs/research/eventstudyinteract.md`
  - `docs/research/csdid.md`
- 对每个命令写清：
  - 目标 estimand
  - 数据结构要求
  - 识别假设
  - 核心估计公式
  - 推断口径
  - Stata/社区命令的关键选项
  - 最小兼容子集
  - 明确不做的选项
- 在 `docs/testing/test-case-catalog.md` 预登记：
  - synthetic 样例
  - real-data 样例
  - 对齐字段

### Stage B: Minimum Implementation

对三个命令都做最小实现，但范围必须收紧。

#### `did_imputation`

最小子集要求：

- staggered adoption panel
- balanced 或近平衡 panel
- 单次吸收处理
- 单位聚类标准误
- event time 动态效应输出

明确不做：

- repeated cross-section
- 多值处理
- 多层 bootstrap
- 复杂 aggregation 变体

#### `eventstudyinteract`

最小子集要求：

- Sun-Abraham interaction-weighted event-study
- cohort × relative-time 结构
- 单位 FE + 时间 FE
- 单位聚类标准误
- 基准期显式可控

明确不做：

- 多向 cluster
- 高级 postestimation
- 图形输出

#### `csdid`

最小子集要求：

- panel 版本优先
- group-time ATT 输出
- 至少支持一个常用 aggregation
- 单位聚类标准误

明确不做：

- repeated cross-section
- doubly robust 的所有分支变体一次性全开
- bootstrap-based 全部推断选项

### Stage C: Real-Data Validation And Hardening

每个命令都必须至少有：

- 1 个 synthetic 黄金样例
- 1 个真实公开数据样例

并完成：

- Stata / Python 双跑
- 字段级对齐报告
- 已知差异文档化
- `docs/backlog.md` 与 `docs/testing/test-case-catalog.md` 状态同步

## 真实数据要求

优先使用公开、可复现、带有经典 staggered adoption 结构的数据。

推荐候选：

- Castle Doctrine / stand-your-ground 风格州年面板
- minimum wage / policy adoption 州年面板
- 公开县年政策 panel
- Stata / Wooldridge / teaching datasets 中可复现的 staggered treatment 子集

要求：

- 数据必须落到本地研究目录
- 文档中记录来源、清洗、变量定义、Stata 命令、Python 命令

## 允许修改的文件

- `src/statapy/estimators/` 下与 DID / event study 相关的新文件
- `src/statapy/__init__.py`
- `src/statapy/estimators/__init__.py`
- `tests/golden/` 下新增的 Wave 4 测试
- `docs/research/` 下的 Wave 4 文档
- `docs/testing/test-case-catalog.md`
- `docs/backlog.md`
- `workspace/current-task/REPORT.md`

## 禁止事项

- 不要扩展到 `drdid`、`did2s`、`bacondecomp`、`honestdid`
- 不要在本 wave 混入 `predict`、`margins`、图形接口
- 不要一次性实现所有 bootstrap / simulation / randomization inference
- 不要引入多向 cluster
- 不要把未验证的统计差异写成“可接受”后直接放行

## 强制验证命令

完成后必须至少运行：

```bash
python -m pytest tests/golden/test_w4_did_imputation_basic.py -v
python -m pytest tests/golden/test_w4_eventstudyinteract_basic.py -v
python -m pytest tests/golden/test_w4_csdid_basic.py -v
python -m pytest tests -v
```

如果新增了更多 Wave 4 golden tests，必须在报告中逐项列出并运行。

## 回报要求

报告必须分 Stage A / Stage B / Stage C 三段，明确写清：

1. 三个命令各自的最小实现边界
2. 每个命令的识别假设与 estimand
3. 每个命令新增了哪些 synthetic 样例
4. 每个命令用了哪些真实公开数据
5. 哪些字段与 Stata 对齐，哪些字段若仍有偏差，偏差原因是什么
6. 全量测试结果

## 通过标准

只有同时满足以下条件，Codex 才会放行整个 Wave 4：

- `did_imputation`、`eventstudyinteract`、`csdid` 都完成研究档案
- 三个命令都至少有 synthetic 黄金样例
- 三个命令都至少有一个真实公开数据双跑样例
- 全量测试通过
- `docs/backlog.md` 与 `docs/testing/test-case-catalog.md` 状态一致
- 没有未解释的关键统计口径偏差
