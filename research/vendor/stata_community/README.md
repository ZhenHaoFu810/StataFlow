# Stata Community Source Mirrors

本目录用于保存公开 Stata / SSC / GitHub 命令的本地源码镜像，供离线研究使用。

当前状态：

- 已通过 GitHub 仓库归档 zip 下载并展开本地快照
- 已建立如下本地镜像目录：
  - `reghdfe/`
  - `ivreghdfe/`
  - `ppmlhdfe/`
  - `did_imputation/`
  - `eventstudyinteract/`
  - `rdrobust/`
- 每个目录当前同时保留：
  - 原始 zip 快照
  - 解压后的源码目录
  - 本地 README 占位说明

说明：

- 这些内容用于离线研究与算法对照，不代表可直接搬运到 Python 实现。
- 后续应在对应 `docs/research/*.md` 中补版本、许可证、源码入口和最小实现子集。
