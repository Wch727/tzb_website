"""仓库内置长征史内容的统一读取与匹配工具。"""

from __future__ import annotations

import csv
import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils import DATA_DIR, normalize_knowledge_type


ROUTE_CHAPTERS: List[Dict[str, Any]] = [
    {
        "id": "departure_breakthrough",
        "title": "出发与突围",
        "subtitle": "从中央苏区出发，穿越封锁线，在巨大压力下寻找新的战略转移通道。",
        "badge": "第一篇章",
        "node_ids": [
            "ruijin_departure",
            "yudu_crossing",
            "break_four_blockades",
            "xiangjiang_battle",
        ],
    },
    {
        "id": "turning_adjustment",
        "title": "转折与调整",
        "subtitle": "通道转兵、黎平与猴场会议相继展开，最终在遵义实现全局性转折。",
        "badge": "第二篇章",
        "node_ids": [
            "tongdao_turn",
            "liping_meeting",
            "houchang_meeting",
            "zunyi_meeting",
            "loushanguan_battle",
        ],
    },
    {
        "id": "crossing_breakthrough",
        "title": "巧渡与突破",
        "subtitle": "以灵活机动摆脱强敌围追堵截，在赤水、金沙江与大渡河一线打开新局面。",
        "badge": "第三篇章",
        "node_ids": [
            "sidu_chishui",
            "jinshajiang_crossing",
            "daduhe_forcing",
            "luding_bridge",
            "maogong_meeting",
        ],
    },
    {
        "id": "northward_victory",
        "title": "北上与会师",
        "subtitle": "翻雪山、过草地、经榜罗镇与吴起镇北上，最终实现胜利会师。",
        "badge": "第四篇章",
        "node_ids": [
            "snow_mountains",
            "grassland_crossing",
            "bangluo_meeting",
            "wuqi_meeting",
            "zhiluozhen_battle",
            "huining_meeting",
        ],
    },
]


def _load_json_list(path: Path) -> List[Dict[str, Any]]:
    """读取 JSON 列表文件。"""
    if not path.exists():
        return []
    content = json.loads(path.read_text(encoding="utf-8"))
    return [item for item in content if isinstance(item, dict)] if isinstance(content, list) else []


def _load_csv_rows(path: Path) -> List[Dict[str, Any]]:
    """读取 CSV 行数据。"""
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _merge_image_fields(item: Dict[str, Any], mapped: Dict[str, Any]) -> Dict[str, Any]:
    """将图片映射信息补齐到内容记录中。"""
    merged = item.copy()
    for field in ["image", "image_alt", "image_caption", "remote_image_url"]:
        if not merged.get(field) and mapped.get(field):
            merged[field] = mapped[field]
    merged.setdefault("image", "")
    merged.setdefault("image_alt", merged.get("title", "长征史图片"))
    merged.setdefault("image_caption", merged.get("summary", "")[:60])
    merged.setdefault("remote_image_url", "")
    return merged


@lru_cache(maxsize=1)
def load_image_map() -> Dict[str, Any]:
    """读取图片映射配置。"""
    path = DATA_DIR / "image_map.json"
    if not path.exists():
        return {"items": {}, "fallbacks": {}}
    content = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(content, dict):
        return {"items": {}, "fallbacks": {}}
    return {
        "items": content.get("items", {}) if isinstance(content.get("items"), dict) else {},
        "fallbacks": content.get("fallbacks", {}) if isinstance(content.get("fallbacks"), dict) else {},
    }


def _image_mapping_for_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """根据标题、节点名和地点查找图片映射。"""
    image_map = load_image_map().get("items", {})
    candidates = [
        item.get("id", ""),
        item.get("title", ""),
        item.get("route_stage", ""),
        item.get("place", ""),
    ]
    for candidate in candidates:
        candidate = str(candidate or "").strip()
        if candidate and candidate in image_map and isinstance(image_map[candidate], dict):
            return image_map[candidate]
    return {}


@lru_cache(maxsize=1)
def load_route_nodes_data() -> List[Dict[str, Any]]:
    """读取主路线节点数据。"""
    path = DATA_DIR / "route_nodes.json"
    rows = _load_json_list(path)
    nodes: List[Dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        item = _merge_image_fields(row, _image_mapping_for_item(row))
        item["type"] = normalize_knowledge_type(item.get("type", "route"))
        item["order"] = int(item.get("order", index))
        item["score"] = int(item.get("score", 10))
        item.setdefault("image_key", item.get("id", "") or item.get("title", ""))
        item.setdefault("avatar", "assets/avatar/guide.svg")
        item.setdefault("summary", "")
        item.setdefault("background", "")
        item.setdefault("process", "")
        item.setdefault("significance", "")
        item.setdefault("figures", [])
        item.setdefault("key_points", [])
        item.setdefault("related_nodes", [])
        item.setdefault("quiz", {})
        nodes.append(item)
    nodes.sort(key=lambda row: int(row.get("order", 0)))
    return nodes


@lru_cache(maxsize=1)
def load_figures_data() -> List[Dict[str, Any]]:
    """读取人物数据。"""
    rows = _load_json_list(DATA_DIR / "figures.json")
    figures: List[Dict[str, Any]] = []
    for row in rows:
        item = _merge_image_fields(row, _image_mapping_for_item(row))
        item["type"] = normalize_knowledge_type(item.get("type", "figure"))
        item.setdefault("image_key", item.get("id", "") or item.get("title", ""))
        item.setdefault("summary", "")
        item.setdefault("background", item.get("summary", ""))
        item.setdefault("significance", "")
        item.setdefault("role", "重要人物")
        figures.append(item)
    return figures


@lru_cache(maxsize=1)
def load_events_data() -> List[Dict[str, Any]]:
    """读取事件数据。"""
    rows = _load_json_list(DATA_DIR / "events.json")
    events: List[Dict[str, Any]] = []
    for row in rows:
        item = _merge_image_fields(row, _image_mapping_for_item(row))
        item["type"] = normalize_knowledge_type(item.get("type", "event"))
        item.setdefault("image_key", item.get("id", "") or item.get("title", ""))
        item.setdefault("summary", "")
        item.setdefault("significance", "")
        events.append(item)
    return events


@lru_cache(maxsize=1)
def load_spirit_topics() -> List[Dict[str, Any]]:
    """读取长征精神专题。"""
    rows = _load_json_list(DATA_DIR / "spirit.json")
    topics: List[Dict[str, Any]] = []
    for row in rows:
        item = _merge_image_fields(row, _image_mapping_for_item(row))
        item["type"] = normalize_knowledge_type(item.get("type", "spirit"))
        item.setdefault("image_key", item.get("id", "") or item.get("title", ""))
        item.setdefault("summary", "")
        item.setdefault("detail", "")
        topics.append(item)
    return topics


@lru_cache(maxsize=1)
def load_faq_items() -> List[Dict[str, Any]]:
    """读取 FAQ 数据。"""
    items = []
    for row in _load_csv_rows(DATA_DIR / "faq.csv"):
        row = row.copy()
        row["type"] = normalize_knowledge_type(row.get("type", "faq"))
        row.setdefault("title", row.get("question", "长征史问答"))
        row.setdefault("summary", row.get("answer", ""))
        row.setdefault("extended_note", "")
        items.append(row)
    return items


@lru_cache(maxsize=1)
def load_places_data() -> List[Dict[str, Any]]:
    """读取地点数据。"""
    rows = _load_json_list(DATA_DIR / "places.json")
    places: List[Dict[str, Any]] = []
    for row in rows:
        item = _merge_image_fields(row, _image_mapping_for_item(row))
        item["type"] = normalize_knowledge_type(item.get("type", "place"))
        item.setdefault("image_key", item.get("id", "") or item.get("title", ""))
        item.setdefault("summary", "")
        item.setdefault("background", item.get("summary", ""))
        item.setdefault("significance", "")
        places.append(item)
    return places


def get_route_node_data(node_id: str) -> Optional[Dict[str, Any]]:
    """按 id、标题或路线阶段获取节点。"""
    for node in load_route_nodes_data():
        if node_id in [node.get("id"), node.get("title"), node.get("route_stage")]:
            return node
    return None


def get_route_chapters() -> List[Dict[str, Any]]:
    """按展陈篇章组织长征主线节点。"""
    node_index = {item.get("id"): item for item in load_route_nodes_data()}
    chapters: List[Dict[str, Any]] = []
    for chapter in ROUTE_CHAPTERS:
        nodes = [node_index[node_id] for node_id in chapter.get("node_ids", []) if node_id in node_index]
        chapter_item = chapter.copy()
        chapter_item["nodes"] = nodes
        chapter_item["count"] = len(nodes)
        chapters.append(chapter_item)
    return chapters


def get_chapter_for_node(node: Dict[str, Any]) -> Dict[str, Any]:
    """根据节点定位其所属的主线篇章。"""
    node_id = str(node.get("id", "") or "")
    for chapter in get_route_chapters():
        if node_id in chapter.get("node_ids", []):
            return chapter
    return {
        "id": "general",
        "title": "主线展项",
        "subtitle": "沿着长征主线继续深入阅读与学习。",
        "badge": "展项单元",
        "nodes": [],
        "count": 0,
    }


def get_featured_route_nodes(limit: int = 6) -> List[Dict[str, Any]]:
    """返回首页优先展示的代表性节点。"""
    featured_ids = [
        "ruijin_departure",
        "xiangjiang_battle",
        "zunyi_meeting",
        "sidu_chishui",
        "luding_bridge",
        "huining_meeting",
    ]
    node_index = {item.get("id"): item for item in load_route_nodes_data()}
    featured = [node_index[node_id] for node_id in featured_ids if node_id in node_index]
    if len(featured) < limit:
        existing_ids = {item.get("id") for item in featured}
        for node in load_route_nodes_data():
            if node.get("id") not in existing_ids:
                featured.append(node)
            if len(featured) >= limit:
                break
    return featured[:limit]


def build_node_related_questions(node: Dict[str, Any], limit: int = 4) -> List[str]:
    """围绕节点构造相关问题，优先复用 FAQ。"""
    title = str(node.get("title", "") or "")
    place = str(node.get("place", "") or "")
    faq_matches: List[str] = []
    for item in load_faq_items():
        question = str(item.get("question", "") or item.get("title", "") or "").strip()
        keywords = str(item.get("keywords", "") or "")
        if not question:
            continue
        if title and title in question:
            faq_matches.append(question)
            continue
        if title and title in keywords:
            faq_matches.append(question)
            continue
        if place and place.split("、")[0] in question:
            faq_matches.append(question)
    generated = [
        f"{title}发生在什么历史背景下？",
        f"{title}为什么能成为长征中的关键节点？",
        f"{title}与哪些重要人物密切相关？",
        f"从{title}可以理解哪些长征精神内涵？",
    ]
    questions: List[str] = []
    for question in faq_matches + generated:
        if question and question not in questions:
            questions.append(question)
        if len(questions) >= limit:
            break
    return questions[:limit]


def get_recommended_questions(limit: int = 8) -> List[str]:
    """返回首页和知识页通用的推荐问题。"""
    defaults = [
        "长征为什么要开始？",
        "湘江战役为什么重要？",
        "遵义会议意味着什么？",
        "四渡赤水体现了什么战略智慧？",
        "飞夺泸定桥在长征中具有怎样的象征意义？",
        "为什么说长征是战略转移的伟大胜利？",
        "长征精神包括哪些核心内涵？",
        "会宁会师为什么被视为长征胜利的重要标志？",
    ]
    questions: List[str] = []
    for item in load_faq_items():
        candidate = str(item.get("question", "") or item.get("title", "") or "").strip()
        if candidate and candidate not in questions:
            questions.append(candidate)
        if len(questions) >= limit:
            break
    for candidate in defaults:
        if candidate not in questions:
            questions.append(candidate)
        if len(questions) >= limit:
            break
    return questions[:limit]


def get_node_extended_reading(node: Dict[str, Any], limit: int = 4) -> List[Dict[str, Any]]:
    """围绕节点整理延伸阅读卡片。"""
    reading: List[Dict[str, Any]] = []
    for figure_name in node.get("figures", [])[:3]:
        figure = get_figure_data(figure_name)
        if figure:
            reading.append(figure)
    title = str(node.get("title", "") or "")
    for item in load_faq_items():
        question = str(item.get("question", "") or "")
        if title and title in question:
            reading.append(item)
    for item in load_spirit_topics():
        haystack = f"{node.get('summary', '')}\n{node.get('significance', '')}"
        if item.get("title") and str(item.get("title")) in haystack:
            reading.append(item)
    deduped: List[Dict[str, Any]] = []
    seen = set()
    for item in reading:
        key = (item.get("type", ""), item.get("title", ""), item.get("question", ""))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
        if len(deduped) >= limit:
            break
    return deduped


def get_figure_data(name: str) -> Optional[Dict[str, Any]]:
    """按人物名称获取人物数据。"""
    for item in load_figures_data():
        if name in [item.get("title"), item.get("name")]:
            return item
    return None


def match_route_node(question: str) -> Optional[Dict[str, Any]]:
    """从问题中匹配最相关的路线节点。"""
    text = str(question or "").strip()
    best: Optional[Dict[str, Any]] = None
    best_length = 0
    for node in load_route_nodes_data():
        candidates = [node.get("title", ""), node.get("route_stage", ""), node.get("place", "")]
        for candidate in candidates:
            candidate = str(candidate or "").strip()
            if candidate and candidate in text and len(candidate) > best_length:
                best = node
                best_length = len(candidate)
    return best


def match_faq(question: str) -> Optional[Dict[str, Any]]:
    """从问题中匹配最相关 FAQ。"""
    text = str(question or "").strip()
    best: Optional[Dict[str, Any]] = None
    best_score = 0
    for item in load_faq_items():
        score = 0
        title = str(item.get("title", "") or "")
        prompt = str(item.get("question", "") or "")
        keywords = str(item.get("keywords", "") or "")
        for candidate in [title, prompt]:
            if candidate and candidate in text:
                score = max(score, len(candidate) + 20)
        if keywords:
            for keyword in [part.strip() for part in keywords.split("、") if part.strip()]:
                if keyword and keyword in text:
                    score += len(keyword)
        if score > best_score:
            best = item
            best_score = score
    return best


def build_source_card(item: Dict[str, Any], snippet: str = "") -> Dict[str, Any]:
    """将本地内容记录转换为来源卡片。"""
    item_type = normalize_knowledge_type(item.get("type", "event"))
    return {
        "source_file": item.get("source_file", "仓库内置数据"),
        "title": item.get("title", "未命名"),
        "type": item_type,
        "snippet": snippet or item.get("summary", "")[:220],
    }


def get_related_nodes(node: Dict[str, Any], limit: int = 3) -> List[Dict[str, Any]]:
    """获取当前节点附近的相关推荐节点。"""
    nodes = load_route_nodes_data()
    related_ids = [item for item in node.get("related_nodes", []) if item]
    if related_ids:
        related = [candidate for candidate in nodes if candidate.get("id") in related_ids]
        return related[:limit]

    current_order = int(node.get("order", 0))
    related = [
        candidate
        for candidate in nodes
        if candidate.get("id") != node.get("id") and abs(int(candidate.get("order", 0)) - current_order) <= 2
    ]
    return related[:limit]


def build_static_sources_for_node(node: Dict[str, Any], extra_items: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    """为静态模式构建来源卡片。"""
    sources = [
        build_source_card(
            {
                "title": node.get("title", "长征节点"),
                "type": node.get("type", "route"),
                "source_file": "data/route_nodes.json",
                "summary": node.get("summary", ""),
            },
            snippet=node.get("summary", ""),
        )
    ]
    for item in extra_items or []:
        if item:
            sources.append(build_source_card(item, snippet=item.get("answer", "") or item.get("summary", "")))
    return sources


def load_all_knowledge_items() -> List[Dict[str, Any]]:
    """汇总全部知识卡片。"""
    items: List[Dict[str, Any]] = []
    items.extend(load_route_nodes_data())
    items.extend(load_events_data())
    items.extend(load_figures_data())
    items.extend(load_places_data())
    items.extend(load_spirit_topics())
    items.extend(load_faq_items())
    return items


def clear_content_caches() -> None:
    """清理内容缓存，便于后台修改后即时生效。"""
    load_image_map.cache_clear()
    load_route_nodes_data.cache_clear()
    load_figures_data.cache_clear()
    load_events_data.cache_clear()
    load_places_data.cache_clear()
    load_spirit_topics.cache_clear()
    load_faq_items.cache_clear()
