# AGENTS.md — 牛马 Skill 仓库操作指南

## 仓库性质

这是一个纯内容仓库，只存放 AI 技能定义文件（SKILL.md）。**没有根级构建系统、测试框架、lint 配置或包管理器**。不要尝试运行 `npm install`、`pip install` 或任何构建命令。

## 克隆与子模块

部分技能是 git submodule，必须递归克隆：

```bash
git clone --recurse-submodules https://github.com/zhangtao2016/awesome-niuma-skills.git
```

当前子模块：
- `skills/名人传记/yupi-skill`
- `skills/名人传记/mao-zedong-perspective`
- `skills/名人传记/qiqing-liuyu`
- `skills/名人传记/colleague-skill`
- `skills/知识管理/notebooklm-skill`
- `skills/知识管理/obsidian-skills`
- `skills/图形处理/fireworks-tech-graph`
- `skills/创业与商业/极简主义创业之旅`
- `skills/程序员_开发/开发工作流/verification-before-completion`

子模块只读镜像，修改请提 PR 到上游仓库。

## 技能结构

```
skills/
└── <分类>/
    └── <技能名称>/
        ├── SKILL.md          # 必需，技能主文件
        ├── README.md         # 可选
        ├── scripts/          # 可选，辅助脚本
        └── references/       # 可选，参考资料
```

每个技能按 `skills/<分类>/<技能名称>/` 组织，`SKILL.md` 是唯一必需文件。

## 自动生成文件（禁止手动编辑）

以下文件由工具或 CI 自动生成，**直接编辑会被覆盖**：

- `docs/skills-list.md` — 技能清单（工具生成）
- `docs/skills-tree.md` — 目录树（工具生成）
- `docs/skills-intro.md` — 技能介绍（工具生成）
- `CONTRIBUTORS.md` — 贡献者列表（CI 通过 thanks-contributors 生成）

## CI 自动写入区域

`README.md` 中的以下 HTML 注释标记区域由 GitHub Actions 自动更新，**不要在这些标记之间手动写入内容**：

- `<!-- CONTRIBUTION_STATS_START -->` / `<!-- CONTRIBUTION_STATS_END -->`
- `<!-- CONTRIBUTORS -->`

## 技能内建工具链

部分技能自带可执行脚本，但不属于仓库级 CI/CD：

- `skills/文档处理/minimax-docx/scripts/dotnet/` — .NET 项目，需 `dotnet` SDK
- `skills/知识管理/notebooklm-skill/scripts/` — Python 脚本，需 Chrome 浏览器
- `skills/程序员_测试/test-case-generation/scripts/` — Python 测试用例生成脚本

## 语言约定

项目整体以中文为主。技能描述、README 内容、分类名称均使用简体中文。部分技能（多来自上游英文仓库）保留英文原文，但中文始终是仓库的第一语言。

## 工作边界

- 修改已有技能时，只编辑该技能目录下的文件，不要跨技能修改
- 添加新技能：在对应分类下创建 `skills/<分类>/<技能名称>/SKILL.md`
- 修改子模块技能时，提醒用户去上游仓库提 PR
- 不要修改 `.gitmodules` 除非确实需要增删子模块