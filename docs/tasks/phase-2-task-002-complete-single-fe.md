# Phase 2 Task 002：推进完成 Single FE 阶段交付

## 基本信息

- 任务名称：Single FE 与 FE + cluster 联合交付
- 所属阶段：Phase 2
- 对应 backlog 条目：`单向 FE`、`单向 FE + vce(cluster)`
- 优先级：P2
- 执行人：QwenCode
- 审查人：Codex

## 目标

在本轮内尽量推进完成 Phase 2 剩余核心范围：

1. 交付 `FixedEffectsOLS` 或等价公开接口，支持单一 FE 变量。
2. 完成 `xtreg ..., fe` 与 Python 实现的 Stata 双跑对照。
3. 完成 `xtreg ..., fe vce(cluster firm_id)` 与 Python 实现的 Stata 双跑对照。
4. 将 Phase 2 backlog、样例目录和工作区入口更新到可审查状态。

本轮允许工作量明显大于前几轮，但仍需坚持“先测后写”和 Stata 对齐优先。

## 必读文档

按以下顺序阅读，不要跳步：

1. `docs/operations/qwencode-playbook.md`
2. `docs/operations/review-gates.md`
3. `docs/phases/phase-2-weights-fe.md`
4. `docs/architecture/public-api.md`
5. `docs/architecture/result-schema.md`
6. `docs/architecture/stata-compatibility.md`
7. 本任务卡 `docs/tasks/phase-2-task-002-complete-single-fe.md`

## 前置条件

- [ ] 已确认 `Phase 2 Task 001 - aweight` 已由 Codex 验收通过
- [ ] 已在 `docs/testing/test-case-catalog.md` 中登记 `p2_fe_basic` 与 `p2_fe_cluster`
- [ ] 已确认本轮不扩展到双向 FE、高维 FE、`areg` 或新权重类型

## 本轮执行步骤

1. 先补测试与样例设计
   - 为 `p2_fe_basic` 设计面板样例与黄金测试。
   - 为 `p2_fe_cluster` 设计面板样例与黄金测试。
   - 明确 Stata 侧命令、输出字段和容差。
2. 先运行测试并锁定失败点
   - 新测试先应失败，证明当前实现尚未满足。
3. 实施最小公开接口
   - 新增 `FixedEffectsOLS` 或在现有模块内补充等价类。
   - 对外接口必须明确 `fe=` 参数和 `fit(vce=...)` 形态。
   - 结果对象字段必须与 OLS 路径兼容。
4. 实施单向 FE 主路径
   - 实现单个 FE 变量的 within 变换或等价残差化。
   - 明确 `nobs`、`df_model`、`df_resid`、`r2`、`rmse`、`f_stat` 的 Stata 对齐口径。
   - 将 FE 元数据写入结果对象，例如 `fe_vars`。
5. 实施 FE + cluster
   - 在单向 FE 基础上支持 `vce="cluster"`。
   - 明确 cluster 个数、自由度修正、整体检验统计量与 Stata 的对应方式。
6. 跑完整验证
   - 运行新增 FE 黄金测试。
   - 运行 `pytest tests -v`，不得引入回归。
7. 回填文档与证据
   - 如通过，将 `docs/backlog.md` 中 `单向 FE` 与 `单向 FE + vce(cluster)` 更新为 `done`。
   - 将 `docs/testing/test-case-catalog.md` 中 `p2_fe_basic`、`p2_fe_cluster` 更新为 `done`。
   - 用 `workspace/qwencode-current/REPORT_TEMPLATE.md` 提交完成报告。

## 需要新增或修改的文件

- 代码：
  - `src/statapy/estimators/` 下与 FE 相关的实现文件
  - 如需公开导出，更新 `src/statapy/__init__.py` 或相应模块入口
- 测试：
  - `tests/golden/test_p2_fe_basic.py`
  - `tests/golden/test_p2_fe_cluster.py`
- 文档：
  - `docs/backlog.md`
  - `docs/testing/test-case-catalog.md`
  - 必要时补充 FE 相关说明，但不得改写顶层原则

## 验收标准

- [ ] `p2_fe_basic` 双跑通过
- [ ] `p2_fe_cluster` 双跑通过
- [ ] `pytest tests -v` 全绿
- [ ] FE 路径结果对象与 OLS 路径兼容
- [ ] `f_stat` 与 Stata 对齐，不接受“统计量类型不同但可接受”的说明
- [ ] 文档状态与完成报告一致
- [ ] 无未解释偏差

## 禁止事项

- 不得扩展到双向 FE、高维 FE、`areg`
- 不得把 `robust + FE` 作为本轮隐含范围
- 不得跳过 Stata 双跑，仅以 Python 自测替代
- 不得把 Stata 与 Python 在整体检验统计量上的差异记为“可接受”后直接放行
- 不得修改项目章程、ADR 或统计等价原则来规避实现难点

## 风险与备注

- 若 `xtreg, fe` 的某些统计量与直接虚拟变量 OLS 口径不同，必须以 Stata 17 实际输出为准，并在报告中写清验证证据。
- 若 FE + cluster 的自由度修正存在不确定性，先用测试锁定 Stata 结果，再实施代码，不要先猜公式。
- 若在本轮内发现 Phase 2 无法整体收口，必须明确指出卡点属于 `p2_fe_basic` 还是 `p2_fe_cluster`，不得模糊汇报“部分完成”。
