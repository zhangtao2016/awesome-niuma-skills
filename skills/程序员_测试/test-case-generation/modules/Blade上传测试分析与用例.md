# Blade 上传测试分析与用例

## 顺序

主脚本 `generate_from_requirement.py` 在指定 `--upload` 时：

1. 上传**测试用例** JSON（`importOfflineCase`，与现有逻辑一致）。
2. 若已生成 `test_analysis-*.json`，在**用例上传成功**后，再 POST **测试分析**到固定地址 `importKity`（见 `upload_analysis_to_blade.py` 中 `DEFAULT_ANALYSIS_IMPORT_KITY_URL`）。

任一步失败则**不会**因上传成功而清理中间产物（与用例上传失败行为一致）。

## public/config.json（default 与各产品键可覆盖）

测试分析与用例共用以下键（无单独「分析 URL / 分析 token / projectId」配置项）：

| 键 | 说明 |
|----|------|
| `api_token` | Blade OpenAPI / share 接口鉴权 |
| `account` | 域账号 |
| `node_path` | 测试分析在 Blade 中的目录基础路径（与用例上传逻辑一致，脚本会结合项目名与 `importDirectory`） |

**接口契约附录**：`importKity` 模式下脚本将交付物 `title` + `topic_data` 转为 kity 并组装请求体；自定义 OpenAPI 时使用 `upload_analysis_to_blade.py --raw` 并将完整 body 写在 JSON 根对象中。若与接口不符，请在本地先做字段映射或调整文件内容后再上传。

## 单独上传分析

```powershell
python <skill>/scripts/upload_analysis_to_blade.py "<绝对路径>/test_analysis-xxx.json" --product HUI
```

默认使用脚本内 `importKity` 地址；需其它接口时传 `--api-url`。
