# Validation 导览

这个目录是对外证据册的入口。

## 建议先读

- [overview.md](./overview.md)
- [evidence-matrix.md](./evidence-matrix.md)
- [dataset-registry.md](./dataset-registry.md)
- [validation-policy.md](./validation-policy.md)

## 已生成的结果汇总

- [research/results/validation/evidence-summary.md](../../research/results/validation/evidence-summary.md)
- [research/results/validation/oos/oos_master_summary.md](../../research/results/validation/oos/oos_master_summary.md)

## 执行脚本层

validation runner 保留在：

- [scripts/validation](../../scripts/validation)
- [scripts/validation/oos](../../scripts/validation/oos)

这个干净版本里，对外主证据优先使用基于公开真实数据的 Stata 17 双跑结果。开发期 synthetic tests 仍保留在代码库中作为回归保护，但不是这份开源副本对外说明可靠性的核心层。
