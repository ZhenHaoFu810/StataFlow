# Package F — Release Candidate Polish 完成报告

**日期：** 2026-04-23
**任务：** `package-f-release-candidate-polish`
**运行者：** Claude Code
**状态：** 完成

---

## 1. 公开用户视角审查结论

### 1.1 审查方法

以首次访问 GitHub 仓库的外部用户视角，依次阅读：

- `README.md` / `README.zh-CN.md`
- `docs/USER_GUIDE.md` / `docs/USER_GUIDE.zh-CN.md`
- `docs/cookbook.md` / `docs/cookbook.zh-CN.md`
- `docs/command-support-matrix/README.md`
- `docs/release/open-source-alpha-status.md`
- `docs/release/known-issues.md`
- `examples/`

### 1.2 发现的最影响首发的 5 个问题

| 优先级 | 问题 | 影响 |
|--------|------|------|
| P0 | README / cookbook / release docs 一致声称“多层聚类尚未支持”，但 `regress` 已支持双向聚类 | 用户会低估 `regress` 能力，或误以为项目文档严重滞后 |
| P0 | `docs/cookbook.zh-CN.md` 的 rdrobust 示例指向已不存在的 `research/vendor/.../rdrobust_senate.dta` | 外部用户直接复制代码会报错，首跑即失败 |
| P0 | `docs/release/known-issues.md` 声称“没有配置 CI”，但 `.github/workflows/ci.yml` 已存在且运行 | 破坏文档可信度 |
| P1 | `docs/release/open-source-alpha-status.md` 测试数写 681 passed，实际非 golden 测试为 194 | 数字与开源仓实际状态不符，造成误导 |
| P1 | `docs/cookbook.md` 出现编码损坏字符“脳”（U+8133） | 影响专业感，可能引发编码疑虑 |

---

## 2. 本轮修复内容与优先理由

### 2.1 修复多层聚类表述漂移（P0）

**涉及文件：**
- `README.md`
- `docs/cookbook.md`
- `docs/cookbook.zh-CN.md`
- `docs/release/open-source-alpha-status.md`
- `docs/release/known-issues.md`

**修复前：** 多处文档一致声称“仅支持单层聚类 / 多层聚类尚未支持”。

**修复后：** 明确区分——`regress` 支持双向聚类（Cameron-Gelbach-Miller 2011），其余命令仍限于单层聚类。这一表述与 `docs/command-support-matrix/README.md` 的 Common Limitations 段保持一致。

**优先理由：** 这是 Package D（Cross-Cutting Inference）已实现的核心能力，文档却未同步。用户若因文档放弃使用双向聚类功能，等于直接损失已实现的价值。

### 2.2 修复 rdrobust 中文 cookbook 数据路径（P0）

**涉及文件：** `docs/cookbook.zh-CN.md`

**修复前：** 示例使用 `research/vendor/stata_community/rdrobust/rdrobust-master/stata/rdrobust_senate.dta`，该路径在开源仓中不存在（`research/vendor/` 是 closed 目录）。

**修复后：** 改为 `tests/data/rdrobust_senate.dta`，与 `tests/test_rdrobust.py` 实际依赖一致。

**优先理由：** 这是“复制即运行”的 cookbook 示例，首跑失败会直接劝退用户。

### 2.3 修复 CI 配置 false negative（P0）

**涉及文件：** `docs/release/known-issues.md`

**修复前：** “No automated continuous integration pipeline is configured.”

**修复后：** “GitHub Actions pipeline is configured (`.github/workflows/ci.yml`) and runs on Python 3.10, 3.11, and 3.12.”

**优先理由：** 开源用户第一眼看到 known-issues 会误以为项目没有 CI，与仓库实际状态矛盾。

### 2.4 修复测试计数与日期漂移（P1）

**涉及文件：** `docs/release/open-source-alpha-status.md`

**修复：**
- 版本号从笼统的 “Alpha” 改为 “0.1.4 (Alpha)”
- 日期从 2026-04-18 更新为 2026-04-23
- 测试数从含 golden tests 的 “681 passed” 改为开源仓可复现的 “194 passed, 0 failed”

**优先理由：** 公开文档的数字必须能被外部用户验证。681 包含需本地 Stata 17 的 golden tests，开源用户无法复现。

### 2.5 修复 cookbook 编码损坏（P1）

**涉及文件：** `docs/cookbook.md`

**修复：** 将 “Continuous 脳 continuous interaction” 和 “Categorical 脳 categorical interaction” 中的损坏字符恢复为 “×”。

**优先理由：** 编码问题损害项目专业形象。

### 2.6 修复 statapy 拼写漂移（P1）

**涉及文件：** `docs/release/known-issues.md`

**修复：** `statapy.compat.stata` → `stataflow.compat.stata`。

**优先理由：** 包名错误会让用户找不到对应模块。

### 2.7 创建 release candidate checklist（P2）

**新增文件：** `docs/release/release-candidate-checklist.md`

**内容：** 覆盖导出前检查（版本、文档一致性、测试/示例）、导出执行、导出后检查（内容完整性、清洁环境验证、文档风险审查、已知风险确认）及签字段。

**优先理由：** Package E 已建立导出机制，但缺乏可重复的发布门槛文档。Checklist 确保未来每次导出都经过相同验证，防止文档/元数据漂移重演。

---

## 3. 修改文件汇总

| 文件 | 修改类型 | 修改原因 |
|------|---------|---------|
| `README.md` | 修复 | 更正 multi-way clustering 表述；修正 Alpha — Partial 示例 |
| `docs/cookbook.md` | 修复 | 修复 clustering 表述；修复编码损坏字符（2 处）；更新日期 |
| `docs/cookbook.zh-CN.md` | 修复 | 修复 clustering 表述；修正 rdrobust 数据路径；更新日期 |
| `docs/release/open-source-alpha-status.md` | 修复 | 更正 clustering 表述；更新版本号、日期、测试计数 |
| `docs/release/known-issues.md` | 修复 | 更正 CI 配置表述；修复 `statapy` 拼写；更正 clustering 表述 |
| `docs/release/release-candidate-checklist.md` | 新增 | 建立可执行的发布门槛检查清单 |

---

## 4. 本地验证

### 4.1 主仓测试

```bash
pytest tests/ -v --ignore=tests/golden/
```

**结果：194 passed, 0 failed**

### 4.2 Examples

```bash
python examples/demo_regress.py
python examples/demo_reghdfe.py
python examples/demo_ppmlhdfe.py
python examples/demo_ivregress_2sls.py
```

**结果：全部正常执行，无报错。**

### 4.3 导出验证

```bash
python scripts/release/export_open_source.py --force
```

- 导出完成，无异常
- 开源镜像文件数：167 个非 git 文件
- 导出后测试：`StataFlow_open_source` 内运行 pytest，**194 passed, 0 failed**
- 导出后 examples：全部正常

---

## 5. 残余风险与留待后续

| 问题 | 位置 | 留给后续 |
|------|------|---------|
| `README.zh-CN.md` 未提及 PyPI 安装（仅写 `pip install -e .`） | README.zh-CN.md | 非阻断，但影响中文用户首次安装体验 |
| 中文 cookbook 未覆盖双向聚类示例 | cookbook.zh-CN.md | 属于功能展示扩展，不影响现有功能可信度 |
| `docs/operations/open-source-scope-audit.md` 仍需随 manifest 版本同步 | docs/operations | 每次 manifest 升级时由 checklist 强制检查 |
| 部分内部 research docs 仍有编码损坏（`docs/research/*.md`） | docs/research | 这些文件属于 closed 目录，不进入开源仓 |

---

## 6. 返工说明（Codex 复审后）

### 6.1 复审指出的两类问题

1. **`docs/cookbook.md` 仍残留一处编码损坏字符**：首轮报告声称已修复 cookbook 编码问题，但 `Categorical × continuous interaction` 这一节的标题仍为损坏字符“脳”（U+8133）。
2. **`REPORT.md` 导出文件计数与实际不符**：报告写“开源镜像文件数：166 个非 git 文件”，但重新导出后实际统计为 **167** 个非 git 文件。

### 6.2 修复方式

- **F-R1**：将 `docs/cookbook.md` 第 454 行标题中的“脳”替换为“×”。同时全文搜索确认无其他同类损坏字符残留。
- **F-R2**：重新执行 `python scripts/release/export_open_source.py --force`，用 `find ../StataFlow_open_source -type f | grep -v '/\.git/' | wc -l` 精确统计，将 `REPORT.md` 中的数字从 166 修正为 167。

### 6.3 复核结果

- `docs/cookbook.md` 全文搜索非 ASCII 字符：仅剩正常的 “×” 和 em-dash，无“脳”残留。
- 导出后统计：`167` 个非 git 文件，与报告一致。
- 导出后测试：`194 passed, 0 failed`。

---

# Package G — Final Release Consistency Cleanup 完成报告

**日期：** 2026-04-23
**任务：** `package-g-final-release-consistency-cleanup`
**运行者：** Claude Code
**状态：** 完成

---

## G1. Codex 最终复审发现的阻断问题

1. **HDFE 能力口径回退为旧版 “1-2 FE”**：`README.md`、`docs/command-support-matrix/README.md`、`docs/release/open-source-alpha-status.md` 的摘要表格仍把 `reghdfe` / `ivreghdfe` / `ppmlhdfe` 写成 “1-2 group HDFE” / “1-2 FEs”，但 Package B 已实现并测试了 `1+ supported`。
2. **`docs/command-support-matrix/ppmlhdfe.md` 残留损坏文本**：`predict(type="residuals")` 一行残留 `y - 渭`（损坏字符）；fit-stats evidence 一行残留 `pseudo-R虏`（损坏字符）。
3. **`docs/release/release-candidate-checklist.md` 使用旧导出文件基线**：仍写 `~166 non-git files`，实际导出后为 **167**。

---

## G2. 修复内容与修改文件

### G2.1 统一 HDFE 家族能力表述

**涉及文件：**
- `README.md`
- `docs/command-support-matrix/README.md`
- `docs/release/open-source-alpha-status.md`

**修复：** 将三处摘要表格中的 “1-2 group HDFE” / “1-2 categorical FEs” / “1-2 FEs” 统一改为 “1+ group HDFE” / “1+ categorical FEs” / “1+ FEs”，与 `reghdfe` 参数表中 “1+ supported” 的口径保持一致。

### G2.2 修复 ppmlhdfe.md 损坏文本

**涉及文件：** `docs/command-support-matrix/ppmlhdfe.md`

**修复：**
- `y - 渭` → `y - mu`
- `pseudo-R虏` → `pseudo-R2`

### G2.3 修正 release checklist 文件基线

**涉及文件：** `docs/release/release-candidate-checklist.md`

**修复：** `~166 non-git files` → `167 non-git files`。

---

## G3. 本地验证

### G3.1 主仓测试

```bash
pytest tests/ -q --ignore=tests/golden/
```

**结果：194 passed, 0 failed**

### G3.2 导出验证

```bash
python scripts/release/export_open_source.py --force
```

- 导出完成，无异常
- 开源镜像文件数：**167** 个非 git 文件
- 导出后关键文件确认：
  - `StataFlow_open_source/README.md` 已同步为 `1+ group HDFE`
  - `StataFlow_open_source/docs/command-support-matrix/ppmlhdfe.md` 已无 `渭` / `虏` 残留
  - `StataFlow_open_source/docs/release/release-candidate-checklist.md` 已更新为 `167 non-git files`

---

## G4. 成功标准核验

- [x] 所有公开发布文档对 HDFE 家族的能力表述不再回退到旧版 `1-2 FE`
- [x] `ppmlhdfe.md` 中不再残留损坏的英文文本
- [x] release checklist 的导出文件基线与当前实际结果一致
- [x] 主仓非 golden 测试继续通过
- [x] 开源镜像仓已同步到修正后的发布文档状态

---

## G5. Package G Rework（Codex 复审后）

### G5.1 复审指出的遗漏

Codex 复审发现 Package G 首轮交付遗漏了 HDFE 三个命令矩阵正文尾部的旧口径：

- `docs/command-support-matrix/reghdfe.md`
- `docs/command-support-matrix/ivreghdfe.md`
- `docs/command-support-matrix/ppmlhdfe.md`

三文件的 “Alignment Evidence” 末尾仍写着 “Stata 17 dual-run verified for 1-2 absorbed FEs...”，与已更新的摘要表格和 release 文档不一致。

### G5.2 修复方式

将三处末尾的 `1-2 absorbed FEs` 统一改为 `1+ absorbed FEs`：

- `reghdfe.md` 第 86 行
- `ivreghdfe.md` 第 90 行
- `ppmlhdfe.md` 第 90 行

### G5.3 复核结果

- 主仓全文搜索 `1-2 absorbed FEs`：零残留。
- 导出镜像 `StataFlow_open_source` 三文件已同步更新。
- 主仓测试：`194 passed, 0 failed`。

---

# Package F — Release Candidate Polish 完成报告（归档）

**日期：** 2026-04-23
**任务：** `package-f-release-candidate-polish`
**运行者：** Claude Code
**状态：** 完成

---

## 1. 公开用户视角审查结论

### 1.1 审查方法

以首次访问 GitHub 仓库的外部用户视角，依次阅读：

- `README.md` / `README.zh-CN.md`
- `docs/USER_GUIDE.md` / `docs/USER_GUIDE.zh-CN.md`
- `docs/cookbook.md` / `docs/cookbook.zh-CN.md`
- `docs/command-support-matrix/README.md`
- `docs/release/open-source-alpha-status.md`
- `docs/release/known-issues.md`
- `examples/`

### 1.2 发现的最影响首发的 5 个问题

| 优先级 | 问题 | 影响 |
|--------|------|------|
| P0 | README / cookbook / release docs 一致声称“多层聚类尚未支持”，但 `regress` 已支持双向聚类 | 用户会低估 `regress` 能力，或误以为项目文档严重滞后 |
| P0 | `docs/cookbook.zh-CN.md` 的 rdrobust 示例指向已不存在的 `research/vendor/.../rdrobust_senate.dta` | 外部用户直接复制代码会报错，首跑即失败 |
| P0 | `docs/release/known-issues.md` 声称“没有配置 CI”，但 `.github/workflows/ci.yml` 已存在且运行 | 破坏文档可信度 |
| P1 | `docs/release/open-source-alpha-status.md` 测试数写 681 passed，实际非 golden 测试为 194 | 数字与开源仓实际状态不符，造成误导 |
| P1 | `docs/cookbook.md` 出现编码损坏字符“脳”（U+8133） | 影响专业感，可能引发编码疑虑 |

---

## 2. 本轮修复内容与优先理由

### 2.1 修复多层聚类表述漂移（P0）

**涉及文件：**
- `README.md`
- `docs/cookbook.md`
- `docs/cookbook.zh-CN.md`
- `docs/release/open-source-alpha-status.md`
- `docs/release/known-issues.md`

**修复前：** 多处文档一致声称“仅支持单层聚类 / 多层聚类尚未支持”。

**修复后：** 明确区分——`regress` 支持双向聚类（Cameron-Gelbach-Miller 2011），其余命令仍限于单层聚类。这一表述与 `docs/command-support-matrix/README.md` 的 Common Limitations 段保持一致。

**优先理由：** 这是 Package D（Cross-Cutting Inference）已实现的核心能力，文档却未同步。用户若因文档放弃使用双向聚类功能，等于直接损失已实现的价值。

### 2.2 修复 rdrobust 中文 cookbook 数据路径（P0）

**涉及文件：** `docs/cookbook.zh-CN.md`

**修复前：** 示例使用 `research/vendor/stata_community/rdrobust/rdrobust-master/stata/rdrobust_senate.dta`，该路径在开源仓中不存在（`research/vendor/` 是 closed 目录）。

**修复后：** 改为 `tests/data/rdrobust_senate.dta`，与 `tests/test_rdrobust.py` 实际依赖一致。

**优先理由：** 这是“复制即运行”的 cookbook 示例，首跑失败会直接劝退用户。

### 2.3 修复 CI 配置 false negative（P0）

**涉及文件：** `docs/release/known-issues.md`

**修复前：** “No automated continuous integration pipeline is configured.”

**修复后：** “GitHub Actions pipeline is configured (`.github/workflows/ci.yml`) and runs on Python 3.10, 3.11, and 3.12.”

**优先理由：** 开源用户第一眼看到 known-issues 会误以为项目没有 CI，与仓库实际状态矛盾。

### 2.4 修复测试计数与日期漂移（P1）

**涉及文件：** `docs/release/open-source-alpha-status.md`

**修复：**
- 版本号从笼统的 “Alpha” 改为 “0.1.4 (Alpha)”
- 日期从 2026-04-18 更新为 2026-04-23
- 测试数从含 golden tests 的 “681 passed” 改为开源仓可复现的 “194 passed, 0 failed”

**优先理由：** 公开文档的数字必须能被外部用户验证。681 包含需本地 Stata 17 的 golden tests，开源用户无法复现。

### 2.5 修复 cookbook 编码损坏（P1）

**涉及文件：** `docs/cookbook.md`

**修复：** 将 “Continuous 脳 continuous interaction” 和 “Categorical 脳 categorical interaction” 中的损坏字符恢复为 “×”。

**优先理由：** 编码问题损害项目专业形象。

### 2.6 修复 statapy 拼写漂移（P1）

**涉及文件：** `docs/release/known-issues.md`

**修复：** `statapy.compat.stata` → `stataflow.compat.stata`。

**优先理由：** 包名错误会让用户找不到对应模块。

### 2.7 创建 release candidate checklist（P2）

**新增文件：** `docs/release/release-candidate-checklist.md`

**内容：** 覆盖导出前检查（版本、文档一致性、测试/示例）、导出执行、导出后检查（内容完整性、清洁环境验证、文档风险审查、已知风险确认）及签字段。

**优先理由：** Package E 已建立导出机制，但缺乏可重复的发布门槛文档。Checklist 确保未来每次导出都经过相同验证，防止文档/元数据漂移重演。

---

## 3. 修改文件汇总

| 文件 | 修改类型 | 修改原因 |
|------|---------|---------|
| `README.md` | 修复 | 更正 multi-way clustering 表述；修正 Alpha — Partial 示例 |
| `docs/cookbook.md` | 修复 | 修复 clustering 表述；修复编码损坏字符（2 处）；更新日期 |
| `docs/cookbook.zh-CN.md` | 修复 | 修复 clustering 表述；修正 rdrobust 数据路径；更新日期 |
| `docs/release/open-source-alpha-status.md` | 修复 | 更正 clustering 表述；更新版本号、日期、测试计数 |
| `docs/release/known-issues.md` | 修复 | 更正 CI 配置表述；修复 `statapy` 拼写；更正 clustering 表述 |
| `docs/release/release-candidate-checklist.md` | 新增 | 建立可执行的发布门槛检查清单 |

---

## 4. 本地验证

### 4.1 主仓测试

```bash
pytest tests/ -v --ignore=tests/golden/
```

**结果：194 passed, 0 failed**

### 4.2 Examples

```bash
python examples/demo_regress.py
python examples/demo_reghdfe.py
python examples/demo_ppmlhdfe.py
python examples/demo_ivregress_2sls.py
```

**结果：全部正常执行，无报错。**

### 4.3 导出验证

```bash
python scripts/release/export_open_source.py --force
```

- 导出完成，无异常
- 开源镜像文件数：167 个非 git 文件
- 导出后测试：`StataFlow_open_source` 内运行 pytest，**194 passed, 0 failed**
- 导出后 examples：全部正常

---

## 5. 残余风险与留待后续

| 问题 | 位置 | 留给后续 |
|------|------|---------|
| `README.zh-CN.md` 未提及 PyPI 安装（仅写 `pip install -e .`） | README.zh-CN.md | 非阻断，但影响中文用户首次安装体验 |
| 中文 cookbook 未覆盖双向聚类示例 | cookbook.zh-CN.md | 属于功能展示扩展，不影响现有功能可信度 |
| `docs/operations/open-source-scope-audit.md` 仍需随 manifest 版本同步 | docs/operations | 每次 manifest 升级时由 checklist 强制检查 |
| 部分内部 research docs 仍有编码损坏（`docs/research/*.md`） | docs/research | 这些文件属于 closed 目录，不进入开源仓 |

---

## 6. 返工说明（Codex 复审后）

### 6.1 复审指出的两类问题

1. **`docs/cookbook.md` 仍残留一处编码损坏字符**：首轮报告声称已修复 cookbook 编码问题，但 `Categorical × continuous interaction` 这一节的标题仍为损坏字符“脳”（U+8133）。
2. **`REPORT.md` 导出文件计数与实际不符**：报告写“开源镜像文件数：166 个非 git 文件”，但重新导出后实际统计为 **167** 个非 git 文件。

### 6.2 修复方式

- **F-R1**：将 `docs/cookbook.md` 第 454 行标题中的“脳”替换为“×”。同时全文搜索确认无其他同类损坏字符残留。
- **F-R2**：重新执行 `python scripts/release/export_open_source.py --force`，用 `find ../StataFlow_open_source -type f | grep -v '/\.git/' | wc -l` 精确统计，将 `REPORT.md` 中的数字从 166 修正为 167。

### 6.3 复核结果

- `docs/cookbook.md` 全文搜索非 ASCII 字符：仅剩正常的 “×” 和 em-dash，无“脳”残留。
- 导出后统计：`167` 个非 git 文件，与报告一致。
- 导出后测试：`194 passed, 0 failed`。

---

## 7. 成功标准核验

- [x] 至少一个真实的 release-candidate 阻断问题被修掉（多层聚类表述漂移 + rdrobust 数据路径）
- [x] 不是只写建议或只做分析（落地了 6 个文件修改 + 1 个新增 checklist）
- [x] 对外文档 / 版本元数据 / 发布状态比当前更一致
- [x] `REPORT.md` 可供 Codex 下一轮复审直接使用
