# M03 HDFE 审查总结 summary.md

## 审查结论

M03 HDFE 模块本轮独立审查完成。通过 8 个全新 synthetic 双跑、2 个新真实数据实验、4 个性质测试和 3 个最小复现，共确认 **4 个 finding（3 个 P1、1 个 P2）** 和 **1 个跨模块共享基础设施风险**。

在常规 2-FE conventional VCE、2-way cluster、singleton 删除、MAP/LSDV 等价性等路径上，Python 与 Stata 17 一致；但 **FE 嵌套于 cluster 的冗余识别、slope 吸收的 `df_a` 与 cluster VCE、退化设计下的 `r2_adj`** 等关键路径存在明显偏差。

## 基线

| 项目 | 值 |
|---|---|
| 基线分支 | `dev` |
| 基线 commit | `2c7db1ca095e03d29c471e8d523fdaa943306174` |
| Python | 3.11.7 |
| NumPy | 1.26.4 |
| pandas | 3.0.2 |
| SciPy | 1.17.1 |
| statsmodels | 0.14.6 |
| Stata | 17.0 MP |
| reghdfe | 6.13.1 |

## 已验证通过项

| 类别 | 实验 | 结果 |
|---|---|---|
| Synthetic | S1_hand_computable_2fe | PASS |
| Synthetic | S2_random_panel_2fe | PASS |
| Synthetic | S5_two_way_cluster | PASS |
| Synthetic | S7_singleton_drop | PASS |
| Synthetic | S8_map_vs_lsdv | PASS |
| Property | P1_absorb_label_invariance | PASS |
| Property | P2_redundant_absorb_fe | PASS |
| Property | P3_scale_invariance | PASS |
| Property | P4_row_order_invariance | PASS |
| Regression | 现有非 golden 测试 | 349 passed，无破坏 |

## 已确认问题

| ID | 严重性 | 问题简述 | 关键证据 |
|---|---|---|---|
| M03-HDFE-001 | P1 | FE 嵌套于 cluster 变量时冗余未被识别，导致 df_a/k_eff/SE/F 错误 | S3, R1, MR01 |
| M03-HDFE-002 | P1 | Slope 吸收时 df_a=0，cluster SE、R²、RMSE、F 偏离 Stata | S6, R2, MR02 |
| M03-HDFE-003 | P2 | 非连通 FE 图退化时 Stata 缺失 r2_adj，Python 报告 0.0 | S4, MR03 |
| M03-HDFE-004 | P2 | 真实数据 2-FE cluster VCE 存在 1.99e-6 相对差异 | R1 |

## 共享基础设施风险

| ID | 问题 | 影响模块 |
|---|---|---|
| SI-VCE-001 | `detect_collinear_columns` tolerance 偏松，近共线变量未正确省略 | M01、M02、M03、M04 |

## 未覆盖区域

- `areg()` 单吸收路径未独立穷举。
- Driscoll-Kraay VCE 未做独立真实数据验证。
- 权重 FE、高维 MAP 大规模压力测试、`savefe` 未审查。

## 建议后续行动

1. **修复 M03-HDFE-001**：在 `_cluster_k_eff` / `_compute_df_a` 中检测 FE 是否嵌套于 cluster（按取值），并对冗余 FE 扣除自由度。
2. **修复 M03-HDFE-002**：修正 slope 吸收的 `df_a` 计算，并连锁修正 `k_eff`、RMSE 分母、R²_adj、F 检验。
3. **处理 M03-HDFE-003**：当 `df_resid <= 0` 时将 `r2_adj` 设为 `None`。
4. **调查 M03-HDFE-004**：逐元素比较 R1 的 cluster meat 与小样本修正因子。
5. **处理共享基础设施 SI-VCE-001**：与 M01/M02/M04 协调统一共线性检测 tolerance。
6. **补充审查**：修复后重新跑本轮全部实验作为回归验证。

## 交付物清单

- `docs/audit/modular-revalidation-v1.3/M03-hdfe/task_plan.md`
- `docs/audit/modular-revalidation-v1.3/M03-hdfe/test-design-register.md`
- `docs/audit/modular-revalidation-v1.3/M03-hdfe/findings.md`
- `docs/audit/modular-revalidation-v1.3/M03-hdfe/progress.md`
- `docs/audit/modular-revalidation-v1.3/M03-hdfe/summary.md`
- `docs/audit/modular-revalidation-v1.3/M03-hdfe/evidence/synthetic/`
- `docs/audit/modular-revalidation-v1.3/M03-hdfe/evidence/real-data/`
- `docs/audit/modular-revalidation-v1.3/M03-hdfe/evidence/property/`
- `docs/audit/modular-revalidation-v1.3/M03-hdfe/evidence/minimal-reproductions/`
- `tests/audit_v1_3/m03_hdfe/audit_utils.py`
- `tests/audit_v1_3/m03_hdfe/test_m03_synthetic.py`
- `tests/audit_v1_3/m03_hdfe/test_m03_realdata.py`
- `tests/audit_v1_3/m03_hdfe/test_m03_property.py`
- `tests/audit_v1_3/m03_hdfe/repro_m03_hdfe_findings.py`
- `stata/cases/audit_v1_3_m03/`（本轮 `.do` 与 `.csv`）
- `stata/output/audit_v1_3_m03/`（本轮 `.log`）

本轮未修改 `src/stataflow/` 产品代码。
