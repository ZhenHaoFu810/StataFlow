# 审计后任务包 002：Stata 因子变量、交乘项与 `absorb()` 命令层语义

## 1. 任务背景

当前项目已经有较完整的估计器内核与 `compat.stata` wrapper，但 **Stata 因子变量语义基本缺失**，`absorb()` 的命令层语法也还不完整。

这意味着下面这类高频写法目前并不能作为真正的 Stata 命令迁移体验来使用：

- `reghdfe y c.x1#c.x2`
- `reghdfe y c.x1##c.x2`
- `reghdfe y i.industry##c.post`
- `reghdfe y i.treat##i.post`
- `regress y c.x1##c.x2`
- `poisson y c.x1##c.x2`
- `reghdfe y x1##x2, absorb(firm year)`

这是一个真实的命令层缺口，而不是“语法糖问题”。对实证研究者来说，`#` 和 `##` 的语义就是命令本身的一部分：

- `c.x1#c.x2` 只包含交乘项
- `c.x1##c.x2` 包含 `x1`、`x2` 和 `x1*x2`
- `i.a#i.b` 表示分类变量交互虚拟变量
- `i.a##c.x` 表示分类主效应、连续主效应和交互项的完整展开

同时，`reghdfe y x1##x2, absorb(firm year)` 这类命令还有一个关键语义：

- 主效应可能因为 absorbed FE 而被完全共线并被省略
- 但交互项如果仍有组内变化，应该继续可识别

这不是特殊边角情况，而是 `reghdfe`/`areg`/面板实证中的常见用法。

如果没有这层支持，当前库虽然数值内核强，但仍不是用户可直接迁移的 Stata 风格库。

## 2. 总目标

本轮要建立 **Stata 因子变量语义的第一阶段命令层实现**，并把它接入当前高频 wrapper 命令，同时补上 `absorb()` 的常见命令层语法。

重点不是“凑出与手工构造交乘列相同的结果”，而是：

1. 明确建模语义是否与 Stata 对应
2. 明确设计矩阵构造过程是否与 Stata 因子变量规则一致
3. 明确 wrapper 是否真正接受 Stata 风格项并正确展开
4. 明确 absorbed FE 与因子变量主效应/交互项的共线性处理是否与 Stata 行为一致

## 3. 本轮必须完成的范围

### A. 建立因子变量解析与展开层

新增一个专门的命令层语义模块，建议放在：

- `src/statapy/compat/stata/factor_variables.py`

至少支持以下语法：

- `x1`
- `c.x1`
- `i.g1`
- `c.x1#c.x2`
- `c.x1##c.x2`
- `i.g1#i.g2`
- `i.g1##i.g2`
- `i.g1#c.x1`
- `i.g1##c.x1`

本轮允许只支持 **连续变量与分类变量** 的一阶 `# / ##` 展开，不强行一次做完整 Stata factor grammar，但不能只做连续变量子集。

需要明确一个默认规则：

- 普通裸变量 `x1` 在 estimator 层仍作为普通列处理
- Stata factor 语义只在显式 `c.` / `i.` 标记或 `#` / `##` term 中触发
- 不允许对裸变量偷偷猜测为 `i.` 或 `c.`

### B. 明确本轮支持与拒绝边界

必须显式处理，而不是静默接受：

- 对本轮支持的语法：正常展开
- 对本轮暂不支持的语法：直接 `ValueError`

至少要显式拒绝：

- `ib#.var`
- `o.var`
- `b.var`
- 时间序列算子如 `L.x`
- 三阶及以上因子交互
- 更高阶复杂组合
- 本轮未实现的任意 factor 语法变体

不能出现“字符串被读进来但当普通变量名忽略处理”的情况。

### C. 接入高频 wrapper 命令

至少接入以下 wrapper：

- `regress`
- `areg`
- `reghdfe`
- `ivregress_2sls`
- `ivreghdfe`
- `logit`
- `probit`
- `poisson`
- `ppmlhdfe`

要求是：

- `x` 参数中允许混合普通变量名和 factor-term
- wrapper 内部负责把 term 展开成设计矩阵列
- 结果对象中保留稳定、可预测、尽量接近 Stata 习惯的列名
- `absorb` 参数必须支持：
  - `absorb="firm"`
  - `absorb=["firm", "year"]`
  - `absorb="firm year"` 这种 Stata 风格空格分隔写法

### D. absorbed FE 与因子项共线性语义

本轮必须显式覆盖以下场景：

- `reghdfe y c.x1##c.x2, absorb(firm year)`
- `reghdfe y i.treat##c.post, absorb(firm year)`
- `reghdfe y i.treat##i.post, absorb(firm year)`

要求不是“强迫主效应都保留”，而是：

- 若主效应被 FE 完全吸收，应按 Stata 风格识别为 omitted / dropped
- 若交互项仍有 variation，应保留并估计
- 结果对象、警告信息、参数名必须与这一行为一致

### E. 写清楚“本轮不是完整 factor grammar”

新增一份研究/产品文档，建议：

- `docs/research/factor-variable-semantics.md`

必须写清：

- Stata `#` 与 `##` 的当前支持子集
- `c.` / `i.` 的当前支持子集
- 当前 Python 端如何映射
- `absorb="firm year"` 如何解析
- absorbed FE 与主效应/交互项共线性时的当前处理原则
- 本轮明确不支持的 factor 语法
- 下一轮若要继续扩展，应优先做什么

### F. 更新对外文档

至少同步更新：

- `README.md`
- `docs/command-support-matrix/regress.md`
- `docs/command-support-matrix/reghdfe.md`
- `docs/command-support-matrix/ivregress_2sls.md`
- `docs/command-support-matrix/ivreghdfe.md`
- `docs/command-support-matrix/logit.md`
- `docs/command-support-matrix/probit.md`
- `docs/command-support-matrix/poisson.md`
- `docs/command-support-matrix/ppmlhdfe.md`

文档必须诚实区分：

- 已支持：连续变量与分类变量的一阶 `#` / `##`
- 已支持：`absorb` 的 list 和空格分隔字符串
- 未支持：更复杂 factor grammar 与更高阶组合

## 4. 测试要求

### A. parser / expansion 单元测试

新增专门测试，验证：

- `["x1"]` 与 `["c.x1"]` 语义一致
- `["i.g1"]` 会生成稳定的虚拟变量展开并有明确基准组处理
- `["c.x1#c.x2"]` 只生成交乘项
- `["c.x1##c.x2"]` 生成主项 + 交乘项
- `["i.g1#i.g2"]` 只生成交互项
- `["i.g1##c.x1"]` 生成分类主效应、连续主效应、交互项
- 混合 varlist 顺序稳定
- `absorb="firm year"` 会被解析成两个 absorb 变量
- 不支持语法会明确报错

### B. 与手工构造设计矩阵的等价测试

至少对以下命令做“命令语义 vs 手工展开”的等价测试：

- `regress`
- `reghdfe`
- `poisson` 或 `logit`

例如：

- `regress(..., x=["c.x1#c.x2"])`
  与
- `regress(..., x=["x1_x2_manual"])`

结果应严格一致。

还要至少覆盖一个分类变量场景，例如：

- `regress(..., x=["i.g1##c.x1"])`
  与
- 手工 dummy + interaction 展开后的设计矩阵

结果应严格一致。

### C. Stata 双跑测试

至少新增以下 dual-run case：

- `regress y c.x1#c.x2`
- `regress y c.x1##c.x2`
- `regress y i.g1##c.x1`
- `reghdfe y c.x1##c.x2, absorb(...)`
- `reghdfe y i.g1##c.x1, absorb(firm year)`
- 一个非线性命令的 `##` case：`logit`、`probit`、`poisson` 三者任选其一

重点比较：

- 系数
- 标准误
- 检验统计量
- 结果列名/参数语义
- 被吸收或共线后被省略的主效应行为

### D. 反“凑数值”要求

不能只做“factor syntax -> 手工构造列 -> 结果一样”的最小测试然后宣称完成。

必须额外证明：

- wrapper 确实理解了 Stata term 语义
- 不支持的 term 不会悄悄漏掉或当普通列名使用
- Stata 双跑样例不是靠宽容差放过
- absorbed FE 与主效应/交互项的识别结果不是靠特判写死的

## 5. 禁止事项

本轮不要做：

- 完整 base-level 语义
- 完整时间序列算子
- 所有 `fvvarlist` 变体
- 所有 Stata factor 语法一次做完
- 借机扩其他无关算法面

本轮的目标是把 **连续变量 + 分类变量的一阶因子交互语义** 以及常见 `absorb()` 写法作为命令层基础打牢。

## 6. 验证要求

完成后至少回报：

```powershell
python -m pytest tests/test_factor_variables.py -v
python -m pytest tests/test_compat_stata_linear.py tests/test_compat_stata_hdfe.py tests/test_compat_stata_iv.py tests/test_compat_stata_glm.py -v
python -m pytest tests -v
```

如果新增 golden dual-run 测试，也要在报告里单列说明通过情况。

## 7. 完成标准

本轮通过的最低标准：

- 连续变量与分类变量的一阶 `#` / `##` 语义已进入 wrapper 层
- 高频命令 wrapper 已可直接接受这些 term
- `absorb="firm year"` 这类命令层写法已正确解析
- 不支持语法会明确拒绝，不会静默忽略
- 至少 1 个线性命令、1 个 HDFE 命令、1 个非线性命令完成 dual-run 证据
- 至少 1 个 absorbed FE 下主效应被吸收但交互项仍可识别的 case 被验证
- 文档、support matrix、报告同步一致

本轮即使通过，也**不代表完整 Stata factor-variable grammar 已实现**。如果 Claude Code 在报告里把本轮夸大成“Stata 因子变量已完整支持”，视为未完成。
