钉钉全产品 Skill `dws`（即 DingTalk Workspace CLI）是钉钉官方于2026年3月开源的命令行工具，旨在让 AI Agent 和开发者通过统一接口操作钉钉核心功能。它覆盖了钉钉主要产品能力，并支持结构化输出，便于自动化集成。

---

核心功能概览

`dws` 支持以下主要产品域的操作（截至2026年3月）：

- 通讯录：搜索用户、查看部门  
- 群聊：管理群成员、发机器人消息  
- 日历：查日程、会议室、闲忙状态  
- 待办：创建和管理任务  
- 审批：处理审批流程  
- 考勤：打卡记录、排班查询  
- DING 消息：发送与撤回强提醒  
- 日志：查看与统计日报/周报  
- 智能表格（AITable）：操作多维表格数据  
- 工作台：查询已安装应用  

> 更多功能如文档、邮箱、钉盘、视频会议、Teambition 等正在陆续接入中 。

---

使用步骤

1. 安装 `dws`
无需安装 Go、Node.js 等依赖，直接运行对应系统命令：

- macOS / Linux：
  ```bash
  curl -fsSL https://raw.githubusercontent.com/DingTalk-Real-AI/dingtalk-workspace-cli/main/scripts/install.sh | sh
  ```

- Windows (PowerShell)：
  ```powershell
  irm https://raw.githubusercontent.com/DingTalk-Real-AI/dingtalk-workspace-cli/main/scripts/install.ps1 | iex
  ```

> 安装后需确保 `~/.local/bin`（或 Windows 对应路径）已加入系统 `PATH` 。

2. 完成认证
需企业管理员授权，目前处于灰度共创阶段，需加入钉钉 DWS 共创群获取白名单权限 。

- 方式一：命令行认证
  ```bash
  dws auth login --client-id <你的AppKey> --client-secret <你的AppSecret>
  ```

- 方式二：设置环境变量
  ```bash
  export DWS_CLIENT_ID=<你的AppKey>
  export DWS_CLIENT_SECRET=<你的AppSecret>
  dws auth login
  ```

> 凭证需从钉钉开放平台创建的“魔法棒”或“AI 应用”中获取 。

3. 常用操作示例

- 列出今日日程：
  ```bash
  dws calendar event list
  ```

- 创建待办：
  ```bash
  dws todo task create --title "完成季度汇报" --executors "<userId>"
  ```

- 列出日历事件：
  ```bash
  dws calendar event list
  ```

- 搜索联系人：
  ```bash
  dws contact user search --keyword "悟空"
  ```

- 发送 DING 消息：
  ```bash
  dws ding send --user-ids "<userId>" --content "请审核文档"
  ```

- 查看 AI 表格数据（JSON 格式，便于 AI 处理）：
  ```bash
  dws aitable query_records --table-id "tbl_abc" -f json
  ```

> 所有命令支持 `--dry-run` 参数预览操作而不执行，避免误操作 。

  ```bash
  dws todo task list --dry-run
  ```

---

AI Agent 集成

`dws` 内置 Agent Skills，自动部署至 `~/.agents/skills/dws`，主流 AI 工具（如 Claude Code、Cursor、Windsurf）可自动识别并调用 。

- 技能自动发现：无需手动配置，AI 可直接通过自然语言指令调用钉钉功能。
- 跨产品工作流示例：
  > “帮我给今天要跟进的客户创建会议，并分配待办给销售。”  
  > AI 会自动调用 CRM Skill → 日历 Skill → 待办 Skill，实现自动化流转 。

---

注意事项

- 权限限制：当前需企业管理员授权，仅限白名单企业使用 。
- 输出格式灵活：支持 `table`（默认）、`json`（推荐用于 AI）、`raw`（调试）三种格式 。
- 安全机制：凭证采用 PBKDF2 + AES-256-GCM 加密，密钥绑定设备 MAC，不可跨设备迁移 。

---

官方资源

- GitHub 仓库：[DingTalk Workspace CLI](https://github.com/DingTalk-Real-AI/dingtalk-workspace-cli)  
- 钉钉开放平台（配置魔法棒应用）：[钉钉开放平台](https://open.dingtalk.com/document/ai-dev/configure-the-magic-wand-application) 

如需进一步自动化，可结合管道操作（如 `dws contact list | jq '.users[] | select(.name=="xxx")'`）构建复杂工作流 。