# M02 Panel / FE 审查总结 summary.md

## 审查结论

M02 Panel / FE 模块本轮独立审查完成。通过 7 个全新 synthetic 双跑、2 个新真实数据实验、4 个性质测试和 7 个最小复现，共确认 **7 个 finding（1 个 P0、6 个 P1）** 和 **1 个跨模块共享基础设施风险**。

在常规平衡面板、常规 VCE 路径下，斜率系数与标准误可与 Stata 17 在 1e-6 内对齐；但 **FE 整体 F 检验、`add_constant=True` 的 `_cons` 恢复、cluster FE 自由度、wrapper 默认行为、共线性/实体不变变量删除** 等关键路径存在明显偏差或崩溃。

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

## 已验证通过项

| 类别 | 实验 | 结果 |
|---|---|---|
| Synthetic | S2_random_panel_ols | PASS：系数、VCE、标量字段均与 Stata 一致 |
| Synthetic | S6_wrapper_default_constant | 用于证明 wrapper 默认行为问题，本身结果明确 |
| Real-Data | R2_grunfeld_two_way_fe | PASS：entity FE + time dummies 的两向 within 模型与 Stata 一致 |
| Property | P1_entity_label_invariance | PASS |
| Property | P2_time_reorder_invariance | PASS |
| Property | P4_scale_invariance | PASS |
| Regression | 现有非 golden 测试 | 349 passed，无破坏 |

## 已确认问题

| ID | 严重性 | 问题简述 | 关键证据 |
|---|---|---|---|
| M02-FE-001 | P1 | FE F 检验 p-value 使用 `k` 而非 Stata `e(df_m)=G+k-1` | S1, R1, MR01 |
| M02-FE-002 | P0 | `add_constant=True` + 组内共线变量导致 `LinAlgError` | S3, MR02 |
| M02-FE-003 | P1 | 非平衡面板 + singleton 下 `_cons` 系数/SE 偏离 Stata | S4, MR03 |
| M02-FE-004 | P1 | cluster FE 下 `df_model`、`r2_adj`、F p-value 与 Stata 不一致 | S5, R1, MR04 |
| M02-FE-005 | P1 | `xtreg_fe()` wrapper 默认 `constant=False` | S6, MR05 |
| M02-FE-006 | P1 | 组内近共线变量未被省略 | S7, MR06 |
| M02-FE-007 | P1 | 实体内部不变变量未被删除或导致崩溃 | P3, MR07 |

## 共享基础设施风险

| ID | 问题 | 影响模块 |
|---|---|---|
| SI-VCE-001 | `detect_collinear_columns` tolerance 偏松，近共线变量未正确省略 | M01、M02、M03、M04 |

## 未覆盖区域

- `areg()` 单吸收 FE 路径未独立穷举。
- FE 权重（`aweight`/`fweight`）行为未审查。
- `predict`、残差、savefe 等 postestimation 未纳入。
- 非 `add_constant=True` 的 `_cons` 语义未逐项比较。

## 建议后续行动

1. **修复 M02-FE-002（P0 崩溃）**：在 `fe.py` 中同步更新共线删除后的维度，确保 `add_constant=True` 路径的 VCE 扩展正确。
2. **修复 M02-FE-005（wrapper 默认行为）**：将 `xtreg_fe()` 默认 `constant` 改为 `True`。
3. **校准 F 检验与 cluster FE 自由度**：统一按 Stata `e(df_m)` 语义计算 `df_model`、`f_pvalue`、`r2_adj`。
4. **修复 `_cons` 恢复逻辑**：验证非平衡面板/singleton 下的 LSDV 均值权重。
5. **处理共享基础设施 SI-VCE-001**：与 M01、M03、M04 协调，统一共线性检测 tolerance 与遗漏变量处理。
6. **补充审查**：在 M02 修复后，重新跑本轮全部实验作为回归验证。

## 交付物清单

- `docs/audit/modular-revalidation-v1.3/M02-panel-fe/task_plan.md`
- `docs/audit/modular-revalidation-v1.3/M02-panel-fe/test-design-register.md`
- `docs/audit/modular-revalidation-v1.3/M02-panel-fe/findings.md`
- `docs/audit/modular-revalidation-v1.3/M02-panel-fe/progress.md`
- `docs/audit/modular-revalidation-v1.3/M02-panel-fe/summary.md`
- `docs/audit/modular-revalidation-v1.3/M02-panel-fe/evidence/synthetic/`
- `docs/audit/modular-revalidation-v1.3/M02-panel-fe/evidence/real-data/`
- `docs/audit/modular-revalidation-v1.3/M02-panel-fe/evidence/property/`
- `docs/audit/modular-revalidation-v1.3/M02-panel-fe/evidence/minimal-reproductions/`
- `tests/audit_v1_3/m02_panel_fe/audit_utils.py`
- `tests/audit_v1_3/m02_panel_fe/test_m02_synthetic.py`
- `tests/audit_v1_3/m02_panel_fe/test_m02_realdata.py`
- `tests/audit_v1_3/m02_panel_fe/test_m02_property.py`
- `tests/audit_v1_3/m02_panel_fe/repro_m02_fe_findings.py`
- `stata/cases/audit_v1_3_m02/`（本轮 `.do` 与 `.csv`）
- `stata/output/audit_v1_3_m02/`（本轮 `.log`）

本轮未修改 `src/stataflow/` 产品代码。
