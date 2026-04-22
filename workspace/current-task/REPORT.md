# Open-Source Export and CI Root Cause Fix — 完成报告

**日期：** 2026-04-21
**任务：** `open-source-export-and-ci-root-cause-fix`
**运行者：** Claude Code
**状态：** 完成

---

## 1. 项目开源范围审计与决策

已完成 `docs/operations/open-source-scope-audit.md`，对 `StataFlow` 与 `StataFlow_open_source` 之间的每一个目录和文件进行了显式 Open/Closed 判定。

**核心原则：**
- `StataFlow` 是唯一的维护源，`StataFlow_open_source` 是可复现的导出目标。
- 新文件在未显式白名单的目录中，默认视为 **Closed**，防止内部材料意外泄露。
- 白名单按目录、特定文件、数据目录、测试文件四类管理；黑名单在复制后执行，捕获生成产物和密钥。

**关键决策：**
- `src/stataflow/`、`examples/`、`docs/architecture/`、`docs/command-support-matrix/`、`docs/release/`、`docs/validation/`、`docs/adr/` 全部开放。
- `docs/audit/`、`docs/qa/`、`docs/tasks/`、`docs/research/`、`docs/phases/` 等内部开发材料关闭。
- `tests/golden/` 关闭（需要本地 Stata 17，不适合干净开源包）。
- `stata/output/` 和 `stata/cases/` 关闭（生成产物）。
- `tests/test_rdrobust.py` 对 `stata/output/rdrobust_senate_with_z.dta` 的依赖被识别为 bug，将在后续修复。

---

## 2. 导出机制实现

新增三个文件构成完整的可复现导出流程：

| 文件 | 作用 |
|------|------|
| `scripts/release/open_source_manifest.yml` | YAML 格式的白名单/黑名单规则，是导出的唯一权威配置。 |
| `scripts/release/export_open_source.py` | Python 导出脚本（核心实现），解析 manifest，计算 SHA-256 增量复制，清理孤儿文件和空目录。 |
| `scripts/release/export_open_source.ps1` | PowerShell 薄包装器，调用 Python 脚本，保持与任务指令的接口一致。 |
| `docs/operations/open-source-export.md` | 导出机制的设计文档和使用说明。 |

**导出脚本特性：**
- 支持 `--dry-run` 预览、 `--force` 强制覆盖、 `--target-root` 自定义目标路径。
- 基于 SHA-256 的增量复制，未变更文件跳过。
- 自动删除目标端不再属于白名单的孤儿文件（保留 `.git/` 和 `dist/`）。
- 自动清理空目录。

---

## 3. 中文 Markdown 编码乱码修复

**根因：** UTF-8 的 em-dash/en-dash 字节序列被 GBK 误解析后重新保存为 UTF-8，产生 `鈥` (U+9225) 乱码。

**修复范围：** 对以下所有导出文件执行了全局替换：
- `README.md`
- `docs/release/open-source-alpha-status.md`
- `docs/command-support-matrix/*.md`（全部 10 个命令 + README）
- `src/stataflow/__init__.py`
- `docs/cookbook.md`

**替换规则：**
- `鈥?` → `— `（em-dash + 空格）
- `鈥攗` → `—u`（README 中的 `directly—use`）
- `1— ` → `1–2 `（表示 1 到 2 个分类 FE 的 en-dash）

**同时从 `StataFlow_open_source` 反向迁移了 4 份仅存在于开源仓的公共文档到主仓：**
- `README.zh-CN.md`
- `docs/USER_GUIDE.md`
- `docs/USER_GUIDE.zh-CN.md`
- `docs/cookbook.zh-CN.md`

**验证：** 导出文件范围内已无 `鈥` (U+9225) 残留。

---

## 4. Python 3.11 CI 根因修复

**根因：** `tests/test_rdrobust.py` 中的两个测试用例读取了 `stata/output/rdrobust_senate_with_z.dta`，而该路径属于关闭目录，在开源仓中不存在，导致 `FileNotFoundError`。

**修复：**
1. 将 `stata/output/rdrobust_senate_with_z.dta` 复制到 `research/data/public/rdrobust_senate_with_z.dta`，使其成为公开的测试数据。
2. 将 `tests/test_rdrobust.py` 中两处路径从 `stata/output/rdrobust_senate_with_z.dta` 替换为 `research/data/public/rdrobust_senate_with_z.dta`。
3. 在 `.github/workflows/ci.yml` 的 strategy 中加入 `fail-fast: false`，确保 Python 3.10/3.11/3.12 全部运行，不因单个版本失败而中断矩阵。

**验证：**
- 主仓 `tests/test_rdrobust.py`：17 passed。
- 导出后的 `StataFlow_open_source` 完整测试套件：165 passed, 0 failed。

---

## 5. 导出执行与验证

执行了实际导出：

```bash
python scripts/release/export_open_source.py --force
```

**结果：**
- Copied / updated：28 个文件（156,301 字节）
- Unchanged：135 个文件
- Removed orphaned：32 个文件（包括 `CLAUDE.md`、`.pytest_cache`、`.egg-info`、过时的 `docs/OPEN_SOURCE_PACKAGE_MANIFEST.md` 等）

在 `StataFlow_open_source` 运行完整非 golden 测试：

```bash
pytest tests/ -v --ignore=tests/golden/
```

**结果：165 passed, 0 failed。**

---

## 6. 第二轮精简（2026-04-21 追加）

根据用户反馈，开源版本进一步精简为：源码 + 介绍 + 使用指南 + 必要 demo/示例 + validation 结果。

### 6.1 从白名单移除的目录和文件

| 移除项 | 原因 |
|--------|------|
| `docs/architecture/` | 内部架构文档，面向开发者而非用户 |
| `docs/release/` | 内部发布状态管理 |
| `docs/validation/` | 内部验证策略与证据矩阵文档 |
| `docs/adr/` | 内部架构决策记录 |
| `docs/operations/` | 内部运维文档 |
| `docs/project-charter.md` | 内部项目章程 |
| `research/data/public/` | 开发期 AI 学习数据，非用户必要 |
| `research/vendor/.../rdrobust_senate.dta` | 随数据迁移到测试目录 |

保留的 docs 内容：
- `docs/command-support-matrix/`（命令支持矩阵，用户必看）
- `docs/cookbook.md` / `docs/cookbook.zh-CN.md`
- `docs/USER_GUIDE.md` / `docs/USER_GUIDE.zh-CN.md`

### 6.2 测试数据迁移

将两个 rdrobust 测试数据文件从 `research/` 迁移到 `tests/data/`，消除非测试目录依赖：
- `tests/data/rdrobust_senate.dta`
- `tests/data/rdrobust_senate_with_z.dta`

同步修改 `tests/test_rdrobust.py` 中的读取路径。

### 6.3 文档内容清理

从所有导出文档中移除了指向以下已关闭目录的链接和引用：
- `docs/validation/`
- `docs/release/`
- `docs/architecture/`
- `docs/research/`
- `research/data/public/`

清理的文件包括：`README.md`、`README.zh-CN.md`、`docs/USER_GUIDE.md`、`docs/USER_GUIDE.zh-CN.md`、`docs/cookbook.md`、`docs/command-support-matrix/*.md`。

同时修复了：
- `README.zh-CN.md` 中的 airfare.csv 示例改为合成数据（避免依赖已移除的公开数据集）
- `docs/cookbook.zh-CN.md` 标题中的旧名 `Stata2Python` → `StataFlow`
- 所有从 `StataFlow_open_source` 复制过来的文档中的绝对路径链接（`D:/OneDrive...`）替换为相对路径

### 6.4 第二轮导出验证

执行导出后，`StataFlow_open_source` 的 docs 目录仅保留 18 个文件（USER_GUIDE ×2 + cookbook ×2 + command-support-matrix ×14），research 目录仅保留 validation 结果产物。

完整非 golden 测试：**165 passed, 0 failed**。

---

## 7. 遗留说明

- `docs/validation/validation-policy.md`、`docs/validation/evidence-matrix.md`、`docs/validation/overview.md` 等中文 Markdown 文件在主仓历史版本中曾被严重损坏，已从 `StataFlow_open_source` 的干净版本反向迁移回主仓，并修复了编码问题。但 `docs/validation/` 整体不再进入开源导出。
- `docs/project-charter.md` 主仓工作树版本曾损坏，通过 `git show HEAD:docs/project-charter.md` 恢复为干净 UTF-8 版本。该文件也不再进入开源导出。
- `src/stataflow/__init__.py` 在 git HEAD 中不存在（主仓 HEAD 仍为 `src/statapy/` 包名），该文件是在工作树中新增且未提交的，因此直接手动修复了 docstring 乱码。
- 内部/关闭目录（`docs/audit/`、`docs/research/`、`docs/tasks/` 等）中仍有 `鈥` 乱码，但这些文件不进入开源导出，不影响对外发布。

---

## 8. 结论

- 开源边界审计完成，决策写入 `docs/operations/open-source-scope-audit.md`（内部维护）。
- 可复现导出机制完成，支持增量同步和孤儿清理。
- 全部导出中文 Markdown 的 `鈥` 乱码已修复，UTF-8 编码稳定。
- 开源版本已精简为用户导向结构：源码 + 示例 + 用户文档 + 命令矩阵 + validation 结果 + 测试。
- 导出后的开源镜像通过 165 项测试，0 失败，具备持续集成能力。
- Python 3.11 CI 失败根因已消除，CI 矩阵加入 `fail-fast: false`。
- 导出后的开源镜像通过 165 项测试，0 失败，具备持续集成能力。
