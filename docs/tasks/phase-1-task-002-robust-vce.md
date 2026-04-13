# 任务卡：Phase 1 Task 002 - `vce(robust)` 收口与 Stata 对照

## 基本信息

- 任务名称：OLS `vce(robust)` 实现与 Stata 对照验证
- 所属阶段：Phase 1
- 对应 backlog 条目：
  - `vce(robust)`
- 优先级：P1
- 执行人：QwenCode
- 审查人：Codex

## 本轮目标

在已稳定的 OLS 主路径上，实现并验证 `vce(robust)`，使 Python 结果与 Stata `regress, vce(robust)` 在核心推断字段上对齐。

本轮只做单一目标：robust 协方差。不要提前扩展到 cluster、权重或 FE。

## 必读文档

1. `workspace/qwencode-current/INSTRUCTIONS.md`
2. `docs/architecture/public-api.md`
3. `docs/architecture/result-schema.md`
4. `docs/architecture/stata-compatibility.md`
5. `docs/phases/phase-1-linear-core.md`
6. `docs/testing/testing-strategy.md`
7. `docs/testing/test-case-catalog.md`

## 本轮必须完成的工作

### Step 1: 实现 `vce="robust"`

- 在 `OLS.fit(...)` 路径中支持 `vce="robust"`
- 明确 robust 协方差的公式与自由度处理
- 保证结果对象中的 `vcetype` 与相关推断字段正确填充

### Step 2: 新增 Stata-Python 对照样例

- 至少新增一个 robust 黄金样例
- 样例应比较以下字段：
  - `nobs`
  - `df_model`
  - `df_resid`
  - `r2`
  - `beta`
  - `std_err`
  - 如可稳定提取，也比较 `t` / `p`

### Step 3: 保证旧测试不回归

- `pytest tests -v` 必须继续通过
- Phase 0 和 Phase 1 Task 001 的样例不得被破坏

### Step 4: 文档回填

- 在 `docs/testing/test-case-catalog.md` 登记 robust 样例
- 在 `docs/backlog.md` 更新 `vce(robust)` 状态
- 若实现细节需要补充说明，则更新兼容性文档

## 本轮建议样例

- `p1_robust_hc1`

## 本轮验收标准

- `OLS.fit(vce="robust")` 可运行
- robust 样例具备 Stata-Python 对照证据
- `pytest tests -v` 全绿
- 文档状态与实际结果一致

## 本轮禁止事项

- 不要进入 `vce(cluster)`
- 不要引入权重或 FE
- 不要擅自改变 `vce="ols"` 现有行为

## 失败与升级条件

- 若 robust 小样本修正或自由度规则无法明确，需要停止并上报
- 若 Stata 与 Python 在 robust 标准误上出现系统性偏差，需要输出字段级差异报告
