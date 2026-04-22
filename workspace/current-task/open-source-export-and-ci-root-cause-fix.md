# 任务卡：建立开源导出机制并修复 Python 3.11 CI 根因

## 背景

当前同时维护两个目录：

- 开发主仓：`D:\OneDrive - SAIF\PhD3\StataFlow`
- 开源发布仓：`D:\OneDrive - SAIF\PhD3\StataFlow_open_source`

现在的问题是：

1. `StataFlow_open_source` 带有明显的手工搬运和手工整理痕迹，长期维护成本高，容易漏同步、漏删除、版本不一致。
2. 不希望把 `StataFlow` 中的开发文档、AI 协作文档、任务卡、审查记录等内部材料上传到 GitHub。
3. 之前推送 `StataFlow_open_source` 到 GitHub 后，CI 邮件显示：
   - `3.11` failed
   - `3.10` cancelled
   - `3.12` cancelled
4. 已经知道后两个 cancelled 很可能只是 GitHub Actions matrix 默认 `fail-fast` 的表象，但不接受仅靠规避或跳过 Python `3.11` 的方式解决。必须定位 `3.11` 根因并修复。

你的任务是：在 `StataFlow` 中先明确开源边界，再实现一套正式的开源导出机制，并同时修复开源仓 CI 的 Python `3.11` 失败问题，以及修复中文 Markdown 文档的乱码/编码问题。

## 总目标

把 `StataFlow` 作为唯一开发事实来源，把 `StataFlow_open_source` 改造成可重复生成的开源发布镜像；并修复开源仓 GitHub Actions 中 Python `3.11` 的真实失败根因，以及中文 Markdown 文档的乱码/编码问题。

---

## 子任务 1：先做开源范围审计，再设计并实现 `export_open_source.ps1 + manifest`

### 目标

在 `D:\OneDrive - SAIF\PhD3\StataFlow` 中先完成一份严格的开源范围审计，再基于这份审计设计并实现一套可执行、可重复、可维护、可审计的开源导出方案，使 `StataFlow_open_source` 不再依赖手工复制整理。

### 先做的事情：项目范围审计

你必须先对项目主要目录做开源边界审计，至少覆盖：

- 仓库根目录文件
- `.github/`
- `docs/`
- `examples/`
- `research/`
- `scripts/`
- `src/`
- `stata/`
- `tests/`
- `workspace/`

请不要默认整个目录可以开源。必须明确判断每个主要目录或子目录：

- 应开源
- 不应开源
- 条件性开源（例如仅保留其中某些子目录/文件）

尤其要重点审计：

- `docs/adr/`
- `docs/audit/`
- `docs/tasks/`
- `docs/phases/`
- `docs/operations/`
- `docs/qa/`
- `docs/testing/`
- `research/vendor/`
- `scripts/internal/`
- `scripts/validation/`
- `stata/cases/`
- `stata/output/`
- `tests/golden/`
- `workspace/`

你需要形成一个明确的“开源边界决策”，而不是泛泛地说“公开文档保留，内部文档删除”。

### 审计交付物

请新增一份可长期维护的边界说明文件，建议放在：

- `docs/operations/open-source-scope-audit.md`

这份文件至少应包含：

- 仓库各主要目录的开源判定
- 每个目录的理由
- 最终进入 manifest 的白名单与黑名单原则
- 哪些目录是“只开放子集”
- 哪些目录未来若新增文件，需要默认视为不公开

### 设计原则

- `StataFlow` 是唯一开发源
- `StataFlow_open_source` 是导出产物，不再手工维护主要内容
- 导出规则必须配置化，不要把规则硬编码散落在脚本里
- 使用白名单为主，黑名单为辅
- 保护目标仓 `.git`
- 支持 dry run
- 输出清晰 summary
- 失败时给出明确错误并返回非零退出码

### 需要新增的文件

请在 `StataFlow` 中新增：

- `scripts/release/export_open_source.ps1`
- `scripts/release/open_source_manifest.yml`
- `docs/operations/open-source-export.md`
- `docs/operations/open-source-scope-audit.md`

如果你认为需要辅助模块文件，也可以新增，但请保持结构简洁。

### manifest 要求

manifest 至少应表达以下信息：

- 源目录
- 目标目录
- 需要纳入开源的路径白名单
- 必须排除的路径黑名单
- 文件通配排除规则
- 导出前目标目录清理规则
- 导出后删除规则
- 是否保留目标目录 `.git`

manifest 的公开范围必须以你的开源范围审计为准，不能再使用粗放的目录整体白名单。

也就是说，像 `docs/`、`research/`、`scripts/`、`stata/`、`tests/` 这种目录，如果最终只有一部分适合公开，就必须在 manifest 中表达成细粒度规则，而不是整个目录一股脑纳入。

请特别注意：

- `docs/` 下面存在大量不适合开源的材料，不能整体纳入
- `research/vendor/` 是否整体保留需要审计结论支撑
- `scripts/internal/` 原则上应视为内部
- `stata/output/` 原则上应视为内部或生成物，不能默认开源
- `tests/golden/` 不要默认保留
- `workspace/` 不允许进入开源仓

### 脚本功能要求

`export_open_source.ps1` 至少支持：

- 从 manifest 读取导出规则
- 默认目标目录为 `D:\OneDrive - SAIF\PhD3\StataFlow_open_source`
- 支持 `-DryRun`
- 支持 `-Force`
- 支持 `-TargetRoot`
- 保留目标仓 `.git`
- 禁止将目标目录错误指向源目录本身
- 白名单复制后，再进行黑名单删除
- 打印导出 summary：
  - copied
  - skipped
  - deleted
  - missing expected paths

### 文档要求

在 `docs/operations/open-source-export.md` 中说明：

- 为什么采用这个方案
- manifest 如何维护
- 如何 dry run
- 如何正式导出
- 导出后需要人工检查哪些内容
- 这个方案如何替代手工整理 `StataFlow_open_source`

### 顺手修复的公开仓问题

导出机制实现后，请同步修正这些开源仓现有问题，并让它们由主仓导出过去：

1. `StataFlow_open_source/README.zh-CN.md` 顶部项目名现在写成了 `Statapy`，改成 `StataFlow`
2. `StataFlow_open_source/docs/release/open-source-alpha-status.md` 中写了 `No CI/CD pipeline is configured yet`，但仓库实际已有 `.github/workflows/ci.yml`，请修正
3. 同文件引用了不存在的 `docs/audit/next-development-plan.md`，请删除或改成实际存在的文档路径

### 验证要求

你完成后，至少验证：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\release\export_open_source.ps1 -DryRun
powershell -ExecutionPolicy Bypass -File .\scripts\release\export_open_source.ps1 -Force
```

并确认导出结果满足：

- `StataFlow_open_source\.git` 仍在
- `workspace` 不在开源仓
- `Pypi token.txt` 不在开源仓
- `.github/workflows/ci.yml` 在开源仓
- `README.md`、`README.zh-CN.md`、`pyproject.toml`、`src/stataflow` 都在开源仓
- 不应公开的 `docs/tasks/`、`docs/audit/`、`workspace/` 等材料没有进入开源仓
- 公开文档和代码能正常被同步过去

---

## 子任务 2：定位并修复 Python 3.11 CI 根因

### 目标

修复 `StataFlow_open_source` GitHub Actions 中 Python `3.11` 的真实失败问题，并保留 `3.10`、`3.11`、`3.12` 三版本矩阵。

### 已知现象

CI 邮件显示：

- `CI / test (3.11)` failed
- `CI / test (3.10)` cancelled
- `CI / test (3.12)` cancelled

已经知道后两个 cancelled 很可能只是 matrix 默认 `fail-fast` 的表象。

### 硬约束

以下做法不允许：

- 删除 Python `3.11`
- 把矩阵改成只跑 `3.10` / `3.12`
- 通过跳过失败测试来糊过去
- 加 `xfail`
- 放宽断言让测试看起来通过
- 用按 Python 版本分支绕过 bug
- 仅修改 `fail-fast` 然后宣称任务完成

必须做到：

1. 保留 Python `3.10` / `3.11` / `3.12`
2. 定位 Python `3.11` 的真实失败根因
3. 做出最小且正确的修复
4. 同时把 matrix 改成 `fail-fast: false`，让以后三个版本都能完整显示结果

### 需要检查的文件

至少检查：

- `StataFlow_open_source/.github/workflows/ci.yml`
- 以及在主仓中负责导出该文件的对应位置

当前已知 CI workflow 位于：

- `D:\OneDrive - SAIF\PhD3\StataFlow_open_source\.github\workflows\ci.yml`

### 你的任务要求

#### 2.1 修复 matrix 可观测性

在 CI workflow 中显式设置：

- `fail-fast: false`

目的仅是让 matrix 中其余版本不要被自动取消，方便看到完整结果。

#### 2.2 定位 Python 3.11 根因

你必须查明：

- 失败发生在哪个 step
- 是测试失败、example 失败、依赖安装失败、版本兼容问题，还是其他问题
- 为什么 `3.11` 首先暴露该问题，或者为什么该问题在 `3.11` 上触发

#### 2.3 做根因修复

允许的修复包括：

- 代码实现修复
- 测试中错误的版本假设修复
- example 代码修复
- 依赖版本声明修复
- CI 环境配置修复

但修复必须满足：

- 不牺牲测试原意
- 不弱化验证目标
- 不是隐藏问题
- 能解释为什么修复是正确的

### 验证要求

你完成后，应至少给出：

- 最小复现方式
- 根因说明
- 修改内容
- 为什么不是掩盖问题
- 本地验证结果
- 修复后 CI 预期结果

如果可以在本地直接验证，也请给出相应命令与结果摘要。

---

## 子任务 3：检查并修复中文 Markdown 文档乱码/编码问题

### 目标

扫描当前仓库中的中文 Markdown 文档，定位乱码或编码不一致问题，并修正为稳定可读的状态。

### 任务要求

你需要：

- 扫描仓库中的中文 Markdown 文件
- 定位哪些文件存在明显乱码、编码不一致、打开后中文异常的问题
- 判断问题是文件内容本身损坏，还是编码格式不统一
- 做出修复

修复目标不是“当前终端里看起来正常”，而是：

- 文件在仓库中以稳定编码保存
- 后续导出到开源仓后不会继续乱码
- 关键中文文档能被正常阅读

### 重点检查路径

至少检查：

- `README.zh-CN.md`
- `docs/` 下所有中文或含中文内容的 `.md`
- `workspace/current-task/` 下当前任务相关 `.md`
- 任何在终端读取时已经明显出现乱码的 Markdown 文件

### 修复要求

- 优先统一为 UTF-8
- 不要无意义重写大量正常文件
- 对确实损坏的文件，应做最小但明确的内容修复
- 若某些文件属于内部文档但仍需要保留在主仓，也应修好编码

### 验证要求

请在最终报告中说明：

- 哪些文件存在乱码
- 原因判断
- 修复方式
- 如何验证修复后可读

---

## 执行顺序要求

请按以下顺序完成，不要乱序：

1. 先完成项目开源范围审计，并写入 `docs/operations/open-source-scope-audit.md`
2. 在 `StataFlow` 中实现 `manifest + export_open_source.ps1`
3. 把 `.github/workflows/ci.yml` 和最终允许公开的文件纳入导出体系
4. 在主仓修复公开文档中的已知问题
5. 在主仓修复 CI 配置与 Python `3.11` 根因
6. 扫描并修复中文 Markdown 文档乱码/编码问题
7. 运行导出脚本同步到 `StataFlow_open_source`
8. 检查导出结果
9. 给出最终总结

---

## 交付物

完成后请交付：

### 代码与文件

- `scripts/release/export_open_source.ps1`
- `scripts/release/open_source_manifest.yml`
- `docs/operations/open-source-scope-audit.md`
- `docs/operations/open-source-export.md`
- 修复后的 CI workflow
- 修复后的公开文档
- 修复后的中文 Markdown 文档

### 说明

- 导出机制设计说明
- 项目开源范围审计结论
- 为什么这个方案比手工维护 `StataFlow_open_source` 更合理
- Python `3.11` 失败的根因
- 修复理由
- 中文 Markdown 乱码问题的根因和修复方式
- 是否有残余风险

### 验证结果

- `-DryRun` 结果摘要
- 正式导出结果摘要
- 导出后目录检查结果
- CI 修复后的本地验证结果或预期说明
- 中文 Markdown 修复后的验证结果

---

## 额外要求

- 不要做无关重构
- 不要扩大功能范围
- 保持修改最小化、可维护、可解释
- 如果发现当前开源仓还有其他明显的发布级错误，可以顺手修，但请在最终汇报中明确列出来
- 如果某个点确实需要人工决策，请先继续推进能确定的部分，再把阻塞点单独列出

---

## 成功标准

只有当以下条件全部满足时，任务才算完成：

1. `StataFlow` 成为唯一维护源
2. 开源范围已经被显式审计，不再依赖粗放白名单
3. `StataFlow_open_source` 可以由脚本稳定导出
4. 开源仓不再依赖手工搬运
5. 开源仓 CI 保留 `3.10` / `3.11` / `3.12`
6. `fail-fast: false` 已设置
7. Python `3.11` 真实失败根因已定位并修复
8. 没有通过跳过、删版本、弱化测试来规避问题
9. 已知公开文档错误已修正
10. 中文 Markdown 乱码问题已完成排查与修复
