# Revalidation v1.2 执行记录

## 2026-06-11

- 建立只读审查框架，未修改 `src/`、`tests/` 或任何测试期望。
- 非 golden 基线：`307 passed, 28 warnings`。
- 编译基线：`python -m compileall -q src/stataflow` 通过。
- 完整 golden：`788 passed, 4 skipped, 16 errors, 74 warnings`，耗时约 16 分 52 秒。
- 16 个 golden error 已定位为 DID 真实数据测试依赖的 Stata 日志缺失。
- 已完成线性、FE、HDFE、factor、共享 VCE、IV、GLM、postestimation、DID、RD、schema、runner 和文档静态审查。
- 已对 FE 共线、完美拟合、重复索引、错误 sample mask、单 cluster、欠识别 IV、非法 GLM outcome 和不收敛 GLM 做最小复现。
- 结论与证据汇总见 `summary.md` 和 `findings.md`。
