# `did_imputation` controls / unitcontrols / timecontrols 研究档案

## 命令定位

- 命令族：`DID / Event Study Extensions`
- 类型：社区贡献命令 `did_imputation` 的协变量处理子系统
- 规则来源：Borusyak, Jaravel & Spiess (2023) + `did_imputation.ado` v2023-11-22 + Stata 17 双跑
- 关联文件：`research/vendor/stata_community/did_imputation/did_imputation-main/did_imputation.ado`

## 核心洞察

`did_imputation` 的协变量处理**不是**简单的 "把 X 放进 TWFE 回归"。它分为三类，每类的 residualization 逻辑、FE 交互方式和 imputation 传播路径都不同：

| 类型 | 语法 | FE 交互 | Residualization 层级 | Y0 构造方式 |
|------|------|---------|---------------------|------------|
| Simple controls | `controls(varlist)` | 无 | 全局（control sample） | `sum(beta_k * X_k)` |
| Unit controls | `unitcontrols(varlist)` | `i##c.(X)` | 单元内（unit-specific） | `alpha_i + sum(slope_ij * X_jt)` |
| Time controls | `timecontrols(varlist)` | `t##c.(X)` | 时间内（time-specific） | `gamma_t + sum(slope_tj * X_jt)` |

关键区别：`controls` 的系数是**全局共享**的（一个 beta 对应一个协变量），而 `unitcontrols` 和 `timecontrols` 的系数是**分层**的（每个单元或每个时间有自己的 slope）。

## 识别假设的变化

引入协变量后，平行趋势假设变为 **条件平行趋势**：

$$
\mathbb{E}[Y_{it}(0) \mid X_{it}, \alpha_i, \gamma_t] = \alpha_i + \gamma_t + f(X_{it})
$$

其中 $f(X_{it})$ 的形式取决于协变量类型：
- `controls`：$f(X) = \beta' X$
- `unitcontrols`：$f(X) = \sum_j \delta_{ij} X_{jt}$（单元特定斜率）
- `timecontrols`：$f(X) = \sum_j \eta_{tj} X_{jt}$（时间特定斜率）

## Stata 源码映射

### Part 3: 估计反事实模型（ado 第 330–395 行）

```stata
if ("`unitcontrols'"!="") local fe_i `i'##c.(`unitcontrols')
if ("`timecontrols'"!="") local fe_t `t'##c.(`timecontrols')

reghdfe `Y' `controls' if (`D'==0) & (`touse') `weiexp', ///
    a(`fe_i' `fe_t' `fe', savefe) nocon keepsing resid(`imput_resid') cluster(`cluster')
```

**关键参数：**
- `nocon`：无总体常数项，常数被吸收进第一个 FE
- `savefe`：保存 FE 估计值（包括 `unitcontrols` 和 `timecontrols` 的 slopes）
- `keepsing`：保留 singleton 观测（对仅出现在一个时期的处理单元至关重要）
- `resid()`：保存控制样本的残差，用于后续 SE 计算

### Y0 构造（ado 第 354–384 行）

```stata
gen `Y0' = 0 if `touse'

// 1. Unit-interacted controls
if ("`unitcontrols'"!="") {
    recover __hdfe1__*, from(`i')
    replace `Y0' = `Y0' + __hdfe1__ if `touse'
    foreach v of local unitcontrols {
        replace `Y0' = `Y0' + __hdfe1__Slope`j' * `v' if `touse'
    }
}

// 2. Time-interacted controls
if ("`timecontrols'"!="") {
    recover __hdfe1__* 或 __hdfe2__*, from(`t')
    replace `Y0' = `Y0' + __hdfe2__ if `touse'
    foreach v of local timecontrols {
        replace `Y0' = `Y0' + __hdfe2__Slope`j' * `v' if `touse'
    }
}

// 3. Regular FEs
forvalues feindex = 1/`fecount' {
    recover __hdfe`feset'__, from(`fe`feindex'')
    replace `Y0' = `Y0' + __hdfe`feset'__ if `touse'
}

// 4. Simple controls
foreach v of local controls {
    replace `Y0' = `Y0' + _b[`v'] * `v' if `touse'
}
```

**`recover` 子程序的作用：**

`recover` (ado 第 866–873 行) 用于填充缺失的 FE 预测值：
```stata
program define recover, sortpreserve
    syntax varlist, from(varlist)
    foreach var of local varlist {
        gsort `from' -`var'
        by `from' : replace `var' = `var'[1] if mi(`var')
    }
end
```

对于 `unitcontrols`，`recover __hdfe1__*, from(i)` 会按单元排序，将同一个单元的 FE 和 slope 值填充到该单元的所有时期（包括处理时期）。这是 imputation 能够工作的关键——处理时期的 Y0 必须能从控制样本的 FE 估计中推断出来。

### 三种协变量的数学公式

#### controls（简单控制变量）

在控制样本（$D=0$）上运行：

$$
Y_{it} = \alpha_i + \gamma_t + \beta' X_{it} + \varepsilon_{it}
$$

Y0 预测：

$$
\hat{Y}_{it}(0) = \hat{\alpha}_i + \hat{\gamma}_t + \hat{\beta}' X_{it}
$$

其中 $\hat{\beta}$ 是全局共享的斜率向量。

**与标准 TWFE + controls 的区别：**
- 估计仅在 $D=0$ 子样本上进行
- $\hat{\alpha}_i$ 和 $\hat{\gamma}_t$ 来自控制样本，但应用于全部样本
- $\hat{\beta}$ 也是来自控制样本，但应用于全部样本的 $X$

#### unitcontrols（单元交互控制变量）

在控制样本上运行：

$$
Y_{it} = \alpha_i + \sum_j \delta_{ij} Z_{jt} + \gamma_t + \varepsilon_{it}
$$

其中 $Z_{jt}$ 是 time-varying covariates。每个单元 $i$ 有自己的截距 $\alpha_i$ 和斜率 $\delta_{ij}$。

等价于 `reghdfe` 语法：`absorb(i##c.Z)`。

Y0 预测：

$$
\hat{Y}_{it}(0) = \hat{\alpha}_i + \sum_j \hat{\delta}_{ij} Z_{jt} + \hat{\gamma}_t
$$

**适用场景：**
- 协变量随时间变化，且不同单元的响应不同
- 例如：州级政策分析中，各州有不同的时间趋势

#### timecontrols（时间交互控制变量）

在控制样本上运行：

$$
Y_{it} = \gamma_t + \sum_j \eta_{tj} W_{ij} + \alpha_i + \varepsilon_{it}
$$

其中 $W_{ij}$ 是 unit-varying covariates。每个时间 $t$ 有自己的截距 $\gamma_t$ 和斜率 $\eta_{tj}$。

等价于 `reghdfe` 语法：`absorb(t##c.W)`。

Y0 预测：

$$
\hat{Y}_{it}(0) = \hat{\gamma}_t + \sum_j \hat{\eta}_{tj} W_{ij} + \hat{\alpha}_i
$$

**适用场景：**
- 协变量随单元变化，且不同时期的响应不同
- 例如：全国性冲击对各行业的不同影响

## Imputation Weights 的协变量处理

`imputation_weights` 子程序（ado 第 717–840 行）计算标准误所需的 imputation weights。对于三种协变量，residualization 方式不同：

### controls 的权重计算

```stata
foreach v of local controls {
    tempvar dm_`v' c`v'
    sum `v' [aw=`wei'] if `D'==0 & `touse'
    gen `dm_`v'' = `v' - r(mean) if `touse'
    egen `c`v'' = sum(`wei' * `dm_`v''^2) if `D'==0 & `touse'
}
```

在迭代中：
```stata
foreach v of local controls {
    update_weights `dm_`v'', w(`keepiterating') wei(`wei') d(`D') touse(`touse') denom(`c`v'')
}
```

**数学含义：**
- `dm_v` = $X - \bar{X}_{control}$（在控制样本中去均值）
- `c_v` = $\sum_{D=0} w_i \cdot dm_v^2$（控制样本中的加权平方和）
- `update_weights` 执行：$w \leftarrow w - \frac{\sum w_i \cdot dm_v}{c_v} \cdot dm_v$

这是 FWL（Frisch-Waugh-Lovell）定理的迭代实现，等价于将权重对协变量进行正交化。

### unitcontrols 的权重计算

```stata
foreach v of local unitcontrols {
    tempvar u`v' dm_u`v' s_u`v'
    egen `s_u`v'' = pc(`wei') if `D'==0 & `touse', by(`i') prop
    egen `dm_u`v'' = sum(`s_u`v'' * `v') if `touse', by(`i')
    replace `dm_u`v'' = `v' - `dm_u`v'' if `touse'
    egen `u`v'' = sum(`wei' * `dm_u`v''^2) if `D'==0 & `touse', by(`i')
}
```

**数学含义：**
- `s_u` = 单元内权重比例（`pc(wei)` 是 proportion weights）
- `dm_u` = $Z - \bar{Z}_{i,control}$（在单元 $i$ 的控制样本中去均值）
- `u` = $\sum_{D=0, i} w \cdot dm_u^2$（单元内加权平方和）

然后迭代中：
```stata
foreach v of local unitcontrols {
    update_weights `dm_u`v'', w(...) denom(`u`v'') by(`i')
}
update_weights , w(...) denom(`N0i') by(`i')
```

注意：每个 `unitcontrol` 之后还要更新一次纯单元 FE 的权重（`N0i` 是单元内控制样本的权重和），因为 `unitcontrols` 和单元 FE 是同时被吸收的。

### timecontrols 的权重计算

与 unitcontrols 对称，只是 `by(t)` 而非 `by(i)`。

## 标准误计算中的协变量处理

### controls 的 SE（ado 第 399–440 行）

对于每个 control 变量，构造其 influence function：

```stata
forvalues h = 1/`ctrl_num' {
    local ctrl_current : word `h' of `controls'
    local rhsvars : list ctrlvars - ctrl_current
    reghdfe `ctrl_current' `rhsvars' `weiexp' if `touse' & `D'==0, ///
        a(`fe_i' `fe_t' `fe') cluster(`cluster') resid(`ctrlweight')
    replace `ctrlweight' = `ctrlweight' * `wei'
    gen `ctrlweight_product' = `ctrlweight' * `ctrl_current'
    sum `ctrlweight_product' if `touse' & `D'==0
    replace `ctrlweight' = `ctrlweight' / r(sum)
    egen `ctrleps_w`h'' = total(`ctrlweight' * `imput_resid') if `touse', by(`cluster')
    replace `ctrleps_w`h'' = `ctrleps_w`h'' * sqrt(`dof_adj')
}
```

**数学含义：**
1. 将当前 control 对其他 controls（和 FEs）做回归，得到残差 `ctrlweight`
2. 用 `ctrlweight * X` 的加权和作为分母进行标准化
3. 计算 `sum(ctrlweight * imputation_resid)` 按 cluster 聚合
4. 乘以 `sqrt(dof_adj)` 做小样本自由度调整

这与标准 OLS 的 influence function 一致：每个 control 的估计量可以表示为 $\sum w_{ih} \cdot \varepsilon_i$，其中 $w_{ih}$ 是该 control 的 "SE weight"。

## 关键风险与边界情况

### 1. 控制样本共线性（ado 第 494–513 行）

```stata
reghdfe `tnorm' `controls' if (`D'==0) & (`touse'), a(`fe_i' `fe_t' `fe') nocon keepsing
local df_m_control = e(df_m)
local df_a_control = e(df_a)
reghdfe `tnorm' `controls', a(`fe_i' `fe_t' `fe') nocon keepsing
local df_m_full = e(df_m)
local df_a_full = e(df_a)

if (`df_m_control' < `df_m_full') {
    di as error "Could not run imputation for some observations because some controls are collinear in the D==0 subsample but not in the full sample"
}
```

**含义：** 如果某个 control 在控制样本中是常数（例如，一个 time-invariant 变量在所有控制观测中取值相同），但在全样本中不是，则 imputation 会失败。因为该 control 的系数无法从控制样本中识别，但 Y0 构造需要它。

**处理：**
- `autosample` **无法**处理这种情况
- 用户必须手动修正样本（例如，drop 该 control 或调整样本）

### 2. `unitcontrols` + 单元 FE 的冗余

当 `unitcontrols` 存在时，ado 会跳过单元 FE（`i`）：
```stata
if (("`fecurrent'"!="`i'" | "`unitcontrols'"=="") & ("`fecurrent'"!="`t'" | "`timecontrols'"==""))
```

这是因为 `i##c.Z` 已经包含了单元 FE（每个单元有自己的截距和斜率），再额外 absorb `i` 会导致完全共线性。

### 3. `timecontrols` + 时间 FE 的冗余

同理，`timecontrols` 存在时跳过时间 FE（`t`）。

### 4. 数值稳定性：小分母

在 `update_weights` 中：
```stata
replace `w_j' = `w_j' - `sumw'*`1'/`denom' if `d'==0 & `denom'!=0 & `touse'
```

如果 `denom`（加权平方和）接近 0，该协变量的正交化步骤会被跳过。这在 control 样本中某个单元（或时间）的所有观测取值几乎相同时会发生。

## Python 实现路径（Round 2 参考）

### controls 的实现

1. 在控制样本上运行 `reghdfe(y ~ 1, absorb=[id, time], X=controls)`
2. 获取 `beta_controls`（来自 `reghdfe` 的 slope 系数）
3. Y0 = `alpha_fe[id] + gamma_fe[time] + X @ beta_controls`

### unitcontrols 的实现

1. 在控制样本上运行 `reghdfe(y ~ 1, absorb=[id##c.unitcontrols, time])`
2. 从 `reghdfe` 的 `savefe` 输出中提取：
   - `alpha_i`（单元截距）
   - `delta_ij`（每个单元对每个 unitcontrol 的 slope）
3. Y0 = `alpha_i + sum_j(delta_ij * Z_jt) + gamma_t`

**关键：** Python 端需要 `reghdfe` 支持 `id##c.Z` 的吸收语法，或者手动实现：
- 对每个单元，在控制样本上运行 `y ~ Z` 的 OLS，得到 `(alpha_i, delta_i)`
- 这等价于 `groupby(id).apply(lambda g: lstsq(Z, y))`

### timecontrols 的实现

与 unitcontrols 对称，只是 `groupby(time)` 而非 `groupby(id)`。

## Synthetic 样例设计

### `w9_di_controls_basic`

- **数据集**：500 单元 × 11 年，3 个 cohort + never-treated
- **协变量**：
  - `x1`：time-varying（随机游走），作为 `controls`
  - `x2`：unit-specific 趋势，作为 `unitcontrols`
- **Stata 命令**：
  ```stata
  did_imputation y id year first_treat, allhorizons cluster(id) autosample controls(x1) unitcontrols(x2)
  ```
- **对齐焦点**：
  - 引入 controls 后的 tau_h 系数变化（应与无 controls 时不同）
  - control 系数 `_b[x1]` 的符号和量级
  - 标准误变化（controls 应降低 SE）

### `w9_di_controls_collinear`

- **数据集**：同上，但 `x_col` 在控制样本中为常数
- **Stata 行为**：报错 "collinear in the D==0 subsample"
- **Python 行为**：应匹配 Stata 的报错信息

## 与现有代码的衔接

当前 `DIDImputation.fit()` 使用**迭代去均值**而非 `reghdfe` 来拟合 TWFE。引入协变量后，需要：

1. **方案 A**：继续使用迭代去均值，但扩展为带协变量的版本
   - 对 `controls`：在每次迭代中加入 `X @ beta` 项
   - 对 `unitcontrols`：在单元层面同时估计截距和斜率
   - 对 `timecontrols`：在时间层面同时估计截距和斜率

2. **方案 B**：直接调用 `reghdfe` 兼容层（`AbsorbingOLS` 或 `reghdfe` wrapper）
   - 优点：自动处理 `i##c.Z` 语法、collinearity、savefe
   - 缺点：引入对 `reghdfe` 层的依赖，可能增加耦合

**推荐：** 方案 B，因为 `did_imputation` 的 ado 本身也直接调用 `reghdfe`，这是与其行为对齐的最可靠方式。
