# Wave 3 最终返工：`PPMLHDFE` 的 z 推断与字段覆盖

## 基本信息

- 任务名称：Wave 3 最终返工：修正 `PPMLHDFE` 的 z 推断
- 所属命令族：`Binary / Count`
- 优先级：P0
- 执行人：Claude Code
- 审查人：Codex

## 背景

Wave 3 第二次返工后，`logit` / `probit` / `poisson` 的 `z` 推断已修复，`probit` 的 robust sandwich 也已修复，`PPMLHDFE` 的 `vce="ols"` 语义也已经收口。

但 `PPMLHDFE` 仍有最后一个阻塞问题：

- `p_value`
- `ci_low`
- `ci_high`

依然按 `t` 分布计算，而不是按与 Stata `ppmlhdfe` 一致的 `z` 分布计算。

## 必读文件

1. `workspace/current-task/review-wave-3-rework-codex.md`
2. `docs/research/ppmlhdfe.md`
3. `docs/tasks/wave-3-rework-inference-semantics.md`
4. `workspace/current-task/REPORT.md`

## 本轮目标

只做 `PPMLHDFE` 的推断分布收口，不做任何新功能扩展。

### A. 修正 `PPMLHDFE` 的推断分布

在 `src/statapy/estimators/ppmlhdfe.py` 中：

- 移除 `t` 分布推断
- 将 `p_value` 改为基于标准正态分布计算
- 将 `ci_low` / `ci_high` 改为基于标准正态分布计算

保持现有 schema 不变：

- `CoefficientRow.t_stat` 字段名可以继续保留
- 但其值实际是 `beta / se`，应按 `z` 统计量解释

### B. 补上 `PPMLHDFE` 字段级测试覆盖

必须为 `PPMLHDFE` 新增字段级断言，至少覆盖：

- `p_value`
- `ci_low`
- `ci_high`

建议在以下文件中补测试：

- `tests/golden/test_w3_ppmlhdfe_basic.py`
- `tests/golden/test_w3_ppmlhdfe_real_gravity.py`

测试要求：

- 用 Stata 返回的 `beta` 和 `se`，按正态分布反推期望值
- 与 Python 结果对象里的字段逐项比较

## 允许修改的文件

- `src/statapy/estimators/ppmlhdfe.py`
- `tests/golden/test_w3_ppmlhdfe_basic.py`
- `tests/golden/test_w3_ppmlhdfe_real_gravity.py`
- 必要时少量更新 `docs/research/ppmlhdfe.md`
- `workspace/current-task/REPORT.md`

## 禁止事项

- 不要扩展到 `nbreg`、`zip`、`zinb`
- 不要修改 `logit` / `probit` / `poisson` 已通过部分
- 不要扩展 `ppmlhdfe` 的新选项
- 不要把未验证字段写成“可接受差异”

## 强制验证命令

```bash
python -m pytest tests/golden/test_w3_ppmlhdfe_basic.py -v
python -m pytest tests/golden/test_w3_ppmlhdfe_real_gravity.py -v
python -m pytest tests/golden/test_w3_ppmlhdfe_cluster.py -v
python -m pytest tests -v
```

如果新增了新的 `PPMLHDFE` 测试文件，必须在报告中列出并实际运行。

## 回报要求

报告必须明确写清：

1. `PPMLHDFE` 的 `p_value` / `ci` 现在如何按 `z` 分布计算
2. 新增了哪些测试来覆盖之前遗漏的字段
3. 哪些字段是直接拿 Stata 的 `beta` / `se` 反推的
4. 全量测试结果

## 通过标准

只有同时满足以下条件，Codex 才会放行 Wave 3：

- `PPMLHDFE` 不再使用 `t` 分布进行推断
- `PPMLHDFE` 的 `p_value` / `ci_low` / `ci_high` 被黄金测试显式覆盖
- `python -m pytest tests -v` 全绿
- `REPORT.md` 不再过早宣称 Wave 3 完成
