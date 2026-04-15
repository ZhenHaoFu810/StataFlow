# Priority Wave Task 002：`reghdfe` 最小实现

## 基本信息

- 任务名称：`reghdfe` 最小实现与 synthetic 对齐
- 所属命令族：`Panel / FE / HDFE`
- 对应 backlog 条目：`reghdfe`
- 优先级：P1
- 执行人：Claude Code
- 审查人：Codex

## 任务目标

本轮是 `Priority Wave: reghdfe` 的 Round 2，只做 `Phase A` 的最小实现，不做真实数据收口。

需要交付：

1. 在现有 `AbsorbingOLS` 基础上支持 `absorb=[var1]` 与 `absorb=[var1, var2]`。
2. 支持 `reghdfe Phase A` 的最小统计语义：
   - 1-2 个分类 FE
   - `vce="ols"`
   - 单 `vce="cluster"`
   - 默认 singleton drop
   - `df_a`、`df_r`、`cluster_count`
3. 跑通以下 synthetic 黄金样例：
   - `p3_reghdfe_basic`
   - `p3_reghdfe_cluster`
4. 若需要新增 `p3_reghdfe_two_fe` 作为纯双 FE OLS synthetic 样例，可在本轮补登记并实现。
5. 全量测试不回归。

## 必读文档

1. `docs/operations/executor-playbook.md`
2. `docs/project-charter.md`
3. `docs/architecture/public-api.md`
4. `docs/architecture/stata-compatibility.md`
5. `docs/research/reghdfe.md`
6. `docs/research/stata-source-inventory.md`
7. 本任务卡

## 本轮允许修改的文件

- `src/statapy/estimators/absorbing_ols.py`
- `src/statapy/estimators/__init__.py`
- 如确有必要，最小范围修改 `src/statapy/results/result.py`
- `tests/golden/` 下 `reghdfe` 对应 synthetic 测试
- 必要的测试工具文件
- `docs/testing/test-case-catalog.md`
- `workspace/current-task/REPORT.md`

## 本轮禁止事项

- 不得做 `reghdfe` 的真实数据双跑收口
- 不得实现 `ivreghdfe`
- 不得实现 `ppmlhdfe`
- 不得实现 multi-way cluster
- 不得把未研究清楚的 mobility group / pairwise DoF 修正硬塞进 Phase A
- 不得把真实数据失败或未验证字段写成“可接受”后直接推进

## 最小功能边界

本轮只承诺：

- `AbsorbingOLS(..., absorb=[var1])`
- `AbsorbingOLS(..., absorb=[var1, var2])`
- `fit(vce="ols")`
- `fit(vce="cluster", cluster="...")`
- 默认自动 drop singleton 观测
- 结果对象能表达：
  - `df_a`
  - `df_r`
  - `cluster_count`
  - `absorb_vars`
  - `r2`
  - `rmse`
  - `f_stat`
  - 系数与协方差

## 测试要求

### 必做

- 新增或补齐 `p3_reghdfe_basic`
- 新增或补齐 `p3_reghdfe_cluster`
- 如引入 `p3_reghdfe_two_fe`，必须先在样例目录登记
- 先让新测试失败
- 再实现最小代码
- 跑通对应 synthetic 黄金测试
- 最后跑 `python -m pytest tests -v`

### 本轮不做

- `p3_reghdfe_real_panel`
- 任何真实数据收口
- `robust` 如无法稳定对齐可先不开放，但不得伪装为已支持

## 必须比对的字段

- `nobs`
- `df_model`
- `df_a`
- `df_resid`
- `r2`
- `rmse`
- `f_stat`
- 系数
- 标准误
- `cluster_count`（cluster 时）
- `absorb_vars`

## 回报要求

回报必须至少包含：

- 修改文件
- 新增或更新的 synthetic 测试
- `p3_reghdfe_basic` 的 Stata 双跑结果
- `p3_reghdfe_cluster` 的 Stata 双跑结果
- singleton drop、`df_a`、`df_r`、`F`、cluster 修正的对齐情况
- 尚存风险
- 是否建议开放 `Priority Wave Task 003 - reghdfe real-data validation`

## 验收标准

- `p3_reghdfe_basic` 通过
- `p3_reghdfe_cluster` 通过
- `python -m pytest tests -v` 全绿
- 本轮未触碰真实数据收口
- 本轮未扩展到 `ivreghdfe` 或 `ppmlhdfe`
- 无未解释的关键统计偏差
