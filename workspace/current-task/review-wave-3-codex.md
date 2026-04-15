# Wave 3 Codex Review

## 结论

本轮 **不通过，需要返工**。

阻塞原因不是测试套件没过，而是当前 `Binary / Count` 实现中存在会系统性影响统计推断口径的数学问题。现有 golden tests 主要覆盖了系数、标准误和部分拟合统计量，但没有覆盖这些推断层字段，因此不能据此认定整个 Wave 3 已达成 “Stata 对齐”。

## 阻塞项

### 1. `logit` / `probit` / `poisson` 使用了 `t` 分布而不是 `z` 分布

- 文件：`src/statapy/estimators/glm.py`
- 证据：
  - 顶部导入 `t_dist`
  - `p_values = 2 * (1 - t_dist.cdf(...))`
  - `t_crit = t_dist.ppf(...)`
- 问题：
  - Stata 的 `logit`、`probit`、`poisson` 属于 MLE 框架，默认报告 **z-statistics** 与基于标准正态分布的 p 值/置信区间，不应使用 OLS 风格的 t 分布。
  - 这不是显示层差异，而是结果对象本身的统计口径错误。即便当前 golden tests 没覆盖 `p_value` 和 `ci`，公开 API 已经暴露了错误推断结果。
- 处理要求：
  - 将 MLE 路径的显著性检验与置信区间改为正态分布。
  - 对 `logit`、`probit`、`poisson` 分别补至少一组字段级测试，明确校验 `p_value` / `ci_low` / `ci_high`。

### 2. `probit` 的 robust / cluster sandwich meat 用错了 score

- 文件：`src/statapy/estimators/glm.py`
- 证据：
  - `Probit._compute_vce()` 中 robust 分支使用 `residuals = y - mu`
  - cluster 分支使用 `score_g = X_g.T @ r_g`
- 问题：
  - `probit` 不是 canonical link。其观测得分不是简单的 `x_i (y_i - p_i)`，而应为：
    - `x_i * φ_i * (y_i - p_i) / (p_i * (1 - p_i))`
  - 因此 robust 和 cluster 的 meat 不能直接照搬 logit / poisson 的残差形式。
  - 现在 `vce="robust"` 和 `vce="cluster"` 虽然 API 可调用，但数学上不正确。哪怕 Wave 3 本轮只把 `vce="ols"` 作为硬要求，也不能让错误实现继续公开暴露。
- 处理要求：
  - 用正确的 probit score 重写 robust / cluster meat。
  - 至少新增一组 probit robust 或 probit cluster 的 synthetic 对齐样例，证明修正后的 VCE 真正对齐 Stata。
  - 如果暂时不准备对齐，则应明确关闭该路径，而不是保留错误实现。

### 3. `PPMLHDFE.fit(vce="ols")` 实际实现的是 robust sandwich，不是 conventional OIM/OLS

- 文件：`src/statapy/estimators/ppmlhdfe.py`
- 证据：
  - `if vce == "ols":` 分支下有注释：`ppmlhdfe always reports robust/sandwich SEs even without explicit vce option`
  - 分支中使用了 `meat = X' diag((y-mu)^2) X` 的 sandwich 形式，而不是 conventional Hessian inverse
- 问题：
  - 任务卡和公开接口都把这一分支暴露为 `fit(vce="ols")`。
  - 但实现本质上不是 “OLS/conventional” 口径，而是稳健口径。若 Stata 命令显式写了 `vce(ols)`，则这里的 Python 语义就是错误映射。
  - 如果你要主张 `ppmlhdfe` 默认应当是 robust，那也应该通过 API 和结果元数据明确体现，而不是让 `vce="ols"` 走 robust。
- 处理要求：
  - 二选一：
    1. 严格实现 `vce="ols"` 的 conventional VCE，并保持当前 API；
    2. 重构 API / 命令映射，把默认行为与 `vce="ols"` 语义明确区分。
  - 无论采用哪种方案，都需要补测试证明 Stata 与 Python 的 `vcetype` 和标准误口径一致。

## 非阻塞但需要关注

### 4. Wave 3 回报把 `ppmlhdfe` 的默认稳健推断与任务卡要求混在一起

- 当前回报中既写了 `fit(vce="ols")`，又写了 `ppmlhdfe` 默认 robust 的实现逻辑。
- 这会导致审查口径混乱：到底当前 wave 是在对齐 `vce(ols)`，还是在对齐命令默认值？
- 返工时必须在回报中把这点说清楚，避免再用“测试过了”掩盖统计语义不一致。

## 返工后的最低重新验收要求

至少需要重新提供以下证据：

```bash
python -m pytest tests/golden/test_w3_logit_basic.py -v
python -m pytest tests/golden/test_w3_logit_real.py -v
python -m pytest tests/golden/test_w3_probit_basic.py -v
python -m pytest tests/golden/test_w3_probit_real.py -v
python -m pytest tests/golden/test_w3_poisson_basic.py -v
python -m pytest tests/golden/test_w3_poisson_real.py -v
python -m pytest tests/golden/test_w3_ppmlhdfe_basic.py -v
python -m pytest tests/golden/test_w3_ppmlhdfe_cluster.py -v
python -m pytest tests/golden/test_w3_ppmlhdfe_real_gravity.py -v
python -m pytest tests -v
```

此外必须新增至少以下一种：

- `probit` 的 robust 或 cluster 黄金测试
- `logit/probit/poisson` 的 `p_value` / `ci` 字段测试
- `ppmlhdfe` 的 `vcetype` / VCE 语义测试

## 当前状态建议

- 不要推进到下一 wave。
- 先把 Wave 3 返工收口。
- 只有当：
  - MLE 模型的推断分布改正为 `z`
  - probit 的 sandwich score 修正完毕
  - `ppmlhdfe` 的 `vce="ols"` 语义与实现一致
  才能重新进入审查。
