# Codex Review: Wave 3 Rework 仍未通过

## 结论

本轮 **不通过**，不能进入下一个 wave。

虽然 Claude Code 报告的 Wave 3 返工测试全部通过，而且我独立复跑 `python -m pytest tests -v` 也得到 `396 passed`，但 `PPMLHDFE` 仍然存在一个未修复的推断语义错误：`p_value` 和置信区间继续使用 `t` 分布，而不是与 Stata `ppmlhdfe` 一致的 `z` 分布。

这不是“展示层”问题，而是公开结果对象的数学口径错误。由于当前 golden tests 没有覆盖 `PPMLHDFE` 的 `p_value` / `ci_low` / `ci_high`，所以测试全绿并不能证明这部分已对齐。

## 独立复核证据

### 1. Claude Code 声称的测试结果

- `python -m pytest tests -v`
- 结果：`396 passed`

### 2. Codex 独立补充核验

我额外运行了一个直接检查 `PPMLHDFE` 推断分布的小脚本，结果如下：

- `reported_p = 2.848779692143921e-07`
- `z_p = 9.444265525182516e-08`
- `t_p = 2.848779692143921e-07`

这说明当前实现返回的 `p_value` 明确等于 `t` 分布结果，而不是 `z` 分布结果。

## 阻塞问题

### 1. `PPMLHDFE` 仍在使用 `t` 分布推断

- 文件：`src/statapy/estimators/ppmlhdfe.py`
- 问题：
  - 仍然 `import scipy.stats.t as t_dist`
  - `p_values` 用 `t_dist.cdf(...)`
  - `ci_low` / `ci_high` 用 `t_dist.ppf(...)`

这与 Poisson PML / `ppmlhdfe` 的 MLE 推断口径不一致。

### 2. 测试覆盖仍然缺失

当前新增的返工测试覆盖了：

- `logit/probit/poisson` 的 `z` 分布推断
- `probit` robust VCE
- `ppmlhdfe` 的 `vcetype` / `vce="ols"` 语义

但没有覆盖：

- `PPMLHDFE` 的 `p_value`
- `PPMLHDFE` 的 `ci_low`
- `PPMLHDFE` 的 `ci_high`

所以这一轮“测试全过”并不足以支撑 Wave 3 放行。

### 3. 报告结论仍然过早

- 文件：`workspace/current-task/REPORT.md`
- 问题：
  - 仍然把 Wave 3 返工写成“已完成”
  - 但核心推断字段仍未完全对齐

因此这份报告不能作为完成证据。

## 返工要求

Claude Code 下一轮只做一件事：

- 修正 `PPMLHDFE` 的 `p_value` / `ci_low` / `ci_high` 推断分布，使其与 Stata 的 `z` 口径一致

同时必须补上对应测试：

- `tests/golden/test_w3_ppmlhdfe_basic.py`
- `tests/golden/test_w3_ppmlhdfe_real_gravity.py`

至少要新增字段级断言，显式验证：

- `p_value`
- `ci_low`
- `ci_high`

## 当前状态

- Wave 3：**仍未完成**
- 下一个 wave：**不得开始**
- 本轮只允许做 `PPMLHDFE` 推断语义收口，不得扩展到新命令
