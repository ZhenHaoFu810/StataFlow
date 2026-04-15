# Wave 5 Final Rework: margins 常数项语义对齐

## 基本信息

- 任务名称：Wave 5 最终返工
- 执行人：Claude Code
- 审查人：Codex

## 目标

修正 `margins` 结果对象的变量集合语义，使其与 Stata 对齐：`_cons` 不能再作为边际效应变量返回。

## 本轮只做什么

- 只修 `margins()` 的返回结果语义
- 只改相关 golden tests、报告和状态文件

## 本轮明确不做什么

- 不改 `predict()`
- 不推进到下一个 wave
- 不扩展 `marginsplot`
- 不引入新的 postestimation 功能

## 任务要求

1. 修正 `OLS`、`FixedEffectsOLS`、`AbsorbingOLS`、`Logit`、`Probit`、`Poisson`、`PPMLHDFE` 的 `margins()` 结果，使其只返回真正的解释变量，不返回 `_cons`。
2. 更新 Wave 5 golden tests，显式断言 `_cons` 不出现在 `margins` 结果中。
3. 如果某个模型需要保留内部常数项参与 Jacobian 计算，可以保留内部计算，但最终对外结果必须去掉 `_cons`。
4. 更新 `workspace/current-task/REPORT.md`。

## 强制验证命令

```powershell
python -m pytest tests/golden/test_w5_margins_logit_basic.py -v
python -m pytest tests/golden/test_w5_margins_real_mroz.py -v
python -m pytest tests/golden/test_w5_margins_real_crime1.py -v
python -m pytest tests -v
```

## 通过标准

只有同时满足以下条件，Codex 才会放行整个 Wave 5：

1. 所有 `margins` 结果对象都不再包含 `_cons`。
2. Wave 5 `margins` golden tests 显式覆盖这一点。
3. 全量测试通过。
4. 报告不再夸大完成状态。
