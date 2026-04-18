# 审计后任务包 003：因子变量 Phase B 与 HDFE / IV / Count 命令语义收口

## 1. 任务背景

任务包 002 已把 Stata 因子变量的第一阶段高频子集接入 wrapper 层，当前已支持：

- `c.x1#c.x2`
- `c.x1##c.x2`
- `i.g1#i.g2`
- `i.g1##i.g2`
- `i.g1#c.x1`
- `i.g1##c.x1`
- `absorb="firm year"` 这类 Stata 风格写法

但它仍然只是 **Phase A 子集**，还没有把命令层语义真正做稳做全。当前最危险的缺口有三类：

1. **混合因子项的顺序对称性缺失**
   - 现在支持 `i.g1##c.x1`
   - 但 `c.x1##i.g1`、`c.x1#i.g1` 这类等价写法并未系统支持
2. **HDFE / IV / PPML 下的 factor 语义覆盖还偏薄**
   - 真实使用中，factor 语法与 `reghdfe`、`ivreghdfe`、`ppmlhdfe` 往往同时出现
   - 目前 dual-run 证据主要集中在线性/HDFE/logit 的最小样例
3. **错误语义与边界说明仍需进一步产品化**
   - 对不支持的 factor 写法，当前虽然已有 `ValueError`
   - 但还不够系统，不足以支撑“开源给外部用户直接用”的稳定命令层体验

## 2. 总目标

本轮要把 factor-variable 语义从“Phase A 能跑”推进到“Phase B 可稳定使用”，重点收口：

- mixed interaction 的顺序对称性
- HDFE / IV / Count 系列命令中的 factor 语义
- 更严格的错误处理与支持矩阵说明

本轮仍然**不是**完整 Stata `fvvarlist` grammar 的最终版，但应该把目前最容易误伤用户的命令层缺口补掉。

## 3. 本轮必须完成的内容

### A. mixed interaction 顺序对称性

当前 `i.g1##c.x1` 已支持，本轮必须把以下写法做成与之语义等价：

- `c.x1#i.g1`
- `c.x1##i.g1`

要求：

- 设计矩阵展开结果与 `i.g1#c.x1` / `i.g1##c.x1` 等价
- 列名保持稳定并尽量贴近 Stata
- wrapper 层对两种写法都接受

### B. 明确裸变量与 factor-term 的边界

本轮必须对以下情形给出**显式、稳定、文档化**的行为：

- `x1#x2`
- `x1##x2`
- `x1#c.x2`
- `x1##i.g1`

可以接受两种策略中的任意一种，但必须统一且写清楚：

1. 明确支持，并给出确定的 Stata 语义映射
2. 明确拒绝，并要求用户显式写 `c.` / `i.`

禁止出现：

- 有时当普通变量，有时当 factor term
- 语义依赖样本 dtype 或偶然数据值
- 文档没写清、错误信息也不清楚

### C. HDFE / IV / Count 命令的 factor 语义收口

本轮必须新增并通过以下命令层场景：

- `reghdfe y c.x1##i.g1, absorb(firm year)`
- `ivreghdfe y ...` 中至少一个 `x_exog` 或 `instruments` 含 factor term 的场景
- `ppmlhdfe y i.g1##c.x1, absorb(exporter importer)` 或同等 HDFE count 场景

要求：

- factor-term 真正进入 wrapper
- absorbed FE 与主效应 / 交互项的 collinearity 行为可解释
- 结果对象中的系数命名稳定

### D. 更新研究与支持矩阵

至少更新：

- `docs/research/factor-variable-semantics.md`
- `docs/command-support-matrix/reghdfe.md`
- `docs/command-support-matrix/ivreghdfe.md`
- `docs/command-support-matrix/ppmlhdfe.md`
- `docs/command-support-matrix/ivregress-2sls.md`
- 如有必要，`README.md`

必须把以下信息写清：

- mixed interaction 的顺序是否对称支持
- 裸变量参与 `#` / `##` 的处理策略
- 哪些命令已经有 factor dual-run 证据
- 哪些命令仍只有 unit / synthetic 证据

## 4. 测试要求

### A. 单元测试

新增或扩展 `tests/test_factor_variables.py`，至少覆盖：

- `c.x1#i.g1` 与 `i.g1#c.x1` 等价
- `c.x1##i.g1` 与 `i.g1##c.x1` 等价
- 裸变量参与 `#` / `##` 时的统一行为
- 不支持语法的错误信息稳定、明确

### B. 命令层等价测试

至少覆盖：

- `reghdfe` factor-term 与手工展开等价
- `ivreghdfe` factor-term 与手工展开等价
- `ppmlhdfe` 或 `poisson` factor-term 与手工展开等价

### C. Stata dual-run

本轮至少新增并通过：

- 一个 `reghdfe` mixed-order factor case
- 一个 `ivreghdfe` factor case
- 一个 `ppmlhdfe` factor case

### D. 全量验证

完成后至少回报：

```powershell
python -m pytest tests/test_factor_variables.py -v
python -m pytest tests/test_hdfe_synthetic.py tests/test_compat_stata_iv.py tests/test_compat_stata_hdfe.py tests/test_compat_stata_glm.py -v
python -m pytest tests -v
```

## 5. 禁止事项

本轮不要顺手做：

- 完整 `ib#.` / `b.` / `o.` 全支持
- 时间序列 factor 语法
- 三阶及以上交互
- 全面重写 estimator 内核
- 与 factor grammar 无关的算法扩展

## 6. 完成标准

本轮通过的最低标准：

- mixed interaction 顺序对称性已经收口
- 裸变量参与 `#` / `##` 的策略已统一并文档化
- `reghdfe`、`ivreghdfe`、`ppmlhdfe` 至少各有一类 factor 语义证据
- 文档、支持矩阵、测试、报告同步一致

如果 Claude Code 在报告里把本轮夸大成“完整 factor-variable grammar 已实现”，视为未完成。
