# M08 RD 审查进度

## 审查基线

- 基线 commit: `2c7db1ca095e03d29c471e8d523fdaa943306174`
- 审查对象: `stataflow.RDRobust`, `stataflow.compat.stata.rdrobust`, `stataflow.compat.stata.rdplot`
- 约束: 未修改 `src/stataflow/` 产品代码

## 任务清单

- [x] 阅读 MASTER_AUDIT_BRIEF.md 与 M08 task_plan.md / test-design-register.md
- [x] 阅读现有 RD 源码与测试（仅用于覆盖地图）
- [x] 设计并登记 7 个 synthetic 双跑实验（S1–S7）
- [x] 设计并登记 2 个真实数据双跑实验（R1–R2）
- [x] 设计并登记 3 个 metamorphic/property tests（P1–P3）
- [x] 实现通用执行与日志解析工具 `m08_audit_utils.py`
- [x] 实现 synthetic 测试 `test_m08_synthetic.py`
- [x] 实现真实数据测试 `test_m08_realdata.py`
- [x] 实现 property 测试 `test_m08_property.py`
- [x] 构造最小复现脚本 `repro_m08_rd_findings.py`
- [x] 字段级比较并记录差异
- [x] 修复测试脚本中的 Stata 命令构造问题（`c()` 与 `vce(cluster var)` 语法）
- [x] 更新 findings.md / summary.md / progress.md / test-design-register.md
- [x] 运行 M08 测试并报告 pass/xfail/fail
- [x] 运行全量非 golden 测试确认无回归

## 测试结果

### M08 专用测试

```bash
pytest tests/audit_v1_3/m08_rd -v
```

结果: **13 passed, 1 xfailed, 14 total**

| 测试 | 结果 | 备注 |
|------|------|------|
| S1 hand-checkable small sample | PASS | conventional 字段级对齐；Stata bc/rb 缺失（M08-RD-002） |
| S2 standard sharp RD | PASS | mserd 字段级对齐 |
| S3 covariate-adjusted | PASS | covs="z" 字段级对齐 |
| S4 cluster VCE | PASS | vce="cluster" 字段级对齐 |
| S5A explicit asymmetric h | PASS | h=(0.9,1.3) 精确匹配 |
| S5B certwo selector | XFAIL | M08-RD-001：非对称密度下 h_r/b_r ~0.3% 残余 |
| S6 numerical stress | PASS | 极端尺度 + 稀疏 cutoff 数据字段级对齐 |
| S7 rdplot esmv / qsmv | PASS | bin 数与 Stata 一致 |
| R1 Senate cersum+covs+hc0 | PASS | 字段级对齐 |
| R2 Senate swapped axes + msetwo | PASS | 字段级对齐 |
| P1 row-order invariance | PASS | Python 内部 + Stata 双跑通过 |
| P2 irrelevant-column invariance | PASS | Python 内部 + Stata 双跑通过 |
| P3 outcome scaling | PASS | Python 内部 + Stata 双跑通过 |

### 全量非 golden 回归测试

已执行:
```bash
pytest tests/ --ignore=tests/golden/ --ignore=tests/benchmarks/ -q
```

结果: **401 passed, 5 failed, 4 xfailed, 61 warnings in 250.10s**

- 失败全部集中在已有的 M06 PPMLHDFE 审查模块（5 项），与 M08 无关。
- M08 审查模块新增的 14 项测试未引入任何非 M08 失败。

## Confirmed Findings

| ID | Severity | API | 状态 | 关键差异 |
|----|----------|-----|------|----------|
| M08-RD-001 | P2 | RDRobust(rdrobust) | Confirmed-Stata | certwo/msetwo 在非对称密度下 h_r/b_r ~0.3% 残余，N_h_r 差 1 |
| M08-RD-002 | P2 | RDRobust(rdrobust) | Confirmed-Stata | 小有效样本下 Stata 抑制 bc/rb 输出，Python 仍返回有限值 |

## 证据资产

- `docs/audit/modular-revalidation-v1.3/M08-rd/evidence/synthetic/S{1-7}_*/`
- `docs/audit/modular-revalidation-v1.3/M08-rd/evidence/real-data/R{1-2}_*/`
- `docs/audit/modular-revalidation-v1.3/M08-rd/evidence/property/P{1-3}_*/`
- `stata/cases/audit_v1_3_m08/*.dta`
- `stata/output/audit_v1_3_m08/*.log`

## 未决事项

1. M08-RD-001 的精确来源（msetwo 右侧独立 MSE 迭代中的边界/数值差异）需进一步与 rdrobust 参考实现比对。
2. M08-RD-002 的低有效样本 guardrails 是否应在产品代码中实现，需 Codex/维护者裁定。
3. 本轮未覆盖 fuzzy RD、weights、masspoints 的独立真实数据双跑；这些已在 `tests/test_rdrobust.py` 中有合成测试，但 v1.3 真实数据证据不足。
4. `rdplot` 的协变量调整与多项式拟合 y 值未做字段级双跑。

## 是否需 Codex 裁定

- **建议裁定**: M08-RD-001 的 ~0.3% 带宽残余在非对称设计下是否可接受为已知局限。
- **建议裁定**: M08-RD-002 中 Python 是否应复制 Stata 的低有效样本抑制行为。
