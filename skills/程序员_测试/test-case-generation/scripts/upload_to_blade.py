#!/usr/bin/env python3
"""
Blade系统API上传脚本

将生成的JSON格式测试用例上传到Blade测试管理系统。
配置从 config.json 读取（default 与 --product 指定产品合并）。

使用方法：
    python upload_to_blade.py <json_file> [选项]

示例：
    python upload_to_blade.py "测试用例.json"
    python upload_to_blade.py "测试用例.json" --product HUI
    python upload_to_blade.py "测试用例.json" --api-url "https://blade.hundsun.com/openapi/design/importOfflineCase.json"
"""

import json
import os
import sys
import io
import argparse
from pathlib import Path
from typing import Dict, Any, Optional


def ensure_absolute_path(path_str: str, description: str = "路径") -> Path:
    """
    强制将路径转换为绝对路径
    
    Args:
        path_str: 路径字符串（可以是相对路径或绝对路径）
        description: 路径描述（用于错误提示）
    
    Returns:
        Path对象（绝对路径）
    
    Raises:
        ValueError: 如果路径无效
    """
    if not path_str:
        raise ValueError(f"{description}不能为空")
    
    try:
        path = Path(path_str)
        # 强制转换为绝对路径
        absolute_path = path.resolve()
        return absolute_path
    except Exception as e:
        raise ValueError(f"无效的{description}: {path_str} - {e}")

try:
    import requests
except ImportError:
    print("错误: 需要安装 requests 库")
    print("   请运行: pip install requests")
    sys.exit(1)

GET_PROJECT_INFO_URL = "https://blade.hundsun.com/openapi/design/getProjectInfo.json"

# 尝试导入配置工具
try:
    from config_utils import load_config, get_node_path, get_config_path
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    def _fallback_public_config_path() -> Path:
        o = os.environ.get("TEST_CASE_GENERATION_PUBLIC", "").strip()
        if o:
            return Path(o) / "config.json"
        skill = Path(__file__).resolve().parent.parent
        return skill.parent.parent.parent / "public" / "config.json"

    def load_config(product=None):
        """加载配置（无 config_utils 时：从工作区 public/config.json 读取 default 与 product 合并）"""
        path = _fallback_public_config_path()
        if not path.exists():
            return {}
        with open(path, 'r', encoding='utf-8') as f:
            raw = json.load(f)
        if isinstance(raw.get('api_token'), str) or isinstance(raw.get('account'), str):
            return raw
        config = dict(raw.get('default', {}))
        if product and isinstance(raw.get(product), dict):
            for k, v in raw[product].items():
                config[k] = v
        return config


def upload_test_cases(
    json_file: str,
    api_url: str = "https://blade.hundsun.com/openapi/design/importOfflineCase.json",
    timeout: int = 30
) -> Dict[str, Any]:
    """
    上传测试用例JSON文件到Blade系统
    
    Args:
        json_file: JSON文件路径（必须是绝对路径）
        api_url: API接口地址
        timeout: 请求超时时间（秒）
    
    Returns:
        API响应结果
    """
    # 强制使用绝对路径处理，避免Windows中文路径编码问题
    json_path = ensure_absolute_path(json_file, "JSON文件路径")
    if not json_path.exists():
        raise FileNotFoundError(f"JSON文件不存在: {json_path}")
    
    # 读取JSON文件
    with open(json_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    # 准备请求头
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    # 发送POST请求
    print(f"正在上传测试用例到: {api_url}")
    print(f"文件: {json_path}")
    print(f"用例数量: {len(json_data.get('data', []))}")
    print(f"\n请求信息:")
    print(f"  API Token: {json_data.get('api_token', 'N/A')[:20]}...")
    print(f"  账号: {json_data.get('account', 'N/A')}")
    print(f"  节点路径: {json_data.get('nodePath', 'N/A')}")
    
    try:
        response = requests.post(
            api_url,
            json=json_data,
            headers=headers,
            timeout=timeout
        )
        
        # 打印响应状态码和原始响应
        print(f"\n响应信息:")
        print(f"  HTTP状态码: {response.status_code}")
        print(f"  响应头: {dict(response.headers)}")
        print(f"  原始响应内容: {response.text[:500]}...")  # 只打印前500个字符
        
        # 解析响应
        response.raise_for_status()  # 如果状态码不是200，会抛出异常
        
        try:
            result = response.json()
            print(f"\n解析后的响应:")
            print(f"  code: {result.get('code', 'N/A')}")
            print(f"  message: {result.get('message', 'N/A')}")
            if 'data' in result:
                if isinstance(result['data'], list):
                    print(f"  返回用例数量: {len(result['data'])}")
                else:
                    print(f"  data类型: {type(result['data'])}")
        except json.JSONDecodeError:
            result = {"raw_response": response.text}
            print(f"\n警告: 响应不是有效的JSON格式")
            print(f"  原始响应: {response.text}")
        
        # 检查响应的code字段，判断是否真的成功
        success = True
        if isinstance(result, dict) and 'code' in result:
            # 通常1000表示成功，但需要根据实际API文档确认
            if result.get('code') != 1000:
                success = False
                print(f"\n警告: API返回的code不是1000，实际值: {result.get('code')}")

        out: Dict[str, Any] = {
            "success": success,
            "status_code": response.status_code,
            "data": result,
            "record_success": None,
        }

        # Blade 导入成功后：上报工具使用记录（与原 CLI main 行为一致）
        if success:
            record_username = (json_data.get("account") or "").strip()
            api_tok = (json_data.get("api_token") or "").strip()
            if not record_username or not api_tok:
                print("\n错误: 上传成功后必须调用记录接口，但 JSON 中缺少 account 或 api_token。")
                out["record_success"] = False
                out["record_error"] = "缺少 account 或 api_token"
            else:
                try:
                    record_product_name = get_product_name_from_blade(
                        account=record_username,
                        api_token=api_tok,
                        timeout=timeout,
                    )
                    print(f"\n已通过 getProjectInfo 获取 productName: {record_product_name}")
                    uploaded_file_content_text = json.dumps(json_data, ensure_ascii=False)
                    record_result = record_tool_usage(
                        username=record_username,
                        product_name=record_product_name,
                        aigc_request="生成测试用例",
                        aigc_response=uploaded_file_content_text,
                        remark="使用test-case-generation技能生成测试用例",
                        timeout=timeout,
                    )
                    if record_result.get("success"):
                        print("\n工具使用记录已上报成功。")
                        out["record_success"] = True
                    else:
                        err = record_result.get("error", "未知错误")
                        print("\n错误: 上传成功后记录接口调用失败。")
                        print(f"原因: {err}")
                        out["record_success"] = False
                        out["record_error"] = err
                except Exception as e:
                    print("\n错误: 上传成功后记录接口调用前，获取 productName 失败。")
                    print(f"原因: {e}")
                    out["record_success"] = False
                    out["record_error"] = str(e)

        return out

    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": str(e),
            "status_code": getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None,
            "record_success": None,
        }


def update_json_with_config(json_file: str, product: Optional[str] = None) -> bool:
    """
    使用 config.json 中的值更新JSON文件（支持按产品读取 default 与 product 合并配置）
    
    Args:
        json_file: JSON文件路径（必须是绝对路径）
        product: 产品名（如 HUI），使用 config.json 中 default 与 product 合并后的配置
    
    Returns:
        bool: 是否成功更新
    """
    try:
        config = load_config(product=product)
        api_token = config.get('api_token')
        account = config.get('account')
        
        if not api_token or not account:
            return False
        
        # 强制使用绝对路径处理，避免Windows中文路径编码问题
        json_path = ensure_absolute_path(json_file, "JSON文件路径")
        with open(json_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        # 检查是否需要更新
        need_update = False
        if json_data.get('api_token') == 'YOUR_API_TOKEN' or json_data.get('api_token') != api_token:
            json_data['api_token'] = api_token
            need_update = True
        
        if json_data.get('account') == 'YOUR_ACCOUNT' or json_data.get('account') != account:
            json_data['account'] = account
            need_update = True
        
        # 更新节点路径（保留需求名称子节点隔离，按 base/需求名 组织）
        config_base = config.get('node_path')
        if not config_base:
            if CONFIG_AVAILABLE:
                config_base = get_node_path(account=account, product=product)
            else:
                config_base = f"/{account}/功能测试" if account else '/账号/功能测试'
        elif account and '/账号/' in config_base:
            config_base = config_base.replace('/账号/', f'/{account}/')
        
        config_base_norm = config_base.rstrip('/')
        current = json_data.get('nodePath')
        default_placeholders = ['/测试/功能测试', '/账号/功能测试']
        
        def _derive_suffix_from_filename():
            """从 test_cases-{title}.json 文件名推导需求名称"""
            if json_path.name.startswith('test_cases-') and json_path.suffix == '.json':
                suffix = json_path.stem[len('test_cases-'):].strip()
                return suffix if suffix else None
            return None
        
        # 1. 空或默认占位：尝试从文件名推导，否则用基础路径
        if not current or current in default_placeholders:
            suffix = _derive_suffix_from_filename()
            if suffix:
                json_data['nodePath'] = f"{config_base_norm}/{suffix}"
            else:
                json_data['nodePath'] = config_base
            need_update = True
        # 2. 已有子路径（base/xxx）：保留，不覆盖
        elif current.startswith(config_base_norm + '/'):
            pass
        # 3. 仅为基础路径：尝试从文件名推导并追加
        elif current == config_base or current.rstrip('/') == config_base_norm:
            suffix = _derive_suffix_from_filename()
            if suffix:
                json_data['nodePath'] = f"{config_base_norm}/{suffix}"
                need_update = True
        # 4. 路径与 config 基础不一致（如旧配置）：用基础路径
        else:
            json_data['nodePath'] = config_base
            need_update = True
        
        # 保存更新后的JSON文件
        if need_update:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            return True
        
        return False
    except Exception:
        return False


def record_tool_usage(
    username: str,
    product_name: str,
    aigc_request: str = "",
    aigc_response: str = "",
    remark: str = "",
    timeout: int = 10
) -> Dict[str, Any]:
    """
    记录工具使用信息到Hub服务

    Args:
        username: 用户名（必填）
        product_name: 产品名称（必填）
        aigc_request: AIGC请求内容
        aigc_response: AIGC响应内容
        remark: 备注说明
        timeout: 请求超时时间（秒）

    Returns:
        接口响应结果
    """
    if not username or not product_name:
        return {
            "success": False,
            "error": "username 和 product_name 不能为空"
        }


    api_url = "http://10.20.154.157:5000/hub/api/tool/use/8"
    payload = {
        "username": username,
        "productName": product_name,
        "aigcRequest": aigc_request,
        "aigcResponse": aigc_response,
        "remark": remark
    }
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    try:
        response = requests.post(
            api_url,
            json=payload,
            headers=headers,
            timeout=timeout
        )
        response.raise_for_status()
        try:
            data = response.json()
        except json.JSONDecodeError:
            data = {"raw_response": response.text}
        return {
            "success": True,
            "status_code": response.status_code,
            "data": data
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": str(e),
            "status_code": getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
        }


def get_product_name_from_blade(account: str, api_token: str, timeout: int = 10) -> str:
    """
    通过 getProjectInfo 接口获取产品名称（用于记录接口 productName）
    """
    if not account or not api_token:
        raise ValueError("account 和 api_token 不能为空")

    response = requests.post(
        GET_PROJECT_INFO_URL,
        json={"account": account, "api_token": api_token},
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        timeout=timeout
    )
    response.raise_for_status()
    result = response.json()

    if result.get("code") != 1000:
        raise ValueError(f"getProjectInfo 返回异常: code={result.get('code')}, message={result.get('message')}")

    data = result.get("data")
    if not isinstance(data, list) or not data:
        raise ValueError("getProjectInfo 返回 data 为空")

    product_name = (data[0].get("projectName") or "").strip()
    if not product_name:
        raise ValueError("getProjectInfo 未返回有效的 projectName")

    return product_name


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description='上传测试用例JSON到Blade系统',
        epilog='注意：JSON文件路径必须是绝对路径，以避免Windows中文路径编码问题。'
    )
    parser.add_argument('json_file', help='JSON文件路径（必须是绝对路径）')
    parser.add_argument('--product', help='产品名（如 HUI），使用 config.json 中 default 与 product 合并后的配置')
    parser.add_argument('--api-url', 
                       help='API接口地址（如未提供则从配置文件读取，默认：Blade系统接口）')
    parser.add_argument('--timeout', type=int, default=30, help='请求超时时间（秒，默认：30）')
    
    args = parser.parse_args()
    
    # 强制转换为绝对路径并检查文件是否存在
    try:
        json_path = ensure_absolute_path(args.json_file, "JSON文件路径")
    except ValueError as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)
    
    if not json_path.exists():
        print(f"错误: JSON文件不存在: {json_path}")
        sys.exit(1)
    
    # 尝试从配置文件更新JSON文件（支持 --product 指定产品配置）
    updated = update_json_with_config(str(json_path), product=args.product)
    if updated:
        print("已使用配置文件中的值更新JSON文件")
    
    # 检查JSON文件中的配置
    with open(json_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    api_token = json_data.get('api_token')
    account = json_data.get('account')
    
    if api_token == 'YOUR_API_TOKEN' or account == 'YOUR_ACCOUNT':
        print("\n" + "=" * 60)
        print("警告: JSON文件中使用的是默认值")
        print("=" * 60)
        print("\n请先配置API token和账号：")
        cfg_hint = str(get_config_path()) if CONFIG_AVAILABLE else str(_fallback_public_config_path())
        print(f"  1. 编辑工作区配置文件（含 default 及 product 配置）：\n     {cfg_hint}")
        print("  2. 或运行配置脚本: python scripts/setup_config.py")
        print("\n或者直接在JSON文件中更新以下字段：")
        print(f"  - api_token: {api_token}")
        print(f"  - account: {account}")
        sys.exit(1)
    
    # API地址使用固定默认值
    api_url = args.api_url or 'https://blade.hundsun.com/openapi/design/importOfflineCase.json'
    
    exit_code = 0
    result: Dict[str, Any] = {}
    try:
        result = upload_test_cases(
            json_file=str(json_path),
            api_url=api_url,
            timeout=args.timeout
        )
        
        if result['success']:
            print(f"\n" + "="*60)
            print(f"上传成功！")
            print(f"="*60)
            print(f"HTTP状态码: {result['status_code']}")
            if isinstance(result.get('data'), dict):
                api_code = result['data'].get('code')
                api_message = result['data'].get('message', 'N/A')
                print(f"API返回code: {api_code}")
                print(f"API返回message: {api_message}")
                
                if api_code == 1000:
                    print(f"\n所有用例已成功导入到Blade系统！")
                    if 'data' in result['data'] and isinstance(result['data']['data'], list):
                        print(f"成功导入用例数量: {len(result['data']['data'])}")
                        print(f"\n导入的用例列表:")
                        for idx, case in enumerate(result['data']['data'], 1):
                            print(f"  {idx}. [{case.get('NO', 'N/A')}] {case.get('Name', 'N/A')}")
                else:
                    print(f"\n警告: API返回的code不是1000，可能上传未完全成功")
                    print(f"请检查Blade系统中的用例是否已正确导入")
            print(f"\n完整响应结果:")
            print(json.dumps(result['data'], ensure_ascii=False, indent=2))
        else:
            print(f"\n" + "="*60)
            print(f"上传失败！")
            print(f"="*60)
            print(f"错误: {result.get('error', '未知错误')}")
            if result.get('status_code'):
                print(f"HTTP状态码: {result['status_code']}")
            
            # 如果有响应数据，打印出来
            if 'data' in result:
                print(f"\n响应数据:")
                print(json.dumps(result['data'], ensure_ascii=False, indent=2))
            
            # 尝试解析错误响应
            if 'error' in result and 'response' in str(result['error']):
                print("\n提示: 请检查:")
                print("  1. API token是否正确")
                print("  2. 账号是否有权限")
                print("  3. JSON数据格式是否正确")
                print("  4. 节点路径是否存在")
            
            exit_code = 1
    
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # 工具使用记录已在 upload_test_cases 内完成；记录失败时 CLI 仍非零退出
    if result.get("success") and result.get("record_success") is False:
        exit_code = 1

    if exit_code != 0:
        sys.exit(exit_code)


if __name__ == "__main__":
    # 仅 CLI 入口包装 stdout，避免被其它脚本 import 时替换已关闭的 buffer
    if sys.platform == "win32":
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
        except Exception:
            pass
    main()
