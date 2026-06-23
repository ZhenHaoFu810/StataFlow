# REV-RD-01

## 元信息
- **命令**: `rdrobust`, `rdplot`
- **命令族**: `RD / Local Polynomial`
- **审查类型**: 源码审查
- **stataflow 版本**: 0.1.5
- **日期**: 2026-06-03

## 问题摘要
本次审查覆盖 RD 命令族的 4 个核心文件，共发现 **3 项 Critical、3 项 Major、4 项 Minor** 问题。核心风险集中在：
1. Stata 兼容性层面——`rdrobust` wrapper 默认行为与 Stata 17 不一致；
2. 统计方法层面——Cluster VCE 的带宽选择未考虑聚类结构，`rdplot` 协变量调整使用全局 OLS；
3. 工程层面——权重归一化缺失、结果模式外附加字段。

---

## 发现 1：rdrobust wrapper 默认未启用带宽选择（Critical）

### 现象描述
`compat/stata/rdrobust.py` 第 109–113 行：
```python
if h is None and bwselect is None:
    raise NotImplementedError(
        "Automatic bandwidth selection is required when h is not provided. "
        "Use bwselect='mserd' or provide h explicitly."
    )
```
Stata 17 的 `rdrobust` 在不提供 `h()` 时，**默认执行** `bwselect(mserd)`。Python wrapper 将 `bwselect` 默认设为 `None`，导致用户必须显式传入 `bwselect='mserd'` 才能复现 Stata 的默认行为。这违反了 AGENTS.md 中“Stata-compatible command layer”的设计目标。

### 根因分析
Wrapper 参数签名直接透传了 `bwselect: str | None = None`，未像 Stata 一样设置默认 `"mserd"`。

### 涉及文件
- `src/stataflow/compat/stata/rdrobust.py`

### 影响评估
- **影响范围**: 单一命令（`rdrobust`）
- **用户 workaround**: 有（显式传入 `bwselect='mserd'`）
- **是否阻塞实际使用**: 否，但造成 API 行为与 Stata 17 不一致

### 修复建议
将 wrapper 签名默认值改为 `bwselect: str = "mserd"`，或在 `h is None` 时自动回退到 `"mserd"`。预计工作量：5 分钟。

---

## 发现 2：Cluster VCE 的带宽选择未考虑聚类结构（Critical）

### 现象描述
`RDRobust.fit()` 第 886–902 行在自动带宽选择时调用 `_rdbwselect(..., cluster_l=g_l_full, cluster_r=g_r_full)`，但 `_rdbwselect` 内部仅将 cluster 计数用于 CER scaling（`_cer_scale`）。真正决定带宽的 `_three_step_bw_rd` / `_three_step_bw_sum` / `_three_step_bw_two` 及其底层 `_rdrobust_bw` **完全不接收 cluster 信息**，始终使用 `vce_bw` 映射后的 `"hc0"` 或 `"nn"` 计算残差。这意味着：
- 当用户指定 `vce='cluster'` 或 `vce='nncluster'` 时，带宽是基于 i.i.d./异方差稳健公式选出的；
- 只有最终点估计的 VCE 才使用 cluster-robust sandwich。

原始 `rdrobust` 包（Calonico-Cattaneo-Titiunik）在 cluster-robust 情形下，带宽选择中的有效样本量和方差估计都需要按聚类调整。

### 根因分析
`_rdrobust_bw` 函数签名及其实现缺少 `cluster_ids` 参数；`_rdbwselect` 将 cluster 信息仅传递给 `_cer_scale`，未下传至 three-step plug-in。

### 涉及文件
- `src/stataflow/estimators/rdrobust.py`（`_rdbwselect`, `_three_step_bw_*`, `_rdrobust_bw`）

### 影响评估
- **影响范围**: 命令族（`rdrobust` 的 cluster VCE 场景）
- **用户 workaround**: 无（除非手动提供 `h`）
- **是否阻塞实际使用**: 否，但统计方法不完整，可能导致带宽与 VCE 不匹配

### 修复建议
在 `_rdrobust_bw` 中加入 `cluster_ids` 参数，对 `nncluster`/`cluster` VCE 路径在 meat 矩阵计算时使用 `_rdrobust_vce_multi` 的 cluster-aggregation 逻辑，并基于聚类数量调整 effective sample size。预计工作量：1–2 天。

---

## 发现 3：rdplot 协变量调整使用全局 OLS 而非局部 FWL（Critical）

### 现象描述
`rdplot.py` 第 318–326 行：
```python
if Z is not None:
    Z_centered = Z - Z.mean(axis=0)
    y_centered = y - y.mean()
    gamma_cov = np.linalg.lstsq(Z_centered, y_centered, rcond=None)[0]
    y_l_adj = y_l - Z_l @ gamma_cov
    y_r_adj = y_r - Z_r @ gamma_cov
```
`rdplot` 使用**全局** OLS 估计 `gamma_cov`，然后 partial out。原始 `rdplot`（Stata / CCT 参考实现）的协变量调整是在**带宽内**（或至少是在 cutoff 邻域内）进行局部回归或 FWL，以避免全局协变量关系扭曲 RD 断点处的条件均值形状。如果协变量在 cutoff 两侧存在分布差异或跳跃，全局 OLS 会错误地吸收部分跳跃，导致拟合曲线与真实条件均值偏离。

### 根因分析
实现时简化了 covariate adjustment 路径，直接复用了全局最小二乘，未遵循局部多项式的局部性原则。

### 涉及文件
- `src/stataflow/estimators/rdplot.py`

### 影响评估
- **影响范围**: 单一命令（`rdplot` 带 `covs` 时）
- **用户 workaround**: 无（除非用户手动 partial out 后再传入）
- **是否阻塞实际使用**: 否，但可视化结果可能有偏

### 修复建议
改为在带宽 `h` 内分别对左右两侧运行局部 WLS（或至少使用带宽内的观测估计 `gamma_cov`），与 `rdrobust` 的 covariate adjustment 逻辑保持一致。预计工作量：0.5 天。

---

## 发现 4：rdplot bin statistics 与 fit line 的 y 值不一致（Major）

### 现象描述
当 `covs` 不为 `None` 时，`rdplot.fit()`：
1. 局部多项式拟合（`fit` DataFrame）使用 `y_l_adj` / `y_r_adj`（已 partial out covariates）；
2. 但分箱统计（`bins` DataFrame）在第 308–309 行仍调用 `_collapse_bins(x_l, y_l, edges_l)`，使用的是**原始** `y_l` / `y_r`。

这导致返回的 `bins`（用于画散点/柱状图）和 `fit`（用于画拟合线）基于不同的响应变量，图像上会出现系统性错位。

### 根因分析
`_collapse_bins` 调用发生在 covariate adjustment 之前，且 adjustment 后的 `y_l_adj` 未传入分箱步骤。

### 涉及文件
- `src/stataflow/estimators/rdplot.py`

### 影响评估
- **影响范围**: 单一命令（`rdplot` 带 `covs` 时）
- **用户 workaround**: 有（用户可自行调整 y 后再传入）
- **是否阻塞实际使用**: 否

### 修复建议
将 `_collapse_bins` 的输入改为 `y_l_adj` / `y_r_adj`，确保 bin means 与 fit line 基于同一响应变量。预计工作量：10 分钟。

---

## 发现 5：weights 参数缺少 aweight 归一化（Major）

### 现象描述
AGENTS.md 第 9 条明确规定：
> **aweight normalization:** Normalize so `sum(w) = N` after missing drop.

`rdrobust.py` 第 807–820 行处理 `weights`：
```python
fw = df[self.weights].to_numpy(dtype=float)
valid = fw > 0
y = y[valid]
fw = fw[valid]
...
w_h_l = w_h_l * fw_l
```
代码仅筛选正权重并与核权重相乘，**未做任何归一化**。如果用户传入的是 aweights（如 Stata 的 `aweight`），`sum(fw) != N` 会导致 VCE 和带宽选择中的有效样本量计算出现偏差。当前实现更像 fweights（频数权重），但接口文档未区分两种权重类型。

### 根因分析
实现时未区分 aweight / fweight，也未执行 aweight 归一化。

### 涉及文件
- `src/stataflow/estimators/rdrobust.py`

### 影响评估
- **影响范围**: 单一命令（`rdrobust` 带 `weights` 时）
- **用户 workaround**: 有（用户可手动归一化权重后再传入）
- **是否阻塞实际使用**: 否

### 修复建议
在 missing/positive 筛选后增加 `fw = fw / fw.sum() * len(fw)` 归一化步骤，并在 docstring 中明确说明当前仅支持 aweight 行为。预计工作量：15 分钟。

---

## 发现 6：`_rd_extras` 动态附加属性不符合 ResultSchema 规范（Major）

### 现象描述
`rdrobust.py` 第 1269–1298 行：
```python
result._rd_extras = { ... }
```
`ResultSchema` 并未定义 `_rd_extras` 字段，而是在实例上动态附加属性。这破坏了 ResultSchema 的契约：下游消费者（如 golden dual-run tests、序列化、结果比较框架）无法通过 schema 反射发现这些字段，可能导致字段丢失或类型检查失败。

### 根因分析
RD 特有统计量（如 `tau_cl_l`, `tau_bc_r`, `h_l`, `h_r` 等）没有找到合适的 schema 槽位，临时使用了动态属性。

### 涉及文件
- `src/stataflow/estimators/rdrobust.py`

### 影响评估
- **影响范围**: 跨命令（任何消费 ResultSchema 的测试/后处理逻辑）
- **用户 workaround**: 无（对动态属性的依赖不可靠）
- **是否阻塞实际使用**: 否

### 修复建议
将 RD 特有字段纳入 `ResultSchema` 的正式扩展（例如新增 `rd_info: dict | None` 字段），或在 `diagnostics` / `fit` 中提供规范化存储。预计工作量：0.5 天（需评估 ResultSchema 变更对其它命令的影响）。

---

## 发现 7：`_kernel_weight` 包含非标准 `1/h` 缩放（Minor）

### 现象描述
```python
w[inside] = (1.0 - np.abs(u[inside])) / h
```
标准 local polynomial regression 的核函数为 `K(u)`（如三角核 `1-|u|`），不含额外的 `1/h` 密度归一化因子。虽然经推导，该常数缩放因子在 WLS 点估计、VCE sandwich 以及 bandwidth selection 的 rate 计算中会被整体抵消，**不造成数学偏差**，但它：
1. 与 CCT `rdrobust` 参考实现不一致，增加跨实现比对的认知成本；
2. 若未来有人修改 VCE 公式时未意识到 `w` 已含 `1/h`，可能引入隐式错误。

### 涉及文件
- `src/stataflow/estimators/rdrobust.py`

### 修复建议
移除 `/ h` 因子，保持核函数为纯形状函数。预计工作量：5 分钟（需跑通现有测试验证数值不变）。

---

## 发现 8：`_vce_hc0` 与 `_vce_nn` 函数体完全重复（Minor）

### 现象描述
两个函数的代码逐行相同，仅函数名不同：
```python
def _vce_nn(...): ...
def _vce_hc0(...): ...  # 与 _vce_nn 完全一致
```
这是维护隐患：未来若修改 VCE 公式，极易遗漏其中一个副本。

### 涉及文件
- `src/stataflow/estimators/rdrobust.py`

### 修复建议
合并为单一函数 `_vce_sandwich(inv_gram, R, w, res)`，由 `_vce_nn` 和 `_vce_hc0` 薄包装调用。预计工作量：10 分钟。

---

## 发现 9：rdrobust docstring 未完整反映支持的 bwselect（Minor）

### 现象描述
`compat/stata/rdrobust.py` docstring 第 76–78 行：
> Supported: "mserd", "msesum", "msetwo", ...

而 `RDRobust` 的类 docstring 第 663–665 行却说：
> bwselect : str or None. Bandwidth selector. Supported: "mserd".

类级别文档严重不完整，容易误导使用者认为仅支持 `mserd`。

### 涉及文件
- `src/stataflow/estimators/rdrobust.py`

### 修复建议
统一两处 docstring，明确列出全部 9 个支持的 selector。预计工作量：5 分钟。

---

## 发现 10：`ResultSchema` 的 `df_model` / `df_resid` 定义随意（Minor）

### 现象描述
`fit()` 第 1251–1253 行：
```python
fit=FitInfo(
    df_model=float(self.p + 1),
    df_resid=float(nobs - 2 * (self.p + 1)),
),
```
RD local polynomial 的两侧各估计 `p+1` 个参数，总有效参数约为 `2(p+1)`。当前 `df_model` 仅计单侧参数，`df_resid` 的定义也缺乏统计依据。rdrobust 原始包并不以传统 OLS 方式报告 `df_model`/`df_resid`。

### 涉及文件
- `src/stataflow/estimators/rdrobust.py`

### 修复建议
将 `df_model` 设为 `float(2 * (self.p + 1))` 或设为 `np.nan` 并附注说明 RD 无传统 df_model 概念。预计工作量：10 分钟。

---

## 关联项
- `docs/architecture/stata-compatibility.md` — Stata 兼容层行为规范
- `docs/operations/review-gates.md` — 统计偏差需走 Codex 仲裁
- `AGENTS.md` §9 — aweight 归一化硬性规则
- 已知 issue：Fuzzy RD 自动带宽选择已显式 `NotImplementedError`，不在本次审查范围内（属已声明的缺失功能）
