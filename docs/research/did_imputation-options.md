# `did_imputation` 其他选项研究档案

## 命令定位

- 命令族：`DID / Event Study Extensions`
- 类型：`did_imputation` 的辅助选项子系统
- 规则来源：`did_imputation.ado` v2023-11-22 + Borusyak, Jaravel & Spiess (2023)
- 规则来源：公开发布的 `did_imputation.ado`

## 0. 版本边界：`window()`

M07 revalidation confirmed that the current target Stata ado, Borusyak
`did_imputation` Nov 2023, rejects `window()` with `option window() not
allowed`. StataFlow therefore treats `window` as a Python-native
`DIDImputation.fit(...)` extension only. The Stata-compatible wrapper
`compat.stata.did_imputation(..., window=...)` rejects it explicitly and does
not claim a direct Stata mapping for this ado version.

## 1. `wtr(varlist)` — 自定义处理权重

### 核心功能

默认情况下，`did_imputation` 计算处理组在**每个 horizon** 上的简单平均处理效应。`wtr` 允许用户指定自定义权重，实现：
- 加权平均处理效应（WATE）
- 特定子组的处理效应
- 自定义聚合（例如，按处理强度加权）

### 数学公式

默认（无 `wtr`）：

$$
\hat{\tau}_h = \frac{1}{N_h} \sum_{i: K_{it}=h} (Y_{it} - \hat{Y}_{it}(0))
$$

有 `wtr(w)` 时：

$$
\hat{\tau}_w = \sum_{i: D_{it}=1} w_{it} \cdot (Y_{it} - \hat{Y}_{it}(0))
$$

其中权重在 ado 中被**标准化**为：`sum(wei * w * (D==1)) == 1`

### Stata 源码（ado 第 138–162 行）

```stata
local wtr_count : word count `wtr'
if (`wtr_count'==0) {
    tempvar wtr
    gen `wtr' = 1 if (`touse') & (`D'==1)
    local wtrnames tau
    local wtr_count = 1
}
```

### 与 `horizons` 的互斥性

```stata
if (("`horizons'"!="" | "`allhorizons'"!="") & `wtr_count'>1) {
    di as error "Options horizons and allhorizons cannot be combined with multiple wtr variables"
}
```

- 单 `wtr` + `horizons`/`allhorizons`：允许，每个 horizon 是一个独立的加权平均
- 多 `wtr` + `horizons`：禁止

## 2. `sum` — 加权求和而非平均

### 核心功能

默认计算**平均**处理效应（除以观测数）。`sum` 选项改为计算**总和**处理效应：

$$
\text{Sum}_w = \sum_{i: D_{it}=1} w_{it} \cdot (Y_{it} - \hat{Y}_{it}(0))
$$

**不标准化权重**，直接求和。

### Stata 源码（ado 第 252–262 行）

```stata
if ("`sum'"=="" & "`project'"=="") {
    foreach v of local wtr {
        cap assert `v'>=0 if (`touse') & (`D'==1)
        sum `v' `weiexp' if (`touse') & (`D'==1)
        replace `v' = `v'/r(sum)
    }
}
```

当 `sum` 为空（默认）时，权重被标准化。当 `sum` 非空时，跳过标准化。

### 互斥约束

- `sum` 不能与 `autosample` 同时使用
- `sum` 不能与 `hbalance` 同时使用
- `sum` 不能与 `project` 同时使用

## 3. `hbalance` — 平衡样本约束

### 核心功能

强制要求：对于每个处理单元，如果它在某个 horizon 上被计入，则它必须在**所有指定的 horizons** 上都有观测。

### 实现逻辑（ado 第 176–198 行）

```stata
if ("`hbalance'"=="hbalance") {
    tempvar in_horizons num_horizons_by_i
    gen `in_horizons'=0 if `touse'
    foreach h of numlist `horizons' {
        replace `in_horizons'=1 if (`K'==`h') & `touse'
    }
    egen `num_horizons_by_i' = sum(`in_horizons') if `in_horizons'==1, by(`i')
    replace `wtr' = 0 if `touse' & (`in_horizons'==0 | (`num_horizons_by_i'<`n_horizons'))
}
```

**步骤：**
1. 标记所有属于指定 horizons 的观测
2. 计算每个单元在这些 horizons 中出现的次数
3. 如果出现次数 < 总 horizon 数，则将该单元的权重设为 0

### 权重一致性检查

```stata
egen `min_weight_by_i' = min(`wtr'*`wei') if ... , by(`i')
egen `max_weight_by_i' = max(`wtr'*`wei') if ... , by(`i')
cap assert `max_weight_by_i'<=1.000001*`min_weight_by_i'
```

确保每个单元在所有 horizons 上的 `wtr * wei` 相同（即权重不随时间变化）。

## 4. `hetby(varname)` — 异质性处理效应

### 核心功能

按某个分组变量（如性别、地区）将每个 `wtr` 拆分为多个子组效应。

### 实现逻辑（ado 第 209–250 行）

```stata
if ("`hetby'"!="") {
    levelsof `hetby' if `touse' & (`D'==1), local(hetby_values)
    foreach v of local wtr {
        foreach g of local hetby_values {
            gen `v'_`g' = `v' if `hetby'==`g'
        }
    }
}
```

**约束：**
- `hetby` 变量必须在处理样本中取值非负整数（或字符串，最多 30 个值）
- `hetby` 不能与 `project` 同时使用

### 输出命名

- 原 `wtr` 名为 `tau`，`hetby` 取值为 `male`/`female`
- 输出系数名：`tau_male`, `tau_female`

## 5. `project(varlist)` — 投影到协变量空间

### 核心功能

将处理效应投影到一组协变量上，估计 "conditional treatment effect"。

### 数学公式

对 treated 样本，运行：

$$
\text{effect}_{it} = \beta_0 + \beta' P_{it} + u_{it}
$$

然后报告的系数是 $\hat{\beta}$ 而非 $\hat{\tau}$。

### 实现逻辑（ado 第 264–314 行）

使用 FWL（Frisch-Waugh-Lovell）定理：
1. 将常数项对其他 `project` 变量做回归，取残差 → `wtr_cons`
2. 将每个 `project` 变量对其他 `project` 变量做回归，取残差 → `wtr_var`
3. 标准化每个残差权重：除以 `sum(wei * resid^2)`

```stata
reg `one' `project' `weiexp' if `touse' & (`D'==1) & !mi(`v') & (`v'>0), nocon
predict `wtr_curr', resid
replace `wtrsq' = `wei'*`wtr_curr'^2
sum `wtrsq'
replace `wtr_curr' = `wtr_curr'/r(sum)
```

**约束：**
- `project` 不能与 `wtr` 同时使用（只能与 `horizons`/`allhorizons`）
- `project` 不能与 `sum` 同时使用
- `project` 不能与 `hetby` 同时使用

## 6. `saveestimates(name)` — 保存效应估计值

### 核心功能

将每个观测的 `effect = Y - Y0` 保存为新变量。

### Stata 源码（ado 第 387–393 行）

```stata
if ("`saveestimates'"=="") tempvar effect
else {
    local effect `saveestimates'
    cap confirm var `effect', exact
    if (_rc==0) drop `effect'
}
gen `effect' = `Y' - `Y0' if (`D'==1) & (`touse')
```

- 只在处理观测（`D==1`）上保存
- 控制观测的 `effect` 为缺失

## 7. `saveweights` / `loadweights` — 保存/加载 imputation 权重

### 核心功能

`saveweights`：将 `imputation_weights` 子程序计算的权重保存为变量（每个系数一个变量）。

`loadweights`：跳过 `imputation_weights` 计算，直接加载用户提供的权重。

### 用途

- **加速**：当需要多次运行相同设计时，保存权重避免重复计算
- **验证**：用户可以检查 imputation 权重的分布
- **自定义**：高级用户可以手动调整权重

### 权重变量的命名

```stata
foreach vn of local wtrnames {
    local weightvars `weightvars' __w_`vn'
}
```

例如：`__w_tau0`, `__w_tau1`, `__w_pre1`

## 8. `saveresid(name)` — 保存残差

### 核心功能

将每个系数的回归残差保存为变量。

### Stata 源码（ado 第 655–676 行）

```stata
if ("`saveresid'"=="") tempvar resid
else local resid `saveresid'_`wtrname'

gen `resid' = `resid0'
replace `resid' = `effect' - `avgtau' if (`touse') & (`D'==1)
```

其中：
- `resid0 = Y - Y0`（控制样本的残差）
- `effect - avgtau`（处理样本的去均值效应）

**约束：**
- 不能与 `se(nose)` 同时使用（因为残差是 SE 计算的中间产物）

## 实现优先级建议

| 选项 | 复杂度 | 用户价值 | 实现状态 |
|------|--------|---------|------------|
| `wtr` | LOW | MEDIUM | 已实现 |
| `sum` | LOW | LOW | 已实现 |
| `hbalance` | LOW | LOW | 尚未实现 |
| `hetby` | LOW-MEDIUM | MEDIUM | 已实现 |
| `project` | MEDIUM | LOW | 尚未实现 |
| `saveestimates` | LOW | HIGH | 已实现 |
| `saveweights` | LOW | MEDIUM | 已实现 |
| `saveresid` | LOW | LOW | 已实现 |

## Synthetic 样例设计

### `w9_di_hetby_basic`

- **数据集**：500 单元 × 11 年，3 个 cohort + never-treated
- **分组变量**：`group` = {1, 2}（各 50%）
- **Stata 命令**：
  ```stata
  did_imputation y id year first_treat, allhorizons cluster(id) autosample hetby(group)
  ```
- **对齐焦点**：`tau_group1` 与 `tau_group2` 的差异

### `w9_di_saveestimates`

- **数据集**：同上
- **Stata 命令**：
  ```stata
  did_imputation y id year first_treat, allhorizons cluster(id) autosample saveestimates(effect)
  ```
- **对齐焦点**：保存的 `effect` 变量是否在 `D==1` 时等于 `Y - Y0`
