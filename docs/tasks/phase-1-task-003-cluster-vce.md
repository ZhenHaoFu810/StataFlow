# 任务卡：Phase 1 Task 003 - `vce(cluster)` 单聚类对齐

## 基本信息

- 任务名称：OLS `vce(cluster)` 实现与 Stata `regress, vce(cluster ...)` 对齐
- 所属阶段：Phase 1
- 对应 backlog 条目：
  - `vce(cluster)` 单聚类
- 优先级：P1
- 执行人：QwenCode
- 审查人：Codex

## 本轮目标

在已稳定的 `OLS` 与 `vce(robust)` 基础上，实现并验证单聚类标准误 `vce(cluster)`，使 Python 输出与 Stata 在核心推断字段上对齐。

本轮只做单维 cluster，不进入多维 cluster、权重或 FE。

## 必读文档

1. `workspace/qwencode-current/INSTRUCTIONS.md`
2. `docs/architecture/public-api.md`
3. `docs/architecture/result-schema.md`
4. `docs/architecture/stata-compatibility.md`
5. `docs/phases/phase-1-linear-core.md`
6. `docs/testing/testing-strategy.md`
7. `docs/testing/test-case-catalog.md`

## 本轮必须完成的工作

### Step 1: 实现 `vce="cluster"`

- 在 `OLS.fit(...)` 路径中支持 `vce="cluster"`
- 要求必须传入 `cluster=...`
- 实现单聚类 sandwich 协方差
- 对齐 Stata 的小样本修正、群组计数与自由度口径
- 在结果对象中正确填充：
  - `model.vcetype`
  - `model.cluster_var`
  - `diagnostics.cluster_count`
  - 相关 `fit` 字段

### Step 2: 新增 Stata-Python 对照样例

- 至少新增一个单聚类黄金样例：
  - 推荐：`p1_cluster_firm`
- 样例应比较以下字段：
  - `nobs`
  - `df_model`
  - `df_resid`
  - `f_stat`
  - `beta`
  - `std_err`
  - `cluster_count`
  - 如可稳定提取，则比较 `p_value`

### Step 3: 覆盖边界情况

- 至少明确一个边界规则并写入测试或报告：
  - 少群组
  - 单例群组
  - cluster 变量含缺失

如果该边界不能在本轮完整实现，必须在报告中写明原因和当前处理方式。

### Step 4: 保证旧测试不回归

- `pytest tests -v` 必须继续全绿
- 不能破坏已有 OLS 与 robust 路径

### Step 5: 文档回填

- 在 `docs/testing/test-case-catalog.md` 更新 cluster 样例状态
- 在 `docs/backlog.md` 更新 `vce(cluster)` 状态
- 如实现细节需要补充说明，可更新兼容性文档，但不得自行改变总原则

## 本轮验收标准

- `OLS.fit(vce="cluster", cluster="...")` 可运行
- 单聚类样例具备 Stata-Python 对照证据
- cluster 标准误和核心推断字段对齐
- `pytest tests -v` 全绿
- 文档状态与实际结果一致

## 本轮禁止事项

- 不要进入多维 cluster
- 不要引入权重或 FE
- 不要擅自改动 `vce="ols"` 与 `vce="robust"` 的既有通过行为
- 若结果 schema 需要变化，先报告给 Codex 裁决

## 失败与升级条件

- 若 cluster 小样本修正与 Stata 规则无法明确，必须暂停并报告
- 若发现 `f_stat`、`df_resid` 或群组计数口径和 Stata 系统性偏离，必须输出字段级差异报告
