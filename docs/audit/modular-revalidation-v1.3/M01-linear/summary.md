# M01 Linear 模块审查总结 v1.3

## 审查目标

对 StataFlow 的 M01 Linear 模块（`OLS` / `regress()`、robust/cluster VCE、aweight、factor variables、sample mask、postestimation）进行完全独立的重新审查，发现数学错误、统计语义偏差、代码缺陷、边界条件错误、结果字段错误和 Stata 17 复现失败。

## 审查基线

- 分支：`dev`
- Commit：`2c7db1ca095e03d29c471e8d523fdaa943306174`
- Python：3.11.7
- Stata：17

## 完成门槛检查

| 门槛 | 状态 | 说明 |
|---|---|---|
| 当前支持能力逐项建立审查矩阵 | ✅ | 支持边界核对结果写入 progress.md |
| 关键数学公式与 Stata 语义已核对 | ✅ | OLS、HC1、cluster、aweight 公式已核对 |
| 至少 6 个实质不同的新 synthetic 双跑 | ✅ | 8 个 synthetic 实验（S1-S7 + S4b） |
| 至少 2 个新的真实数据实验 | ✅ | R1、R2 |
| 至少 3 个 metamorphic/property tests | ✅ | P1、P2、P3 |
| 关键结果使用完整字段级比较 | ✅ | 系数、完整 VCE、df、R²、RMSE、F、cluster count |
| 所有异常均已区分产品/测试/runner/parser 根因 | ✅ | 3 个 confirmed finding 均定位到产品代码 |
| 每个 confirmed finding 均有最小复现 | ✅ | 3 个最小复现脚本 |
| 未复现或未验证部分明确列出 | ✅ | findings.md 列出 4 项未决事项 |
| findings.md、progress.md、test-design-register.md、summary.md 完整 | ✅ | 全部完成 |
| 本轮没有修改产品代码 | ✅ | 仅新增审查资产 |
| 审查资产可以从干净环境重复执行 | ✅ | 脚本使用相对路径，依赖 statsmodels + 项目包 |

## 发现的问题

本轮确认 3 项 P1 问题：

### M01-LIN-001: aweight=0 处理不一致

Python 在 `OLS._prepare_data` 中显式拒绝所有非正权重，而 Stata 17 将 `aweight=0` 视为零权重观测并删除后继续回归。

### M01-LIN-002: 近共线变量未被省略

`detect_collinear_columns` 使用 `np.linalg.matrix_rank` 默认 tolerance，未对齐 Stata 17 的共线性 tolerance。当回归变量近似共线且量纲差异大时，Stata 会明确省略变量，Python 则保留所有变量并产生数值病态系数。

### M01-LIN-003: 两路 cluster F 统计量语义不一致

单路 cluster 时 Python 与 Stata 的 F 一致；两路 cluster 时，Stata 17 的 `e(F)` 等于 OLS F-statistic（使用残差 df），而 Python 报告 cluster-robust Wald F（使用 cluster VCE 和 cluster df）。两者字段语义不同。

## 已验证通过的领域

以下路径在本轮新建实验中字段级对齐（相对误差 < 1e-6）：

- 小样本 OLS 解析真值
- 异方差 robust VCE
- 单路 cluster-robust VCE（含极不均衡组大小）
- 含缺失值的 aweight
- factor 交互项在缺失改变有效 base level 时的参数化
- 行顺序不变性、无关列不变性、尺度变换可推导性
- Engel 真实数据 robust OLS
- 平衡大 G 两路 cluster 的系数/SE/VCE

## 未决/需继续验证事项

1. v1.2 LIN-003（完美拟合除零）未在本轮专门复现；当前代码已加入分支，需新实验验证。
2. aweight + robust/cluster 的权重阶数（v1.2 VCE-005）未专门测试。
3. `OLS.predict` 在 newdata + collinearity drops 路径的字段级双跑未进行。
4. `FixedEffectsOLS` / `AbsorbingOLS` 的共线性处理归 M02/M03 审查。

## 对下游模块的影响

- M01-LIN-002（共线性 tolerance）可能也影响 M02/M03 的 FE/HDFE 路径，因为 `detect_collinear_columns` 是共享基础设施。
- M01-LIN-003（两路 cluster F 语义）可能影响 M04（IV）和 M03（HDFE）的两路 cluster F 统计量，需在对应模块审查中验证。

## 结论

M01 Linear 模块在当前基线下不能被无条件标记为所有路径严格复现 Stata 17。核心估计（OLS、robust、单路 cluster、aweight 缺失处理、factor base 重确定）表现良好，但存在 3 个明确的 P1 偏差，涉及边界权重处理、共线性判定和两路 cluster F 统计量语义。建议在修复后重新验证 M01，并将修复同步应用到共享基础设施。
