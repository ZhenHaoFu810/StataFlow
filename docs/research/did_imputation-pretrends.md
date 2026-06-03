# `did_imputation` pretrends 研究档案

## 命令定位

- 命令族：`DID / Event Study Extensions`
- 类型：`did_imputation` 的 pretreatment 检验子系统
- 规则来源：Borusyak, Jaravel & Spiess (2023) Section 4 + `did_imputation.ado` v2023-11-22
- 关联文件：`research/vendor/stata_community/did_imputation/did_imputation-main/did_imputation.ado` (第 540–591 行)

## 核心洞察

Pretrends 检验不是独立统计程序，而是**同一个 imputation 回归的副产品**：

1. `pretrends(H)` 在控制样本的 TWFE 回归中加入 `H` 个 pretreatment period dummies
2. 这些 dummies 的系数就是 pretreatment 效应估计
3. 联合 F 检验作为 overall pretrend 检验

关键性质：**pretreatment dummies 只进入控制样本的估计回归，不进入 Y0 构造**。它们的存在是为了检验 "控制样本中处理组与对照组是否平行"，而不是为了调整 imputation。

## 数学公式

### 带 pretrends 的 imputation 回归

在控制样本（$D=0$）上运行：

$$
Y_{it} = \alpha_i + \gamma_t + \sum_{h=1}^{H} \pi_h \cdot \mathbf{1}(K_{it} = -h) + \beta' X_{it} + \varepsilon_{it}
$$

其中：
- $K_{it} = t - g_i$ 为相对处理时间
- $\mathbf{1}(K_{it} = -h)$ 是 pretreatment horizon $-h$ 的指示变量
- $\pi_h$ 是 pretreatment 效应（应在原假设下为 0）

### 输出

命令输出矩阵 `b` 中，pretrends 系数位于 tau 系数之后、control 系数之前：
```
b = [tau_0, tau_1, ..., tau_H, pre_1, pre_2, ..., pre_H, beta_1, beta_2, ...]
```

### 联合检验

```stata
test `prenames', df(`pre_df')
ereturn scalar pre_F = r(F)
ereturn scalar pre_p = r(p)
ereturn scalar pre_df = `pre_df'
```

这是标准的 Wald F 检验：
- 原假设：$\pi_1 = \pi_2 = \cdots = \pi_H = 0$
- 检验统计量：$F = \frac{(R\hat{\pi})' [R \hat{V}_{\pi} R']^{-1} (R\hat{\pi})}{H}$
- $R = I_H$（单位矩阵，因为所有系数都参与检验）

## Stata 源码映射

### Pretreatment dummies 构造（ado 第 541–548 行）

```stata
if (`pretrends'>0) {
    tempname pretrendvar
    tempvar preresid
    forvalues h = 1/`pretrends' {
        gen `pretrendvar'`h' = (`K'==-`h') if `touse'
        local pretrendvars `pretrendvars' `pretrendvar'`h'
        local prenames `prenames' pre`h'
    }
    reghdfe `Y' `controls' `pretrendvars' `weiexp' if `touse' & `D'==0, ///
        a(`fe_i' `fe_t' `fe') cluster(`cluster') resid(`preresid')
    forvalues h = 1/`pretrends' {
        matrix `b'[1,`tau_num'+`h'] = _b[`pretrendvar'`h']
        local preb`h' = _b[`pretrendvar'`h']
        local prese`h' = _se[`pretrendvar'`h']
    }
    local pre_df = e(df_r)
}
```

**注意：**
- `pretrendvar'h` = 1 当且仅当 $K = -h$
- 这些变量只在 `D==0` 样本中有意义（因为 $K < 0$ 意味着未处理）
- 但 ado 在 `if touse` 上生成，所以处理样本中这些变量自动为 0

### Pretrends SE 权重构造（ado 第 559–588 行）

与 controls 的 SE 权重构造逻辑几乎相同：

```stata
forvalues h = 1/`pretrends' {
    tempvar preeps_w`h'
    if (`preb`h''==0 & `prese`h''==0) gen `preeps_w`h'' = 0 // omitted
    else {
        local rhsvars = subinstr(" `pretrendvars' "," `pretrendvar'`h' "," ",.)
        reghdfe `pretrendvar'`h' `controls' `rhsvars' `weiexp' if `touse' & `D'==0, ///
            a(`fe_i' `fe_t' `fe') cluster(`cluster') resid(`preweight')
        replace `preweight' = `preweight' * `wei'
        sum `preweight' if `touse' & `D'==0 & `pretrendvar'`h'==1
        replace `preweight' = `preweight'/r(sum)
        egen `preeps_w`h'' = total(`preweight' * `preresid') if `touse', by(`cluster')
        replace `preeps_w`h'' = `preeps_w`h'' * sqrt(`dof_adj')
    }
}
```

**关键步骤：**
1. 将当前 pretrend dummy 对其他 pretrend dummies（和 controls、FEs）做回归
2. 残差 `preweight` 乘以观测权重 `wei`
3. 只在 `pretrendvar==1` 的观测上求和并标准化（因为 dummy 只在特定 horizon 为 1）
4. 按 cluster 聚合 `preweight * preresid`
5. 乘以 `sqrt(dof_adj)`

### 与主效应 VCE 的整合

```stata
matrix accum `V' = `list_weps' `list_pre_weps' `list_ctrl_weps' if `tag_clus', nocon
```

所有三类 influence function（主效应 `weps`、pretrends `pre_weps`、controls `ctrl_weps`）一起进入协方差矩阵。这意味着：
- tau_h 的标准误**不受** pretrends 存在与否的影响（因为 pretrends 只在控制样本中）
- pretrends 系数之间的协方差被正确估计
- pretrends 与 controls 之间的协方差也被估计（虽然通常不报告）

## 自由度调整

```stata
local dof_adj = (e(N)-1)/(e(N)-e(df_m)-e(df_a)) * (e(N_clust)/(e(N_clust)-1))
```

这与 `reghdfe` 的标准 cluster-robust 小样本调整一致：
- $(N-1)/(N - df_m - df_a)$：HC1 类型的自由度调整
- $G/(G-1)$：cluster-robust 的小样本调整
- 两者相乘得到 `dof_adj`

## 关键设计决策

### 1. Pretrends 是否影响主效应估计？

**否。** Pretrends dummies 只在控制样本的回归中出现，而主效应 `tau_h` 是处理样本的 `Y - Y0` 平均。Y0 的构造**不包含** pretrends 系数：

```stata
// Y0 构造中完全没有 pretrends 的成分
gen `Y0' = 0
// ... 加上 FEs、controls、unitcontrols、timecontrols ...
// 没有 pretrendvar 的项！
```

这意味着：
- `pretrends(3)` 和 `pretrends(0)` 产生的 `tau_h` 点估计**完全相同**
- 只有标准误和 covariance matrix 的维度不同

### 2. 为什么 pretrends 能降低主效应的 SE？

虽然点估计不变，但 pretrends dummies 吸收了控制样本中的部分变异，使 `imput_resid`（控制样本残差）更小。由于主效应的 SE 依赖于 `imput_resid`（通过 imputation weights 和 residual），更小的残差意味着更小的 SE。

不过，因为 pretrends 只在控制样本中，对处理样本的 imputation 残差影响有限。实际中，加入 pretrends 后 tau_h 的 SE 变化通常很小。

### 3. Pretrends 与 allhorizons 的交互

当 `allhorizons` 和 `pretrends` 同时使用时：
- `allhorizons` 决定输出哪些 tau_h（包括 pretreatment horizons）
- `pretrends` 决定做多少个 pretreatment 系数的联合检验
- 两者独立：可以 `allhorizons` 输出 `tau_{-3}` 但不设 `pretrends`

## Python 实现路径（Round 2 参考）

### 最小实现

1. 在 `fit()` 签名中添加 `pretrends: int = 0`
2. 若 `pretrends > 0`：
   a. 构造 pretreatment dummies：`pre_h = (K == -h)` for h in 1..pretrends
   b. 将它们加入控制样本的 TWFE 回归
   c. 提取系数 `pi_h` 和 SE `se_pi_h`
   d. 计算 joint F test
3. 在结果矩阵中预留 pretrends 的位置
4. 在 VCE 中纳入 pretrends 的 influence functions

### 代码结构建议

```python
# 在控制样本回归阶段
if self.pretrends > 0:
    for h in range(1, self.pretrends + 1):
        controls_df[f"pre_{h}"] = (controls_df["_K"] == -h).astype(int)
    # reghdfe 会自动处理这些 dummies

# 提取 pretrends 系数
pre_coefs = []
for h in range(1, self.pretrends + 1):
    pre_coefs.append({
        "name": f"pre{h}",
        "beta": reghdfe_result.params.get(f"pre_{h}", 0.0),
        "std_err": reghdfe_result.bse.get(f"pre_{h}", 0.0),
    })

# Joint F test
if self.pretrends > 0:
    pre_params = [c["beta"] for c in pre_coefs]
    pre_vcov = reghdfe_result.cov_params().loc[pre_names, pre_names]
    f_stat, p_value = wald_test(pre_params, pre_vcov, R=np.eye(len(pre_names)))
```

## Synthetic 样例设计

### `w9_di_pretrends_basic`

- **数据集**：500 单元 × 11 年，3 个 cohort + never-treated
- **设计**：在事件前 3 期引入轻微正向趋势（violation of parallel trends）
- **Stata 命令**：
  ```stata
  did_imputation y id year first_treat, allhorizons cluster(id) autosample pretrends(3)
  ```
- **对齐焦点**：
  - `pre1`, `pre2`, `pre3` 的系数是否显著不为 0
  - `pre_F` 和 `pre_p` 的值
  - 主效应 `tau_h` 的点估计是否与无 pretrends 时相同

### `w9_di_pretrends_no_violation`

- **数据集**：同上，但无 pretreatment trend（纯正态噪声）
- **预期**：`pre_F` 不显著（p > 0.05），`pre1`–`pre3` 接近 0

## 与 controls 的交互

当 `controls` 和 `pretrends` 同时存在时：
- pretrends dummies 和 controls 一起进入控制样本的 reghdfe
- 两者都需要 residualization 来构造 SE weights
- VCE 矩阵同时包含 tau、pre、ctrl 三部分

这是 `did_imputation` 中最复杂的 VCE 情形之一。
