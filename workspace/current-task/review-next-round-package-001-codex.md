# Codex Review: 下一轮任务包 001

## 结论

不通过，不能下放任务包 002。

## 阻塞点

### 1. `reghdfe()` wrapper 的公开命令语义仍然错误

当前：

- `from statapy.compat.stata import reghdfe`
- 当 `absorb` 传入单个变量字符串时，返回结果对象里的 `res.model.command` 仍然是 `areg`

这说明 wrapper 只是把参数转发给了 `AbsorbingOLS`，并没有真正把对外语义收口到 `reghdfe`。

这不是展示层问题，而是公共 API 语义问题。  
如果用户调用的是 `reghdfe()`，结果对象、支持矩阵和文档都不应该再暴露成 `areg`。

### 2. 支持矩阵中的证据路径存在虚构或失真

当前至少发现：

- `docs/command-support-matrix/reghdfe.md` 引用了不存在的：
  - `tests/golden/test_p4_reghdfe_basic.py`
  - `tests/golden/test_p4_reghdfe_real_gravity.py`
- `docs/command-support-matrix/ppmlhdfe.md` 引用了不存在的：
  - `tests/golden/test_p8_ppmlhdfe_basic.py`
  - `tests/golden/test_p8_ppmlhdfe_real_gravity.py`
- `docs/command-support-matrix/csdid.md` 引用了不存在的：
  - `tests/golden/test_p9_csdid_basic.py`
  - `tests/golden/test_p9_csdid_real.py`
  - `research/vendor/stata_community/csdid/`

这意味着当前支持矩阵不是可靠证据清单，存在“写上去了但仓库里并没有”的情况。

对下一轮开源初版来说，这类文档不只是瑕疵，而是阻塞项，因为它会直接误导后续实现与对外说明。

### 3. 报告夸大了“无 core / wrapper 语义冲突”

`REPORT.md` 明确写到：

- “未发现数学语义冲突”
- “无 core / wrapper 语义冲突”

但实际上 `reghdfe()` 返回 `areg` 命令标签这一点本身就是公开语义冲突。  
因此当前报告不能作为该任务包完成的可信证据。

## 建议返工范围

只做以下收口，不要提前进入任务包 002：

1. 修正 `reghdfe()` wrapper 的公共结果语义
   - 确保调用 `reghdfe()` 时，结果对象中的命令标签、元数据、支持矩阵说法一致
   - 不能因为内部复用 `AbsorbingOLS` 就对外泄露成 `areg`

2. 全面核查 13 份支持矩阵
   - 所有测试路径必须是真实存在的仓库路径
   - 所有本地源码镜像路径必须真实存在
   - 不允许引用不存在的 case id 或目录

3. 重写 `REPORT.md` 中的结论段
   - 不得再声称“无语义冲突”
   - 必须按修复后的实际状态回报

## 重新验收前的最低要求

- wrapper 专项测试 fresh run 通过
- 全量测试 fresh run 通过
- `reghdfe()` 公共语义 spot check 通过
- 支持矩阵抽查不再出现虚构路径
