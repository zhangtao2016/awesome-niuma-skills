---
name: sdd-riper-one
description: Spec 驱动研发框架，以 RIPER 阶段门禁保障 No Spec No Code。覆盖 CodeMap、上下文打包、Spec 生命周期与三轴评审。
---

# SDD-RIPER-ONE Skill

三条底线：`No Spec, No Code` · `No Approval, No Execute` · `Spec is Truth`

## 全局安全底线

- **高危操作阻断**：永远不要静默或提议执行 `git clean`（特别是 `-fdx`），防止未提交数据不可逆丢失。
- **研发纪律**：
  - `No Spec, No Code`：未形成并持久化 Spec 前，不进入代码实现。
  - `No Approval, No Execute`：未收到精确字样 `Plan Approved`，禁止进入 Execute。
  - `Spec is Truth`：聊天决议或改动必须回源到 Spec，Spec 是唯一真相源。
  - `Reverse Sync`：执行中发现 Bug，先更新 Spec 再修代码。

## 核心定位

- 协议全文：`references/sdd-riper-one-protocol.md`
- 总纲：`Pre-Research → RIPER`，全程遵循 SDD 并持续维护 Spec
- `create_codemap` / `build_context_bundle` 是 Pre-Research 输入准备；`sdd_bootstrap` 是 RIPER 启动命令
- RIPER 主流程：`Research → (Innovate, 可选) → Plan → Execute → Review`
- 不要在每轮对话里重载整份 Skill / Spec；默认只回读当前阶段需要的小节
- **Spec 受众分层**：Spec 第一受众是人类（持久化上下文与组织记忆），第二受众是模型。协议对模型的价值：注意力聚焦、信息索引、防止上下文腐烂、辅助 Review。协议不应导致上下文挤爆——RIPER 管流程，Spec 管记录，模型按需取用。

## 推荐流程

| 场景 | 流程 |
|---|---|
| 标准流（中大型任务） | `create_codemap → build_context_bundle → sdd_bootstrap → Research → (Innovate) → Plan → Execute → Review` |
| 快速流（小任务/需求模糊） | `sdd_bootstrap → 按需补 codemap/context → Research → Plan → Execute → Review` |

**门禁**：首版 Spec 落盘前不实现 · `Plan Approved` 前不执行 · Review 不通过回到 Research/Plan

## 上下文装配规则

SDD 是完整持久化上下文层，RIPER 是审批驱动状态机。裁剪目标是减少重复重放，不是削弱门禁。

### 热上下文（每轮必带）

`phase` · `approval status` · `spec path` · `Goal` · `In Scope / Out of Scope` · 活跃 `Checklist` · `Open Questions` · 风险与 `Next Action`

> 热上下文只用于当前轮聚焦，不替代完整 Spec；冲突时以 Spec 为准。

### 温上下文（切阶段时加载）

| 切换方向 | 需加载 |
|---|---|
| Research → Plan | Research Findings、关键事实、方案结论 |
| Plan → Execute | File Changes、Signatures、原子 Checklist |
| Execute → Review | Validation、实际改动摘要、偏差说明 |

### 冷上下文（按需加载）

全量 Change Log · 历史 Research 细节 · 完整 codemap / context bundle · MULTI / DEBUG / ARCHIVE 扩展规则

### 硬门禁（不可因裁剪削弱）

1. `phase` 与 `approval status` 必须是显式状态，不允许推断
2. 冲突、字段缺失、记忆不确定时，立即回读完整 Spec

### 回读触发规则

- **每轮**：phase、approval status、spec path、Goal、活跃 Checklist、Next Action
- **切阶段**：回读目标阶段对应 Spec 区块
- **执行 review**：`review_spec` 回读 Plan；`review_execute` 回读 Plan + Validation + Review
- **全量回读**：阶段切换有争议、摘要与 Spec 冲突、长对话遗忘迹象、高风险改动
- **禁止**：不能用热上下文替代 Spec 原文跨阶段推进

## 原生命令动作

> 详细参数见 `references/commands.md`

### create_codemap

生成代码索引地图（`feature` 功能级 / `project` 项目级）。

- 输入：scope (`feature` | `project`) + 目标路径
- 输出：`mydocs/codemap/YYYY-MM-DD_hh-mm_<name>.md`

### build_context_bundle

整理需求上下文（目录输入 → 全模态需求汇总），支持 Lite/Standard 粒度。

- 输入：需求目录路径
- 输出：`mydocs/context/YYYY-MM-DD_hh-mm_<task>_context_bundle.md`

### sdd_bootstrap

RIPER 启动命令，收口 Pre-Research 并产出首版 Spec。

- 输入：口述 / 文档 / 聊天记录 / context bundle
- 输出：`mydocs/specs/YYYY-MM-DD_hh-mm_<TaskName>.md`

### review_spec

Plan → Execute 前的建议性评审，输出 `GO/NO-GO`（不硬阻塞）。

- 输入：当前 Spec
- 输出：分阶段检查结果 + GO/NO-GO 判定

### review_execute

Execute 后三轴评审：Spec 质量 · Spec-代码一致性 · 代码质量。

- 输入：Spec + 实际改动
- 输出：Review Matrix + Overall Verdict + Plan-Execution Diff

### archive

归档沉淀，生成 `human`（汇报视角）+ `llm`（开发参考视角）双文档。

- 输入：已完成 Review 的 Spec / CodeMap
- 输出：`mydocs/archive/YYYY-MM-DD_hh-mm_<topic>_{human,llm}.md`

### debug

日志驱动排查与功能验证，本身不改代码。

- 输入：`log_path` + (`issue` 排查 | `spec` 验证)
- 输出：根因候选 + 建议修复 / 逐条验收结果

## 多项目协作

> 详细规则见 `references/multi-project.md`

- 触发：`mode=multi_project` 或触发词 `MULTI / 多项目`
- 自动扫描 workdir 识别子项目，产出 Project Registry 确认后继续
- 默认 `change_scope=local`；`CROSS / 跨项目` 显式触发跨项目改动
- 跨项目须记录 Contract Interfaces 与 Touched Projects
- 智能降级：1 个子项目 → 单项目模式；0 个 → workdir 本身作为单项目

## 阶段约束

- 每轮先同步 Spec 再推进阶段
- 默认只回读当前阶段区块；切换阶段、执行 review、发现冲突时全量回读
- `Innovate` 可选：复杂任务建议 2-3 方案；小任务可跳过但写原因
- `Plan` 必须可执行：文件路径 + 签名 + 原子 Checklist
- `Review` 必须三轴评审并回写结论
- 任务闭环后建议执行 `archive`

## Debug 模式

- 触发词：`DEBUG / 排查 / 日志分析 / 验证功能`
- 本身不改代码，仅分析定位；需改代码时走 RIPER 或 FAST
- 分析结论回写 Spec `§ Debug Log`

## 触发词速查

| 触发词 | 动作 |
|---|---|
| `MAP / 链路梳理 / 只看代码` | `create_codemap(feature)` |
| `PROJECT MAP / 项目总图 / MAP ALL` | `create_codemap(project)` |
| `MULTI / 多项目` | 进入多项目模式 |
| `CROSS / 跨项目` | 允许跨项目改动 |
| `FAST / 快速 / >>` | 小改快速通道 |
| `REVIEW SPEC / 计划评审` | 建议性预审 |
| `REVIEW EXECUTE / 代码评审` | 三轴审查 |
| `ARCHIVE / 归档 / 沉淀` | 知识沉淀 |
| `DEBUG / 排查` | 日志驱动诊断 |
| `EXIT SDD / 退出协议` | 退出状态机 |

## 命名规则

统一时间前缀 `YYYY-MM-DD_hh-mm_`，未经用户允许不可省略。

| 产物 | 路径 |
|---|---|
| codemap(feature) | `mydocs/codemap/YYYY-MM-DD_hh-mm_<feature>功能.md` |
| codemap(project) | `mydocs/codemap/YYYY-MM-DD_hh-mm_<project>项目总图.md` |
| context bundle | `mydocs/context/YYYY-MM-DD_hh-mm_<task>_context_bundle.md` |
| spec | `mydocs/specs/YYYY-MM-DD_hh-mm_<TaskName>.md` |
| archive | `mydocs/archive/YYYY-MM-DD_hh-mm_<topic>_{human,llm}.md` |

## Quick Start

**标准流（中大型任务）**：先生成 CodeMap 和上下文包，再启动 RIPER。

```text
请启用 $sdd-riper-one，依次执行：
1. create_codemap scope=feature path=src/auth
2. build_context_bundle dir=requirements/auth
3. sdd_bootstrap task=用户认证重构 goal=迁移到 JWT requirement=mydocs/context/..._context_bundle.md
```

**快速流（小任务）**：直接 bootstrap，按需补充上下文。

```text
请启用 $sdd-riper-one，执行 sdd_bootstrap：
- task=修复登录超时
- goal=登录接口超时从 30s 降到 5s
- requirement=用户反馈登录偶发 30s 无响应
```

## 参考文件

| 文件 | 用途 |
|---|---|
| `references/sdd-riper-one-protocol.md` | 完整协议 |
| `references/spec-template.md` | Spec 模板（单项目 + 多项目） |
| `references/workflow-quickref.md` | 工作流速查卡 |
| `references/usage-examples.md` | 实战示例 |
| `references/commands.md` | 命令详细参数 |
| `references/multi-project.md` | 多项目协作规则 |
| `references/archive-template.md` | 归档模板 |
