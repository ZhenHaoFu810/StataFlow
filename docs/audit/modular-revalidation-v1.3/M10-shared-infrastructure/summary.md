# M10 Shared Infrastructure 审查总结

## 基线与范围

- 基线 commit：`2c7db1ca095e03d29c471e8d523fdaa943306174`
- 审查对象：`factor_variables.py`、`_vce_utils.py`、`result.py`、`stata_runner/runner.py`、sample mask 机制。
- 方法：以 `regress()` 为调用入口，对共享组件进行字段级 Stata 17 双跑；同时执行不变性 property tests。

## 证据概览

- Synthetic 双跑：7 项（M10-S01–S07），全部通过。
- 真实数据双跑：2 项（M10-R01–R02），全部通过。
- Property tests：3 项（M10-P01–P03），全部通过。
- 总新增可执行测试：13 个，位于 `tests/audit_v1_3/m10_shared_infrastructure/`。

## 通过项

- Robust VCE 矩阵与 Stata 一致。
- Cluster VCE 在含 singleton 场景下 n_clust、df、系数、VCE 与 Stata 一致。
- 缺失值 sample mask 与 Stata `e(sample)` 逐行一致。
- 完全共线性、常数项模型等退化场景处理正确。
- 行顺序、无关列、聚类标签置换三类不变性成立。

## 发现的问题

| ID | Severity | 问题 | 证据状态 |
|---|---|---|---|
| M10-FACTOR-001 | P2 | Python 因子变量结果省略 Stata 中的基期/省略系数行（如 `0b.g`），导致 `ResultSchema.coefficients` 维度与 Stata `e(b)` 不完全一致。 | Confirmed-Stata |
| M10-RUNNER-001 | P2 | `StataRunner.run_do_file` 在 Stata 运行时错误（如 `r(111)`）时仍返回 `exit_code=0`，错误信息仅存在于 log 中。 | Confirmed-Code |

## 结论

M10 共享基础设施在核心数学路径（VCE、sample mask、共线性、常数项模型）上与 Stata 17 一致。发现的两个问题均为 API/工具层差异，不影响估计参数的数值正确性，但需要在文档或 runner 错误处理中明确说明。

## 未覆盖区域

- 多向 cluster VCE 的独立 synthetic 验证（已在 M03/M04/M06 中覆盖）。
- `fix_psd_reghdfe` 与 Stata 的逐项 PSD 修正对比（已在 M03/M06 中覆盖）。
- StataRunner 在高并发/多进程场景下的稳定性压力测试。
