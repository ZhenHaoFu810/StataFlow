# 当前任务

你现在进入的是一个新的实现任务，不再是上一轮 `Validation Package 001`。

当前唯一活动任务是：

- [open-source-export-and-ci-root-cause-fix.md](</D:/OneDrive - SAIF/PhD3/StataFlow/workspace/current-task/open-source-export-and-ci-root-cause-fix.md>)

## 任务目标

把 `D:\OneDrive - SAIF\PhD3\StataFlow` 变成唯一维护源，并把
`D:\OneDrive - SAIF\PhD3\StataFlow_open_source` 改造成可重复生成的开源发布镜像。

同时：

- 全面审计项目目录边界，明确哪些文件和目录适合开源，哪些不适合
- 修复开源仓 GitHub Actions 中 Python `3.11` 的真实失败根因
- 检查并修正当前仓库中中文 Markdown 文档的乱码/编码问题

## 必须先读

1. [workspace/current-task/open-source-export-and-ci-root-cause-fix.md](</D:/OneDrive - SAIF/PhD3/StataFlow/workspace/current-task/open-source-export-and-ci-root-cause-fix.md>)
2. [README.md](</D:/OneDrive - SAIF/PhD3/StataFlow/README.md>)
3. [workspace/current-task/REPORT_TEMPLATE.md](</D:/OneDrive - SAIF/PhD3/StataFlow/workspace/current-task/REPORT_TEMPLATE.md>)
4. [D:/OneDrive - SAIF/PhD3/StataFlow_open_source/.github/workflows/ci.yml](</D:/OneDrive - SAIF/PhD3/StataFlow_open_source/.github/workflows/ci.yml>)

## 执行边界

- 只在 `StataFlow` 中实现开源导出机制，`StataFlow_open_source` 作为导出目标与验证对象
- 不做与本任务无关的重构
- 不扩大功能范围
- 不再假设 `docs`、`research`、`scripts`、`stata`、`tests` 可以整体开源，必须做显式范围审计
- 不删除 Python `3.11`
- 不通过跳过测试、`xfail`、放宽断言、条件分支绕过等方式掩盖 `3.11` 问题
- `fail-fast: false` 只能作为增强可观测性的辅助修改，不能替代根因修复
- 中文 Markdown 的修复必须以“文件实际可读、编码稳定、后续导出不再乱码”为目标，而不是只在当前终端显示正常

## 预期执行顺序

1. 对项目所有主要目录做开源范围审计，形成明确的 include/exclude 决策
2. 在 `StataFlow` 中实现 `manifest + export_open_source.ps1`
3. 把 `.github/workflows/ci.yml` 和其他最终允许公开的文件纳入导出体系
4. 修复公开文档中的已知错误
5. 定位并修复 Python `3.11` 的真实失败根因
6. 扫描并修复中文 Markdown 文档的乱码/编码问题
7. 运行导出脚本同步到 `StataFlow_open_source`
8. 检查导出结果和 CI 相关结果
9. 在 `REPORT.md` 中完成任务汇报

## 交付要求

完成后在 [workspace/current-task/REPORT.md](</D:/OneDrive - SAIF/PhD3/StataFlow/workspace/current-task/REPORT.md>) 中明确说明：

- 项目各主要目录中哪些内容允许开源，哪些不允许，以及判断理由
- 新增了哪些导出机制文件
- manifest 如何组织公开/排除规则
- 导出脚本如何运行，`DryRun` 与正式执行结果如何
- 导出后 `StataFlow_open_source` 的关键检查结果
- 修复了哪些公开文档问题
- Python `3.11` 失败发生在哪一步
- 根因是什么
- 做了什么修复
- 为什么该修复不是掩盖问题
- 哪些中文 Markdown 文件存在乱码/编码问题
- 做了什么修复
- 修复后如何验证这些文件不再乱码
- 本地验证结果与 CI 预期结果

## 完成判定

只有当以下条件全部满足时，任务才算完成：

- `StataFlow` 成为唯一维护源
- 开源范围已经被显式审计，不再依赖粗放白名单
- `StataFlow_open_source` 可以由脚本稳定导出
- 开源仓不再依赖手工搬运
- 开源仓 CI 保留 `3.10` / `3.11` / `3.12`
- `fail-fast: false` 已设置
- Python `3.11` 真实失败根因已定位并修复
- 没有通过跳过、删版本或弱化测试来规避问题
- 已知公开文档错误已修正
- 中文 Markdown 乱码问题已完成排查与修复
