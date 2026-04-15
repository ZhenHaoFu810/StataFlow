# Wave 1 Task 002：`areg` 最小实现

## 基本信息

- 任务名称：`areg` 最小实现与 synthetic 对齐
- 所属命令族：`Panel / FE / HDFE`
- 对应 backlog 条目：`areg`
- 优先级：P1
- 执行人：Claude Code
- 审查人：Codex

## 任务目标

本轮进入 Wave 1 的 Round 2，只做 `areg`，不碰 `reghdfe` 实现。

需要交付：

1. 引入 `AbsorbingOLS` 或等价最小内核，支持单一吸收变量。
2. 提供 `areg` 所需的最小统计语义：
   - 单吸收变量
   - `vce="ols"`
   - `_cons`
   - `df_a`
3. 跑通 `p3_areg_basic` synthetic 双跑。
4. 全量测试不回归。

## 必读文档

1. `docs/operations/executor-playbook.md`
2. `docs/project-charter.md`
3. `docs/architecture/public-api.md`
4. `docs/architecture/stata-compatibility.md`
5. `docs/research/areg.md`
6. `docs/research/xtreg-fe.md`
7. 本任务卡

## 本轮允许修改的文件

- `src/statapy/estimators/` 下与吸收式 OLS 相关的最小实现文件
- `src/statapy/__init__.py`
- `src/statapy/estimators/__init__.py`
- `tests/golden/` 下 `p3_areg_basic` 对应测试
- 如有必要，补一个最小单元测试文件
- `docs/testing/test-case-catalog.md`
- `workspace/current-task/` 下回报文件

## 本轮禁止事项

- 不得实现 `reghdfe`
- 不得实现双向 FE
- 不得实现 multi-way cluster
- 不得自行扩展到 `aweight + areg`
- 不得把 `real_data` 验证混进本轮；真实数据留到 Round 3

## 最小功能边界

本轮只承诺：

- `AbsorbingOLS(data, y, x, absorb, add_constant=True, missing="drop")`
- `fit(vce="ols")`
- 单一 `absorb` 变量
- 结果对象能表达：
  - `df_a`
  - `fe_vars` 或等价吸收元数据
  - `r2`
  - `rmse`
  - `f_stat`
  - 系数与协方差

## 测试要求

### 必做

- 新增 `p3_areg_basic` 黄金测试
- 先让新测试失败
- 再实现最小代码
- 再让该测试通过
- 最后跑 `pytest tests -v`

### 本轮不做

- `p3_areg_real_panel`
- `p3_reghdfe_basic`
- `p3_reghdfe_real_panel`

## 回报要求

回报必须至少包含：

- 修改文件
- 新增测试
- `p3_areg_basic` 的 Stata 双跑结果
- `df_a`、`_cons`、`r2`、`rmse`、`f_stat` 的对齐情况
- 尚存风险
- 是否建议开放 Round 3 的 `areg` 真实数据验证

## 验收标准

- `p3_areg_basic` 通过
- `pytest tests -v` 全绿
- 本轮没有触碰 `reghdfe` 实现
- `AbsorbingOLS` 的最小接口与研究档案一致
- 无未解释统计偏差
