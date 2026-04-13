# 测试样例目录清单

## 目录字段定义

| 字段 | 含义 |
| --- | --- |
| `case_id` | 测试样例唯一标识 |
| `phase` | 所属阶段 |
| `command` | 对应 Stata 命令 |
| `python_api` | 对应 Python API |
| `source` | 数据来源 |
| `risk_focus` | 样例主要风险点 |
| `stata_artifacts` | `.do/.log/.json` 等产物 |
| `python_test` | 对应 pytest 路径 |
| `comparison_mode` | `strict` 或 `stat_equiv` |
| `status` | `planned`/`ready`/`done` |

## 样例清单

| case_id | phase | command | python_api | source | risk_focus | stata_artifacts | python_test | comparison_mode | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `p0_min_ols_auto` | Phase 0 | `regress` | `OLS.fit(vce="ols")` | Stata 官方最小样例或手工构造数据 | runner 打通、结构化导出、字段对齐 | 待创建 | 待创建 | strict | planned |
| `p1_ols_basic` | Phase 1 | `regress` | `OLS.fit(vce="ols")` | 官方线性样例 | 系数、自由度、R2 | 待创建 | 待创建 | strict | planned |
| `p1_robust_hc1` | Phase 1 | `regress, vce(robust)` | `OLS.fit(vce="robust")` | 官方或手工构造 | robust 协方差 | 待创建 | 待创建 | strict | planned |
| `p1_cluster_firm` | Phase 1 | `regress, vce(cluster firm_id)` | `OLS.fit(vce="cluster", cluster="firm_id")` | firm-year panel | 单聚类修正、群组计数 | 待创建 | 待创建 | strict | planned |
| `p1_collinearity_drop` | Phase 1 | `regress` | `OLS.fit(vce="ols")` | 手工构造 | 共线变量剔除 | 待创建 | 待创建 | strict | planned |
| `p2_aweight_basic` | Phase 2 | `regress [aweight=...]` | `OLS(..., weights=..., weight_type="aweight")` | 横截面样例 | 权重语义 | 待创建 | 待创建 | strict | planned |
| `p2_fe_basic` | Phase 2 | `xtreg ..., fe` | `FixedEffectsOLS.fit(vce="ols")` | 面板样例 | within 转换、FE 自由度 | 待创建 | 待创建 | strict | planned |
| `p2_fe_cluster` | Phase 2 | `xtreg ..., fe vce(cluster firm_id)` | `FixedEffectsOLS.fit(vce="cluster", cluster="firm_id")` | 面板样例 | FE + cluster | 待创建 | 待创建 | strict | planned |

## 维护规则

- 新增能力前先新增样例条目
- 每个样例完成后补齐实际产物路径
- 若样例使用统计等价模式，必须在对应元数据文件中写明原因
