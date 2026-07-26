# Dataset Registry

本表登记“迁移成功证据册”使用或预留的公开数据集。  
规则：

- 只有登记过的数据集才能进入主证据集
- 优先官方/教学/论文复现数据
- Kaggle 仅在许可明确、研究价值高时纳入

## Registered Datasets

| Key | Family | Source | Local path | License / redistribution | Applicable commands | Preprocess entry | Validation status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `grunfeld` | Panel | RDatasets / plm | `research/data/public/panel/grunfeld.csv` | Open teaching mirror | `regress`, `xtreg, fe`, `areg` | none | validated |
| `wagepan` | Panel | RDatasets / Wooldridge | `research/data/public/panel/wooldridge/wagepan.csv` | Open teaching mirror | `xtreg, fe`, `areg`, `reghdfe`, `ivreghdfe` | none | validated |
| `card` | IV | Wooldridge teaching data | `research/data/public/iv/card.csv` | Open teaching mirror | `ivregress 2sls` | none | validated |
| `mroz` | Binary | Wooldridge teaching data | `research/data/public/binary/mroz.csv` | Open teaching mirror | `logit`, `probit` | none | validated |
| `crime1` | Count | Wooldridge teaching data | `research/data/public/count/crime1.csv` | Open teaching mirror | `poisson` | none | validated |
| `countymurders_ca` | Count / HDFE | Wooldridge / public policy panel subset | `research/data/public/gravity/countymurders_ca.csv` | Open teaching/policy subset | `ppmlhdfe` | none | validated |
| `ezunem` | DID | Wooldridge DID teaching data | `research/data/public/did/ezunem_prepared.dta` | Prepared local mirror from open teaching data | `did_imputation`, `eventstudyinteract`, `csdid` | `research/data/public/did/prepare_ezunem.py` | validated |
| `jtrain` | DID | Wooldridge DID teaching data | `research/data/public/did/jtrain_prepared.dta` | Prepared copy from open teaching data | `did_imputation`, `eventstudyinteract`, `csdid` | `research/data/public/did/prepare_jtrain.py` | Historical OOS: 2 passed, 1 differing sample |
| `ff3` | Finance | Kenneth French Data Library | `research/data/public/finance/fama_french/ff3/F-F_Research_Data_Factors.csv` | Public academic data library | `regress` | none | registered |
| `ff5` | Finance | Kenneth French Data Library | `research/data/public/finance/fama_french/ff5/F-F_Research_Data_5_Factors_2x3.csv` | Public academic data library | `regress` | none | registered |
| `rdrobust_senate` | RD | Official `rdrobust` Stata package (https://github.com/rdpackages/rdrobust) | `tests/data/rdrobust_senate.dta` | 随测试套件分发的公开副本 | `rdrobust` | `stata/cases/rdrobust_gen_z.do` | validated (development + OOS) |
| `airfare` | Panel | Wooldridge teaching data | `research/data/public/panel/oos/airfare.csv` | Open teaching mirror | `regress`, `xtreg, fe`, `areg`, `reghdfe` | none | OOS validated |
| `vote1` | Binary | Wooldridge teaching data | `research/data/public/binary/oos/vote1.csv` | Open teaching mirror | `logit`, `probit` | none | OOS validated |
| `smoke` | Binary | Wooldridge teaching data | `research/data/public/binary/oos/smoke.csv` | Open teaching mirror | `logit` | none | OOS validated |
| `fertil1` | Count / Panel | Wooldridge teaching data | `research/data/public/count/oos/fertil1.csv` | Open teaching mirror | `poisson`, `ppmlhdfe` | none | OOS validated |

## Priority Expansion Queue

### First priority

- 更高维 firm-year / county-year panel
- 公开 staggered adoption panel
- RD 官方或论文复现数据
- 金融学经典教学/复现数据

### Second priority

- 更多 Fama-French / asset pricing 样例
- 公开 trade / gravity panel
- 更多 count / binary 实证数据

### Third priority

- 许可证或清洗成本高的数据
- 仅在某个命令边界确实需要时才增加的数据

## Current Notes

- 当前证据册已经覆盖主要命令族的真实数据 baseline。
- `ff3` / `ff5` 已入库但暂未进入主证据矩阵，后续用于扩展金融场景展示面。
- Validation Package 001 新增了 4 个 OOS 数据集：`airfare`、`vote1`、`smoke`、`fertil1`，全部来自 Wooldridge 教学数据。
- `jtrain` 用于历史 OOS DID 比较：`eventstudyinteract` 与 `csdid` 被分类为
  passed；`did_imputation` 因 Stata 与 Python 保留不同估计样本而不作数值
  对齐结论。
- `rdrobust_senate` 已同时用于开发期证据和 OOS 证据（covs + auto bandwidth）。
- `rdrobust_senate` 的验证证据使用公开副本 `tests/data/rdrobust_senate.dta`。
