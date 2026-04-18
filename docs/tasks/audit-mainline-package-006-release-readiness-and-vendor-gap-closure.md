# 审计主线任务包 006：开源发布准备与 vendor 完整度收口
## 任务定位

HDFE / IV / DID 三条主线都已经推进到可验证的 Phase B 子集。  
下一轮不再扩单个估计器主线，而是进入 **开源发布前的产品收口阶段**：

- 让 README、support matrix、source map、wrapper 语义、示例与当前真实实现完全一致
- 把 `research/vendor/stata_community` 下各命令的完整度状态正式收口成对外可读的发布级说明
- 为下一轮更深的 vendor 命令完整复现建立清晰的 release gap 清单

## 目标

本轮至少完成下面四类工作中的前三类：

1. **对外发布面收口**
   - README、命令支持矩阵、示例脚本、wrapper 公共语义完全一致。
2. **vendor 完整度总表收口**
   - 对 `reghdfe`、`ivreghdfe`、`ppmlhdfe`、`did_imputation`、`eventstudyinteract`、`csdid`、`rdrobust` 输出统一的完整度状态。
3. **已知缺口显式化**
   - 不再把高频子集写成“完整支持”。
   - 对未实现项、显式拒绝项、未来主线项写清楚。
4. **发布前验证脚本与示例收口**
   - 确保外部用户按 README 和 examples 路径能实际跑通高频命令。

## 必须使用的依据

- 审计文档：
  - `docs/audit/audit-findings.md`
  - `docs/audit/project-gaps.md`
  - `docs/audit/next-development-plan.md`
- 命令支持矩阵目录：
  - `docs/command-support-matrix/`
- 研究档案目录：
  - `docs/research/`
- 示例脚本：
  - `examples/`
- 审查协议：
  - `docs/operations/codex-review-protocol.md`

## 必须重点审视的内容

### A. README / 示例 / wrapper 语义

至少检查并必要时修正：

- README 中所有 quick-start 示例是否真的能直接运行
- wrapper 返回对象的语义是否和 README / 支持矩阵一致
- examples 中是否仍存在“内部开发式”而不是“外部用户式”写法

### B. vendor 完整度总表

至少对以下命令形成统一口径：

- `reghdfe`
- `ivreghdfe`
- `ppmlhdfe`
- `did_imputation`
- `eventstudyinteract`
- `csdid`
- `rdrobust`

每个命令都必须明确归类为：

- `near-complete`
- `partial`
- `research-only`

不得再使用模糊的“基本支持”“高频可用”而不给状态。

### C. release-facing 文档一致性

至少检查并修正：

- `README.md`
- `docs/command-support-matrix/README.md`
- 各命令 support matrix 顶部完整度状态
- 各命令 support matrix 的 “Supported / Planned / Explicitly Unsupported” 三分法
- 示例和支持矩阵是否互相矛盾

### D. 已知延后项登记

必须把不再阻塞主线、但仍存在的问题登记成正式的已知问题，而不是隐含留在 review 文档里。

本轮至少登记：

- `ivreghdfe` Package 004 的 `REPORT.md` fresh-run 旧数字问题
- `did` Package 005 的 `REPORT.md` fresh-run 旧数字问题

## 最低交付要求

### 1. 文档层

必须更新：

- `README.md`
- `docs/command-support-matrix/README.md`
- 至少所有 vendor 命令对应的 support matrix
- `docs/audit/project-gaps.md`（若严重度或描述需要更新）

如有必要，可新增：

- `docs/release/open-source-alpha-status.md`
- `docs/release/known-issues.md`

### 2. 示例层

如 README 或 support matrix 宣称某条 quick-start 路径可用，则至少一条对应 example 必须实际可跑。

允许修改：

- `examples/demo_regress.py`
- `examples/demo_reghdfe.py`
- `examples/demo_ppmlhdfe.py`
- `examples/demo_ivregress_2sls.py`
- 必要时新增一个 DID example

### 3. 测试层

本轮不要求大规模新算法测试，但至少必须：

- 跑一遍全量测试
- 跑一遍 examples / smoke 级示例验证
- 如修了 README / wrapper 语义不一致，必须补对应的 smoke 测试或示例验证证据

## 明确禁止

- 不开启新的大算法分支
- 不顺手重写 `reghdfe` / `ppmlhdfe` / `ivreghdfe` 内核
- 不为了“文档好看”把子集命令夸写成完整实现
- 不允许把已知问题静默删除，必须显式登记

## 通过标准

Codex 只会在以下条件同时满足时放行：

1. README、support matrix、wrapper、examples 之间没有明显公开语义冲突。
2. 所有 vendor 命令都有统一的完整度状态和清晰的缺口说明。
3. 已知延后项被正式登记，不再散落在历史 review 中。
4. 全量测试通过，且至少主要 example/quick-start 路径已验证。

## 已知延后项（不阻塞本轮）

- `workspace/current-task/REPORT.md` 中关于 DID Package 005 的旧 fresh-run 数字问题。
- `workspace/current-task/REPORT.md` 中关于 `ivreghdfe` Package 004 的旧 fresh-run 数字问题。
- 这些问题应在本轮被转登记到正式 known-issues 文档，但不要求回头补旧报告本身。

## 回报格式

完成后在 `workspace/current-task/REPORT.md` 中按下面结构汇报：

1. README / examples / support matrix / wrapper 哪些地方被收口了
2. vendor 命令完整度总表最终怎么定级
3. 哪些问题被正式登记为 known issues
4. 跑了哪些 example / smoke / pytest 验证
5. fresh run 结果
6. 你认为当前仓库距离“对外开源初版发布”还剩哪些 release-blocking 问题
