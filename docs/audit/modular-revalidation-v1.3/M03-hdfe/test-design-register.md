# M03 HDFE 测试设计登记册 v1.3

## 基线信息

| 项目 | 值 |
|---|---|
| 模块 | M03 HDFE |
| 基线分支 | `dev` |
| 基线 commit | `2c7db1ca095e03d29c471e8d523fdaa943306174` |
| Python | 3.11.7 |
| Stata | 17.0 MP |
| reghdfe | 6.13.1 (2026-01-10) |
| 审查日期 | 2026-06-13 |

## 审查对象

- 核心估计器：`stataflow.AbsorbingOLS`
- Stata 兼容层：`stataflow.compat.stata.reghdfe`、`stataflow.compat.stata.areg`
- 关键机制：LSDV/MAP 双路径、多向 FE、singleton 删除、slope 吸收、1-way/2-way cluster、Driscoll-Kraay、`_cons` 与 R² 语义

---

## Synthetic 双跑实验

### S1_hand_computable_2fe

| 字段 | 内容 |
|---|---|
| Test ID | S1_hand_computable_2fe |
| 审查问题 | 2-FE 小样本下 LSDV 系数、VCE、df 是否可复现 |
| DGP | 3 firm × 4 year 手工面板，确定性实体/时间效应 |
| 理论预期 | 斜率接近 2.0，df_a = 3 + 3 = 6（再按 reghdfe 扣减 1）= 5 |
| 与旧测试差异 | 手工构造、新 seed，专门验证 `df_a` 和 F 字段 |
| Stata 命令 | `reghdfe y x, absorb(firm year) vce(ols)` |
| Python API | `AbsorbingOLS(df, y='y', x=['x'], absorb=['firm','year'], add_constant=True).fit(vce='ols')` |
| 比较字段 | coefficients, VCE, nobs, df_model, df_resid, df_a, r2, r2_adj, rmse, f_stat, f_pvalue |
| 执行结果 | **PASS** |
| Evidence | `evidence/synthetic/S1_hand_computable_2fe_report.json` |

### S2_random_panel_2fe

| 字段 | 内容 |
|---|---|
| Test ID | S2_random_panel_2fe |
| 审查问题 | 中等样本随机面板 2-FE conventional VCE 精度 |
| DGP | `seed=2025`，30 firms × 6 periods |
| Stata 命令 | `reghdfe y x, absorb(firm year) vce(ols)` |
| Python API | 同上 |
| 比较字段 | 全字段 |
| 执行结果 | **PASS** |
| Evidence | `evidence/synthetic/S2_random_panel_2fe_report.json` |

### S3_nested_fe_cluster

| 字段 | 内容 |
|---|---|
| Test ID | S3_nested_fe_cluster |
| 审查问题 | FE 嵌套于 cluster 变量时，Python 是否正确识别冗余 FE |
| DGP | 24 firms 分 6 industries（每 industry 4 firms），cluster(industry) |
| 理论预期 | Stata reghdfe 将 `firm` 的 24 个类别全部判为 redundant，仅保留 `year` 的 3 个系数，df_a=3 |
| 与旧测试差异 | 主动构造嵌套层级，专门测试 `_cluster_k_eff` 与 `_compute_df_a` 的嵌套检测 |
| Stata 命令 | `reghdfe y x, absorb(firm year) vce(cluster industry)` |
| Python API | `AbsorbingOLS(...).fit(vce='cluster', cluster='industry')` |
| 执行结果 | **FAIL**：Python df_a=27，Stata df_a=3；cluster SE、F 统计量、VCE 均偏离 |
| Evidence | `evidence/synthetic/S3_nested_fe_cluster_report.json` |

### S4_disconnected_fe_graph

| 字段 | 内容 |
|---|---|
| Test ID | S4_disconnected_fe_graph |
| 审查问题 | 非连通二部图下冗余 FE 自由度与退化结果 |
| DGP | 4 firms × 4 years，每个 firm 只出现 2 个年份，形成 disconnected cells |
| 理论预期 | 模型饱和，df_r=0，R²=1，Stata 不报告 r2_adj |
| Stata 命令 | `reghdfe y x, absorb(firm year) vce(ols)` |
| Python API | 同上 |
| 执行结果 | **FAIL（边界）**：`_cons` 数值微小偏离；Stata r2_adj 缺失，Python 报告 0.0 |
| Evidence | `evidence/synthetic/S4_disconnected_fe_graph_report.json` |

### S5_two_way_cluster

| 字段 | 内容 |
|---|---|
| Test ID | S5_two_way_cluster |
| 审查问题 | 2-way cluster inclusion-exclusion 与低聚类数 fallback |
| DGP | 15 firms × 6 years，cluster(firm year) |
| Stata 命令 | `reghdfe y x, absorb(firm year) vce(cluster firm year)` |
| Python API | `AbsorbingOLS(...).fit(vce='cluster', cluster=['firm','year'])` |
| 执行结果 | **PASS** |
| Evidence | `evidence/synthetic/S5_two_way_cluster_report.json` |

### S6_slope_absorption

| 字段 | 内容 |
|---|---|
| Test ID | S6_slope_absorption |
| 审查问题 | 截距 + 斜率吸收 `firm##c.year` 的 df_a、系数、VCE |
| DGP | 12 firms × 5 years，每 firm 有各自时间趋势 |
| Stata 命令 | `reghdfe y x, absorb(firm##c.year) vce(cluster firm)` |
| Python API | `AbsorbingOLS(..., absorb=[AbsorbSpec(var='firm', slopes=['year'], has_intercept=True)]).fit(vce='cluster', cluster='firm')` |
| 执行结果 | **FAIL**：Python df_a=0，Stata df_a=12；cluster SE、R²、RMSE、F 均偏离 |
| Evidence | `evidence/synthetic/S6_slope_absorption_report.json` |

### S7_singleton_drop

| 字段 | 内容 |
|---|---|
| Test ID | S7_singleton_drop |
| 审查问题 | singleton 删除与样本数、df_a 一致性 |
| DGP | 20 firms × 4 years，firm 20 仅出现 1 次 |
| Stata 命令 | `reghdfe y x, absorb(firm year) vce(ols)` |
| Python API | 默认 `drop_singletons=True` |
| 执行结果 | **PASS** |
| Evidence | `evidence/synthetic/S7_singleton_drop_report.json` |

### S8_map_vs_lsdv

| 字段 | 内容 |
|---|---|
| Test ID | S8_map_vs_lsdv |
| 审查问题 | MAP 迭代吸收与 LSDV 是否等价 |
| DGP | 600 firms × 3 periods，1-FE，强制 MAP vs LSDV |
| Stata 命令 | `reghdfe y x, absorb(firm) vce(ols)` |
| Python API | `technique='map'` vs `technique='lsdv'` |
| 执行结果 | **PASS**（MAP 与 LSDV 一致，且与 Stata 一致） |
| Evidence | `evidence/synthetic/S8_map_vs_lsdv_report.json` |

---

## Real-Data 双跑实验

### R1_grunfeld_2fe_cluster

| 字段 | 内容 |
|---|---|
| 数据来源 | statsmodels `grunfeld`（公开） |
| 与旧测试差异 | 旧 golden 多为 1-FE 或 conventional VCE；本实验为 **2-FE + cluster(firm)** |
| Stata 命令 | `reghdfe invest mvalue, absorb(firm_id year) vce(cluster firm_id)` |
| Python API | `AbsorbingOLS(..., absorb=['firm_id','year']).fit(vce='cluster', cluster='firm_id')` |
| 比较字段 | coefficients, VCE, nobs, df_model, df_resid, df_a, r2, r2_adj, rmse, F, cluster_count |
| 执行结果 | **FAIL**：VCE max_rel_diff=1.99e-6，略超容差 |
| Evidence | `evidence/real-data/R1_grunfeld_2fe_cluster_report.json` |

### R2_grunfeld_slope

| 字段 | 内容 |
|---|---|
| 数据来源 | statsmodels `grunfeld` |
| 与旧测试差异 | 旧 golden 未覆盖 slope 吸收；本实验使用 `absorb(firm_id##c.year)` |
| Stata 命令 | `reghdfe invest mvalue, absorb(firm_id##c.year) vce(cluster firm_id)` |
| Python API | `AbsorbingOLS(..., absorb=[AbsorbSpec(var='firm_id', slopes=['year'], has_intercept=True)]).fit(vce='cluster', cluster='firm_id')` |
| 执行结果 | **FAIL**：df_a=0 vs 11，cluster SE、R²、RMSE、F、VCE 均偏离 |
| Evidence | `evidence/real-data/R2_grunfeld_slope_report.json` |

---

## Metamorphic / Property Tests

### P1_absorb_label_invariance

| 字段 | 内容 |
|---|---|
| 性质 | 吸收变量标签一一重命名不改变估计 |
| 结果 | **PASS** |
| Evidence | `evidence/property/P1_absorb_label_invariance_report.json` |

### P2_redundant_absorb_fe

| 字段 | 内容 |
|---|---|
| 性质 | 增加一个完全冗余的吸收 FE 副本不改变斜率 |
| 结果 | **PASS** |
| Evidence | `evidence/property/P2_redundant_absorb_fe_report.json` |

### P3_scale_invariance

| 字段 | 内容 |
|---|---|
| 性质 | 对 `y` 和 `x` 同乘常数，斜率不变 |
| 结果 | **PASS** |
| Evidence | `evidence/property/P3_scale_invariance_report.json` |

### P4_row_order_invariance

| 字段 | 内容 |
|---|---|
| 性质 | 行顺序随机打乱不改变估计 |
| 结果 | **PASS** |
| Evidence | `evidence/property/P4_row_order_invariance_report.json` |

---

## 最小复现脚本

| Finding | 脚本路径 |
|---|---|
| M03-HDFE-001 | `tests/audit_v1_3/m03_hdfe/repro_m03_hdfe_findings.py::repro_001_nested_fe_cluster` |
| M03-HDFE-002 | 同上 `repro_002_slope_absorption` |
| M03-HDFE-003 | 同上 `repro_003_disconnected_graph` |

---

## 代码资产清单

- `tests/audit_v1_3/m03_hdfe/audit_utils.py`
- `tests/audit_v1_3/m03_hdfe/test_m03_synthetic.py`
- `tests/audit_v1_3/m03_hdfe/test_m03_realdata.py`
- `tests/audit_v1_3/m03_hdfe/test_m03_property.py`
- `tests/audit_v1_3/m03_hdfe/repro_m03_hdfe_findings.py`
- `stata/cases/audit_v1_3_m03/`（本轮 `.do` 与 `.csv`）
- `stata/output/audit_v1_3_m03/`（本轮 `.log`）
