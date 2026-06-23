# M10 Shared Infrastructure 测试设计登记

## 1. Synthetic 双跑

| ID | 审查问题 | DGP / 设计 | 新颖性 | Stata 命令 | Python API | 比较字段 | 结果 | Evidence |
|---|---|---|---|---|---|---|---|---|
| M10-S01 | 因子变量展开与基期/交互项 | `i.g##c.x`，g∈{1,2,3}，手工构造交互系数 | 新 DGP、新交互结构，专门检查 Python 列名与基期处理 | `regress y i.g##c.x` | `regress(df,'y',['i.g##c.x'])` | nobs, df, R², 全部系数, 完整 VCE | PASS | `evidence/synthetic/M10-S01.json` |
| M10-S02 | Robust VCE 完整矩阵 | 异方差误差 `z * ε` | 专门比较完整 robust VCE 矩阵而非仅 SE | `regress y x z, robust` | `regress(..., vce='robust')` | 系数、完整 VCE | PASS | `evidence/synthetic/M10-S02.json` |
| M10-S03 | Cluster VCE 小样本与 singleton | 聚类变量含一个 singleton cluster | 检查 singleton 是否被保留、G 统计、df 处理 | `regress y x, cluster(cid)` | `regress(..., vce='cluster', cluster='cid')` | nobs, n_clust, df_resid, 系数, VCE | PASS | `evidence/synthetic/M10-S03.json` |
| M10-S04 | Sample mask 与缺失值筛选 | y/x/z 分别缺失，保留 cluster 变量 | 直接比较 `e(sample)` 与 Python `sample_mask` 的逐行映射 | `regress y x z, cluster(cid)` | `regress(..., vce='cluster', cluster='cid')` | nobs, sample mask, 系数, VCE | PASS | `evidence/synthetic/M10-S04.json` |
| M10-S05 | StataRunner 路径与错误处理 | 含空格/Unicode 的输出目录；无效命令 | 首次系统检查 runner 对非 ASCII 路径和运行时错误的反馈 | `regress y x` / `regress y nonexistent_var` | `StataRunner.run_do_file` | exit_code, log 内容 | PASS | `evidence/synthetic/M10-S05.json`（由测试内部保存） |
| M10-S06 | 完全共线性筛选 | `x2 == x1` | 检查冗余列删除、维度一致性 | `regress y x1 x2` | `regress(df,'y',['x1','x2'])` | 系数名、VCE 维度 | PASS | `evidence/synthetic/M10-S06.json` |
| M10-S07 | 空解释变量 / 常数项模型 | 仅 y 变量 | 检查 ResultSchema 在 0 个回归元时的有效性 | `regress y` | `regress(df,'y',[])` | nobs, df, _cons, VCE | PASS | `evidence/synthetic/M10-S07.json` |

## 2. 真实数据双跑

| ID | 数据来源 | 研究设计 | Stata 命令 | Python API | 比较字段 | 结果 | Evidence |
|---|---|---|---|---|---|---|---|
| M10-R01 | `research/data/public/binary/oos/vote1.csv` | 竞选支出与党派交互 | `regress voteA i.democA##c.lexpendA` | `regress(df,'voteA',['i.democA##c.lexpendA'])` | nobs, df, R², 系数, 完整 VCE | PASS | `evidence/real-data/M10-R01.json` |
| M10-R02 | `research/data/public/did/jtrain_prepared.dta` | 含大量缺失值的 scrap 对 grant + year FE，cluster(fcode) | `regress lscrap grant i.year, cluster(fcode)` | `regress(df,'lscrap',['grant','i.year'], vce='cluster', cluster='fcode')` | nobs, sample mask, df, n_clust, 系数, VCE | PASS | `evidence/real-data/M10-R02.json` |

## 3. 变形 / 性质测试

| ID | 性质 | 验证方式 | 结果 | Evidence |
|---|---|---|---|---|
| M10-P01 | 行顺序改变不应改变估计结果 | Python 与 Stata 双跑（Python 全系数/VCE；Stata 系数/SE） | PASS | `evidence/property/M10-P01.json` |
| M10-P02 | 增加未使用的无关列不应改变结果 | Python 比较 | PASS | `evidence/property/M10-P02.json` |
| M10-P03 | 聚类标签一致置换不应改变 cluster VCE | Python 与 Stata 双跑 | PASS | `evidence/property/M10-P03.json` |

## 4. 与旧测试差异说明

- 所有 DGP、seed、Stata `.do` 内容均为本轮新建，未使用 `tests/golden/` 中的样本生成函数或 `.do` 文件。
- 与既有 `test_factor_variables.py` 的区别：本模块从完整回归结果（系数名、VCE、sample mask）角度验证因子变量，而非仅检查设计矩阵。
- 与既有 `test_result_schema.py` 的区别：本模块通过现场 Stata 双跑验证 schema 字段与 Stata `e()` 的对应关系。
