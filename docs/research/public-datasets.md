# 公开数据集验证规划

## 目标

后续每个高频命令除了 synthetic 样例外，还应至少配一组真实公开数据集验证。

## 当前已下载的首批数据

本地目录：

- `research/data/public/finance/fama_french/`
- `research/data/public/panel/`

### 金融类

1. Fama-French 3 Factors
   - 来源：Kenneth French Data Library
   - 本地文件：
     - `research/data/public/finance/fama_french/F-F_Research_Data_Factors_CSV.zip`
     - `research/data/public/finance/fama_french/ff3/F-F_Research_Data_Factors.csv`
   - 预期用途：
     - `regress`
     - 真实金融时间序列回归基线

2. Fama-French 5 Factors (2x3)
   - 来源：Kenneth French Data Library
   - 本地文件：
     - `research/data/public/finance/fama_french/F-F_Research_Data_5_Factors_2x3_CSV.zip`
     - `research/data/public/finance/fama_french/ff5/F-F_Research_Data_5_Factors_2x3.csv`
   - 预期用途：
     - 多因子回归
     - 真实数据下的 OLS / robust / cluster 测试扩展

### 面板教学数据

3. `wagepan`
   - 来源：RDatasets / Wooldridge
   - 本地文件：
     - `research/data/public/panel/wooldridge/wagepan.csv`
   - 预期用途：
     - `xtreg, fe`
     - `areg`
     - 后续 HDFE 面板基线

4. `Grunfeld`
   - 来源：RDatasets / plm
   - 本地文件：
     - `research/data/public/panel/grunfeld.csv`
   - 预期用途：
     - 面板回归
     - FE 与吸收式实现的真实数据 sanity check

## 尚未下载但优先级较高的数据

- gravity trade panel
  - 面向 `ppmlhdfe`
- 州级或县级政策 panel
  - 面向 DID / event study
- 更多 Stata 官方公开样例
  - 面向 `areg`、`ivregress`

## 每个真实数据验证文档需记录

- 数据来源
- 下载方式
- 固定版本与处理日期
- 清洗脚本入口
- Stata 命令脚本
- Python 命令脚本
- 对齐字段
- 已知差异与解释

## 初始优先对应关系

- `regress`
  - Fama-French 因子回归
- `xtreg, fe`
  - `wagepan`
  - `Grunfeld`
- `areg`
  - `wagepan`
  - `Grunfeld`
- `reghdfe`
  - 后续补充公开 firm-year 或 panel 替代样例
- `ppmlhdfe`
  - 后续补充 gravity trade 数据
- DID 命令
  - 后续补充县级或州级政策 panel
