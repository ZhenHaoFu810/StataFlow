# 任务卡：Package B - HDFE Completion Core

## 背景

根据最新总开发计划，`Package A` 已完成并通过复审，项目现在应进入第一条主线：

- HDFE family 补全

当前 `reghdfe` / `ivreghdfe` / `ppmlhdfe` 的共同问题是：

- 已具备高频路径和基本验证
- 但仍停留在“子集可用”
- 距离真实研究迁移仍有关键缺口

本轮任务要做的不是一次性把 HDFE family 全部补完，而是推进最核心、最有复用价值的一步。

## 总目标

在 `D:\OneDrive - SAIF\PhD3\StataFlow` 中完成一轮 **HDFE family 的核心能力补全**，使 `reghdfe` / `ivreghdfe` / `ppmlhdfe` 中至少一项关键能力获得实质性推进，并把这一推进同步落实到：

- 实现
- 测试
- support matrix
- examples / 报告

## 本轮建议优先级

如果评估后可行，优先级建议如下：

### P1

- `reghdfe`：从仅限 1-2 个 absorbed FE，推进到更一般的多重 FE 支持

### P1

- `ivreghdfe`：补 first-stage / weak-IV / overidentification 中最小可用的一段诊断链

### P1

- `ppmlhdfe`：补 separation handling 的最小可用版本

你不必三者全部做完，但必须：

- 先评估三者的可实施性
- 选出本轮实际主攻目标
- 在报告中解释为什么这样切分

## 最低要求

本轮不能只是“分析+写计划”。必须至少落地以下之一：

1. `reghdfe` 的多重 FE 支持取得实质性实现
2. `ivreghdfe` 具备最小可用的诊断链
3. `ppmlhdfe` 具备最小可用的 separation handling

如果你判断三者中某一个最适合作为本轮主攻目标，可以聚焦一个，但必须把理由讲清楚。

## 具体要求

## B1. 先做边界判断

你必须先确认：

- 哪个目标最适合在本轮落地
- 哪些现有实现可复用
- 哪些 support matrix 声明需要同步修改
- 哪些测试最适合先补

不要盲目同时推进三个大目标。

## B2. 共享内核优先

如果发现某个底层改动可以同时服务多个 HDFE 命令，应优先改共享内核，而不是分别打补丁。

尤其应关注：

- `AbsorbingOLS`
- `IVAbsorbingOLS`
- `PPMLHDFE`
- HDFE 相关结果对象与 diagnostics 输出

## B3. 测试必须同步

本轮任何功能推进都必须补测试。测试至少覆盖：

- 新增能力的 happy path
- 一个关键边界条件
- 至少一个会失败的旧限制是否已解除

## B4. 文档必须同步

如果你改变了能力边界，必须同步更新：

- `docs/command-support-matrix/reghdfe.md`
- `docs/command-support-matrix/ivreghdfe.md`
- `docs/command-support-matrix/ppmlhdfe.md`

必要时再补 README 或 examples。

## 不在本轮范围内的事项

本轮不要扩张到：

- DID family
- `rdrobust`
- multi-way clustering 的完整通用框架（除非它是你主攻目标所必需的一小步）
- open-source export
- 大规模 UI / summary 输出重构

## 推荐执行方式

1. 先评估三条可能路线
2. 选定一个主攻目标
3. 明确“本轮做到什么、刻意不做什么”
4. 落地实现
5. 补测试
6. 更新 support matrix
7. 在 `REPORT.md` 中清楚写明结果与边界

## 最低交付物

完成后至少应交付：

- 一组真实代码改动
- 一组新增或更新测试
- 同步更新后的 support matrix
- 完整的 [REPORT.md](</D:/OneDrive - SAIF/PhD3/StataFlow/workspace/current-task/REPORT.md>)

## 必须在报告中回答的问题

1. 本轮最终选了哪个 HDFE 子目标，为什么
2. 为什么没选另外两个
3. 实现上改了什么核心逻辑
4. 新能力的行为边界是什么
5. 补了哪些测试
6. support matrix 如何同步修改
7. 哪些 HDFE family 缺口仍留待后续

## 成功标准

只有当以下条件全部满足时，本轮任务才算完成：

- 至少一个 HDFE family 关键缺口被真实推进
- 不是只改文档或只做分析
- 测试覆盖新增能力
- support matrix 与实现一致
- `REPORT.md` 可供 Codex 下一轮复审直接使用
