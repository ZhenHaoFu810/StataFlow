# M04 IV / GMM 模块独立审查计划 v1.3

**Goal:** 对 StataFlow 的 M04 IV / GMM 模块（`IV2SLS`、`IVAbsorbingOLS`、`ivregress_2sls()`、`ivreghdfe()`、2SLS/GMM2S/LIML、弱工具变量诊断、过度识别检验、多向 cluster VCE）进行独立审查，发现数学错误、统计语义偏差、代码缺陷、边界条件错误、结果字段错误和 Stata 17 复现失败。本轮只记录问题，不修改产品代码。

**Architecture:** 每个实验独立设计新的 DGP / 数据结构，独立编写新的 Stata 17 `.do` 文件和新的 Python 审查脚本，现场执行字段级双跑。审查资产保存在 `docs/audit/modular-revalidation-v1.3/M04-iv-gmm/evidence/` 下。

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

- 核心估计器：`stataflow.IV2SLS`、`stataflow.IVAbsorbingOLS`
- Stata 兼容层：`stataflow.compat.stata.ivregress_2sls`、`stataflow.compat.stata.ivreghdfe`
- 关键机制：2SLS 两阶段、GMM2S、LIML/k-class、弱工具变量诊断、过度识别检验、cluster/HDFE VCE

---

## 关键风险领域

1. **识别条件与秩亏**：恰好识别、过度识别、不可识别情形的样本与错误处理。
2. **弱工具变量 F 统计量与 Stock-Yogo 临界值**：不同 VCE 下的 `widstat`、多内生变量。
3. **吸收 FE 后的 cluster 小样本修正**：`k_eff` 是否包含 `df_a`、嵌套 FE。
4. **一阶段与结构方程样本一致性**：缺失筛选后两阶段样本是否一致。
5. **多向 cluster inclusion-exclusion 与 PSD 修正**：IV 版本与 OLS 版本的差异。
6. **LIML / Fuller / k-class**：lambda 计算、Fuller 调整、VCE。
7. **过度识别检验（Sargan/Hansen J）**：`IV2SLS` 与 `IVAbsorbingOLS` 的覆盖范围。
8. **`ivregress_2sls` 缺失弱工具变量诊断**：支持矩阵声明但代码未实现。

---

## 实验设计

### Synthetic

1. **S1**: 手工小样本 2SLS，验证系数与标准误
2. **S2**: 中等样本随机 DGP，2SLS + robust/cluster
3. **S3**: 弱工具变量设计（低 concentration parameter），检查 first-stage F 与 Stock-Yogo
4. **S4**: 多内生变量 + 多工具变量，检查 df 与 VCE
5. **S5**: 过度识别（2 工具 vs 1 内生），检查 Hansen J / Sargan
6. **S6**: 不可识别 / 恰好识别边界
7. **S7**: LIML/Fuller 与 2SLS 比较
8. **S8**: ivreghdfe 单 FE + cluster
9. **S9**: ivreghdfe 2-way cluster

### Real-Data

1. **R1**: 公开数据（如 card）2SLS with `ivregress 2sls`
2. **R2**: 同一数据集 ivreghdfe with cluster and FE

### Property Tests

1. **P1**: 工具变量标签重命名不影响估计
2. **P2**: 增加弱/无关工具变量不应剧烈改变主系数（边界检查）
3. **P3**: 对 y 和 x 同尺度缩放，斜率不变

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
- Python 审查脚本：`tests/audit_v1_3/m04_iv_gmm/`
- Stata `.do` 文件：`stata/cases/audit_v1_3_m04/`
