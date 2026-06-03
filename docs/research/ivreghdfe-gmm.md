# `ivreghdfe` GMM / LIML / CUE 算法详解

## 来源

- `ivreghdfe.ado` Mata 函数：`s_gmm1s`、`s_egmm`、`s_iegmm`、`s_gmmcue`、`s_liml`
- 底层库：`ivreg2` Mata 库（Baum/Schaffer/Stillman）
- 文献：Hansen (1982) GMM；Newey (1985) 最优权重；Stock & Yogo (2005) 弱工具变量

---

## 1. GMM 估计器家族

### 1.1 符号约定

| 符号 | 维度 | 含义 |
|------|------|------|
| `y` | N×1 | 被解释变量 |
| `X` | N×K | 回归量（含内生 + 外生） |
| `Z` | N×L | 工具变量（含排除 + 包含） |
| `e` | N×1 | 残差 |
| `N` | scalar | 观测数 |
| `K` | scalar | 回归量数 |
| `L` | scalar | 工具变量数 |
| `QXX` | K×K | X'X / N |
| `QXZ` | K×L | X'Z / N |
| `QXy` | K×1 | X'y / N |
| `QZZ` | L×L | Z'Z / N |
| `QZy` | L×1 | Z'y / N |
| `omega` | L×L | 正交条件协方差矩阵 S |
| `W` | L×L | GMM 权重矩阵 |

### 1.2 一步 GMM（`s_gmm1s`）

**用途**：GMM2S 的第一步、标准 IV/2SLS、用户提供权重矩阵的 GMM。

**三种子情况**：

#### A. OLS（X = Z，无 S 矩阵提供）
```
beta = QZZ⁻¹ QZy
omega = sigmasq * QZZ
W = 1/sigmasq * QZZ⁻¹
V = 1/N * sigmasq * QZZ⁻¹
```

#### B. IV/2SLS（X ≠ Z，无 S 矩阵提供）
```
beta = [QXZ QZZ⁻¹ QXZ']⁻¹ QXZ QZZ⁻¹ QZy
omega = sigmasq * QZZ
W = 1/sigmasq * QZZ⁻¹
V = 1/N * sigmasq * [QXZ QZZ⁻¹ QXZ']⁻¹
```

#### C. 用户提供 S 矩阵（高效一步 GMM）
```
beta = [QXZ · omega⁻¹ · QXZ']⁻¹ QXZ · omega⁻¹ · QZy
W = omega⁻¹
V = 1/N * [QXZ · omega⁻¹ · QXZ']⁻¹
```

** inefficent 一步 GMM**：用户提供权重矩阵 W 但不提供 S，仅返回 beta 和 W，不计算 V。

### 1.3 两步高效 GMM（`s_egmm`）

**算法**：
1. 第一步 GMM（通常是 IV/2SLS）得到残差 `e`
2. 基于第一步残差计算 `omega = m_omega(vcvo)`
3. 构造最优权重矩阵 `W = omega⁻¹`
4. 重新估计：
```
beta_2s = [QXZ · W · QXZ']⁻¹ QXZ · W · QZy
V = 1/N * [QXZ · W · QXZ']⁻¹
```

**重要区分：高效 vs 非高效 GMM VCE**

上述 `V = 1/N * [QXZ · W · QXZ']⁻¹` 仅在 **W = omega⁻¹（高效权重）** 时成立。

若用户使用自定义权重矩阵 W（非高效），VCE 需使用 sandwich 形式（见 `s_iegmm` L5680-5682）：
```
V = 1/N * [QXZ·W·QXZ']⁻¹ · QXZ·W · omega · W·QXZ' · [QXZ·W·QXZ']⁻¹
```

`estimator="gmm2s"` 默认使用高效权重，因此采用简化公式。若未来支持 `wmatrix` 参数，必须切换至 sandwich 形式。

**过度识别检验（Hansen J）**：
```
gbar = Z'e / N
J = N * gbar' * W * gbar
     = N * gbar' * omega⁻¹ * gbar
```

在恰好识别时（L = K），J = 0。

### 1.4 迭代高效 GMM（`s_iegmm`）

与 `s_egmm` 的区别：
- beta 由外部提供（通常是用户指定）
- 使用非高效权重矩阵 W（用户提供）
- VCE 公式考虑 W 非最优：
```
V = 1/N * [QXZ·W·QXZ']⁻¹ · QXZ·W · omega · W·QXZ' · [QXZ·W·QXZ']⁻¹
```

这与 Huber-White sandwich 形式一致。

### 1.5 CUE（连续更新 GMM，`s_gmmcue`）

**目标函数**：
```
J(beta) = N * gbar(beta)' * S(beta)⁻¹ * gbar(beta)
其中 gbar(beta) = Z'(y - X*beta) / N
      S(beta) = m_omega(基于残差 e = y - X*beta)
```

**算法**：
1. 用 2SLS 或 GMM2S 估计值作为初始值 beta_init
2. 调用数值优化器最小化 J(beta)
3. 最终 beta_cue 为估计值
4. 最终 omega = S(beta_cue)
5. V = 1/N * [QXZ · omega⁻¹ · QXZ']⁻¹

**Stata 实现细节**：
- 使用 Stata `optimize_init()` + `optimize()`
- evaluator type: `d0`（仅函数值，无解析梯度/Hessian）
- 评价函数：`m_cuecrit(todo, beta, py, pX, vcvo, useqr, j, g, H)`

**Python 实现建议**：
- 使用 `scipy.optimize.minimize`
- 推荐算法：Nelder-Mead（无梯度）、L-BFGS-B（有梯度近似）
- 初始值：2SLS 估计值
- 收敛容差：与 Stata `optimize()` 默认一致（`ftol=1e-7`, `gtol=1e-4`）

---

## 2. LIML 与 k-class 估计量（`s_liml`）

### 2.1 LIML 估计量

**lambda 计算**：

设 Y = [y, X_endo]（约简型系统），Z = [Z_excl, X_exog]，Z2 = X_exog。

```
W  = Y'Y - Y'Z (Z'Z)⁻¹ Z'Y   // Y' M_Z Y，残差二次型
W1 = Y'Y - Y'Z2 (Z2'Z2)⁻¹ Z2'Y  // Y' M_{Z2} Y（若无外生量则 W1 = Y'Y）
M  = W^(-1/2)          // 对称幂
lambda = min(eigenvalues(M * W1 * M))
```

lambda 为特征值问题的最小特征值。在恰好识别时（L = K），lambda = 1。

**k-class 参数**：
```
Fuller(δ): k = lambda - δ / (N - L)
k-class:   k = kclass（用户提供）
LIML:      k = lambda
```
其中 `L` = 结构工具变量数（排除工具变量 + 包含外生变量）。在 `ivreghdfe` 的 FE 残差化框架下，`ivreg2` 看到的是残差化后的数据，因此 `cols(Z)` 等价于结构工具变量数，而非 LSDV 的 `Z_full` 维度（后者包含常数项和 FE dummy）。

**估计量**：
```
Qh = (1-k) * QXX + k * QXZ * QZZ⁻¹ * QXZ'
beta = Qh⁻¹ * [(1-k) * QXy + k * QXZ * QZZ⁻¹ * QZy]
```

### 2.2 VCE 计算

**同方差情况**（`coviv` 为空）：
```
sigmasq = e'e / (N - dofminus)
V = 1/N * sigmasq * Qh⁻¹
```

**异方差/聚类情况**（inefficient LIML）：

`coviv` 为空（默认）：
```
aux5 = solve(Qh, QXZ)            # Qh^-1 * QXZ  (K×L)
aux9 = solve(QZZ, aux5')         # QZZ^-1 * aux5'  (L×K)
V = 1/N * aux9' * omega * aux9   # (K×L) * (L×L) * (L×K) = K×K
```

等价矩阵形式（K×K，由 aux9 = QZZ^-1 * QXZ' * Qh^-1 推导）：
```
V = 1/N * Qh^-1 * QXZ * QZZ^-1 * omega * QZZ^-1 * QXZ' * Qh^-1
```

`coviv` 非空（`coviv="coviv"`）：
```
aux3 = solve(QZZ, QXZ')          # QZZ^-1 * QXZ'  (L×K)
aux10 = QXZ * aux3               # QXZ * QZZ^-1 * QXZ'  (K×K)
aux11 = solve(aux10, aux3')      # aux10^-1 * aux3'  (K×L)
V = 1/N * aux11 * omega * aux11'  # (K×L) * (L×L) * (L×K) = K×K
```

omega 由 `m_omega(vcvo)` 计算，使用 LIML 残差。

**过度识别检验**：
```
beta_2s = [QXZ · omega⁻¹ · QXZ']⁻¹ QXZ · omega⁻¹ · QZy  // 2SLS 估计量（Q-矩阵形式）
e_2s = y - X * beta_2s
QZe = Z'e_2s / N
J = N * QZe' * omega⁻¹ * QZe
```

### 2.3 Fuller 修正

Fuller(δ) 修正通过调整 k-class 参数减少 LIML 的有限样本偏差：
- `fuller(0)` 等价于标准 LIML
- `fuller(1)` 是最常用的 Fuller 修正
- `fuller(4)` 提供更强的偏差修正但增加方差

---

## 3. m_omega：正交条件协方差矩阵

`m_omega(vcvo)` 是 GMM/LIML VCE 的核心，计算正交条件 `g_i = Z_i * e_i` 的协方差矩阵。

**`vcvo` 结构**（来自 `ivreghdfe.ado` Mata 中的 `ms_vcvorthog`）：
- `e`：残差向量（N×1）
- `Z`：工具变量矩阵（N×L）
- `wvar`：权重变量（N×1）
- `robust`：是否 robust VCE
- `clustvarname` / `clustvarname2` / `clustvarname3`：聚类变量名
- `kernel` / `bw` / `tdelta` / `center`：HAC 参数
- `N`：观测数
- `dofminus`：已吸收 FE 的自由度扣减
- `ZZ`：Z'Z 矩阵（L×L）

`m_omega` 根据 `vcvo` 中的 VCE 类型标志（robust / cluster / HAC）选择对应公式计算 omega。

### 3.1 同方差
```
omega = sigmasq * QZZ
```

### 3.2 异方差稳健（White/HC1）
```
omega = 1/N * sum(Z_i' * e_i² * Z_i)
```

### 3.3 聚类稳健
```
omega = 1/N * sum_g(Z_g' * e_g * e_g' * Z_g)
其中 g 为聚类组，Z_g 和 e_g 为组内子矩阵
```

### 3.4 HAC（Newey-West / Bartlett）
```
omega = omega_0 + sum_{j=1}^{bw} k(j/bw) * (omega_j + omega_j')
其中 omega_j = 1/N * sum_t Z_t' * e_t * e_{t-j}' * Z_{t-j}
```

---

## 4. Python 实现矩阵

### 4.1 GMM2S 实现步骤

```python
def fit_gmm2s(self, X, y, Z, vcvo):
    # Step 1: 初始 IV 估计（得到残差）
    beta_1s = self._iv_fit(X, y, Z)
    e_1s = y - X @ beta_1s

    # Step 2: 计算 omega
    omega = self._compute_omega(Z, e_1s, vcvo)
    W = np.linalg.inv(omega)

    # Step 3: 高效 GMM
    XZ = X.T @ Z / N
    Zy = Z.T @ y / N
    Q = XZ @ W @ XZ.T
    beta_2s = np.linalg.solve(Q, XZ @ W @ Zy)

    # Step 4: VCE
    V = np.linalg.inv(Q) / N

    # Step 5: Hansen J
    e_2s = y - X @ beta_2s
    Ze = Z.T @ e_2s / N
    J = N * Ze.T @ W @ Ze

    return beta_2s, V, J
```

### 4.2 LIML 实现步骤

```python
def fit_liml(self, X, y, Z, Z2=None, fuller=0, kclass=None):
    # Y matrix: [y, X_endo]
    Y = np.column_stack([y, X_endo])

    # W and W1 (residual matrices, not projection matrices)
    ZZinv = np.linalg.inv(Z.T @ Z)
    W = Y.T @ Y - Y.T @ Z @ ZZinv @ Z.T @ Y

    if Z2 is not None:
        Z2Z2inv = np.linalg.inv(Z2.T @ Z2)
        W1 = Y.T @ Y - Y.T @ Z2 @ Z2Z2inv @ Z2.T @ Y
    else:
        W1 = Y.T @ Y

    # lambda = min eigenvalue
    M = matrix_power_symmetric(W, -0.5)
    evals = scipy.linalg.eigvalsh(M @ W1 @ M)
    lambda_ = evals.min()

    # Exactly identified => lambda = 1
    if Z.shape[1] == X.shape[1]:
        lambda_ = 1.0

    # k-class parameter
    # L = structural instrument count (excluded + included exogenous)
    # In ivreghdfe's residualized framework, this equals cols(Z) seen by ivreg2
    L = Z.shape[1]  # after FE partial-out, Z contains only structural instruments
    if kclass is not None:
        k = kclass
    elif fuller > 0:
        k = lambda_ - fuller / (N - L)
    else:
        k = lambda_

    # beta (using Q-matrices consistently)
    QXX = X.T @ X / N
    QXZ = X.T @ Z / N
    QZy = Z.T @ y / N
    QXy = X.T @ y / N
    QZZ = Z.T @ Z / N
    QZZinv = np.linalg.inv(QZZ)

    aux = QXZ @ QZZinv @ QXZ.T
    Qh = (1-k) * QXX + k * aux
    aux2 = QXZ @ QZZinv @ QZy
    beta = np.linalg.solve(Qh, (1-k) * QXy + k * aux2)

    return beta, k, lambda_
```

### 4.3 CUE 实现步骤

```python
def fit_cue(self, X, y, Z, vcvo, beta_init):
    from scipy.optimize import minimize

    def cue_objective(beta):
        e = y - X @ beta
        omega = self._compute_omega(Z, e, vcvo)
        W = np.linalg.inv(omega)
        gbar = Z.T @ e / N
        J = N * gbar.T @ W @ gbar
        return float(J)

    res = minimize(cue_objective, beta_init, method='Nelder-Mead',
                   options={'ftol': 1e-7, 'maxiter': 10000})
    beta_cue = res.x
    J_cue = res.fun

    # Final VCE with rank checks (matching Stata s_gmmcue L6095-6112)
    e = y - X @ beta_cue
    omega = self._compute_omega(Z, e, vcvo)
    XZ = X.T @ Z / N
    try:
        aux1 = np.linalg.solve(omega, XZ.T)
    except np.linalg.LinAlgError:
        # omega near-singular, fallback to pseudoinverse
        aux1 = np.linalg.pinv(omega) @ XZ.T
    aux3 = (XZ @ aux1 + aux1.T @ XZ.T) / 2  # force symmetric
    V = np.linalg.inv(aux3) / N

    # Rank check (Stata: diag0cnt(V) > 0 => error 506)
    if np.linalg.matrix_rank(V) < V.shape[0]:
        raise ValueError("CUE variance matrix not of full rank; estimates unreliable")

    return beta_cue, V, J_cue
```

---

## 5. 与 Stata 对齐要点

| 要点 | Stata 行为 | Python 注意 |
|------|-----------|-------------|
| 求解器 | `cholqrsolve`（Cholesky + QR fallback） | `np.linalg.solve` 或 `scipy.linalg.solve` |
| 对称性 | `_makesymmetric` 强制对称 | 结果矩阵需显式对称化 `(A + A.T)/2` |
| 秩检查 | `diag0cnt` 检查对角零元素数 | `np.linalg.matrix_rank` 或检查 `inv` 结果 |
| 自由度 | `dofminus` 扣减已吸收 FE | 与 `AbsorbingOLS` 一致 |
| 权重 | `wf * wvar`（频率权重因子） | 注意 `fweight` 的 `wf` 处理 |
| CUE 优化器 | Stata `optimize()` | scipy `minimize`，需测试算法选择 |

---

## 6. 参考文献

1. Hansen, L. P. (1982). Large Sample Properties of Generalized Method of Moments Estimators. *Econometrica*, 50(4), 1029-1054.
2. Newey, W. K. (1985). Generalized Method of Moments Specification Testing. *Journal of Econometrics*, 29(3), 229-256.
3. Stock, J. H., & Yogo, M. (2005). Testing for Weak Instruments in Linear IV Regression. In *Identification and Inference for Econometric Models* (pp. 80-108). Cambridge University Press.
4. Baum, C. F., Schaffer, M. E., & Stillman, S. (2007). Enhanced routines for instrumental variables/GMM estimation and testing. *Stata Journal*, 7(4), 465-506.
5. Kleibergen, F., & Paap, R. (2006). Generalized reduced rank tests using the singular value decomposition. *Journal of Econometrics*, 133(1), 97-126.
