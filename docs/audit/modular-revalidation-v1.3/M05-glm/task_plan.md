# M05 GLM 模块独立审查计划 v1.3

**Goal:** 对 StataFlow 的 M05 GLM 模块（`Logit`、`Probit`、`Poisson` 核心估计器及 `stataflow.compat.stata.logit()`、`probit()`、`poisson()` 包装器）进行独立审查，发现数学错误、统计语义偏差、代码缺陷、边界条件错误、结果字段错误和 Stata 17 复现失败。本轮只记录问题，不修改产品代码。

**Architecture:** 每个实验独立设计新的 DGP / 数据结构，独立编写新的 Stata 17 `.do` 文件和新的 Python 审查脚本，现场执行字段级双跑。审查资产保存在 `docs/audit/modular-revalidation-v1.3/M05-glm/evidence/` 下。共享基础设施问题登记为 Shared finding，但不得因此停止当前模块审查。

**Tech Stack:** Python 3.11.7, NumPy 1.26.4, pandas 3.0.2, SciPy 1.17.1, statsmodels 0.14.6, Stata 17 MP, project `stataflow` package.

---

## 审查基线

| 项目 | 值 |
|---|---|
| 基线分支 | `dev` |
| 基线 commit SHA | `2c7db1ca095e03d29c471e8d523fdaa943306174` |
| Python | 3.11.7 |
| NumPy | 1.26.4 |
| pandas | 3.0.2 |
| SciPy | 1.17.1 |
| Stata | 17 MP |

---

## 纳入审查的 API

- 核心估计器：`stataflow.estimators.Logit`、`stataflow.estimators.Probit`、`stataflow.estimators.Poisson`
- Stata 兼容层：`stataflow.compat.stata.logit`、`stataflow.compat.stata.probit`、`stataflow.compat.stata.poisson`
- 关键机制：IRLS/Fisher scoring、logit/probit link、Poisson log link、conventional/robust/cluster VCE、伪 R² / LR / deviance、predict / margins、样本筛选、共线性、aweight、分离/收敛。

---

## 关键风险领域

1. **MLE robust/cluster 小样本修正**：`logit`/`poisson` 的 robust VCE 是否应使用 `n/(n-1)` 或纯 sandwich；cluster VCE 是否应使用 `(n-1)/(n-k)·G/(G-1)` 或仅 `G/(G-1)`。当前代码、研究档案、legacy VCE 审计和单元测试相互矛盾。
2. **Probit 数值 Hessian 与 observed information**：有限差分 Hessian 的精度、robust/cluster 修正是否与 Stata 一致。
3. **完全/准完全分离**：稀有事件或强预测变量下，Python 是否会无提示不收敛，而 Stata 是否报告 perfect prediction 并仍返回结果。
4. **收敛边界**：最大迭代、公差、非收敛错误传播、IRLS 初始值敏感性。
5. **样本筛选与缺失值**：`y`、`x`、cluster、aweight 中缺失值是否导致 Python 与 Stata estimation sample 不一致；零/负权重处理。
6. **伪 R²、deviance、LR 统计量**：McFadden pseudo R²、LR chi2 p-value、df_model、df_resid；Poisson deviance 在 y=0 时的处理；Probit deviance 缺失。
7. **aweight 归一化与加权 IRLS**：`sum(w)=N` 后 working weights 计算是否正确。
8. **predict / margins 样本与 delta method**：`predict(type="pr")` 响应尺度、`margins, dydx(*)` AME 点估计和 SE 与 Stata 的对比。

---

## 实验设计

### Synthetic（至少 6 个，覆盖不同统计机制）

1. **S1**: 手工可计算小样本 logit（n=8，单一 0/1 预测变量），验证系数、SE、VCE、LL、伪 R²。
2. **S2**: 中等样本随机 logit，比较 ols/robust/cluster VCE，重点关注 robust/cluster 小样本修正。
3. **S3**: 稀有事件 / 近分离 logit（y 中 1 的比例极低，存在强预测变量），检查系数膨胀、收敛、Stata 的 perfect-prediction 提示。
4. **S4**: Probit 随机 DGP，比较 ols/robust/cluster VCE 和数值 Hessian 精度。
5. **S5**: Poisson 随机 DGP，含大量零值和过度离散，比较 ols/robust/cluster VCE、deviance、伪 R²。
6. **S6**: 缺失值、共线性、冗余变量与样本筛选测试（在 y/x/cluster/aweight 中插入缺失）。
7. **S7**: aweight 设计（logit/poisson），验证权重归一化和加权似然/得分。
8. **S8**: 不收敛 / 分离边界设计，比较 Python 与 Stata 的错误/结果行为。

### Real-Data（至少 2 个，使用公开 Stata 示例数据）

1. **R1**: Mroz 数据 (`webuse mroz`)，logit/probit `inlf` ~ `age educ kidslt6 kidsge6`，`vce(robust)`；同时检查 `margins, dydx(*)`。
2. **R2**: Fish 数据 (`webuse fish`)，Poisson `count` ~ `livebait camper persons child`，`vce(robust)`；验证过度离散下的 QMLE robust SE。
3. **R3**（扩展）: NLSW88 (`sysuse nlsw88`)，logit `collgrad` ~ `age grade tenure married smsa`，`vce(cluster industry)`，检查真实聚类 SE。
4. **R4**（扩展）: Ovary 数据 (`webuse ovary`)，Poisson `follicles` ~ `sin1 cos1 stime`，`vce(cluster mare)`，检查纵向计数数据的聚类 SE。

### Property / Metamorphic Tests（至少 3 个）

1. **P1**: 行顺序打乱不改变估计结果、VCE 和拟合统计量。
2. **P2**: 对连续解释变量做合法线性尺度变换，验证系数按反比变化、VCE 按平方反比变化（对数链接/概率链接的预测不变性）。
3. **P3**: 增加与现有变量完全共线或近似共线的冗余列，验证共线性检测、被丢弃变量列表、其余系数不变。
4. **P4**（扩展）: cluster 标签随机置换不改变 cluster VCE 矩阵。
5. **P5**（扩展）: `eform`/`or`/`irr` 变换后报告的系数和标准误符合 delta method；z/p/CI 仍在原始尺度。

---

## 字段级比较清单

每个实验必须比较：

- `nobs`、`n_input_rows`、`sample_mask`
- coefficient names / order
- coefficients、standard errors、z statistics、p-values、95% CI
- 完整 VCE matrix
- `df_model`、`df_resid`、`rank`
- log likelihood、伪 R²、LR chi2 / p-value
- deviance（若命令支持）
- `cluster_count`（若使用 cluster）
- 警告/错误行为

默认相对容差 `< 1e-6`；任何放宽必须记录字段、数量级和理论原因。

---

## 交付物

- `docs/audit/modular-revalidation-v1.3/M05-glm/task_plan.md`（本文件）
- `docs/audit/modular-revalidation-v1.3/M05-glm/test-design-register.md`
- `docs/audit/modular-revalidation-v1.3/M05-glm/findings.md`
- `docs/audit/modular-revalidation-v1.3/M05-glm/progress.md`
- `docs/audit/modular-revalidation-v1.3/M05-glm/summary.md`
- `docs/audit/modular-revalidation-v1.3/M05-glm/evidence/synthetic/`
- `docs/audit/modular-revalidation-v1.3/M05-glm/evidence/real-data/`
- `docs/audit/modular-revalidation-v1.3/M05-glm/evidence/property/`
- `docs/audit/modular-revalidation-v1.3/M05-glm/evidence/minimal-reproductions/`
- Python 审查脚本：`tests/audit_v1_3/m05_glm/`
- Stata `.do` 文件：`stata/cases/audit_v1_3_m05/`

---

## 执行顺序

按 `MASTER_AUDIT_BRIEF.md` 第 9 节标准流程执行：

1. 建立目录与 `audit_utils.py`。
2. 编写 Stata `.do` 模板和 Python 结果解析/比较工具。
3. 实现 synthetic 实验 S1–S8，逐个现场双跑并保存证据。
4. 实现 real-data 实验 R1–R4，保存数据来源、下载日期、哈希。
5. 实现 property tests P1–P5。
6. 对发现的偏差构造最小复现脚本 `repro_m05_*.py`。
7. 区分产品、测试、runner、parser 根因。
8. 撰写 `findings.md`、`progress.md`、`summary.md`、`test-design-register.md`。
9. 运行现有非 golden 测试，确认审查资产没有破坏仓库。
