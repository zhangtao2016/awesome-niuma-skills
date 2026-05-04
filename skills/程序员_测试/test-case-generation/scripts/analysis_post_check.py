#!/usr/bin/env python3
"""
测试分析后置自查：依据 post_docs 下「测试分析checklist」（产品目录优先）。

与 generate_from_requirement 配合使用；解析函数从同目录模块惰性导入，避免顶层循环依赖。
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any


def _flatten_topic_titles(topic_data: dict) -> str:
    """递归收集 topic_data 中所有键名，供关键词覆盖检查。"""
    parts: List[str] = []

    def walk(node: Any) -> None:
        if not isinstance(node, dict):
            return
        for k, v in node.items():
            parts.append(str(k))
            if isinstance(v, dict) and v:
                walk(v)

    walk(topic_data)
    return " ".join(parts)


def run_analysis_post_check(
    title: str,
    topic_data: dict,
    post_docs_root: Path,
    product_dir: Optional[Path] = None,
) -> Tuple[List[str], str]:
    """
    根据合并后的测试分析 checklist 检查 topic_data。

    产品侧文件（须指定 product 目录时）：
      - 优先 post_docs/<产品>/测试分析checklist.xlsx（专项检查表 + 可辅以 md 章节）
      - 其次 测试分析checklist.md
    可选根目录：post_docs/测试分析checklist.md 作为总底稿（同章节产品覆盖）。

    Returns:
        (missing_items, report)
    """
    import generate_from_requirement as gfr

    missing: List[str] = []

    base_path = post_docs_root / "测试分析checklist.md"
    base_data: Dict = gfr._parse_checklist_file(base_path) if base_path.exists() else {}

    product_data: Dict = {}
    special_items: List = []

    if product_dir and product_dir.exists() and product_dir.is_dir():
        xlsx_target = product_dir / "测试分析checklist.xlsx"
        md_target = product_dir / "测试分析checklist.md"

        if xlsx_target.exists():
            special_items = gfr._parse_special_checklist_from_excel(xlsx_target)
        if not special_items and md_target.exists():
            special_items = gfr._parse_special_checklist_table(md_target)

        if md_target.exists():
            product_data = gfr._parse_checklist_file(md_target)

    merged = gfr._merge_checklists(base_data, product_data)

    topic_blob = (title or "") + " " + _flatten_topic_titles(topic_data)

    if not merged and not special_items:
        return [], ""

    keyword_items: List[str] = []
    format_items: List[str] = []

    for section, items in merged.items():
        if "场景覆盖" in section or "覆盖" in section:
            keyword_items = items or keyword_items
        elif "格式要求" in section or "数量要求" in section:
            format_items.extend(items or [])

    if keyword_items:
        any_found = False
        for kw in keyword_items:
            if kw in topic_blob:
                any_found = True
                break
        if not any_found:
            missing.append(
                "场景覆盖缺失: 分析主题中未发现包含任一关键词（关键词: "
                + ", ".join(keyword_items)
                + "）"
            )

    generic_placeholders = ("场景1", "场景2", "测试场景1", "测试场景2", "功能点1", "功能点2")
    for item in format_items:
        if "占位" in item or "具体" in item or "泛化" in item:
            for g in generic_placeholders:
                if g in topic_blob:
                    missing.append(f"格式: 分析主题中出现占位或泛化片段「{g}」")
                    break
        if "测试场景" in item and ("三层" in item or "层级" in item or "细分" in item):
            if "测试场景" not in topic_data:
                missing.append("格式: topic_data 中缺少「测试场景」分支")
            else:
                ts = topic_data.get("测试场景") or {}
                if not isinstance(ts, dict):
                    missing.append("格式: 「测试场景」必须为对象")
                else:
                    for need in ("正常场景", "异常场景", "边界场景"):
                        if need not in ts:
                            missing.append(f"格式: 「测试场景」下缺少「{need}」")

    if special_items:
        all_text = topic_blob
        all_text_lower = all_text.lower()
        for scene, check_item, supplement in special_items:
            trigger, required, apply_only_if = gfr._extract_trigger_and_required(
                scene, check_item, supplement
            )
            if not trigger or not required:
                continue
            scene_applies = any(t.lower() in all_text_lower for t in trigger)
            if not scene_applies:
                continue
            if apply_only_if and apply_only_if not in all_text:
                continue
            has_required = any(r in all_text for r in required)
            if not has_required:
                missing.append(
                    f"专项检查: [{scene}] {check_item}，分析主题中未发现相关覆盖（建议包含: {', '.join(required[:5])}）"
                )

    if not missing:
        report = "测试分析自查通过：所有检查项已满足"
    else:
        report = (
            "测试分析自查发现缺失项，请补充到 test_analysis_content.json 后重新运行：\n  - "
            + "\n  - ".join(missing)
        )

    return missing, report
