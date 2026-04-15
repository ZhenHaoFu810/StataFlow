# Priority Wave Task 003：`reghdfe` 真实数据验证与收口

## 基本信息

- 任务名称：`reghdfe` 真实数据验证与收口
- 所属命令族：`Panel / FE / HDFE`
- 对应 backlog 条目：`reghdfe`
- 优先级：P1
- 执行人：Claude Code
- 审查人：Codex

## 任务目标

本轮是 `Priority Wave: reghdfe` 的 Round 3，也是该优先波次的收口轮。

需要交付：

1. 完成 `p3_reghdfe_real_panel` 的真实数据双跑。
2. 使用本地公开数据至少覆盖一组真实面板样例，优先：
   - `wagepan`
   - 如有必要再补 `Grunfeld`
3. 确认真实数据下：
   - 样本筛选
   - singleton drop
   - 自动 omitted 的 time-invariant / FE 共线变量
   - 系数
   - 标准误
   - `df_a`
   - `df_resid`
   - `r2`
   - `rmse`
   - `f_stat`
   与 Stata 一致。
4. 若通过，则回填 `docs/backlog.md` 和 `docs/testing/test-case-catalog.md`，将 `reghdfe` 正式推进为 `done`。
5. 若通过，则在回报中明确建议结束 `Priority Wave: reghdfe`，进入下一个 wave。

## 必读文档

1. `docs/operations/executor-playbook.md`
2. `docs/project-charter.md`
3. `docs/roadmap.md`
4. `docs/research/public-datasets.md`
5. `docs/research/reghdfe.md`
6. 本任务卡

## 本轮允许修改的文件

- `tests/golden/` 下 `p3_reghdfe_real_panel` 对应测试
- 必要的测试工具文件
- 若真实数据暴露最小实现缺陷，可最小修改：
  - `src/statapy/estimators/absorbing_ols.py`
  - 如确有必要，最小范围修改 `src/statapy/results/result.py`
- `docs/testing/test-case-catalog.md`
- `docs/backlog.md`
- `workspace/current-task/REPORT.md`

## 本轮禁止事项

- 不得实现 `ivreghdfe`
- 不得实现 `ppmlhdfe`
- 不得实现 multi-way cluster
- 不得新增新的大功能面
- 不得把真实数据验证失败写成“可接受”后直接推进 `done`

## 真实数据要求

优先顺序：

1. `wagepan`
2. `Grunfeld`

本轮至少完成一组真实数据双跑；若第一组已足以覆盖：

- 双向 FE
- 单 cluster
- omitted 变量
- `df_a` 嵌套扣减

则不强制做第二组。

固定使用本地数据路径：

- `research/data/public/panel/wooldridge/wagepan.csv`
- `research/data/public/panel/grunfeld.csv`

## 测试要求

### 必做

- 新增或补齐 `p3_reghdfe_real_panel`
- 先让测试失败
- 修正必要的最小问题
- 跑通 `python -m pytest tests/golden/test_p3_reghdfe_real_panel.py -v`
- 再跑 `python -m pytest tests -v`

### 必须比对的字段

- `nobs`
- `df_model`
- `df_a`
- `df_resid`
- `r2`
- `r2_adj`
- `rmse`
- `f_stat`
- 系数
- 标准误
- `cluster_count`
- `absorb_vars`

## 回报要求

回报必须至少包含：

- 使用了哪一个真实数据集
- 数据预处理与样本筛选说明
- singleton drop 与 omitted 变量说明
- Stata 命令
- Python 调用
- 成功对齐的字段
- 若有偏差，偏差字段和解释
- 是否建议把 `reghdfe` 标记为 `done`
- 是否建议结束 `Priority Wave: reghdfe`

## 验收标准

- `p3_reghdfe_real_panel` 通过
- `python -m pytest tests -v` 全绿
- `docs/testing/test-case-catalog.md` 中 `p3_reghdfe_real_panel` 更新为 `done`
- `docs/backlog.md` 中 `reghdfe` 更新为 `done`
- 本轮未引入 `ivreghdfe`、`ppmlhdfe` 或 multi-way cluster
- 无未解释统计偏差
