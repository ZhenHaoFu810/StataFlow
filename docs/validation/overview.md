# Validation Overview

`stataflow` 的对外验证不是“看起来差不多”，而是基于 **Stata 17 field-level dual-run** 的证据册。  
这份文档给开源用户一个总入口，说明：

- 我们验证了什么
- 用了哪些公开数据
- 采用什么判定标准
- 当前哪些命令已经被证明“迁移成功且准确”
- 哪些命令仍然只是“已验证子集”

## Validation Goal

目标是证明：对当前已经实现的命令路径，`stataflow` 在数学口径、字段级结果和公开命令语义上，与 **Stata 17** 对齐。

这份证据册不做两种事：

- 不把“支持矩阵里的子集实现”包装成完整命令复现
- 不用“统计意义上差不多”代替字段级对齐

## Evidence Structure

每个命令的证据都由三部分组成：

1. `synthetic`
   - controlled cases，锁定公式、自由度、边界情况
2. `real_data`
   - 公开经济学/金融学真实数据，验证真实研究环境下的结果对齐
3. `source-backed`
   - 对社区命令，结合 source map / support matrix 限定“已验证子集”的边界

## Current Coverage

当前证据册覆盖这些命令：

- `regress`
- `xtreg, fe`
- `areg`
- `reghdfe`
- `ivregress 2sls`
- `ivreghdfe`
- `logit`
- `probit`
- `poisson`
- `ppmlhdfe`
- `did_imputation`
- `eventstudyinteract`
- `csdid`
- `rdrobust`

## Interpretation Standard

- `stable`
  - synthetic + real-data 双线完成，当前公开路径已经是稳定命令面
- `validated subset`
  - 对实现子集已经完成严格 dual-run 验证，但不宣称完整复现整个社区命令

当前关键判断：

- 基础命令：`regress`、`xtreg, fe`、`areg`、`ivregress 2sls`、`logit`、`probit`、`poisson`
  - 已达到稳定验证状态
- 社区命令：`reghdfe`、`ivreghdfe`、`ppmlhdfe`、`did_imputation`、`eventstudyinteract`、`csdid`、`rdrobust`
  - 当前是 **validated subset**
  - 证据证明“当前实现的高频子集是成功且准确的”
  - 不意味着完整复制全部 Stata 社区命令参数面

## Public Dataset Coverage

### Development-time real-data evidence

- Panel / FE / HDFE
  - `grunfeld`
  - `wagepan`
- IV
  - `card`
- Binary
  - `mroz`
- Count
  - `crime1`
  - `countymurders_ca`
- DID / Event Study
  - `ezunem`
- RD
  - `rdrobust_senate`

### Out-of-sample (OOS) real-data evidence (Validation Package 001)

- Panel / FE / HDFE
  - `airfare` — route-level airline panel, new OOS baseline + factor-variable stress case
- IV
  - `card` — new specification (two instruments)
  - `wagepan` — new specification (absorbed IV with different controls)
- Binary / Count
  - `vote1` — congressional election binary outcome
  - `smoke` — smoking behavior with factor-variable interaction
  - `fertil1` — fertility count panel with year FE
- DID / Event Study
  - `jtrain` — firm-level job training staggered-adoption panel (3-period short panel)
- RD
  - `rdrobust_senate` — covariate adjustment + automatic bandwidth selection

登记但尚未纳入主证据矩阵的公开数据：

- `ff3`
- `ff5`

详见 [Dataset Registry](./dataset-registry.md)。

## How to Read This Evidence Book

建议按这个顺序看：

1. [Validation Policy](./validation-policy.md)
2. [Evidence Matrix](./evidence-matrix.md)
3. 各命令 support matrix
4. 对应 golden tests / validation runners / generated artifacts

## Generated Artifacts

### Development-time validation

- `scripts/validation/run_validation_linear.py`
- `scripts/validation/run_validation_hdfe.py`
- `scripts/validation/run_validation_iv.py`
- `scripts/validation/run_validation_glm.py`
- `scripts/validation/run_validation_did.py`
- `scripts/validation/run_validation_rd.py`
- `scripts/validation/run_validation_all.py`
- `scripts/validation/collect_validation_summary.py`

生成产物：

- `research/results/validation/evidence-summary.json`
- `research/results/validation/evidence-summary.md`

### Out-of-sample validation (Validation Package 001)

- `scripts/validation/oos/run_oos_linear.py`
- `scripts/validation/oos/run_oos_iv.py`
- `scripts/validation/oos/run_oos_glm.py`
- `scripts/validation/oos/run_oos_did.py`
- `scripts/validation/oos/run_oos_rd.py`
- `scripts/validation/oos/run_oos_all.py`
- `scripts/validation/oos/common.py`

生成产物：

- `research/results/validation/oos/oos_master_summary.json`
- `research/results/validation/oos/oos_master_summary.md`
- `research/results/validation/oos/linear_summary.json`
- `research/results/validation/oos/iv_summary.json`
- `research/results/validation/oos/glm_summary.json`
- `research/results/validation/oos/did_summary.json`
- `research/results/validation/oos/rd_summary.json`
- `research/results/validation/oos/case_*.json` (per-case structured reports)

## Bottom-Line Statement

如果外部读者的问题是：

> “你们的 Stata → Python 迁移到底有没有成功？”

当前项目给出的最严格、最诚实回答是：

- 对已实现并进入证据册的命令路径，**迁移是成功且准确的**
- 对基础命令，这个结论适用于当前公开命令面
- 对社区命令，这个结论适用于 **已验证子集**，而不是完整原生命令表面

### Out-of-sample 补充结论

Validation Package 001 在全新公开真实数据上完成了 17 个 OOS case 的字段级双跑：

- **16 / 17 passed**，1 blocked（`did_imputation` on `jtrain`，短面板数据限制，非算法错误）
- 5 个命令族全部覆盖了新的真实研究场景
- 包含 baseline、variation 和 stress case（factor-variable 交互、自动带宽选择、零值占比高的 count panel）

这意味着：在开发期证据之外，当前已实现的高频路径在 **独立的真实数据环境中仍然稳定对齐**。该 OOS 证据册可作为首次开源版本“迁移成功且准确”的核心可信度说明之一。
