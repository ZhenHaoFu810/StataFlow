# 任务卡：Phase 0 Task 001 - Stata Runner 与首个 OLS 双跑样例

## 基本信息

- 任务名称：Stata runner 最小链路与首个 OLS 黄金样例
- 所属阶段：Phase 0
- 对应 backlog 条目：
  - 项目骨架与包结构
  - Stata runner 最小链路
  - 结果 schema 与序列化
  - 首个 OLS 双跑样例
- 优先级：P0
- 执行人：QwenCode
- 审查人：Codex

## 本轮目标

交付一个最小但完整的可验证闭环：

1. 建立 Python 项目骨架
2. 建立结果 schema 骨架
3. 实现可执行的 Stata runner 最小链路
4. 完成首个 `regress` 对照样例
5. 让 Python 与 Stata 至少有一条字段级双跑测试跑通

本轮目标不是实现完整 OLS 库，而是先打通“可开发、可测试、可比对”的工程回路。

## 必读文档

QwenCode 开始前必须阅读：

1. `docs/project-charter.md`
2. `docs/architecture/overview.md`
3. `docs/architecture/result-schema.md`
4. `docs/architecture/stata-compatibility.md`
5. `docs/testing/testing-strategy.md`
6. `docs/testing/test-case-catalog.md`
7. `docs/phases/phase-0-bootstrap.md`
8. `docs/operations/qwencode-playbook.md`
9. `docs/operations/review-gates.md`

## 建议文件结构

本轮建议创建或补齐以下路径：

- `src/statapy/__init__.py`
- `src/statapy/results/`
- `src/statapy/stata_runner/`
- `tests/`
- `tests/golden/`
- `stata/`
- `stata/cases/`
- `stata/output/`
- `pyproject.toml`

若 QwenCode 认为目录名需要微调，可以调整，但不得改变四层架构含义。

## 本轮执行步骤

### Step 1: 建立项目骨架

需要完成：

- 创建 `src/` 包结构
- 创建 `tests/` 结构
- 创建 Stata 相关目录
- 选择最小依赖管理方案并初始化配置

本步产出：

- 可导入的最小 Python 包
- 可运行的最小测试配置

### Step 2: 建立 result schema 最小实现

需要完成：

- 创建结果对象骨架
- 支持序列化为 dict 或 JSON 兼容结构
- 至少覆盖 `model`、`sample`、`fit`、`coefficients`、`variance`、`provenance` 这些顶层块

本步测试：

- round-trip 或序列化 smoke test

### Step 3: 实现 Stata runner 最小链路

需要完成：

- 能找到 Stata 可执行文件
- 能生成最小 `.do` 文件
- 能调用 Stata 批处理运行
- 能读取退出状态和输出文件

约束：

- 不要在 runner 中编码具体回归逻辑
- 路径配置尽量可参数化，不要把单一本机路径写死在核心代码里

本步测试：

- runner smoke test

### Step 4: 创建首个 OLS 对照样例

需要完成：

- 准备一个最小数据集
- 编写 Stata `.do` 文件运行 `regress`
- 导出结构化结果，至少包括系数向量、协方差矩阵、样本数和自由度
- 在 Python 侧创建对应黄金测试

本步约束：

- 不得只比较系数
- 至少比较：`params`、`cov`、`nobs`、`df_model`、`df_resid`

### Step 5: 回填文档状态

需要完成：

- 在 `docs/testing/test-case-catalog.md` 更新 `p0_min_ols_auto` 的状态与实际产物路径
- 若目录结构与计划有偏差，在对应阶段手册或任务结果中说明

## 本轮建议测试顺序

1. 包导入 smoke test
2. result schema 序列化测试
3. runner smoke test
4. 首个 OLS 双跑测试

## QwenCode 回报格式

本轮结束后，QwenCode 必须至少回报：

- 修改文件列表
- 新增测试列表
- Stata 可执行文件定位方式
- Stata 双跑命令或触发方式
- 双跑成功字段
- 尚未完成的字段
- 是否存在需要 Codex 裁决的问题

## 本轮验收标准

- Python 包骨架已建立
- result schema 最小实现可序列化
- runner 最小链路可执行
- `p0_min_ols_auto` 已落地并通过
- 文档状态已回填

## 本轮禁止事项

- 不要实现完整线性模型 API
- 不要提前进入 robust、cluster、FE
- 不要为了“先跑通”而绕过结构化结果导出
- 不要修改项目章程或公共 API 原则

## 失败与升级条件

出现以下任一情况，QwenCode 应停止并上报：

- 无法稳定调用 Stata 17
- Stata 导出结构无法映射到 result schema
- 阶段文档与实际实施存在结构性冲突
- 需要改动结果 schema 的顶层结构
