# ADR-0005: CSDID 结果契约

## 背景

`csdid` 的结果面曾与其他命令不一致：`csdid()` 返回拟合好的
`CSDID` 模型对象，但该对象没有默认可展示的 `ResultSchema`，也没有
`display()` / `summary()` 入口。1.2.0 在**不改变 `csdid()` 默认返回类型**
的前提下补齐该契约；改变返回类型仍属于未来主版本决策。

## 决策

确立以下向后兼容的结果契约：

1. **`csdid(...)` 继续返回拟合好的 `CSDID` 模型对象**。默认返回类型不变；任何返回类型变更需要单独的主版本决策。
2. **`CSDID.result` 属性**返回默认聚合（event aggregation）的 `ResultSchema`，与 `estat("event")` 逐字段一致。
3. **`CSDID.summary()` 与 `CSDID.display()`** 委托给上述默认 `ResultSchema` 的同名方法，不重复构造结果。
4. **`estat("simple" | "event" | "group" | "calendar" | "pretrend")` 保持显式聚合入口**，语义不变。
5. **wrapper 不声称接受 `aggtype` 参数**。`aggtype` 是 `estat()` 的参数，不是 `csdid()` wrapper 的参数；支持矩阵文档据此修正。
6. 未拟合的核心模型（未调用 `fit()`）访问 `result` / `summary()` / `display()` / `estat("event")` 时抛出清晰的 `ValueError`（"Model has not been fitted."），与其他 `estat_*` 方法的防护一致。

实现上，聚合与协方差逻辑继续保留在现有 `estat_*` 方法中；新增的展示/结果面仅做委托，不复制结果构造逻辑。

## 备选方案

### 方案 A：`csdid()` 直接返回 `ResultSchema`

- 优点：与 `regress` 等命令完全一致
- 缺点：破坏向后兼容（用户当前链式调用 `csdid(...).estat(...)`）；属于主版本变更，本里程碑明确禁止

### 方案 B：仅在 evaluator 侧特判 csdid

- 优点：零包代码改动
- 缺点：把不一致性固化在评估器里，跨命令 UX 契约名存实亡

## 后果

- `CSDID` 模型对象与 `ResultSchema` 一样具备可展示的默认结果面，跨命令 `Coef` 表头检查可对 csdid 生效
- 展示层无重复的结果构造逻辑，`result` 与 `estat("event")` 逐字段一致由测试保证
- evaluator 侧删除两个恒真占位检查，UX 检查数从 20 收敛为 18 个有意义检查

## 受影响文件

- `src/stataflow/estimators/csdid.py`（新增 `result` / `summary()` / `display()`，补 `estat_event` 未拟合防护）
- `src/stataflow/compat/stata/did.py`（docstring 记录结果契约）
- `docs/command-support-matrix/csdid.md`（移除 wrapper 不接受的 `aggtype` 行，补充结果契约说明）
- `docs/architecture/public-api.md`、`docs/USER_GUIDE.md`、`docs/USER_GUIDE.zh-CN.md`（记录契约）
- `tests/test_compat_stata_did.py`、`tests/test_result_schema.py`（契约一致性测试）

## 何时重审

- 若未来主版本决定将 `csdid()` 改为直接返回 `ResultSchema`，本 ADR 由新 ADR 取代
- 若默认聚合从 event 变更为其他类型，需同步更新本契约与测试
