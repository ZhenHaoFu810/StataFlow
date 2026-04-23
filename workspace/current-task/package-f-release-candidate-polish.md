# 任务卡：Package F - Release Candidate Polish

## 背景

`Package A` 到 `Package E` 已完成以下主线：

- 正确性与 release hygiene
- HDFE family 核心补全
- DID family 核心补全
- 跨命令公共推断能力
- 开源范围审计与导出机制

项目现在已经具备：

- 可运行的主仓
- 可导出的开源镜像
- 基本稳定的 CI
- 公开文档与支持矩阵

下一步的关键不是继续扩功能，而是从“准备开源”推进到“可以对外发第一个 release candidate”。这要求仓库从公开用户视角看起来是自洽的、边界清楚的、路径顺畅的。

## 总目标

在 `D:\OneDrive - SAIF\PhD3\StataFlow` 中完成一轮 **release candidate 收口整理**，聚焦以下问题：

- README / USER_GUIDE / support matrix / examples 是否形成顺畅的首次使用路径
- 版本号、包元数据、发布文档是否一致
- 开源镜像是否有清晰的 release gating checklist
- 公开文档中是否还存在误导、断链、命名不一致、状态描述漂移

## 本轮建议优先级

如评估后可行，优先级建议如下：

### P1

- 修 README / USER_GUIDE / support matrix / examples 之间的对外叙事断裂

### P1

- 修版本号、包元数据、发布状态文档之间的不一致

### P2

- 建立一份 release candidate checklist / gating doc，明确首发前必须检查什么

你不必把三者全部做完，但必须：

- 先从公开用户视角审一遍
- 选出本轮最值得修的一组问题
- 在报告中解释为什么这些问题优先

## 最低要求

本轮不能只是“分析 + 写建议”。必须至少落地以下之一：

1. 修掉一组真实存在的公开文档 / 元数据 / 发布状态不一致问题
2. 建立一份可执行的 release candidate gating checklist，并与当前仓库状态对齐

## 具体要求

## F1. 先做公开用户路径审查

你必须先从一个首次访问 GitHub 仓库的外部用户视角审查：

- `README.md`
- `README.zh-CN.md`
- `docs/USER_GUIDE.md`
- `docs/USER_GUIDE.zh-CN.md`
- `docs/command-support-matrix/README.md`
- `examples/`

你要回答：

- 用户第一眼看到项目时，会不会误解它的完成度
- 用户想“安装、运行一个例子、理解哪些命令可用”时，路径是否顺畅
- 中英文文档是否一致

## F2. 版本与发布状态必须一致

重点检查：

- `pyproject.toml`
- `src/stataflow/__init__.py`
- `README*`
- `docs/release/*`
- 任何对外声明当前版本/当前状态的地方

如果存在版本号、状态描述、命名或发布日期漂移，必须修正。

## F3. release gating 文档要可执行

如果当前仓库还缺一个真正面向 release candidate 的 checklist，本轮应补出来。建议位置：

- `docs/release/release-candidate-checklist.md`

内容应包括：

- 导出前检查
- 导出后检查
- CI / tests / examples 检查
- 文档一致性检查
- 已知风险确认

## F4. 文档修复必须和实际行为一致

如果你改 README、guide 或 support matrix，必须确保它们和当前仓库真实状态一致。不要写“未来将支持”式的模糊宣传。

## 不在本轮范围内的事项

- 新 estimator 功能开发
- 再次修改 A-E 已通过的核心实现，除非发现真实发布阻断问题
- 新的 open-source export 架构设计
- 自动发布流水线的大规模搭建

## 推荐执行顺序

1. 做公开用户路径审查
2. 识别最影响首发的 2-4 个问题
3. 选定本轮主攻项
4. 落地修复
5. 补 release checklist 或必要验证
6. 写 `REPORT.md`

## 最低交付物

完成后至少应交付：

- 一组真实文档 / 元数据 / release 文档修复
- 必要时新增一份 release checklist
- 一份完整的 [REPORT.md](</D:/OneDrive - SAIF/PhD3/StataFlow/workspace/current-task/REPORT.md>)

## 必须在报告中回答的问题

1. 从公开用户视角，当前仓库最影响首发的几个问题是什么
2. 本轮最终修了哪些问题，为什么优先修这些
3. 哪些文件被修改
4. 是否新增了 release checklist 或其他 gating 文档
5. 做了哪些本地验证
6. 哪些首发风险仍留待后续

## 成功标准

只有当以下条件全部满足时，本轮任务才算完成：

- 至少一个真实的 release-candidate 阻断问题被修掉
- 不是只写建议或只做分析
- 对外文档 / 版本元数据 / 发布状态比当前更一致
- `REPORT.md` 可供 Codex 下一轮复审直接使用
