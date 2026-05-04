#!/usr/bin/env python3
"""
将测试分析交付 JSON（test_analysis-*.json）POST 到 Blade 配置的分析导入地址。

- 交付物格式（根含 title + topic_data）：按 Blade 已验证的 importKity 契约组装请求体
  （逻辑对齐技能工具库 `skills/utils/blade.py` 中 TestKity.kity_to_blade / create_kity_path）。
- 其它根对象：原样作为 JSON POST，并按 config 合并 api_token（兼容自定义 OpenAPI）。

请求体默认即为文件中的 JSON 对象；鉴权字段以实际接口契约为准，见 modules/Blade上传测试分析与用例.md。
"""

import argparse
import copy
import io
import json
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import requests
except ImportError:
    print("错误: 需要安装 requests 库")
    print("   请运行: pip install requests")
    sys.exit(1)

# 与 utils/blade.py TestKity.kity_to_blade 一致：share 域测分导入
DEFAULT_ANALYSIS_IMPORT_KITY_URL = (
    "https://blade.hundsun.com/shareInterface/analysis/importKity.json"
)
_GET_PROJECT_INFO_URL = "https://blade.hundsun.com/openapi/design/getProjectInfo.json"
_IMPORT_DIRECTORY_URL = "https://blade.hundsun.com/openapi/analysis/importDirectory.json"

try:
    from config_utils import load_config, get_node_path
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    load_config = None  # type: ignore
    get_node_path = None  # type: ignore


def ensure_absolute_path(path_str: str, description: str = "路径") -> Path:
    if not path_str:
        raise ValueError(f"{description}不能为空")
    path = Path(path_str)
    return path.resolve()


def _is_delivery_analysis(body: Dict[str, Any]) -> bool:
    return isinstance(body.get("title"), str) and isinstance(body.get("topic_data"), dict)


def _uses_import_kity_url(api_url: str) -> bool:
    u = (api_url or "").strip().lower()
    return "importkity" in u or "shareinterface/analysis/importkity" in u


def _suffix_from_analysis_filename(json_path: Path) -> Optional[str]:
    if json_path.name.startswith("test_analysis-") and json_path.suffix == ".json":
        s = json_path.stem[len("test_analysis-") :].strip()
        return s if s else None
    return None


def _resolve_node_path_string(cfg: Dict[str, Any], json_path: Path, product: Optional[str]) -> str:
    account = (cfg.get("account") or "").strip()
    base = ""
    if CONFIG_AVAILABLE and get_node_path:
        base = (get_node_path(account=account or None, product=product) or "").strip()
    else:
        base = (cfg.get("node_path") or "").strip()
    if not base and account:
        base = f"/{account}/功能测试"
    base_norm = base.rstrip("/")
    suffix = _suffix_from_analysis_filename(json_path)
    if suffix and base_norm:
        return f"{base_norm}/{suffix}"
    if suffix and not base_norm:
        return f"/{suffix}".replace("//", "/")
    return base or base_norm


def _node_path_to_array(node_path: str) -> List[str]:
    p = (node_path or "").strip().strip("/")
    if not p:
        return []
    return [x for x in p.split("/") if x]


def _relative_path_for_create_kity(config_path: str, project_name: str) -> str:
    """若配置路径首段与 Blade 项目名相同，则去掉首段后供 importDirectory 逐级创建。"""
    p = (config_path or "").strip().strip("/")
    if not p:
        return ""
    parts = p.split("/")
    if parts and parts[0] == project_name:
        return "/".join(parts[1:])
    return p


# --- 以下 kity 预处理与目录创建逻辑从 utils/blade.py 抽取，改为 requests，避免 utils 包路径依赖 ---


def _kity_add_unique_id(node: Dict[str, Any]) -> Dict[str, Any]:
    if "data" in node and isinstance(node.get("data"), dict):
        node["data"]["id"] = str(uuid.uuid4()).replace("-", "")[:24]
    ch = node.get("children")
    if isinstance(ch, list):
        for child in ch:
            if isinstance(child, dict):
                _kity_add_unique_id(child)
    return node


def _kity_split_long_text(node: Dict[str, Any]) -> None:
    data = node.get("data")
    if not isinstance(data, dict):
        return
    text = data.get("text", "")
    if not isinstance(text, str):
        return
    while len(text) > 200:
        new_node = copy.deepcopy(node)
        if isinstance(new_node.get("data"), dict):
            new_node["data"]["text"] = text[200:]
            new_node["data"]["id"] = str(uuid.uuid4()).replace("-", "")[:24]
        data["text"] = text[:200]
        data["note"] = ""
        node["children"] = [new_node]
        node = new_node
        data = node.get("data") or {}
        text = data.get("text", "") if isinstance(data, dict) else ""
    ch = node.get("children")
    if isinstance(ch, list):
        for c in ch:
            if isinstance(c, dict):
                _kity_split_long_text(c)


def _kity_remove_null(node: Dict[str, Any]) -> None:
    ch = node.get("children")
    if isinstance(ch, list):
        kept = [c for c in ch if c is not None]
        if len(kept) != len(ch):
            node["children"] = kept
        for c in node.get("children", []):
            if isinstance(c, dict):
                _kity_remove_null(c)


def _prepare_kity_tree(kity: Dict[str, Any]) -> Dict[str, Any]:
    _kity_remove_null(kity)
    _kity_split_long_text(kity)
    _kity_add_unique_id(kity)
    return kity


def topic_data_to_kity_children(topic_data: Any) -> List[Dict[str, Any]]:
    """将 topic_data 嵌套 dict 转为 kity 子节点列表（键为节点 text，值为子树）。"""
    if not isinstance(topic_data, dict):
        return []
    out: List[Dict[str, Any]] = []
    for key, sub in topic_data.items():
        text = key if isinstance(key, str) else str(key)
        node: Dict[str, Any] = {"data": {"text": text}, "children": []}
        if isinstance(sub, dict) and sub:
            node["children"] = topic_data_to_kity_children(sub)
        out.append(node)
    return out


def delivery_to_kity_root(title: str, topic_data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "data": {"text": (title or "").strip() or "测试分析"},
        "children": topic_data_to_kity_children(topic_data),
    }


def get_project_info(account: str, api_token: str, timeout: int) -> Dict[str, Any]:
    r = requests.post(
        _GET_PROJECT_INFO_URL,
        json={"account": account, "api_token": api_token},
        timeout=timeout,
    )
    r.raise_for_status()
    return r.json()


def create_kity_path(
    account: str, api_token: str, node_path: str, timeout: int
) -> str:
    """
    在 Blade 测试分析树下创建目录，返回「项目名/配置路径」形式的完整路径字符串。
    与 utils/blade.create_kity_path 行为一致。
    """
    pinfo = get_project_info(account, api_token, timeout)
    pdata = pinfo.get("data")
    if pdata is None:
        raise ValueError(f"无法获取项目信息，请检查 account / api_token: {pinfo}")
    project_name = pdata[0]["projectName"]
    root: Dict[str, Any] = {"name": "root", "children": []}
    node = root
    for p in node_path.split("/"):
        if not p:
            continue
        node["children"].append({"name": p, "children": []})
        node = node["children"][0]
    req = {
        "account": account,
        "api_token": api_token,
        "data": [{"nodePath": [project_name], "node": root["children"]}],
    }
    ret = requests.post(_IMPORT_DIRECTORY_URL, json=req, timeout=timeout).json()
    if ret.get("code") == 1000:
        return f"{project_name}/{node_path}"
    if ret.get("code") == 5999 and ret.get("message") == "null: null":
        return f"{project_name}/{node_path}"
    raise ValueError(f"创建分析目录失败: {node_path!r} -> {ret}")


def _build_import_kity_body(
    title: str,
    kity: Dict[str, Any],
    node_path_array: List[str],
    account: str,
    api_token: str,
) -> Dict[str, Any]:
    body: Dict[str, Any] = {
        "account": account,
        "api_token": api_token,
        "vid": "",
        "vName": "",
        "data": [
            {
                "analyLayer": "1",
                "analyName": title[:200] if title else "测试分析",
                "analyStatus": "0",
                "nodePath": node_path_array,
                "kity": kity,
            }
        ],
    }
    return body


def _merge_config_into_body(body: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(body)
    token = (config.get("api_token") or "").strip()
    if token and "api_token" not in out:
        out["api_token"] = token
    return out


def _response_business_success(result: Any, api_url: str) -> bool:
    if not isinstance(result, dict):
        return True
    if _uses_import_kity_url(api_url):
        code = result.get("code")
        if str(code) == "10000" or code == 10000:
            return True
        msg = (result.get("msg") or "").strip().lower()
        if msg == "success":
            return True
        return False
    if "code" in result:
        return result.get("code") == 1000
    return True


def upload_analysis_json(
    json_file: str,
    api_url: str,
    product: Optional[str] = None,
    timeout: int = 30,
) -> Dict[str, Any]:
    json_path = ensure_absolute_path(json_file, "JSON文件路径")
    if not json_path.exists():
        raise FileNotFoundError(f"JSON文件不存在: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        body = json.load(f)
    if not isinstance(body, dict):
        return {"success": False, "error": "分析JSON根节点必须为对象"}

    cfg: Dict[str, Any] = {}
    if CONFIG_AVAILABLE and load_config:
        cfg = load_config(product=product)

    use_kity = (
        _is_delivery_analysis(body)
        and _uses_import_kity_url(api_url)
    )

    if use_kity:
        account = (body.get("account") or cfg.get("account") or "").strip()
        token = (
            (body.get("api_token") or "").strip()
            or (cfg.get("api_token") or "").strip()
        )
        if not account or not token:
            return {
                "success": False,
                "error": "importKity 需要 account 与 api_token，请在 config.json 或交付 JSON 中配置",
            }
        title = (body.get("title") or "").strip() or "测试分析"
        topic_data = body.get("topic_data") or {}
        if not isinstance(topic_data, dict):
            return {"success": False, "error": "topic_data 必须为对象"}

        kity = _prepare_kity_tree(delivery_to_kity_root(title, topic_data))

        path_str = _resolve_node_path_string(cfg, json_path, product)
        if not path_str.strip("/"):
            return {
                "success": False,
                "error": "未配置 node_path，无法确定测试分析在 Blade 中的目录",
            }

        try:
            pinfo = get_project_info(account, token, timeout)
            pdata = pinfo.get("data")
            if pdata is None:
                raise ValueError(pinfo)
            project_name = pdata[0]["projectName"]
        except Exception as e:
            return {"success": False, "error": f"获取 Blade 项目信息失败: {e}"}

        rel = _relative_path_for_create_kity(path_str, project_name)
        if not rel:
            return {
                "success": False,
                "error": f"无法从 node_path 推导创建路径（与项目名 {project_name!r} 关系不明）: {path_str!r}",
            }
        try:
            full_path = create_kity_path(account, token, rel, timeout)
        except Exception as e:
            return {"success": False, "error": str(e)}

        node_arr = _node_path_to_array(full_path)
        if not node_arr:
            return {"success": False, "error": "nodePath 解析为空"}

        post_body = _build_import_kity_body(title, kity, node_arr, account, token)
    else:
        post_body = _merge_config_into_body(body, cfg)

    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    print(f"正在上传测试分析到: {api_url}")
    print(f"文件: {json_path}")
    if use_kity:
        print(f"模式: importKity（由 title/topic_data 组装）")
        print(f"分析名称: {post_body.get('data', [{}])[0].get('analyName', '')}")

    try:
        response = requests.post(api_url, json=post_body, headers=headers, timeout=timeout)
        print(f"HTTP状态码: {response.status_code}")
        try:
            result = response.json()
        except json.JSONDecodeError:
            result = {"raw_response": response.text[:500]}
        response.raise_for_status()
        success = _response_business_success(result, api_url)
        if not success:
            print(f"警告: 业务返回表示可能未成功: {result}")
        return {"success": success, "status_code": response.status_code, "data": result}
    except requests.exceptions.RequestException as e:
        err_body: Any = None
        resp = getattr(e, "response", None)
        if resp is not None:
            try:
                err_body = resp.json()
            except Exception:
                err_body = (resp.text or "")[:500]
        return {
            "success": False,
            "error": str(e),
            "status_code": getattr(resp, "status_code", None) if resp is not None else None,
            "data": err_body,
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="上传测试分析JSON到Blade（URL 来自参数或默认值）")
    parser.add_argument("json_file", help="test_analysis-*.json 绝对路径")
    parser.add_argument("--product", help="产品名，合并 config.json")
    parser.add_argument(
        "--api-url",
        help="上传地址；不传时默认使用 importKity",
    )
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args()

    api_url = (args.api_url or "").strip() or DEFAULT_ANALYSIS_IMPORT_KITY_URL

    result = upload_analysis_json(
        json_file=args.json_file,
        api_url=api_url,
        product=args.product,
        timeout=args.timeout,
    )
    if result.get("success"):
        print("上传完成（请根据返回 JSON 确认业务是否成功）")
        print(json.dumps(result.get("data"), ensure_ascii=False, indent=2))
        sys.exit(0)
    print(f"上传失败: {result.get('error', '未知错误')}", file=sys.stderr)
    if result.get("data") is not None:
        print(json.dumps(result.get("data"), ensure_ascii=False, indent=2), file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    if sys.platform == "win32":
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
        except Exception:
            pass
    main()
