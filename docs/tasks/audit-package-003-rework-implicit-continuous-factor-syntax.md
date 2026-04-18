# 审计后任务包 003 返工：隐式连续变量 factor 语义

## 1. 返工目标

本次返工只解决一个阻塞问题：

让 Stata 常用的**裸连续变量**交乘语义真正可用，而不是必须写成显式 `c.` 才能通过。

最低需要对齐的 Stata 语义：

- `x1#x2` 等价于 `c.x1#c.x2`
- `x1##x2` 等价于 `c.x1##c.x2`

这点对 `reghdfe y x1##x2, absorb(firm year)` 之类命令是刚需，不能继续要求用户改写成显式 `c.`。

## 2. 必须完成的内容

### A. parser 语义修正

更新 `src/statapy/compat/stata/factor_variables.py`：

- 不再把裸变量参与 `#` / `##` 一律硬拒绝
- 对连续变量场景做 Stata 对齐：
  - `x1#x2` → `c.x1#c.x2`
  - `x1##x2` → `c.x1##c.x2`

### B. mixed 写法统一

至少明确并实现以下混合情形的统一策略：

- `x1#c.x2`
- `c.x1#x2`
- `x1##c.x2`
- `c.x1##x2`
- `x1#i.g`
- `i.g#x1`
- `x1##i.g`
- `i.g##x1`

可以把裸变量解释为连续变量，但必须：

- 全局一致
- 文档写清楚
- 结果与显式 `c.` 写法一致

### C. 新增测试

至少新增：

- `x1#x2` 与 `c.x1#c.x2` 等价
- `x1##x2` 与 `c.x1##c.x2` 等价
- `x1##i.g` 与 `c.x1##i.g` 等价
- `reghdfe y x1##x2, absorb(firm year)` 可以运行并与手工展开一致

### D. Stata dual-run

至少新增一组：

- `regress y x1##x2`
- `reghdfe y x1##x2, absorb(firm year)`

若时间允许，再补一个非线性命令的裸变量 `##` case。

### E. 文档同步

至少同步：

- `docs/research/factor-variable-semantics.md`
- `README.md`
- `docs/command-support-matrix/regress.md`
- `docs/command-support-matrix/reghdfe.md`
- `docs/command-support-matrix/ivreghdfe.md`
- `docs/command-support-matrix/ppmlhdfe.md`

必须明确写清：

- 裸变量在交乘语法里默认按连续变量解释
- 哪些写法仍未支持

## 3. 不要做的事

本轮不要顺手做：

- `ib#.` / `b.` / `o.` 全支持
- 时间序列算子
- 三阶及以上交互
- 与本返工无关的算法扩展

## 4. 验证要求

至少回报：

```powershell
python -m pytest tests/test_factor_variables.py -v
python -m pytest tests/test_hdfe_synthetic.py tests/test_compat_stata_iv.py tests/test_compat_stata_hdfe.py tests/test_compat_stata_glm.py -v
python -m pytest tests -v
```

## 5. 完成标准

本轮返工通过的最低标准：

- `x1#x2` 与 `x1##x2` 已被接受并按 Stata 连续变量语义处理
- `reghdfe y x1##x2, absorb(firm year)` 已可用
- 混合裸变量/显式 `c.` / `i.` 写法策略统一
- 文档与测试同步一致
