# M08 RD 模块独立审查总结

## 审查目标

对 `stataflow.RDRobust`、`stataflow.compat.stata.rdrobust()`、`stataflow.compat.stata.rdplot()` 进行独立、不依赖旧 golden 的双跑审查。本轮禁止修改 `src/stataflow/` 产品代码，仅创建测试、证据与文档。

## 审查范围与资产

- **新建 synthetic 双跑**: 7 个（S1–S7）
- **新建真实数据双跑**: 2 个（R1–R2）
- **新建 property tests**: 3 个（P1–P3）
- **最小复现脚本**: `tests/audit_v1_3/m08_rd/repro_m08_rd_findings.py`
- **通用工具**: `tests/audit_v1_3/m08_rd/m08_audit_utils.py`
- **文档**: `task_plan.md`、`findings.md`、`progress.md`、`test-design-register.md`

## 关键结论

### 1. 核心 sharp RD 路径在常规场景下与 Stata 17 字段级对齐

在标准同质处理效应（S2）、协变量调整（S3）、cluster-robust VCE（S4）、用户指定非对称带宽（S5A）、真实数据 CER-SUM 与交换轴设计（R1/R2）中，Python 与 Stata 的系数、标准误、样本数、带宽等核心字段均达到默认或记录放宽后的容差。

### 2. `certwo` / `msetwo` 在非对称密度下存在约 0.3% 的带宽残余（M08-RD-001）

S5B 使用左侧密度 65%、右侧 35% 的设计，`certwo` 右侧带宽 Python=0.4638 vs Stata=0.4626，差异约 0.26%；有效观测数相差 1 个。常规点估计与 SE 仍高度一致，差异集中在左右独立 MSE 带宽选择器的数值路径。

### 3. 小有效样本下 Stata 抑制稳健推断，Python 仍返回有限值（M08-RD-002）

S1 的手工可计算小样本（每侧有效观测 5–6）中，Stata 的 `e(b)` / `e(V)` 中 bias-corrected 与 robust 元素为缺失值，并发出低有效样本警告；Python 实现仍返回有限 `tau_bc` / `tau_rb`。这是 Python 缺少 Stata 式可靠性 guardrails 的表现。

### 4. `rdplot` 自动 bin 选择基本对齐

S7 的 `esmv` 与 `qsmv` bin 数量与 Stata 一致，说明 `RDPlot` 的 IMSE-optimal bin selection 实现基本正确。

### 5. Python 内部性质稳定

行顺序不变性、无关列不变性、结果变量缩放不变性在 Python 内部均保持，且与 Stata 双跑一致。

## 审查完成度

- [x] 7 synthetic 双跑（含 1 项 xfail 的 S5B）
- [x] 2 真实数据双跑（R1/R2 均通过）
- [x] 3 property tests（P1–P3 全部通过）
- [x] 2 confirmed findings（均为 P2）
- [x] 全部证据已保存并可复跑
- [x] 全量非 golden 回归测试已执行，M08 未引入新失败
- [x] `workspace/current-task/REPORT.md` 追加 M08 报告

## 风险与限制

- M08-RD-001 的 0.3% 残余是否可接受需 Codex 裁定；当前已用 xfail 记录证据。
- M08-RD-002 的低有效样本行为差异可能导致用户在极小样本下得到与 Stata 不同的输出结构。
- 本轮未对 fuzzy RD、weights、masspoints 的真实数据场景做独立双跑，建议在修复 M08-RD-001/002 后补充。
- `rdplot` 的协变量调整与拟合线 y 值未做字段级双跑。

## 建议后续行动

1. **评估 M08-RD-001**: 比对新版 rdrobust 参考实现中 `_three_step_bw_two` 的边界处理，决定是提高数值精度还是文档化为已知残余。
2. **修复 M08-RD-002**: 增加低有效样本检查，使 Python 在样本不足时返回 `NaN` 或发出明确警告。
3. **补充证据**: 在 fuzzy RD、weights、masspoints 真实数据上增加独立双跑。
4. **完善 rdplot**: 对 `rdplot` 的拟合值和 bin 统计量做字段级双跑。
