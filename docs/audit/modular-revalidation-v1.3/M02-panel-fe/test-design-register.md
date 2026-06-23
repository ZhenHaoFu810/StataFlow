# M02 Panel / FE 测试设计登记册 v1.3

## 基线信息

| 项目 | 值 |
|---|---|
| 模块 | M02 Panel / FE |
| 基线分支 | `dev` |
| 基线 commit | `2c7db1ca095e03d29c471e8d523fdaa943306174` |
| Python | 3.11.7 |
| Stata | 17.0 MP |
| 审查日期 | 2026-06-13 |

## 审查对象

- 核心估计器：`stataflow.FixedEffectsOLS`
- Stata 兼容层：`stataflow.compat.stata.xtreg_fe`、`areg` 单吸收 FE 路径
- 关键机制：within transformation、LSDV 等价性、组内共线性、cluster-robust FE VCE、`add_constant` 与 `_cons` VCE 扩展

---

## Synthetic 双跑实验

### S1_hand_computable_panel

| 字段 | 内容 |
|---|---|
| Test ID | S1_hand_computable_panel |
| 审查问题 | within transformation 与 LSDV 是否给出一致系数、VCE、df_model、F p-value |
| DGP | 手工构造 3 entity × 4 period 平衡面板，实体固定效应可手工计算 |
| 理论预期 | FE 去心后 OLS 斜率 = 2.0（设计值），`e(df_m)=G+k-1=3`，F p-value 使用 `e(df_m)` |
| 与旧测试差异 | 旧 golden 使用 statsmodels 随机面板；本实验使用确定性手工小面板，可直接验证 within 结果 |
| Stata 命令 | `xtset entity time` / `xtreg y x, fe` |
| Python API | `FixedEffectsOLS(df, y='y', x=['x'], fe='entity', add_constant=True).fit(vce='ols')` |
| 比较字段 | coefficients, VCE, nobs, df_model, df_resid, r2, r2_adj, rmse, f_stat, f_pvalue |
| 新颖性 | 手工面板可人工复算，专门用于验证整体 F 检验的 df 语义 |
| 执行结果 | 系数/VCE/大部分标量 PASS；**f_pvalue FAIL**（Python 使用 `k=1` 的 dfn，Stata 使用 `e(df_m)=3`） |
| Evidence | `docs/audit/modular-revalidation-v1.3/M02-panel-fe/evidence/synthetic/S1_hand_computable_panel_report.json` |

### S2_random_panel_ols

| 字段 | 内容 |
|---|---|
| Test ID | S2_random_panel_ols |
| 审查问题 | 中等样本随机面板下常规 FE VCE 的数值精度 |
| DGP | `np.random.default_rng(2024)`，20 entities × 5 periods，含实体效应和时变误差 |
| 理论预期 | within 估计量与 Stata `xtreg, fe` 在 1e-6 内一致 |
| 与旧测试差异 | 新 seed、新样本维度、独立构造数据生成过程 |
| Stata 命令 | `xtreg y x, fe` |
| Python API | `FixedEffectsOLS(...).fit(vce='ols')` |
| 比较字段 | coefficients, VCE, nobs, df_model, df_resid, r2, r2_adj, rmse, f_stat, f_pvalue |
| 执行结果 | **PASS** |
| Evidence | `evidence/synthetic/S2_random_panel_ols_report.json` |

### S3_entity_invariant_dropped

| 字段 | 内容 |
|---|---|
| Test ID | S3_entity_invariant_dropped |
| 审查问题 | 组内无变异变量 `z_i` 是否被正确删除 |
| DGP | 8 entities × 5 periods，`z = entity-level mean(x)` 加极小扰动 |
| 理论预期 | Stata 标记 `z` 为 omitted；Python 应同样删除且不崩溃 |
| 与旧测试差异 | 主动注入与 `x` 近共线的实体不变变量，测试删除后 VCE 维度一致性 |
| Stata 命令 | `xtreg y x z, fe` |
| Python API | `FixedEffectsOLS(..., x=['x','z'], ...).fit(vce='ols')` |
| 比较字段 | coefficients, VCE, nobs, df_model, df_resid |
| 执行结果 | **FAIL / 崩溃**：`add_constant=True` 时 `LinAlgError: Singular matrix`；`add_constant=False` 可完成但保留 `z` |
| Evidence | `evidence/synthetic/S3_entity_invariant_dropped_report.json` |

### S4_unbalanced_singleton

| 字段 | 内容 |
|---|---|
| Test ID | S4_unbalanced_singleton |
| 审查问题 | 不平衡面板 + singleton entity 的 `_cons`、自由度与样本筛选 |
| DGP | 10 entities，各 entity 观测数从 1 到 10 不等，含一个 singleton |
| 理论预期 | Stata 保留 singleton 并估计其 FE；`_cons` 的 VCE 扩展需与 LSDV 一致 |
| 与旧测试差异 | 旧测试多为平衡面板；本实验专门构造非平衡 + singleton |
| Stata 命令 | `xtreg y x, fe` |
| Python API | `FixedEffectsOLS(...).fit(vce='ols')` |
| 比较字段 | coefficients, VCE, nobs, df_model, df_resid, r2, r2_adj, rmse |
| 执行结果 | **FAIL**：`_cons` beta 与 SE 与 Stata 偏离；其他字段接近 |
| Evidence | `evidence/synthetic/S4_unbalanced_singleton_report.json` |

### S5_fe_cluster_different_id

| 字段 | 内容 |
|---|---|
| Test ID | S5_fe_cluster_different_id |
| 审查问题 | cluster 层级与 panel id 不一致时 FE cluster-robust VCE、df_model、r2_adj |
| DGP | 20 entities × 5 periods，再划分为 4 cluster groups，每个 group 包含 5 entities |
| 理论预期 | `xtreg y x, fe cluster(g)` 的 `e(df_m)=0`（Stata cluster FE 默认不报告模型 F） |
| 与旧测试差异 | 明确构造 cluster id ≠ entity id 的两层结构，专门检查 df_model 语义 |
| Stata 命令 | `xtreg y x, fe cluster(g)` |
| Python API | `FixedEffectsOLS(...).fit(vce='cluster', cluster='g')` |
| 比较字段 | coefficients, VCE, df_model, r2_adj, f_pvalue, cluster_count |
| 执行结果 | **FAIL**：Python `df_model=1` vs Stata `0`；`r2_adj` 不一致；`f_pvalue` 缺失 |
| Evidence | `evidence/synthetic/S5_fe_cluster_different_id_report.json` |

### S6_add_constant

| 字段 | 内容 |
|---|---|
| Test ID | S6_add_constant |
| 审查问题 | `add_constant=True` 时 `_cons` 的数值与 VCE 扩展是否正确 |
| DGP | 30 entities × 4 periods，真实常数项 1.0 |
| 理论预期 | `_cons` 系数与 SE 与 Stata `xtreg, fe` 一致 |
| 与旧测试差异 | 单独隔离 `add_constant=True` 路径，不依赖 wrapper 默认行为 |
| Stata 命令 | `xtreg y x, fe` |
| Python API | `FixedEffectsOLS(..., add_constant=True).fit(vce='ols')` |
| 比较字段 | `_cons` beta/SE/VCE，以及斜率 x |
| 执行结果 | **FAIL**：`_cons` beta 与 SE 偏离 Stata；斜率 x PASS |
| Evidence | `evidence/synthetic/S6_add_constant_report.json` |

### S6_wrapper_default_constant

| 字段 | 内容 |
|---|---|
| Test ID | S6_wrapper_default_constant |
| 审查问题 | `xtreg_fe()` wrapper 的默认 `constant` 参数是否与 Stata `xtreg, fe` 一致 |
| DGP | 40 entities × 4 periods |
| 理论预期 | Stata `xtreg, fe` 始终报告 `_cons`；wrapper 应默认输出 `_cons` |
| 与旧测试差异 | 直接测试 wrapper 契约，而非底层 estimator |
| Stata 命令 | `xtreg y x, fe` |
| Python API | `xtreg_fe(df, y='y', x=['x'], fe='entity')` |
| 比较字段 | coefficient names、`_cons` beta/SE |
| 执行结果 | **FAIL**：wrapper 默认 `constant=False`，不返回 `_cons` |
| Evidence | `evidence/synthetic/S6_wrapper_default_constant_report.json` |

### S7_near_collinear_within

| 字段 | 内容 |
|---|---|
| Test ID | S7_near_collinear_within |
| 审查问题 | 组内近共线变量是否被正确省略（M01-LIN-002 的 FE 版本） |
| DGP | 8 entities × 5 periods，`w = x + 1e-10 * noise` |
| 理论预期 | Stata 将 `w` 标记 omitted；Python 应同样识别组内共线性 |
| 与旧测试差异 | 把 M01 发现的共线性 tolerance 问题迁移到 within-transformed 数据 |
| Stata 命令 | `xtreg y x w, fe` |
| Python API | `FixedEffectsOLS(..., x=['x','w'], ...).fit(vce='ols')` |
| 比较字段 | 保留系数集合、VCE、`_cons` beta/SE |
| 执行结果 | **FAIL**：Python 保留 `w` 并给出巨大系数/SE；Stata 省略 `w`；`_cons` 亦偏离 |
| Evidence | `evidence/synthetic/S7_near_collinear_within_report.json` |

---

## Real-Data 双跑实验

### R1_grunfeld_fe_cluster

| 字段 | 内容 |
|---|---|
| Test ID | R1_grunfeld_fe_cluster |
| 数据来源 | statsmodels `grunfeld` 数据集（公开） |
| 与旧测试差异 | 旧 golden `test_v1_xtreg_fe_real_grunfeld.py` 使用 conventional VCE 和两个斜率；本实验使用 **cluster(firm)** |
| Stata 命令 | `xtset firm_id year` / `xtreg invest mvalue, fe cluster(firm_id)` |
| Python API | `FixedEffectsOLS(..., x=['mvalue'], fe='firm_id', add_constant=True).fit(vce='cluster', cluster='firm_id')` |
| 比较字段 | coefficients, VCE, nobs, df_model, df_resid, r2, r2_adj, rmse, f_pvalue, cluster_count |
| 执行结果 | **FAIL**：`df_model` 1 vs 0、`r2_adj` 偏离、`f_pvalue` 缺失、VCE max_rel_diff=2.38e-6 |
| Evidence | `evidence/real-data/R1_grunfeld_fe_cluster_report.json` |

### R2_grunfeld_two_way_fe

| 字段 | 内容 |
|---|---|
| Test ID | R2_grunfeld_two_way_fe |
| 数据来源 | statsmodels `grunfeld` 数据集 |
| 与旧测试差异 | 旧 golden 使用单 FE；本实验构造 **entity FE + time dummies** 的两向 within 模型 |
| Stata 命令 | `xtset firm_id year` / `xtreg invest mvalue i.year, fe` |
| Python API | `FixedEffectsOLS(..., x=['mvalue'] + year_dummies, fe='firm_id', add_constant=True).fit(vce='ols')` |
| 比较字段 | coefficients（mvalue + 时间虚拟变量）、nobs、df_model、df_resid、r2、r2_adj、rmse、F |
| 执行结果 | **PASS** |
| Evidence | `evidence/real-data/R2_grunfeld_two_way_fe_report.json` |

---

## Metamorphic / Property Tests

### P1_entity_label_invariance

| 字段 | 内容 |
|---|---|
| 性质 | 实体标签一一重命名不应改变估计 |
| 执行方式 | 先生成基线 FE 估计，再将 `entity` 映射为字符串标签后重新估计 |
| 结果 | **PASS** |
| Evidence | `evidence/property/P1_entity_label_invariance_report.json` |

### P2_time_reorder_invariance

| 字段 | 内容 |
|---|---|
| 性质 | 对每个实体内部的时间顺序重排不应改变斜率估计 |
| 执行方式 | 在保持 entity 分组的前提下随机打乱行顺序 |
| 结果 | **PASS** |
| Evidence | `evidence/property/P2_time_reorder_invariance_report.json` |

### P3_entity_invariant_dropped

| 字段 | 内容 |
|---|---|
| 性质 | 增加一个实体内部不变的变量应被删除，且不破坏估计 |
| 执行方式 | 在面板中构造 `z = entity mean(x)` 并加入回归 |
| 结果 | **FAIL**：Python 未删除 `z`，产生巨大系数/SE 或 `LinAlgError` |
| Evidence | `evidence/property/P3_entity_invariant_dropped_report.json` |

### P4_scale_invariance

| 字段 | 内容 |
|---|---|
| 性质 | 对 `y` 和所有 `x` 同乘常数，斜率估计不变 |
| 执行方式 | 将 `y` 和 `x` 乘以 7.0 后重新估计 |
| 结果 | **PASS** |
| Evidence | `evidence/property/P4_scale_invariance_report.json` |

---

## 最小复现脚本

| Finding | 脚本路径 |
|---|---|
| M02-FE-001 | `tests/audit_v1_3/m02_panel_fe/repro_m02_fe_findings.py`（函数 `repro_001_f_pvalue_df_model`） |
| M02-FE-002 | 同上 `repro_002_collinear_drop_crash` |
| M02-FE-003 | 同上 `repro_003_unbalanced_cons` |
| M02-FE-004 | 同上 `repro_004_cluster_df_model` |
| M02-FE-005 | 同上 `repro_005_wrapper_default_constant` |
| M02-FE-006 | 同上 `repro_006_within_collinear_not_dropped` |
| M02-FE-007 | 同上 `repro_007_entity_invariant_not_dropped` |

---

## 代码资产清单

- `tests/audit_v1_3/m02_panel_fe/audit_utils.py`：M02 专用 Stata 执行、日志解析、字段级比较、证据保存
- `tests/audit_v1_3/m02_panel_fe/test_m02_synthetic.py`：7 个 synthetic 双跑实验
- `tests/audit_v1_3/m02_panel_fe/test_m02_realdata.py`：2 个真实数据双跑实验
- `tests/audit_v1_3/m02_panel_fe/test_m02_property.py`：4 个性质测试
- `tests/audit_v1_3/m02_panel_fe/repro_m02_fe_findings.py`：7 个最小复现
- `stata/cases/audit_v1_3_m02/`：本轮生成的 `.do` 与 `.csv`
- `stata/output/audit_v1_3_m02/`：本轮 Stata `.log`
