# 任务卡：Package E - Open-Source Release Readiness

## 背景

`Package A` 到 `Package D` 已分别推进了正确性、HDFE、DID 和跨命令推断能力。当前项目的下一个关键瓶颈不在 estimator 本身，而在于：

- 你已经维护了一个私有开发主仓 `StataFlow`
- 同时又维护了一个公开镜像目录 `StataFlow_open_source`
- 目前开源版本仍带有明显的手工整理痕迹
- 仓库中仍存在大量不适合开源的内部文档、审计材料、开发记录
- 公开文档、中文 Markdown 编码、CI 和发布边界仍需系统整理

本轮任务的目标是把开源发布从“手工复制 + 人工删减”推进成“边界清晰 + 可重复导出 + 文档/CI/编码稳定”的正式流程。

## 总目标

在 `D:\OneDrive - SAIF\PhD3\StataFlow` 中完成一轮 **开源发布就绪化** 工作，使：

- `StataFlow` 成为唯一维护源
- `StataFlow_open_source` 可以由脚本稳定导出
- 开源边界可解释、可维护、可审计
- 开源仓的文档、CI、编码状态达到可发布水平

## 本轮必须完成的四个子目标

## E1. 开源范围审计

你必须先全面审查仓库中的目录与文件边界，明确哪些应该 open，哪些应该 closed。

重点审查对象至少包括：

- `docs/`
- `research/`
- `scripts/`
- `tests/`
- `stata/`
- `workspace/`

要求：

- 不能简单把整个 `docs/` 或整个 `research/` 视为 open
- 必须逐目录判断
- 对明显的内部材料给出 closed 判定
- 形成一份清晰的 open/closed 清单，作为后续 manifest 的基础

建议输出到：

- `docs/operations/open-source-scope-audit.md`

## E2. 设计并实现导出机制

在主仓内实现：

- `scripts/release/open_source_manifest.yml`
- `scripts/release/export_open_source.ps1`

如有必要，可以加一个 Python 辅助脚本，但 PowerShell 入口必须存在。

要求：

- 使用 manifest 管理白名单/黑名单，而不是把规则硬编码散落在脚本里
- 默认导出到 `D:\OneDrive - SAIF\PhD3\StataFlow_open_source`
- 保留目标仓 `.git`
- 支持 dry-run
- 支持 force
- 能删除目标仓中不再属于导出范围的旧文件
- 对危险路径做保护
- 导出结果有清晰 summary

## E3. 修复开源发布直接相关的问题

至少覆盖以下内容：

1. 中文 Markdown 编码 / 乱码问题
2. 开源文档中的命名不一致、失效路径、错误引用
3. GitHub Actions 的可观测性问题

CI 方面最低要求：

- 确认 `.github/workflows/ci.yml` 已设置 `fail-fast: false`
- 不允许通过删除 Python 3.11、跳过测试、弱化测试来规避问题
- 若 CI 仍有与开源发布相关的明显问题，可一并修

## E4. 导出与验证

实现完导出机制后，必须实际执行导出并验证：

- `StataFlow_open_source` 中不存在 closed 内容
- 公开代码、文档、CI 文件都在
- 关键测试可运行
- 开源仓结构符合发布预期

## 具体要求

## E-A. manifest 必须建立在审计结论之上

不要先拍脑袋写 manifest 再倒推解释。必须先做 open-source scope audit，再把 audit 结果落进 manifest。

## E-B. 不要把 `.gitignore` 当发布边界

本轮目标是“版本控制边界 + 导出边界”一起清楚，而不是依赖 `.gitignore` 掩盖已经被版本控制的内部文件。

## E-C. 文档与脚本必须一致

如果文档说某类目录不会进入开源仓，manifest 和导出结果也必须一致。

## E-D. 报告必须可审计

`REPORT.md` 必须能让 Codex 直接判断：

- 为什么某些内容被排除
- 导出脚本怎么运行
- 修了哪些开源阻断问题
- 导出后结果是否可信

## 不在本轮范围内的事项

- 新 estimator 功能开发
- HDFE / DID / RD 的进一步功能补全
- 大规模 UI 或 summary 重构
- 修改已通过复审的前四包核心功能，除非发现发布级阻断问题

## 推荐执行顺序

1. 做 open-source scope audit
2. 定义 manifest
3. 实现 export 脚本
4. 修文档 / 编码 / CI
5. 执行导出
6. 做导出后验证
7. 写 `REPORT.md`

## 最低交付物

完成后至少应交付：

- 一份开源范围审计文档
- 一份 manifest
- 一个可运行的导出脚本
- 修复后的开源相关文档/CI/编码问题
- 一份完整的 [REPORT.md](</D:/OneDrive - SAIF/PhD3/StataFlow/workspace/current-task/REPORT.md>)

## 必须在报告中回答的问题

1. 哪些目录/文件最终被判定为 open，哪些为 closed，为什么
2. manifest 的关键规则是什么
3. export 脚本如何使用
4. 修了哪些发布级问题
5. 导出后验证做了什么
6. 哪些开源风险仍留待后续

## 成功标准

只有当以下条件全部满足时，本轮任务才算完成：

- 开源范围边界有明确审计文档
- `StataFlow_open_source` 可以从主仓稳定导出
- 开源相关文档、编码、CI 问题得到实质性修复
- 不是只写计划或只做文档
- `REPORT.md` 可供 Codex 下一轮复审直接使用
