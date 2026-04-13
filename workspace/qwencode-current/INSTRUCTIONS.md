# QwenCode 本轮直接指令

你当前正在为 `Stata2Python` 项目执行 Phase 1 的第一轮任务。

## 先做什么

按以下顺序阅读，不要跳步：

1. `docs/operations/qwencode-playbook.md`
2. `docs/operations/review-gates.md`
3. `docs/phases/phase-1-linear-core.md`
4. `docs/tasks/phase-1-task-001-ols-core-and-sample-rules.md`

如果这些文档之间存在冲突：

- 以任务卡 `docs/tasks/phase-1-task-001-ols-core-and-sample-rules.md` 作为本轮直接执行依据
- 同时把冲突点在回报中明确写出，交由 Codex 裁决

## 本轮任务目标

本轮目标不是继续搭 Phase 0 基建，而是把 OLS 主路径规则收口：

1. 固化 OLS 主路径
2. 固化缺失值样本筛选规则
3. 固化常数项有无时的统计量行为
4. 固化共线性处理路径
5. 补充对应 Stata-Python 对照样例并回填文档

## 你必须遵守的规则

- 先测试，再实现
- 不得跳过 Stata 双跑验证
- 本轮不得自行扩展到 robust、cluster、权重、FE
- 不得修改项目章程、架构原则和统计等价判定结论
- 若出现统计偏差、结构冲突或需要改 API/schema，必须停下并上报

## 你完成后必须回报

完成本轮后，使用 `workspace/qwencode-current/REPORT_TEMPLATE.md` 的格式回报，至少包括：

- 修改文件
- 新增测试
- Stata 可执行文件定位方式
- Stata 双跑触发方式
- 成功对齐的字段
- 尚未完成或存在风险的部分
- 是否需要 Codex 进一步裁决
