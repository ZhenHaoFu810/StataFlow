# `ivreghdfe` 弱工具变量检验研究档案

## 来源

- `ivreghdfe.ado`：`ivreg2` 弱工具变量检验框架的透传封装
- 文献：Stock & Yogo (2005)；Kleibergen & Paap (2006)
- Stata 命令：`ranktest`（计算 rk 统计量）

---

## 1. 弱工具变量检验框架

`ivreghdfe`（通过 `ivreg2`）报告的弱工具变量统计量包含三个层次：

1. **Underidentification test**：检验工具变量是否与被解释变量相关（原假设：模型不可识别）
2. **Weak identification test**：检验工具变量的强度（原假设：工具变量弱）
3. **Stock-Yogo 临界值**：判断弱工具变量的临界标准

---

## 2. Underidentification Test（不可识别检验）

### 2.1 同方差：Anderson Canonical Correlations LM

**原假设**：工具变量与内生变量不相关（模型不可识别）

基于约简型回归的 canonical correlations：
```
LM = N * sum(λ_i)  ~ χ²(L - K + 1)
```

其中 λ_i 为 canonical correlations，在 `ivreg2` 中通过 `ranktest` 命令计算。

### 2.2 异方差/聚类：Kleibergen-Paap rk LM

**公式**（Kleibergen & Paap 2006）：

`ranktest` 计算原始 χ² 统计量，然后 `ivreghdfe` 做自由度调整：
```
非聚类: LM = r(chi2) / r(N) * (N - dofminus)  ~ χ²(iv1_ct - rhs1_ct + 1)
聚类:   LM = r(chi2)                           ~ χ²(iv1_ct - rhs1_ct + 1)
```

其中：
- `r(chi2)` 为 `ranktest` 返回的 LM χ² 统计量
- `r(N)` 为 `ranktest` 使用的观测数（通常等于 N）
- `dofminus` = 已吸收 FE 数的自由度扣减
- `iv1_ct` = 全部工具变量数（含常数项）
- `rhs1_ct` = 全部回归量数（含常数项）

**Stata 实现**：
- `ivreghdfe.ado` L1772-1778：
```stata
if "`cluster'"=="" {
    scalar `idstat'=r(chi2)/r(N)*(`N'-`dofminus')
}
else {
    scalar `idstat'=r(chi2)
}
```
- `ranktest` 使用 SVD 分解计算 rk 统计量

---

## 3. Weak Identification Test（弱工具变量检验）

### 3.1 同方差：Cragg-Donald Wald F

**公式**：

Cragg-Donald 特征值（基于最小 canonical correlation）：
```
cc_min = λ_min                 # 最小 canonical correlation 的平方
cd = cc_min / (1 - cc_min)     # Cragg-Donald 特征值
F = cd * (N - sdofminus - iv1_ct - dofminus) / exex1_ct
```

其中：
- `iv1_ct` = 全部工具变量数（含常数项）
- `exex1_ct` = 被排除工具变量数
- `sdofminus` = 小样本额外自由度调整
- `dofminus` = 已吸收 FE 数的自由度扣减

**Stata 实现**：
- `ivreghdfe.ado` L1789-1790：
```stata
scalar `cd'=`cdeval'[1,`endo1_ct']
scalar `cdf'=`cd'*(`N'-`sdofminus'-`iv1_ct'-`dofminus')/`exex1_ct'
```
- `ivreghdfe.ado` L2617：显示 "Cragg-Donald Wald F statistic"

### 3.2 异方差/聚类：Kleibergen-Paap rk Wald F

**公式**（同方差时退化为 Cragg-Donald F）：

同方差（`robust=""` 且 `cluster=""`）：
```
F = cd * (N - iv1_ct - sdofminus - dofminus) / exex1_ct
```
其中 `cd` 为 Cragg-Donald 特征值，`iv1_ct` = 全部工具变量数（含常数），`exex1_ct` = 被排除工具变量数。

异方差 / 聚类：
```
非聚类: F = r(chi2) / r(N) * (N - iv1_ct - sdofminus - dofminus) / exex1_ct
聚类:   F = r(chi2) / (N - 1) * (N - iv1_ct - sdofminus) * (N_clust - 1) / N_clust / exex1_ct
```

其中：
- `r(chi2)` 为 `ranktest` 返回的 Wald χ² 统计量
- `r(N)` 为 `ranktest` 使用的观测数（通常等于 N）
- `iv1_ct` = 全部工具变量数（含常数项）
- `exex1_ct` = 被排除工具变量数
- `sdofminus` = 小样本额外自由度调整
- `dofminus` = 已吸收 FE 数的自由度扣减
- `N_clust` = 聚类组数

**Stata 实现**：
- `ivreghdfe.ado` L1828-1837：
```stata
if "`cluster'"=="" {
    scalar `rkf'=r(chi2)/r(N)*(`N'-`iv1_ct'-`sdofminus'-`dofminus')/`exex1_ct'
}
else {
    scalar `rkf' = r(chi2)/(`N'-1) * (`N'-`iv1_ct'-`sdofminus') * (`N_clust'-1)/`N_clust' / `exex1_ct'
}
scalar `widstat'=`rkf'
```

- `ivreghdfe.ado` L2619：显示 "Kleibergen-Paap rk Wald F statistic"

---

## 4. Stock-Yogo 临界值

### 4.1 临界值含义

Stock-Yogo (2005) 提供了基于 "maximum IV relative bias" 和 "maximum IV size distortion" 的临界值：

- **10% maximal IV size**：允许 IV 估计量的 Wald 检验 size  distortion 不超过 10%
- **15% maximal IV size**：size distortion 不超过 15%
- **20% maximal IV size**：size distortion 不超过 20%
- **25% maximal IV size**：size distortion 不超过 25%

通常使用 **10% maximal IV size** 作为弱工具的拒绝标准：若 Kleibergen-Paap F > 临界值，则拒绝"弱工具"的原假设。

### 4.2 临界值表

临界值取决于：
- `nendog`：内生变量数（K1）
- `k2`：被排除工具变量数（L1）
- `model`：估计量类型（2SLS / LIML）

**常用临界值（2SLS，单内生变量）**：

| L1 (被排除 IV 数) | 10% max IV size | 15% max IV size | 20% max IV size | 25% max IV size |
|-------------------|-----------------|-----------------|-----------------|-----------------|
| 1 | — | — | — | — |
| 2 | 19.93 | 11.59 | 8.75 | 7.25 |
| 3 | 22.30 | 12.83 | 9.54 | 7.80 |
| 4 | 24.58 | 13.96 | 10.26 | 8.31 |
| 5 | 26.87 | 15.09 | 10.98 | 8.84 |
| 6 | 29.18 | 16.23 | 11.72 | 9.38 |
| 7 | 31.50 | 17.38 | 12.48 | 9.93 |
| 8 | 33.84 | 18.54 | 13.24 | 10.50 |
| 9 | 36.19 | 19.71 | 14.01 | 11.07 |
| 10 | 38.54 | 20.88 | 14.78 | 11.65 |

**LIML 临界值（单内生变量，Stock-Yogo 2005 Table 5.4）**：

| L1 (被排除 IV 数) | 10% max IV size | 15% max IV size | 20% max IV size | 25% max IV size |
|-------------------|-----------------|-----------------|-----------------|-----------------|
| 1 | 16.38 | 8.96 | 6.66 | 5.53 |
| 2 | 8.68 | 5.33 | 4.42 | 3.92 |
| 3 | 6.46 | 4.36 | 3.69 | 3.32 |
| 4 | 5.44 | 3.87 | 3.30 | 2.98 |
| 5 | 4.83 | 3.56 | 3.05 | 2.77 |
| 6 | 4.43 | 3.36 | 2.87 | 2.61 |
| 7 | 4.12 | 3.20 | 2.73 | 2.49 |
| 8 | 3.89 | 3.08 | 2.63 | 2.40 |
| 9 | 3.71 | 2.98 | 2.55 | 2.33 |
| 10 | 3.56 | 2.90 | 2.49 | 2.27 |

### 4.3 Stata 实现

`ivreghdfe` 调用 `s_cdsy()` Mata 函数查表（来自 `ivreg2` Mata 库）。该函数接受：
- `model`："2sls" 或 "liml"
- `k2`：被排除 IV 数
- `nendog`：内生变量数
- `fuller`：Fuller 参数（影响 LIML 临界值）

返回：
- 四个临界值（10%/15%/20%/25% max IV size）

**Python 实现建议**：
- 将 Stock-Yogo 表硬编码为字典/数组
- 运行时查表 + 线性插值（若需要非整数 L1）
- 版权考虑：Stock-Yogo 表为学术发表内容，硬编码小样本表属于"事实数据"，通常不构成版权问题

---

## 5. 冗余工具变量检验（IV Redundancy Test）

**原假设**：被测试的工具变量是冗余的（与内生变量不相关）。

**统计量**：
```
LM = N * g_redundant' * V_redundant⁻¹ * g_redundant  ~ χ²(m)
```

其中 m 为被测试的冗余工具变量数。

**Stata 实现**：
- `ivreghdfe.ado` L2002-2010：`redundant(varlist)` 选项
- 调用 `ranktest` 计算

---

## 6. 过度识别检验（Overidentification Tests）

### 6.1 同方差：Sargan 统计量

```
S = N * gbar' * (sigmasq * Z'Z)⁻¹ * gbar  ~ χ²(L - K)
```

### 6.2 异方差/聚类：Hansen J 统计量

```
J = N * gbar' * S⁻¹ * gbar  ~ χ²(L - K)
```

其中 S 为 robust/cluster 正交条件协方差矩阵。

### 6.3 C 统计量（差分 Sargan）

用于检验部分工具变量的有效性（`orthog(varlist)` 选项）：
```
C = J_full - J_partial  ~ χ²(m)
```

---

## 7. 一阶段诊断统计量（`first` / `ffirst`）

已在 `ivreghdfe.md` Wave 7 研究收束中详细记录。Wave 10 新增要点：

- GMM/LIML 的 `first` 输出与 2SLS 的 `first` 相同（第一阶段不随估计器变化）
- `ffirst` 的 SW / AP F 统计量基于约简型 VCE 计算，对 GMM/LIML 同样适用
- `weakiv` 选项额外输出 Kleibergen-Paap F 和 Stock-Yogo 临界值

---

## 8. Python 实现路径

### 8.1 weakiv 统计量计算

```python
def compute_weakiv_stats(self, X, y, Z, Z1, X2, vcvo):
    """
    X1: 内生变量
    X2: 外生变量（含常数）
    Z1: 被排除工具变量
    Z = [Z1, X2]: 全部工具变量
    """
    K1 = X1.shape[1]  # 内生变量数
    L1 = Z1.shape[1]  # 被排除 IV 数
    L = Z.shape[1]

    # 1. Underidentification test (Kleibergen-Paap rk LM)
    # 调用 ranktest 近似实现获取原始 chi2（Wald 近似，非精确 SVD）
    chi2_id, iddf = self._ranktest_lm(X1, Z1, X2, vcvo)

    # 应用 ivreghdfe 自由度调整 (L1772-1778)
    if not vcvo.cluster:
        idstat = chi2_id / N * (N - vcvo.dofminus)
    else:
        idstat = chi2_id
    idp = 1 - chi2.cdf(idstat, iddf)

    # 2. Weak identification test (Kleibergen-Paap rk Wald F)
    # 调用 ranktest 近似实现获取原始 chi2 (L1801-1809)（Wald 近似，非精确 SVD）
    chi2_rk = self._ranktest_wald(X1, Z1, X2, vcvo)

    iv1_ct = Z.shape[1] + (1 if has_constant else 0)  # 全部 IV 数含常数
    exex1_ct = Z1.shape[1]  # 被排除 IV 数

    if not vcvo.cluster:
        # L1829: r(chi2)/r(N)*(N-iv1_ct-sdofminus-dofminus)/exex1_ct
        widstat = chi2_rk / N * (N - iv1_ct - vcvo.sdofminus - vcvo.dofminus) / exex1_ct
    else:
        # L1832-1835: r(chi2)/(N-1)*(N-iv1_ct-sdofminus)*(N_clust-1)/N_clust/exex1_ct
        N_clust = vcvo.N_clust
        widstat = chi2_rk / (N - 1) * (N - iv1_ct - vcvo.sdofminus) * (N_clust - 1) / N_clust / exex1_ct

    # 3. Stock-Yogo critical values
    sy_crit = self._stock_yogo_critical_values(
        model="2sls",
        nendog=K1,
        k2=L1
    )

    return {
        'idstat': idstat, 'iddf': iddf, 'idp': idp,
        'widstat': widstat,
        'sy_10pct': sy_crit['10%'],
        'sy_15pct': sy_crit['15%'],
        'sy_20pct': sy_crit['20%'],
        'sy_25pct': sy_crit['25%'],
    }
```

### 8.2 ranktest Wald 统计量（简化版）

```python
def _ranktest_wald(self, X1, Z1, X2, vcvo):
    """
    计算 Kleibergen-Paap rk Wald 统计量（Wald 近似实现）。
    用约简型 Wald 统计量近似 ranktest 的 rk Wald 统计量。
    注意：Stata 的 ranktest 使用 SVD 分解，此实现为近似而非精确等价。
    """
    # 对每个内生变量，跑第一阶段回归
    chi2_total = 0
    for i in range(X1.shape[1]):
        x1_i = X1[:, i]
        if X2 is not None:
            Z_full = np.column_stack([Z1, X2])
        else:
            Z_full = Z1

        # 回归 x1_i 对 Z_full
        beta = np.linalg.solve(Z_full.T @ Z_full, Z_full.T @ x1_i)
        e = x1_i - Z_full @ beta

        # 仅检验 Z1 的系数
        R = np.eye(Z1.shape[1], Z_full.shape[1])
        r = np.zeros(Z1.shape[1])
        Rb = R @ beta

        # VCV
        V = self._compute_ols_vcv(Z_full, e, vcvo)
        RVR = R @ V @ R.T

        chi2_i = (Rb - r).T @ np.linalg.inv(RVR) @ (Rb - r)
        chi2_total += chi2_i

    return chi2_total
```

---

## 9. 与 Stata 对齐要点

| 要点 | Stata 行为 | Python 注意 |
|------|-----------|-------------|
| `ranktest` | 外部命令，使用 SVD | 需自行实现或使用 Wald 近似 |
| `sdofminus` | 小样本额外自由度调整 | 记录 `ivreghdfe` 的 `sdofminus` 计算逻辑 |
| 聚类 F 公式 | 含 `N_clust` 调整项 | 必须精确复现分母中的 `(N-1)` 和 `N_clust` |
| Stock-Yogo 表 | `s_cdsy()` 查表 | 硬编码表 + 插值 |
| 显示格式 | "Kleibergen-Paap rk Wald F statistic" | 字段名映射 `widstat` |

---

## 10. 参考文献

1. Stock, J. H., & Yogo, M. (2005). Testing for Weak Instruments in Linear IV Regression. In *Identification and Inference for Econometric Models* (pp. 80-108). Cambridge University Press.
2. Kleibergen, F., & Paap, R. (2006). Generalized reduced rank tests using the singular value decomposition. *Journal of Econometrics*, 133(1), 97-126.
3. Cragg, J. G., & Donald, S. G. (1993). Testing identifiability and specification in instrumental variable models. *Econometric Theory*, 9(2), 222-240.
4. Anderson, T. W. (1951). Estimating linear restrictions on regression coefficients for multivariate normal distributions. *Annals of Mathematical Statistics*, 22(3), 327-351.
5. Baum, C. F., Schaffer, M. E., & Stillman, S. (2007). Enhanced routines for instrumental variables/GMM estimation and testing. *Stata Journal*, 7(4), 465-506.
