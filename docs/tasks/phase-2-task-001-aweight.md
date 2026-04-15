# 任务卡：Phase 2 Task 001 - `aweight` 语义落地与 Stata 对齐

## 基本信息

- 任务名称：OLS `aweight` 实现与 Stata `regress [aweight=...]` 对齐
- 所属阶段：Phase 2
- 对应 backlog 条目：
  - `aweight`
- 优先级：P2
- 执行人：QwenCode
- 审查人：Codex

## 本轮目标

在已稳定的 `OLS`、`vce(robust)`、`vce(cluster)` 基础上，实现并验证 `aweight`，使 Python 在点估计、标准误和结果元数据上与 Stata 的 `regress [aweight=...]` 对齐。

本轮只做 `aweight`，不要提前扩展到 `fweight`、`pweight` 或 FE。

## 必读文档

1. `workspace/qwencode-current/INSTRUCTIONS.md`
2. `docs/architecture/public-api.md`
3. `docs/architecture/result-schema.md`
4. `docs/architecture/stata-compatibility.md`
5. `docs/phases/phase-2-weights-fe.md`
6. `docs/testing/testing-strategy.md`
7. `docs/testing/test-case-catalog.md`

## 本轮必须完成的工作

### Step 1: 明确 `aweight` 统计语义

- 先用文档和 Stata 双跑样例确认 `aweight` 的点估计与协方差口径
- 在实现前写清楚：
  - 点估计如何加权
  - 残差方差如何处理
  - 自由度是否沿用当前 OLS 口径
  - `weight_type="aweight"` 应如何进入结果对象

如果语义仍不清楚，必须先停下并回报，不要直接按 `WLS` 猜写。

### Step 2: 实现 `aweight`

- 在 `OLS(...)` 构造器已有 `weights` 和 `weight_type` 预留位的基础上落地
- 至少支持：
  - `weights` 传数组或 Series
  - `weight_type="aweight"`
- 对非法组合给出明确错误：
  - `weights is None` 但设置了 `weight_type`
  - `weight_type` 不是当前支持集合
  - 权重长度与样本长度不一致

### Step 3: 新增 Stata-Python 对照样例

- 至少新增一个黄金样例：
  - 推荐：`p2_aweight_basic`
- 样例应比较以下字段：
  - `nobs`
  - `df_model`
  - `df_resid`
  - `r2`
  - `rmse`
  - `beta`
  - `std_err`
  - `f_stat`
  - `weight_type`

### Step 4: 覆盖至少一个边界情况

- 至少覆盖或说明一个边界：
  - 极端权重
  - 非整数权重
  - 权重缺失导致样本剔除

如果边界不在本轮实现，也必须在报告中明确记录当前处理方式和风险。

### Step 5: 保证旧测试不回归

- `pytest tests -v` 必须继续全绿
- 不能破坏已有 OLS、robust、cluster 路径

### Step 6: 文档回填

- 在 `docs/testing/test-case-catalog.md` 更新 `p2_aweight_basic`
- 在 `docs/backlog.md` 更新 `aweight` 状态
- 如需补充权重口径说明，可更新兼容性文档，但不得擅自改变顶层原则

## 本轮验收标准

- `OLS(..., weights=..., weight_type="aweight")` 可运行
- `p2_aweight_basic` 具备 Stata-Python 对照证据
- `aweight` 的点估计、标准误和核心统计字段对齐
- `pytest tests -v` 全绿
- 文档状态与实际结果一致

## 本轮禁止事项

- 不要进入 `fweight`、`pweight`
- 不要进入 FE
- 不要用“近似等于 WLS”替代 Stata 语义说明
- 不要擅自改动已通过的 OLS / robust / cluster 结果定义

## 失败与升级条件

- 若 `aweight` 的 Stata 语义无法从文档和样例中稳定确认，必须暂停并报告
- 若发现 `aweight` 与普通 WLS 在关键字段上不一致，必须输出字段级差异说明
