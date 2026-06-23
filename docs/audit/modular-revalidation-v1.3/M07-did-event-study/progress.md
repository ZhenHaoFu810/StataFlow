# M07 DID / Event Study 审查进度

## 审查基线

- 基线 commit: `2c7db1ca095e03d29c471e8d523fdaa943306174`
- 审查对象: `stataflow.DIDImputation`, `stataflow.EventStudyInteract`, `stataflow.CSDID` 及其 Stata 兼容层
- 约束: 未修改 `src/stataflow/` 产品代码

## 任务清单

- [x] 阅读 MASTER_AUDIT_BRIEF.md 与 M07 task_plan.md / test-design-register.md
- [x] 阅读现有 golden 测试（仅用于覆盖地图，未复用 DGP/seed/expected）
- [x] 阅读 DIDImputation / CSDID / EventStudyInteract 源码（只读）
- [x] 设计并登记 8 个 synthetic 双跑实验（S1-S8）
- [x] 设计并登记 2 个真实数据双跑实验（R1-R2）
- [x] 设计并登记 3 个 metamorphic/property tests（P1-P3）
- [x] 实现通用执行与日志解析工具 `m07_audit_utils.py`
- [x] 实现 synthetic 测试 `test_m07_synthetic.py`
- [x] 实现真实数据测试 `test_m07_realdata.py`
- [x] 实现 property 测试 `test_m07_property.py`
- [x] 构造最小复现脚本 `repro_m07_did_findings.py`
- [x] 字段级比较并记录差异
- [x] root-agent 现场复核：重新运行测试、定位原始失败的根因、修正测试 DGP 与容差
- [x] 更新 findings.md / summary.md / progress.md / test-design-register.md
- [x] 更新 `workspace/current-task/REPORT.md` 中的 M07 追加报告
- [x] 运行 M07 测试并报告 pass/xfail/fail
- [x] 运行全量非 golden 测试确认无回归

## 测试结果

### M07 专用测试

```bash
pytest tests/audit_v1_3/m07_did_event_study -v
```

结果: **10 passed, 3 xfailed, 13 total**

| 测试 | 结果 | 备注 |
|------|------|------|
| S1 DID imputation basic | PASS | 无 never-treated DGP；系数 <1e-7，SE <2% |
| S2 DID imputation allhorizons | PASS | 使用末期之后 cohort 作为伪 never-treated 控制组 |
| S3 DID imputation controls+pretrends | PASS | 无 never-treated DGP；系数/SE 对齐 |
| S4 CSDID reg event | PASS | 字段级对齐 |
| S5 CSDID notyet (无 never-treated) | PASS | 字段级对齐 |
| S6 EventStudyInteract | PASS | 系数 <1e-7，SE 残余 <2% |
| S7 first_treat semantics | XFAIL | M07-DID-001/004：0/负/缺失编码与 Stata 冲突 |
| S8 custom cluster | PASS | 无 never-treated DGP；系数/SE 对齐 |
| R1 ezunem DID imputation controls | XFAIL | M07-DID-001：Python 删除 Stata 的 never-treated（缺失）行 |
| R2 ezunem CSDID notyet | XFAIL | M07-DID-003：notyet 控制组定义与 Stata 不一致 |
| P1 row-order invariance | PASS | Python 内部 + Stata 双跑均通过 |
| P2 irrelevant-column invariance | PASS | Python 内部 + Stata 双跑均通过 |
| P3 outcome scaling | PASS | Python 内部 + Stata 双跑均通过 |

### 全量非 golden 回归测试

已执行:
```bash
pytest tests/ -v --ignore=tests/golden/ --ignore=tests/benchmarks/
```

结果: **388 passed, 5 failed, 3 xfailed, 59 warnings in 258.88s**

- 失败全部集中在既有的 M06 PPMLHDFE 审查模块（5 项）。
- M07 审查模块的 3 项 xfail 已对应记录 finding（M07-DID-001/003/004）。
- 既有非审查测试（包括 DID/GLM/Linear/HDFE/IV/RD/Postestimation 等）未出现回归。

## Confirmed Findings

| ID | Severity | API | 状态 | 关键差异 |
|----|----------|-----|------|----------|
| M07-DID-001 | P1 | DIDImputation | Confirmed-Stata | `first_treat` 缺失行被 Python 删除，Stata 将其作为 never-treated 控制组 |
| M07-DID-002 | P1 | DIDImputation | Confirmed-Stata（测试设计问题） | 原始失败由编码不一致导致；语义一致后核心算法对齐 |
| M07-DID-003 | P0 | CSDID(notyet) | Confirmed-Stata | notyet 控制组应包含 never-treated + not-yet-treated |
| M07-DID-004 | P1 | DIDImputation | Confirmed-Stata | `first_treat` 0/负值语义与 Stata 冲突 |
| M07-DID-005 | P3 | EventStudyInteract | Confirmed-Stata | SE 残余 ~0.5–1.5% |
| M07-DID-006 | P2 | Stata ado | Confirmed-Stata | `window()` 选项不被当前 ado 支持 |

## 证据资产

- `docs/audit/modular-revalidation-v1.3/M07-did-event-study/evidence/synthetic/S{1-8}_*/`
- `docs/audit/modular-revalidation-v1.3/M07-did-event-study/evidence/real-data/R{1-2}_*/`
- `docs/audit/modular-revalidation-v1.3/M07-did-event-study/evidence/property/P{1-3}_*/`
- `docs/audit/modular-revalidation-v1.3/M07-did-event-study/evidence/minimal-reproductions/` (via `repro_m07_did_findings.py`)
- `stata/cases/audit_v1_3_m07/*.dta`
- `stata/output/audit_v1_3_m07/*.log`

## 未决事项

1. DIDImputation 的 `first_treat` 编码约定需要在产品代码中修复，并重新验证 R1/S7。
2. CSDID `notyet=True` 控制组选择算法需复核并修复，重新验证 R2。
3. EventStudyInteract SE 残余的精确来源尚未定位。
4. `did_imputation` ado 版本差异（`window()` 支持）需在支持矩阵中说明。

## 是否需 Codex 裁定

- **建议裁定**: M07-DID-001/004 的修复策略（是否在 `DIDImputation` 中统一采用 Stata 的“缺失 = never-treated”约定，并如何处理 0/负值）。
- **建议裁定**: M07-DID-003 中 CSDID `notyet` 的算法设计（是否采用 Stata 的“never-treated + not-yet-treated”混合控制组）。
- **建议裁定**: M07-DID-005 的 SE 残余是否可接受为已知局限。
