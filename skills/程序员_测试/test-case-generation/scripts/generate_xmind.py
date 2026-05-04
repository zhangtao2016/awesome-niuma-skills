#!/usr/bin/env python3
"""
XMind文件生成脚本（格式层：只负责「内容 -> XMind 文件」）

用于生成符合XMind格式规范的思维导图文件。
XMind文件本质是一个ZIP压缩包，包含content.json、metadata.json、manifest.json和content.xml四个文件。

内容由外部提供，脚本只做格式输出。支持两种用法：

用法1 - 从内容文件读取（推荐，供 AI/用户事先写好内容）：
    python generate_xmind.py --content <test_analysis_content.json> --output <out.xmind>

用法2 - 命令行传入（向后兼容）：
    python generate_xmind.py <output_path> <root_title> [topic_data_json]
"""

import json
import zipfile
import uuid
import time
import sys
import argparse
from pathlib import Path


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


def generate_id():
    """生成UUID，去掉横线"""
    return str(uuid.uuid4()).replace('-', '')


def create_topic(title, children=None):
    """
    创建主题节点
    
    Args:
        title: 主题标题
        children: 子主题列表，如果为None则不包含children字段
    
    Returns:
        主题字典对象
    """
    topic = {
        "id": generate_id(),
        "title": title,
        "style": {"id": generate_id(), "properties": {}}
    }
    if children:
        topic["children"] = {"attached": children}
    return topic


def build_topic_tree(topic_data):
    """
    递归构建主题树形结构
    
    Args:
        topic_data: 字典格式的主题数据，格式如：
                   {"主题1": {}, "主题2": {"子主题1": {}, "子主题2": {}}}
    
    Returns:
        主题对象列表
    """
    topics = []
    for title, children_data in topic_data.items():
        children = None
        if children_data:
            children = build_topic_tree(children_data)
        topics.append(create_topic(title, children))
    return topics


def generate_xmind(output_path, root_title, topic_data=None):
    """
    生成XMind文件
    
    Args:
        output_path: 输出文件路径（必须是绝对路径，支持中文路径）
        root_title: 根主题标题
        topic_data: 主题数据字典，格式如：
                   {"子主题1": {}, "子主题2": {"子子主题1": {}}}
                   如果为None，则只创建根主题
    """
    # 强制使用绝对路径处理，避免Windows中文路径编码问题
    output_file = ensure_absolute_path(output_path, "输出文件路径")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # 构建rootTopic树形结构
    root_children = None
    if topic_data:
        root_children = build_topic_tree(topic_data)
    
    root_topic = {
        "id": generate_id(),
        "title": root_title,
        "style": {"id": generate_id(), "properties": {}}
    }
    if root_children:
        root_topic["children"] = {"attached": root_children}
    
    # 创建content.json数据
    content_data = {
        "id": generate_id(),
        "title": generate_id(),
        "rootTopic": root_topic,
        "style": {"id": generate_id(), "properties": {}},
        "topicPositioning": "fixed"
    }
    
    # 生成content.xml（必须包含完整的XML结构和命名空间）
    timestamp = int(time.time() * 1000)
    sheet_id = generate_id()
    theme_id = generate_id()
    content_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<xmap-content xmlns="urn:xmind:xmap:xmlns:content:2.0" xmlns:fo="http://www.w3.org/1999/XSL/Format" xmlns:svg="http://www.w3.org/2000/svg" xmlns:xhtml="http://www.w3.org/1999/xhtml" xmlns:xlink="http://www.w3.org/1999/xlink" modified-by="system" timestamp="{timestamp}" version="2.0">
<sheet id="{sheet_id}" modified-by="system" theme="{theme_id}" timestamp="{timestamp}">
<topic id="{root_topic['id']}" modified-by="system" structure-class="org.xmind.ui.logic.right" timestamp="{timestamp}">
<title>{root_topic['title']}</title>
</topic>
</sheet>
</xmap-content>'''
    
    # 创建ZIP文件
    # 使用绝对路径（通过Path对象处理），写入ZIP时转换为字符串
    with zipfile.ZipFile(str(output_file), 'w', zipfile.ZIP_DEFLATED) as zf:
        # content.json必须是数组格式，使用ensure_ascii=False确保中文正确显示
        zf.writestr('content.json', json.dumps([content_data], ensure_ascii=False, indent=2))
        zf.writestr('metadata.json', json.dumps({}, ensure_ascii=False))
        zf.writestr('manifest.json', json.dumps({"file-entries":{"content.json":{},"metadata.json":{}}}, ensure_ascii=False))
        zf.writestr('content.xml', content_xml)  # 使用完整的XML格式，确保xmind能正常打开
    
    print(f"XMind文件已生成: {output_file}")


def validate_topic_data(topic_data, path="root"):
    """
    验证 topic_data 结构是否正确（所有值必须是字典类型，不能是字符串）
    
    Args:
        topic_data: 要验证的主题数据
        path: 当前路径（用于错误提示）
    
    Raises:
        ValueError: 如果结构不正确（包含字符串值）
    """
    if not isinstance(topic_data, dict):
        raise ValueError(f"topic_data 必须是字典类型，但在路径 '{path}' 处发现 {type(topic_data).__name__}")
    
    for key, value in topic_data.items():
        current_path = f"{path}.{key}" if path != "root" else key
        if not isinstance(value, dict):
            raise ValueError(
                f"topic_data 中所有值必须是字典类型（即使是空字典 {{}}），"
                f"但在路径 '{current_path}' 处发现 {type(value).__name__}: {repr(value)}\n"
                f"请将 '{current_path}' 的值改为空对象 {{}}"
            )
        # 递归验证子节点
        if value:  # 如果字典不为空，继续验证
            validate_topic_data(value, current_path)


def load_analysis_content(content_file: str) -> tuple:
    """
    从内容文件加载测试分析结构（供「格式层」使用，内容由 AI/用户填写）
    
    Args:
        content_file: JSON 文件路径，格式为 {"title": "根标题", "topic_data": {...}}
    
    Returns:
        (title, topic_data) 元组
    
    Raises:
        FileNotFoundError, ValueError, json.JSONDecodeError
    """
    path = ensure_absolute_path(content_file, "内容文件路径")
    if not path.exists():
        raise FileNotFoundError(f"内容文件不存在: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    title = data.get('title') or 'Test Analysis'
    topic_data = data.get('topic_data')
    if topic_data is None:
        raise ValueError("内容文件必须包含 topic_data 字段")
    
    # 验证 topic_data 结构是否正确（所有值必须是字典类型，不能是字符串）
    try:
        validate_topic_data(topic_data)
    except ValueError as e:
        raise ValueError(f"test_analysis_content.json 格式错误: {e}")
    
    return title, topic_data


def main():
    """命令行入口：支持 --content/--output（内容驱动）或 位置参数（向后兼容）"""
    parser = argparse.ArgumentParser(
        description='生成 XMind 文件（格式层：仅根据内容生成格式，内容由外部提供）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例（内容文件驱动，推荐）:
  python generate_xmind.py --content test_analysis_content.json --output test_analysis-requiret.xmind

示例（向后兼容）:
  python generate_xmind.py "d:/out/test.xmind" "测试分析" '{"功能测试": {}, "性能测试": {}}'
"""
    )
    parser.add_argument('--content', '-c', help='测试分析内容 JSON 文件路径，格式见 SKILL 文档')
    parser.add_argument('--output', '-o', help='输出的 .xmind 文件路径（与 --content 同时使用）')
    parser.add_argument('output_path', nargs='?', help='[向后兼容] 输出文件路径')
    parser.add_argument('root_title', nargs='?', help='[向后兼容] 根主题标题')
    parser.add_argument('topic_data_json', nargs='?', help='[向后兼容] topic_data 的 JSON 字符串')
    args = parser.parse_args()

    if args.content and args.output:
        # 内容文件驱动：只做格式
        try:
            output_path = str(ensure_absolute_path(args.output, "输出文件路径"))
            title, topic_data = load_analysis_content(args.content)
            generate_xmind(output_path, title, topic_data)
        except Exception as e:
            print(f"错误: {e}", file=sys.stderr)
            sys.exit(1)
        return

    if args.content and not args.output:
        print("错误: 使用 --content 时必须同时指定 --output", file=sys.stderr)
        sys.exit(1)

    # 向后兼容：位置参数
    if not args.output_path or not args.root_title:
        print("用法: python generate_xmind.py --content <内容.json> --output <out.xmind>")
        print("  或: python generate_xmind.py <output_path> <root_title> [topic_data_json]")
        sys.exit(1)

    output_path = args.output_path
    root_title = args.root_title
    topic_data = None
    if args.topic_data_json:
        try:
            topic_data = json.loads(args.topic_data_json)
        except json.JSONDecodeError as e:
            print(f"错误: 无法解析 topic_data JSON: {e}", file=sys.stderr)
            sys.exit(1)

    try:
        output_path = str(ensure_absolute_path(output_path, "输出文件路径"))
        generate_xmind(output_path, root_title, topic_data)
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
