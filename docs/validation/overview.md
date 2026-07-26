# Validation Overview

[English](../../VALIDATION.md)

`stataflow` 的公开验证以 **Stata 17 字段级对照**为标准，而不是以
“统计意义上相近”代替具体字段的一致性。

## 验证目标

对当前已实现的命令路径，验证数学口径、字段级结果和公开命令语义与
Stata 17 对齐。社区命令只对支持矩阵中列明的子集作出结论，不宣称完整
复制其全部参数面。

## 证据结构

每个命令的证据包含：

1. `synthetic`：锁定公式、自由度、样本筛选和边界行为；
2. `real_data`：使用公开经济学或金融学数据验证实际研究场景；
3. `source-backed`：以官方手册、公开社区命令和论文限定实现边界。

## 当前覆盖

1.2.0 覆盖 14 个公开估计命令：

- Linear / FE：`regress`、`xtreg_fe`、`areg`、`reghdfe`
- IV：`ivregress_2sls`、`ivreghdfe`
- Binary / count：`logit`、`probit`、`poisson`、`ppmlhdfe`
- DID：`did_imputation`、`eventstudyinteract`、`csdid`
- RD：`rdrobust`

`rdplot` 是另行导出的可视化辅助工具，不计入 14 个估计命令。

## 状态解释

- `stable`：当前公开核心路径已完成 synthetic 与 real-data Stata 17
  对照，API 预期保持向后兼容。
- `validated subset`：已实现的高频子集有严格证据，但不代表完整复制
  社区命令。

## 公开数据覆盖

- Panel / FE / HDFE：`grunfeld`、`wagepan`
- IV：`card`
- Binary：`mroz`
- Count：`crime1`、`countymurders_ca`
- DID / Event Study：`ezunem`
- RD：`rdrobust_senate`

`ff3`、`ff5` 和 `jtrain` 也在数据集登记中，用于补充或历史比较。
详见[数据集登记](./dataset-registry.md)。

## 发布汇总

2026 年 7 月冻结的 1.2.0 范围包含：

- `40/40` 个数值 Stata 17 对照；
- 1 项 DID 功能检查；
- 完整本地 Stata 验证检查 `856 passed, 12 skipped`；
- 公开可复现验证套件 `10/10`。

相对偏差公式、命令族最大值和计数均存储在
[机器可读证据汇总](../../research/results/validation/evidence-summary.json)
中；[可读汇总](../../research/results/validation/evidence-summary.md)由同一
证据口径展示。

## 历史 OOS 记录

较早的 Validation Package 001 在额外公开样本上记录了 17 个 OOS
比较，其中 16 个被分类为 passed。该结果是**历史补充证据**，不属于
2026 年 7 月冻结的 `40/40` 发布汇总。

未分类为 passed 的 `did_imputation` / `jtrain` 比较使用三期短面板。
Stata 与 Python 在该设定下保留了不同的估计样本，因此没有形成可比的
字段级数值结论。这里仅记录样本筛选差异，不据此判断任一实现正确或错误。

## 阅读顺序

1. [Validation Policy](./validation-policy.md)
2. [Evidence Matrix](./evidence-matrix.md)
3. [Dataset Registry](./dataset-registry.md)
4. [Reproducible Validation Cases](./reproducible-validation.md)
5. [Command Support Matrix](../command-support-matrix/README.md)
