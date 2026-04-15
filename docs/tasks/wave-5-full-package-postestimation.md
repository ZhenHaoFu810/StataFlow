# Wave 5 Full Package: Postestimation

## 基本信息

- 任务名称：Wave 5 整包任务：Postestimation
- 所属命令族：`Postestimation`
- 优先级：P5
- 执行人：Claude Code
- 审查人：Codex

## 任务目标

一次性推进整个 `Wave 5`，但必须按内部 `Stage A / B / C` 顺序完成，不能跳阶段宣称整包完成。

本 wave 的目标不是复刻 Stata 全部 postestimation，而是交付一个 **高频、可双跑、结果语义清晰** 的最小子集：

- `predict`
- `margins` 高频子集

## 内部阶段

### Stage A: Research Closure

必须先补齐研究文档，再进入实现：

- `docs/research/predict.md`
- `docs/research/margins.md`

每份文档至少写清：

- 支持的模型族
- 支持的 Stata 语法子集
- 输出对象与字段语义
- 数学定义
- 推断口径
- 明确不支持的选项

同时必须在 `docs/testing/test-case-catalog.md` 预登记：

- synthetic 样例
- real-data 样例
- 每个样例的主要风险点

### Stage B: Minimum Implementation

#### `predict`

最小子集要求：

- 线性类模型：
  - `predict, xb`
  - `predict, residuals`
- 二元/计数模型：
  - `predict, xb`
  - `predict, pr` 或 `predict, mu`
- 覆盖的 Python 模型至少包括：
  - `OLS`
  - `FixedEffectsOLS` / `AbsorbingOLS`
  - `Logit`
  - `Probit`
  - `Poisson`
  - `PPMLHDFE`

明确不做：

- 所有 Stata `predict` 选项全集
- influence / score / stdp / hat 等高级输出
- 图形接口

#### `margins`

最小子集要求：

- `margins, dydx(*)`
- `margins, atmeans`
- 首先覆盖：
  - `Logit`
  - `Probit`
  - `Poisson`
- 对线性模型，高频子集可接受：
  - `margins, dydx(*)` 结果回到系数本身或等价对象

明确不做：

- `marginsplot`
- factor-variable 全历史兼容
- 高维交互效应图
- bootstrap / delta-method 以外复杂推断扩展

### Stage C: Real-Data Validation And Hardening

至少做到：

- `predict` 有 synthetic + real-data 双线验证
- `margins` 有 synthetic + real-data 双线验证
- 至少覆盖 1 个线性真实数据样例
- 至少覆盖 1 个非线性真实数据样例

优先复用项目内已有公开数据：

- `Fama-French 3 factors`
- `wagepan`
- `Grunfeld`
- `Mroz`
- `crime1`
- `countymurders`

## 真实数据要求

所有 real-data 验证必须：

- 使用本地公开数据
- 在报告中记录 Stata 命令与 Python 调用
- 说明对齐字段
- 说明任何剩余偏差及其数学原因

## 允许修改的文件

- `src/statapy/` 下与 postestimation 相关文件
- `tests/golden/` 下新增的 Wave 5 测试
- `docs/research/predict.md`
- `docs/research/margins.md`
- `docs/testing/test-case-catalog.md`
- `docs/backlog.md`
- `workspace/current-task/REPORT.md`

## 禁止事项

- 不要扩展到 `marginsplot`
- 不要扩展到复杂 bootstrap / simulation inference
- 不要把所有 Stata `predict` 子选项都一次做完
- 不要引入未文档化的模型专用特殊行为
- 不要把未验证字段写成“可接受”后直接放行

## 强制验证命令

完成后至少运行：

```powershell
python -m pytest tests/golden/test_w5_predict_* -v
python -m pytest tests/golden/test_w5_margins_* -v
python -m pytest tests -v
```

如果命名不同，必须在报告里逐项列出实际命令。

## 回报要求

报告必须分为 `Stage A / Stage B / Stage C`，明确写清：

1. `predict` 覆盖了哪些模型与输出类型
2. `margins` 覆盖了哪些模型与语义子集
3. 每个新增 synthetic 样例的风险点
4. 每个 real-data 样例的数据来源与 Stata/Python 命令
5. 哪些字段与 Stata 严格对齐，哪些字段若仍有偏差，偏差原因是什么
6. 全量测试结果

## 通过标准

只有同时满足以下条件，Codex 才会放行整个 Wave 5：

1. `predict` 与 `margins` 的研究文档完成。
2. `predict` 与 `margins` 都有 synthetic 黄金样例。
3. `predict` 与 `margins` 都至少有 1 个真实公开数据双跑样例。
4. 全量测试通过。
5. `docs/backlog.md` 与 `docs/testing/test-case-catalog.md` 状态一致。
6. 没有未解释的关键统计口径偏差。
