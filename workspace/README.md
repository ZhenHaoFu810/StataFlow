# Workspace 目录

本目录用于承载执行代理的当前工作区说明、任务入口和反馈材料。

## 当前约定

- `workspace/current-task/`
  - 中性执行入口
  - 供 Claude Code 或后续其他执行代理使用
- `workspace/qwencode-current/`
  - 历史工作区
  - 仅保留既有回报与 review 记录，不再作为默认入口

## 设计目的

- 给执行代理一个稳定、单一、低歧义的工作入口
- 集中保存当前任务指令、回报模板和辅助说明
- 把旧的 QwenCode 时代材料与新的中性入口分开
