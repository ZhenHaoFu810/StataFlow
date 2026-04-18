# 审计主线任务包 002：`reghdfe` 完整度推进（Phase B）

## 1. 背景

根据 [docs/audit/next-development-plan.md](</D:/OneDrive - SAIF/PhD3/Stata2Python/docs/audit/next-development-plan.md>)，`rdrobust` 进入主线后，下一优先级不是继续横向扩语法，而是把最有价值的 vendor 命令做深、做全、做准。

当前 `reghdfe` 的审计结论是：

- 已有高质量 Phase A 子集
- 高频场景已可用
- 但距离“完整、全面、正确复现 `reghdfe`”仍有明显缺口

本轮任务只做一件事：**把 `reghdfe` 从当前 Phase A 推进到更完整的 Phase B**。

## 2. 总目标

本轮至少在以下三个方向中，真实补齐一批之前明确缺失的 `reghdfe` 能力：

1. `absorb()` 语义与 HDFE 处理边界
2. singleton / keepsingletons / DoF 行为
3. `predict` 或结果对象语义的 `reghdfe` 命令级完善

本轮不要求把 `reghdfe` 一次做成最终态，但必须让审计文档里的 “planned / missing” 项显著减少。

## 3. 必须完成的内容

### A. 源码支撑下的缺口收口

优先基于本地源码镜像：

- [research/vendor/stata_community/reghdfe](</D:/OneDrive - SAIF/PhD3/Stata2Python/research/vendor/stata_community/reghdfe>)
- [docs/research/reghdfe-source-map.md](</D:/OneDrive - SAIF/PhD3/Stata2Python/docs/research/reghdfe-source-map.md>)

至少补齐下列缺口中的 **2-3 个实质项**：

- `keepsingletons`
- 更明确的 singleton dropping 证据
- `df_a` / nested FE / absorbed DoF 的更完整实现或更精确语义
- `predict` 子选项扩展
- wrapper 层 `absorb()` 更完整的 Stata 风格输入处理

### B. 不能只做“参数能传进去”

如果新增某个参数或行为，必须同时满足：

- wrapper 可调用
- core estimator 真正实现该语义
- support matrix 更新
- source map 更新
- 至少一类测试覆盖该行为

禁止只把参数暴露出来但内部静默忽略。

### C. 必须显式区分“实现”和“拒绝”

对于本轮仍不做的 `reghdfe` 能力，必须在文档中显式写出：

- 未实现
- 为什么未实现
- 是否计划在后续包里实现

不允许继续使用“部分支持”但不说明具体边界的描述。

## 4. 测试要求

### A. synthetic tests

至少补一个直接针对本轮新增行为的 synthetic case，例如：

- singleton dropping vs keepsingletons
- nested FE DoF 变化
- `predict` 子选项语义

### B. Stata dual-run

至少补 1 个新的 `reghdfe` dual-run case，必须真正命中本轮新增能力。

### C. full regression

完成后至少回报：

```powershell
python -m pytest tests/test_hdfe_synthetic.py -v
python -m pytest tests/golden/test_p3_reghdfe_basic.py tests/golden/test_p3_reghdfe_cluster.py tests/golden/test_p3_reghdfe_two_fe.py tests/golden/test_p3_reghdfe_real_panel.py -v
python -m pytest tests -v
```

## 5. 文档要求

必须同步更新：

- [docs/research/reghdfe-source-map.md](</D:/OneDrive - SAIF/PhD3/Stata2Python/docs/research/reghdfe-source-map.md>)
- [docs/command-support-matrix/reghdfe.md](</D:/OneDrive - SAIF/PhD3/Stata2Python/docs/command-support-matrix/reghdfe.md>)
- 如有必要，更新 [docs/backlog.md](</D:/OneDrive - SAIF/PhD3/Stata2Python/docs/backlog.md>) 和 [docs/testing/test-case-catalog.md](</D:/OneDrive - SAIF/PhD3/Stata2Python/docs/testing/test-case-catalog.md>)

## 6. 禁止事项

本轮不要顺手做：

- `ppmlhdfe` 新功能
- `ivreghdfe` 新功能
- DID 命令扩展
- 新一轮通用 factor grammar 扩展

除非某项工作是本轮 `reghdfe` 新行为的直接依赖。

## 7. 完成标准

本轮通过的最低标准：

- `reghdfe` 的 support matrix 中，至少一批此前 planned / missing 的条目被真实消化
- 有新增源码映射证据，而不是只靠测试过
- synthetic + dual-run + full regression 都通过
- 报告中明确写清楚“本轮补了什么、还缺什么”

如果报告把本轮夸大成“`reghdfe` 已完整复现”，视为未完成。
