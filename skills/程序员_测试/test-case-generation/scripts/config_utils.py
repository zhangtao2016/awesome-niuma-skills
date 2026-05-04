#!/usr/bin/env python3
"""
配置工具模块

提供配置文件的读取和管理功能。
默认约定：技能包位于工作区内含中间层的固定目录（如 <workspace>/<中间层目录>/skills/test-case-generation/，其中中间层可为以 . 开头的目录，常见如 .cursor、.claude、.trae）；
config.json、pre_docs、post_docs、templates 位于工作区 public/（可用配置项覆盖路径）。
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional


def get_config_dir() -> Path:
    """获取技能包目录（test-case-generation）。"""
    script_dir = Path(__file__).resolve().parent
    return script_dir.parent


def get_skill_dir() -> Path:
    """同 get_config_dir()，技能包根目录。"""
    return get_config_dir()


def get_workspace_public_dir() -> Path:
    """
    工作区下的 public 目录：<workspace>/public/
    由技能包根向上三级：test-case-generation -> skills -> workspace 子目录 -> workspace。
    若技能包不在上述层级，可设环境变量 TEST_CASE_GENERATION_PUBLIC 为绝对路径覆盖。
    """
    override = os.environ.get("TEST_CASE_GENERATION_PUBLIC", "").strip()
    if override:
        return Path(override)
    return get_skill_dir().parent.parent.parent / "public"


def get_config_path() -> Path:
    """获取配置文件路径（工作区 public/config.json）。"""
    return get_workspace_public_dir() / "config.json"


def get_templates_dir() -> Path:
    """内容 JSON 模板目录（默认 public/templates）。"""
    return get_workspace_public_dir() / "templates"


def load_config(product: Optional[str] = None) -> Dict[str, Any]:
    """
    从单一 config.json 加载配置，支持多产品。

    config.json 结构示例：
    {
      "default": { "api_token": "...", "account": "...", "node_path": "...", "precondition_key": "..." },
      "HUI": { "api_token": "...", "precondition_key": "..." }
    }

    - default 为必填默认配置
    - product 非空时，用 default 与 product 合并（同键时产品配置覆盖 default）

    Args:
        product: 产品名（如 HUI），对应 config 中的 "HUI" 键

    Returns:
        合并后的配置字典
    """
    base_path = get_config_path()
    raw = {}
    if base_path.exists():
        try:
            with open(base_path, 'r', encoding='utf-8') as f:
                raw = json.load(f)
        except Exception as e:
            print(f"警告: 读取配置文件失败: {e}")
            return {}
    # 兼容旧格式：顶层直接是 api_token 等，视为 default
    if not raw:
        return {}
    if isinstance(raw.get('api_token'), str) or isinstance(raw.get('account'), str):
        base_config = raw
    else:
        base_config = dict(raw.get('default', {}))
    if not product:
        return base_config
    product_config = raw.get(product, {})
    if isinstance(product_config, dict):
        for k, v in product_config.items():
            base_config[k] = v
    return base_config


def get_config_value(key: str, default: Any = None, override: Optional[Any] = None, product: Optional[str] = None) -> Any:
    """
    获取配置值

    Args:
        key: 配置键名
        default: 默认值
        override: 覆盖值（优先级最高，通常来自命令行参数）
        product: 产品名，用于从 config.json 中读取 default 与 product 合并后的配置

    Returns:
        配置值，优先级：override > 产品/基础配置 > default
    """
    if override is not None:
        return override

    config = load_config(product=product)
    return config.get(key, default)


def get_api_token(override: Optional[str] = None, product: Optional[str] = None) -> Optional[str]:
    """获取API token（可按产品从 config.json 读取）"""
    return get_config_value('api_token', override=override, product=product)


def get_account(override: Optional[str] = None, product: Optional[str] = None) -> Optional[str]:
    """获取账号（可按产品从 config.json 读取）"""
    return get_config_value('account', override=override, product=product)


def get_node_path(override: Optional[str] = None, account: Optional[str] = None, product: Optional[str] = None) -> Optional[str]:
    """
    获取节点路径

    Args:
        override: 覆盖值（优先级最高）
        account: 账号（用于自动生成节点路径）
        product: 产品名，用于加载对应配置

    Returns:
        节点路径，如果未指定且账号存在，则自动生成 /账号/功能测试
    """
    if override:
        return override

    config = load_config(product=product)
    node_path = config.get('node_path')

    # 如果配置文件中没有节点路径，根据账号自动生成
    if not node_path:
        account = account or config.get('account')
        if account:
            return f"/{account}/功能测试"
        return '/账号/功能测试'  # 默认值

    # 如果节点路径中包含"账号"占位符，替换为实际账号
    if account and '/账号/' in node_path:
        node_path = node_path.replace('/账号/', f'/{account}/')

    return node_path


def get_pre_docs_dir(override: Optional[str] = None, product: Optional[str] = None) -> Path:
    """
    获取前置文档目录路径

    按产品名存放前置文档，目录结构：pre_docs/<产品名>/

    Args:
        override: 覆盖值（优先级最高，绝对路径）
        product: 产品名（仅用于读取 pre_docs_dir 配置项，目录结构仍为 pre_docs/）

    Returns:
        前置文档根目录路径
    """
    if override:
        return Path(override)

    config = load_config(product=product)
    pre_docs = config.get('pre_docs_dir')

    if pre_docs:
        return Path(pre_docs)

    return get_workspace_public_dir() / 'pre_docs'


def get_post_docs_dir(override: Optional[str] = None, product: Optional[str] = None) -> Path:
    """
    获取后置文档目录路径

    按产品名存放后置自查清单，目录结构：post_docs/<产品名>/

    Args:
        override: 覆盖值（优先级最高，绝对路径）
        product: 产品名（仅用于读取 post_docs_dir 配置项）

    Returns:
        后置文档根目录路径
    """
    if override:
        return Path(override)

    config = load_config(product=product)
    post_docs = config.get('post_docs_dir')

    if post_docs:
        return Path(post_docs)

    return get_workspace_public_dir() / 'post_docs'


def get_analysis_import_url(override: Optional[str] = None, product: Optional[str] = None) -> str:
    """分析结果导入 Blade 的 POST 地址；未配置时返回空字符串。"""
    v = get_config_value("analysis_import_url", default="", override=override, product=product)
    return (v or "").strip() if isinstance(v, str) else ""


def get_precondition_key(override: Optional[str] = None, product: Optional[str] = None) -> str:
    """
    获取前置条件字段名（Blade 步骤中前置条件的 key）

    Args:
        override: 覆盖值（优先级最高）
        product: 产品名，用于从 config.json 中读取对应产品配置

    Returns:
        前置条件字段名，默认：user_key_c808a8ed36781fe8de3d8f
    """
    return get_config_value('precondition_key', default='user_key_c808a8ed36781fe8de3d8f', override=override, product=product)

