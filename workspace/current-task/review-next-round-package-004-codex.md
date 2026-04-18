# Codex Review: 下一轮任务包 004

## 结论

本轮 **打回**，暂不视为“开源初版 Alpha 收口完成”。

阻塞点不是测试失败。相反，我重新跑了：

- `python -m pytest tests -v` -> `485 passed`
- `python examples/demo_regress.py` -> 正常
- `python examples/demo_reghdfe.py` -> 正常
- `python examples/demo_ppmlhdfe.py` -> 正常
- `python examples/demo_ivregress_2sls.py` -> 正常

但这轮的核心目标是**面向外部用户的产品化收口**。在这个标准下，当前公开文档与 wrapper 实际返回对象语义仍然不一致。

## 阻塞项

### 1. README 的公开 quick-start 示例会误导用户

README 当前写法把：

- `logit(...)`

当成可以继续调用：

- `.margins(type="dydx")`

的对象。

但实际运行结果是：

- `statapy.compat.stata.logit(...)` 返回 `ResultSchema`
- 该对象没有 `.margins()` 方法

这意味着 README 的公开示例对外是不可工作的。

### 2. 支持矩阵把 wrapper 描述成支持 postestimation，但实际接口没有暴露

例如：

- `docs/command-support-matrix/logit.md`
- `docs/command-support-matrix/ppmlhdfe.md`

都写了 `predict(...)` / `margins(...)` 为 “Supported Postestimation”。

但当前 `compat.stata` wrapper 返回的并不是估计器对象，而是结果对象 `ResultSchema`，调用层没有这些方法。

这会让用户自然理解为：

- `logit(...).margins(...)`
- `ppmlhdfe(...).predict(...)`

是支持的，而实际上并不支持。

### 3. 报告错误声称“README / wrapper / 支持矩阵 / 测试四者一致”

当前报告中明确写了：

- README 示例可运行
- 支持矩阵与 wrapper 行为一致
- 无夸大描述

这与实际不符，因为 wrapper 公开表面并没有暴露 `predict` / `margins`。

## 返工要求

本次返工只需收口公开 API 语义，不要求新增新算法：

1. 决定并统一一种外部语义：
   - **方案 A**：`compat.stata` wrapper 继续返回 `ResultSchema`
     - 那么 README、支持矩阵、总览页都必须改写，不能再把 wrapper 描述成直接支持 `.predict()` / `.margins()`
   - **方案 B**：让 wrapper 返回支持 postestimation 的对象
     - 那么要真正补齐调用层接口，并补测试

2. 无论选哪种方案，都必须：
   - 更新 `README.md`
   - 更新 `docs/command-support-matrix/README.md`
   - 更新所有受影响命令的单命令支持矩阵（至少 `logit`、`probit`、`poisson`、`ppmlhdfe`，必要时也包括线性命令）
   - 更新 `workspace/current-task/REPORT.md`

3. 返工后必须补一类直接公共接口测试：
   - 明确断言 wrapper 返回对象上哪些 postestimation 方法存在，哪些不存在

## 放行条件

只有当以下条件同时满足，任务包 004 才能放行：

- README 示例与真实公开 API 语义一致
- 支持矩阵不再夸大 wrapper 层 postestimation 能力
- 报告不再错误宣称“一致性已完成”
- 全量测试继续通过
