# 任务卡：Phase 1 Task 001 - OLS 核心收口与样本规则固化

## 基本信息

- 任务名称：OLS 核心收口、样本筛选、常数项与共线性规则固化
- 所属阶段：Phase 1
- 对应 backlog 条目：
  - OLS
  - 样本筛选与缺失值规则
  - 常数项与共线性处理
- 优先级：P1
- 执行人：QwenCode
- 审查人：Codex

## 本轮目标

在 Phase 0 已打通最小双跑链路的基础上，把 Phase 1 中与 OLS 本体直接相关的规则收口为稳定实现，并用 Stata 对照样例把这些规则固定下来。

本轮不进入 `vce(robust)` 和 `vce(cluster)`。重点是把 OLS 的样本规则、常数项规则、共线性处理和结果字段稳定下来。

## 必读文档

1. `workspace/qwencode-current/INSTRUCTIONS.md`
2. `docs/architecture/public-api.md`
3. `docs/architecture/result-schema.md`
4. `docs/architecture/stata-compatibility.md`
5. `docs/phases/phase-1-linear-core.md`
6. `docs/testing/testing-strategy.md`
7. `docs/testing/test-case-catalog.md`

## 本轮必须完成的工作

### Step 1: 固化 OLS 主路径

- 检查并清理当前 OLS 实现中仅为 Phase 0 临时服务的逻辑
- 保证 `OLS.fit(vce="ols")` 的公开行为稳定
- 明确结果对象中 OLS 路径必须填充的字段

### Step 2: 样本筛选规则

- 明确缺失值剔除顺序
- 保证 `sample_mask`、`n_input_rows`、`nobs` 一致
- 新增含缺失值的 Stata-Python 对照样例

### Step 3: 常数项规则

- 覆盖 `add_constant=True/False`
- 明确 `tss`、`r2`、`df_model` 在有无常数项时的行为
- 为无常数项新增至少一组测试

### Step 4: 共线性处理

- 让 rank-deficient 设计矩阵不会崩溃
- 明确被剔除变量如何记录到 diagnostics
- 新增一个 Stata 对照样例，验证共线变量剔除行为

### Step 5: 文档回填

- 在 `docs/testing/test-case-catalog.md` 补登记本轮新样例
- 在 `docs/backlog.md` 将本轮已完成条目更新为合适状态
- 若 OLS 结果字段有实际补充，更新对应文档

## 本轮建议新增样例

- `p1_ols_missing_drop`
- `p1_ols_noconstant`
- `p1_collinearity_drop`

命名可微调，但必须先登记到测试样例目录。

## 本轮验收标准

- `pytest tests -v` 继续通过
- 新增样例有 Stata-Python 对照证据
- `OLS.fit(vce="ols")` 的样本筛选、常数项、共线性路径有明确测试覆盖
- 文档状态与实际结果一致

## 本轮禁止事项

- 不要进入 `vce(robust)` 或 `vce(cluster)`
- 不要开启权重或 FE
- 不要修改项目章程或 Phase 边界

## 失败与升级条件

出现以下情况必须停止并上报：

- Stata 对照样例显示样本规则与 Python 路径存在系统性差异
- 无常数项情形的统计量语义不清
- 共线性处理必须修改公开 API 或 result schema
