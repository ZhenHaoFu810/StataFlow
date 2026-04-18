# 下一轮任务包 004 返工：Wrapper Postestimation 公开语义收口

## 基本信息

- 任务名称：Wrapper Postestimation 公开语义收口
- 所属阶段：开源初版下一轮
- 来源：任务包 004 被 Codex 退回后的定向返工
- 优先级：P0
- 执行人：Claude Code
- 审查人：Codex

## 返工目标

本次返工 **不要求新增新的计量算法**，只要求把公开 API 文档与真实 wrapper 语义收口。

当前阻塞点是：

- `compat.stata` wrapper 实际返回 `ResultSchema`
- 但 README 与支持矩阵把这些 wrapper 描述成直接支持 `.predict()` / `.margins()`

必须先解决这个公开语义冲突，才能把仓库当作开源 Alpha 对外发布。

## 必读材料

1. `workspace/current-task/review-next-round-package-004-codex.md`
2. `README.md`
3. `docs/command-support-matrix/README.md`
4. `docs/command-support-matrix/logit.md`
5. `docs/command-support-matrix/probit.md`
6. `docs/command-support-matrix/poisson.md`
7. `docs/command-support-matrix/ppmlhdfe.md`
8. `src/statapy/compat/stata/`

## 必须完成的工作

### A. 统一 wrapper 的公开语义

必须明确并落实一种方案：

1. **保留当前语义**
   - wrapper 返回 `ResultSchema`
   - 文档不能再暗示可以直接 `.predict()` / `.margins()`

或

2. **提升当前语义**
   - wrapper 返回支持 postestimation 的对象
   - 需要真正补接口和测试

不得维持当前“代码一种语义，文档另一种语义”的状态。

### B. 更新公开文档

至少必须同步更新：

- `README.md`
- `docs/command-support-matrix/README.md`
- 受影响命令的支持矩阵
- `workspace/current-task/REPORT.md`

### C. 增加公共接口测试

必须新增直接针对 wrapper 返回对象的测试，明确断言：

- 哪些方法存在
- 哪些方法不存在

不能再只靠估计器层测试来掩盖 wrapper 语义错误。

## 明确不做

- 不新增新的命令
- 不扩新的估计能力
- 不提前开启下一轮规划

## 验收标准

- [ ] README 示例与真实公开 API 一致
- [ ] 支持矩阵不再夸大 wrapper postestimation 能力
- [ ] wrapper 返回对象语义有直接测试覆盖
- [ ] `pytest tests -v` 通过
