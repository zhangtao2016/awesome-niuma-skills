# SDD-RIPER-ONE Light

> 面向强模型的轻量 checkpoint-driven 编码工作流。

## 一句话定位

保留 spec、checkpoint、审批三类硬门禁，其余让强模型自行处理——少废话，强控制。

## 与标准版的区别

| | sdd-riper-one | sdd-riper-one-light |
|---|---|---|
| 流程 | 完整 RIPER 阶段门禁 | checkpoint-driven，按需展开 |
| 适用模型 | 各类模型 | 强模型（Claude Opus/GPT-5+）|
| 常驻上下文 | 热/温/冷三层 | 最小 spec + 核心目标锚点 |
| 适用场景 | 中大型团队任务 | 高频多轮、大上下文任务 |

## 核心约束（8条，必须遵守）

1. **Spec is Truth** — spec 是唯一真相源
2. **No Spec, No Code** — 没有最小 spec 不写代码
3. **No Approval, No Execute** — 没有明确批准不执行
4. **Restate First** — 先用自己的话复述理解
5. **Core Goal as Loop Anchor** — 阶段性核心目标是当前 loop 锚点
6. **Checkpoint Before Execute** — 执行前必给一次短 checkpoint
7. **Done by Evidence** — 完成由验证结果证明，不由模型自行宣布
8. **Reverse Sync** — 执行后必须回写 spec

## 快速上手

给 agent 任务时，用这个模板：

```
请使用 sdd-riper-one-light 先收敛任务，不要直接改代码。
先给我：
- 你对任务的理解
- 本轮阶段性核心目标
- micro-spec / summary
- Done Contract（什么算完成、由什么证明）
- 下一步动作 + 风险
我批准后再执行。
```

## 任务深度选择

| 深度 | 适用场景 | Spec 要求 |
|------|---------|-----------|
| `zero` | typo、配置值等纯机械改动 | 跳过，完成后一句话 summary |
| `fast` | 单文件小改动 | micro-spec（1-3 句）|
| `standard` | 2+ 文件、一般功能开发 | 轻量 spec，落盘 |
| `deep` | 架构/跨模块/需求模糊 | 完整分析写回 spec，获批后执行 |

## 按需模块

- `references/spec-lite-template.md` — 最小 spec 模板
- `references/modules.md` — Deep Planning / Debug / Review / Multi-project
- `references/conventions.md` — 落盘目录与命名规则

## 安装

```bash
your-skill-host install /path/to/sdd-riper-one-light
```
