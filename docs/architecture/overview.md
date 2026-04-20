# 总体架构说明

## 1. 目标

项目架构不再围绕少量线性模型命令展开，而是围绕“Stata 命令映射平台”展开。平台需要兼顾：

- Python 原生接口的长期可维护性
- Stata 命令迁移时的低摩擦使用体验
- 规则来源与对齐证据的可追踪性
- synthetic 与真实数据双线验证

## 2. 四层结构

### `core`

职责：

- 提供稳定的 Python 原生估计器
- 定义公共结果对象与统一拟合接口
- 不直接绑定具体 Stata 命令字符串

典型对象：

- `OLS`
- `FixedEffectsOLS`
- `AbsorbingOLS`
- `IV2SLS`
- `Poisson`
- `Logit`
- `Probit`

### `compat.stata`

职责：

- 提供常见 Stata 命令的兼容映射层
- 复用 `core`，但命名、默认值和字段尽量贴近 Stata

典型函数：

- `regress()`
- `xtreg_fe()`
- `areg()`
- `reghdfe()`
- `ivregress_2sls()`
- `ivreghdfe()`
- `poisson()`
- `ppmlhdfe()`

### `research`

职责：

- 保存官方手册、公开源码、返回值、自由度、修正因子、样例设计与已知差异
- 为每个新命令提供实现前的规则依据

组成：

- 命令族规划
- 源码清单
- 逐命令研究档案
- 公开数据集目录
- 本地源码镜像区

### `validation`

职责：

- 管理 synthetic 黄金样例
- 管理真实公开数据样例
- 驱动 Stata 双跑
- 输出字段级 diff 报告

## 3. 依赖方向

- `compat.stata` 依赖 `core`
- `validation` 依赖 `core` 与 `compat.stata`
- `research` 不依赖估计器实现，但为其提供依据

禁止：

- 用 `compat.stata` 反向约束 `core` 内部结构
- 在无研究档案时直接实现新命令
- 用真实数据测试替代 synthetic 规则测试

## 4. 当前默认主线

近期默认主线为：

- `Panel / FE / HDFE`

这条线的关键中间层是：

- `AbsorbingOLS` 或等价吸收式内核

该内核后续将同时服务：

- `areg`
- 双向 FE
- `reghdfe`
- `ivreghdfe`
- `ppmlhdfe`

## 5. 执行约束

- 研究档案先于实现
- 双线验证先于 `done`
- 社区命令默认作为扩展兼容层，不直接混入核心稳定 API 承诺
