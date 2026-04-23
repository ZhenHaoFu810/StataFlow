# 任务卡：Package C - DID Completion Core

## 背景

`Package A` 已解决 correctness / release hygiene，`Package B` 已推进 HDFE family 的核心能力。按照总开发计划，下一条主线应进入 DID family。

当前 DID family 的共同状态是：

- `did_imputation`、`eventstudyinteract`、`csdid` 已有可用主干
- 但仍停留在高频子集
- 距离真实研究迁移仍有明显命令面和行为边界缺口

本轮任务要做的不是把 DID family 一次性补完，而是推进最关键、最值得优先落地的一段。

## 总目标

在 `D:\OneDrive - SAIF\PhD3\StataFlow` 中完成一轮 **DID family 的核心能力补全**，使 `did_imputation` / `eventstudyinteract` / `csdid` 中至少一项关键能力获得实质性推进，并把这一推进同步落实到：

- 实现
- 测试
- support matrix
- examples / 报告

## 本轮建议优先级

如果评估后可行，优先级建议如下：

### P1

- `did_imputation`：补 `window` / `minn` / `pretrends` 中最小可用的一段

### P1

- `eventstudyinteract`：补 `window` / `minn` / 更完整 horizon 约束的一段

### P2

- `csdid`：明确并推进 `method="reg"` 之外的下一步，但这条通常比前两者更重

你不必三者全部做完，但必须：

- 先评估三者的可实施性
- 选出本轮实际主攻目标
- 在报告中解释为什么这样切分

## 最低要求

本轮不能只是“分析+写计划”。必须至少落地以下之一：

1. `did_imputation` 的关键选项子集取得实质性实现
2. `eventstudyinteract` 的命令面获得实质性补全
3. `csdid` 的方法或 aggregation 生态获得实质性推进

如果你判断三者中某一个最适合作为本轮主攻目标，可以聚焦一个，但必须把理由讲清楚。

## 具体要求

## C1. 先做边界判断

你必须先确认：

- 哪个目标最适合在本轮落地
- 哪些现有实现可复用
- 哪些 support matrix 声明需要同步修改
- 哪些测试最适合先补

不要盲目同时推进三个大目标。

## C2. 优先补真实研究中常见的缺口

优先推进以下类型的问题：

- 公开列为 planned / missing 的常用选项
- 影响论文 replication 的命令行为
- 会让用户误以为“支持了这个命令”，但实际关键选项还缺失的地方

不要把时间花在低频边角选项上。

## C3. 测试必须同步

本轮任何功能推进都必须补测试。测试至少覆盖：

- 新增能力的 happy path
- 一个关键边界条件
- 至少一个旧限制是否已解除

## C4. 文档必须同步

如果你改变了能力边界，必须同步更新：

- `docs/command-support-matrix/did-imputation.md`
- `docs/command-support-matrix/eventstudyinteract.md`
- `docs/command-support-matrix/csdid.md`

必要时再补 README 或 examples。

## 不在本轮范围内的事项

本轮不要扩张到：

- RD family
- HDFE family 新一轮大改
- open-source export
- 全局 summary/table 重构
- 多命令通用 clustering / weights 大框架

## 推荐执行方式

1. 先评估三条 DID 路线
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

1. 本轮最终选了哪个 DID 子目标，为什么
2. 为什么没选另外两个
3. 实现上改了什么核心逻辑
4. 新能力的行为边界是什么
5. 补了哪些测试
6. support matrix 如何同步修改
7. 哪些 DID family 缺口仍留待后续

## 成功标准

只有当以下条件全部满足时，本轮任务才算完成：

- 至少一个 DID family 关键缺口被真实推进
- 不是只改文档或只做分析
- 测试覆盖新增能力
- support matrix 与实现一致
- `REPORT.md` 可供 Codex 下一轮复审直接使用
