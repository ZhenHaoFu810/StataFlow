# Stata2Python

Stata2Python 是一个面向金融与经济学实证研究的计量工具包项目，目标是在 Python 环境中复现与 Stata 高度对齐的估计结果、标准误、检验统计量与输出行为。项目当前优先建设文档驱动的治理体系，以支持后续由 QwenCode 按规范实施代码、测试与持续验证。

## 当前阶段

当前处于 v1 前期架构与治理阶段，第一批目标聚焦于：

- Stata 验证执行链路
- 统一结果 schema
- 线性模型核心
- 自动化双跑测试框架

## 文档导航

- 项目章程：`docs/project-charter.md`
- 总体架构：`docs/architecture/overview.md`
- 公共 API 规范：`docs/architecture/public-api.md`
- 结果 schema：`docs/architecture/result-schema.md`
- Stata 对齐规范：`docs/architecture/stata-compatibility.md`
- 总体路线图：`docs/roadmap.md`
- 全局任务池：`docs/backlog.md`
- 测试策略：`docs/testing/testing-strategy.md`
- QwenCode 操作手册：`docs/operations/qwencode-playbook.md`

## 阅读顺序

建议任何执行代理按以下顺序进入项目：

1. 阅读 `docs/project-charter.md`
2. 阅读 `docs/architecture/overview.md`
3. 阅读 `docs/architecture/public-api.md`
4. 阅读 `docs/architecture/result-schema.md`
5. 阅读 `docs/architecture/stata-compatibility.md`
6. 阅读 `docs/roadmap.md` 与 `docs/backlog.md`
7. 阅读对应阶段执行手册
8. 开始实施具体任务

## QwenCode 入口

QwenCode 不应自行决定项目边界、公开 API 变化或统计等价标准。开始任何实现之前，必须：

- 先阅读 `docs/operations/qwencode-playbook.md`
- 在 `docs/backlog.md` 确认目标能力已登记
- 在 `docs/testing/test-case-catalog.md` 确认测试样例计划
- 按阶段手册执行，不得跳过测试门禁

## 当前默认约束

- 目标 Stata 版本：17
- 默认验证安装路径：`D:\Software\Stata.v17.0`
- 第一阶段公开范围：`regress`、`vce(robust)`、`vce(cluster)`、单向 FE 基础
- 第一阶段不承诺：GLM、IV、RE、双向/高维 FE 完整公开接口
