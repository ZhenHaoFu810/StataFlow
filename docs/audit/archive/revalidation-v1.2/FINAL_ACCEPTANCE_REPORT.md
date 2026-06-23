# Revalidation v1.2 最终开发验收报告

验收日期：2026-06-12

起始基线：`dev` 分支 `777b43f`

结论：**代码与本地 Stata 17 验收通过，可以提交；GitHub 推送仍取决于认证和代理恢复。**

## 最终验证结果

| 验证项 | 结果 |
|---|---|
| 非 Golden | `349 passed, 0 failed` |
| 完整 Golden | `835 passed, 4 skipped, 0 xfailed, 0 failed` |
| Python 编译 | `python -m compileall -q src/stataflow` 通过 |
| wheel | `stataflow-1.1.0-py3-none-any.whl` 构建成功 |
| diff hygiene | `git diff --check` 通过 |
| Stata 社区命令 | `csdid`、`did_imputation`、`eventstudyinteract` 均 `_rc=0` |

## 本轮关闭的问题

### CSDID 自定义聚类

- `simple/group/calendar/event/pretrend` 统一使用 cluster-level influence-function covariance。
- `simple` 仅聚合处理后 group-time ATT。
- `pretrend` 联合检验全部处理前 group-time ATT。
- group/calendar/event 返回完整协方差矩阵，不再只保留对角线。
- 新增 5 项 Stata 17 自定义聚类事后统计双跑，全部通过。

### HDFE 二维聚类

- 根因不是 LSDV/MAP 必须重构，而是旧实现遗漏 `reghdfe` 在标准化尺度执行 CGM PSD 修正的顺序。
- `fix_psd_reghdfe()` 已按上游源码修正，随后还原变量尺度。
- 合成与 wagepan 的 slope 和 `_cons` SE 均按 `<1e-6` 对齐。
- 删除两个 `_cons` `xfail`，32 项二维聚类 Golden 全部硬通过。
- 删除约 180 行从未调用的旧 MAP 常数方差近似代码。

### Factor-aware margins

- factor expansion 保留简单 `i.var` 的离散列元数据。
- logit/probit/poisson 的 AME 与 MEM 对 indicator 使用 0→1 离散变化。
- 修复 delta method 隐藏 `_cons` 输出时错误删除常数协方差贡献的问题。
- 3 个模型、AME/MEM 共 6 项 Stata 17 双跑的点估计和 SE 全部通过。
- 含因子交互的 margins 明确抛出 `NotImplementedError`，不再静默返回错误数值。

### StataRunner 与诊断脚本

- 相对 `output_dir` 统一转为绝对路径，避免 `cwd` 与 `cd` 重复解释。
- `stata/cases/check_install.do` 作为正式诊断资产保留；单个社区命令缺失不会中断后续检查。
- 调用方法已写入 `docs/operations/local-stata-invocation.md`。

## 残余说明

- 4 个 skipped Golden 为既有条件性跳过，不是本轮失败。
- 测试仍报告依赖弃用、数据列名转换和预期数值警告，但没有失败或新的统计阻断项。
- 本地构建目录和 Stata 输出按项目 `.gitignore` 管理，不纳入提交。

## 发布判断

本地代码验收通过。提交前应纳入本报告、返工任务、实施计划、新增 Golden/单元测试和正式 Stata 安装诊断脚本。

GitHub 发布仍需满足：

1. `gh auth status` 成功；
2. Git 全局代理 `127.0.0.1:10808` 可连接或已移除；
3. 明确将独立 `dev` 历史推送至 `origin/dev`，或按既定 public-main 同步流程发布；不得直接 force push `origin/main`。
