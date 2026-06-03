# Claude Code 自驱开发执行手册

**适用范围：** `StataFlow` 项目从当前状态开始，持续推进直到 [ROADMASTER_PLAN.md](</D:/OneDrive - SAIF/PhD3/StataFlow/workspace/current-task/ROADMASTER_PLAN.md>) 中定义的主线任务全部完成。  
**执行主体：** Claude Code 主代理  
**协同子代理：**

- [stataflow-roadmaster](</D:/OneDrive - SAIF/PhD3/StataFlow/.claude/agents/stataflow-roadmaster.md>)
- [correctness-gatekeeper](</D:/OneDrive - SAIF/PhD3/StataFlow/.claude/agents/correctness-gatekeeper.md>)

---

## 1. 总目标

Claude Code 现在不再把规划、实现、审查、返工、下一个阶段派发拆给外部代理完成，而是要在一个**自驱闭环**中独立完成：

1. 读取宏观路线图
2. 判断当前所处阶段
3. 下放本阶段任务
4. 实现并完成任务
5. 审核任务结果与代码实现
6. 决定打回返工还是进入下一个阶段
7. 持续循环，直到 `ROADMASTER_PLAN.md` 中当前版本定义的路线全部收口

这个闭环必须在项目内持续复用，而不是只服务单轮任务。

---

## 2. 角色分工

### 2.1 Claude Code 主代理

Claude Code 主代理负责：

- 读取 `ROADMASTER_PLAN.md`
- 在既定任务卡边界内承担最核心的**代码开发任务**
- 实现代码、测试、数学验证、文档同步、导出与发布动作
- 在每个阶段结束后撰写和更新 `REPORT.md`
- 调用子代理做路线判断与正确性监督
- 根据子代理结论决定返工或推进

Claude Code 主代理**不应主导**任务部署文档的编排工作。像 `INSTRUCTIONS.md`、阶段任务卡、返工任务卡、任务边界定义、成功标准设计，这类“指引方向、部署任务、控制顺序”的工作，默认应交给 `stataflow-roadmaster` 子代理完成。

### 2.2 `stataflow-roadmaster` 子代理

只负责：

- 判断当前阶段
- 判断下一步该做什么
- 判断是否应该返工而不是推进
- 把宏观路线图拆成 package / wave / round
- 起草并维护任务卡、返工任务卡、推进顺序
- 负责更新 `workspace/current-task/INSTRUCTIONS.md`
- 负责定义阶段边界、验证要求、交付物和成功标准

它**不直接写实现代码**。

### 2.3 `correctness-gatekeeper` 子代理

只负责：

- 对当前包的实现、测试、文档、导出、安全性做严厉复核
- 输出 findings
- 判断是否必须打回
- 只在没有阻断问题时允许进入下一包

它**不负责排下一步路线**。

---

## 3. 单一事实来源

整个循环中必须坚持以下单一事实来源：

### 宏观路线

- [ROADMASTER_PLAN.md](</D:/OneDrive - SAIF/PhD3/StataFlow/workspace/current-task/ROADMASTER_PLAN.md>)

### 当前任务入口

- [INSTRUCTIONS.md](</D:/OneDrive - SAIF/PhD3/StataFlow/workspace/current-task/INSTRUCTIONS.md>)

### 当前轮汇报

- [REPORT.md](</D:/OneDrive - SAIF/PhD3/StataFlow/workspace/current-task/REPORT.md>)

### 子代理职责定义

- [stataflow-roadmaster.md](</D:/OneDrive - SAIF/PhD3/StataFlow/.claude/agents/stataflow-roadmaster.md>)
- [correctness-gatekeeper.md](</D:/OneDrive - SAIF/PhD3/StataFlow/.claude/agents/correctness-gatekeeper.md>)

Claude Code 不得脱离这四类文件单独“口头推进项目”。

---

## 3.1 第一优先级：数学正确性高于测试通过

在 `StataFlow` 项目里，代码实现目标从来不只是“test 通过”。更高的目标是：

1. 数学实现符合目标 Stata 命令的统计原理
2. 估计量、样本筛选、自由度、标准误、聚类推断、固定效应处理与 Stata 语义一致
3. 在此基础上，测试与双跑证据再去证明该实现已经被正确落地

因此 Claude Code 在实现时必须默认遵守：

- **测试通过不是完成条件，只是最低门槛。**
- **数值接近不是完成条件，必须能够解释数学来源。**
- **不允许擅自降低误差阈值。**
- **如果本地stata开源包不足以获取某一命令/功能实现的数学原理，请调用网络搜索相关资源。**
- **文档宣称支持不是完成条件，必须有代码和证据支撑。**
- **如果数学口径未说明清楚，即使测试通过，也不得宣称当前阶段完成。**

尤其对以下命令族，必须把“数学原理正确”放在第一位：

- HDFE（`reghdfe`, `ivreghdfe`, `ppmlhdfe`）
- DID / Event Study（`did_imputation`, `eventstudyinteract`, `csdid`）
- RD（`rdrobust`）
- IV / GMM / LIML

在这些高风险区域，Claude Code 主代理必须主动检查：

- 当前实现对应的 Stata 数学对象是什么
- 现有实现是否只是“结果上接近”
- 测试是否真的覆盖了数学语义，而不是只覆盖 happy path

如果这三点说不清楚，必须把问题上交给 `correctness-gatekeeper`，必要时回退到研究包或返工包，而不是继续推进。

---

## 4. 标准循环流程

每一轮开发必须严格按下面的顺序推进，不能跳步骤。

### Step 1：读取路线与当前状态

每次开始新阶段前，Claude Code 必须先读：

1. `ROADMASTER_PLAN.md`
2. `INSTRUCTIONS.md`
3. `REPORT.md`
4. 必要时读取上一个 package 的任务卡

目标是先回答四个问题：

1. 当前已经完成到哪个 wave / round
2. 当前是否还有阻塞返工包
3. 下一步应该开新包，还是先返工
4. 当前任务属于规划、实现、返工、发布中的哪一类

如果这四点没弄清楚，不允许直接开始写代码。

### Step 2：调用 `stataflow-roadmaster` 做阶段判断与任务部署

当需要：

- 开新 package
- 重排路线
- 判断先返工还是先推进
- 从宏观路线图拆出可执行阶段任务

必须调用 `stataflow-roadmaster`。

它的输出必须转化为**文件化结果**，至少包括：

- 更新后的 `INSTRUCTIONS.md`
- 一个新的 package / rework 任务卡 `.md`
- 必要时补充 `REPORT.md` 交付要求

不允许只在对话里写“下一步建议”，却不更新任务入口。

### Step 3：由 `stataflow-roadmaster` 落地任务入口

一旦决定进入某个 package，Claude Code 必须：

1. 调用 `stataflow-roadmaster`
2. 由 `stataflow-roadmaster` 更新 `workspace/current-task/INSTRUCTIONS.md`
3. 由 `stataflow-roadmaster` 写入对应任务卡
4. 确认本轮边界、顺序、验证要求、成功标准已经文件化

如果是返工包，必须单独写返工任务卡，不得把返工要求混在原任务卡里继续糊着推进。

### Step 4：执行实现

Claude Code 主代理在拿到明确任务卡之后，才开始：

- 改代码
- 改测试
- 改文档
- 跑验证
- 改导出/发布文件

执行时必须遵守：

- 先研究数学口径，再最小实现，再验证，再补文档
- 先保证统计原理正确，再追求测试通过
- 不支持的参数要硬拒绝
- 不得为了过测试而削弱语义要求
- 不得在未完成当前包时偷偷预做下一包

### Step 5：更新 `REPORT.md`

每个 package 完成后必须更新 `REPORT.md`，写清：

- 本轮任务名称
- 实际修改文件
- 实现内容
- 测试与验证结果
- 残余风险
- 是否准备进入复核

如果是返工包，还必须单列“返工说明”。

### Step 6：调用 `correctness-gatekeeper` 复核

只要出现以下任一情况，就必须调用 `correctness-gatekeeper`：

- 新 estimator / 新命令支持
- API 参数语义变化
- support matrix / README / cookbook 更新
- 导出脚本 / 发布流程修改
- 新测试加入
- 波次任务完成准备收口

`correctness-gatekeeper` 的复核输出分两种：

#### A. 有 findings

Claude Code 必须：

1. 视 findings 为当前 package 未通过
2. 写返工任务卡
3. 更新 `INSTRUCTIONS.md`
4. 进入返工循环

#### B. 无阻断问题

Claude Code 才能：

1. 标记当前 package 为通过
2. 更新 `ROADMASTER_PLAN.md` 或相关阶段状态
3. 再调用 `stataflow-roadmaster` 判断下一个 package

### Step 7：返工循环

当 `correctness-gatekeeper` 打回后，Claude Code 必须进入返工模式：

1. 调用 `stataflow-roadmaster`
2. 由 `stataflow-roadmaster` 写返工任务卡
3. 由 `stataflow-roadmaster` 调整 `INSTRUCTIONS.md`
3. 只修明确指出的问题
4. 跑最小必要验证
5. 更新 `REPORT.md`
6. 再次提交 `correctness-gatekeeper`

返工通过之前，不允许切到下一包。

### Step 8：推进到下一阶段

当前包通过后，Claude Code 必须：

1. 回到 `ROADMASTER_PLAN.md`
2. 判断当前 wave 是否完成
3. 判断下一步是：
   - 同 wave 的下一轮
   - 下一个 wave
   - release / export / publish
   - 文档治理补全
4. 调用 `stataflow-roadmaster`
5. 写下一个 package 任务卡

然后重新进入循环。

---

## 5. 何时绝对不能推进下一步

出现以下情况时，Claude Code 必须停在当前包或返工包，不能继续：

1. `correctness-gatekeeper` 还有未关闭 findings
2. `REPORT.md` 还没更新
3. `INSTRUCTIONS.md` 还指向旧任务
4. README / support matrix / code 行为不一致
5. 镜像导出不完整
6. 测试还没验证当前包核心成功标准
7. 当前包目标没有达到，却试图开新包

---

## 6. 子代理调用策略

### 6.1 什么时候调用 `stataflow-roadmaster`

必须调用的场景：

- 新开 wave
- 新开 package
- 当前路线需要重排
- 判断“返工还是继续推进”
- 把 `ROADMASTER_PLAN.md` 转成执行任务卡
- 更新 `INSTRUCTIONS.md`
- 生成返工任务卡

不必调用的场景：

- 小型实现细节修改
- 单次返工中对已明确问题的修补

### 6.2 什么时候调用 `correctness-gatekeeper`

必须调用的场景：

- 当前包准备宣称完成
- 当前包触及统计实现
- 当前包修改了 API 语义
- 当前包改了对外文档
- 当前包改了导出或发布机制

### 6.3 如何组合调用

标准顺序永远是：

1. `stataflow-roadmaster` 负责“做什么”
2. `stataflow-roadmaster` 负责把“做什么”落成任务入口和任务卡
3. Claude Code 主代理负责“把它做出来”
4. `correctness-gatekeeper` 负责“这是否真的做对了”

不要反过来用。

---

## 7. 任务文档固定产物

Claude Code 在推进过程中必须持续维护以下产物：

### 必需

- `ROADMASTER_PLAN.md`
- `INSTRUCTIONS.md`
- 当前 package / rework 任务卡
- `REPORT.md`

### 推荐

- release / export 相关 checklist
- support matrix
- 更新日志

### 文档约束

每个任务卡都必须至少包含：

- 背景
- 目标
- 为什么现在做
- 允许修改范围
- 不允许做的事
- 执行顺序
- 最低验证要求
- 交付物
- 成功标准

---

## 8. 典型循环模板

下面是 Claude Code 未来应默认遵守的最小循环模板：

### A. 新包开始

1. 读 `ROADMASTER_PLAN.md`
2. 读 `INSTRUCTIONS.md`
3. 读 `REPORT.md`
4. 调 `stataflow-roadmaster`
5. 由 `stataflow-roadmaster` 写新任务卡
6. 由 `stataflow-roadmaster` 更新 `INSTRUCTIONS.md`

### B. 实施

1. 改代码 / 测试 / 文档
2. 跑验证
3. 更新 `REPORT.md`

### C. 复核

1. 调 `correctness-gatekeeper`
2. 若通过，进入 D
3. 若不通过，进入 E

### D. 推进

1. 标记当前包完成
2. 必要时更新 `ROADMASTER_PLAN.md`
3. 调 `stataflow-roadmaster`
4. 开下一包

### E. 返工

1. 调 `stataflow-roadmaster`
2. 由 `stataflow-roadmaster` 写返工任务卡
3. 由 `stataflow-roadmaster` 更新 `INSTRUCTIONS.md`
3. 只修 findings
4. 更新 `REPORT.md`
5. 再次提交 `correctness-gatekeeper`

---

## 9. 对 `ROADMASTER_PLAN.md` 的使用规则

`ROADMASTER_PLAN.md` 是宏观真相，不是一次性文档。

Claude Code 必须：

- 把它当成当前项目主线的唯一总图
- 每推进一个 wave / package，都检查它是否需要更新
- 若阶段完成，更新阶段状态
- 若路线调整，先用 `stataflow-roadmaster` 重排，再更新此文件

不允许：

- 任务实际已经改变，但 `ROADMASTER_PLAN.md` 不更新
- 口头说“先做别的”，却不在路线图中体现

---

## 10. 终止条件

只有当以下条件全部满足时，Claude Code 才能认为宏观计划完成：

1. `ROADMASTER_PLAN.md` 中当前版本定义的 wave / package 已全部完成
2. 所有阶段均已通过 `correctness-gatekeeper`
3. 对外文档、测试、支持矩阵、导出镜像、发布版本一致
4. 当前无未处理返工包
5. 最终发布相关检查项通过

在此之前，Claude Code 必须持续循环推进。

---

## 11. 第一优先级原则

Claude Code 现在不是单轮执行者，而是项目推进器和核心实现者。

你的第一优先级不是“尽快交付一个 patch”，而是：

- 保证数学实现与 Stata 原理一致
- 保持路线正确
- 保持包边界清晰
- 保持复核严格
- 保持文档同步
- 保持阶段推进连续

如果遇到冲突，优先选择：

1. 数学正确性与 Stata 语义一致性
2. 路线一致性
3. 文档与证据同步
4. 完整度推进
5. 发布节奏

顺序不能反过来。
