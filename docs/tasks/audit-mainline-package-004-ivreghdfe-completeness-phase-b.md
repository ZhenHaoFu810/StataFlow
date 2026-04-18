# 审计主线任务包 004：`ivreghdfe` 完整度推进（Phase B）

## 任务定位

本轮进入审计主线的下一条命令族：`ivreghdfe`。

目标不是再做一个“能跑的 2SLS + FE 子集”，而是把当前实现从高频子集推进到更接近 `ivreghdfe` 命令本身的完整语义，并且以本地 vendor 源码为约束，而不是单纯围绕测试数值调参。

## 目标

本轮至少完成下面三类工作中的前两类，并尽量推进第三类：

1. **命令面补齐**
   - 复核并补齐当前 wrapper / core 已缺失但属于高频 `ivreghdfe` 使用面的参数或行为。
2. **source-backed 收口**
   - 把 `docs/research/ivreghdfe-source-map.md` 更新成真正可作为审计依据的映射文档。
3. **证据链补强**
   - 为本轮新增或纠正的能力补 synthetic / real-data / source-backed 证据，而不是只补 wrapper delegation 测试。

## 必须使用的依据

- 本地源码镜像：
  - `research/vendor/stata_community/ivreghdfe/`
- 现有研究文档：
  - `docs/research/ivreghdfe-source-map.md`
- 当前支持矩阵：
  - `docs/command-support-matrix/ivreghdfe.md`

## 必须重点审视的内容

### A. 命令语义与参数面

至少检查并明确下列项目当前状态：

- `absorb()`
- `vce(ols|robust|cluster)`
- `cluster()`
- `noconstant`
- `keepsingletons`
- `first-stage` / first-stage evidence 是否缺失
- `predict()` 语义是否完整
- wrapper 是否真的用 Stata 命令名且公共语义正确

### B. 估计与推断过程

至少审视并说明：

- FE 残差化与 IV 两阶段是如何组合的
- robust / cluster VCE 在 `ivreghdfe` 中是否与本地源码逻辑可映射
- DoF / `df_a` / `df_model` / `df_resid` 口径是否和当前 `reghdfe` / `ivregress 2sls` 体系一致

### C. 结果对象与 postestimation

至少明确：

- 当前 `ResultSchema` 里哪些字段已经有 `ivreghdfe` 语义
- 是否支持 `predict(type="xb")`
- 是否需要明确拒绝尚未支持的 predict 子选项

## 最低交付要求

### 1. 代码层

如确有必要，可以修改：

- `src/statapy/estimators/iv.py`
- `src/statapy/compat/stata/iv.py`
- 以及直接相关的结果 / 工具层文件

但禁止：

- 顺手改与 `ivreghdfe` 无关的 factor grammar
- 顺手扩 `reghdfe`、`ppmlhdfe`、DID 命令

### 2. 文档层

必须更新：

- `docs/research/ivreghdfe-source-map.md`
- `docs/command-support-matrix/ivreghdfe.md`

如本轮新增测试样例，也必须同步：

- `docs/testing/test-case-catalog.md`
- `docs/backlog.md`（若完整度状态发生变化）

### 3. 测试层

必须至少补或复核以下证据：

- synthetic:
  - `ivreghdfe` 基础
  - `ivreghdfe` robust
  - `ivreghdfe` cluster
  - 如本轮新增 `predict`，需要对应 synthetic 行为测试
- real-data:
  - 至少保持现有 real panel dual-run 通过
- source-backed:
  - 在 `REPORT.md` 中说明本轮新增能力与 vendor 源码哪一段相对应

## 明确禁止

- 不允许只靠放宽容差让 dual-run 过关
- 不允许只补 wrapper delegation 测试就宣称命令完整度提升
- 不允许在没有源码/手册依据时，为了和现有样例数值一致去硬调实现
- 不允许把“已支持高频子集”写成“已完整实现 `ivreghdfe`”

## 通过标准

Codex 只会在以下条件同时满足时放行：

1. `ivreghdfe` 的本轮目标能力有实际代码或明确的公共接口收口，不只是文档修改。
2. `docs/research/ivreghdfe-source-map.md` 与当前代码一致，不保留过期结论。
3. `docs/command-support-matrix/ivreghdfe.md` 与 wrapper / estimator / 测试一致。
4. 有至少一项新增的 source-backed 证据，而不是仅复用旧测试。
5. 重新跑相关专项测试和全量测试通过。

## 回报格式

完成后在 `workspace/current-task/REPORT.md` 中按下面结构汇报：

1. 本轮新增或修正了哪些 `ivreghdfe` 能力
2. 每项能力对应哪段本地源码依据
3. 哪些仍然缺失，为什么缺失
4. 新增了哪些测试与证据
5. fresh run 结果
6. 你认为本轮后 `ivreghdfe` 的完整度评级：`partial / near-complete / full`，并给出理由
