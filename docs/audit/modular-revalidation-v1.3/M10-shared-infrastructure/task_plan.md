# M10 Shared Infrastructure 审查计划

## 审查基线

- 分支/状态：当前工作目录未提交修改前的 `dev` 状态
- Git commit：`2c7db1ca095e03d29c471e8d523fdaa943306174`
- Python：3.11.7
- Stata：Stata/MP 17.0

## 审查范围

M10 聚焦被所有 estimator 共享、但自身不是单一命令的基础设施：

1. `src/stataflow/compat/stata/factor_variables.py` — Stata 风格因子变量解析与展开。
2. `src/stataflow/estimators/_vce_utils.py` — cluster-robust meat、多向 cluster、PSD 修正、共线性检测。
3. `src/stataflow/results/result.py` — `ResultSchema` 维度不变量与字段对齐。
4. `src/stataflow/stata_runner/runner.py` — 路径、日志、返回码、错误传播。
5. 各 estimator 中的 sample mask / 缺失值筛选 / 行映射一致性。

## 审查策略

- 不修改 `src/stataflow/` 产品代码。
- 通过线性回归 `regress()` 作为消费者调用共享组件，完成字段级双跑。
- 每个 synthetic 设计使用新的随机种子、DGP 和 Stata `.do` 脚本，不复制旧 golden 测试。
- 真实数据使用仓库已公开的 `vote1.csv` 与 `jtrain_prepared.dta`。
- property tests 同时检查 Python 不变量，并在可行时与 Stata 对照。

## 交付物

```text
docs/audit/modular-revalidation-v1.3/M10-shared-infrastructure/
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
tests/audit_v1_3/m10_shared_infrastructure/
  m10_audit_utils.py
  test_m10_synthetic.py
  test_m10_realdata.py
  test_m10_property.py
```

## 执行顺序

1. 阅读共享基础设施源码与现有测试。
2. 编写审计工具 `m10_audit_utils.py`（Stata 执行、日志解析、字段比较）。
3. 设计并执行 6+ synthetic 双跑。
4. 设计并执行 2 个真实数据实验。
5. 设计并执行 3 个 property tests。
6. 对异常构造最小复现并写入 findings。
7. 跑全非 golden 回归，确认没有新增失败。
8. 撰写 summary 并更新 REPORT.md。
