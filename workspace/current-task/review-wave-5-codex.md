# Wave 5 审查结论（Codex）

## 结论

本轮 **不通过**，暂不放行 `Wave 5: Postestimation`。

当前阻塞点不是测试失败，而是 `margins` 的公共结果语义仍与 Stata 不一致：

- `margins` 结果对象中仍包含 `_cons`
- 但 Stata 的 `margins, dydx(*)` 与 `margins, dydx(*) atmeans` 并不会把常数项当作可报告的边际效应变量

这是一个**数学语义层面**的问题，不是简单的展示差异。

## 我独立复核的证据

我重新运行了：

```powershell
python -m pytest tests/golden/test_w5_predict_basic.py tests/golden/test_w5_predict_real_wagepan.py tests/golden/test_w5_predict_real_mroz.py tests/golden/test_w5_margins_logit_basic.py tests/golden/test_w5_margins_real_mroz.py tests/golden/test_w5_margins_real_crime1.py -v
python -m pytest tests -v
```

结果：

- Wave 5 专项测试在当前环境下通过
- 全量测试：`428 passed`

但我又额外做了直接核验，结果显示：

- `OLS(...).fit().margins(type="dydx").params.keys()` 包含 `_cons`
- `Logit(...).fit().margins(type="dydx").params.keys()` 也包含 `_cons`

这说明当前测试没有覆盖到这一点，而实现本身确实把常数项错误地暴露成边际效应。

## 阻塞点

### 1. `margins` 不应对 `_cons` 生成边际效应

对于 OLS、logit、probit、poisson 等模型，`margins, dydx(*)` 的含义是对解释变量求边际效应。常数项不是解释变量，不应出现在 `dydx(*)` 的结果中。

### 2. 当前 golden tests 没有把这个错误卡住

现有 Wave 5 golden tests 对于 `_cons` 是“如果 Stata 里没有，就跳过不比”。这让错误 API 语义在测试中被漏掉了。

### 3. 报告把这一轮写成已完成，结论过强

在当前 `margins` 公共结果对象仍有 `_cons` 的情况下，`Wave 5` 不能视为已经完全与 Stata 对齐。

## 下一轮必须完成的内容

1. 修正所有 `margins()` 结果对象，使其不再包含 `_cons`。
2. 收紧 Wave 5 golden tests，显式断言 `_cons` 不应出现在 `margins` 结果中。
3. 更新 `REPORT.md`，撤回过强的“Wave 5 已完成”结论，直到语义真正收口。

## 备注

`predict` 当前没有发现新的阻塞性数学问题。当前阻塞点集中在 `margins` 结果对象语义。
