# 审计主线任务包 005 返工：DID 报告证据链收口
## 任务定位

`did_imputation`、`eventstudyinteract`、`csdid` 的代码、测试、source map、support matrix 已经通过 Codex 复核。  
当前只剩 `workspace/current-task/REPORT.md` 的 fresh-run 证据仍是旧数字，尚未与当前真实 rerun 结果同步。

本轮返工 **不涉及任何算法修复**，只做报告证据链收口。

## 目标

把 `workspace/current-task/REPORT.md` 中的 fresh-run 数字更新为当前真实 rerun 结果，并让结论段与之保持一致。

## 必须先阅读

1. `workspace/current-task/review-audit-mainline-package-005-codex.md`
2. `docs/operations/executor-playbook.md`
3. `docs/operations/codex-review-protocol.md`

## 允许修改的文件

- `workspace/current-task/REPORT.md`

## 明确禁止

- 不改 `src/`
- 不改 `docs/research/`
- 不改 `docs/command-support-matrix/`
- 不新增或修改测试
- 不顺手处理其他包的问题

## 应写入报告的 fresh-run 结果

```powershell
python -m pytest tests/test_compat_stata_did.py tests/golden/test_w4_did_imputation_basic.py tests/golden/test_w4_eventstudyinteract_basic.py tests/golden/test_w4_csdid_basic.py tests/golden/test_w4_did_imputation_real_ezunem.py tests/golden/test_w4_eventstudyinteract_real_ezunem.py tests/golden/test_w4_csdid_real_ezunem.py -v
# 35 passed, 2 warnings

python -m pytest tests -v
# 681 passed, 2 warnings
```

## 通过标准

Codex 只会在以下条件同时满足时放行：

1. `REPORT.md` 第 5 节 fresh-run 数字已经和当前真实 rerun 一致。
2. 结论段不再保留旧数字。
3. 本轮没有顺手改动与报告无关的任何代码或文档。
