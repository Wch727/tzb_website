"""首页与展示页示例内容。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from utils import DATA_DIR


def _load_json(path: Path) -> List[Dict[str, Any]]:
    """读取 JSON 列表文件。"""
    if not path.exists():
        return []
    content = json.loads(path.read_text(encoding="utf-8"))
    return content if isinstance(content, list) else []


def load_route_showcase_nodes(limit: int = 12) -> List[Dict[str, Any]]:
    """读取推荐路线节点。"""
    nodes = _load_json(DATA_DIR / "route_nodes.json")
    return nodes[:limit]


def load_home_sample_content() -> Dict[str, Any]:
    """构造首页示例展示内容。"""
    figures = _load_json(DATA_DIR / "figures.json")
    events = _load_json(DATA_DIR / "events.json")
    spirit = _load_json(DATA_DIR / "spirit.json")
    nodes = load_route_showcase_nodes(limit=12)
    sample_scripts = _load_json(DATA_DIR / "sample_scripts.json")
    script_block = sample_scripts[0] if sample_scripts else {}

    return {
        "featured_nodes": nodes[:6],
        "timeline_nodes": nodes,
        "hero_route_map": "assets/images/changzheng_route_map.jpg",
        "recommended_route": script_block.get("recommended_routes", []),
        "spirit_topics": spirit[:4],
        "example_questions": script_block.get("example_questions", []),
        "example_guide_script": script_block.get("example_guide_script", ""),
        "example_video_script": script_block.get("example_video_script", ""),
        "quick_try_questions": script_block.get("quick_try_questions", []),
        "figure_cards": figures[:6],
        "event_cards": events[:6],
    }
