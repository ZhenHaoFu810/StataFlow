# StataFlow Agent Project Management Runbook

> 本文档是后续 Agent 进入 StataFlow 项目的第一操作手册。任何 Agent 在修改代码、文档、Git 分支、GitHub 远端、公开发布分支之前，都必须先阅读并遵守本文档。

最后更新：2026-06-05  
适用仓库根目录：`D:/OneDrive - SAIF/PhD3/StataFlow`

---

## 1. 项目管理总原则

StataFlow 不是普通 Python 包。它是一个以 Stata 17 为地面真值的计量经济学复现工具包。所有开发、测试、文档、Git 操作和 GitHub 交互都必须服从两个目标：

1. 内部开发线必须保留完整研究、审计、golden dual-run、Stata 证据和治理文档。
2. 公开发布线必须只包含可公开发布的源码、公开测试、示例、公开数据、公开验证证据和用户文档。

任何 Agent 的首要职责不是“尽快改完”，而是保护项目状态不被错误分支、错误远端、错误公开内容、错误强推或历史 secret 污染破坏。

禁止事项：

- 不得在未确认分支和远端前运行 `git push`。
- 不得向公开 GitHub 仓库推送完整内部 `dev`。
- 不得绕过 GitHub push protection。
- 不得用 `git push --force`、`git reset --hard`、`git clean -fdx` 等破坏性命令，除非用户明确要求并且已记录回滚点。
- 不得删除 `StataFlow_open_source` 备份目录。
- 不得把 `docs/audit/`、`docs/operations/`、`workspace/`、`stata/`、`tests/golden/`、`scripts/` 等内部路径带入公开 `main`。
- 不得把 token、secret、license、私有数据、临时 session zip、debug 脚本推到任何远端。

推荐习惯：

- 每次开始前记录 `git status --short --branch`。
- 每次推送前运行测试和公开泄漏审计。
- 每次跨工作树同步前先确认源和目标目录。
- 每次遇到 GitHub 拒绝、secret scanning、非快进、冲突时先停下分析，不要强行推进。
- 文档和治理材料主要用中文；代码、注释、docstring 用英文。

---

## 2. 当前本地布局和角色

截至 2026-06-05，机器上有三个相关目录：

```text
D:/OneDrive - SAIF/PhD3/StataFlow/
D:/OneDrive - SAIF/PhD3/StataFlow_public/
D:/OneDrive - SAIF/PhD3/StataFlow_open_source/
```

### 2.1 `StataFlow`

路径：

```text
D:/OneDrive - SAIF/PhD3/StataFlow
```

角色：

- 内部完整开发工作树。
- 包含治理文档、架构文档、审计材料、golden tests、Stata artifacts、workspace 当前任务材料等。
- 当前主要工作分支是 `fix/v1.0.1-hotfix`。
- 本地 `dev` 分支也指向同一内部开发线。

当前已知状态：

```text
HEAD: 6a0750e docs: record migration execution status
branch: fix/v1.0.1-hotfix
local dev: 6a0750e
```

远端：

```text
origin          https://github.com/ZhenHaoFu810/StataFlow.git
statapy-legacy  https://github.com/ZhenHaoFu810/Statapy.git
```

注意：

- `origin` 是 StataFlow 的公开 GitHub 仓库。
- `statapy-legacy` 是历史遗留远端，不得误推。
- `dev` 当前只应视为本地内部开发分支，不得直接推到公开 `origin`。

### 2.2 `StataFlow_public`

路径：

```text
D:/OneDrive - SAIF/PhD3/StataFlow_public
```

角色：

- 公开 `main` 的本地 worktree。
- 只用于检查、修复、验证和推送公开发布线。
- 不包含内部治理、审计、golden tests、workspace、scripts、Stata artifacts。

当前已知状态：

```text
HEAD: b599187 test: include public rdrobust fixtures
branch: public-main
tracks: origin/main
```

公开远端：

```text
origin/main: b599187
```

注意：

- 本地分支名叫 `public-main`，但推送目标是远端 `main`。
- 推送命令应使用：

```powershell
git -c safe.directory='D:/OneDrive - SAIF/PhD3/StataFlow_public' push origin public-main:main
```

### 2.3 `StataFlow_open_source`

路径：

```text
D:/OneDrive - SAIF/PhD3/StataFlow_open_source
```

角色：

- 旧的公开导出仓库。
- 当前只作为迁移备份保留。
- 不再作为主要公开开发工作树。

处理规则：

- 不要删除。
- 不要继续以它作为主要开发入口。
- 只有在用户明确要求、并确认 `StataFlow_public` 和远端 `main` 稳定至少 2-4 周后，才考虑归档或删除。

---

## 3. 当前远端分支事实

截至 2026-06-05：

```text
origin/main exists: b5991871628dff6f13299e0b5f1e8731ddcc9d91
origin/dev does not exist
```

这是有意状态，不是遗漏。

原因：

- 尝试推送完整内部 `dev` 到 `https://github.com/ZhenHaoFu810/StataFlow.git` 时，GitHub push protection 阻止了推送。
- 被拦截原因是历史提交中存在 `Pypi token.txt`，GitHub 识别为 PyPI API Token。
- GitHub 仓库没有“分支级别私有/公开”隔离。如果仓库是公开的，任何推到该仓库的 `dev` 分支也会公开可见。
- 内部 `dev` 包含治理、审计、golden、workspace、scripts 等不应公开的内容。

结论：

- 公开 GitHub 仓库只承载 `main`。
- 完整内部 `dev` 只能留在本地，或推到确认私有且完成 secret-history 清洗的私有远端。
- 不得绕过 GitHub 给出的 unblock-secret 链接。

---

## 4. Agent 每次接手时的启动流程

任何 Agent 开始工作前，都必须按顺序执行以下检查。

### 4.1 读取项目规则

先阅读：

```text
AGENTS.md
docs/project-charter.md
docs/architecture/overview.md
docs/architecture/public-api.md
docs/architecture/stata-compatibility.md
docs/operations/executor-playbook.md
docs/operations/review-gates.md
docs/roadmap.md
docs/backlog.md
docs/operations/migrate-to-monorepo-branches.md
docs/operations/agent-project-management.md
```

如果任务涉及本轮 revalidation，还要读：

```text
docs/audit/revalidation-v1.1/
```

### 4.2 检查工作树和分支

在内部工作树：

```powershell
Set-Location "D:/OneDrive - SAIF/PhD3/StataFlow"
git -c safe.directory='D:/OneDrive - SAIF/PhD3/StataFlow' status --short --branch
git -c safe.directory='D:/OneDrive - SAIF/PhD3/StataFlow' branch --show-current
git -c safe.directory='D:/OneDrive - SAIF/PhD3/StataFlow' log --oneline --decorate -5
git -c safe.directory='D:/OneDrive - SAIF/PhD3/StataFlow' remote -v
git -c safe.directory='D:/OneDrive - SAIF/PhD3/StataFlow' worktree list
```

在公开 worktree：

```powershell
Set-Location "D:/OneDrive - SAIF/PhD3/StataFlow_public"
git -c safe.directory='D:/OneDrive - SAIF/PhD3/StataFlow_public' status --short --branch
git -c safe.directory='D:/OneDrive - SAIF/PhD3/StataFlow_public' branch --show-current
git -c safe.directory='D:/OneDrive - SAIF/PhD3/StataFlow_public' log --oneline --decorate -5
```

### 4.3 检查远端分支

```powershell
Set-Location "D:/OneDrive - SAIF/PhD3/StataFlow"
git -c safe.directory='D:/OneDrive - SAIF/PhD3/StataFlow' ls-remote --heads origin main dev
```

正确预期：

- `main` 存在。
- `dev` 通常不存在。
- 如果突然出现 `origin/dev`，必须停下检查它是否错误公开了内部内容。

### 4.4 判断当前任务应该在哪个工作树做

使用以下规则：

| 任务类型 | 工作目录 |
|----------|----------|
| 内部开发、算法、golden tests、Stata 验证、审计文档、架构文档 | `StataFlow` |
| 公开 README、公开用户文档、公开 CI、公开源码发布修复 | 通常先在 `StataFlow` 修改，再同步到 `StataFlow_public` |
| 只验证公开分支是否可安装、可测试、可发布 | `StataFlow_public` |
| 历史备份检查 | `StataFlow_open_source`，只读优先 |
| 任何删除、归档、历史重写、远端重命名 | 先向用户明确说明风险并获得确认 |

---

## 5. 分支管理规范

### 5.1 内部分支

内部当前开发线：

```text
fix/v1.0.1-hotfix
dev
```

`fix/v1.0.1-hotfix` 是当前 checkout 分支。`dev` 是本地指针，用来表示完整内部开发线。

如果完成内部文档或代码提交后需要同步本地 `dev` 指针：

```powershell
Set-Location "D:/OneDrive - SAIF/PhD3/StataFlow"
git -c safe.directory='D:/OneDrive - SAIF/PhD3/StataFlow' branch -f dev HEAD
```

不要推送：

```powershell
git push origin dev
```

除非已经完成：

1. 目标远端确认是私有仓库，或用户明确批准完整内部树公开。
2. 历史 secret 扫描通过。
3. 用户明确要求推送。

### 5.2 公开分支

公开远端分支：

```text
origin/main
```

本地公开 worktree 分支：

```text
public-main
```

从公开 worktree 推送到远端 main：

```powershell
Set-Location "D:/OneDrive - SAIF/PhD3/StataFlow_public"
git -c safe.directory='D:/OneDrive - SAIF/PhD3/StataFlow_public' push origin public-main:main
```

推送前必须满足：

- `git status --short --branch` 干净，或只有计划内公开变更。
- 公开测试通过。
- 泄漏审计无输出。
- 没有新 secret。
- 没有非快进风险；如果 push 被拒绝，要 fetch/merge 后重新测试。

### 5.3 不要使用本地旧 `main`

内部 repo `StataFlow` 里可能有旧的本地 `main` 指针。不要假设它等于公开 `origin/main`。

检查：

```powershell
git -c safe.directory='D:/OneDrive - SAIF/PhD3/StataFlow' show-ref --heads
```

如果需要公开视图，使用 `StataFlow_public`，不要在内部工作树直接 checkout `main`。

---

## 6. 提交规范

### 6.1 提交前检查

每次 commit 前：

```powershell
git status --short --branch
git diff --stat
git diff --name-status
```

如果有用户或其他 Agent 的无关修改：

- 不要 revert。
- 不要纳入自己的提交。
- 只 stage 与当前任务相关的文件。

### 6.2 提交命名

推荐格式：

```text
docs: ...
test: ...
fix: ...
feat: ...
chore: ...
sync: ...
```

示例：

```text
docs: record migration execution status
test: include public rdrobust fixtures
sync: align public main with v1.1.0 validation fixes
fix: align did_imputation aggregate sample
```

### 6.3 内部提交

在 `StataFlow`：

```powershell
Set-Location "D:/OneDrive - SAIF/PhD3/StataFlow"
git add <files>
git commit -m "docs: update agent project management runbook"
git branch -f dev HEAD
```

默认不要 push。

### 6.4 公开提交

在 `StataFlow_public`：

```powershell
Set-Location "D:/OneDrive - SAIF/PhD3/StataFlow_public"
git add <public-files>
git commit -m "docs: update public user guide"
```

然后先验证，再 push。

---

## 7. 公开分支内容边界

### 7.1 公开白名单

公开 `main` 可以包含：

```text
README.md
README.zh-CN.md
LICENSE
pyproject.toml
.gitignore
VALIDATION.md
.github/workflows/ci.yml
src/stataflow/
examples/
tests/
tests/data/rdrobust_senate.dta
tests/data/rdrobust_senate_with_z.dta
research/data/public/
research/results/validation/
docs/USER_GUIDE.md
docs/USER_GUIDE.zh-CN.md
docs/cookbook.md
docs/cookbook.zh-CN.md
```

注意：

- `.gitignore` 全局忽略 `*.dta`。
- 公开测试依赖两个 RD fixture，因此这两个 `.dta` 文件必须用 `git add -f` 精确纳入。

命令：

```powershell
git add -f tests/data/rdrobust_senate.dta tests/data/rdrobust_senate_with_z.dta
```

### 7.2 公开禁止路径

公开 `main` 禁止包含：

```text
AGENTS.md
CLAUDE.md
.claude/
docs/architecture/
docs/audit/
docs/operations/
docs/research/
docs/tasks/
docs/project-charter.md
docs/backlog.md
scripts/
stata/
workspace/
tests/golden/
research/vendor/
session_restore/
debug_*.py
extract_cdsy.py
golden_test_results.txt
*.zip
*token*
*secret*
*.pem
*.key
```

### 7.3 泄漏审计命令

在公开 worktree 执行：

```powershell
Set-Location "D:/OneDrive - SAIF/PhD3/StataFlow_public"
git -c safe.directory='D:/OneDrive - SAIF/PhD3/StataFlow_public' ls-files | rg '^(AGENTS\.md$|CLAUDE\.md$|\.claude/|docs/(architecture|audit|operations|research|tasks)/|docs/(project-charter|backlog)\.md$|scripts/|stata/|workspace/|tests/golden/|research/vendor/|session_restore/|debug_.*\.py$|extract_cdsy\.py$|golden_test_results\.txt$|.*\.zip$)'
```

正确结果：

```text
无输出，命令退出码可为 1
```

`rg` 没找到匹配时退出码为 1，这是正常的。

再检查 secret 命名：

```powershell
git -c safe.directory='D:/OneDrive - SAIF/PhD3/StataFlow_public' ls-files | rg -i '(token|secret|credential|password|\.env|\.pem|\.key)'
```

正确结果：

```text
无输出，或只有经人工确认的非敏感公开文档文本
```

---

## 8. 标准测试和验证流程

### 8.1 内部快速测试

在 `StataFlow`：

```powershell
Set-Location "D:/OneDrive - SAIF/PhD3/StataFlow"
$env:PYTHONPATH='D:\OneDrive - SAIF\PhD3\StataFlow\src'
pytest tests/ -v --ignore=tests/golden/ --ignore=tests/benchmarks/
```

### 8.2 内部 golden dual-run

需要本地 Stata 17：

```powershell
Set-Location "D:/OneDrive - SAIF/PhD3/StataFlow"
$env:PYTHONPATH='D:\OneDrive - SAIF\PhD3\StataFlow\src'
pytest tests/golden/ -v
```

仅当任务需要 Stata 对齐、golden 证据、审计修复时运行。

### 8.3 公开测试

在 `StataFlow_public`：

```powershell
Set-Location "D:/OneDrive - SAIF/PhD3/StataFlow_public"
$env:PYTHONPATH='D:\OneDrive - SAIF\PhD3\StataFlow_public\src'
pytest tests/ -q --ignore=tests/golden/ --ignore=tests/benchmarks/
```

当前正确结果：

```text
299 passed
```

可能有 warnings：

- pandas `numexpr` / `bottleneck` 版本 warning。
- DID `first_treat <= 0` encoding warning。
- sklearn logistic deprecation warning。
- multiway cluster fallback runtime warning。
- rdplot covs warning。

这些 warning 当前可接受，但如果新增 warning 与业务逻辑、公开路径、secret、文件缺失有关，必须调查。

### 8.4 公开 example smoke

在 `StataFlow_public`：

```powershell
Set-Location "D:/OneDrive - SAIF/PhD3/StataFlow_public"
$env:PYTHONPATH='D:\OneDrive - SAIF\PhD3\StataFlow_public\src'
python examples/demo_regress.py
python examples/demo_reghdfe.py
python examples/demo_ppmlhdfe.py
python examples/demo_ivregress_2sls.py
```

四个命令必须 exit code 0。

`demo_ppmlhdfe.py` 可能输出 `IRLS did not converge` warning；当前这不是 smoke failure。

---

## 9. 公开同步流程

公开同步是高风险操作。不要随手复制整个内部目录。

### 9.1 何时需要同步公开分支

以下情况需要同步：

- 内部源码修复需要发布到公开 `main`。
- 公开测试需要跟上源码行为。
- README、用户文档、公开验证证据需要更新。
- PyPI release 前准备公开分支。

以下情况不需要同步：

- 只更新内部审计文档。
- 只更新 `docs/architecture/`、`docs/operations/`。
- 只更新 `tests/golden/`。
- 只更新 `workspace/`。

### 9.2 手动同步最小安全流程

1. 确认内部工作树干净或提交完成：

```powershell
Set-Location "D:/OneDrive - SAIF/PhD3/StataFlow"
git status --short --branch
```

2. 确认公开 worktree 干净：

```powershell
Set-Location "D:/OneDrive - SAIF/PhD3/StataFlow_public"
git status --short --branch
git fetch origin main
```

如果远端有新提交：

```powershell
git merge origin/main --no-edit
```

合并后必须重新测试。

3. 只复制公开允许的目录或文件。

示例：同步源码和公开测试：

```powershell
$src='D:\OneDrive - SAIF\PhD3\StataFlow'
$dst='D:\OneDrive - SAIF\PhD3\StataFlow_public'

Copy-Item -LiteralPath (Join-Path $src 'src\stataflow') -Destination (Join-Path $dst 'src') -Recurse -Force
Copy-Item -Path (Join-Path $src 'tests\*.py') -Destination (Join-Path $dst 'tests') -Force
```

不要复制：

```text
docs/
scripts/
stata/
workspace/
tests/golden/
```

如果确实需要公开 docs，只复制白名单中的用户文档。

4. 检查 diff：

```powershell
Set-Location "D:/OneDrive - SAIF/PhD3/StataFlow_public"
git diff --name-status
git diff --stat
```

5. 泄漏审计。

6. 公开测试。

7. example smoke。

8. commit。

9. push。

### 9.3 处理公开测试文件依赖内部脚本的问题

公开 `main` 不允许有 `scripts/`。

如果从内部复制了以下测试：

```text
tests/test_export_safety.py
tests/test_validation_summary.py
```

必须确认它们是否依赖 `scripts/`。截至 2026-06-05：

- `test_export_safety.py` 依赖 `scripts/release/export_open_source.py`。
- `test_validation_summary.py` 依赖 `scripts/validation/`。

这两个测试不适合公开 `main`，除非相关脚本也被重新设计为公开安全内容。不要为了让测试通过而把整个 `scripts/` 目录带进公开分支。

### 9.4 处理 `.dta` fixture

如果公开 RD 测试失败并报：

```text
FileNotFoundError: tests/data/rdrobust_senate.dta
FileNotFoundError: tests/data/rdrobust_senate_with_z.dta
```

说明公开 worktree 缺少被 `.gitignore` 忽略的 fixture。

正确修复：

```powershell
git add -f tests/data/rdrobust_senate.dta tests/data/rdrobust_senate_with_z.dta
git commit -m "test: include public rdrobust fixtures"
```

不要移除 `.gitignore` 中全局 `*.dta` 规则，除非用户明确要求重新设计数据管理策略。

---

## 10. GitHub 交互规范

### 10.1 推送公开 main

只从 `StataFlow_public` 推送公开 `main`：

```powershell
Set-Location "D:/OneDrive - SAIF/PhD3/StataFlow_public"
git status --short --branch
git push origin public-main:main
```

如果被拒绝：

```text
rejected: fetch first
```

不要强推。

正确处理：

```powershell
git fetch origin main
git log --oneline --decorate --left-right --cherry-pick public-main...origin/main
git merge origin/main --no-edit
```

然后重新运行：

```powershell
$env:PYTHONPATH='D:\OneDrive - SAIF\PhD3\StataFlow_public\src'
pytest tests/ -q --ignore=tests/golden/ --ignore=tests/benchmarks/
```

通过后再 push。

### 10.2 不要推送内部 dev 到公开 origin

禁止：

```powershell
git push origin dev
```

除非全部满足：

- 用户明确要求。
- 仓库确认是私有，或用户明确批准公开完整内部树。
- 历史 secret 扫描通过。
- 当前分支泄漏审计通过。

历史 secret 检查：

```powershell
Set-Location "D:/OneDrive - SAIF/PhD3/StataFlow"
git log --all -- "Pypi token.txt"
git ls-tree -r --name-only dev | rg -i '(token|secret|credential|password|\.env|\.pem|\.key)'
```

如果 GitHub push protection 报 secret：

- 停止。
- 不要点击 unblock。
- 不要 force push。
- 不要删除当前工作树。
- 记录 commit、path、secret 类型。
- 告知用户需要单独做 secret rotation 和 history rewrite。

### 10.3 GitHub CLI

如果使用 `gh`：

```powershell
gh repo view ZhenHaoFu810/StataFlow --json visibility,nameWithOwner,url
gh pr status
gh run list --limit 10
```

如果 `gh` 请求失败，先判断是网络、认证、代理还是 GitHub API 问题。不要因此改用危险 Git 操作。

### 10.4 Pull Request 策略

推荐未来流程：

- 公开 `main` 保护。
- 所有公开发布变化通过 PR。
- CI 必须包含公开结构审计。
- 禁止 force push。
- 禁止直接在 GitHub 网页编辑公开分支中的复杂文件，除非是 README 小修。

---

## 11. Secret 和敏感信息管理

### 11.1 已知历史风险

GitHub push protection 已报告：

```text
PyPI API Token
commit: 9ddae39000076e97191b2ed693282eb4ab518c35
path: Pypi token.txt:1
```

这说明内部历史里存在敏感文件。

后续 Agent 必须假设：

- 该 token 已经泄露风险存在。
- 不得把包含该历史的分支推到公开远端。
- 需要用户自行确认 PyPI token 是否已 revoke/rotate。

### 11.2 搜索敏感文件

当前树文件名检查：

```powershell
git ls-files | rg -i '(token|secret|credential|password|\.env|\.pem|\.key)'
```

历史路径检查：

```powershell
git log --all --name-only --pretty=format: | rg -i '(token|secret|credential|password|\.env|\.pem|\.key)' | Sort-Object -Unique
```

不要把搜索结果中的敏感内容原文粘贴到公开文档或聊天里。

### 11.3 如果必须清洗历史

历史清洗是单独高风险任务，不能顺手做。

必须先：

1. 创建 bundle 备份。
2. 确认所有协作者暂停 push。
3. 列出要移除的路径和 commit。
4. 选择工具，例如 `git filter-repo`。
5. 清洗后重新跑测试。
6. 确认 secret 已 revoke。
7. 明确告知所有协作者需要重新 clone 或 reset。

未得到用户明确指令，不执行。

---

## 12. 回滚和事故处理

### 12.1 如果公开 push 错误

先记录：

```powershell
git ls-remote --heads origin main
git log --oneline --decorate -10
```

不要立刻 force push。

判断错误类型：

- 只是公开测试失败：提交修复，再 push。
- 带入内部路径：如果尚未被他人拉取，可讨论 revert 或受控历史处理；默认先用普通 commit 删除并补 CI 审计。
- 带入 secret：立刻停止，通知用户，按 secret incident 处理。

### 12.2 如果误改内部工作树

先看：

```powershell
git status --short
git diff --stat
```

不要直接 `git reset --hard`。

如果是自己刚改且确认不要：

```powershell
git restore -- <file>
```

只有在用户明确要求时才使用更强命令。

### 12.3 如果 worktree 损坏

查看：

```powershell
Set-Location "D:/OneDrive - SAIF/PhD3/StataFlow"
git worktree list
```

如果要移除公开 worktree：

```powershell
git worktree remove "../StataFlow_public"
```

不要删除 `StataFlow` 主目录。

### 12.4 如果 `StataFlow_open_source` 与 `StataFlow_public` 不一致

默认以 `StataFlow_public` 和远端 `origin/main` 为准。

`StataFlow_open_source` 是备份，不再是权威公开线。

---

## 13. 推荐的日常开发流程

### 13.1 内部代码开发

1. 在 `StataFlow` 工作。
2. 阅读相关架构、审计、research 文档。
3. 写或更新测试。
4. 最小实现。
5. 跑非 golden 测试。
6. 如涉及 Stata 对齐，跑 golden。
7. 更新 `workspace/current-task/REPORT.md`。
8. commit。
9. 更新本地 `dev` 指针。
10. 如需要公开发布，进入公开同步流程。

### 13.2 内部文档开发

1. 在 `StataFlow` 工作。
2. 修改 `docs/architecture/`、`docs/operations/`、`docs/audit/` 等内部文档。
3. 不同步到公开 `main`，除非文档属于公开白名单。
4. commit。
5. 更新本地 `dev` 指针。

### 13.3 公开发布修复

1. 先在内部确认修复来源。
2. 把公开允许文件同步到 `StataFlow_public`。
3. 审计公开路径。
4. 跑公开测试。
5. 跑 example smoke。
6. commit。
7. push `public-main:main`。
8. 如果 push 非快进，fetch/merge/retest/push。

---

## 14. 常用命令速查

### 14.1 内部状态

```powershell
Set-Location "D:/OneDrive - SAIF/PhD3/StataFlow"
git status --short --branch
git log --oneline --decorate -5
git remote -v
git worktree list
```

### 14.2 公开状态

```powershell
Set-Location "D:/OneDrive - SAIF/PhD3/StataFlow_public"
git status --short --branch
git log --oneline --decorate -5
git diff --stat
```

### 14.3 远端状态

```powershell
Set-Location "D:/OneDrive - SAIF/PhD3/StataFlow"
git ls-remote --heads origin main dev
```

### 14.4 公开测试

```powershell
Set-Location "D:/OneDrive - SAIF/PhD3/StataFlow_public"
$env:PYTHONPATH='D:\OneDrive - SAIF\PhD3\StataFlow_public\src'
pytest tests/ -q --ignore=tests/golden/ --ignore=tests/benchmarks/
```

### 14.5 公开泄漏审计

```powershell
git ls-files | rg '^(AGENTS\.md$|CLAUDE\.md$|\.claude/|docs/(architecture|audit|operations|research|tasks)/|docs/(project-charter|backlog)\.md$|scripts/|stata/|workspace/|tests/golden/|research/vendor/|session_restore/|debug_.*\.py$|extract_cdsy\.py$|golden_test_results\.txt$|.*\.zip$)'
```

### 14.6 推公开 main

```powershell
Set-Location "D:/OneDrive - SAIF/PhD3/StataFlow_public"
git push origin public-main:main
```

### 14.7 更新本地 dev 指针

```powershell
Set-Location "D:/OneDrive - SAIF/PhD3/StataFlow"
git branch -f dev HEAD
```

---

## 15. Agent 交接报告模板

每次完成较大任务后，在最终回复或 `workspace/current-task/REPORT.md` 中记录：

```text
任务：

工作目录：

起始分支和提交：

结束分支和提交：

修改文件：

测试：

公开分支审计：

GitHub 操作：

未完成事项：

风险：

下一个 Agent 应先检查：
```

示例：

```text
任务：同步公开 main 并建立公开 worktree
工作目录：StataFlow, StataFlow_public
起始提交：12651c4 / 4f7aa74
结束提交：6a0750e / b599187
测试：public pytest 299 passed; examples 4/4 passed
公开分支审计：禁止路径 rg 无输出
GitHub 操作：pushed public-main:main to b599187
未完成事项：dev 未推送，等待私有远端或历史 secret 清洗
风险：历史 PyPI token commit 仍存在于内部本地历史
```

---

## 16. 当前待办

以下事项仍未完成，后续 Agent 不得误认为已完成：

- 完整内部 `dev` 远端尚未建立。
- 历史 PyPI token 仍需用户确认 revoke/rotate，并决定是否做 history rewrite。
- 公开 CI 还应加入更强的 public-structure audit。
- 公开同步脚本 `scripts/release/sync_public.ps1` 尚未设计；即使未来创建，也不得出现在公开 `main`。
- `StataFlow_open_source` 仍是备份目录，暂不删除。
- 需要长期决定：内部开发线留本地、推私有远端，还是创建单独 private repository。

---

## 17. 最终判断规则

如果后续 Agent 不确定某个操作是否安全，使用以下判断：

1. 会不会把内部内容推到公开 `main`？如果会，停止。
2. 会不会触碰远端历史、force push、删除目录、重写 commit？如果会，停止并询问用户。
3. 会不会绕过 GitHub secret protection？如果会，停止。
4. 是否已经跑了公开测试和泄漏审计？如果没有，不推公开 `main`。
5. 是否明确知道当前目录是 `StataFlow` 还是 `StataFlow_public`？如果不知道，先 `pwd` 和 `git status`。

保守地停下，比错误推送更好。
