# 审计后任务包 005：Factor Variable Phase D 与更完整 `fvvarlist` 子集

## 1. 任务背景

任务包 002 到 004 已经把以下高频 factor 语义接入 wrapper 层：

- `c.x1#c.x2`
- `c.x1##c.x2`
- `i.g1#i.g2`
- `i.g1##i.g2`
- `i.g1#c.x1`
- `i.g1##c.x1`
- `c.x1##i.g1`
- `x1##x2`
- `x1##i.g`
- `ib#.` / `b#.` / `o#.` 的最小 base-level / omitted-level 语义

这一层已经覆盖了大量常见回归写法，但仍然与 Stata 真实 `fvvarlist` 使用体验有明显差距，尤其是：

- 三阶 `##` 的常见全因子展开
- `c.(x1 x2)`、`i.(g1 g2)` 这类括号缩写
- 上述语义在 `reghdfe`、`ivreghdfe`、非线性命令中的一致证据

如果项目要继续向“Stata 常用命令可直接迁移”推进，这一层不能长期缺失。

## 2. 总目标

本轮把 factor grammar 从当前 Phase C 再推进一步，形成一个更接近 Stata 常用 `fvvarlist` 的 **Phase D 子集**。

本轮至少实现：

- 限定范围内的三阶 `##`
- 限定范围内的括号缩写
- 在核心 wrapper 命令中的真实可用性
- 手工展开等价测试与 Stata dual-run 证据

本轮仍然不追求完整 Stata `fvvarlist` 终态，但必须把这几个高价值缺口做出来。

## 3. 必须完成的内容

### A. 支持有限范围内的三阶 `##`

扩展 `src/statapy/compat/stata/factor_variables.py`，至少支持：

- `x1##x2##x3`
- `i.g##c.x1##c.x2`
- `i.g1##i.g2##c.x1`

语义要求：

- `##` 必须做完整 factorial expansion
- 展开结果要与 Stata 一致地包含：
  - 主效应
  - 二阶交互
  - 三阶交互
- 裸变量仍默认按连续变量 `c.` 解释

本轮不要求支持任意更高阶交互；四阶及以上必须继续明确拒绝。

### B. 支持有限范围内的括号缩写

至少支持：

- `c.(x1 x2)`
- `i.(g1 g2)`
- `c.(x1 x2)##i.g`
- `i.(g1 g2)##c.x1`

语义要求：

- 括号缩写要在 wrapper 层先展开，再走现有 factor parser
- 展开结果必须与手工写出的等价式一致
- 不允许 silent ignore

### C. 接到高频 wrapper 命令

至少接到：

- `regress`
- `reghdfe`
- `ivreghdfe`
- `logit` 或 `poisson`

并验证：

- `reghdfe(..., absorb="firm year")` 与 factor expansion 共存
- 主效应可被 absorb 掉时，仍保留有 variation 的交互项

### D. 更新研究文档与支持矩阵

至少更新：

- `docs/research/factor-variable-semantics.md`
- `docs/command-support-matrix/regress.md`
- `docs/command-support-matrix/reghdfe.md`
- `docs/command-support-matrix/ivreghdfe.md`
- `docs/command-support-matrix/logit.md` 或 `poisson.md`

必须明确区分：

- 本轮新支持的三阶 / 括号缩写语义
- 继续未支持的语法
- 明确拒绝规则

## 4. 测试要求

### A. 单元测试

扩展 `tests/test_factor_variables.py`，至少覆盖：

- `x1##x2##x3` 展开结果
- `i.g##c.x1##c.x2` 展开结果
- `c.(x1 x2)` 与手工展开等价
- `i.(g1 g2)##c.x1` 与手工展开等价
- 四阶交互继续抛 `ValueError`
- 未支持的复杂括号组合继续抛 `ValueError`

### B. 手工展开等价测试

至少覆盖：

- `regress(..., x=["x1##x2##x3"])`
- `reghdfe(..., x=["i.g##c.x1##c.x2"], absorb="firm year")`
- `ivreghdfe(..., x=["i.(g1 g2)##c.x1"], absorb="firm year")`

### C. Stata dual-run

至少新增并通过：

- `regress y x1##x2##x3`
- `reghdfe y i.g##c.x1##c.x2, absorb(firm year)`
- 一个 `ivreghdfe` 或非线性命令的括号缩写 case

### D. 全量验证

完成后至少回报：

```powershell
python -m pytest tests/test_factor_variables.py -v
python -m pytest tests/test_compat_stata_linear.py tests/test_compat_stata_hdfe.py tests/test_compat_stata_iv.py tests/test_compat_stata_glm.py -v
python -m pytest tests -v
```

## 5. 禁止事项

本轮不要顺手做：

- 时间序列算子 `L.` / `F.` / `D.`
- 五阶及以上交互
- 全量 Stata `fvvarlist` 终态
- 与 factor grammar 无关的估计器扩展

## 6. 完成标准

本轮通过的最低标准：

- 三阶 `##` 的最小可用子集进入 wrapper 层
- 括号缩写的最小可用子集进入 wrapper 层
- `regress` / `reghdfe` / `ivreghdfe` / 至少一个非线性命令具备真实证据
- 文档、支持矩阵、测试、报告同步一致

如果 Claude Code 在报告中把本轮夸大成“完整 `fvvarlist` 已完成”，视为未完成。
