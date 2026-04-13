# 总体架构

## 1. 架构目标

项目采用分层内核路线。设计目标是让 Stata 对齐逻辑、统计估计逻辑、结果对象和测试验证逻辑相互解耦，避免每扩展一个命令就重新发明一套实现与验收流程。

## 2. 核心分层

### `stata_runner`

职责：

- 调用本机 Stata 17 可执行文件
- 生成临时 `.do`、输入数据与输出文件
- 收集 Stata 执行日志、退出状态与结构化结果

禁止事项：

- 不直接暴露为最终用户的主入口
- 不包含计量估计算法
- 不嵌入结果比较逻辑

### `result_spec`

职责：

- 定义统一结果对象 schema
- 承载 Stata 和 Python 两侧的可比字段
- 作为测试、展示与序列化的共享契约

禁止事项：

- 不负责估计
- 不负责调用 Stata

### `estimators.linear`

职责：

- 实现线性计量估计主干
- 负责 OLS、加权 OLS 子集、robust、cluster、单向 FE 基础
- 将预处理、点估计、协方差估计和输出对象拼装起来

禁止事项：

- 不直接执行 Stata
- 不以内嵌文本方式定义测试金标准

### `testing_harness`

职责：

- 驱动 Stata-Python 双跑
- 执行字段级结果比较
- 输出详细 diff 报告
- 提供 CI 可用的验收入口

禁止事项：

- 不承担业务 API
- 不直接修改估计器逻辑

## 3. 依赖方向

允许的依赖方向如下：

- `estimators.linear -> result_spec`
- `testing_harness -> stata_runner`
- `testing_harness -> result_spec`
- `testing_harness -> estimators.linear`

禁止的依赖方向如下：

- `result_spec -> estimators.linear`
- `result_spec -> stata_runner`
- `stata_runner -> estimators.linear`
- 任意层绕过 `result_spec` 直接比对原始对象

## 4. 横切关注点

以下逻辑必须以独立模块或清晰职责形式存在，不得散落在命令封装中：

- 样本筛选
- 缺失值处理
- 常数项管理
- 共线性识别与变量剔除
- 权重语义
- 聚类索引构造
- FE 残差化

## 5. 扩展位点

为后续阶段预留但 v1 不完全公开的扩展位点：

- 双向 FE 与高维 FE 吸收
- 离散选择模型
- IV / GMM
- DID 封装与事件研究接口

扩展时必须优先复用已有结果 schema、测试框架和样本规则，不允许平行造新体系。
