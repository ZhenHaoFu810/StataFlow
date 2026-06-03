# Wave 12 Research: Driscoll-Kraay Standard Errors

**日期：** 2026-04-30
**主题：** 面板 HAC 标准误 (`vce(dkraay)`) 的公式与实现路径
**来源：** Driscoll-Kraay 1998 + Hoechle 2007 + reghdfe `Driscoll_Kraay.mata`

---

## 1. 问题定义

标准聚类稳健标准误（`vce(cluster time)`）假设同一时间周期内的观测完全相关，但不考虑**序列相关**（跨时间的相关性）。

Driscoll-Kraay (1998) 提出一种面板 HAC（Heteroskedasticity and Autocorrelation Consistent）标准误：
- 在**时间维度**上聚类（类似 `cluster(time)`）
- 对时间聚合后的矩条件应用 **Newey-West 型核函数**，修正自相关

**适用场景：** 面板数据中，同一时间点上的截面单元可能存在相关性（如宏观经济冲击），且这种相关性在时间上自相关。

## 2. 数学公式

### 2.1 基本设定

模型：`y_it = X_it'β + ε_it`，其中 `i = 1,...,N`（截面），`t = 1,...,T`（时间）。

OLS 估计量：`β̂ = (X'X)⁻¹ X'y`

方差-协方差矩阵的三明治形式：`V = D M D`，其中 `D = (X'X)⁻¹`。

### 2.2 传统聚类稳健 VCE（对比）

对于 `cluster(time)`：

```
M_cluster = Σ_t (X_t' e_t)(X_t' e_t)'
```

其中 `X_t` 是时间 `t` 上所有观测的设计矩阵，`e_t` 是残差向量。

### 2.3 Driscoll-Kraay VCE

DK 标准误在 `M_cluster` 基础上加入时间自相关修正：

```
M_DK = S_0 + Σ_{j=1}^L w_j (S_j + S_j')
```

其中：

- `h_t = Σ_{i∈t} X_it e_it`：时间 `t` 上的截面矩条件（`K × 1` 向量）
- `S_0 = Σ_{t=1}^T h_t h_t'`：零阶矩（同传统聚类）
- `S_j = Σ_{t=j+1}^T h_t h_{t-j}'`：`j` 阶自协方差
- `w_j = 1 - j/(L+1)`：Bartlett 核权重（Newey-West 形式）
- `L`：滞后阶数（`lags = bw - 1`，其中 `bw` 是 bandwidth）

### 2.4 自由度调整

reghdfe 使用 ivreg2 风格的调整：

```
dof_adj = (N - 1) / (N - K - df_a) × T / (T - 1)
```

其中：
- `N`：总观测数
- `K`：回归变量数（含常数项）
- `df_a`：吸收掉的 FE 自由度
- `T`：时间周期数

备选（xtscc 风格）：`dof_adj = (N / (N - K)) × (T / (T - 1))`

### 2.5 自由度

DK 标准误的参考分布使用 `T - 1` 自由度（因为时间矩条件的数量为 `T`）。

如果 `df_r > T - 1`，则 `df_r = T - 1`。

## 3. 带宽选择

### 3.1 默认规则

reghdfe 使用 Newey-West (1994) 的 plug-in 公式：

```
bw = floor(4 × (T/100)^(2/9)) + 1
lags = bw - 1
```

### 3.2 边界处理

- `bw < 1` → 设为 1（0 滞后，无自相关修正）
- `lags >= T` → 设为 `T - 1`

### 3.3 用户自定义

用户可指定 `vce(dkraay #)`，其中 `#` 是带宽（正整数）。

## 4. 与现有 VCE 框架的集成

### 4.1 当前 VCE 架构

当前 `AbsorbingOLS.fit()` 支持：
- `vce="ols"`
- `vce="robust"`
- `vce="cluster"`

`vce="dkraay"` 需要新增分支。

### 4.2 实现步骤

1. **解析 `vce` 参数**：`vce="dkraay"` 或 `vce="dkraay_5"`（带宽=5）
2. **需要时间变量**：必须从 `absorb` 参数中识别时间变量，或要求用户显式提供
3. **按时间排序**：将残差和设计矩阵按时间变量排序
4. **计算 `h_t`**：对每个时间周期 `t`，计算 `h_t = X_t' e_t`
5. **构建 `M_DK`**：应用 Bartlett 核加权自协方差
6. **三明治组装**：`V = D @ M_DK @ D × dof_adj`
7. **PSD 修正**：如果 `V` 不正定，应用 `_fix_psd`

### 4.3 Python 伪代码

```python
def compute_dkraay_vce(X, resid, timevar, bw=None, df_a=0):
    """
    Compute Driscoll-Kraay HAC VCE.

    X: design matrix (N x K) after partial-out
    resid: residuals (N,)
    timevar: time variable array (N,)
    bw: bandwidth (None = default)
    """
    N, K = X.shape
    T = len(np.unique(timevar))

    if bw is None:
        bw = int(4 * (T / 100) ** (2 / 9)) + 1
    lags = bw - 1
    lags = max(0, min(lags, T - 1))

    # Sort by time
    sort_idx = np.argsort(timevar)
    X_sorted = X[sort_idx]
    resid_sorted = resid[sort_idx]
    time_sorted = timevar[sort_idx]

    # Compute h_t for each time period
    # h_t is K x 1 vector = sum over i in t of X_it * e_it
    h_dict = {}
    for t in np.unique(time_sorted):
        mask = time_sorted == t
        h_dict[t] = X_sorted[mask].T @ resid_sorted[mask]

    times = sorted(h_dict.keys())
    h_matrix = np.array([h_dict[t] for t in times])  # T x K

    # S_0
    M = h_matrix.T @ h_matrix

    # S_j with Bartlett kernel
    for j in range(1, lags + 1):
        weight = 1 - j / (lags + 1)
        Omega_j = h_matrix[j:].T @ h_matrix[:-j]
        M += weight * (Omega_j + Omega_j.T)

    # Sandwich: V = D M D
    XtX_inv = np.linalg.inv(X.T @ X)
    V = XtX_inv @ M @ XtX_inv

    # DOF adjustment
    dof_adj = (N - 1) / (N - K - df_a) * T / (T - 1)
    V *= dof_adj

    # PSD fix
    V = fix_psd(V)

    df_r = T - 1
    return V, df_r
```

## 5. 与 Stata `reghdfe` 的对齐点

### 5.1 关键对齐项

| 项目 | Stata 行为 | Python 实现对齐要求 |
|------|-----------|-------------------|
| 带宽默认值 | `floor(4*(T/100)^(2/9)) + 1` | 必须完全一致 |
| 核函数 | Bartlett（线性递减） | 必须完全一致 |
| 自由度调整 | ivreg2 风格 `(N-1)/(N-K-df_a) * T/(T-1)` | 必须完全一致 |
| 参考自由度 | `T - 1` | 必须完全一致 |
| PSD 修正 | `reghdfe_fix_psd` | 复用现有 `_fix_psd` |
| 时间变量 | 从 `tsset` 获取 | 需从 `absorb` 推断或显式传入 |

### 5.2 测试策略

**Synthetic 测试：**
- 生成面板数据：`N=50` firms, `T=10` years
- 运行 Stata: `reghdfe y x, absorb(firm_id year) vce(dkraay)`
- 运行 Python DK VCE
- 对比：系数 `< 1e-6`，SE `< 1e-4`（HAC 容差通常较宽）

**带宽边界测试：**
- `T=5`，默认带宽应截断为 `T-1=4`
- `bw=1`，应退化为标准 `cluster(time)`

## 6. 参考文献

1. Driscoll & Kraay (1998), "Consistent Covariance Matrix Estimation with Spatially Dependent Panel Data", REStat
2. Hoechle (2007), "Robust Standard Errors for Panel Regressions with Cross-Sectional Dependence", Stata Journal
3. Newey & West (1994), "Automatic Lag Selection in Covariance Matrix Estimation", REStud
4. reghdfe `Driscoll_Kraay.mata`：实现源码
