# M05 GLM 模块审查总结

## 审查目标

对 StataFlow 的 M05 GLM 模块（`Logit`、`Probit`、`Poisson` 核心估计器及 Stata 兼容包装器）进行新一轮独立、严格的 Stata 17 双跑审查，发现数学错误、统计语义偏差、代码缺陷和边界条件错误。本轮不修改产品代码，只记录问题与证据。

## 审查范围与方法

- **纳入 API**: `stataflow.Logit` / `Probit` / `Poisson`；`stataflow.compat.stata.logit` / `probit` / `poisson`。
- **审查文件**: `src/stataflow/estimators/glm.py`、`src/stataflow/compat/stata/glm.py`、`src/stataflow/results/result.py`、`src/stataflow/postestimation.py`；对应支持矩阵和研究档案。
- **实验数量**:
  - 新 synthetic 双跑：8 个设计（S1-S8），共 13 个测试函数。
  - 新真实数据双跑：4 个数据集，5 个测试函数。
  - property / metamorphic tests：3 个。
- **字段级比较**: 系数、标准误、完整 VCE、LL、伪 R²、deviance、df、cluster_count、警告/错误行为等。
- **默认容差**: 相对 `< 1e-6`；真实数据中小方差元素和 NLSW88 cluster VCE 放宽至 `1e-4`/`1e-6` 并记录原因。

## 主要结论

1. **核心估计数值正确**
   - Logit、Probit、Poisson 在 conventional、robust、cluster VCE 下的系数、标准误和完整 VCE 矩阵与 Stata 17 高度一致。
   - Robust VCE 的小样本修正使用 `n/(n-1)` 与 Stata 一致；cluster VCE 仅使用 `G/(G-1)` 与 Stata 一致。
   - Log-likelihood、伪 R²、deviance（logit/poisson）在有效样本下与 Stata 一致。

2. **包装器与 Stata 命令存在不一致（M05-GLM-001）**
   - `logit`/`probit`/`poisson` 包装器支持 `aweight`，但 Stata 17 官方命令拒绝 `[aweight]`（`r(101)`）。
   - 支持矩阵和文档存在夸大；需要重新设计权重参数映射或文档。

3. **结果字段语义存在偏差（M05-GLM-002 / M05-GLM-003）**
   - cluster VCE 下 Python 报告 `df_resid = G-1`，而 Stata GLM 命令不定义 `e(df_r)`，使用正态 z 推断。
   - robust/cluster VCE 下 Python 的 `f_stat` 仍是 LR chi2，Stata 的 `e(chi2)` 变为 Wald chi2。
   - 这些问题不影响系数/SE，但会导致 `ResultSchema` 字段与 Stata `e()` 字段不对应。

4. **分离/收敛处理不足（M05-GLM-004）**
   - Stata 检测完全分离并立即报错；Python 迭代至上限后报 `RuntimeError`，过程中出现除零警告。
   - 需要增加分离检测和更安全的数值裁剪。

5. **真实数据 cluster VCE 残余（M05-GLM-005）**
   - NLSW88 行业聚类 logit 的 VCE 非对角元素存在约 `2e-5` 相对残余，推断上无实质影响。

## 问题分级

| 等级 | 数量 | 内容 |
|---|---|---|
| P0 | 0 | 无阻断性错误 |
| P1 | 1 | `aweight` 参数与 Stata 命令不兼容 |
| P2 | 3 | `df_resid` 语义、`f_stat` 语义、分离检测/错误处理 |
| P3 | 1 | NLSW88 cluster VCE 2e-5 残余；共享 `detect_collinear_columns` 容差风险 |

## 通过项

- OLS/robust/cluster VCE 的系数、SE、VCE（synthetic + real-data）。
- 样本筛选、缺失值处理、共线性检测。
- 行顺序不变性、尺度变换、冗余变量删除等 metamorphic 性质。
- Logit/poisson deviance 计算（使用 `e(sample)` 限制后）。

## 未深入覆盖项

- `predict` / `margins` 的完整字段级双跑（部分在 M09 Postestimation 模块范围内）。
- `offset` / `exposure`（当前代码明确拒绝，未做 Stata 对比）。
- 多向 cluster / HAC VCE（GLM 模块未声明支持）。
- 大样本下的数值精度优化（已记录为 P3 残余）。

## 建议后续行动

1. 修复 GLM 包装器权重参数：统一使用 Stata 可接受的 `pweight`/`iweight` 或更新支持矩阵。
2. 明确 `ResultSchema` 中 `df_resid` 和 `f_stat` 在 GLM robust/cluster 下的语义，或增加 Wald/LR 区分字段。
3. 在 IRLS 中加入完全/准完全分离检测，并改进 `mu`/`gprime` 裁剪避免除零。
4. 全局统一审查 `detect_collinear_columns` 容差（跨 M01-M05）。

## 交付物清单

- `docs/audit/modular-revalidation-v1.3/M05-glm/task_plan.md`
- `docs/audit/modular-revalidation-v1.3/M05-glm/test-design-register.md`
- `docs/audit/modular-revalidation-v1.3/M05-glm/findings.md`
- `docs/audit/modular-revalidation-v1.3/M05-glm/progress.md`
- `docs/audit/modular-revalidation-v1.3/M05-glm/summary.md`
- `docs/audit/modular-revalidation-v1.3/M05-glm/evidence/synthetic/*`
- `docs/audit/modular-revalidation-v1.3/M05-glm/evidence/real-data/*`
- `docs/audit/modular-revalidation-v1.3/M05-glm/evidence/property/*`
- `tests/audit_v1_3/m05_glm/audit_utils.py`
- `tests/audit_v1_3/m05_glm/test_m05_synthetic.py`
- `tests/audit_v1_3/m05_glm/test_m05_realdata.py`
- `tests/audit_v1_3/m05_glm/test_m05_property.py`
- `tests/audit_v1_3/m05_glm/repro_m05_glm_findings.py`
- `stata/cases/audit_v1_3_m05/*.do`
- `stata/output/audit_v1_3_m05/*.log`
