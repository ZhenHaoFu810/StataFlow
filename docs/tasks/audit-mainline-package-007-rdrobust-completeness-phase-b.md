# 审计主线任务包 007：`rdrobust` 完整度推进（Phase B）

## 任务定位

`rdrobust` 目前已经从 “missing” 推进到 **可验证的最小 sharp RD 子集**，但距离常见研究工作流仍有明显缺口。

当前支持矩阵把 `rdrobust` 定为 **Partial / Minimal Subset**，最大的可用性缺口是：

- 必须显式提供 `h`，不能自动带宽选择
- 不支持 `covs()`
- 不支持更完整的结果与命令层语义

下一步不再横向扩其他命令，而是把 `rdrobust` 从“最小可跑”推进到“常见 sharp RD 工作流可用”的 **Phase B 子集**。

## 目标

本轮至少完成下面三类工作中的前两类，最好三类全部完成：

1. **自动带宽选择进入主线**
   - 支持至少一个常见 selector，并给出清晰的 source-backed 对应关系。
2. **covariate-adjusted sharp RD 进入主线**
   - 支持 `covs()` 的最小但正确子集。
3. **`rdrobust` 对外文档与验证证据收口**
   - source map、support matrix、README / release-facing 文档同步更新。

## 必须使用的依据

- 审计文档：
  - `docs/audit/audit-findings.md`
  - `docs/audit/project-gaps.md`
  - `docs/audit/next-development-plan.md`
- 研究档案：
  - `docs/research/rdrobust-source-map.md`
- 本地源码镜像：
  - `research/vendor/stata_community/rdrobust/`
- 当前支持矩阵：
  - `docs/command-support-matrix/rdrobust.md`
- 审查协议：
  - `docs/operations/codex-review-protocol.md`

## 数学与实现要求

### A. 严禁“为过测试反推数值”

本轮必须坚持以下规则：

- 先明确 Stata / 官方 Python / 论文公式的对应关系，再写实现
- 不允许通过放宽容差、特殊 case 修补、对单一样例调参来宣称完成
- 自动带宽与 covariate-adjusted RD 的实现必须能解释清楚估计流程、偏差修正和 VCE 口径

### B. 自动带宽选择

至少支持 **一个** 高频 selector，并明确写清楚：

- 选中的 selector 是什么
- 与 Stata `rdrobust` / `rdbwselect` 的哪个分支对应
- 当前是否只支持 sharp RD / local linear / 某些 kernel 组合

优先建议：

- `bwselect="mserd"` 或等价的最常见 sharp RD selector

本轮不要求一次性覆盖全部 selector 家族，但必须：

- wrapper 能接受 `bwselect=...`
- 若未支持其他 selector，必须显式 hard-reject
- 若 `h` 与 `bwselect` 同时给出，行为必须明确且文档化

### C. `covs()` 最小子集

本轮若实现 `covs()`，必须满足：

- 仅在 sharp RD 下先支持
- 明确样本筛选和缺失值处理
- 明确 covariate-adjusted local polynomial 的估计口径
- 对不支持的扩展场景（如 fuzzy + covs、cluster + covs）显式 hard-reject

### D. 结果对象与命令语义

若新增自动带宽或 covariates，至少要保证：

- 结果对象中主带宽、偏差带宽和有效样本仍然可读
- wrapper 命令层参数与 Stata 命令语义一致
- 不允许出现 README / support matrix 写支持、但 wrapper 实际不接受的情况

## 必须重点审视的内容

### 1. 源码映射

必须把以下逻辑写进 `docs/research/rdrobust-source-map.md`：

- 自动带宽选择对应的源码入口与 Python 映射
- `covs()` 对应的源码 / 公式分支与 Python 映射
- 当前仍未实现的参数面

### 2. 支持矩阵

必须更新 `docs/command-support-matrix/rdrobust.md`：

- `Supported Parameters`
- `Planned Parameters`
- `Explicitly Unsupported Parameters`
- `Alignment Evidence`

不允许再把已实现参数放在 planned，也不允许把未实现参数写得模糊。

### 3. 测试设计

本轮测试不能只做“数值对一下”。

至少要包含：

- synthetic：
  - 自动带宽 selector 行为
  - covariate-adjusted sharp RD
  - `h` / `bwselect` 冲突或优先级语义
- real-data：
  - 至少一个公开 RD 数据上的 dual-run（继续可用 `rdrobust_senate.dta`，如需要可补新数据）
- negative tests：
  - 不支持的参数必须显式报错，不能静默忽略

### 4. wrapper / example / 文档一致性

若 README 或 support matrix 宣称 `bwselect` / `covs` 可用，则：

- wrapper 必须真的接受
- 至少一个 example 或 smoke 证据必须能跑

## 最低交付要求

### 1. 代码层

允许修改：

- `src/statapy/estimators/rdrobust.py`
- `src/statapy/compat/stata/rd.py` 或对应 wrapper 文件
- 必要的结果 schema / helper

### 2. 文档层

必须更新：

- `docs/research/rdrobust-source-map.md`
- `docs/command-support-matrix/rdrobust.md`

如确有必要，可同步更新：

- `README.md`
- `docs/release/open-source-alpha-status.md`
- `docs/release/known-issues.md`

### 3. 测试层

至少必须新增或更新：

- `tests/test_rdrobust.py`
- 必要的 golden / dual-run 测试
- 若新增 example，则补 smoke 证据

## 明确禁止

- 不顺手改 `reghdfe` / `ppmlhdfe` / `ivreghdfe` / DID 内核
- 不把 fuzzy RD、cluster RD、全部 selector 家族一口气塞进本轮后再用大容差放行
- 不允许对 unsupported 参数静默忽略
- 不允许只依据官方 Python 包输出而不解释 Stata / 论文 / 源码对应关系

## 通过标准

Codex 只会在以下条件同时满足时放行：

1. 至少一个自动带宽 selector 进入命令层，且 source-backed 说明清楚。
2. 若实现 `covs()`，其估计口径、VCE 口径和缺失值处理有明确依据。
3. `rdrobust` source map、support matrix、wrapper、测试证据一致。
4. 全量测试通过，并且 `rdrobust` 专项测试 / dual-run 通过。
5. 不支持的参数仍然被显式 hard-reject。

## 回报格式

完成后在 `workspace/current-task/REPORT.md` 中按下面结构汇报：

1. 自动带宽选择实现了什么、没有实现什么
2. `covs()` 实现了什么、没有实现什么
3. 估计过程 / 偏差修正 / VCE 是如何与 Stata 或官方源码对应的
4. 更新了哪些 source map / support matrix / release-facing 文档
5. 跑了哪些 synthetic / dual-run / full pytest
6. 最新 fresh run 结果
7. 当前 `rdrobust` 距离“完整 community command 复现”还差什么
