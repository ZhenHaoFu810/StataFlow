# 返工任务卡：Package D - Codex Review Rework

## 背景

`Package D` 首轮交付已经通过本地测试，但在 Codex 复审中发现了三处阻断问题，因此当前版本不能视为通过：

1. two-way clustering 的 intersection cluster id 采用字符串拼接构造，存在真实碰撞风险，会导致不同的 `(c1, c2)` 组合被错误合并，进而产生错误的 covariance 估计。
2. `xtreg_fe` / `areg` 的 wrapper 签名现在接受 `list[str]` 作为 `cluster`，但底层 estimator 并未接入 multi-way clustering，实际调用会抛出底层 `TypeError: unhashable type: 'list'`，不是清晰、受控的 `ValueError`。
3. support matrix 没有同步完成：`docs/command-support-matrix/regress.md` 仍把 `cluster` 写成单个 `str`，与当前实现不一致。

此外，`REPORT.md` 中关于 `xtreg_fe` / `areg` “会触发 `ValueError`” 的表述也是错误的，必须一并修正。

## 返工目标

只修复上述阻断问题，不扩新功能，不改变 `Package D` 的主目标。

## 必修项

## D-R1. 修复 two-way clustering 的 intersection id 碰撞

当前实现位于：

- [src/stataflow/estimators/ols.py](</D:/OneDrive - SAIF/PhD3/StataFlow/src/stataflow/estimators/ols.py>)

现状问题：

- 代码使用 `f"{a}__{b}"` 形式构造 intersection cluster id
- 当 cluster 标签本身包含分隔符时，会把不同组合错误地映射到同一个组合 id
- 这是正确性问题，不是文档问题

你必须改成**不会碰撞**的组合表示方式，例如：

- tuple / MultiIndex / structured array / factorize over exact pair objects

要求：

- 行为对数值型和字符串型 cluster 标签都正确
- 不依赖“用户标签里通常不会出现某个分隔符”这种假设
- 补至少一个针对字符串标签碰撞场景的测试

## D-R2. 修复 `xtreg_fe` / `areg` 的误导性接口行为

当前实现位于：

- [src/stataflow/compat/stata/linear.py](</D:/OneDrive - SAIF/PhD3/StataFlow/src/stataflow/compat/stata/linear.py>)
- [src/stataflow/estimators/fe.py](</D:/OneDrive - SAIF/PhD3/StataFlow/src/stataflow/estimators/fe.py>)
- [src/stataflow/estimators/absorbing_ols.py](</D:/OneDrive - SAIF/PhD3/StataFlow/src/stataflow/estimators/absorbing_ols.py>)

现状问题：

- wrapper 签名允许 `cluster: list[str]`
- 但底层 estimator 不支持 multi-way clustering
- 实际调用 `xtreg_fe(..., cluster=["g1", "g2"])` / `areg(..., cluster=["g1", "g2"])` 会抛出：
  - `TypeError: unhashable type: 'list'`

这不符合当前项目一贯的“unsupported parameters are hard-rejected via clear ValueError”规范。

你必须在以下两种方案中选一种，并在报告中说明理由：

1. **收回 wrapper 签名扩展**
   - 让 `xtreg_fe` / `areg` 继续只接受单个 `str`
   - 保持只有 `regress` / `OLS` 暴露 two-way clustering

2. **保留签名扩展，但显式拦截**
   - wrapper 或底层 estimator 必须对 `list[str]` 做清晰、受控的 `ValueError`
   - 错误信息要明确说明“当前仅 `regress` 支持 two-way clustering，其他命令尚未支持”

无论选哪种，都必须：

- 不能再出现底层 `TypeError`
- 行为与文档一致
- 报错语义清楚

## D-R3. 修正文档与报告漂移

必须同步修正：

- [docs/command-support-matrix/regress.md](</D:/OneDrive - SAIF/PhD3/StataFlow/docs/command-support-matrix/regress.md>)
- [workspace/current-task/REPORT.md](</D:/OneDrive - SAIF/PhD3/StataFlow/workspace/current-task/REPORT.md>)

至少应修正：

- `regress.md` 中 `cluster` 仍写成 `str`
- `regress.md` 未明确 two-way clustering 已支持
- `REPORT.md` 中关于 `xtreg_fe` / `areg` “会触发 `ValueError`” 的表述不准确，必须改成返工后的真实行为

## 测试要求

至少补以下测试之一，且推荐都补：

- two-way clustering 在字符串标签含分隔符时不会错误合并 intersection clusters
- `xtreg_fe` / `areg` 对 list cluster 的行为是受控且清晰的

如果你选择“收回 wrapper 签名扩展”，测试应体现：

- `xtreg_fe` / `areg` 对 multi-way cluster 明确拒绝

如果你选择“保留签名扩展但显式拦截”，测试应体现：

- 报错类型是 `ValueError`
- 报错消息准确说明当前支持边界

## 不在返工范围内的事项

- 不扩展 `xtreg_fe` / `areg` / `reghdfe` / `ivreghdfe` / `ppmlhdfe` 的 two-way clustering 真正实现
- 不引入新的 clustering 维度（3-way+）
- 不扩展 weights
- 不推进 wrapper post-estimation

## 交付要求

返工完成后，`REPORT.md` 必须新增一个“返工说明”小节，明确写：

1. Codex 复审指出了哪三类问题
2. 你分别如何修复
3. 新增了哪些测试
4. 文档和报告如何同步纠正

## 完成标准

只有当以下条件全部满足时，返工才算完成：

- two-way clustering 的 intersection id 不再有分隔符碰撞风险
- `xtreg_fe` / `areg` 不再因 `list[str]` 输入抛出 `TypeError`
- `regress.md` 与当前实现边界一致
- `REPORT.md` 与返工后真实行为一致
- 相关测试通过，可再次交给 Codex 复审
