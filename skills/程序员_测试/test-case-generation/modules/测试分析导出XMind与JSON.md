# 测试分析导出 XMind 与 JSON

## 目标

将 `test_analysis_content.json` 转为交付物：

- `test_analysis-{标题英文}.xmind`
- `test_analysis-{标题英文}.json`（与内容结构一致：`title` + `topic_data`，UTF-8）

`{标题英文}` 由脚本按 `requirement_title` / 需求摘要做 `sanitize_filename`。

## 主脚本（推荐）

在输出目录放置 `test_analysis_content.json` 后：

```powershell
cd <your_workspace> ; python <skill>/scripts/generate_from_requirement.py "<需求绝对路径>" --output-dir "<输出绝对路径>"
```

## 单独生成 XMind

```powershell
python <skill>/scripts/generate_xmind.py --content "<绝对路径>/test_analysis_content.json" --output "<绝对路径>/test_analysis-out.xmind"
```

单独使用 `generate_xmind.py` **不会**写出 JSON 交付物；需要 JSON 时请用主脚本或自行复制内容文件为交付文件名。

## 路径与 PowerShell

- 一律使用**绝对路径**、英文目录名；PowerShell 多条命令用 `;` 分隔。
