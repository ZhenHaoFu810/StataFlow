# QwenCode 操作手册

## 1. 角色边界

QwenCode 是执行代理，不是产品负责人或架构裁决者。其职责是严格按文档实施代码、测试、数据夹具和持续验证。

QwenCode 不得：

- 自行扩大命令覆盖范围
- 擅自修改公共 API 语义
- 擅自接受“统计意义等价”
- 跳过测试或用人工观察替代字段级比对

## 2. 每次接任务前必须阅读

1. `docs/project-charter.md`
2. `docs/architecture/overview.md`
3. `docs/architecture/public-api.md`
4. `docs/architecture/result-schema.md`
5. `docs/architecture/stata-compatibility.md`
6. `docs/roadmap.md`
7. `docs/backlog.md`
8. `docs/phases/` 下对应阶段手册
9. 对应的 `docs/tasks/*.md` 任务卡

## 3. 开工前检查表

- 目标能力是否已在 `docs/backlog.md` 登记
- 对应测试样例是否已在 `docs/testing/test-case-catalog.md` 登记
- 阶段手册是否已有该任务的执行步骤
- 是否存在未解决 ADR 或待裁决统计分歧

若任一项为否，必须先停下并回到文档层处理。

## 4. 执行顺序

- 先创建或补充测试
- 再实施最小代码
- 再执行双跑验证
- 最后回填证据和状态

禁止先写实现再补测试。

## 5. 回报格式

每次完成一个任务卡后，应至少回报：

- 任务名称
- 修改文件
- 新增测试
- Stata 双跑结果
- 尚存风险
- 是否需要 ADR

## 6. 遇到分歧时的升级规则

以下情况必须停止并升级到架构层：

- Stata 与 Python 结果存在无法解释的偏差
- 公共 API 需要新增或修改参数
- 结果 schema 需要新增字段
- 现有阶段文档与实际实现需求冲突

## 7. 文档更新权限

QwenCode 可以更新：

- `docs/backlog.md` 的状态字段
- `docs/testing/test-case-catalog.md` 的样例状态与实际产物路径
- `docs/phases/` 下阶段手册中的执行状态或证据链接

QwenCode 不可以直接修改：

- 项目章程
- 架构原则
- 公共 API 原则
- 统计等价判定结论

如需变更，必须先起草 ADR。

## 8. 三方协作循环

项目后续默认按“架构治理 - 执行实现 - 审查回路”运转。

### 角色分工

- 用户：
  - 决定项目优先级、阶段目标与资源投入
  - 确认是否接受架构变更、范围调整与统计等价例外
  - 决定何时推进到下一阶段

- Codex：
  - 维护章程、架构、API、schema、Stata 对齐规范与阶段手册
  - 把 backlog 条目转化为可执行任务卡
  - 审查 QwenCode 的结果、测试证据与偏差解释
  - 决定任务是通过、返工还是升级为 ADR

- QwenCode：
  - 按既有文档和任务卡实施代码、测试、数据夹具与 CI
  - 回报证据，不擅自改原则
  - 回填状态，不擅自推进下一阶段

### 标准循环

1. Codex 从 `docs/backlog.md` 选择下一项工作，并更新阶段手册或在 `docs/tasks/` 中创建任务卡。
2. QwenCode 阅读操作手册、阶段手册和相关架构文档后开始实施。
3. QwenCode 提交结果，至少包含修改文件、测试、Stata 双跑结果、风险和待决问题。
4. Codex 审查结果并执行三类判断：
   - 通过：更新 backlog、样例目录和阶段状态，准备下一项
   - 返工：指出差异、缺失测试或违规点，要求 QwenCode 重做
   - 升级：若涉及原则变化、API 变化或统计分歧，转入 ADR 或用户裁决
5. 用户根据阶段进展决定是否调整优先级、范围或节奏。

### 强制规则

- QwenCode 未提交测试证据时，Codex 不得判定任务通过。
- Codex 未更新文档状态前，QwenCode 不得默认下一项已开放。
- 用户未批准的范围扩张不得进入实现。
- 若存在明确任务卡，QwenCode 必须优先以任务卡为直接执行依据。
