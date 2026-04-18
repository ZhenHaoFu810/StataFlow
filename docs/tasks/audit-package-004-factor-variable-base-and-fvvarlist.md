# 审计后任务包 004：因子变量 Phase C 与 base-level / omitted-level 语义

## 1. 任务背景

任务包 002 与 003 已经把以下高频 factor 语义接入 wrapper 层：

- `c.x1#c.x2`
- `c.x1##c.x2`
- `i.g1#i.g2`
- `i.g1##i.g2`
- `i.g1#c.x1`
- `i.g1##c.x1`
- `c.x1##i.g1`
- `x1##x2`
- `x1##i.g`

这已经足以覆盖大量常见实证回归写法，但当前 factor grammar 仍有一个很明显的下一阶段缺口：

- `ib#.` / `b.` / `o.` 的 base-level / omitted-level 语义仍未实现

这意味着用户还不能更精确地控制：

- 哪个分类水平作为基准组
- 哪些水平被显式省略
- 某些 Stata `fvvarlist` 结果列名与对照逻辑

如果项目要继续逼近“Stata 常用命令真实迁移体验”，这一层不能长期缺失。

## 2. 总目标

本轮把 factor grammar 从当前 Phase B 再推进一步，重点实现：

- `ib#.` / `b.` / `o.` 的最小可用语义
- 更明确的 base/omitted level 列命名与结果对象行为
- 在 `regress`、`reghdfe`、至少一个非线性命令中完成 dual-run 证据

本轮仍然不追求完整 `fvvarlist` 终态，但要把 **最核心的基准组/省略组控制语义** 做出来。

## 3. 必须完成的内容

### A. parser 支持 base / omitted level 语法

扩展 `src/statapy/compat/stata/factor_variables.py`，至少支持：

- `ib2.g`
- `ib3.g`
- `b2.g`
- `o2.g`

需要明确：

- `ib2.g` / `b2.g` 如何指定基准组
- `o2.g` 如何指定额外省略水平
- 如果指定的 level 不存在，必须报明确错误

### B. 与现有 `i.g` 语义整合

要求：

- `i.g` 仍默认取第一排序水平为基准组
- `ib#.g` / `b#.g` 会覆盖默认基准组
- `o#.g` 在生成项时正确省略对应水平
- 结果列名保持 Stata 风格

### C. 接入高频 wrapper 命令

至少接入：

- `regress`
- `reghdfe`
- `ivreghdfe`
- `logit` 或 `poisson`

### D. 更新研究与支持矩阵

至少更新：

- `docs/research/factor-variable-semantics.md`
- `docs/command-support-matrix/regress.md`
- `docs/command-support-matrix/reghdfe.md`
- `docs/command-support-matrix/ivreghdfe.md`
- `docs/command-support-matrix/logit.md` 或 `poisson.md`
- `README.md`（如有必要）

文档必须明确区分：

- 已支持：`i.`、`ib#.`、`b#.`、`o#.`
- 仍未支持：更复杂 `fvvarlist` 变体、时间序列算子、三阶交互

## 4. 测试要求

### A. 单元测试

新增或扩展 `tests/test_factor_variables.py`，至少覆盖：

- `i.g` 默认基准组行为
- `ib2.g` 覆盖默认基准组
- `b2.g` 与 `ib2.g` 等价
- `o2.g` 正确省略水平
- 不存在 level 时明确报错

### B. 手工展开等价测试

至少覆盖：

- `regress(..., x=["ib2.g##c.x1"])` 与手工 dummy/interaction 展开一致
- `reghdfe(..., x=["ib2.g##c.x1"], absorb=...)` 与手工展开一致

### C. Stata dual-run

至少新增并通过：

- `regress y ib2.g##c.x1`
- `reghdfe y ib2.g##c.x1, absorb(firm year)`
- 一个非线性命令的 `ib#.` / `b#.` case

### D. 全量验证

完成后至少回报：

```powershell
python -m pytest tests/test_factor_variables.py -v
python -m pytest tests/test_compat_stata_linear.py tests/test_compat_stata_hdfe.py tests/test_compat_stata_iv.py tests/test_compat_stata_glm.py -v
python -m pytest tests -v
```

## 5. 禁止事项

本轮不要顺手做：

- 时间序列 factor 语法
- 三阶及以上交互
- 全量 `fvvarlist` 终态
- 与 factor grammar 无关的其他算法扩展

## 6. 完成标准

本轮通过的最低标准：

- `ib#.` / `b#.` / `o#.` 的最小语义已进入 wrapper 层
- `regress` / `reghdfe` / 至少一个非线性命令具备 dual-run 证据
- 文档、支持矩阵、测试、报告同步一致

如果 Claude Code 在报告里把本轮夸大成“完整 factor-variable grammar 已完成”，视为未完成。
