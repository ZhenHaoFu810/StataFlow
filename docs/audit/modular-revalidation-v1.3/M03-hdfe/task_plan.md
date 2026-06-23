# M03 HDFE 模块独立审查计划 v1.3

**Goal:** 对 StataFlow 的 M03 HDFE 模块（`AbsorbingOLS`、`reghdfe()`、`areg()`、多向固定效应吸收、LSDV/MAP 路径、slope 吸收、多向 cluster VCE、`_cons` 恢复、singleton 删除）进行独立审查，发现数学错误、统计语义偏差、代码缺陷、边界条件错误、结果字段错误和 Stata 17 复现失败。本轮只记录问题，不修改产品代码。

**Architecture:** 每个实验独立设计新的 DGP / 数据结构，独立编写新的 Stata 17 `.do` 文件和新的 Python 审查脚本，现场执行字段级双跑。审查资产保存在 `docs/audit/modular-revalidation-v1.3/M03-hdfe/evidence/` 下。

**Tech Stack:** Python 3.11, NumPy, pandas, SciPy, statsmodels, Stata 17, project `stataflow` package.

---

## 审查基线

| 项目 | 值 |
|---|---|
| 基线分支 | `dev` |
| 基线 commit SHA | `2c7db1ca095e03d29c471e8d523fdaa943306174` |
| Python | 3.11.7 |
| Stata | 17 |

---

## 纳入审查的 API

- 核心估计器：`stataflow.AbsorbingOLS`
- Stata 兼容层：`stataflow.compat.stata.reghdfe`、`stataflow.compat.stata.areg`
- 关键机制：LSDV vs MAP、多向 FE、singleton 删除、slope 吸收、多向 cluster VCE、Driscoll-Kraay、`_cons` 与 R² 语义

---

## 关键风险领域

1. **Disconnected FE graphs / 冗余自由度**：`_compute_df_a` 的 `(n_fes - 1)` 扣减是否匹配 Stata 的 mobility-group 处理。
2. **Nested FE 与 cluster 调整**：`_cluster_k_eff` 仅检查变量名相等，是否遗漏构造性嵌套。
3. **多向 cluster inclusion-exclusion 与 PSD 修正**：小样本、低聚类数、交互编码一致性。
4. **Slope 吸收与组内共线**：LSDV slope dummy 构造、`lstsq` 回退、`_cons` 恢复。
5. **Singleton 删除与 sample mask**：迭代算法、 slope-singleton、与 Stata `reghdfe` 等价性。
6. **`_cons` / R² / adjusted R² 语义**：LSDV 与 MAP 路径的常数项恢复、非平衡面板。
7. **`areg` 与 `reghdfe` 语义差异**：`df_a`、cluster `k_eff`、`noconstant`。
8. **MAP 收敛与数值稳定性**：高维 FE、多向 FE 迭代停止条件。

---

## 实验设计

### Synthetic

1. **S1**: 手工小样本 2-FE 平衡设计，验证 LSDV 系数与 `df_a`
2. **S2**: 中等样本随机面板 + 2 FE，conventional VCE
3. **S3**: 嵌套 FE（firm 嵌套于 industry）+ cluster(industry)，检查 `k_eff`
4. **S4**: 非连通二部图设计（某 firm 只出现在某 year），检查冗余自由度
5. **S5**: 多向 cluster（firm + year）与低聚类数 fallback
6. **S6**: Slope 吸收 `firm#c.time` 与 `firm##c.time`
7. **S7**: Singleton 删除与 `keepsingletons` 对样本数和 `_cons` 的影响
8. **S8**: MAP vs LSDV 等价性（高维 1-FE 强制 MAP）

### Real-Data

1. **R1**: 公开面板数据（wagepan 或 grunfeld）2-FE `reghdfe y x, absorb(firm year) cluster(firm)`
2. **R2**: 同一数据集的 slope 吸收规格 `reghdfe y x, absorb(firm#c.year) vce(cluster firm)`

### Property Tests

1. **P1**: 吸收变量标签重命名不影响估计
2. **P2**: 增加一个被吸收的冗余 FE（如 `entity` 和 `entity_copy`）应给出等价或明确错误结果
3. **P3**: 对 `y` 和 `x` 同尺度缩放，斜率不变
4. **P4**: 行顺序随机打乱不影响估计

---

## 交付物

- `task_plan.md`（本文件）
- `test-design-register.md`
- `findings.md`
- `progress.md`
- `summary.md`
- `evidence/synthetic/`
- `evidence/real-data/`
- `evidence/minimal-reproductions/`
- Python 审查脚本：`tests/audit_v1_3/m03_hdfe/`
- Stata `.do` 文件：`stata/cases/audit_v1_3_m03/`
