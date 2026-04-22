# Validation Summary

- Strict alignment standard: `field_level_strict`
- Target Stata version: `17`
- Commands with evidence rows: `14`
- Registered public datasets: `11`
- Commands with real-data evidence: `14`

## Command Coverage

| Command | Status | Synthetic cases | Real-data cases | Datasets |
| --- | --- | --- | --- | --- |
| `regress` | `stable` | 1 | 1 | grunfeld |
| `xtreg, fe` | `stable` | 1 | 1 | grunfeld |
| `areg` | `stable` | 1 | 1 | wagepan |
| `reghdfe` | `validated_subset` | 1 | 1 | wagepan |
| `ivregress 2sls` | `stable` | 1 | 1 | card |
| `ivreghdfe` | `validated_subset` | 1 | 1 | wagepan |
| `logit` | `stable` | 1 | 1 | mroz |
| `probit` | `stable` | 1 | 1 | mroz |
| `poisson` | `stable` | 1 | 1 | crime1 |
| `ppmlhdfe` | `validated_subset` | 1 | 1 | countymurders_ca |
| `did_imputation` | `validated_subset` | 1 | 1 | ezunem |
| `eventstudyinteract` | `validated_subset` | 1 | 1 | ezunem |
| `csdid` | `validated_subset` | 1 | 1 | ezunem |
| `rdrobust` | `validated_subset` | 1 | 1 | rdrobust_senate |

## Dataset Registry Snapshot

| Dataset | Family | Local path | Status | Commands |
| --- | --- | --- | --- | --- |
| `grunfeld` | panel | `research/data/public/panel/grunfeld.csv` | `validated` | regress, xtreg, fe, areg |
| `wagepan` | panel | `research/data/public/panel/wooldridge/wagepan.csv` | `validated` | xtreg, fe, areg, reghdfe, ivreghdfe |
| `card` | iv | `research/data/public/iv/card.csv` | `validated` | ivregress 2sls |
| `mroz` | binary | `research/data/public/binary/mroz.csv` | `validated` | logit, probit |
| `crime1` | count | `research/data/public/count/crime1.csv` | `validated` | poisson |
| `countymurders_ca` | count_hdfe | `research/data/public/gravity/countymurders_ca.csv` | `validated` | ppmlhdfe |
| `ezunem` | did | `research/data/public/did/ezunem_prepared.dta` | `validated` | did_imputation, eventstudyinteract, csdid |
| `jtrain` | did | `research/data/public/did/jtrain_prepared.dta` | `registered` | did_imputation |
| `ff3` | finance | `research/data/public/finance/fama_french/ff3/F-F_Research_Data_Factors.csv` | `registered` | regress |
| `ff5` | finance | `research/data/public/finance/fama_french/ff5/F-F_Research_Data_5_Factors_2x3.csv` | `registered` | regress |
| `rdrobust_senate` | rd | `research/vendor/stata_community/rdrobust/rdrobust-master/stata/rdrobust_senate.dta` | `validated` | rdrobust |
