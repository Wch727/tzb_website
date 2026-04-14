"""首页与展示页示例内容。"""

from __future__ import annotations

from typing import Any, Dict, List

from content_store import (
    build_long_march_story_script,
    get_featured_route_nodes,
    get_recommended_questions,
    get_route_chapters,
    get_storytelling_tracks,
    load_events_data,
    load_figures_data,
    load_route_nodes_data,
    load_spirit_topics,
)
from utils import DATA_DIR, read_json


def load_route_showcase_nodes(limit: int = 12) -> List[Dict[str, Any]]:
    """读取推荐路线节点。"""
    nodes = load_route_nodes_data()
    return nodes[:limit]


def load_home_sample_content() -> Dict[str, Any]:
    """构造首页示例展示内容。"""
    figures = load_figures_data()
    events = load_events_data()
    spirit = load_spirit_topics()
    nodes = load_route_showcase_nodes(limit=20)
    chapters = get_route_chapters()
    sample_scripts = read_json(DATA_DIR / "sample_scripts.json", [])
    script_block = sample_scripts[0] if sample_scripts else {}

    return {
        "featured_nodes": get_featured_route_nodes(limit=6),
        "timeline_nodes": nodes,
        "chapter_sections": chapters,
        "story_tracks": get_storytelling_tracks(),
        "hero_route_map": "assets/images/changzheng_route_map.jpg",
        "recommended_route": script_block.get("recommended_routes", []),
        "spirit_topics": spirit[:6],
        "example_questions": get_recommended_questions(limit=8),
        "long_march_story_script": build_long_march_story_script(),
        "example_guide_script": script_block.get("example_guide_script", ""),
        "example_video_script": script_block.get("example_video_script", ""),
        "quick_try_questions": script_block.get("quick_try_questions", []),
        "figure_cards": figures[:6],
        "event_cards": events[:8],
        "recommended_learning_paths": script_block.get("recommended_learning_paths", []),
        "featured_faqs": script_block.get("featured_faqs", []),
        "recommended_nodes_by_stage": [
            {
                "title": chapter.get("title", ""),
                "subtitle": chapter.get("subtitle", ""),
                "nodes": chapter.get("nodes", [])[:3],
            }
            for chapter in chapters
        ],
    }
