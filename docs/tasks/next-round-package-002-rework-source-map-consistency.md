# 下一轮任务包 002 返工：HDFE Source Map 一致性收口

## 基本信息

- 任务名称：HDFE Source Map 一致性收口
- 所属阶段：开源初版下一轮
- 来源：任务包 002 被 Codex 退回后的定向返工
- 优先级：P0
- 执行人：Claude Code
- 审查人：Codex

## 返工目标

本次返工 **不新增功能范围**，只做一件事：

把 `reghdfe`、`ivreghdfe`、`ppmlhdfe` 三份 source-to-python mapping 文档与当前真实实现、wrapper 暴露面、测试证据链完全对齐。

## 必读材料

1. `workspace/current-task/review-next-round-package-002-codex.md`
2. `docs/research/reghdfe-source-map.md`
3. `docs/research/ivreghdfe-source-map.md`
4. `docs/research/ppmlhdfe-source-map.md`
5. `src/statapy/compat/stata/hdfe.py`
6. `src/statapy/compat/stata/iv.py`
7. `src/statapy/estimators/absorbing_ols.py`
8. `src/statapy/estimators/iv.py`
9. `src/statapy/estimators/ppmlhdfe.py`
10. `tests/test_hdfe_synthetic.py`

## 必须完成的工作

### A. 修正三份 source map 的过期结论

必须修正至少以下矛盾：

- `reghdfe-source-map.md` 中关于 `vce(robust)` “尚未实现”的旧结论
- `ivreghdfe-source-map.md` 中关于 `vce(robust)` “尚未支持”的旧结论
- `ppmlhdfe-source-map.md` 中关于 `offset/exposure` “未暴露/未实现”的旧结论

### B. 为每份 source map 增加统一结构

每份文档都必须单独增加 3 个小节：

1. `已实现且有明确源码依据`
2. `已实现，但属于 Phase A 的等价实现`
3. `未实现或显式拒绝`

不能再把“已实现但只是最小子集”和“尚未实现”混在一起。

### C. 更新执行报告

`workspace/current-task/REPORT.md` 必须：

- 更新为与最新测试状态一致
- 不再保留 `400/401 passed` 等旧结论
- 明确写清：这次返工只收口文档与证据链，不新增算法范围

## 明确不做

- 不新增 HDFE 功能
- 不扩新的参数面
- 不修改 backlog 规划
- 不提前开始任务包 003

## 验收标准

- [ ] 三份 source map 不再包含与当前实现矛盾的旧结论
- [ ] 每份 source map 都有统一的三段式收口结构
- [ ] `REPORT.md` 与最新测试结果一致
- [ ] `pytest tests/test_hdfe_synthetic.py -v` 通过
- [ ] `pytest tests -v` 通过
