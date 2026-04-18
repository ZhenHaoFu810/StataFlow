# 下一轮任务包 001：命令层 API 与支持矩阵收口

## 基本信息

- 任务名称：命令层 API 与支持矩阵收口
- 所属阶段：开源初版下一轮
- 对应 backlog 条目：
  - `compat.stata` 命令层
  - `regress`
  - `xtreg_fe`
  - `areg`
  - `reghdfe`
  - `ivregress 2sls`
  - `ivreghdfe`
  - `logit`
  - `probit`
  - `poisson`
  - `ppmlhdfe`
  - `did_imputation`
  - `eventstudyinteract`
  - `csdid`
- 优先级：P0
- 执行人：Claude Code
- 审查人：Codex

## 目标

本任务包的目标不是扩张新的计量功能，而是把当前已经存在的估计器内核变成一个真正可开源使用的 Stata 命令映射层，并建立正式的支持矩阵文档。

完成后应满足：

1. 用户可以通过 Stata 命令名调用当前已实现的高频命令，而不必直接理解内部类名。
2. 每个高频命令都有独立支持矩阵，明确“已支持 / planned / 明确不支持”的参数与行为。
3. 对外接口不得继续依赖 `AbsorbingOLS`、`IVAbsorbingOLS` 这种内部类名来表达命令语义。
4. 不支持的参数必须硬报错，不允许静默忽略。

## 必读文档

1. `docs/operations/executor-playbook.md`
2. `docs/next-round-open-source-plan.md`
3. `docs/architecture/public-api.md`
4. `docs/architecture/overview.md`
5. `docs/backlog.md`
6. `docs/testing/test-case-catalog.md`
7. `docs/operations/codex-review-protocol.md`

## 前置条件

- [ ] 当前 wave 0-5 的既有测试保持可运行
- [ ] 本任务包不擅自扩张新的估计量
- [ ] 本任务包不把“接口包装”伪装成“功能完整迁移”

## 本轮必须交付

### A. 新增命令层目录与入口

新增目录：

- `src/statapy/compat/stata/`

最低文件：

- `src/statapy/compat/__init__.py`
- `src/statapy/compat/stata/__init__.py`
- `src/statapy/compat/stata/linear.py`
- `src/statapy/compat/stata/hdfe.py`
- `src/statapy/compat/stata/iv.py`
- `src/statapy/compat/stata/glm.py`
- `src/statapy/compat/stata/did.py`

最低导出函数：

- `regress`
- `xtreg_fe`
- `areg`
- `reghdfe`
- `ivregress_2sls`
- `ivreghdfe`
- `logit`
- `probit`
- `poisson`
- `ppmlhdfe`
- `did_imputation`
- `eventstudyinteract`
- `csdid`

### B. 新增支持矩阵目录

新增目录：

- `docs/command-support-matrix/`

至少创建以下文件：

- `docs/command-support-matrix/regress.md`
- `docs/command-support-matrix/xtreg-fe.md`
- `docs/command-support-matrix/areg.md`
- `docs/command-support-matrix/reghdfe.md`
- `docs/command-support-matrix/ivregress-2sls.md`
- `docs/command-support-matrix/ivreghdfe.md`
- `docs/command-support-matrix/logit.md`
- `docs/command-support-matrix/probit.md`
- `docs/command-support-matrix/poisson.md`
- `docs/command-support-matrix/ppmlhdfe.md`
- `docs/command-support-matrix/did-imputation.md`
- `docs/command-support-matrix/eventstudyinteract.md`
- `docs/command-support-matrix/csdid.md`

每份支持矩阵至少包含：

- 命令目标
- 当前 Python 入口
- 已支持参数
- 已支持结果字段
- planned 参数
- 明确不支持参数
- 真实对齐证据链接
- 对应内核实现文件

### C. 收口 README 与公开入口

必须更新：

- `README.md`
- `docs/architecture/public-api.md`
- `src/statapy/__init__.py` 或等价公开入口

要求：

- README 示例优先展示命令层 API
- 保留 core estimator 示例，但不再作为唯一主入口
- 明确区分：
  - core estimators
  - Stata compatibility commands

## 明确不做

本任务包不负责：

- 新估计量开发
- `reghdfe` / `ppmlhdfe` / `ivreghdfe` 数学层新增能力
- DID 命令的新增估计方法
- `rdrobust` 实现

如果在包装过程中发现核心实现无法支撑 wrapper 语义，只能登记问题，不得顺手无边界扩算法。

## 核心原则

### 1. 命令语义优先

对外 API 必须尽量遵守 Stata 命令语义，即使内部共用同一内核类。

### 2. 不得静默忽略参数

凡是 wrapper 暴露出来的参数：

- 要么实现
- 要么显式报 `NotImplementedError` / `ValueError`

不得出现“参数收进来但悄悄没生效”。

### 3. 不得伪造完整支持

支持矩阵必须诚实反映当前实现边界。  
如果 `reghdfe` 只支持当前子集，就必须明确写成子集，而不是写成“已实现 reghdfe”。

## 测试要求

### 必须新增

新增命令层 wrapper 测试，至少覆盖：

- wrapper 能正确调用对应 estimator
- wrapper 参数能正确映射到 estimator
- 不支持参数会硬报错
- wrapper 结果对象与原 estimator 结果核心字段一致

建议新增：

- `tests/test_compat_stata_linear.py`
- `tests/test_compat_stata_hdfe.py`
- `tests/test_compat_stata_iv.py`
- `tests/test_compat_stata_glm.py`
- `tests/test_compat_stata_did.py`

### 必须保留

- 既有 golden tests 全部通过
- 不得通过放宽现有容差来让 wrapper 测试通过

## 验收标准

- [ ] `src/statapy/compat/stata/` 正式存在
- [ ] 所有高频命令已具备 wrapper
- [ ] wrapper 的不支持参数会显式报错
- [ ] 支持矩阵文档完整
- [ ] README 与公开 API 文档同步更新
- [ ] wrapper 测试通过
- [ ] 全量测试通过
- [ ] 无“静默忽略参数”行为

## 回报要求

完成后必须在 `workspace/current-task/REPORT.md` 中单独列出：

1. 新增了哪些 wrapper
2. 每个 wrapper 暴露了哪些参数
3. 每个 wrapper 显式拒绝了哪些参数
4. 新增了哪些支持矩阵文档
5. 新增了哪些 wrapper 测试
6. 是否发现当前 core 层与命令语义冲突的地方
