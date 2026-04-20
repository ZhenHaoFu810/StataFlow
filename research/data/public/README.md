# Public Dataset Mirror

本目录用于保存后续真实数据双跑验证所需的公开数据集。

## 当前已下载

- `finance/fama_french/`
  - Fama-French 3 factors
  - Fama-French 5 factors (2x3)
- `panel/wooldridge/`
  - `wagepan.csv`
- `panel/`
  - `grunfeld.csv`

## 目录目的

- 为真实数据回归测试提供固定输入
- 避免每次验证时重复联网下载
- 给后续 Stata 脚本和 Python 脚本一个稳定数据路径

## 使用原则

- 不直接修改原始下载文件
- 若需要清洗，另建衍生文件或脚本
- 后续每个数据集都应在 `docs/research/public-datasets.md` 中登记
