# Git 工作流

## 1. 目标

Git 不是可选附属品，而是项目治理的一部分。后续所有文档、代码、测试和 Stata 样例都必须通过 Git 管理，以保证阶段边界清晰、证据可追踪、回滚可控。

## 2. 分支策略

默认使用以下分支约定：

- `main`
  - 始终保持可阅读、可审计
  - 只接收经过审查的文档或已通过门禁的阶段成果

- `codex/<topic>`
  - 用于 Codex 维护文档、治理规则和阶段计划
  - 示例：`codex/project-governance`

- `qwen/<topic>`
  - 用于 QwenCode 实施具体代码、测试或数据夹具任务
  - 示例：`qwen/phase0-runner`

## 3. 提交粒度

提交必须小而清晰，推荐规则如下：

- 文档治理变更单独提交
- 代码实现与对应测试尽量同一提交
- 不要把无关阶段的改动混在一个提交中
- 一个提交只服务一个明确目标

## 4. 提交信息规范

推荐格式：

- `docs: define governance loop and git workflow`
- `feat: add phase0 stata runner skeleton`
- `test: add p0_min_ols_auto golden test`
- `refactor: isolate covariance estimator interface`
- `fix: align cluster df correction with stata17`

## 5. 默认协作流程

### 文档轮次

1. Codex 在 `codex/<topic>` 分支更新文档。
2. 文档经用户确认后合并回 `main`。

### 代码轮次

1. QwenCode 从最新 `main` 创建 `qwen/<topic>` 分支。
2. QwenCode 按任务卡实施代码与测试。
3. QwenCode 提交结果和证据。
4. Codex 审查结果是否满足门禁。
5. 通过后再合并回 `main`。

## 6. 何时必须开新分支

以下情况必须新开分支：

- 新阶段开始
- 新命令或新能力开始开发
- 原则层文档有明显变化
- 需要试验性实现但尚未确认是否纳入主线

## 7. 何时禁止直接合并到 `main`

- 尚未完成测试门禁
- 尚未完成文档回填
- 统计偏差未解释
- API 变化未经批准

## 8. 标签与里程碑

建议在阶段完成后打 tag，例如：

- `v0.1-phase0-bootstrap`
- `v0.2-phase1-linear-core`

只有在阶段门禁通过后才允许打 tag。

## 9. 文档与代码是否可混合提交

默认规则：

- 与同一功能直接相关的代码、测试和最小必要文档可以同一分支推进
- 原则层文档、ADR、章程和公共 API 规范不应混在普通代码提交里

## 10. 仓库卫生

- 保持 `.gitignore` 覆盖 Python 缓存、虚拟环境、测试缓存和 Stata 临时产物
- 不提交临时日志、导出缓存和本机路径配置
- 若需提交样例结果，应提交规范化后的稳定产物，而非临时中间文件
