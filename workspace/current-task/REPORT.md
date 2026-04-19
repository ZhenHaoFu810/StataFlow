# 发布任务包 001 报告：首次开源 Alpha 修缮

**Date:** 2026-04-19
**Executor:** Claude Code
**Task:** `docs/tasks/release-package-001-first-open-source-alpha-remediation.md`

---

## 1. 本轮修缮目标

本轮不新增任何估计器功能，只做首次开源发布面修缮：
- 清除 release-blocking 硬阻塞
- 整理仓库根目录卫生
- 补齐最低工程化信号（CI、LICENSE、包元数据）

---

## 2. 修掉的 release-blocking 问题

### 2.1 新增 LICENSE 文件

- **新增文件：** `LICENSE`（MIT License）
- **理由：** MIT 是宽松、清晰、适合首次开源的许可证，对学术/商业使用都友好。
- **同步位置：**
  - `pyproject.toml` 中新增 `license = {text = "MIT"}`
  - `pyproject.toml` 中 classifiers 包含 `"License :: OSI Approved :: MIT License"`

### 2.2 补齐 `pyproject.toml` 元数据

补齐前只有 `name`、`version`、`description`、`requires-python`、`dependencies`。

补齐后新增字段：
- `readme = "README.md"`
- `license = {text = "MIT"}`
- `authors = [{name = "Zhenhao Fu", email = "zhenhaofu2001@gmail.com"}]`
- `keywords`（econometrics, stata, regression, fixed-effects, panel-data）
- `classifiers`（Alpha, Science/Research, MIT, Python 3.10/3.11/3.12）
- `[project.urls]`（Homepage, Repository, Issues）

### 2.3 统一 Python 版本口径

- **问题：** README 写 `Python 3.9+`，`pyproject.toml` 要求 `>=3.10`
- **决策：** 统一提升到 `3.10+`
- **理由：** 代码中已使用 `list[str]` 等 Python 3.10+ 类型注解语法，降级到 3.9 有风险。
- **同步位置：**
  - `pyproject.toml`：`requires-python = ">=3.10"`
  - `README.md`：`Requirements: Python 3.10+, NumPy, pandas, SciPy.`

### 2.4 修正 release-facing 错误链接

- **问题：** `docs/release/open-source-alpha-status.md` 第 90 行把反馈 issue 指向了 `anthropics/claude-code`
- **修复：** 替换为正确的仓库 issue 地址：`https://github.com/ZhenhaoFu/Stata2Python/issues`

---

## 3. 根目录文件迁移与清理

### 3.1 迁移的内部脚本

以下 8 个根目录 `.py` 文件迁移到 `scripts/internal/`：

- `find_mpdta.py`
- `run_did_realdata_stata.py`
- `run_wagepan2.py`
- `run_wagepan3.py`
- `run_wagepan_check.py`
- `test_ezunem_didimp.py`
- `test_jtrain_didimp.py`
- `test_runner_simple.py`

**原则：** 这些脚本仍有研究/调试价值，不直接删除；通过迁移到明确子目录，根目录只保留正式入口。

### 3.2 删除的日志文件

- `rdrobust_bwselect.log`
- `rdrobust_gen_z.log`

`.gitignore` 已有 `*.log`，这些文件本就不应进入版本控制。

### 3.3 更新 `src/statapy/__init__.py`

- **原内容：** `# Stata2Python - Phase 0 Bootstrap`
- **新内容：** 正式项目描述，不再保留原型期文案

### 3.4 更新 `.gitignore`

新增对 `scripts/internal/` 的日志和 `__pycache__` 的忽略规则。

---

## 4. 新增 CI / release-facing 文件

### 4.1 `.github/workflows/ci.yml`

新增基础 CI workflow，覆盖：
- Python 3.10 / 3.11 / 3.12 矩阵
- 安装包及开发依赖
- import smoke（`import statapy`）
- unit tests（排除 golden tests：`--ignore=tests/golden/`）
- example smoke（4 个 demo 脚本）
- wheel 构建验证

**局限说明：**
- golden dual-run tests 依赖本地 Stata 17 安装，GitHub Actions 环境无法提供，因此 CI 中通过 `--ignore=tests/golden/` 跳过。
- 本地完整验证（含 golden tests）仍需在具备 Stata 17 的环境中手动执行。

### 4.2 新增 LICENSE

根目录 `LICENSE`（MIT）。

---

## 5. 验证命令与结果

### 5.1 构建验证

```powershell
python -m pip wheel . --no-deps -w .codex_tmp_dist
```

**结果：** 成功构建 `statapy-0.1.0-py3-none-any.whl`（78,944 bytes）。

### 5.2 全量测试

```powershell
python -m pytest tests -v
```

**结果：**
- `687 passed`
- `0 failed`
- `2 warnings`（pandas numexpr / bottleneck 版本提示，不影响功能）
- 耗时约 153.90s

### 5.3 Example smoke

```powershell
python examples/demo_regress.py
python examples/demo_reghdfe.py
python examples/demo_ppmlhdfe.py
python examples/demo_ivregress_2sls.py
```

**结果：** 4 个 demo 均成功运行，输出格式正常。

---

## 6. 当前仓库是否达到首次开源 Alpha 发布标准

**结论：是。**

本轮修缮后，仓库已满足首次对外开源发布的基本要求：

| 检查项 | 状态 |
|--------|------|
| LICENSE 文件 | ✅ MIT |
| pyproject.toml 元数据完整 | ✅ readme, license, authors, classifiers, keywords, urls |
| Python 版本口径一致 | ✅ 统一为 3.10+ |
| release-facing 错误链接已修正 | ✅ |
| 根目录整洁 | ✅ 临时脚本已迁移，日志已清理 |
| CI workflow | ✅ 安装 + import + unit tests + example smoke + wheel build |
| 全量测试通过 | ✅ 687 passed, 0 failed |
| wheel 可构建 | ✅ |
| examples 可运行 | ✅ |

**剩余已知局限（不影响首次发布，已在文档中诚实说明）：**
- multi-way clustering 未实现
- wrapper 层不直接暴露 predict/margins
- 部分社区命令仍为高频子集而非完整复现
- golden tests 依赖本地 Stata，不在 CI 中运行

这些局限已在 README、support matrix 和 release 文档中明确披露，不会误导外部用户。

---

等待 Codex 审查。
