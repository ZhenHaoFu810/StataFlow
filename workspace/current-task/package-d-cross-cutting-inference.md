# 任务卡：Package D - Cross-Cutting Inference

## 背景

`Package A` 已解决 correctness / release hygiene，`Package B` 已推进 HDFE family 的核心能力，`Package C` 已推进 DID family 的关键缺口。按照总开发计划，下一条主线应进入跨命令公共推断能力。

当前项目最明显的公共缺口不是“再多加一个命令名”，而是一些基础能力仍然停留在单命令或单路径级别，导致多个命令都共享同一类能力边界：

- 目前只支持单 cluster，不支持 multi-way clustering
- 目前只支持 `aweight`，不支持更完整的权重体系
- wrapper 层仍以 `ResultSchema` 为主，post-estimation / summary 的对外能力边界不够完整

本轮任务不是要求你一次性把这三条全部补完，而是要求你选出**最适合本轮高质量落地的一条主线**，做出真正可复用的推进。

## 总目标

在 `D:\OneDrive - SAIF\PhD3\StataFlow` 中完成一轮 **跨命令公共推断能力补全**，使至少一项目前写在公共限制里的能力获得实质性推进，并把这一推进同步落实到：

- 实现
- 测试
- support matrix
- 必要的 example / 报告

## 本轮建议优先级

如评估后可行，优先级建议如下：

### P1

- multi-way clustering：至少在最自然的一条命令链或 estimator 家族中落地最小可用版本，并为后续横向扩展打下公共接口

### P1

- `aweight` 之外的权重支持：优先考虑最有复用价值的一类，例如 `fweight` 或 `pweight`，但必须先明确其统计语义和当前项目能否正确承载

### P2

- wrapper 层 post-estimation / summary：推进可直接改善用户使用体验的一小段真实能力，而不是做空泛重构

你不必三者全做完，但必须：

- 先评估三者的可实施性
- 选出本轮实际主攻目标
- 在报告中解释为什么这样切分

## 最低要求

本轮不能只是“分析 + 写计划”。必须至少落地以下之一：

1. multi-way clustering 获得实质性实现推进
2. 一类新的权重支持获得实质性实现推进
3. wrapper 层 post-estimation / summary 获得可验证的实质性能力推进

如果你判断三者中某一项最适合作为本轮主攻目标，可以聚焦一个，但必须把理由讲清楚。

## 具体要求

## D1. 先做边界判断

你必须先确认：

- 哪个目标最适合在本轮落地
- 哪些现有实现可复用
- 哪些 support matrix 声明需要同步修改
- 哪些测试最适合先补

不要盲目同时推进三个大目标。

## D2. 公共能力优先于单命令补丁

如果发现某个底层改动可以服务多个命令，应优先改公共层，而不是只在某个 wrapper 上打补丁。

尤其应关注：

- `src/stataflow/results/`
- `src/stataflow/postestimation/`
- OLS / IV / GLM / HDFE 共享的 VCE 或 weights 入口
- wrapper 层与 estimator 层之间的能力映射

## D3. 统计语义必须讲清楚

如果你选择的是 clustering 或 weights 路线，不能只做接口层支持，必须说明：

- 新能力的统计语义是什么
- 当前实现在哪些 estimator 上是正确的
- 哪些 estimator 暂不适用，为什么

不允许通过“先接受参数、内部静默忽略”这种方式推进。

## D4. 测试必须同步

本轮任何功能推进都必须补测试。测试至少覆盖：

- 新能力的 happy path
- 一个关键边界条件
- 至少一个以前不支持、现在应支持的路径

如果某条路径仍明确不支持，也应有清晰的报错或边界说明。

## D5. 文档必须同步

如果你改变了能力边界，必须同步更新：

- `docs/command-support-matrix/README.md`
- 与本轮目标直接相关的 command matrix

必要时再补 README、examples 或设计说明。

## 不在本轮范围内的事项

本轮不要扩展到：

- 新的 DID family 补全
- 新的 HDFE family 大功能
- `rdrobust` 单独补功能
- open-source export / CI root-cause
- 无关的大规模 summary / UI 重构

## 推荐执行方式

1. 先评估三条候选路线
2. 选定一个主攻目标
3. 明确“本轮做到什么、刻意不做什么”
4. 落地实现
5. 补测试
6. 更新 support matrix
7. 在 `REPORT.md` 中写清结果与边界

## 最低交付物

完成后至少应交付：

- 一组真实代码改动
- 一组新增或更新测试
- 同步更新后的 support matrix
- 完整的 [REPORT.md](</D:/OneDrive - SAIF/PhD3/StataFlow/workspace/current-task/REPORT.md>)

## 必须在报告中回答的问题

1. 本轮最终选了哪条公共能力主线，为什么
2. 为什么没选另外两条
3. 这次改动服务了哪些命令或 estimator
4. 新能力的行为边界是什么
5. 补了哪些测试
6. support matrix 如何同步修改
7. 哪些跨命令能力仍留待后续

## 成功标准

只有当以下条件全部满足时，本轮任务才算完成：

- 至少一个跨命令公共推断缺口被真实推进
- 不是只改文档或只做分析
- 测试覆盖新增能力
- support matrix 与实现一致
- `REPORT.md` 可供 Codex 下一轮复审直接使用
