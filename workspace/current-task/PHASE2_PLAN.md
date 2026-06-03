# Phase 2: 真实数据双跑验证计划

## 目标
对 Phase 1 发现的 90 项问题进行真实数据复现验证，同时通过全面参数组合扫描发现更多潜在 bug。

## 方法
每个命令族使用真实公开数据集：
1. Python 端：调用 `stataflow.compat.stata` 对应命令
2. Stata 端：生成 `.do` 文件，用 `StataMP-64.exe /e do` 执行
3. 字段级比较：coefficients, SE, t/z, p, R2, RMSE, F, df, N
4. 偏差记录：rtol > 1e-6 或任何异常/崩溃

## 数据集映射

| 命令族 | 数据集 | 路径 | 适用命令 |
|--------|--------|------|----------|
| DID | ezunem_prepared.dta | `research/data/public/did/` | csdid, did_imputation |
| IV | card.csv | `research/data/public/iv/` | ivregress_2sls |
| GLM | mroz.csv, crime1.csv | `research/data/public/binary/`, `research/data/public/count/` | logit, probit, poisson |
| Panel | grunfeld.csv | `research/data/public/panel/` | reghdfe, areg, xtreg_fe |
| RD | rdrobust_senate_with_z.dta | `research/data/public/` | rdrobust, rdplot |
| Linear | card.csv | `research/data/public/iv/` | regress |

## Stata 执行
- 可执行文件: `D:\Software\Stata17\StataMP-64.exe`
- 命令: `cmd /c "cd /d <dir> && StataMP-64.exe /e do <file>.do"`
- 输出: `.log` 文件与 `.do` 同目录

## 输出要求
每个 Agent 输出：
1. `docs/audit/revalidation-v1.1/phase2-evidence/VAL-<family>.md` — 验证报告
2. `docs/audit/revalidation-v1.1/phase2-evidence/NEW-<family>.md` — 新发现问题（如有）
3. `stata/output/phase2/*.do` 和 `*.log` — Stata 执行产物

## 验证优先级
1. **P0** — 复现 Phase 1 Blocker/Critical（预期会崩溃或偏差）
2. **P1** — 常用参数组合全面扫描（ols/robust/cluster, weights, noconstant 等）
3. **P2** — 边缘case（缺失值、共线、小样本、大FE levels）
