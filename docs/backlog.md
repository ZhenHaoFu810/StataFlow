# 全局任务池

## 状态定义

- `planned`：已进入项目范围但未开始
- `ready`：研究与前置条件满足，可进入执行
- `in_progress`：正在实施
- `blocked`：因规则不清、研究不足或依赖缺失暂缓
- `done`：已实现并通过双线验证门禁

## Command Families

| 条目 | 优先级 | 状态 | 依赖 | 说明 |
| --- | --- | --- | --- | --- |
| `Linear Base` | P0 | done | 无 | `regress`、robust、cluster、`aweight`、single FE 原型已完成 |
| `Panel / FE / HDFE` | P1 | ready | Linear Base | 下一主线 |
| `IV / GMM` | P2 | done | Panel / FE / HDFE | `ivregress 2sls`、`ivreghdfe` 已完成 |
| `Binary / Count` | P3 | done | Linear Base | `logit`、`probit`、`poisson`、`ppmlhdfe` |
| `DID / Event Study Extensions` | P4 | done | Panel / FE / HDFE | `did_imputation`、`eventstudyinteract`、`csdid` 已完成 |
| `Postestimation` | P5 | done | 前述命令族稳定 | `predict`、`margins` 子集、输出层已完成 |
| `RD / Local Polynomial` | P5 | done | Linear Base | `rdrobust` minimal subset (Sharp RD) 已完成 |

## High-Value Commands

| 命令或能力 | 命令族 | 优先级 | 状态 | 规则来源 |
| --- | --- | --- | --- | --- |
| `regress` | Linear Base | P0 | done | 官方手册 + 双跑 |
| `vce(robust)` | Linear Base | P0 | done | 官方手册 + 双跑 |
| `vce(cluster)` | Linear Base | P0 | done | 官方手册 + 双跑 |
| `aweight` | Linear Base | P0 | done | 官方手册 + 双跑 |
| `xtreg, fe` | Panel / FE / HDFE | P0 | done | 官方手册 + 双跑 |
| `areg` | Panel / FE / HDFE | P1 | done | 官方手册 + 双跑 |
| 双向 FE 吸收内核 | Panel / FE / HDFE | P1 | planned | 设计文档 + 双跑 |
| `reghdfe` | Panel / FE / HDFE | P1 | done | 公开源码 + 双跑 |
| `ivregress 2sls` | IV / GMM | P2 | done | 官方手册 + 双跑 |
| `ivreghdfe` | IV / GMM | P2 | done | 公开源码 + 双跑 |
| `logit` | Binary / Count | P3 | done | 官方手册 + 双跑 |
| `probit` | Binary / Count | P3 | done | 官方手册 + 双跑 |
| `poisson` | Binary / Count | P3 | done | 官方手册 + 双跑 |
| `ppmlhdfe` | Binary / Count | P3 | done | 公开源码 + 双跑 |
| `did_imputation` | DID / Event Study Extensions | P4 | done | 公开源码 + 双跑 |
| `eventstudyinteract` | DID / Event Study Extensions | P4 | done | 公开源码 + 双跑 |
| `csdid` | DID / Event Study Extensions | P4 | done | 公开源码 + 双跑 |
| `rdrobust` | RD / Local Polynomial | P5 | done | 公开源码 + 双跑 |
| `predict` 高频子集 | Postestimation | P5 | done | 手册 + 双跑 |
| `margins` 高频子集 | Postestimation | P5 | done | 手册 + 双跑 |

## Entry Criteria

任一命令从 `planned` 进入 `ready`，至少需要：

- 已在 `docs/research/` 建立研究档案
- 已明确其来源属于“公开源码”还是“官方手册”
- 已在 `docs/testing/test-case-catalog.md` 预登记 synthetic 与 real-data 样例

任一命令从 `ready` 进入 `done`，至少需要：

- synthetic 黄金样例通过
- 至少一个真实公开数据样例通过
- 全量回归测试通过
- 研究档案与结果语义无冲突
