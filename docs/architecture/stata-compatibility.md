# Stata 对齐规范

## 1. 目标版本

- 默认目标版本：`Stata 17`
- 当前本机验证路径基准：`D:\Software\Stata17\StataMP-64.exe`

## 2. 命令研究来源分流

项目默认将命令分成两类研究路径：

### A 类：公开源码命令

优先通过本地源码镜像研究：

- `reghdfe`
- `ivreghdfe`
- `ppmlhdfe`
- `did_imputation`
- `eventstudyinteract`
- `rdrobust`

要求：

- 先下载到 `research/vendor/stata_community/`
- 建立逐命令研究档案
- 记录源码入口、依赖、关键算法与最小实现子集

### B 类：官方内建命令

优先通过手册、返回值与双跑研究：

- `regress`
- `xtreg, fe`
- `areg`
- `ivregress`
- `logit`
- `probit`
- `poisson`

要求：

- 研究官方帮助文档与 manuals
- 固定 `e()` / `r()` 返回值解释
- 用对照样例反推自由度、修正因子与 summary 语义

## 3. 命令族优先级

当前优先级如下：

1. `Panel / FE / HDFE`
2. `IV / GMM`
3. `Binary / Count`
4. `DID / Event Study Extensions`

## 4. 样本筛选规则

默认硬规则：

- 任何参与估计的变量出现缺失，观测行必须被剔除
- 因变量、自变量、权重、cluster、FE、工具变量都参与样本判定
- 样本掩码必须记录到结果对象

## 5. 自由度与检验统计量

每个命令研究档案都必须明确：

- `df_model`
- `df_resid`
- 整体检验统计量语义
- cluster / FE / HDFE 下的小样本修正规则

不允许在缺乏明确研究依据时，把统计量差异写成“可接受”后直接放行。

## 6. 权重与协方差

当前已完成：

- `aweight`
- 单聚类
- FE + 单聚类

后续所有新权重、新协方差或新组合都必须独立研究、独立建样例。

## 7. 双线验证原则

每个命令都默认需要两条验证线：

### synthetic / controlled

用于锁定：

- 数学规则
- 边界条件
- 自由度
- 样本剔除
- cluster 与 FE 修正

### real public datasets

用于锁定：

- 真实研究环境中的稳健一致性
- 常见面板、金融因子、政策评估场景下的行为

## 8. 严格一致与统计意义等价

### 严格一致

默认要求以下字段在容差内一致：

- 系数
- 标准误
- 检验统计量
- 协方差矩阵
- 自由度
- `R-squared`
- `RMSE`

### 统计意义等价

只有在以下条件同时满足时才能接受：

- 差异来源可解释
- 推断结论不变
- 样例元数据记录原因与容差
- 已由 Codex 明确裁决接受

## 9. 进入实现前的最低要求

一个命令进入实现前，至少需要：

- 研究档案已创建
- 来源路径已确定为“源码”或“手册”
- synthetic 与 real-data 样例计划已登记
