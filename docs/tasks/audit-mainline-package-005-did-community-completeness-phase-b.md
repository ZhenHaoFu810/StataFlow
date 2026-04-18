# 审计主线任务包 005：DID 社区命令完整度推进（Phase B）
## 任务定位

`reghdfe`、`ppmlhdfe`、`ivreghdfe` 主线已经推进到可验证的 Phase B 子集。下一条主线进入 DID 社区命令族：

- `did_imputation`
- `eventstudyinteract`
- `csdid`

本轮目标不是“再补几个 wrapper 测试”，而是把这三个命令从“高频核心路径可跑”推进到“命令语义、源码依据、真实数据证据、公开支持矩阵更接近可发布状态”的 Phase B。

## 目标

本轮至少完成下面四类工作中的前三类：

1. **命令面补齐**
   - 复核并补齐当前 wrapper / core 已缺失但属于高频 DID 使用面的参数、边界与错误语义。
2. **source-backed 收口**
   - 把 `did_imputation`、`eventstudyinteract` 的 source map 收口成真正可审计文档。
   - 明确 `csdid` 的当前边界，不允许继续模糊描述。
3. **真实数据与数学证据增强**
   - 不是只重复旧样例，而是补更有说服力的 real-data / edge-case 证据。
4. **支持矩阵与 README 对齐**
   - 让 DID 命令的 support matrix 与 wrapper、core estimator、测试状态完全一致。

## 必须使用的依据

- 本地源码镜像：
  - `research/vendor/stata_community/did_imputation/`
  - `research/vendor/stata_community/eventstudyinteract/`
- 现有研究文档：
  - `docs/research/did_imputation.md`
  - `docs/research/eventstudyinteract.md`
  - `docs/research/csdid.md`
- 现有测试与公开数据：
  - `tests/golden/test_w4_*`
  - `research/data/public/`
- 审查协议：
  - `docs/operations/codex-review-protocol.md`

## 必须重点审视的内容

### A. 命令语义与参数面

至少检查并明确当前以下内容的状态：

- `did_imputation`
  - `allhorizons`
  - `autosample`
  - `window`
  - `pretrend`
  - `minn`
- `eventstudyinteract`
  - 自动 event-dummy 生成
  - cohort / control group 语义
  - cluster 语义
- `csdid`
  - 当前只支持 `method="reg"` 的边界
  - `estat_event()` 输出口径
  - 对未支持 method 的显式拒绝

### B. 数学过程与推断

至少说明：

- 各命令的估计目标与聚合过程是否能由源码或手册支持
- 标准误、聚合标准误、事件时间系数的生成与当前实现如何对应
- 是否存在“通过宽容差”掩盖实现差异的旧问题；若存在，必须修掉，不允许继续留在本轮

### C. 结果对象与公开接口

至少说明：

- wrapper 返回对象和 core estimator 的职责边界
- 哪些 postestimation 语义已经支持，哪些没有
- 文档不能把“core 支持”误写成“wrapper 支持”

## 最低交付要求

### 1. 代码层

如确有必要，可以修改：

- `src/statapy/estimators/did_imputation.py`
- `src/statapy/estimators/eventstudyinteract.py`
- `src/statapy/estimators/csdid.py`
- `src/statapy/compat/stata/did.py`
- 与上述直接相关的结果或工具层文件

但禁止：

- 顺手改与 DID 主线无关的 factor grammar
- 顺手修改 HDFE / IV / GLM 主线代码

### 2. 文档层

必须更新：

- `docs/research/did_imputation-source-map.md`
- `docs/research/eventstudyinteract-source-map.md`
- `docs/command-support-matrix/did_imputation.md`
- `docs/command-support-matrix/eventstudyinteract.md`
- `docs/command-support-matrix/csdid.md`

如本轮新增长样例，也必须同步：

- `docs/testing/test-case-catalog.md`
- `docs/backlog.md`（若完整度状态发生变化）

### 3. 测试层

必须至少补或复核以下证据：

- synthetic:
  - 三个 DID 命令至少各有一项非平凡 synthetic 或 edge-case 行为测试
- real-data:
  - 保持现有 `ezunem` 等真实数据 dual-run 通过
  - 至少新增一类更灵活的 real-data 或 edge-case 验证
- source-backed:
  - 在 `REPORT.md` 里明确说明每个命令本轮新增能力对应哪段本地源码或哪条手册依据

## 明确禁止

- 不允许只靠放宽 real-data 容差就宣称 DID 命令完整度提升
- 不允许只做 wrapper delegation 测试就说“命令更完整”
- 不允许把 `csdid(method=\"reg\")` 的单一路径写成“已完整实现 csdid”
- 不允许在没有源码/手册依据时为了通过测试去调数值

## 通过标准

Codex 只会在以下条件同时满足时放行：

1. 三个 DID 命令中，本轮目标能力有实际代码、接口或显式边界收口，而不是只改文档。
2. `did_imputation-source-map.md`、`eventstudyinteract-source-map.md` 与当前实现一致。
3. `csdid` 的支持矩阵与 wrapper / estimator / 测试一致，边界说法清楚。
4. 有至少一项新增的 source-backed 证据，而不是只复用旧 Wave 4 结果。
5. 相关专项测试和全量测试通过。

## 已知延后项（不阻塞本轮）

- `ivreghdfe` Phase B 的 `REPORT.md` fresh-run 证据仍有旧数字残留。
- 该问题已登记在：
  - `workspace/current-task/review-audit-mainline-package-004-final-codex.md`
  - `docs/tasks/audit-mainline-package-004-rework-report-evidence.md`
- 本轮不要求处理该问题，也不要顺手再改 `ivreghdfe` 主线。

## 回报格式

完成后在 `workspace/current-task/REPORT.md` 中按下面结构汇报：

1. 本轮新增或修正了哪些 DID 命令能力
2. 每项能力对应哪些源码或手册依据
3. 哪些仍然缺失，为什么缺失
4. 新增了哪些 synthetic / real-data / source-backed 证据
5. fresh run 结果
6. 你认为 `did_imputation`、`eventstudyinteract`、`csdid` 各自当前应评为 `partial / near-complete / full`，并给出理由
