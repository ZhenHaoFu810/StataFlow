# 结果对象与结构化导出规范

## 1. 目的

结果 schema 是实现层、Stata 导出层和测试层之间的共享契约。任何估计器、Stata runner 或双跑比较器都必须遵守该 schema。

## 2. 顶层结构

统一结果对象建议包含以下顶层字段：

```yaml
model:
  command: string
  estimator_family: string
  vcetype: string
  weight_type: string | null
  fe_vars: list[string]
  cluster_var: string | null
  has_constant: bool
sample:
  nobs: int
  n_input_rows: int
  sample_mask: list[bool] | encoded mask
  dropped_rows_reason: list[string] | null
fit:
  df_model: float
  df_resid: float
  rank: int
  rss: float
  tss: float
  mss: float
  rmse: float
  r2: float
  r2_adj: float
  f_stat: float | null
  f_pvalue: float | null
coefficients:
  rows:
    - name: string
      beta: float
      std_err: float
      t_stat: float
      p_value: float
      ci_low: float
      ci_high: float
      is_base: bool
      is_omitted: bool
variance:
  cov_matrix:
    row_names: list[string]
    values: 2d array
diagnostics:
  residual_df_correction: string | null
  cluster_count: int | null
  warnings: list[string]
provenance:
  source: "python" | "stata"
  stata_version_target: string | null
  stata_command: string | null
```

## 3. 字段规则

- 数值字段默认使用双精度浮点序列化
- 所有系数与协方差矩阵必须保留变量名顺序
- Stata-compatible factor-variable wrappers must retain Stata-style base/omitted rows in `coefficients` and matching zero rows/columns in `variance`; those rows are marked by `is_base` and `is_omitted`
- `sample_mask` 必须可逆推出保留样本，不能只给计数
- 缺失或不适用字段使用 `null`，不允许混用字符串 `"NA"`

## 4. Python 内部结果对象要求

- 应提供属性访问与序列化接口
- 导出为字典时键名与 schema 一致
- 结果对象中不应保存不可序列化的运行时句柄

## 5. Stata 导出要求

Stata 导出必须尽量映射到同一结构：

- 系数字段来自 `e(b)`
- 协方差矩阵来自 `e(V)`
- 自由度和样本数来自 `e()` 结果
- 任何无法直接提取的值应在 `.do` 导出脚本中显式构造

## 6. 精度与比较要求

- 默认比较精度由测试策略文档统一管理
- schema 本身不定义具体容差值，但要求每个数值字段可被比较器逐字段读取
- 若某字段允许统计等价而非严格一致，必须在测试用例元数据中声明

## 7. 缺失值与异常处理

结果 schema 中的缺失值规则：

- 统计上不存在的值：`null`
- 计算失败：应在 `diagnostics.warnings` 记录，并由调用层决定是否视为失败
- 不允许将失败静默吞掉后写入伪值
