#!/usr/bin/env python3
"""
从需求文档生成测试交付物主脚本

基于内容文件（test_analysis_content.json、test_cases_content.json）生成：
1. 测试分析（XMind 格式）
2. 测试用例（Markdown 格式）
3. 测试用例（JSON 格式）

工作流：
    - 前置：先读需求文档，再读 pre_docs/<产品名>/context 参考示例（--product 时加载）
    - 后置：AI 生成 test_cases_content.json 后按 post_docs 校验；不通过则修改后用 --post-check-only 重试，通过后脚本直接生成交付物
    - 自动清理：仅在上传成功后删除中间产物；未使用上传或上传失败时保留，便于重试

用法：
    python generate_from_requirement.py <需求文档路径> [选项]

示例：
    python generate_from_requirement.py "<your_workspace>/requirement.txt"
    python generate_from_requirement.py "<your_workspace>/requirement.txt" --output-dir "<your_workspace>/output" --upload
    # 后置校验失败时，AI 修改后仅运行校验（不生成交付物）：
    python generate_from_requirement.py "<your_workspace>/requirement.txt" --output-dir "<your_workspace>/output" --product HUI --post-check-only

注意：
    - 路径须为绝对路径、英文路径，详见「路径处理和编码要求」
    - 首次使用前运行 setup_config.py 配置 API token 和账号
"""

import sys
import os
import argparse
import json
import subprocess
import re
import time
from pathlib import Path
from typing import Optional

# 设置脚本目录路径（用于导入其他脚本）
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)


def sanitize_filename(filename: str) -> str:
    """
    将文件名转换为英文（中文字符替换为下划线），避免 PowerShell 编码问题。
    转换后为空则返回 'requirement'。
    """
    # 如果文件名已经是英文或数字，直接返回
    if re.match(r'^[a-zA-Z0-9_\-\.]+$', filename):
        return filename
    
    # 简单的转换规则：将常见的中文字符映射为英文
    # 如果包含中文，使用通用的英文命名
    if any('\u4e00' <= char <= '\u9fff' for char in filename):
        # 将中文替换为下划线，然后清理
        sanitized = re.sub(r'[^\w\-_\.]', '_', filename)
        sanitized = re.sub(r'_+', '_', sanitized)  # 合并多个下划线
        sanitized = sanitized.strip('_')  # 移除首尾下划线
        
        # 如果转换后为空，使用默认名称
        if not sanitized:
            sanitized = 'requirement'
        
        return sanitized
    
    # 移除特殊字符，只保留字母、数字、下划线、连字符和点
    sanitized = re.sub(r'[^\w\-_\.]', '_', filename)
    sanitized = re.sub(r'_+', '_', sanitized)
    sanitized = sanitized.strip('_')
    
    return sanitized if sanitized else 'requirement'


def ensure_absolute_path(path_str: str, description: str = "路径") -> Path:
    """
    强制将路径转换为绝对路径并验证。路径须为绝对路径、英文路径，见 SKILL 文档。
    Raises ValueError: 路径为空或无效。
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

from generate_xmind import generate_xmind, load_analysis_content
from convert_to_json import convert_test_cases_to_json, infer_case_priority, infer_case_side_type, infer_case_detail_type

try:
    from upload_to_blade import upload_test_cases
    UPLOAD_AVAILABLE = True
except ImportError:
    UPLOAD_AVAILABLE = False

try:
    from upload_analysis_to_blade import upload_analysis_json
    ANALYSIS_UPLOAD_AVAILABLE = True
except ImportError:
    ANALYSIS_UPLOAD_AVAILABLE = False

try:
    from config_utils import (
        get_api_token, get_account, get_node_path, get_pre_docs_dir, get_post_docs_dir,
        get_precondition_key, load_config, get_config_path,
    )
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    get_pre_docs_dir = None
    get_post_docs_dir = None
    get_precondition_key = None
    load_config = None
    get_config_path = None

# Blade系统API地址（固定值，不再从配置读取）
BLADE_API_URL = 'https://blade.hundsun.com/openapi/design/importOfflineCase.json'


def _public_config_path_fallback() -> Path:
    """与 config_utils.get_config_path 一致（无法导入 config_utils 时）。"""
    override = os.environ.get("TEST_CASE_GENERATION_PUBLIC", "").strip()
    if override:
        return Path(override) / "config.json"
    skill = Path(script_dir).resolve().parent
    return skill.parent.parent.parent / "public" / "config.json"


def resolve_public_config_path() -> Path:
    if CONFIG_AVAILABLE and get_config_path:
        return get_config_path()
    return _public_config_path_fallback()


def workspace_root_from_script() -> Path:
    """scripts -> 技能包 -> skills -> 中间目录 -> 工作区根。"""
    return Path(script_dir).resolve().parent.parent.parent.parent


def is_interactive():
    """检查是否在交互式环境中"""
    return sys.stdin.isatty() and sys.stdout.isatty()


def check_and_setup_config():
    """
    检查 config.json 是否存在且含 API token、账号。不存在则交互式询问是否配置。
    Returns: True 配置有效，False 不存在或信息不完整。
    """
    config_path = resolve_public_config_path()
    
    # 检查配置文件是否存在
    if not config_path.exists():
        print("\n" + "=" * 60)
        print("警告: 检测到未配置API token和账号")
        print("=" * 60)
        print("\n为了生成JSON格式的测试用例并上传到Blade系统，需要先配置：")
        print("  - API Token")
        print("  - 账号（节点路径会根据账号自动生成）")
        print()
        
        # 检查是否在交互式环境中
        if not is_interactive():
            print("警告: 当前为非交互式环境，无法自动配置")
            print(f"提示：请编辑工作区配置文件（当前路径）：\n  {config_path}\n或运行 'python scripts/setup_config.py' 进行配置")
            return False
        
        # 询问是否现在配置
        try:
            response = input("是否现在进行配置？(y/n，默认y): ").strip().lower()
            if response == '' or response == 'y':
                print("\n正在启动配置向导...")
                print("=" * 60)
                
                # 调用配置脚本
                setup_script = Path(script_dir) / 'setup_config.py'
                result = subprocess.run(
                    [sys.executable, str(setup_script)],
                    cwd=str(workspace_root_from_script()),
                )
                
                if result.returncode == 0:
                    print("\n配置完成！")
                    # 重新检查配置（支持 default 与 product 结构）
                    if config_path.exists() and CONFIG_AVAILABLE:
                        try:
                            cfg = load_config(product=None)
                            if cfg.get('api_token') and cfg.get('account'):
                                return True
                        except Exception:
                            pass
                    print("警告: 配置未保存或信息不完整，将使用默认值继续生成")
                    return False
                else:
                    print("警告: 配置过程中出现错误，将使用默认值继续生成")
                    return False
            else:
                print("已跳过配置，将使用默认值生成JSON文件")
                print(f"提示：可以稍后编辑工作区配置文件：\n  {config_path}\n或运行 'python scripts/setup_config.py' 进行配置")
                return False
        except (KeyboardInterrupt, EOFError):
            print("\n\n已取消配置，将使用默认值继续生成")
            return False
        except Exception as e:
            print(f"\n警告: 启动配置脚本时出错: {e}")
            print("将使用默认值继续生成")
            return False
    
    # 检查配置是否完整（支持 default 与 product 结构）
    try:
        if CONFIG_AVAILABLE:
            config = load_config(product=None)
        else:
            with open(config_path, 'r', encoding='utf-8') as f:
                raw = json.load(f)
            config = raw.get('default', raw) if isinstance(raw.get('default'), dict) else raw
        if not config.get('api_token') or not config.get('account'):
            print("\n警告: 配置文件存在但缺少必要信息（API token或账号）")
            print(f"提示：请编辑工作区配置文件，确保 default 或顶层包含 api_token、account：\n  {config_path}")
            return False
        return True
    except Exception as e:
        print(f"\n警告: 读取配置文件时出错: {e}")
        return False


def summarize_requirement_content(content: str, max_chars: int = 50) -> str:
    """
    从需求文档内容生成简短摘要（≤max_chars）。优先从【产品目标】等字段提取，否则取首条非标题行。
    """
    if not (content and content.strip()):
        return ''
    lines = [s.strip() for s in content.split('\n') if s.strip()]
    # 仅保留有意义的行（去掉纯标题行、过短行）
    skip_titles = {'客户', '版本', '需求背景', '实现目标', '客户要求', '非功能性需求', '是否已通过需求自检'}
    # 优先从带冒号的字段行提取（产品目标、业务所期待解决的问题、目标、业务背景等）
    for line in lines:
        for marker in ('【产品目标】', '【业务所期待解决的问题】', '【目标】', '【产品背景】', '*【目标】', '*【业务背景】', '*【业务所期待解决的问题】'):
            if marker in line:
                idx = line.find('：') if '：' in line else line.find(':')
                if idx != -1:
                    text = line[idx + 1:].strip().lstrip('*').strip()
                    if text and len(text) >= 2:
                        # 去掉首尾方括号等，取前 max_chars 字
                        for c in '【】':
                            text = text.replace(c, '')
                        if text:
                            return text[:max_chars]
    # 否则取首条非标题、长度≥2 的实质性内容行并截断
    for line in lines:
        if line in skip_titles or len(line) < 2:
            continue
        if line.startswith('*【') or line.startswith('【'):
            idx = line.find('：') if '：' in line else line.find(':')
            if idx != -1:
                text = line[idx + 1:].strip().lstrip('*').strip()
                for c in '【】':
                    text = text.replace(c, '')
                if text and len(text) >= 2:
                    return text[:max_chars]
        else:
            return line[:max_chars]
    return ''


def parse_requirement_document(requirement_file: str) -> dict:
    """
    解析需求文档，提取 title（内容摘要≤25 字符，若无则用文件名）、content、file_path。
    """
    # 强制使用绝对路径处理，避免Windows中文路径编码问题
    req_path = ensure_absolute_path(requirement_file, "需求文档路径")
    if not req_path.exists():
        raise FileNotFoundError(f"需求文档不存在: {req_path}")
    
    with open(req_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    summary = summarize_requirement_content(content, max_chars=25)
    title = summary if summary else req_path.stem
    
    requirement_info = {
        'title': title,
        'content': content,
        'file_path': str(req_path)
    }
    
    return requirement_info


def _split_lines(text: str) -> list:
    """按行分割并过滤空行，保留非空行的 strip 结果。"""
    return [s.strip() for s in (text or '').split('\n') if s.strip()]


def normalize_steps_expects_count(steps: str, expects: str, case_name: str = "") -> tuple:
    """
    将步骤与预期结果数量对齐（预期多于步骤则合并，少于则用最后一条补齐）。
    Returns: (steps, expects) 元组，行数已一致。
    """
    step_list = _split_lines(steps)
    expect_list = _split_lines(expects)
    ns = len(step_list)
    ne = len(expect_list)
    if ns == ne:
        return steps, expects
    if ns == 0 and ne == 0:
        return steps, expects
    if ns == 0:
        step_list = ['']
        ns = 1
    if ne == 0:
        expect_list = ['同上']
        ne = 1
    if ne > ns:
        merged_last = '；'.join(expect_list[ns - 1:])
        expect_list = expect_list[: ns - 1] + [merged_last]
        expects_out = '\n'.join(expect_list)
        print(f"校验并修正: 用例「{case_name}」预期结果多于步骤({ne}>{ns})，已合并为{ns}条。")
        return steps, expects_out
    else:
        last_expect = expect_list[-1] if expect_list else '同上'
        expect_list = expect_list + [last_expect] * (ns - ne)
        expects_out = '\n'.join(expect_list)
        print(f"校验并修正: 用例「{case_name}」预期结果少于步骤({ne}<{ns})，已用最后一条补齐为{ns}条。")
        return steps, expects_out


def validate_steps_expects_match(steps: str, expects: str, case_name: str = "") -> tuple:
    """验证步骤与预期结果数量一致，不一致则抛出 ValueError。"""
    step_list = _split_lines(steps)
    expect_list = _split_lines(expects)
    if len(step_list) != len(expect_list):
        error_msg = f"用例 '{case_name}' 的步骤描述数量({len(step_list)})与预期结果数量({len(expect_list)})不匹配"
        if case_name:
            error_msg += f"\n  步骤描述: {step_list}"
            error_msg += f"\n  预期结果: {expect_list}"
        raise ValueError(error_msg)
    return steps, expects


def load_cases_content(cases_content_path: str) -> tuple:
    """
    从 test_cases_content.json 加载用例列表（内容由 AI/用户填写，脚本只做格式）。

    Returns:
        (requirement_title, cases_list)。cases_list 每项含 case_name, priority, precondition, steps, expects 等。
    """
    path = ensure_absolute_path(cases_content_path, "内容文件路径")
    if not path.exists():
        raise FileNotFoundError(f"内容文件不存在: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    cases = data.get('cases')
    if not cases or not isinstance(cases, list):
        raise ValueError("内容文件必须包含 cases 数组且非空")
    requirement_title = data.get('requirement_title') or 'requirement'
    normalized = []
    for i, c in enumerate(cases):
        pre = c.get('precondition', '')
        steps = c.get('steps', '')
        expects = c.get('expects', '')
        if isinstance(pre, list):
            pre = '\n'.join(str(x) for x in pre)
        if isinstance(steps, list):
            steps = '\n'.join(str(x) for x in steps)
        if isinstance(expects, list):
            expects = '\n'.join(str(x) for x in expects)
        case_name = c.get('case_name') or f'用例{i+1}'
        # 生成时自动校验并修正步骤与预期结果数量，避免静默跳过用例
        steps, expects = normalize_steps_expects_count(steps, expects, case_name)
        normalized.append({
            'case_name': case_name,
            'priority': c.get('priority', 'P0'),
            'side_type': c.get('side_type', '0'),
            'detail_type': c.get('detail_type', '0'),
            'precondition': pre,
            'steps': steps,
            'expects': expects,
            'analysis_ref': (c.get('analysis_ref') or '').strip(),
        })
    return requirement_title, normalized


def generate_test_analysis_xmind_from_content(
    analysis_content_path: str, output_path: str, fallback_title: str
) -> tuple:
    """
    从 test_analysis_content.json 生成测试分析 XMind，并写出同标题的交付 JSON。

    Returns:
        (xmind_abs_path, analysis_json_abs_path 或 None)
    """
    output_dir = ensure_absolute_path(output_path, "输出目录路径")
    title, topic_data = load_analysis_content(analysis_content_path)
    title_en = sanitize_filename(fallback_title)
    analysis_json_path = output_dir / f"test_analysis-{title_en}.json"
    export_obj = {"title": title, "topic_data": topic_data}
    with open(analysis_json_path, "w", encoding="utf-8") as jf:
        json.dump(export_obj, jf, ensure_ascii=False, indent=2)
    xmind_path = output_dir / f"test_analysis-{title_en}.xmind"
    generate_xmind(str(xmind_path), title, topic_data)
    return str(xmind_path), str(analysis_json_path)


def _write_md_from_cases(test_cases: list, md_path: Path, doc_title: str, requirement_file_path: str = "") -> int:
    """根据用例列表写入 Markdown 表格（格式层），返回写入的用例行数。"""
    table_rows = []
    for i, case in enumerate(test_cases, 1):
        case_num = f"TC{i:03d}"
        case_name = case['case_name']
        steps_raw = case.get('steps', '')
        expects_raw = case.get('expects', '')
        # 加载时已做数量对齐，此处仅做最终校验；若仍不匹配则直接报错，不跳过用例
        validate_steps_expects_match(steps_raw, expects_raw, case_name)
        priority = case.get('priority') or infer_case_priority(case_name, steps_raw + " " + expects_raw)
        side_type = case.get('side_type') or infer_case_side_type(case_name, steps_raw + " " + expects_raw)
        detail_type = case.get('detail_type') or infer_case_detail_type(case_name, steps_raw + " " + expects_raw)
        precondition = (case.get('precondition') or '').replace('\n', '<br>')
        steps = steps_raw.replace('\n', '<br>')
        expects = expects_raw.replace('\n', '<br>')
        table_rows.append(f"| {case_num} | {case_name} | {priority} | {side_type} | {detail_type} | {precondition} | {steps} | {expects} |")
    body = f"""# 测试用例 - {doc_title}

## 测试用例列表

| 用例编号 | 用例名称 | 优先级 | 正反用例类型 | 用例细分类型 | 前置条件 | 步骤描述 | 预期结果 |
|---------|---------|--------|------------|------------|---------|---------|---------|
{chr(10).join(table_rows)}

## 字段说明

- **优先级**：P0（高）、P1（中）、P2（低）、P3（极低），为空默认为P0
- **正反用例类型**：0（正用例）、1（反用例），为空默认为0
- **用例细分类型**：0（功能）、1（性能）、2（文档）、3（安全）、4（兼容性）、5（可靠性）、6（用户体验）、7（安装部署），默认为0

## 说明

本测试用例由内容文件驱动生成，脚本只负责格式输出。

**需求文档**: {requirement_file_path or "(未指定)"}
"""
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(body)
    return len(table_rows)


def _parse_checklist_file(file_path: Path) -> dict:
    """解析 checklist 文件，返回 {section_name: [items]}"""
    result = {}
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except Exception:
        return result
    
    lines = content.split('\n')
    current_section = ""
    
    for line in lines:
        line = line.strip()
        if line.startswith('##'):
            current_section = line
            if current_section and current_section not in result:
                result[current_section] = []
        elif line.startswith('- ') and current_section:
            item = line[2:].strip()
            if current_section not in result:
                result[current_section] = []
            result[current_section].append(item)
    
    return result


def _merge_checklists(base: dict, product: dict) -> dict:
    """合并 checklist，产品优先级高于总清单（同章节以产品为准）"""
    merged = dict(base)
    for section, items in product.items():
        if items:  # 产品有该章节则覆盖
            merged[section] = items
    return merged


def _parse_special_checklist_table(file_path: Path) -> list:
    """
    解析 checklist 中的「专项检查项」表格，返回 [(场景, check项, 补充), ...]。
    表格格式：| 场景 | check 项 | 补充 check 点 |，↑ 表示沿用上一行的场景。
    """
    result = []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except Exception:
        return result

    lines = content.split('\n')
    in_table = False
    last_scene = ""
    header_skipped = False

    for line in lines:
        stripped = line.strip()
        if '专项检查项' in stripped and stripped.startswith('##'):
            in_table = True
            header_skipped = False
            continue
        if in_table and stripped.startswith('##'):
            break
        if not in_table:
            continue

        if stripped.startswith('|') and '---' not in stripped:
            parts = [p.strip() for p in stripped.split('|')]
            parts = [p for p in parts if p]
            if len(parts) >= 2:
                scene = parts[0] if parts[0] != '↑' else last_scene
                check_item = parts[1] if len(parts) > 1 else ''
                supplement = parts[2] if len(parts) > 2 else ''
                # 跳过表头行（场景列为「场景」或 check 列为「check 项」）
                if not header_skipped and (scene in ('场景', '') or 'check' in (check_item or '').lower()):
                    header_skipped = True
                    continue
                if scene and check_item:
                    last_scene = scene
                    result.append((scene, check_item, supplement))

    return result


def _parse_special_checklist_from_excel(file_path: Path) -> list:
    """
    从 Excel 文件解析专项检查项，返回 [(场景, check项, 补充), ...]。
    表格格式：第一行为表头（场景、check项、补充check点），空单元格表示沿用上一行。
    需要 openpyxl：pip install openpyxl
    """
    result = []
    try:
        import openpyxl
    except ImportError:
        return result
    try:
        wb = openpyxl.load_workbook(str(file_path), read_only=True, data_only=True)
        ws = wb.active
        last_scene = ""
        last_check_item = ""
        header_skipped = False
        for row in ws.iter_rows(values_only=True):
            row = [r for r in (row or [])]
            if len(row) < 2:
                continue
            scene = str(row[0]).strip() if row[0] is not None else ""
            check_item = str(row[1]).strip() if row[1] is not None else ""
            supplement = str(row[2]).strip() if len(row) > 2 and row[2] is not None else ""
            if not header_skipped:
                if scene in ("场景", "") or "check" in (check_item or "").lower():
                    header_skipped = True
                    continue
            scene = scene or last_scene
            check_item = check_item or last_check_item
            if scene and check_item:
                last_scene = scene
                last_check_item = check_item
                result.append((scene, check_item, supplement))
        wb.close()
    except Exception:
        pass
    return result


def _extract_tokens(text: str, min_len: int = 2, max_len: int = 8, stopwords: set = None) -> list:
    """
    从文本中动态提取有意义的词。用于触发词和必需关键词的生成。
    """
    if stopwords is None:
        stopwords = {'的', '是', '在', '时', '等', '不', '有', '和', '与', '或', '及', '若', '要', '能', '可'}
    tokens = []
    # 中文字符串
    for m in re.finditer(r'[\u4e00-\u9fff]+', text):
        w = m.group()
        if min_len <= len(w) <= max_len and w not in stopwords:
            tokens.append(w)
    # 英文词（含 ABA、radio、URL 等）
    for m in re.finditer(r'[a-zA-Z]{2,}[a-zA-Z0-9]*', text):
        tokens.append(m.group())
    return list(dict.fromkeys(tokens))


def _extract_trigger_and_required(scene: str, check_item: str, supplement: str) -> tuple:
    """
    从专项检查项中动态提取：触发词、必需关键词、apply_only_if。
    完全基于 checklist 文本内容，无硬编码规则。
    返回 (trigger_keywords: list, required_keywords: list, apply_only_if: str|None)
    """
    text = check_item + ' ' + supplement
    trigger = []
    required = []
    apply_only_if = None

    # 1. 触发词：从场景列动态提取有意义的词
    trigger = _extract_tokens(scene, min_len=2, max_len=8)
    # 场景中的英文/数字词（如 radio、URL、ABA）
    for m in re.finditer(r'[a-zA-Z]{2,}[a-zA-Z0-9]*', scene):
        w = m.group()
        if w not in trigger:
            trigger.append(w)
    # check项/补充 中若明确提到场景相关词（如 ABA、开关），也加入触发
    for m in re.finditer(r'(ABA|开关|打开|关闭|联动)', text):
        if m.group(1) not in trigger:
            trigger.append(m.group(1))

    # 2. apply_only_if：补充中「涉及X」时，仅当用例包含 X 才应用
    involve_m = re.search(r'涉及([^\s，。；、]{2,8})', supplement)
    if involve_m:
        apply_only_if = involve_m.group(1)

    # 3. 必需关键词：从 check项/补充 中动态提取
    # 模式：需要X、考虑X、包含X、X属性、X测试、X场景、X验证
    patterns = [
        r'需要[^，。；、\s]*?([^\s，。；、]{2,6})(?:属性|测试|场景|验证)?',
        r'考虑[^，。；、\s]*?([^\s，。；、]{2,6})(?:属性|测试|场景|验证)?',
        r'包含[^，。；、\s]*?([^\s，。；、]{2,6})',
        r'([^\s，。；、]{2,6})属性',
        r'([^\s，。；、]{2,6})测试',
        r'([^\s，。；、]{2,6})场景',
        r'([^\s，。；、]{2,6})验证',
        r'对于\s*([^\s，。；、]{2,8})',
        r'是否[^，。；、\s]*?([^\s，。；、]{2,6})',
    ]
    for pat in patterns:
        for m in re.finditer(pat, text):
            kw = m.group(1).strip()
            if len(kw) >= 2 and kw not in required:
                required.append(kw)

    # 4. 从「X、Y、Z」结构中提取并列的 2-4 字关键词（如：打开、关闭、禁用）
    generic = {'以及', '或者', '例如', '如不', '若有', '再次', '操作', '功能', '数据', '页面', '组件', '补充', '检查', '点'}
    for seg in re.split(r'[、,；;]', text):
        for m in re.finditer(r'([\u4e00-\u9fff]{2,4})', seg.strip()):
            w = m.group(1)
            if w not in required and w not in generic:
                required.append(w)

    # 5. 去重、过滤无效词并限制数量
    invalid = {'的', '是', '在', '时', '等', '不', '有', '和', '与', '或', '及', '若', '要', '能', '可', '需', '考虑'}
    required = [r for r in dict.fromkeys(required) if r not in invalid][:10]

    return trigger, required, apply_only_if


def _run_special_checks(cases: list, special_items: list) -> list:
    """
    根据专项检查项动态校验用例。当用例涉及某场景（包含触发词）时，必须包含对应必需关键词。
    返回缺失项列表。
    """
    missing = []

    def case_text(c):
        return (c.get('case_name', '') + ' ' + c.get('precondition', '') + ' ' +
                c.get('steps', '') + ' ' + c.get('expects', ''))

    all_text = ' '.join(case_text(c) for c in cases)
    all_text_lower = all_text.lower()

    for scene, check_item, supplement in special_items:
        trigger, required, apply_only_if = _extract_trigger_and_required(scene, check_item, supplement)
        if not trigger or not required:
            continue

        # 用例是否涉及该场景（大小写不敏感）
        scene_applies = any(t.lower() in all_text_lower for t in trigger)
        if not scene_applies:
            continue

        # 补充中「涉及X」时，仅当用例包含 X 才应用此检查
        if apply_only_if and apply_only_if not in all_text:
            continue

        # 用例是否包含任一必需关键词
        has_required = any(r in all_text for r in required)
        if not has_required:
            missing.append(f"专项检查: [{scene}] {check_item}，用例中未发现相关覆盖（建议包含: {', '.join(required[:5])}）")

    return missing


def run_post_check(cases: list, post_docs_root: Path, product_dir: Optional[Path] = None) -> tuple:
    """
    后置校验：根据 post_docs 要求检查用例，不通过则返回缺失项。

    先读总 checklist，产品有各自的则同章节以产品为准。

    Returns:
        (missing_items: list, report: str) 缺失项列表和报告文本
    """
    missing = []
    
    # 1. 读取总 checklist
    base_checklist_path = post_docs_root / 'checklist.md'
    base_data = _parse_checklist_file(base_checklist_path) if base_checklist_path.exists() else {}
    
    # 2. 读取产品「测试用例checklist」（固定文件名，优先 xlsx）；兼容旧名 checklist.md
    product_data = {}
    special_items = []
    if product_dir and product_dir.exists() and product_dir.is_dir():
        cases_xlsx = product_dir / "测试用例checklist.xlsx"
        cases_md = product_dir / "测试用例checklist.md"
        legacy_md = product_dir / "checklist.md"
        legacy_xlsx = [
            f for f in product_dir.iterdir()
            if f.is_file() and f.suffix.lower() == '.xlsx' and f.name != "测试分析checklist.xlsx"
        ]

        if cases_xlsx.exists():
            special_items = _parse_special_checklist_from_excel(cases_xlsx)
        elif legacy_xlsx:
            for cf in sorted(legacy_xlsx):
                special_items = _parse_special_checklist_from_excel(cf)
                if special_items:
                    break
        if not special_items:
            for cf in (cases_md, legacy_md):
                if cf.exists():
                    special_items = _parse_special_checklist_table(cf)
                    if special_items:
                        break
            if not special_items:
                for cf in sorted(
                    f for f in product_dir.iterdir()
                    if f.is_file() and f.suffix.lower() in ('.md', '.txt')
                    and f.name not in ('测试分析checklist.md',)
                ):
                    special_items = _parse_special_checklist_table(cf)
                    if special_items:
                        break

        for cf in (cases_md, legacy_md):
            if cf.exists():
                product_data = _parse_checklist_file(cf)
                if product_data:
                    break
        if not product_data:
            for cf in sorted(
                f for f in product_dir.iterdir()
                if f.is_file() and f.suffix.lower() in ('.md', '.txt')
                and f.name not in ('测试分析checklist.md',)
            ):
                product_data = _parse_checklist_file(cf)
                if product_data:
                    break
    
    # 3. 合并：产品覆盖总清单的同章节
    merged = _merge_checklists(base_data, product_data)
    
    if not merged and not special_items:
        return [], ""
    
    # 4. 按合并后的清单提取检查项
    keyword_items = []
    format_items = [] 
    
    for section, items in merged.items():
        if '场景覆盖' in section or '覆盖' in section:
            keyword_items = items or keyword_items
        elif '格式要求' in section or '数量要求' in section:
            format_items.extend(items or [])
    
    # 5. 执行检查（无合并章节时仅依赖专项检查表）
    if keyword_items:
        any_found = False
        for kw in keyword_items:
            if any(
                kw in (c.get('case_name', '') + c.get('precondition', '') + c.get('steps', '') + c.get('expects', ''))
                for c in cases
            ):
                any_found = True
                break
        if not any_found:
            missing.append(f"场景覆盖缺失: 未发现包含任一关键词的用例（关键词: {', '.join(keyword_items)}）")
    
    for item in format_items:
        if '步骤' in item and '预期结果' in item and '数量' in item:
            for c in cases:
                steps = _split_lines(c.get('steps', ''))
                expects = _split_lines(c.get('expects', ''))
                if len(steps) != len(expects):
                    missing.append(f"格式: 用例「{c.get('case_name', '')}」步骤与预期结果数量不一致")
                    break
        elif '前置条件' in item and '非空' in item:
            for c in cases:
                if not (c.get('precondition') or '').strip():
                    missing.append(f"格式: 用例「{c.get('case_name', '')}」前置条件为空")
                    break
        elif '用例数量' in item or '不少于' in item:
            m = re.search(r'不少于\s*(\d+)', item)
            if m:
                min_count = int(m.group(1))
                if len(cases) < min_count:
                    missing.append(f"数量: 用例数 {len(cases)} < {min_count}")
        elif '用例名称' in item or '具体' in item:
            generic = ['场景1', '场景2', '测试用例', '用例1', '用例2']
            for c in cases:
                name = (c.get('case_name') or '').strip()
                if any(g in name for g in generic) or len(name) < 4:
                    missing.append(f"格式: 用例名称过于泛化「{name}」")
                    break

    # 6. 专项检查项：根据产品 checklist 中的表格动态校验
    if special_items:
        missing.extend(_run_special_checks(cases, special_items))
    
    if not missing:
        report = "自查通过：所有检查项已满足"
    else:
        report = "自查发现缺失项，请补充到 test_cases_content.json 后重新运行：\n  - " + "\n  - ".join(missing)
    
    return missing, report


def generate_test_cases_markdown_from_content(cases_content_path: str, output_path: str, fallback_title: str, requirement_file_path: str = "") -> str:
    """从 test_cases_content.json 生成测试用例 Markdown（格式层：内容 → MD）。返回 .md 绝对路径。"""
    output_dir = ensure_absolute_path(output_path, "输出目录路径")
    title_en = sanitize_filename(fallback_title)
    md_path = output_dir / f"test_cases-{title_en}.md"
    requirement_title, cases = load_cases_content(cases_content_path)
    n = _write_md_from_cases(cases, md_path, requirement_title, requirement_file_path)
    print(f"测试用例（MD格式）已生成: {md_path}")
    print(f"共生成 {n} 个测试用例")
    return str(md_path)


def main():
    """
    主函数：从需求文档生成所有测试交付物

    工作流：前置（需求+pre_docs/context）→ 解析需求 → 生成 XMind → 后置校验（post_docs）→ 生成 MD/JSON → 可选上传 → 仅上传成功后清理中间产物
    """
    parser = argparse.ArgumentParser(
        description='从需求文档生成测试分析、测试用例（MD和JSON格式）',
        epilog='注意：请参考"路径处理和编码要求"章节，所有路径参数必须是绝对路径且使用英文路径。'
    )
    parser.add_argument('requirement_file', help='需求文档路径（必须是绝对路径）')
    parser.add_argument('--output-dir', default=None, help='输出目录（必须是绝对路径，默认：需求文档同级目录）')
    parser.add_argument('--analysis-content', '-A', default=None, help='测试分析内容 JSON 路径；未指定时在输出目录查找 test_analysis_content.json')
    parser.add_argument('--cases-content', '-C', default=None, help='测试用例内容 JSON 路径；未指定时在输出目录查找 test_cases_content.json')
    parser.add_argument('--api-token', help='API token（用于生成JSON格式和上传，如未提供则从配置文件读取）')
    parser.add_argument('--account', help='账号（用于生成JSON格式和上传，如未提供则从配置文件读取）')
    parser.add_argument('--node-path', help='节点路径（用于生成JSON格式和上传，如未提供则从配置文件读取）')
    parser.add_argument('--skip-json', action='store_true', help='跳过JSON格式生成')
    parser.add_argument('--upload', action='store_true', help='生成JSON后自动上传到Blade系统')
    parser.add_argument('--no-preview-doc', action='store_true', help='关闭生成前展示需求文档和参考示例')
    parser.add_argument('--product', help='产品名，用于从 pre_docs/<产品名>/context 加载参考示例，结合需求文档生成更完整的测试用例')
    parser.add_argument('--post-check-only', action='store_true', help='先执行后置校验；通过后直接生成测试分析及测试用例（跳过前置展示），失败则退出')
    parser.add_argument(
        '--analysis-post-check-only',
        action='store_true',
        help='先执行测试分析后置自查（post_docs/<产品>/测试分析checklist）；通过后继续完整生成流程，失败则退出',
    )
    
    args = parser.parse_args()
    
    # 强制将所有路径转换为绝对路径，避免Windows中文路径编码问题
    try:
        req_path = ensure_absolute_path(args.requirement_file, "需求文档路径")
    except ValueError as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)
    
    # 确定输出目录：如果未指定，则使用需求文档同级目录
    if args.output_dir:
        try:
            output_dir = ensure_absolute_path(args.output_dir, "输出目录路径")
        except ValueError as e:
            print(f"错误: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        output_dir = req_path.parent
    
    # 创建输出目录
    output_dir.mkdir(parents=True, exist_ok=True)

    # 后置校验模式：先校验，通过后直接生成交付物（跳过前置展示、解析需求），失败则退出
    post_check_already_passed = False
    analysis_post_check_already_passed = False
    requirement_title_from_cases = None
    if args.analysis_post_check_only:
        ac_path = args.analysis_content or str(output_dir / "test_analysis_content.json")
        if not Path(ac_path).exists():
            print(f"错误: 测试分析内容文件不存在: {ac_path}", file=sys.stderr)
            sys.exit(1)
        if not args.product:
            print("错误: 测试分析自查需要 --product <产品名> 以定位 post_docs/<产品>/测试分析checklist", file=sys.stderr)
            sys.exit(1)
        if not CONFIG_AVAILABLE or not get_post_docs_dir:
            print("错误: 无法加载 post_docs 配置，请确保 config_utils 可用", file=sys.stderr)
            sys.exit(1)
        try:
            from analysis_post_check import run_analysis_post_check

            atitle, topic_data = load_analysis_content(ac_path)
            post_docs_root = get_post_docs_dir(product=args.product)
            product_dir_name = sanitize_filename(args.product) or "default"
            product_post_dir = post_docs_root / product_dir_name
            if not product_post_dir.exists():
                product_post_dir = None
            missing_a, report_a = run_analysis_post_check(
                atitle, topic_data, post_docs_root, product_post_dir
            )
            if missing_a:
                print("\n" + "=" * 60)
                print("后置：测试分析自查（post_docs）未通过")
                print("=" * 60)
                if report_a:
                    print(report_a)
                print("\n请补充 test_analysis_content.json 后使用 --analysis-post-check-only 重试")
                print("=" * 60 + "\n")
                sys.exit(1)
            print("\n后置：测试分析自查已通过，继续生成流程...")
            if report_a:
                print(report_a)
            analysis_post_check_already_passed = True
        except SystemExit:
            raise
        except Exception as e:
            print(f"错误: 测试分析自查执行失败: {e}", file=sys.stderr)
            sys.exit(1)

    if args.post_check_only:
        cases_content_path = args.cases_content or str(output_dir / "test_cases_content.json")
        if not Path(cases_content_path).exists():
            print(f"错误: 内容文件不存在: {cases_content_path}", file=sys.stderr)
            sys.exit(1)
        if not CONFIG_AVAILABLE or not get_post_docs_dir:
            print("错误: 无法加载 post_docs 配置，请确保 config_utils 可用", file=sys.stderr)
            sys.exit(1)
        try:
            requirement_title_from_cases, cases_for_check = load_cases_content(cases_content_path)
            post_docs_root = get_post_docs_dir(product=args.product)
            product_post_dir = post_docs_root / (sanitize_filename(args.product) or 'default') if args.product else None
            if args.product and (not product_post_dir or not product_post_dir.exists()):
                product_post_dir = None
            missing_items, report = run_post_check(cases_for_check, post_docs_root, product_post_dir)
            if missing_items:
                print("\n" + "=" * 60)
                print("后置：自查（post_docs）未通过")
                print("=" * 60)
                if report:
                    print(report)
                print("\n请补充缺失内容到 test_cases_content.json 后重新运行（可用 --post-check-only 快速重试）")
                print("=" * 60 + "\n")
                sys.exit(1)
            print("\n后置：自查（post_docs）已通过，继续生成测试分析及测试用例...")
            if report:
                print(report)
            post_check_already_passed = True
        except Exception as e:
            print(f"错误: 后置自查执行失败: {e}", file=sys.stderr)
            sys.exit(1)
    
    try:
        upload_succeeded = None  # None=未尝试上传, True=成功, False=失败（用于--upload时，仅上传成功后才删除中间产物）
        analysis_json_path = None
        # 0. 前置逻辑：需求文档 + pre_docs 参考示例（--product 时加载）；post_check 已通过时跳过
        if not args.no_preview_doc and not post_check_already_passed and not analysis_post_check_already_passed:
            print("\n" + "=" * 60)
            print("前置：需求文档 + 参考示例（pre_docs）")
            print("=" * 60)
            # 0.1 需求文档（主内容）
            print(f"\n[需求文档] 路径: {req_path}")
            if req_path.exists():
                with open(req_path, 'r', encoding='utf-8', errors='replace') as f:
                    doc_content = f.read()
                preview_lines = doc_content.split('\n')[:80]
                preview = '\n'.join(preview_lines)
                if len(doc_content.split('\n')) > 80:
                    preview += "\n\n... (后续内容已省略，共 {} 行)".format(len(doc_content.split('\n')))
                print(f"\n{'-' * 40}\n{preview}\n{'-' * 40}")
            else:
                print("警告: 需求文档不存在")
            # 0.2 pre_docs 参考示例（读取产品目录下所有文本文件）
            if args.product and CONFIG_AVAILABLE and get_pre_docs_dir:
                pre_docs_root = get_pre_docs_dir(product=args.product)
                product_dir_name = sanitize_filename(args.product) or 'default'
                product_dir = pre_docs_root / product_dir_name
                if product_dir.exists() and product_dir.is_dir():
                    text_ext = ('.md', '.txt', '.markdown')
                    pre_files = sorted(
                        [f for f in product_dir.iterdir() if f.is_file() and f.suffix.lower() in text_ext]
                    )
                    if pre_files:
                        print(f"\n[context] 产品: {args.product} ({product_dir})")
                        print("（阅读以下内容作为参考，有助于生成更完整的测试用例）")
                        print("-" * 40)
                        for pf in pre_files:
                            try:
                                with open(pf, 'r', encoding='utf-8', errors='replace') as f:
                                    content = f.read()
                                lines = content.split('\n')
                                preview = '\n'.join(lines[:50]) if len(lines) > 50 else content
                                if len(lines) > 50:
                                    preview += f"\n\n... (后续省略，共 {len(lines)} 行)"
                                print(f"\n--- {pf.name} ---\n{preview}\n")
                            except Exception as e:
                                print(f"警告: 无法读取 {pf.name}: {e}")
                        print("-" * 40)
            print("=" * 60 + "\n")
        # 1. 解析需求文档（post_check 已通过时跳过，使用 cases 中的 requirement_title）
        # 输出文件名统一以 test_cases_content.json 的 requirement_title 为准，确保 --post-check-only 与完整流程只生成一套文件
        cases_content_path = args.cases_content or str(output_dir / "test_cases_content.json")
        if post_check_already_passed and requirement_title_from_cases is not None:
            requirement_info = {
                'title': requirement_title_from_cases,
                'file_path': str(req_path)
            }
            print(f"跳过解析需求，使用内容文件中的标题: {requirement_info['title']}")
        else:
            print("正在解析需求文档...")
            requirement_info = parse_requirement_document(str(req_path))
            print(f"需求文档解析完成: {requirement_info['title']}")
            # 若 test_cases_content.json 存在且含 requirement_title，优先使用其作为输出文件名
            if Path(cases_content_path).exists():
                try:
                    content_title, _ = load_cases_content(cases_content_path)
                    if content_title and content_title.strip():
                        requirement_info['title'] = content_title.strip()
                        print(f"使用内容文件中的标题（确保输出文件名一致）: {requirement_info['title']}")
                except Exception:
                    pass
        
        xmind_path = None
        md_path = None
        title_en = sanitize_filename(requirement_info['title'])
        
        # 内容文件驱动：脚本只做格式，内容由外部（AI/用户）提供
        analysis_content_path = args.analysis_content or str(output_dir / "test_analysis_content.json")
        
        if Path(analysis_content_path).exists():
            if (
                args.product
                and CONFIG_AVAILABLE
                and get_post_docs_dir
                and not analysis_post_check_already_passed
            ):
                try:
                    from analysis_post_check import run_analysis_post_check

                    atitle, topic_data = load_analysis_content(analysis_content_path)
                    post_docs_root = get_post_docs_dir(product=args.product)
                    product_dir_name = sanitize_filename(args.product) or "default"
                    product_post_dir = post_docs_root / product_dir_name
                    if not product_post_dir.exists():
                        product_post_dir = None
                    missing_a, report_a = run_analysis_post_check(
                        atitle, topic_data, post_docs_root, product_post_dir
                    )
                    if missing_a:
                        print("\n" + "=" * 60)
                        print("后置：测试分析自查（post_docs）未通过")
                        print("=" * 60)
                        if report_a:
                            print(report_a)
                        print("\n请补充 test_analysis_content.json 后重新运行（可加 --analysis-post-check-only 快速重试）")
                        print("=" * 60 + "\n")
                        sys.exit(1)
                    if report_a:
                        print("\n" + "=" * 60)
                        print("后置：测试分析自查已通过")
                        print("=" * 60)
                        print(report_a)
                        print("=" * 60 + "\n")
                except SystemExit:
                    raise
                except Exception as e:
                    print(f"\n警告: 测试分析自查执行失败: {e}")
                    sys.exit(1)
            elif not args.product and not analysis_post_check_already_passed:
                print("\n提示: 未指定 --product，已跳过测试分析后置自查（建议指定以加载 post_docs/<产品>/测试分析checklist）")

            print("\n正在生成测试分析（XMind + JSON 交付物，从内容文件）...")
            xmind_path, analysis_json_path = generate_test_analysis_xmind_from_content(
                analysis_content_path, str(output_dir), requirement_info['title'])
            print(f"测试分析已生成: {xmind_path}")
            print(f"测试分析（JSON交付物）: {analysis_json_path}")
        else:
            print("\n未提供测试分析内容，已跳过。请提供 --analysis-content 或在输出目录放置 test_analysis_content.json")
        
        if Path(cases_content_path).exists():
            # 后置逻辑：在生成 MD 之前执行 post_docs 校验，不通过则阻塞；post_check 已通过时跳过
            if not post_check_already_passed and CONFIG_AVAILABLE and get_post_docs_dir:
                try:
                    _, cases_for_check = load_cases_content(cases_content_path)
                    post_docs_root = get_post_docs_dir(product=args.product)
                    product_post_dir = None
                    if args.product:
                        product_dir_name = sanitize_filename(args.product) or 'default'
                        product_post_dir = post_docs_root / product_dir_name
                    missing_items, report = run_post_check(cases_for_check, post_docs_root, product_post_dir)
                    if missing_items:
                        print("\n" + "=" * 60)
                        print("后置：自查（post_docs）未通过")
                        print("=" * 60)
                        if report:
                            print(report)
                        print("\n请补充缺失内容到 test_cases_content.json 后重新运行脚本")
                        print("=" * 60 + "\n")
                        sys.exit(1)
                    if report:
                        print("\n" + "=" * 60)
                        print("后置：自查（post_docs）已通过")
                        print("=" * 60)
                        print(report)
                        print("=" * 60 + "\n")
                except Exception as e:
                    print(f"\n警告: 后置自查执行失败: {e}")
                    sys.exit(1)
            # 自查通过后，生成 MD 及后续流程
            print("\n正在生成测试用例（MD格式，从内容文件）...")
            md_path = generate_test_cases_markdown_from_content(
                cases_content_path, str(output_dir), requirement_info['title'],
                requirement_info.get('file_path', ''))
        else:
            print("\n未提供测试用例内容，已跳过。请提供 --cases-content 或在输出目录放置 test_cases_content.json")
        
        # 4. 生成测试用例（JSON格式），仅在已有 MD 时
        json_path = None
        if md_path and not args.skip_json:
            # 如果命令行参数未提供，检查配置并可能自动调用配置脚本
            need_setup = False
            if not args.api_token or not args.account:
                # 检查配置是否存在，如果不存在会自动调用配置脚本
                config_exists = check_and_setup_config()
                if not config_exists:
                    need_setup = True
                else:
                    # 配置完成后，重新加载配置（因为配置可能刚被创建）
                    # 这里不需要重新读取，因为后续的get_api_token等函数会自动读取
                    pass
            
            # 从配置文件或命令行参数获取配置
            if CONFIG_AVAILABLE:
                try:
                    product = getattr(args, 'product', None)
                    api_token = get_api_token(args.api_token, product=product)
                    account = get_account(args.account, product=product)
                    # 获取节点路径时传入账号，用于自动生成
                    node_path = get_node_path(args.node_path, account=account, product=product)
                    api_url = BLADE_API_URL
                except Exception as e:
                    print(f"\n警告: 读取配置文件时出错: {e}")
                    api_token = args.api_token
                    account = args.account
                    # 根据账号自动生成节点路径
                    if account:
                        node_path = args.node_path or f"/{account}/功能测试"
                    else:
                        node_path = args.node_path or "/账号/功能测试"
                    api_url = BLADE_API_URL
            else:
                api_token = args.api_token
                account = args.account
                # 根据账号自动生成节点路径
                if account:
                    node_path = args.node_path or f"/{account}/功能测试"
                else:
                    node_path = args.node_path or "/账号/功能测试"
                api_url = BLADE_API_URL
            
            # 如果配置不存在，使用默认值（允许生成JSON文件，但需要后续配置才能上传）
            if not api_token:
                api_token = "YOUR_API_TOKEN"
                if not need_setup:
                    print("\n警告: 未找到API token配置，使用默认值")
                    print(f"   提示：如需上传到Blade系统，请编辑工作区配置文件或运行: python scripts/setup_config.py\n      {resolve_public_config_path()}")
            
            if not account:
                account = "YOUR_ACCOUNT"
                if not need_setup:
                    print("\n警告: 未找到账号配置，使用默认值")
                    print(f"   提示：如需上传到Blade系统，请编辑工作区配置文件或运行: python scripts/setup_config.py\n      {resolve_public_config_path()}")
            
            if not node_path:
                node_path = "/账号/功能测试"
            
            # 在 node_path 后追加当前需求名称，使不同需求自动隔离
            title_en = sanitize_filename(requirement_info['title'])
            node_path = f"{node_path.rstrip('/')}/{title_en}"
            
            # 按产品获取前置条件字段名（用于 Blade 步骤中的前置条件 key）
            precondition_key = None
            if CONFIG_AVAILABLE and get_precondition_key:
                try:
                    precondition_key = get_precondition_key(product=getattr(args, 'product', None))
                except Exception:
                    pass
            
            # 生成JSON文件（即使使用默认值也生成，方便后续配置后使用）
            print("\n正在生成测试用例（JSON格式）...")
            # 使用英文文件名，避免PowerShell编码问题（title_en 已在上方计算并用于 node_path）
            json_path = output_dir / f"test_cases-{title_en}.json"
            try:
                convert_test_cases_to_json(
                    markdown_file=str(md_path),
                    api_token=api_token,
                    account=account,
                    node_path=node_path,
                    output_file=str(json_path),
                    default_values={
                        # 固定值字段（无需修改）
                        'caseType': "1",
                        'caseState':'1',
                        'caseLayer':'1',
                       
                        # 需要动态调整的字段（这些值会被智能推断覆盖，仅作为兜底默认值）
                        'casePrior': 'P0',  # 优先级，默认P0（高），会被智能推断覆盖
                        'caseSideType': '0',  # 正反用例类型，默认0（正用例），会被智能推断覆盖
                        'caseDetailType': '0',  # 用例细分类型，默认0（功能），会被智能推断覆盖
                        'caseName': requirement_info['title'],
                        # 可选字段
                        'caseHeader': account  # 负责人，使用账号
                        # 'templateName': '项目默认模板'  # 注释掉，避免格式错误
                    },
                    xn_product_id=None,  # 可选，多项目时必填
                    precondition_key=precondition_key
                )
                print(f"测试用例（JSON格式）已生成: {json_path}")
                
                # 5. 上传到Blade系统（如果指定了--upload选项）
                if args.upload:
                    if api_token == "YOUR_API_TOKEN" or account == "YOUR_ACCOUNT":
                        print("\n警告: 跳过上传（需要先配置API token和账号）")
                        print(f"   请编辑工作区配置文件或运行: python scripts/setup_config.py\n      {resolve_public_config_path()}")
                        upload_succeeded = False
                    elif not UPLOAD_AVAILABLE:
                        print("\n警告: 跳过上传（需要安装 requests 库: pip install requests）")
                        upload_succeeded = False
                    else:
                        print("\n正在上传测试用例到Blade系统...")
                        upload_result = upload_test_cases(
                            json_file=str(json_path),
                            api_url=api_url
                        )
                        
                        if upload_result['success']:
                            upload_succeeded = True
                            print(f"上传成功！")
                            print(f"状态码: {upload_result['status_code']}")
                            if upload_result.get('data'):
                                print(f"响应: {json.dumps(upload_result['data'], ensure_ascii=False, indent=2)}")
                            if (
                                ANALYSIS_UPLOAD_AVAILABLE
                                and CONFIG_AVAILABLE
                                and analysis_json_path
                                and Path(analysis_json_path).exists()
                            ):
                                try:
                                    from config_utils import get_analysis_import_url

                                    aurl = get_analysis_import_url(product=getattr(args, "product", None))
                                    if aurl:
                                        print("\n正在上传测试分析到Blade...")
                                        ares = upload_analysis_json(
                                            json_file=str(analysis_json_path),
                                            api_url=aurl,
                                            product=getattr(args, "product", None),
                                        )
                                        if not ares.get("success"):
                                            upload_succeeded = False
                                            print(
                                                f"测试分析上传失败: {ares.get('error', '未知错误')}"
                                            )
                                        elif ares.get("data") is not None:
                                            print(
                                                f"测试分析上传响应: {json.dumps(ares.get('data'), ensure_ascii=False, indent=2)}"
                                            )
                                except Exception as ex:
                                    upload_succeeded = False
                                    print(f"测试分析上传异常: {ex}")
                        else:
                            upload_succeeded = False
                            print(f"上传失败: {upload_result.get('error', '未知错误')}")
                            if upload_result.get('status_code'):
                                print(f"状态码: {upload_result['status_code']}")
            except Exception as e:
                print(f"\n警告: 生成JSON文件时出错: {e}")
                print("   将跳过JSON格式生成，但MD和XMind文件已成功生成")
                json_path = None
        
        # 自动清理：仅在上传成功时删除输出目录内的中间产物（-A/-C 指定其它路径的不删除）
        delivery_files_count = 0
        if xmind_path and Path(xmind_path).exists():
            delivery_files_count += 1
        if analysis_json_path and Path(analysis_json_path).exists():
            delivery_files_count += 1
        if md_path and Path(md_path).exists():
            delivery_files_count += 1
        if json_path and Path(json_path).exists():
            delivery_files_count += 1
        
        expected_files_count = 0
        if Path(analysis_content_path).exists():
            expected_files_count += 2
        if Path(cases_content_path).exists():
            expected_files_count += 1  # MD
            if not args.skip_json:
                expected_files_count += 1  # JSON

        should_delete = (
            args.upload
            and upload_succeeded is True
            and delivery_files_count >= expected_files_count
            and expected_files_count > 0
        )
        if args.upload and upload_succeeded is False:
            print("\n上传未成功，保留中间产物以便重试")
        
        if should_delete:
            print(f"\n交付物文件已生成（共{delivery_files_count}个），开始清理中间产物...")
            deleted_count = 0
            failed_files = []
            
            for name in ("test_analysis_content.json", "test_cases_content.json"):
                p = output_dir / name
                if p.exists():
                    try:
                        # 删除文件
                        p.unlink()
                        
                        # 验证文件确实被删除（多次检查，处理Windows延迟删除）
                        # Windows在文件被打开时可能会延迟删除，需要多次检查
                        max_retries = 5
                        retry_delay = 0.5
                        deleted = False
                        
                        for retry in range(max_retries):
                            time.sleep(retry_delay)
                            if not p.exists():
                                deleted = True
                                break
                        
                        if deleted:
                            print(f"已删除中间产物: {p}")
                            deleted_count += 1
                        else:
                            # 文件仍然存在，可能被其他进程占用（如IDE打开）
                            failed_files.append(str(p))
                            print(f"警告: 无法删除中间产物文件（可能被其他进程占用，如IDE打开）: {p}")
                            print(f"提示: 请手动关闭文件后删除，或稍后手动删除")
                    except OSError as e:
                        failed_files.append(str(p))
                        print(f"错误: 删除中间产物失败 {p}: {e}")
            
            if deleted_count > 0:
                print(f"已清理中间产物，共删除 {deleted_count} 个文件")
            if failed_files:
                print(f"警告: 以下中间产物文件删除失败，请手动删除: {', '.join(failed_files)}")
        else:
            if args.upload and upload_succeeded is False:
                pass  # 已在上面打印"上传未成功，保留中间产物以便重试"
            elif delivery_files_count == 0:
                print("警告: 未生成任何交付物文件，跳过中间产物清理")
            elif delivery_files_count < expected_files_count:
                print(f"警告: 期望生成 {expected_files_count} 个交付物文件，但只生成了 {delivery_files_count} 个，跳过中间产物清理")
                print("提示: 请确保所有期望的交付物文件都已生成完成")

        print("\n测试交付物生成完成！")
        print("\n生成的文件：")
        print(f"  测试分析（XMind）: {xmind_path or '未生成（需提供 test_analysis_content.json 或 --analysis-content）'}")
        if analysis_json_path:
            print(f"  测试分析（JSON交付物）: {analysis_json_path}")
        print(f"  测试用例（MD）: {md_path or '未生成（需提供 test_cases_content.json 或 --cases-content）'}")
        if json_path:
            print(f"  测试用例（JSON）: {json_path}")
        elif md_path and not args.skip_json:
            print(f"  警告: 测试用例（JSON）: 未生成（请检查配置或错误信息）")
        elif not md_path and not args.skip_json:
            print(f"  测试用例（JSON）: 未生成（需先有 MD，即提供 test_cases_content.json 或 --cases-content）")
        
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
