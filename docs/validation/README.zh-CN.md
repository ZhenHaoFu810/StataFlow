# Validation 导览

[English](../../VALIDATION.md)

本目录汇总 StataFlow 1.2.0 的公开 Stata 17 验证证据。

## 建议阅读顺序

- [验证总览](./overview.md)
- [证据矩阵](./evidence-matrix.md)
- [数据集登记](./dataset-registry.md)
- [验证政策](./validation-policy.md)
- [可复现验证用例](./reproducible-validation.md)

## 发布证据

- [机器可读汇总 JSON](../../research/results/validation/evidence-summary.json)
- [可读汇总](../../research/results/validation/evidence-summary.md)

2026 年 7 月冻结的发布范围包含 `40/40` 个数值对照和 1 项 DID
功能检查；公开、自包含的 Stata 17 验证套件包含 10 个可复现用例。
完整本地验证为 `856 passed, 12 skipped`；其中 8 项是明确不支持的
加权 GLM/PPML 契约，4 项是 Stata 在相应 IV VCE 下不保存的字段，
均不属于数值比较失败。
历史 OOS 记录用于补充说明不同公开样本上的表现，不属于 1.2.0
冻结汇总。
