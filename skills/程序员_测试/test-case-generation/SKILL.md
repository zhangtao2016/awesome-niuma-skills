---
name: test-case-generation
description: 【入口/路由】测试分析与用例生成（单技能包）。先判定产品，需求目录为「工作区/产品名/需求号-需求简述」（简述≤10字），内含需求号-简述.md 与测试分析/用例产物；需求输入二选一：需求号经 MCP get_story_info 落盘，或直接使用本地需求文件。内容与格式分离，脚本在 scripts/；分模块说明见本包 modules/。
---
# 测试分析与用例生成（入口）

## 概述

- **分工**：AI/用户维护 `test_analysis_content.json`、`test_cases_content.json`；脚本生成 XMind、分析 JSON、Markdown、Blade 用例 JSON，并可上传。
- **产品维度**：`--product <产品名>` 从工作区 **`public/`** 下加载 `pre_docs/<产品>/`、`post_docs/<产品>/` 清单与参考（可用 `config.json` 中 `pre_docs_dir` / `post_docs_dir` 改为绝对路径）；**`public/config.json`** 中 `default` 与各产品键合并。
- **模板**：内容 JSON 样板在 **`public/templates/`**（与 `pre_docs`、`post_docs`、配置文件同属工作区可编辑资产）。
- **脚本根目录**：与本入口同包的 [`scripts/`](scripts/)（如 `generate_from_requirement.py`）。
- **需求目录**：**先判定产品**后，路径为 **`<workspace>/<Product>/<需求号>-<需求简述>/`**（**简述 ≤10 字**，`<Product>` 与 `--product`、`pre_docs/<产品>/` 一致，见 [modules/路径与编码约定.md](modules/路径与编码约定.md)）。其内含 **`需求号-简述.md`**（与需求子目录 stem 一致）、`test_analysis_content.json`、`test_cases_content.json` 及生成的 XMind/MD/JSON；`--output-dir` 与该需求目录一致。
- **凭据字段（须在对应环节显式配置/传入）**：
  - **`devops_access_key`**：调用 MCP **`user-hundsun`**（如 `get_story_info`）时，在工具 `arguments` 中按 schema 传入，与 DevOps 环境一致；详见 [modules/根据需求生成测试分析.md](modules/根据需求生成测试分析.md)（路径 A）。
  - **`blade_api_token`**：Blade 离线导入用令牌（文档统称）；在 **`public/config.json`** 中对应 **`api_token`** 或别名 **`blade_api_token`**；详见 [modules/Blade上传测试分析与用例.md](modules/Blade上传测试分析与用例.md)。

## 需求输入（二选一）

两条路径**等价作为起点**，任选其一得到「本地需求文档」后，再进入测试分析 / 用例生成流程。

| 路径 | 适用场景 | 做法 |
|------|----------|------|
| **A. 需求号** | 用户只给需求号（`story_num`） | **先判定 `<Product>`**（MCP 返回、用户指定或与上下文一致）→ 根据 MCP 返回拟定 **≤10 字需求简述** → 建目录 **`<workspace>/<Product>/<需求号>-<简述>/`** → 调用 **`get_story_info`**（`arguments` 须含 **`devops_access_key`** 等）→ 将 Markdown 写入 **`需求号-简述.md`**（与需求子目录 stem 一致）→ **`--output-dir`** 指向该目录。详见 [modules/根据需求生成测试分析.md](modules/根据需求生成测试分析.md)（路径 A）。**禁止**未调接口就按需求号编造正文。 |
| **B. 直接需求** | 用户已提供需求文档或路径 | 建议落在 **`<workspace>/<Product>/<需求号>-<简述>/需求号-简述.md`**（先定 `<Product>`，简述 ≤10 字），**`--output-dir`** 指向该需求文件夹。无需 MCP。 |

## 端到端流程（简图）

1. 统一前提：**本地需求文件**（路径 A 经 MCP 落盘，或路径 B 已有文件）→ 测试分析内容 → **分析自查** → 导出 XMind/分析 JSON  
2. 测试分析 → 测试用例内容 → **用例自查** → 导出 MD/用例 JSON  
3. 可选：`--upload` 先传用例再传分析（需在 **`public/config.json`** 配置 **`api_token` / `blade_api_token`** 等，见 Blade 模块）

**中间产物清理**：仅当 `--upload` 且上传成功时，删除**该需求目录**内的 `test_analysis_content.json`、`test_cases_content.json`。

## 模块文档（本技能包 `modules/`）

以下均在 **[test-case-generation](.)** 内，按步骤查阅：

| 顺序 | 模块 | 说明 |
|------|------|------|
| 共用 | [路径与编码约定.md](modules/路径与编码约定.md) | **每需求独立目录**、绝对路径、英文目录、PowerShell `;`、控制台编码等 |
| 1 | [根据需求生成测试分析.md](modules/根据需求生成测试分析.md) | 路径 A（MCP 落盘）与路径 B（本地文件）；`test_analysis_content.json`、pre_docs、`测试分析checklist`、`--analysis-post-check-only` |
| 2 | [根据测试分析生成测试用例.md](modules/根据测试分析生成测试用例.md) | `test_cases_content.json`、`analysis_ref`、用例 checklist、`--post-check-only` |
| 3 | [测试分析导出XMind与JSON.md](modules/测试分析导出XMind与JSON.md) | `test_analysis-*.xmind` / `*.json`、`generate_xmind.py` |
| 4 | [测试用例导出Markdown与JSON.md](modules/测试用例导出Markdown与JSON.md) | MD、`convert_to_json.py`、Blade 用例 JSON |
| 5 | [Blade上传测试分析与用例.md](modules/Blade上传测试分析与用例.md) | `public/config.json`、上传脚本、`--upload` |

## 其它入口

- [`pre_docs/README.md`](../../../public/pre_docs/README.md)、[`post_docs/README.md`](../../../public/post_docs/README.md)
- [`public/templates/`](../../../public/templates/)：内容 JSON 模板

## 一键主命令（占位符）

```powershell
cd <your_workspace> ; python <skill_root>/scripts/generate_from_requirement.py "<需求目录>/<需求号>-<简述>.md" --output-dir "<需求目录绝对路径>" --product <产品名> --no-preview-doc
```

示例：产品 `HUI`、需求号 `202602033246`、简述「弹框居中可拖拽」（6 字）时：`<需求目录>` = `<your_workspace>/HUI/202602033246-弹框居中可拖拽`，第一个参数为该目录下的 `202602033246-弹框居中可拖拽.md`，`--output-dir` **同目录**，`--product HUI`。

`<skill_root>` 为本技能包根目录（与 `SKILL.md` 同级、内含 `scripts/`）。路径与 PowerShell 规则见 [modules/路径与编码约定.md](modules/路径与编码约定.md)。
