# M10 Shared Infrastructure Findings

## M10-FACTOR-001：因子变量基期项未进入 ResultSchema

- **Severity**: P2
- **Evidence status**: Confirmed-Stata
- **Affected API**: 所有使用因子变量的 compat wrapper（`regress`, `areg`, `xtreg_fe`, `ivregress_2sls`, `reghdfe`, `ppmlhdfe`, `poisson` 等）以及 `expand_factor_terms` / `ResultSchema.coefficients`。
- **最小复现**:
  1. 运行 `M10-S01` 或 `M10-R01`。
  2. Stata `e(b)` 包含 `0b.g`、`0b.democA` 等基期项（系数为 0）。
  3. Python `ResultSchema.coefficients` 仅包含非基期项，基期项被完全省略。
- **Stata 17 结果示例**:
  ```
  coef_names/order: Python=['1.democA', 'lexpendA', '1.democA#c.lexpendA', '_cons'],
  Stata(active)=['1.democA', 'lexpendA', '1.democA#c.lexpendA', '_cons']
  ```
  完整 Stata `e(b)` 为 `['0b.democA', '1.democA', 'lexpendA', '0b.democA#co.lexpendA', '1.democA#c.lexpendA', '_cons']`。
- **Python 结果**: 见 `evidence/synthetic/M10-S01.json` 与 `evidence/real-data/M10-R01.json`。
- **根因分析**: `factor_variables.py` 在生成虚拟变量时直接跳过基期水平，导致其永远不会出现在设计矩阵中；`ResultSchema` 因此也没有对应的系数行。Stata 则保留基期行以维持 `e(b)` 与因子水平之间的一一映射。
- **用户影响**: 依赖 `e(b)` 长度等于因子水平数的下游工具、 margins 或结果对比脚本可能出现维度不匹配；但从估计参数角度看，非基期系数与 VCE 是正确的。
- **受影响范围**: 全部支持因子变量的命令。
- **是否共享基础设施问题**: 是。
- **当前旧 issue**: 未发现专门记录该差异的旧 issue。
- **建议修复方向**: 在 `ResultSchema` 中可选地保留基期系数行（值为 0，SE 为 0/NaN），或至少在文档中明确说明 Python 不返回基期项。

## M10-RUNNER-001：StataRunner 对 Stata 运行时错误返回 exit_code 0

- **Severity**: P2
- **Evidence status**: Confirmed-Code
- **Affected API**: `StataRunner.run_do_file`。
- **最小复现**:
  1. 构造包含 `regress y nonexistent_var` 的 `.do` 文件。
  2. 调用 `StataRunner().run_do_file(...)`。
  3. 返回 `exit_code == 0`，错误仅在 log 中以 `r(111)` / `not found` 形式出现。
- **Stata 17 结果**: `end of do-file\nr(111);`
- **Python 结果**: `StataResult(exit_code=0, ...)`，log 包含错误文本。
- **根因分析**: Stata `/e do` 批处理模式对运行时错误不设置非零进程退出码；`StataRunner` 仅透传 `subprocess.run` 的返回码，未解析 log 做错误判断。
- **用户影响**: 调用方若仅检查 `exit_code` 会误判脚本成功；测试中需要额外解析 log 来确认错误。
- **受影响范围**: 所有依赖 `StataRunner` 的 dual-run 测试与工具脚本。
- **是否共享基础设施问题**: 是。
- **当前旧 issue**: 未发现。
- **建议修复方向**: 在 `StataRunner` 中增加可选的 log 错误扫描（例如 `r(` 返回码、`not found`、`last error`），并提供 `raise_on_error` 开关；或至少文档化“需自行检查 log”。

## 已验证通过项（不构成 finding）

- Robust VCE 完整矩阵与 Stata 一致（M10-S02）。
- Cluster VCE 在含 singleton cluster 时 n_clust、df_resid、系数、VCE 与 Stata 一致（M10-S03）。
- 缺失值筛选后的 sample mask 与 Stata `e(sample)` 逐行一致（M10-S04、M10-R02）。
- 完全共线性设计下 Python 与 Stata 均正确删除冗余列并保持估计一致（M10-S06）。
- 常数项模型 ResultSchema 有效且与 Stata 一致（M10-S07）。
- 行顺序、无关列、聚类标签置换三类不变性均成立（M10-P01–P03）。
