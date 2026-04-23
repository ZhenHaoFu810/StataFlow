# Package G: Final Release Consistency Cleanup

## 背景

当前主仓代码、测试和导出链路已经基本稳定：

- 主仓非 golden 测试：`194 passed`
- 开源镜像仓非 golden 测试：`194 passed`
- `scripts/release/export_open_source.py --force` 可以成功导出到 `D:\OneDrive - SAIF\PhD3\StataFlow_open_source`

但最终发布前复审仍发现若干**公开文档一致性阻断项**。这些问题不会让测试失败，却会直接影响开源用户对当前能力边界的理解，因此在发布前必须修完。

## 本轮任务目标

修掉当前 release-facing 文档中的最后一批阻断性一致性问题，使主仓与 `StataFlow_open_source` 的公开口径重新对齐。

## Codex 复审阻断项

### 1. HDFE 能力口径回退为旧版 “1-2 FE”

以下公开文档仍在宣称 `reghdfe` / `ivreghdfe` / `ppmlhdfe` 只支持 `1-2` 个 FE，但 `Package B` 已经把实现与 synthetic tests 扩展到了 `1+ supported`：

- [README.md](</D:/OneDrive - SAIF/PhD3/StataFlow/README.md>)
- [docs/command-support-matrix/README.md](</D:/OneDrive - SAIF/PhD3/StataFlow/docs/command-support-matrix/README.md>)
- [docs/release/open-source-alpha-status.md](</D:/OneDrive - SAIF/PhD3/StataFlow/docs/release/open-source-alpha-status.md>)

这是**公开能力声明回退**，必须修正。

### 2. `ppmlhdfe.md` 仍残留损坏文本

以下文件中已确认至少存在两处损坏内容：

- [docs/command-support-matrix/ppmlhdfe.md](</D:/OneDrive - SAIF/PhD3/StataFlow/docs/command-support-matrix/ppmlhdfe.md>)

已定位的问题包括：

- `predict(type="residuals")` 一行残留损坏文本
- fit-stats evidence 一行里的 `pseudo-R...` 文本损坏

这属于公开英文文档质量问题，必须修掉。

### 3. Release checklist 仍使用旧导出文件基线

以下文件仍写着旧的导出文件基线：

- [docs/release/release-candidate-checklist.md](</D:/OneDrive - SAIF/PhD3/StataFlow/docs/release/release-candidate-checklist.md>)

当前实际导出后非 `.git` 文件数已经是 `167`，不应继续保留 `~166` / `166 non-git files` 之类旧口径。

## 允许修改的范围

- `README.md`
- `docs/command-support-matrix/README.md`
- `docs/release/open-source-alpha-status.md`
- `docs/command-support-matrix/ppmlhdfe.md`
- `docs/release/release-candidate-checklist.md`
- 如有必要，可同步更新其他**直接相关**的公开文档，但不要扩大范围
- `workspace/current-task/REPORT.md`

## 不允许做的事

- 不改统计实现
- 不扩新功能
- 不改测试逻辑，除非是为了补最小文档一致性验证
- 不重新设计导出机制
- 不顺手改 unrelated 文档

## 建议执行顺序

1. 先统一 HDFE 家族在公开文档中的能力表述，确保与 `Package B` 当前真实状态一致
2. 再修 `ppmlhdfe.md` 的损坏文本
3. 再把 release checklist 的导出文件基线改成当前实测值
4. 运行最小必要验证
5. 重新执行导出到 `StataFlow_open_source`
6. 更新 `REPORT.md`

## 最低验证要求

至少执行：

```bash
python -m pytest tests/ -q --ignore=tests/golden/
python scripts/release/export_open_source.py --force
```

并至少人工确认：

- `D:\OneDrive - SAIF\PhD3\StataFlow_open_source\README.md` 已同步 HDFE 口径
- `D:\OneDrive - SAIF\PhD3\StataFlow_open_source\docs\command-support-matrix\ppmlhdfe.md` 已无损坏文本
- `D:\OneDrive - SAIF\PhD3\StataFlow_open_source\docs\release\release-candidate-checklist.md` 的文件基线已更新

## 交付物

完成后请在 [REPORT.md](</D:/OneDrive - SAIF/PhD3/StataFlow/workspace/current-task/REPORT.md>) 中新增一个 `Package G` 报告，至少包含：

- 修复前的阻断问题列表
- 修改文件清单
- 每个问题如何修复
- 验证命令与结果
- 导出后开源镜像是否同步成功

## 成功标准

只有当以下条件全部满足时，本轮任务才算完成：

- 所有公开发布文档对 HDFE 家族的能力表述不再回退到旧版 `1-2 FE`
- `ppmlhdfe.md` 中不再残留损坏文本
- release checklist 的导出文件基线与当前实际结果一致
- 主仓非 golden 测试继续通过
- 开源镜像仓已同步到修正后的发布文档状态
