# 首次开源发布修缮计划

本计划只针对**当前已有功能**的发布质量与可用性修缮，不要求新增算法或扩大命令支持面。

---

## 目标

把当前仓库从：

- “高质量 Alpha，但更像内部研究仓库”

推进到：

- “可以认真对外公开、让外部用户安装和试用的首次 Alpha 开源版本”

---

## 包 1：发布阻塞项收口

### 目标

清除所有首次开源的硬阻塞。

### 必做项

1. 新增根目录许可证文件
2. 补齐 `pyproject.toml` 元数据
3. 统一 Python 版本要求
4. 修正 release 文档中的错误 issue / 仓库链接

### 完成标准

- 根目录存在标准 `LICENSE`
- `pyproject.toml` 至少包含：
  - `readme`
  - `license`
  - `authors`
  - `classifiers`
  - `urls`
- README 与 package metadata 的 Python 版本一致
- release-facing 文档不再出现错误外链

### 验证标准

- `python -m pip wheel . --no-deps -w dist_tmp`
- 人工检查 README / pyproject / release 文档一致性

---

## 包 2：仓库整洁度与发布面修缮

### 目标

让外部用户第一次进入仓库时，能一眼看懂正式入口。

### 必做项

1. 清理根目录临时脚本和日志
2. 把内部辅助脚本迁移到明确子目录
3. 更新 `.gitignore`
4. 统一 examples 与 README 的入口关系

### 完成标准

- 根目录只保留：
  - README
  - pyproject
  - LICENSE
  - 正式 docs / src / tests / examples / research / workspace
- 临时 `.log` 文件不再出现在仓库根目录
- 内部一次性脚本迁移完成

### 验证标准

- 根目录文件清单人工检查
- README 中所有 examples 路径都真实存在且可运行

---

## 包 3：开源工程化最低保障

### 目标

补齐首次公开仓库的最基本工程信号。

### 必做项

1. 增加基础 CI workflow
2. 将当前 full test / example smoke 检查固化到 workflow 或脚本
3. 如有必要，新增 CONTRIBUTING / release note 初稿

### 完成标准

- `.github/workflows/` 至少有 1 个基础 workflow
- workflow 能跑最小 smoke + tests
- 外部贡献者能看到最基本的质量门槛

### 验证标准

- workflow 文件存在且语义合理
- 本地能对应执行同一套命令

---

## 建议执行顺序

1. **先做包 1**
   - 这是发布硬阻塞
2. **再做包 2**
   - 这是首次开源观感和可用性修缮
3. **最后做包 3**
   - 这是工程化补强

---

## 明确不在本轮解决的内容

这些内容可以继续作为后续算法主线推进，但**不应阻塞首次 Alpha 开源的发布面修缮**：

- `reghdfe` multi-way clustering / slopes / mobility-group DoF
- `ppmlhdfe` separation detection
- `ivreghdfe` weak-IV / over-ID / first-stage diagnostics
- `rdrobust` fuzzy RD、更多 bandwidth selectors、cluster
- wrapper 层直接暴露 `predict` / `margins`

---

## 期望结果

完成上述 3 个包之后，项目将达到这样一种状态：

- 算法层：保持当前高质量 Alpha 水平
- 文档层：对外叙事清楚，不误导用户
- 包层：元数据齐全，可分发
- 仓库层：整洁、专业、适合第一次公开展示
- 工程层：具备基础自动验证能力

这时再让 Claude Code 进入下一轮修缮，会比继续扩命令更有价值。
