# 首次开源可用性质检报告

**日期：** 2026-04-19  
**审查角色：** Codex  
**审查目标：** 不新增功能，只评估当前仓库作为“第一次对外开源的第三方库”是否已经达到可发布状态。

---

## 1. 审查范围

本次质检覆盖四类内容：

1. **数值与测试基线**
2. **示例与基本可用性**
3. **对外文档与公共 API 语义**
4. **开源发布要件（元数据、许可证、仓库整洁度、发布面一致性）**

本次不重新审裁“是否完整复现全部 Stata 社区命令”，而是从**首次开源发布的质量门槛**出发评估当前版本是否适合公开给外部用户使用。

---

## 2. 实际执行的检查

### 2.1 测试基线

执行：

```powershell
python -m pytest tests -v
```

结果：

- `687 passed`
- `0 failed`
- `2 warnings`

结论：

- 当前测试基线是**强且稳定**的。
- 核心估计器、wrapper、golden dual-run、postestimation、factor-variable、RD、DID 路径都能通过。

### 2.2 示例脚本可运行性

执行：

```powershell
python examples/demo_regress.py
python examples/demo_reghdfe.py
python examples/demo_ppmlhdfe.py
python examples/demo_ivregress_2sls.py
```

结果：

- 四个 demo 均成功运行。
- 输出格式可读，适合作为 README / examples 入口示例。

结论：

- 当前仓库至少已经具备**最小的“拿来就跑”体验**。

### 2.3 构建能力

执行：

```powershell
python -m pip wheel . --no-deps -w .codex_tmp_dist
```

结果：

- wheel 成功构建：`statapy-0.1.0-py3-none-any.whl`

结论：

- 当前仓库**可以被打包**，不是“只能在源码目录里跑”的原型。

---

## 3. 总体结论

### 3.1 可以肯定的部分

当前项目已经满足以下条件：

- 是一个**高质量、强验证**的 Alpha 版本；
- 主要命令族都有 synthetic + real-data 的实证验证链路；
- `compat.stata` 命令层已经建立，不再只是底层 estimator 集合；
- 文档体系、source map、support matrix、已知问题登记都比较完整；
- wheel 能构建，examples 能跑，full test suite 稳定。

### 3.2 不能直接下“可放心首次开源发布”结论的原因

虽然算法和测试面已经很强，但从**第一次公开开源发布**的标准看，当前仓库仍有几项明显短板：

1. **缺少 LICENSE 文件**
2. **打包元数据不完整且部分信息不一致**
3. **对外文档中仍有错误的外部链接**
4. **仓库根目录仍混有内部脚本、调试脚本和日志文件**
5. **没有 CI/CD 工作流**

因此，本次最终判断是：

> **当前仓库在“算法正确性 + 本地可运行性”上已经达到高质量 Alpha 水平，但在“首次正式对外开源”的发布面上还没有完全收口。**

换句话说：

- **作为内部 Alpha / 研究型公开仓库：可以**
- **作为对外认真宣传、鼓励陌生用户直接安装使用的首次开源版本：还差最后一轮发布面修缮**

---

## 4. 主要发现

### 4.1 Release-blocking

#### A. 缺少 LICENSE 文件

仓库根目录没有 `LICENSE` / `COPYING` / `NOTICE` 文件。

影响：

- 这会让外部用户和贡献者无法明确知道代码的使用、分发和修改权限。
- 对“开源”来说，这是最直接、最基础的阻塞点。

判断：

- **Release-blocking**

#### B. 打包元数据不完整且存在不一致

`pyproject.toml` 当前只有最小字段：

- `name`
- `version`
- `description`
- `requires-python`
- `dependencies`

但缺少：

- `readme`
- `license`
- `authors` / `maintainers`
- `keywords`
- `classifiers`
- `urls`

同时还存在明显不一致：

- [README.md](/D:/OneDrive%20-%20SAIF/PhD3/Stata2Python/README.md:34) 写的是 `Python 3.9+`
- [pyproject.toml](/D:/OneDrive%20-%20SAIF/PhD3/Stata2Python/pyproject.toml:9) 实际要求是 `>=3.10`

影响：

- 用户会误判兼容环境；
- PyPI / wheel 元数据不完整，不利于首次公开发布；
- 版本描述显得更像内部研究仓库而不是可消费的包。

判断：

- **Release-blocking**

#### C. 对外 release 文档中有错误 issue 链接

[docs/release/open-source-alpha-status.md](/D:/OneDrive%20-%20SAIF/PhD3/Stata2Python/docs/release/open-source-alpha-status.md:90) 当前把反馈 issue 链接指向了 `anthropics/claude-code`。

影响：

- 外部用户会被导向错误仓库；
- 会直接损害首次开源时的可信度和基本可用性。

判断：

- **Release-blocking**

### 4.2 High priority

#### D. 仓库根目录噪音文件过多

根目录当前仍存在多种明显不应作为首次开源首页暴露的文件：

- `rdrobust_bwselect.log`
- `rdrobust_gen_z.log`
- `run_did_realdata_stata.py`
- `run_wagepan2.py`
- `run_wagepan3.py`
- `run_wagepan_check.py`
- `test_ezunem_didimp.py`
- `test_jtrain_didimp.py`
- `test_runner_simple.py`
- `find_mpdta.py`

影响：

- 外部用户会难以区分：
  - 正式 examples
  - 临时调试脚本
  - 一次性研究脚本
  - 内部辅助脚本
- 首次开源观感会明显下降。

判断：

- **High priority**

#### E. 没有 CI/CD 工作流

仓库中没有 `.github/workflows/`。

影响：

- 外部贡献者无法看到自动测试状态；
- 首次开源缺少最基础的“可验证持续稳定”信号。

判断：

- **High priority**

### 4.3 Medium priority

#### F. 顶层包文案仍保留原型期痕迹

[src/statapy/__init__.py](/D:/OneDrive%20-%20SAIF/PhD3/Stata2Python/src/statapy/__init__.py:1) 仍写着：

- `# Stata2Python - Phase 0 Bootstrap`

影响：

- 会向外部读者传达“项目仍是 bootstrap 原型”的错误信号；
- 与当前已经扩展到 HDFE / IV / DID / RD 的状态不一致。

判断：

- **Medium priority**

#### G. 发布与治理文档仍有历史遗留漂移

虽然 release-facing 文档总体已经收口，但内部 `workspace/current-task/REPORT.md` 仍存在多轮历史 stale fresh-run 数字的尾迹。

影响：

- 这不是外部用户的第一阻塞点；
- 但会影响项目内部证据链的长期可信度。

判断：

- **Medium priority**

---

## 5. 首次开源发布判定

### 现在能不能开源？

**可以公开仓库，但不建议在当前状态下把它作为“正式可安装、可消费的首次开源版本”对外宣布。**

### 为什么？

因为当前问题不在算法主线，而在**发布面与仓库卫生**：

- 缺许可证
- 元数据不完整
- README / release 文档里还有错误外链
- 根目录过于杂乱

这些问题都不是“以后再说”的小问题，而是首次开源时用户第一眼就会碰到的问题。

### 还差多少？

不多。  
从当前状态到“可以认真对外发第一版 Alpha”之间，主要是**一轮仓库收口和发布面修缮**，而不是再花很多轮改算法。

