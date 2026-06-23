# Revalidation v1.2 审查计划

## 目标

对当前 `dev` 分支已实现并公开声明支持的功能做只读、全覆盖、苛刻复核。只识别和记录当前缺陷，不实施修复，也不讨论未来功能扩展。

## 范围

- Linear：OLS、FixedEffectsOLS、AbsorbingOLS 及 Stata wrappers
- IV：2SLS、GMM2S、LIML、k-class、weak-IV、IV-HDFE
- GLM：Logit、Probit、Poisson、PPMLHDFE、margins/predict/estat
- DID：DIDImputation、EventStudyInteract、CSDID
- RD：RDRobust、RDPlot
- Shared：factor variables、VCE、ResultSchema、StataRunner、导出和文档
- Evidence：unit、integration、golden、真实数据资产和支持矩阵

## 已完成阶段

- [x] Phase 0：基线与功能清单
- [x] Phase 1：Linear、FE、HDFE、VCE、factor
- [x] Phase 2：IV
- [x] Phase 3：GLM、PPML、postestimation
- [x] Phase 4：DID
- [x] Phase 5：RD、runner、schema、exports
- [x] Phase 6：最小复现和证据分级
- [x] Phase 7：最终报告与一致性检查

## 审查约束

- 不把“测试未覆盖”直接写成“算法错误”。
- 每项结论注明证据状态和影响范围。
- 既有 v1.1 结论仅作为线索，不继承其“已关闭”判断。
- 项目默认精度标准仍为与 Stata 17 字段级相对误差 `<1e-6`。
