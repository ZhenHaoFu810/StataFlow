# 审计主线任务包 003：`ppmlhdfe` 完整度推进（Phase B）

## 1. 背景

根据 [docs/audit/next-development-plan.md](</D:/OneDrive - SAIF/PhD3/Stata2Python/docs/audit/next-development-plan.md>)，在 `reghdfe` 主线推进之后，下一优先级是把 `ppmlhdfe` 从“高频主路径可用”推进到更接近完整命令。

当前 `ppmlhdfe` 的审计结论是：

- `absorb()`、`offset`、`exposure`、`vce(robust|cluster)`、基础 `predict` 已可用
- synthetic 与 gravity 风格 real-data 双跑已建立
- 但 separation、优化/收敛控制、输出层与命令边界仍明显不完整

本轮任务只做一件事：**把 `ppmlhdfe` 从当前高频子集推进到更完整的 Phase B**。

## 2. 总目标

本轮至少在以下三个方向中，真实补齐一批之前明确缺失的 `ppmlhdfe` 能力：

1. separation 行为与显式边界
2. 优化/收敛相关命令语义
3. `predict` / 结果对象 / wrapper 参数面的进一步完善

本轮不要求把 `ppmlhdfe` 一次做成最终态，但必须让审计文档里的 planned / missing 条目显著减少。

## 3. 必须完成的内容

### A. 源码支撑下的缺口收口

优先基于本地源码镜像：

- [research/vendor/stata_community/ppmlhdfe](</D:/OneDrive - SAIF/PhD3/Stata2Python/research/vendor/stata_community/ppmlhdfe>)
- [docs/research/ppmlhdfe-source-map.md](</D:/OneDrive - SAIF/PhD3/Stata2Python/docs/research/ppmlhdfe-source-map.md>)

至少补齐下列缺口中的 **2-3 个实质项**：

- separation 的更明确实现或更明确的显式拒绝边界
- 收敛/优化参数的命令级支持
- `predict` 子选项扩展
- wrapper 层 `offset` / `exposure` / 其他已实现参数的更完整 Stata 风格语义
- 结果对象中的 `ppmlhdfe` 命令级字段完善

### B. 不能只做“参数能传进去”

如果新增某个参数或行为，必须同时满足：

- wrapper 可调用
- core estimator 真正实现该语义
- support matrix 更新
- source map 更新
- 至少一类测试覆盖该行为

禁止只把参数暴露出来但内部静默忽略。

### C. 必须显式区分“实现”和“拒绝”

对于本轮仍不做的 `ppmlhdfe` 能力，必须在文档中显式写出：

- 未实现
- 为什么未实现
- 是否计划在后续包里实现

不允许继续使用“部分支持”但不说明具体边界的描述。

## 4. 测试要求

### A. synthetic tests

至少补一个直接针对本轮新增行为的 synthetic case，例如：

- separation 触发与拒绝路径
- 新增优化参数的效果或边界
- `predict` 新子选项语义

### B. Stata dual-run

至少补 1 个新的 `ppmlhdfe` dual-run case，必须真正命中本轮新增能力。

### C. full regression

完成后至少回报：

```powershell
python -m pytest tests/test_hdfe_synthetic.py -v
python -m pytest tests/golden/test_w3_ppmlhdfe_basic.py tests/golden/test_w3_ppmlhdfe_cluster.py tests/golden/test_w3_ppmlhdfe_real_gravity.py -v
python -m pytest tests -v
```

## 5. 文档要求

必须同步更新：

- [docs/research/ppmlhdfe-source-map.md](</D:/OneDrive - SAIF/PhD3/Stata2Python/docs/research/ppmlhdfe-source-map.md>)
- [docs/command-support-matrix/ppmlhdfe.md](</D:/OneDrive - SAIF/PhD3/Stata2Python/docs/command-support-matrix/ppmlhdfe.md>)
- 如有必要，更新 [docs/backlog.md](</D:/OneDrive - SAIF/PhD3/Stata2Python/docs/backlog.md>) 和 [docs/testing/test-case-catalog.md](</D:/OneDrive - SAIF/PhD3/Stata2Python/docs/testing/test-case-catalog.md>)

## 6. 禁止事项

本轮不要顺手做：

- `ivreghdfe` 新功能
- DID 命令扩展
- 新一轮通用 factor grammar 扩展
- 与 `ppmlhdfe` 无关的估计器扩展

除非某项工作是本轮 `ppmlhdfe` 新行为的直接依赖。

## 7. 完成标准

本轮通过的最低标准：

- `ppmlhdfe` 的 support matrix 中，至少一批此前 planned / missing 的条目被真实消化
- 有新增源码映射证据，而不是只靠测试过
- synthetic + dual-run + full regression 都通过
- 报告中明确写清楚“本轮补了什么、还缺什么”

如果报告把本轮夸大成“`ppmlhdfe` 已完整复现”，视为未完成。
