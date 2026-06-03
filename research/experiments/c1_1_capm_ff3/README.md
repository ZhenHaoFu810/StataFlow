# C1.1: CAPM / Fama-French 三因子资产定价回归

**实验日期:** 2026-04-30
**优先级:** P0
**数据:** Fama-French 3-Factor daily returns (1926-2025, N=1297 months)

## 研究问题

小盘股溢价 (SMB) 是否能被市场风险 (Mkt-RF) 和价值因子 (HML) 解释？

回归: `SMB ~ Mkt-RF + HML`

检验:
- vce="ols": 标准 OLS
- vce="robust": HC1 异方差稳健标准误
- vce="cluster year": 按年份聚类（面板 HAC 的简单版本）

## 经济学解释

- β_Mkt-RF: SMB 与市场因子的条件相关性。如果显著为正，说明小盘股溢价部分来自市场风险暴露
- β_HML: SMB 与价值因子的相关性。如果显著为负，说明小盘股和价值股有相反的风险特征
- R²: 市场和价值因子对小盘股溢价的解释力

## 数据来源

Kenneth French Data Library: F-F_Research_Data_Factors.csv
https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html

## 预期结果

- 系数、SE、t-统计量、R²、F-统计量在 Stata 和 Python 之间完全一致 (rtol < 1e-6)
- robust 和 cluster VCE 同样一致
