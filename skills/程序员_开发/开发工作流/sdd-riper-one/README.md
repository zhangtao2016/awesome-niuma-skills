# SDD-RIPER-ONE

> Spec 驱动研发框架，让 AI Agent 在严格阶段门禁下工作。

## 一句话定位

用 `No Spec, No Code` + `Plan Approved` 双门禁，把 AI 编码纳入可审计的研发流程。

## 核心价值

- ✅ **防止裸改**：每次改动前必有 Spec，每次执行前必有审批
- 🗺️ **CodeMap 索引**：把大仓库压缩为可按需加载的上下文切片
- 🔄 **三轴评审**：Spec 质量 × Spec-代码一致性 × 代码自身质量
- 📦 **知识归档**：human/llm 双视角归档，任务结束即沉淀

## 快速上手（3步）

**第 1 步：生成 CodeMap（可选，中大型任务推荐）**
```
create_codemap: scope=功能名或项目名
```

**第 2 步：启动 RIPER**
```
sdd_bootstrap: task=任务名, goal=目标描述, requirement=需求描述或文档路径
```

**第 3 步：按阶段推进，遇到 Plan 后回复**
```
Plan Approved
```
（精确字样，不可省略）

## 常用命令

| 命令 | 用途 |
|------|------|
| `create_codemap` | 生成功能级或项目级代码索引 |
| `build_context_bundle` | 整理需求文档为可研究上下文 |
| `sdd_bootstrap` | 启动 RIPER，产出第一版 Spec |
| `review_spec` | Execute 前建议性预审（不强制阻塞）|
| `review_execute` | Execute 后三轴质量评审 |
| `archive` | 归档 Spec/CodeMap，沉淀知识 |

## 适用场景

- 中大型功能开发（2+ 文件改动）
- 架构级改动、接口变更
- 多项目协作（自动发现子项目）
- 需要完整审计链的研发任务

## 流程总览

```
create_codemap → build_context_bundle → sdd_bootstrap
→ Research → [Innovate] → Plan → [Plan Approved] → Execute → Review → archive
```

## 安装

```bash
your-skill-host install /path/to/sdd-riper-one
```

---

> 真正该先记住的不是命令名，而是三句话：
> **No Spec, No Code · No Approval, No Execute · Spec is Truth**
