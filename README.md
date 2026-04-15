# Stata2Python

Stata2Python 是一个面向金融与经济学实证研究的计量工具库项目，目标是在 Python 环境中构建一个可扩展的 Stata 命令映射平台，使研究者可以在不切换回 Stata 的情况下完成高频实证建模，并获得与 Stata 17 高度对齐的估计结果、标准误、检验统计量与输出行为。

项目当前已经验证了 `regress`、`vce(robust)`、`vce(cluster)`、`aweight`、`xtreg, fe` 与 FE + cluster 的对齐能力。后续重点不再是零散补命令，而是建立一套“核心估计器 + Stata 兼容层 + 源码研究层 + 双线验证层”的长期平台结构。

## 当前定位

- 核心产品：
  - Python 原生估计器接口
  - Stata 风格兼容命令层
  - Stata/SSC 源码与规则研究档案
  - synthetic + 真实公开数据 的双线验证框架
- 默认目标版本：
  - `Stata 17`
- 当前优先主线：
  - `Panel / FE / HDFE`
  - `Wave 1` 收口后立即进入独立的 `Priority Wave: reghdfe`

## 文档导航

- 原则层
  - [项目章程](./docs/project-charter.md)
  - [总体架构](./docs/architecture/overview.md)
  - [公共 API 规范](./docs/architecture/public-api.md)
  - [结果 schema](./docs/architecture/result-schema.md)
  - [Stata 对齐规范](./docs/architecture/stata-compatibility.md)
- 路线图与任务池
  - [总体路线图](./docs/roadmap.md)
  - [Wave 执行轮次规则](./docs/roadmap-execution-rounds.md)
  - [全局任务池](./docs/backlog.md)
- 研究层
  - [命令族规划](./docs/research/command-families.md)
  - [源码清单](./docs/research/stata-source-inventory.md)
  - [公开数据集规划](./docs/research/public-datasets.md)
- 测试层
  - [测试策略](./docs/testing/testing-strategy.md)
  - [测试样例目录](./docs/testing/test-case-catalog.md)
- 执行与治理
  - [执行代理手册](./docs/operations/executor-playbook.md)
  - [阶段门禁](./docs/operations/review-gates.md)
  - [Git 工作流](./docs/operations/git-workflow.md)

## 核心设计

项目按四层组织：

- `core`
  - 稳定的 Python 原生估计器，例如 `OLS`、`FixedEffectsOLS`、后续的 `AbsorbingOLS`、`IV2SLS`、`Poisson`。
- `compat.stata`
  - Stata 命令映射层，例如 `regress()`、`xtreg_fe()`、`areg()`、`reghdfe()`、`ivreghdfe()`、`ppmlhdfe()`。
- `research`
  - 命令手册、公开源码、返回值、自由度规则、修正因子、真实数据验证设计。
- `validation`
  - synthetic 黄金样例、真实公开数据样例、Stata 双跑、字段级 diff 报告。

## 源码研究与本地镜像

对公开源码的社区命令，项目默认先建立本地镜像，再离线研究：

- `research/vendor/stata_community/reghdfe/`
- `research/vendor/stata_community/ivreghdfe/`
- `research/vendor/stata_community/ppmlhdfe/`
- `research/vendor/stata_community/did_imputation/`
- `research/vendor/stata_community/eventstudyinteract/`
- `research/vendor/stata_community/rdrobust/`

这些目录用于研究与算法对照，不代表直接搬运原实现。

## 验证原则

每个新命令默认需要两条验证线：

- `synthetic / controlled cases`
  - 锁定公式、自由度、样本筛选、边界条件。
- `real public datasets`
  - 在真实公开金融或经济学数据上做 Stata-Python 双跑，验证研究环境中的稳健一致性。

一个命令从 `ready` 进入 `done`，至少需要：

- synthetic 黄金样例通过
- 至少一个真实公开数据样例通过
- 命令研究档案完整
- 源码或手册来源已归档
- 全量回归测试无破坏

## 执行模式

Codex 负责：

- 项目目标、架构、review、门禁、统计争议裁决

Claude Code 负责：

- 分块实现、测试、证据回填

当前不自动开放新任务。后续仍按分块任务推进，但前提是先完成项目级文档与研究框架升级。

## Wave 结构说明

当前路线图采用：

- `Wave 0`：已完成的原型验证
- `Wave 1`：`areg` 与吸收内核收口
- `Priority Wave: reghdfe`：在 `Wave 1` 之后单独优先推进 `reghdfe` 的研究、最小实现与真实数据验证
- `Wave 2` 及之后：`IV / GMM`、`Binary / Count`、`DID / Event Study Extensions`、`Postestimation`

这意味着 `reghdfe` 不再只是 `Wave 1` 中的研究占位，而是被明确提升为下一阶段的独立实现主线。
