# 发布任务包 001：首次开源 Alpha 修缮

## 任务定位

本轮不是算法扩展轮，也不是 vendor 命令完整度推进轮。  
本轮目标只有一个：

> 把当前仓库从“高质量 Alpha，但更像内部研究仓库”推进到“适合第一次正式对外开源展示与试用”的状态。

你**不需要新增任何估计器功能**，也**不允许**顺手扩命令面。  
所有工作都围绕“首次开源发布面修缮”展开。

## 必须使用的依据

先读并严格遵守以下文档：

1. [docs/qa/first-open-source-release-review.md](</D:/OneDrive - SAIF/PhD3/Stata2Python/docs/qa/first-open-source-release-review.md>)
2. [docs/qa/first-open-source-release-issues.md](</D:/OneDrive - SAIF/PhD3/Stata2Python/docs/qa/first-open-source-release-issues.md>)
3. [docs/qa/first-open-source-release-remediation-plan.md](</D:/OneDrive - SAIF/PhD3/Stata2Python/docs/qa/first-open-source-release-remediation-plan.md>)
4. [docs/operations/executor-playbook.md](</D:/OneDrive - SAIF/PhD3/Stata2Python/docs/operations/executor-playbook.md>)
5. [docs/operations/codex-review-protocol.md](</D:/OneDrive - SAIF/PhD3/Stata2Python/docs/operations/codex-review-protocol.md>)

## 目标

本轮必须至少完成以下三大块：

### A. 发布阻塞项收口

必须修掉以下硬阻塞：

1. 根目录缺少 `LICENSE`
2. `pyproject.toml` 元数据不完整
3. README 与 `pyproject.toml` 的 Python 版本要求不一致
4. release-facing 文档中的错误 issue / 仓库链接

### B. 仓库整洁度修缮

必须整理首次开源的仓库表面：

1. 根目录日志文件处理掉
2. 明显内部 / 一次性脚本迁移到更合适目录，或明确归档
3. `.gitignore` 更新到与当前仓库形态一致
4. README 与 `examples/` 的入口关系清楚

### C. 工程化最低保障

必须补最小工程化信号：

1. 新增基础 CI workflow
2. workflow 至少覆盖：
   - 安装
   - import / smoke
   - 全量 pytest

如你认为合理，也可以补：

3. `CONTRIBUTING.md`
4. 简短 release note / publishing note

## 必须重点修的具体问题

### 1. LICENSE

你必须新增一个正式许可证文件。

要求：

- 许可证类型必须明确写在文件中
- `pyproject.toml` 与 README / release 文档口径一致

如项目治理文档未明确指定许可证，可先采用一个清晰、宽松、适合首次开源的许可证，并在报告中说明选择理由。

### 2. `pyproject.toml`

至少补齐：

- `readme`
- `license`
- `authors` 或 `maintainers`
- `classifiers`
- `keywords`
- `urls`

并确保这些元数据与 README 对外表述一致。

### 3. Python 版本口径统一

当前已知不一致：

- README 说 `Python 3.9+`
- `pyproject.toml` 说 `>=3.10`

你必须统一。

要求：

- 不允许只改其中一个地方而不验证
- 如要下调到 3.9，必须有证据；否则统一提升到 3.10+

### 4. release-facing 错误链接

修掉任何指向错误仓库 / issue 页的链接。

如果还没有正式公开 issue 地址：

- 不要硬填错误地址
- 可以改成占位说明或仓库主页

### 5. 根目录噪音

当前根目录存在多种不适合首次开源暴露的文件。

你必须处理：

- `.log`
- 临时运行脚本
- 一次性诊断脚本

原则：

- 能迁移就迁移到清晰目录
- 不该进版本控制的就加入 `.gitignore`
- 不要删掉真正仍有价值的研究/辅助脚本，但要让它们不再污染根目录

### 6. CI workflow

至少新增一个基础 workflow，例如：

- install dependencies
- run example smoke or import smoke
- run `python -m pytest tests -v`

要求：

- 工作流语义清楚
- 不要写成无法执行的摆设
- 如 golden tests 依赖本地 Stata，需说明是否在 CI 中全部跑，或如何分层跳过

## 允许修改的文件

你可以修改或新增：

- `LICENSE`
- `pyproject.toml`
- `README.md`
- `docs/release/*`
- `.gitignore`
- `.github/workflows/*`
- `examples/*`
- `docs/qa/*`（如需回填）
- 根目录内部脚本与其迁移目标目录

## 明确禁止

- 不新增任何估计器功能
- 不改 `reghdfe` / `ppmlhdfe` / `ivreghdfe` / DID / `rdrobust` 算法逻辑
- 不把“修文档”扩成“顺手重构整个代码库”
- 不为了让根目录更干净而删掉真正有价值但尚未归档的文件，除非已迁移

## 最低验证要求

本轮至少要跑：

```powershell
python -m pip wheel . --no-deps -w .codex_tmp_dist
python -m pytest tests -v
python examples/demo_regress.py
python examples/demo_reghdfe.py
python examples/demo_ppmlhdfe.py
python examples/demo_ivregress_2sls.py
```

如新增或修改 CI workflow，请在报告中说明其覆盖范围与局限。

## 通过标准

Codex 只会在以下条件都满足时放行：

1. 首次开源的硬阻塞项（LICENSE、元数据、版本要求、错误链接）已收口
2. 根目录明显更整洁，临时脚本/日志不再直接污染仓库首页
3. 至少有一个基础 CI workflow
4. wheel 仍能构建
5. 全量测试与核心 example smoke 仍通过
6. 文档与实际对外发布面一致，不夸大、不留明显错误链接

## 回报格式

完成后在 [workspace/current-task/REPORT.md](</D:/OneDrive - SAIF/PhD3/Stata2Python/workspace/current-task/REPORT.md>) 中按下面结构回报：

1. 修掉了哪些 release-blocking 问题
2. `pyproject.toml` / README / release 文档如何统一了
3. 根目录哪些文件被迁移、清理或归档
4. 新增了哪些 CI / release-facing 文件
5. 跑了哪些验证命令
6. 最新 fresh run 结果
7. 当前仓库是否已达到“适合第一次正式对外开源 Alpha 发布”的标准
