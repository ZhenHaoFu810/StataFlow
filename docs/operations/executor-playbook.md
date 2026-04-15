# 执行代理手册

## 1. 角色边界

Claude Code 是执行代理，不是产品负责人或架构裁决者。其职责是严格按文档实施代码、测试、数据夹具和持续验证。

执行代理不得：

- 自行扩大命令覆盖范围
- 擅自修改公共 API 语义
- 擅自接受“统计意义等价”
- 跳过真实数据验证
- 跳过测试或用人工观察替代字段级比对

## 2. 每次接任务前必须阅读

优先入口：

0. 若存在 `workspace/current-task/INSTRUCTIONS.md`，先从该文件进入本轮任务

1. `docs/project-charter.md`
2. `docs/architecture/overview.md`
3. `docs/architecture/public-api.md`
4. `docs/architecture/result-schema.md`
5. `docs/architecture/stata-compatibility.md`
6. `docs/roadmap.md`
7. `docs/backlog.md`
8. `docs/research/` 下对应命令研究档案
9. `docs/phases/` 下对应阶段手册
10. 对应 `docs/tasks/*.md` 任务卡

## 3. 开工前检查表

- 目标能力是否已在 `docs/backlog.md` 登记
- 对应命令是否已有研究档案
- synthetic 与 real-data 样例是否已在 `docs/testing/test-case-catalog.md` 登记
- 是否存在未解决 ADR 或统计分歧

如任一项为否，必须先停下并回到文档层。

## 4. 标准执行顺序

- 先补研究与样例登记
- 再写或补测试
- 再实施最小代码
- 再执行 Stata 双跑
- 最后回填证据与状态

## 5. 回报要求

每次任务回报至少包含：

- 任务名称
- 修改文件
- 新增研究档案或引用来源
- synthetic 测试结果
- real-data 测试结果
- Stata 双跑结果
- 尚存风险
- 是否需要 Codex 裁决

## 6. 遇到分歧时的升级规则

以下情况必须停止并升级：

- Stata 与 Python 结果存在无法解释的偏差
- 公共 API 需要新增或修改参数
- 结果 schema 需要新增字段
- 研究档案与测试结论冲突
- 真实数据与 synthetic 对齐结论不一致

## 7. 文档更新权限

执行代理可以更新：

- `docs/backlog.md` 的状态字段
- `docs/testing/test-case-catalog.md`
- `docs/research/` 下研究档案的证据部分
- `workspace/current-task/` 下的回报类文件

执行代理不可以直接修改：

- 项目章程
- 架构原则
- 公共 API 原则
- 统计等价判定结论

## 8. 协作循环

1. Codex 维护架构、路线图、研究框架与门禁。
2. Claude Code 根据任务卡实施命令的一小块。
3. Claude Code 回报研究证据、测试证据和风险。
4. Codex 决定通过、返工或升级到 ADR。
5. 用户决定是否调整优先级与节奏。
