# Codex Review: 审计后任务包 003

## 结论

**不通过，需要返工。**

## fresh verification

已独立复跑：

```powershell
python -m pytest tests/test_factor_variables.py tests/test_hdfe_synthetic.py tests/test_compat_stata_iv.py tests/test_compat_stata_hdfe.py tests/test_compat_stata_glm.py -v
python -m pytest tests -v
```

结果：

- 专项测试：`69 passed`
- 全量测试：`579 passed`

测试基线是干净的，但这不足以放行。

## 阻塞点

### 1. 裸变量交乘语义与用户明确要求不一致

用户已经明确提出以下 Stata 常用写法应被支持：

```stata
reghdfe y x1##x2, absorb(firm year)
```

当前实现却统一把裸变量参与的 `#` / `##` 写法硬拒绝：

```text
ValueError: Bare variables are not allowed inside factor interactions; explicitly use c. or i. for term: x1##x2
```

这意味着当前库虽然支持了 `c.x1##c.x2`，但仍然**不支持用户明确点名的命令层写法**。在 Stata 中，`x1##x2` 的默认语义就是连续变量全因子展开；当前实现把它当成错误，这不能接受。

这不是文档措辞问题，而是实际公共命令接口不符合目标语义。

### 2. 报告把“明确拒绝裸变量交乘”写成阶段性完成，不可接受

[workspace/current-task/REPORT.md](</D:/OneDrive - SAIF/PhD3/Stata2Python/workspace/current-task/REPORT.md>) 把“裸变量参与 `#` / `##` 明确拒绝”写成了本轮的统一策略与完成项。

但从当前项目目标和用户要求看，这不是可接受的产品边界，而是尚未完成的缺口。报告在这一点上的结论不能作为放行依据。

## 为什么测试全绿仍然不能通过

因为当前测试矩阵已经默认接受了“裸变量交乘必须拒绝”这个产品决策；也就是说，测试验证的是**实现是否忠于当前代码决策**，并没有验证这个决策本身是否符合项目目标与用户要求。

## 返工要求

下一轮返工只聚焦这一件事：

- 支持 Stata 中裸连续变量的 `#` / `##` 语义

最低要求：

- `x1#x2` 等价于 `c.x1#c.x2`
- `x1##x2` 等价于 `c.x1##c.x2`
- `x1#c.x2`、`c.x1#x2`、`x1##i.g`、`i.g##x1` 等混合写法给出统一、可解释、Stata 对齐的处理
- 不能破坏当前已经通过的 `i.` / `c.` 显式语义

通过前，不应下放下一步大任务。
