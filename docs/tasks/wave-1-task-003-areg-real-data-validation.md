# Wave 1 Task 003：`areg` 真实数据验证与收口

## 基本信息

- 任务名称：`areg` 真实数据验证与收口
- 所属命令族：`Panel / FE / HDFE`
- 对应 backlog 条目：`areg`
- 优先级：P1
- 执行人：Claude Code
- 审查人：Codex

## 任务目标

本轮是 Wave 1 的 Round 3，只做 `areg` 的真实数据双跑与收口，不再扩展新功能。

需要交付：

1. 完成 `p3_areg_real_panel` 的真实数据双跑。
2. 使用本地公开数据至少覆盖一组真实面板样例，优先：
   - `wagepan`
   - `Grunfeld`
3. 确认真实数据下：
   - 样本筛选
   - 缺失值处理
   - 系数
   - 标准误
   - `df_a`
   - `r2`
   - `rmse`
   - `f_stat`
   与 Stata 一致。
4. 若通过，则回填 `docs/backlog.md` 和 `docs/testing/test-case-catalog.md`，将 `areg` 正式推进为 `done`。

## 必读文档

1. `docs/operations/executor-playbook.md`
2. `docs/project-charter.md`
3. `docs/research/public-datasets.md`
4. `docs/research/areg.md`
5. `docs/research/xtreg-fe.md`
6. 本任务卡

## 本轮允许修改的文件

- `tests/golden/` 下 `p3_areg_real_panel` 对应测试
- 必要的测试工具文件
- `docs/testing/test-case-catalog.md`
- `docs/backlog.md`
- `workspace/current-task/` 下回报文件

若真实数据验证暴露轻微实现缺陷，可最小修改：

- `src/statapy/estimators/absorbing_ols.py`

但不得顺势扩展新功能面。

## 本轮禁止事项

- 不得实现 `reghdfe`
- 不得推进双向 FE
- 不得新增 `areg` 的 `robust` / `cluster` / `aweight` 支持
- 不得新增第二个真实数据命令族任务
- 不得把真实数据验证失败写成“可接受”后直接推进 `done`

## 真实数据要求

优先顺序：

1. `wagepan`
2. `Grunfeld`

本轮至少完成一组真实数据双跑；如果两组都能完成更好，但不是硬要求。

Stata 脚本和 Python 测试都必须固定使用本地数据路径：

- `research/data/public/panel/wooldridge/wagepan.csv`
- `research/data/public/panel/grunfeld.csv`

## 测试要求

### 必做

- 新增 `p3_areg_real_panel` 黄金测试
- 先让测试失败
- 修正必要的最小问题
- 跑通 `pytest tests/golden/test_p3_areg_real_panel.py -v`
- 再跑 `pytest tests -v`

### 必须比对的字段

- `nobs`
- `df_model`
- `df_a`
- `df_resid`
- `r2`
- `rmse`
- `f_stat`
- 系数
- 标准误

## 回报要求

回报必须至少包含：

- 使用了哪一个真实数据集
- 数据预处理与样本筛选说明
- Stata 命令
- Python 调用
- 成功对齐的字段
- 若有偏差，偏差字段和解释
- 是否建议把 `areg` 标记为 `done`

## 验收标准

- `p3_areg_real_panel` 通过
- `pytest tests -v` 全绿
- `docs/testing/test-case-catalog.md` 中 `p3_areg_real_panel` 更新为 `done`
- `docs/backlog.md` 中 `areg` 更新为 `done`
- 本轮未引入 `reghdfe` 或双向 FE 的实现
