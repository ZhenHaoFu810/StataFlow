# M04 IV / GMM 测试设计登记册 v1.3

## 基线信息

| 项目 | 值 |
|---|---|
| 模块 | M04 IV / GMM |
| 基线分支 | `dev` |
| 基线 commit | `2c7db1ca095e03d29c471e8d523fdaa943306174` |
| Python | 3.11.7 |
| Stata | 17.0 MP |
| ivreghdfe | 1.1.4 |
| ivreg2 | 4.1.12 |
| 审查日期 | 2026-06-13 |

## 审查对象

- 核心估计器：`stataflow.IV2SLS`、`stataflow.IVAbsorbingOLS`
- Stata 兼容层：`stataflow.compat.stata.ivregress_2sls`、`stataflow.compat.stata.ivreghdfe`
- 关键机制：2SLS、GMM2S、LIML、弱工具变量诊断、过度识别检验、cluster VCE、吸收 FE

---

## Synthetic 双跑实验

### S1_hand_computable_2sls

| 字段 | 内容 |
|---|---|
| 审查问题 | 小样本 2SLS 系数、robust SE、VCE |
| DGP | 20 obs，单一内生变量 x，单一工具 z |
| Stata 命令 | `ivregress 2sls y (x = z), robust` |
| Python API | `IV2SLS(...).fit(vce='robust')` |
| 结果 | **PASS** |
| Evidence | `evidence/synthetic/S1_hand_computable_2sls_report.json` |

### S2_random_2sls_cluster

| 字段 | 内容 |
|---|---|
| 审查问题 | 2SLS + cluster VCE |
| DGP | 120 obs，20 clusters，一个外生变量 w |
| Stata 命令 | `ivregress 2sls y w (x = z), cluster(g)` |
| Python API | `IV2SLS(...).fit(vce='cluster', cluster='g')` |
| 结果 | **PASS** |
| Evidence | `evidence/synthetic/S2_random_2sls_cluster_report.json` |

### S3_weak_iv

| 字段 | 内容 |
|---|---|
| 审查问题 | 弱工具变量诊断 `widstat` 是否暴露 |
| DGP | 200 obs，x 对 z 的回归系数仅 0.05 |
| Stata 命令 | `ivreg2 y (x = z), robust` |
| Python API | `IVAbsorbingOLS(..., absorb='__one').fit(vce='robust')` |
| 结果 | **FAIL**：Python 未返回 `widstat`；`_cons` 未报告 |
| Evidence | `evidence/synthetic/S3_weak_iv_report.json` |

### S4_overidentification

| 字段 | 内容 |
|---|---|
| 审查问题 | 过度识别 Hansen J / Sargan |
| DGP | 150 obs，两个工具 z1/z2，一个内生变量 x |
| Stata 命令 | `ivregress 2sls y w (x = z1 z2), robust` |
| Python API | `IV2SLS(...).fit(vce='robust')` |
| 结果 | **PASS** |
| Evidence | `evidence/synthetic/S4_overidentification_report.json` |

### S5_ivreghdfe_2fe_cluster

| 字段 | 内容 |
|---|---|
| 审查问题 | ivreghdfe 2-FE + cluster 下的系数与弱工具变量诊断 |
| DGP | 30 firms × 5 years |
| Stata 命令 | `ivreghdfe y (x = z), absorb(firm year) cluster(firm)` |
| Python API | `IVAbsorbingOLS(..., absorb=['firm','year']).fit(vce='cluster', cluster='firm')` |
| 结果 | **FAIL**：Python 未返回 `widstat` |
| Evidence | `evidence/synthetic/S5_ivreghdfe_2fe_cluster_report.json` |

### S6_liml

| 字段 | 内容 |
|---|---|
| 审查问题 | LIML 系数、SE、VCE、拟合统计量 |
| DGP | 120 obs，两个工具 z1/z2 |
| Stata 命令 | `ivreg2 y (x = z1 z2), liml` |
| Python API | `IVAbsorbingOLS(..., estimator='liml').fit(vce='ols')` |
| 结果 | **FAIL**：SE、RMSE、F 与 Stata 偏离；`_cons` 未报告 |
| Evidence | `evidence/synthetic/S6_liml_report.json` |

---

## Real-Data 双跑实验

### R1_grunfeld_ivregress

| 字段 | 内容 |
|---|---|
| 数据来源 | statsmodels `grunfeld` |
| 与旧测试差异 | 旧 golden 使用真实 card/wagepan 数据；本实验在 Grunfeld 上用 `kstock` 作为 `mvalue` 的工具变量 |
| Stata 命令 | `ivregress 2sls invest (mvalue = kstock), robust` |
| Python API | `IV2SLS(...).fit(vce='robust')` |
| 结果 | **FAIL**：VCE max_rel_diff=5.07e-6，略超容差 |
| Evidence | `evidence/real-data/R1_grunfeld_ivregress_report.json` |

### R2_grunfeld_ivreghdfe

| 字段 | 内容 |
|---|---|
| 数据来源 | statsmodels `grunfeld` |
| 与旧测试差异 | 在 Grunfeld 上做 ivreghdfe 2-FE + cluster |
| Stata 命令 | `ivreghdfe invest (mvalue = kstock), absorb(firm_id year) cluster(firm_id)` |
| Python API | `IVAbsorbingOLS(...).fit(vce='cluster', cluster='firm_id')` |
| 结果 | **FAIL**：Python 未返回 `widstat` |
| Evidence | `evidence/real-data/R2_grunfeld_ivreghdfe_report.json` |

---

## Property Tests

### P1_instrument_label_invariance

| 结果 | **PASS** |
| Evidence | `evidence/property/P1_instrument_label_invariance_report.json` |

### P2_scale_invariance

| 结果 | **PASS** |
| Evidence | `evidence/property/P2_scale_invariance_report.json` |

### P3_row_order_invariance

| 结果 | **PASS** |
| Evidence | `evidence/property/P3_row_order_invariance_report.json` |

---

## 最小复现脚本

| Finding | 路径 |
|---|---|
| M04-IV-001 | `tests/audit_v1_3/m04_iv_gmm/repro_m04_iv_findings.py::repro_001_missing_weakiv_diagnostics` |
| M04-IV-002 | 同上 `repro_002_liml_vce_mismatch` |
| M04-IV-003 | 同上 `repro_003_constant_absorb_no_cons` |

---

## 代码资产

- `tests/audit_v1_3/m04_iv_gmm/audit_utils.py`
- `tests/audit_v1_3/m04_iv_gmm/test_m04_synthetic.py`
- `tests/audit_v1_3/m04_iv_gmm/test_m04_realdata.py`
- `tests/audit_v1_3/m04_iv_gmm/test_m04_property.py`
- `tests/audit_v1_3/m04_iv_gmm/repro_m04_iv_findings.py`
