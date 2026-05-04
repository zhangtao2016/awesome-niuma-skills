---
name: sdd-riper-one-light
description: 轻量 checkpoint-driven coding skill，只常驻最小 spec + 关键锚点，其余按需加载，适用于强模型高频多轮场景。
---

# SDD-RIPER-ONE Light

## 核心定位

- `checkpoint-driven`，非 `phase-heavy`；主协议只保留高杠杆锚点，其余按需查 reference。
- 假设强模型自行分解任务、补足计划、按需追溯上下文；协议目标是减少低价值常驻 token，而非减少控制力。
- **Spec 受众分层**：Spec 第一受众是人类（持久化上下文与组织记忆），第二受众是模型。协议对模型的价值：注意力聚焦、信息索引（按路径回读而非全量常驻）、防上下文腐烂、辅助 Review。RIPER 管流程，Spec 管记录，模型按需取用。

## 硬约束

| # | 约束 | 含义 |
|---|------|------|
| 1 | **Spec is Truth** | spec 是持久化上下文、压缩记忆与协作真相源 |
| 2 | **No Spec, No Code** | 未形成或更新最小 spec 前不写代码 |
| 3 | **No Approval, No Execute** | 未得到明确许可不进入实现或高影响变更 |
| 4 | **Restate First** | 先用自己的话复述理解，再进 spec 或计划 |
| 5 | **Core Goal as Loop Anchor** | 执行前、偏差后、验证时必须重新对齐阶段性核心目标 |
| 6 | **Checkpoint Before Execute** | 实现前给一次短 checkpoint（理解/目标/下一步/风险/验证） |
| 7 | **Done by Evidence** | 完成由验证结果与外部反馈证明，非模型自行宣布 |
| 8 | **Reverse Sync** | 执行后把结果、偏差、验证结论回写 spec |
| 9 | **Resume Ready** | 长任务或暂停前在 spec 中留最小恢复锚点 |

## 任务深度

### `zero`（零 Spec）
纯机械性改动（typo、日志、配置值等无决策单点修改）。
跳过 micro-spec，直接执行，完成后一句话 summary 回写。
复杂度超预期时立即升级。

### `fast`
先写 micro-spec（1-3 句：目标、文件、风险、验证），不裸改。
用户批准后执行；复杂度上升时升级。

### `standard`（默认）
适用于 2+ 文件改动、一般功能开发、缺陷修复。
维护轻量 spec 并落盘；执行前 checkpoint，获批后实施并回写。

### `deep`
需求模糊、架构改动、未知根因、跨模块/跨项目场景。
允许方案比较与风险说明，但保持精简。
深思考结果先写回 spec 待审阅，获批后实现。按需加载 `references/modules.md`。

## 最小工作流

1. **复述对齐** — 用自己的话复述用户任务，确认核心目标一致。
2. **Spec 落盘** — 用最小 spec 固化目标、边界、事实、计划，尽快持久化。
3. **Done Contract** — 在 spec 中用 1-3 行写清：什么算完成、由什么证明、哪些算未完成。
4. **Checkpoint** — 给出：当前理解 / 核心目标 / 下一步 1-3 动作 / 风险 / 验证方式。
5. **获批执行** — 用户批准后执行；范围或方案变化时先更新 spec 再重新请求批准。
6. **偏差处理** — 若测试/日志/反馈暴露偏差，先基于证据重述核心目标是否变化，再决定继续或调整。
7. **回写收尾** — 回写 Change Log / Validation / Resume or Handoff，说明核心目标是否已由证据证明完成。

## 何时暂停

遇到以下情况，先暂停并说明原因：

- 需求存在会改变实现方向的关键歧义。
- 需要破坏性、高风险、不可逆操作。
- 涉及架构级改动、公共接口变更、数据模型变更、迁移策略变更。
- 涉及跨项目修改，而用户未明确允许或范围未清楚。
- 发现现有 spec 明显错误、过期或与代码现实冲突。
- 尚未形成最小 spec 或尚未得到明确执行许可。

## 按需模块

- `references/spec-lite-template.md`：最小 spec 模板。
- `references/modules.md`：`Deep Planning` / `Debug` / `Review` / `Multi-project`。
- `references/conventions.md`：落盘目录、命名规则、`micro-spec` 与正式 spec 的分流规则。

## 输出风格

- 默认中文。
- 默认短输出，不复述完整协议。
- 优先给“当前理解 + 核心目标 + spec 摘要 + 下一步 + 必要风险”。
- 不强制打印阶段状态机。
- 核心目标采用“事件触发式复述”：阶段开始、执行前 checkpoint、偏差暴露后、阶段收尾时必须重对齐；其他轮次不机械复读。
- 需要长链路推进时，优先给最小 `Done Contract` 与 `Resume/Handoff`，而不是扩写长计划。
- 小任务用 `micro-spec + micro-summary`；复杂任务再按需展开。
