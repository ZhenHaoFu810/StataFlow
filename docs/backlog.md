# 全局任务池

## 状态定义

- `planned`：已进入项目范围但未开始
- `ready`：前置条件满足，可进入执行手册
- `in_progress`：正在实施
- `blocked`：因规则不清或依赖缺失暂缓
- `done`：已实现并通过门禁

## Backlog

| 能力 | 优先级 | 状态 | 依赖 | 验收文档 |
| --- | --- | --- | --- | --- |
| 项目骨架与包结构 | P0 | done | 无 | `docs/phases/phase-0-bootstrap.md` |
| Stata runner 最小链路 | P0 | done | 项目骨架 | `docs/phases/phase-0-bootstrap.md` |
| 结果 schema 与序列化 | P0 | done | 项目骨架 | `docs/architecture/result-schema.md` |
| 首个 OLS 双跑样例 | P0 | done | runner, schema | `docs/phases/phase-0-bootstrap.md` |
| OLS | P1 | done | Phase 0 | `docs/phases/phase-1-linear-core.md` |
| `vce(robust)` | P1 | planned | OLS | `docs/phases/phase-1-linear-core.md` |
| `vce(cluster)` 单聚类 | P1 | planned | OLS | `docs/phases/phase-1-linear-core.md` |
| 样本筛选与缺失值规则 | P1 | done | OLS | `docs/phases/phase-1-linear-core.md` |
| 常数项与共线性处理 | P1 | done | OLS | `docs/phases/phase-1-linear-core.md` |
| `aweight` | P2 | planned | Phase 1 | `docs/phases/phase-2-weights-fe.md` |
| 单向 FE | P2 | planned | Phase 1 | `docs/phases/phase-2-weights-fe.md` |
| `areg` 内部吸收基础 | P3 | planned | Phase 2 | 后续文档待补 |
| 双向 FE | P3 | planned | 吸收基础 | 后续文档待补 |
| `logit` | P4 | planned | 线性内核稳定 | 后续文档待补 |
| `probit` | P4 | planned | 线性内核稳定 | 后续文档待补 |
| `poisson` | P4 | planned | 线性内核稳定 | 后续文档待补 |
| IV / GMM | P5 | planned | 线性与测试体系稳定 | 后续文档待补 |

## Backlog 更新规则

- 新命令进入开发前，必须先在本表登记
- 未登记条目不得进入实现
- `done` 状态必须附带可追踪的测试与验收证据
- 若能力边界变化，应先写 ADR 再更新本表
