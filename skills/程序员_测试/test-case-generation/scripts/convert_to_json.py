#!/usr/bin/env python3
"""
测试用例JSON格式转换脚本

将Markdown表格格式的测试用例转换为符合Blade系统要求的JSON格式。

使用方法：
    python convert_to_json.py <markdown_file> <output_json_file> [options]

示例：
    python convert_to_json.py "测试用例.md" "测试用例.json" --api-token "token" --account "account" --node-path "/测试/功能测试"
"""

import json
import re
import sys
import os
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# 导入配置工具（处理相对导入）
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

try:
    from config_utils import get_precondition_key
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False


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


def parse_markdown_table(content: str) -> List[Dict[str, str]]:
    """
    解析Markdown表格内容
    
    Args:
        content: Markdown文件内容
    
    Returns:
        测试用例列表，每个用例是一个字典
    """
    test_cases = []
    
    # 匹配Markdown表格
    table_pattern = r'\|(.+)\|\s*\n\|[-\s\|]+\|\s*\n((?:\|.+\|\s*\n?)+)'
    matches = re.finditer(table_pattern, content, re.MULTILINE)
    
    for match in matches:
        headers = [h.strip() for h in match.group(1).split('|') if h.strip()]
        rows = match.group(2).strip().split('\n')
        
        for row in rows:
            if not row.strip():
                continue
            
            cells = [c.strip() for c in row.split('|') if c.strip()]
            if len(cells) < len(headers):
                continue
            
            case = {}
            for i, header in enumerate(headers):
                if i < len(cells):
                    # 处理HTML换行标签
                    value = cells[i].replace('<br>', '\n').replace('<br/>', '\n')
                    case[header] = value
            
            if case:
                test_cases.append(case)
    
    return test_cases


def infer_case_priority(case_name: str, case_content: str = "") -> str:
    """
    根据用例名称和内容智能推断优先级
    
    Args:
        case_name: 用例名称
        case_content: 用例内容（步骤描述+预期结果）
    
    Returns:
        优先级字符串：P0（高）、P1（中）、P2（低）、P3（极低），默认为P0
    """
    case_name_lower = case_name.lower()
    case_content_lower = (case_name + " " + case_content).lower()
    
    # P0（高）：正常场景、核心功能、安全测试
    if any(keyword in case_name_lower for keyword in ['正常', '正确', '成功', '核心', '主要', 'sql注入', 'xss', '安全']):
        return 'P0'
    
    # P1（中）：边界测试、特殊字符
    if any(keyword in case_name_lower for keyword in ['边界', '特殊字符', '长度']):
        return 'P1'
    
    # P2（低）：异常场景、错误处理
    if any(keyword in case_name_lower for keyword in ['异常', '错误', '失败', '空', '无效']):
        return 'P2'
    
    # P3（极低）：连续错误、极端场景
    if any(keyword in case_name_lower for keyword in ['连续', '多次', '极端']):
        return 'P3'
    
    # 默认为P0
    return 'P0'


def infer_case_side_type(case_name: str, case_content: str = "") -> str:
    """
    根据用例名称和内容智能推断正反用例类型
    
    Args:
        case_name: 用例名称
        case_content: 用例内容（步骤描述+预期结果）
    
    Returns:
        正反用例类型：0（正用例）、1（反用例），默认为0
    """
    case_name_lower = case_name.lower()
    case_content_lower = (case_name + " " + case_content).lower()
    
    # 反用例：异常、错误、失败、空值、无效、注入、攻击
    if any(keyword in case_name_lower for keyword in ['异常', '错误', '失败', '空', '无效', '注入', '攻击', '错误密码', '错误用户名']):
        return '1'
    
    # 正用例：正常、正确、成功
    return '0'


def infer_case_detail_type(case_name: str, case_content: str = "") -> str:
    """
    根据用例名称和内容智能推断用例细分类型
    
    Args:
        case_name: 用例名称
        case_content: 用例内容（步骤描述+预期结果）
    
    Returns:
        用例细分类型：0（功能）、1（性能）、2（文档）、3（安全）、4（兼容性）、5（可靠性）、6（用户体验）、7（安装部署），默认为0
    """
    case_name_lower = case_name.lower()
    case_content_lower = (case_name + " " + case_content).lower()
    
    # 安全测试：SQL注入、XSS攻击、安全
    if any(keyword in case_name_lower for keyword in ['sql注入', 'xss', '安全', '攻击', '注入']):
        return '3'
    
    # 性能测试：性能、速度、响应时间
    if any(keyword in case_name_lower for keyword in ['性能', '速度', '响应时间', '并发']):
        return '1'
    
    # 兼容性测试：兼容性、浏览器、设备
    if any(keyword in case_name_lower for keyword in ['兼容性', '浏览器', '设备', '平台']):
        return '4'
    
    # 可靠性测试：可靠性、稳定性、容错
    if any(keyword in case_name_lower for keyword in ['可靠性', '稳定性', '容错', '连续']):
        return '5'
    
    # 用户体验测试：用户体验、界面、交互
    if any(keyword in case_name_lower for keyword in ['用户体验', '界面', '交互', 'ui', 'ux']):
        return '6'
    
    # 安装部署测试：安装、部署、配置
    if any(keyword in case_name_lower for keyword in ['安装', '部署', '配置', '环境']):
        return '7'
    
    # 文档测试：文档、帮助、说明
    if any(keyword in case_name_lower for keyword in ['文档', '帮助', '说明', '手册']):
        return '2'
    
    # 默认为功能测试
    return '0'


def convert_case_to_json(
    case: Dict[str, str],
    case_index: int,
    default_values: Optional[Dict[str, Any]] = None,
    account: Optional[str] = None,
    precondition_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    将单个测试用例转换为JSON格式
    
    Args:
        case: 测试用例字典（从Markdown表格解析）
        case_index: 用例索引（用于生成用例编号）
        default_values: 默认值字典
        account: 账号（用于设置caseHeader字段，负责人）
        precondition_key: 前置条件字段名（Blade 步骤中前置条件的 key），不传则从配置或默认值获取
    
    Returns:
        符合Blade系统要求的JSON格式用例对象
    """
    if default_values is None:
        default_values = {}
    
    # 解析步骤描述、预期结果和前置条件
    step_descriptions = []
    expected_results = []
    preconditions_str = ""
    
    # 前置条件是用例级别的，所有步骤共享，只放在第一个步骤中
    # 如果Markdown表格中有"前置条件"列，将所有前置条件合并为一个字符串
    if '前置条件' in case:
        preconditions_list = [s.strip() for s in case['前置条件'].replace('<br>', '\n').replace('<br/>', '\n').split('\n') if s.strip()]
        # 将所有前置条件合并，使用换行符分隔
        preconditions_str = '\n'.join(preconditions_list)
    
    if '步骤描述' in case:
        # 处理步骤描述，支持<br>标签和换行符
        step_des_text = case['步骤描述'].replace('<br>', '\n').replace('<br/>', '\n')
        step_descriptions = [s.strip() for s in step_des_text.split('\n') if s.strip()]
    
    if '预期结果' in case:
        # 处理预期结果，支持<br>标签和换行符
        expect_text = case['预期结果'].replace('<br>', '\n').replace('<br/>', '\n')
        expected_results = [e.strip() for e in expect_text.split('\n') if e.strip()]
    
    # 构建步骤数组（使用嵌套的stepJson结构）
    steps = []
    max_steps = max(len(step_descriptions), len(expected_results))
    
    # 获取前置条件字段名：优先使用传入值，否则从 config 或默认值获取
    if precondition_key is None or precondition_key == '':
        if CONFIG_AVAILABLE:
            try:
                precondition_key = get_precondition_key()
            except Exception:
                precondition_key = 'user_key_c808a8ed36781fe8de3d8ff'  # 默认值
        else:
            precondition_key = 'user_key_c808a8ed36781fe8de3d8ff'  # 默认值
    
    # 如果没有步骤，步骤数组可以为空
    if max_steps == 0:
        steps = []
    else:
        for i in range(max_steps):
            step_des = step_descriptions[i] if i < len(step_descriptions) else ""
            expect = expected_results[i] if i < len(expected_results) else ""
            
            # 构建步骤JSON（嵌套结构：stepName + stepJson）
            step_json = {
                "stepDes": step_des,  # 步骤描述
                "Expect": expect,  # 步骤期望
            }
            
            # 前置条件是用例级别的，所有步骤共享，只放在第一个步骤中
            # 只有第一个步骤（i == 0）才包含前置条件
            if i == 0 and preconditions_str:
                step_json[precondition_key] = preconditions_str
            
            # 构建步骤对象（嵌套结构）
            step_obj = {
                "stepName": f"用例步骤-{i+1}",  # 用例步骤名称
                "stepJson": step_json  # 步骤JSON对象
            }
            
            steps.append(step_obj)
    
    # 获取用例名称和内容，用于智能推断
    case_name = case.get('用例名称', f"测试用例-{case_index+1}")
    case_content = case.get('步骤描述', '') + ' ' + case.get('预期结果', '')
    
    # 智能推断优先级、正反用例类型、用例细分类型
    # 优先级：如果Markdown表格中有"优先级"列，优先使用；否则智能推断；最后使用默认值
    priority = case.get('优先级', '').strip()
    if not priority:
        priority = infer_case_priority(case_name, case_content)
        if default_values and 'casePrior' in default_values:
            priority = default_values.get('casePrior', priority)
    else:
        # 如果表格中有优先级，使用表格中的值
        pass
    
    # 正反用例类型：如果Markdown表格中有"正反用例类型"列，优先使用；否则智能推断；最后使用默认值
    side_type = case.get('正反用例类型', '').strip()
    if not side_type:
        side_type = infer_case_side_type(case_name, case_content)
        if default_values and 'caseSideType' in default_values:
            side_type = default_values.get('caseSideType', side_type)
    else:
        # 如果表格中有正反用例类型，使用表格中的值
        pass
    
    # 用例细分类型：如果Markdown表格中有"用例细分类型"列，优先使用；否则智能推断；最后使用默认值
    detail_type = case.get('用例细分类型', '').strip()
    if not detail_type:
        detail_type = infer_case_detail_type(case_name, case_content)
        if default_values and 'caseDetailType' in default_values:
            detail_type = default_values.get('caseDetailType', detail_type)
    else:
        # 如果表格中有用例细分类型，使用表格中的值
        pass
    
    # 构建用例对象（只包含必填字段和需要动态调整的字段）
    json_case = {
        # 必填字段
        "caseName": case_name,  # 必填：用例名称
        "caseType": "1",  # 必填：用例类型（1：手工；2：自动化），固定为1，无需修改
        "caseState": "1",  # 必填：用例状态，默认就是1：已启用，无需修改
        "caseLayer": "1",  # 必填：用例分层，1：模块级，无需修改
        'caseKeyword': "AIGC",   # 必填：标签名，默认为 AIGC

        
        # 需要动态调整的字段（智能推断）
        "casePrior": priority,  # 优先级（P0：高；P1：中；P2：低；P3：极低；为空默认为P0）
        "caseSideType": side_type,  # 正反用例类型（0：正；1：反；为空默认为0）
        "caseDetailType": detail_type,  # 用例细分类型（0：功能；1：性能；2：文档；3：安全；4：兼容性；5：可靠性；6：用户体验；7：安装部署；默认为0）
        
        # 步骤数组（必填）
        "step": steps  # 步骤数组，如果没有步骤可以为空数组
    }
    
    # 添加可选字段：负责人（使用account）
    if account:
        json_case["caseHeader"] = account
    
    # 添加可选字段：用例描述
    if '用例描述' in case and case.get('用例描述'):
        json_case["caseDesc"] = case['用例描述'].strip()
    
    # 可选字段：如果存在则添加
    # 注意：caseNo字段可能导致格式错误，暂时注释掉
    # case_no = case.get('用例编号', '')
    # if case_no:
    #     # 去掉前缀C或TC（如果存在）
    #     if case_no.startswith('C'):
    #         case_no = case_no[1:]
    #     elif case_no.startswith('TC'):
    #         case_no = case_no[2:]
    #     json_case["caseNo"] = case_no
    
    return json_case


def convert_test_cases_to_json(
    markdown_file: str,
    api_token: str,
    account: str,
    node_path: str,
    output_file: Optional[str] = None,
    default_values: Optional[Dict[str, Any]] = None,
    xn_product_id: Optional[str] = None,
    precondition_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    将Markdown格式的测试用例转换为JSON格式
    
    Args:
        markdown_file: Markdown文件路径（必须是绝对路径）
        api_token: API token（必填，200字符）
        account: 账号（必填，20字符）
        node_path: 节点路径（可选，128字符，URL编码）
        output_file: 输出JSON文件路径（可选，必须是绝对路径）
        default_values: 默认值字典
        xn_product_id: 效能平台项目Id（可选，100字符，多项目必填）
        precondition_key: 前置条件字段名（按产品配置，不传则从 config 读取）
    
    Returns:
        完整的JSON数据对象
    """
    # 强制使用绝对路径处理，避免Windows中文路径编码问题
    md_path = ensure_absolute_path(markdown_file, "Markdown文件路径")
    if not md_path.exists():
        raise FileNotFoundError(f"Markdown文件不存在: {md_path}")
    
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 解析Markdown表格
    test_cases = parse_markdown_table(content)
    
    if not test_cases:
        raise ValueError("未找到有效的测试用例表格")
    
    # 转换为JSON格式
    json_cases = []
    for i, case in enumerate(test_cases):
        json_case = convert_case_to_json(case, i, default_values, account, precondition_key=precondition_key)
        json_cases.append(json_case)
    
    # 构建完整的JSON结构（按照API规范）
    json_data = {
        "account": account,  # 必填，String，20字符
        "api_token": api_token,  # 必填，String，200字符
        "xnProductId": xn_product_id or "",  # 可选，String，100字符，多项目必填
        "nodePath": node_path,  # 可选，string，128字符，URL编码
        "data": json_cases  # 用例数组
    }
    
    # 如果xnProductId为空字符串，可以移除该字段（可选字段）
    if not json_data["xnProductId"]:
        del json_data["xnProductId"]
    
    # 保存到文件（强制使用绝对路径处理，避免Windows中文路径编码问题）
    if output_file:
        output_path = ensure_absolute_path(output_file, "输出JSON文件路径")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        print(f"JSON文件已生成: {output_path}")
    
    return json_data


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description='将Markdown测试用例转换为JSON格式',
        epilog='注意：所有文件路径参数必须是绝对路径，以避免Windows中文路径编码问题。'
    )
    parser.add_argument('markdown_file', help='Markdown测试用例文件路径（必须是绝对路径）')
    parser.add_argument('output_file', help='输出JSON文件路径（必须是绝对路径）')
    parser.add_argument('--api-token', required=True, help='API token（必填，200字符）')
    parser.add_argument('--account', required=True, help='账号（必填，20字符）')
    parser.add_argument('--node-path', help='节点路径，如 /账号/功能测试（可选，128字符）')
    parser.add_argument('--xn-product-id', help='效能平台项目Id（可选，100字符，多项目必填）')
    parser.add_argument('--case-type', default='1', help='用例类型（默认：1-手工，2-自动化）')
    parser.add_argument('--case-state', default='1', help='用例状态（默认：1-已启用，0-待设计，2-设计中，3-已废弃）')
    parser.add_argument('--case-prior', default='P2', help='优先级（默认：P2，可选：P0/P1/P2/P3）')
    parser.add_argument('--case-side-type', default='0', help='正反用例类型（默认：0-正用例，1-反用例）')
    parser.add_argument('--case-detail-type', default='0', help='用例细分类型（默认：0-功能，1-性能，2-文档，3-安全，4-兼容性，5-可靠性，6-用户体验，7-安装部署）')
    parser.add_argument('--template-name', default='项目默认模板', help='模板名称')
    
    args = parser.parse_args()
    
    default_values = {
        # 固定值字段（无需修改）
        'caseType': "1",
        'caseState': "1",
        'caseLayer': "1",
        'caseKeyword': "AIGC",   # 必填：标签名，默认为 AIGC

        
        # 需要动态调整的字段
        'casePrior': args.case_prior,  # 优先级，默认P2，可动态调整
        'caseSideType': args.case_side_type,  # 正反用例类型，默认0（正用例），可动态调整
        'caseDetailType': args.case_detail_type,  # 用例细分类型，默认0（功能），可动态调整
        
        # 可选字段
        'caseHeader': args.account  # 负责人，使用账号
        # 'templateName': args.template_name  # 注释掉，避免格式错误
    }
    
    # 节点路径默认值
    if not args.node_path:
        args.node_path = f"/{args.account}/功能测试"
    
    try:
        # 强制转换为绝对路径
        markdown_file = str(ensure_absolute_path(args.markdown_file, "Markdown文件路径"))
        output_file = str(ensure_absolute_path(args.output_file, "输出JSON文件路径"))
        
        convert_test_cases_to_json(
            markdown_file=markdown_file,
            api_token=args.api_token,
            account=args.account,
            node_path=args.node_path,
            output_file=output_file,
            default_values=default_values,
            xn_product_id=args.xn_product_id
        )
    except ValueError as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
