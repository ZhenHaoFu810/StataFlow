# Open-Source 版本导出指南

## 概述

StataFlow 采用 **双仓库** 模式：

| 仓库 | 用途 | 内容 |
|------|------|------|
| `StataFlow`（主仓库） | 完整开发环境 | 全部源码、测试、研究数据、开发文档 |
| `StataFlow_open_source`（开源仓库） | 面向用户的分发版本 | 核心源码、示例、用户文档、验证证据 |

开源版本由主仓库通过 `export_open_source.py` 脚本自动生成，**不手动维护**。

---

## 工作原理

```
主仓库                              开源仓库
┌─────────────────────┐            ┌──────────────────┐
│ src/stataflow/       │───复制───→│ src/stataflow/    │
│ examples/            │───复制───→│ examples/         │
│ docs/USER_GUIDE.md   │───复制───→│ docs/             │
│ docs/cookbook.md     │───复制───→│ docs/             │
│ VALIDATION.md        │───复制───→│ VALIDATION.md     │
│ README.md            │───复制───→│ README.md         │
│ pyproject.toml       │───复制───→│ pyproject.toml    │
│                      │            │                   │
│ tests/               │  不导出    │                   │
│ research/            │  不导出    │                   │
│ workspace/           │  不导出    │                   │
│ docs/adr/            │  不导出    │                   │
│ stata/               │  不导出    │                   │
└─────────────────────┘            └──────────────────┘
```

**导出清单** 由 `open_source_manifest.yml` 控制。只有列入 whitelist 的文件才会被复制；blacklist 排除构建产物和敏感文件。

---

## 何时需要导出

- **每次版本发布前**（更新 version、README、VALIDATION.md 后）
- **新增/删除源文件时**（如果影响公开 API）
- **README 或用户文档有重大更新时**
- **CI 配置变更时**

不需要为了开发文档、测试、内部脚本的变更而导出。

---

## 如何导出

### 1. 确认 Manifest 正确

打开 `open_source_manifest.yml`，确认 whitelist 包含所有需要导出的文件：

```yaml
whitelist:
  files:          # 根目录文件
    - "README.md"
    - "VALIDATION.md"
    - ...
  directories:    # 递归复制的目录
    - "src/stataflow/"
    - "examples/"
  specific_files: # 特定路径文件
    - "docs/USER_GUIDE.md"
    - ".github/workflows/ci.yml"
    - ...
```

### 2. 运行导出

```bash
# 预览（不实际修改）
python scripts/release/export_open_source.py --dry-run

# 实际执行
python scripts/release/export_open_source.py --force
```

默认目标路径为 `../StataFlow_open_source`（即主仓库的同级目录）。

### 3. 验证导出结果

```bash
# 安装
cd ../StataFlow_open_source
pip install -e .

# 导入
python -c "import stataflow; print(stataflow.__version__)"

# 运行示例
python examples/demo_regress.py
python examples/demo_reghdfe.py
python examples/demo_ppmlhdfe.py
python examples/demo_ivregress_2sls.py
```

### 4. 确认目录清洁

确保开源版本中**不存在**以下目录：
- `tests/`
- `research/`
- `scripts/`
- `stata/`
- `workspace/`

```bash
ls ../StataFlow_open_source/
# 应仅显示：docs/  examples/  src/  LICENSE  README.md  VALIDATION.md  pyproject.toml
```

---

## 新增文件到开源版本

如果需要向开源版本添加新文件：

1. 在 `open_source_manifest.yml` 的 whitelist 中添加路径
2. 如果是目录，加入 `directories`；如果是单文件，加入 `files` 或 `specific_files`
3. 运行导出并验证

### 添加原则

| 应该导出 | 不应该导出 |
|---------|-----------|
| 核心源码（`src/stataflow/`） | 测试代码（`tests/`） |
| 用户文档（README、USER_GUIDE、cookbook） | 开发文档（adr、architecture、roadmap 等） |
| 示例脚本（`examples/`） | 研究数据（`research/`） |
| 验证证据（`VALIDATION.md`） | 内部脚本（`scripts/`） |
| CI 配置（`.github/workflows/`） | Stata 运行时产物（`stata/`） |
| 包配置（`pyproject.toml`、`LICENSE`） | 开发过程文档（`workspace/`、`docs/audit/`） |

---

## 常见问题

### Q: 开源版本中某文件丢失了，怎么办？

1. 确认该文件在主仓库中存在
2. 确认其在 `open_source_manifest.yml` 的 whitelist 中
3. 确认其没有被 blacklist 匹配到
4. 运行 `python scripts/release/export_open_source.py --dry-run` 查看是否被选中

### Q: 开源版本中有不该出现的文件，怎么办？

1. 将该文件路径加入 `open_source_manifest.yml` 的 blacklist
2. 运行导出 — 脚本会自动删除孤儿文件

### Q: CI 失败了怎么办？

1. 从 `../StataFlow_open_source` 目录运行 `pip install -e .` 确认安装成功
2. 运行 `python -c "import stataflow"` 确认导入成功
3. 逐一运行 `examples/demo_*.py` 确认 demo 可运行
4. 如果某个 python 模块导入失败，检查 `src/stataflow/` 下的文件是否被正确导出
