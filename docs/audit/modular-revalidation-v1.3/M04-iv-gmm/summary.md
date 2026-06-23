# M04 IV / GMM 审查总结 summary.md

## 审查结论

M04 IV / GMM 模块本轮独立审查完成。通过 6 个全新 synthetic 双跑、2 个新真实数据实验、3 个性质测试和 3 个最小复现，共确认 **4 个 finding（2 P1、2 P2）** 和 **1 个跨模块共享基础设施风险**。

常规 2SLS robust/cluster 与过度识别检验在测试场景下与 Stata 17 一致；但 **弱工具变量诊断未暴露、LIML 推断统计量偏离、常数吸收路径不报告 `_cons`** 等问题突出。

## 基线

| 项目 | 值 |
|---|---|
| 基线 commit | `2c7db1ca095e03d29c471e8d523fdaa943306174` |
| Python | 3.11.7 |
| Stata | 17.0 MP |
| ivreghdfe | 1.1.4 |
| ivreg2 | 4.1.12 |

## 已验证通过项

| 类别 | 实验 | 结果 |
|---|---|---|
| Synthetic | S1_hand_computable_2sls | PASS |
| Synthetic | S2_random_2sls_cluster | PASS |
| Synthetic | S4_overidentification | PASS |
| Property | P1_instrument_label_invariance | PASS |
| Property | P2_scale_invariance | PASS |
| Property | P3_row_order_invariance | PASS |
| Regression | 现有非 golden 测试 | 349 passed |

## 已确认问题

| ID | 严重性 | 问题简述 | 关键证据 |
|---|---|---|---|
| M04-IV-001 | P1 | 弱工具变量 `widstat` 未在 `ResultSchema.diagnostics` 中暴露 | S3, S5, R2, MR01 |
| M04-IV-002 | P1 | LIML 的 SE、RMSE、F 与 Stata 偏离 | S6, MR02 |
| M04-IV-003 | P2 | `IVAbsorbingOLS` 常数吸收路径不报告 `_cons` | S3, S6, MR03 |
| M04-IV-004 | P2 | 真实数据 2SLS robust VCE 5e-6 相对差异 | R1 |

## 共享基础设施风险

| ID | 问题 | 影响模块 |
|---|---|---|
| SI-VCE-001 | `detect_collinear_columns` tolerance 偏松 | M01-M04 |

## 未覆盖区域

- GMM2S 真实数据验证
- 多内生变量 weak-IV 细节
- HAC/HC2/HC3/权重 IV
- LIML Fuller Stock-Yogo 临界值

## 建议后续行动

1. **修复 M04-IV-001**：将 `IVAbsorbingOLS` 内部已计算的 `widstat`/`idstat` 写入 `ResultSchema.diagnostics`；在 `IV2SLS` 中补充弱 IV 诊断，或更新文档。
2. **修复 M04-IV-002**：以 Stata `ivreg2` 为基准核对 LIML 的 VCE 公式与拟合统计量。
3. **修复 M04-IV-003**：在常数/无真实 FE 的吸收路径中保留 `_cons`。
4. **调查 M04-IV-004**：逐元素比较 robust meat 与小样本因子。
5. **处理 SI-VCE-001**：与 M01-M03 协调共线性检测 tolerance。

## 交付物清单

- `docs/audit/modular-revalidation-v1.3/M04-iv-gmm/task_plan.md`
- `docs/audit/modular-revalidation-v1.3/M04-iv-gmm/test-design-register.md`
- `docs/audit/modular-revalidation-v1.3/M04-iv-gmm/findings.md`
- `docs/audit/modular-revalidation-v1.3/M04-iv-gmm/progress.md`
- `docs/audit/modular-revalidation-v1.3/M04-iv-gmm/summary.md`
- `docs/audit/modular-revalidation-v1.3/M04-iv-gmm/evidence/`
- `tests/audit_v1_3/m04_iv_gmm/audit_utils.py`
- `tests/audit_v1_3/m04_iv_gmm/test_m04_synthetic.py`
- `tests/audit_v1_3/m04_iv_gmm/test_m04_realdata.py`
- `tests/audit_v1_3/m04_iv_gmm/test_m04_property.py`
- `tests/audit_v1_3/m04_iv_gmm/repro_m04_iv_findings.py`

本轮未修改 `src/stataflow/` 产品代码。
