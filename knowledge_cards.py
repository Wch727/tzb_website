"""知识卡片与知识检索辅助。"""

from __future__ import annotations

from typing import Any, Dict, List

from content_store import (
    load_all_knowledge_items,
    load_events_data,
    load_faq_items,
    load_figures_data,
    load_places_data,
    load_route_nodes_data,
    load_spirit_topics,
)


def get_knowledge_cards(category: str = "全部", keyword: str = "") -> List[Dict[str, Any]]:
    """按分类与关键词获取知识卡片。"""
    keyword = str(keyword or "").strip()
    category_map = {
        "全部": load_all_knowledge_items,
        "路线节点": load_route_nodes_data,
        "重大事件": load_events_data,
        "重要人物": load_figures_data,
        "重要地点": load_places_data,
        "长征精神": load_spirit_topics,
        "常见问答": load_faq_items,
    }
    loader = category_map.get(category, load_all_knowledge_items)
    rows = loader()
    if not keyword:
        return rows
    matched: List[Dict[str, Any]] = []
    for item in rows:
        haystack = "\n".join(
            [
                str(item.get("title", "")),
                str(item.get("summary", "")),
                str(item.get("background", "")),
                str(item.get("significance", "")),
                str(item.get("question", "")),
                str(item.get("answer", "")),
            ]
        )
        if keyword in haystack:
            matched.append(item)
    return matched


def build_related_knowledge_bundle(node: Dict[str, Any]) -> List[Dict[str, Any]]:
    """围绕节点构建知识卡片。"""
    cards: List[Dict[str, Any]] = []
    for item in load_figures_data():
        if item.get("title") in (node.get("figures") or []):
            cards.append(item)
    for item in load_spirit_topics():
        if item.get("title") and item.get("title") in (
            node.get("summary", "") + node.get("significance", "")
        ):
            cards.append(item)
    for item in load_faq_items():
        title = str(item.get("title", "") or "")
        question = str(item.get("question", "") or "")
        if node.get("title", "") in title or node.get("title", "") in question:
            cards.append(item)
    return cards[:6]

