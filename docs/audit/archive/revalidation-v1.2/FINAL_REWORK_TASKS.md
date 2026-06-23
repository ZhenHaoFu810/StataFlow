# Revalidation v1.2 最终返工任务

## P1-1 修复 CSDID 自定义聚类后估计

涉及文件：

- `src/stataflow/estimators/csdid.py`
- `tests/test_compat_stata_did.py`
- 新增或扩展 CSDID Golden 测试

要求：

1. 提取统一的 IF covariance helper，输入 unit-level IF 矩阵和 unit-to-cluster 映射。
2. 自定义 cluster 时先在 cluster 内求和 IF，再按与 Stata `csdid` 一致的归一化和小样本口径计算 covariance。
3. `estat event/simple/group/calendar/pretrend` 必须复用同一聚类实现。
4. 结果中的 SE、VCE、Wald statistic、p-value、`cluster_count`、`df_resid` 必须来自同一 estimation sample。
5. 增加 cluster 不等于 unit、每个 cluster 包含多个 unit 的回归测试。
6. 增加 Stata 17 双跑，至少验证 `csdid_estat simple`、`group`、`calendar` 和 `pretrend`。

禁止只修改报告值、缩放常数或测试容差来适配当前样例。

## P1-2 缩小或消除 HDFE `xfail`

涉及文件：

- `tests/golden/test_w7_reghdfe_2way_cluster.py`
- `tests/golden/test_w7_reghdfe_2way_cluster_real.py`
- `src/stataflow/estimators/absorbing_ols.py`（若修复实现）

要求：

1. slope SE 必须由普通测试按 `<1e-6` 断言，任何 slope 回归必须使测试失败。
2. `_cons` 检查拆成独立测试，不能用函数级 `xfail` 包住全部系数。
3. 优先修复 `_cons` SE，使 synthetic 和 real-data 均满足 `<1e-6`。
4. 若确实无法修复，必须由用户明确批准修改项目验收标准或公开支持声明；Agent 无权自行将 P1 偏差视为完成。

## P1-3 处理其余开放项

逐项关闭或由用户明确裁定：

- `VCE-002`
- `VCE-003`
- `VCE-004`
- `GLM-003`

`REMEDIATION_REPORT.md`、支持矩阵、ADR 和测试状态必须一致，不得同时出现“开发完成”和“Open / Known limitation”。

## P2-1 清理交付状态

1. 决定 `stata/cases/check_install.do` 是正式诊断脚本还是临时文件；正式文件需补充用途说明并提交，临时文件应删除或忽略。
2. 清理本地 wheel/测试输出。
3. 修复 `git diff --check` 报告的行尾空格。
4. 确认 `git status --short` 为空。

## P2-2 恢复 GitHub 发布能力

1. 用户重新执行 `gh auth login -h github.com`，随后确认 `gh auth status` 成功。
2. 确认本机 `127.0.0.1:10808` 代理已启动，或由用户调整其全局 Git 代理配置。
3. 明确发布拓扑：
   - 内部开发备份：推送 `dev` 到 `origin/dev`；或
   - 公开发布：将审核后的提交同步到 `public-main` 历史，再通过 `origin/main` 发布。
4. 禁止对 `origin/main` 使用 force push，除非用户明确要求并已完成远端备份。

## 最终验收命令

```powershell
pytest tests/ -q --ignore=tests/golden/ --ignore=tests/benchmarks/
pytest tests/golden/ -q
python -m compileall -q src/stataflow
python -m pip wheel . --no-deps -w dist_acceptance
git diff --check
git status --short
```

验收要求：

- 普通测试 0 failed
- Golden 0 failed；不得用过宽 `xfail` 隐藏已支持字段
- 所有宣称严格复现的字段满足项目规定容差
- 工作树清洁
- 发布分支与目标远端历史关系明确
