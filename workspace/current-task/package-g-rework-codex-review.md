# Package G Rework: Codex Final Review Follow-up

## 背景

`Package G` 已经修掉了大部分最终发布前的公开文档阻断项，但 Codex 复审发现还有一个遗漏没有清完，因此当前还不能放行到最终开源镜像版本。

主仓当前状态：

- `python -m pytest tests/ -q --ignore=tests/golden/`：`194 passed`
- `python scripts/release/export_open_source.py --force`：成功，当前为 `Unchanged 167 files`

所以问题不在实现代码，而在**HDFE 命令矩阵内部仍残留旧能力口径**。

## Codex 复审发现

以下 3 个文件的 “Alignment Evidence” 末尾仍写着旧表述：

- [docs/command-support-matrix/reghdfe.md](</D:/OneDrive - SAIF/PhD3/StataFlow/docs/command-support-matrix/reghdfe.md>)
- [docs/command-support-matrix/ivreghdfe.md](</D:/OneDrive - SAIF/PhD3/StataFlow/docs/command-support-matrix/ivreghdfe.md>)
- [docs/command-support-matrix/ppmlhdfe.md](</D:/OneDrive - SAIF/PhD3/StataFlow/docs/command-support-matrix/ppmlhdfe.md>)

当前仍残留的口径是：

- `1-2 absorbed FEs`

但 `Package B` 之后的公开能力表述已经统一为：

- `1+ supported`
- 或与之等价的 `1+ group HDFE` / `1+ FEs`

这意味着：

- 摘要页已经更新
- release 文档已经更新
- 但命令矩阵正文尾部还停留在旧版本

这是发布级文档一致性遗漏，必须补齐。

## 本轮目标

把 HDFE 三个命令矩阵正文尾部的旧 `1-2 absorbed FEs` 口径统一修掉，并同步更新导出镜像。

## 允许修改的文件

- `docs/command-support-matrix/reghdfe.md`
- `docs/command-support-matrix/ivreghdfe.md`
- `docs/command-support-matrix/ppmlhdfe.md`
- `workspace/current-task/REPORT.md`

## 不允许做的事

- 不改实现代码
- 不改测试代码
- 不扩大到其他文档重写
- 不引入新的功能性声明

## 最低验证要求

至少执行：

```bash
python -m pytest tests/ -q --ignore=tests/golden/
python scripts/release/export_open_source.py --force
```

并至少确认：

- `StataFlow_open_source/docs/command-support-matrix/reghdfe.md` 已同步
- `StataFlow_open_source/docs/command-support-matrix/ivreghdfe.md` 已同步
- `StataFlow_open_source/docs/command-support-matrix/ppmlhdfe.md` 已同步

## 交付要求

完成后请在 [REPORT.md](</D:/OneDrive - SAIF/PhD3/StataFlow/workspace/current-task/REPORT.md>) 中追加一个简短的 “Package G Rework” 部分，至少写清：

- 漏掉了什么
- 改了哪些文件
- 如何验证
- 导出后是否同步成功

## 成功标准

只有当以下条件全部满足时，本轮返工才算完成：

- HDFE 三个命令矩阵正文尾部不再残留 `1-2 absorbed FEs`
- 主仓测试继续通过
- 导出后开源镜像同步完成
