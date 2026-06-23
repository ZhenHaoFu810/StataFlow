# M07 DID / Event Study 模块独立审查计划

## 审查基线

- 项目根目录：`D:/OneDrive - SAIF/PhD3/StataFlow`
- 基线分支：`dev`
- 基线 commit：`2c7db1ca095e03d29c471e8d523fdaa943306174`
- Python 3.11.7，NumPy 1.26.4，pandas 3.0.2，SciPy 1.17.1，statsmodels 0.14.6
- Stata 17 MP：`D:\Software\Stata17\StataMP-64.exe`
- 审查遵循：`docs/audit/modular-revalidation-v1.3/MASTER_AUDIT_BRIEF.md`
- 本轮禁止修改 `src/stataflow/` 产品代码

## 审查对象

- 核心估计器：
  - `stataflow.DIDImputation`
  - `stataflow.EventStudyInteract`
  - `stataflow.CSDID`
- Stata 兼容层：`stataflow.compat.stata.did_imputation`、`eventstudyinteract`、`csdid`
- 共享基础设施：`ResultSchema`、sample mask、cluster VCE、factor variables

## 关键风险领域

1. **first_treat 语义**：零/负/缺失值的处理；与 Stata 命令一致。
2. **sample mask / nobs**：autosample、缺失值、控制组缺失后 `len(sample_mask) == n_input_rows` 且 `sum == nobs`。
3. **allhorizons / window / minn**：地平线命名、筛选、遗漏。
4. **controls / unitcontrols / timecontrols / pretrends**：协变量与 pretrend F 检验。
5. **cluster-robust SE**：默认 cluster=id、自定义 cluster、cluster_count、df_resid。
6. **CSDID 聚合**：event/simple/group/calendar/pretrend 返回值、notyet 控制组。
7. **EventStudyInteract**：cohort shares、交互回归、IW 系数与方差。

## 审查任务清单

- [ ] 支持边界核对与代码走查
- [ ] 设计并登记 6+ 个新 synthetic 双跑实验
- [ ] 设计并登记 2 个新真实数据双跑实验
- [ ] 设计并登记 3 个 metamorphic/property tests
- [ ] 实现通用执行与日志解析工具 `tests/audit_v1_3/m07_did_event_study/m07_audit_utils.py`
- [ ] 实现 synthetic 测试 `test_m07_synthetic.py`
- [ ] 实现真实数据测试 `test_m07_realdata.py`
- [ ] 实现 property 测试 `test_m07_property.py`
- [ ] 构造最小复现脚本 `repro_m07_did_findings.py`
- [ ] 字段级比较并记录差异
- [ ] 撰写 `findings.md`、`progress.md`、`summary.md`、`test-design-register.md`
- [ ] 运行现有非 golden 测试，确认审查资产未破坏仓库

## 预期交付物

```text
docs/audit/modular-revalidation-v1.3/M07-did-event-study/
  task_plan.md
  test-design-register.md
  findings.md
  progress.md
  summary.md
  evidence/
    synthetic/
    real-data/
    property/
    minimal-reproductions/

tests/audit_v1_3/m07_did_event_study/
  m07_audit_utils.py
  test_m07_synthetic.py
  test_m07_realdata.py
  test_m07_property.py
  repro_m07_did_findings.py

stata/cases/audit_v1_3_m07/
  *.do
  *.csv

stata/output/audit_v1_3_m07/
  *.log
  *_diff.json
```
