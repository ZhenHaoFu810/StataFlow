# M03 HDFE 审查发现 findings.md

## 基线

| 项目 | 值 |
|---|---|
| 模块 | M03 HDFE |
| 基线 commit | `2c7db1ca095e03d29c471e8d523fdaa943306174` |
| reghdfe 版本 | 6.13.1 |
| 核心对象 | `AbsorbingOLS`、`reghdfe()`、`areg()` |

---

## M03-HDFE-001：嵌套于 cluster 变量的 FE 冗余未被识别

- **Severity**: P1
- **Evidence Status**: Confirmed-Stata
- **Affected API**: `AbsorbingOLS(...).fit(vce='cluster', cluster=...)`
- **最小复现**: `tests/audit_v1_3/m03_hdfe/repro_m03_hdfe_findings.py::repro_001_nested_fe_cluster`
- **Stata 17 结果**:
  - `reghdfe y x, absorb(firm year) vce(cluster industry)`
  - `firm` 24 个类别全部标记为 "* = FE nested within cluster; treated as redundant"
  - `e(df_a) = 3`（仅 year 的 3 个系数有效）
  - cluster SE 基于 6 个 industry clusters
- **Python 结果**:
  - `df_a = 27`（= 24 + 4 - 1）
  - cluster SE 和 F 统计量与 Stata 偏离
- **根因分析**:
  - `_cluster_k_eff()` 和 `_compute_df_a()` 仅检查 FE 变量名是否 **等于** cluster 变量名，未检测 FE 是否按取值嵌套于 cluster。
  - 当 `firm` 的取值完全由 `industry` 决定时，所有 firm FE 系数在 cluster-robust 推断中都是冗余的，但 Python 仍将其计入 `df_a` 和 `k_eff`。
- **用户影响**: 在典型实证设计（如 firm 嵌套于行业/地区、员工嵌套于企业）中，cluster VCE、F 检验、R²_adj 会系统性错误。
- **受影响范围**: 所有 `AbsorbingOLS` / `reghdfe` / `areg` 的 cluster VCE 路径，只要 FE 与 cluster 存在构造性嵌套。
- **是否共享基础设施**: 否，问题在 `absorbing_ols.py` 的嵌套检测逻辑。
- **旧 issue**: 未见已登记。
- **建议修复方向**: 在 `_prepare_data` 或 `_cluster_k_eff` 中增加嵌套检测：若 FE 变量在每个 cluster 组内取值为常数，则该 FE 视为嵌套于 cluster，并在 `df_a`/`k_eff` 中扣除相应冗余。

---

## M03-HDFE-002：Slope 吸收的 `df_a`、R²、RMSE、F 与 cluster VCE 偏离 Stata

- **Severity**: P1
- **Evidence Status**: Confirmed-Stata
- **Affected API**: `AbsorbingOLS(..., absorb=[AbsorbSpec(var, slopes=[...], has_intercept=True)]).fit(vce='cluster', cluster=...)`
- **最小复现**: `repro_m03_hdfe_findings.py::repro_002_slope_absorption`
- **Stata 17 结果**:
  - `reghdfe y x, absorb(firm##c.year) vce(cluster firm)`
  - `e(df_a) = 12`（12 个 firm 的 slope 系数）
  - 报告 x 和 _cons
- **Python 结果**:
  - `df_a = 0`
  - cluster SE 比 Stata 小约 11%（0.0837 vs 0.0939）
  - `r2_adj`、`rmse`、`f_stat`、`f_pvalue` 均偏离
- **根因分析**:
  - `_compute_df_a()` 在 reghdfe 模式下计算 `n_levels * params_per_level`，但 slope 吸收时 `params_per_level` 可能没有正确加总。
  - 更根本地，`_compute_df_a` 接收 `dummy_info` 列表，对 slope FE 的 dummy 信息处理可能遗漏了 slope 交互列，导致 `df_a` 被计为 0。
  - 错误的 `df_a` 进一步影响 `k_eff`、小样本修正、RMSE 分母、R²_adj 和 F 检验。
- **用户影响**: 任何使用 slope 吸收（如 firm-specific trends、region-specific time trends）的模型都会得到错误的推断统计量。
- **受影响范围**: Slope 吸收 + cluster/robust VCE 路径。
- **是否共享基础设施**: 否。
- **旧 issue**: 未见已登记。
- **建议修复方向**: 修正 `_compute_df_a` 对 slope dummy 列数的统计，并重新核对 slope 吸收下的 `_cluster_k_eff`、RMSE 分母和 `_cons` 恢复。

---

## M03-HDFE-003：非连通 FE 图退化情况下 `r2_adj` 与 Stata 语义不一致

- **Severity**: P2
- **Evidence Status**: Confirmed-Stata
- **Affected API**: `AbsorbingOLS(...).fit(vce='ols')` 在退化设计下
- **最小复现**: `repro_m03_hdfe_findings.py::repro_003_disconnected_graph`
- **Stata 17 结果**:
  - `df_r = 0`，R² = 1，SE = 0
  - `e(r2_a) = .`（缺失）
- **Python 结果**:
  - `df_r = 0`
  - `r2_adj = 0.0`（未缺失）
- **根因分析**:
  - 当模型饱和时，Stata reghdfe 将调整 R² 留空；Python 的分母计算产生 0.0。
- **用户影响**: 边界场景，用户可能看到无意义的调整 R²。
- **受影响范围**: 高度退化、样本量极小或 FE 组合导致 df_r=0 的设计。
- **是否共享基础设施**: 否。
- **旧 issue**: 未见已登记。
- **建议修复方向**: 当 `df_resid <= 0` 时，将 `r2_adj` 设为 `None`，与 Stata 一致。

---

## M03-HDFE-004：真实数据 2-FE cluster VCE 存在微小但稳定的相对差异

- **Severity**: P2
- **Evidence Status**: Confirmed-Stata
- **Affected API**: `AbsorbingOLS(..., absorb=[...]).fit(vce='cluster', cluster=...)`
- **Stata 17 结果**:
  - `reghdfe invest mvalue, absorb(firm_id year) vce(cluster firm_id)`
- **Python 结果**:
  - 系数一致，VCE `max_rel_diff = 1.99e-6`，略超 1e-6 容差。
- **根因分析**:
  - 可能是 `_cluster_k_eff` 或 cluster 小样本修正与 Stata 存在微小差异，或非平衡面板下 `_cons` 恢复的 delta-method 权重不同。
- **用户影响**: 大多数系数/SE 接近，但严格复现 Stata 17 时需注意。
- **受影响范围**: 2-FE cluster 真实数据。
- **是否共享基础设施**: 可能涉及 `_vce_utils` 的 cluster meat 计算。
- **旧 issue**: 与 VCE-002/003/004 相关区域可能重叠。
- **建议修复方向**: 在调试 R1 证据的基础上，逐元素比较 cluster meat 与小样本修正因子。

---

## 共享基础设施风险登记

### SI-VCE-001：`detect_collinear_columns` tolerance 偏松

- **影响模块**: M01、M02、M03、M04
- **具体表现**: 近共线变量在 OLS/FE/HDFE/IV 中均可能未被正确省略。
- **证据**: M01-LIN-002、M02-FE-006
- **M03 影响**: 在 slope 吸收或 FE 组合高度共线的设计中，可能出现类似问题。本轮未专门构造 M03 版本，但风险存在。
- **建议**: 统一校准共享共线性检测 tolerance，并在各估计器中补充 post-drop 维度一致性校验。

---

## 未发现问题的说明

- 常规 2-FE conventional VCE 在小样本和中等样本下与 Stata 一致（S1、S2）。
- 2-way cluster inclusion-exclusion 在测试布局下与 Stata 一致（S5）。
- Singleton 删除在测试布局下与 Stata 一致（S7）。
- MAP 与 LSDV 在 1-FE 高维设计下等价，且与 Stata 一致（S8）。
- 标签重命名、冗余 FE、尺度变换、行顺序等性质测试通过（P1-P4）。
