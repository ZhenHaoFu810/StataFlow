# Workspace 目录

本目录用于承载执行代理的当前工作区说明、任务入口和反馈材料。

## 设计目的

- 给 QwenCode 一个稳定、单一、低歧义的工作入口
- 把“当前该做什么”和“做完后如何回报”集中到一个地方
- 避免每轮都要人工重复转述相同步骤

## 目录约定

- `workspace/qwencode-current/`
  - 当前指派给 QwenCode 的工作区
  - 存放本轮任务指令、回报模板和必要的辅助说明

后续如果并行推进多轮任务，可以扩展为：

- `workspace/qwencode-phase0/`
- `workspace/qwencode-phase1/`
- `workspace/qwencode-experiments/`

但在当前阶段，默认只维护一个 `qwencode-current` 即可。
