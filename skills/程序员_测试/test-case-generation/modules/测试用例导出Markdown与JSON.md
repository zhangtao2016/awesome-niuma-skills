# 测试用例导出 Markdown 与 JSON

## 目标

将 `test_cases_content.json` 转为：

- `test_cases-{标题英文}.md`（表格）
- `test_cases-{标题英文}.json`（Blade `importOfflineCase` 等导入格式）

## 主脚本（推荐）

```powershell
cd <your_workspace> ; python <skill>/scripts/generate_from_requirement.py "<需求绝对路径>" --output-dir "<输出绝对路径>" [--skip-json]
```

`--skip-json` 仅生成 MD。

## 仅从 MD 转 JSON

```powershell
python <skill>/scripts/convert_to_json.py "<绝对路径>/test_cases-xxx.md" "<绝对路径>/test_cases-xxx.json" --api-token "..." --account "..." --node-path "/..."
```

具体字段与 Blade 结构以脚本 `convert_to_json.py` 输出为准；模板见 [`test_cases_content.json`](../../../../public/templates/test_cases_content.json)。

## 前置条件 key

按产品的 `precondition_key` 从 **`public/config.json`**（`default` 与产品键合并）读取，主脚本生成 JSON 时会自动带入。
