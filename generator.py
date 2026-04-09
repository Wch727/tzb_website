"""内容生成模块。"""

from __future__ import annotations

from typing import Any, Dict, List

from llm import get_llm_client
from prompts import (
    LONG_MARCH_GUIDE_ROLE_PROMPT,
    build_game_summary_prompt,
    build_guide_script_prompt,
    build_short_video_script_prompt,
)
from rag import retrieve_knowledge


def _context_from_hits(hits: List[Dict[str, Any]]) -> List[str]:
    """将检索结果转成上下文块。"""
    blocks = []
    for item in hits:
        metadata = item.get("metadata", {})
        blocks.append(
            f"标题：{metadata.get('title', '未命名')}\n"
            f"类型：{metadata.get('type', '未知')}\n"
            f"地点：{metadata.get('place', '未标注')}\n"
            f"路线节点：{metadata.get('route_stage', '未标注')}\n"
            f"内容：{item.get('text', '')}"
        )
    return blocks


def _source_cards(hits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """整理生成结果使用到的依据。"""
    cards = []
    for item in hits:
        metadata = item.get("metadata", {})
        cards.append(
            {
                "source_file": metadata.get("source_file", "未知文件"),
                "title": metadata.get("title", "未命名"),
                "type": metadata.get("type", "未知"),
                "snippet": item.get("text", "")[:220],
            }
        )
    return cards


def generate_guide_script(
    topic: str,
    audience: str,
    duration: str,
    provider_config: Dict[str, Any],
) -> Dict[str, Any]:
    """生成讲解稿。"""
    retrieval = retrieve_knowledge(question=topic, filters={"intent": "generate_script"}, top_k=5)
    hits = retrieval["hits"]
    client = get_llm_client(provider_config)
    prompt = build_guide_script_prompt(
        topic=topic,
        audience=audience,
        duration=duration,
        context="\n\n".join(_context_from_hits(hits)),
    )
    result = client.generate_with_context(
        prompt=f"{LONG_MARCH_GUIDE_ROLE_PROMPT}\n\n{prompt}",
        context_blocks=_context_from_hits(hits),
        temperature=0.4,
    )
    return {
        "script": result.get("content", ""),
        "provider_used": result.get("provider", provider_config.get("provider_name", "mock")),
        "model_used": result.get("model", provider_config.get("model", "")),
        "warning": result.get("warning", ""),
        "fallback_used": result.get("fallback_used", False),
        "intent": retrieval.get("intent", "generate_script"),
        "applied_filters": retrieval.get("applied_filters", {}),
        "retrieved_chunks": [item["text"] for item in hits],
        "retrieved_metadata": [item["metadata"] for item in hits],
        "sources": _source_cards(hits),
    }


def generate_short_video_script(
    topic: str,
    audience: str,
    style: str,
    provider_config: Dict[str, Any],
) -> Dict[str, Any]:
    """生成短视频脚本。"""
    retrieval = retrieve_knowledge(question=topic, filters={"intent": "generate_script"}, top_k=5)
    hits = retrieval["hits"]
    client = get_llm_client(provider_config)
    prompt = build_short_video_script_prompt(
        topic=topic,
        audience=audience,
        style=style,
        context="\n\n".join(_context_from_hits(hits)),
    )
    result = client.generate_with_context(
        prompt=f"{LONG_MARCH_GUIDE_ROLE_PROMPT}\n\n{prompt}",
        context_blocks=_context_from_hits(hits),
        temperature=0.4,
    )
    return {
        "script": result.get("content", ""),
        "provider_used": result.get("provider", provider_config.get("provider_name", "mock")),
        "model_used": result.get("model", provider_config.get("model", "")),
        "warning": result.get("warning", ""),
        "fallback_used": result.get("fallback_used", False),
        "intent": retrieval.get("intent", "generate_script"),
        "applied_filters": retrieval.get("applied_filters", {}),
        "retrieved_chunks": [item["text"] for item in hits],
        "retrieved_metadata": [item["metadata"] for item in hits],
        "sources": _source_cards(hits),
    }


def generate_learning_summary(
    role: str,
    score: int,
    unlocked_nodes: List[str],
    provider_config: Dict[str, Any],
) -> Dict[str, Any]:
    """生成闯关结算总结。"""
    query = " ".join(unlocked_nodes) if unlocked_nodes else "长征精神"
    retrieval = retrieve_knowledge(question=query, filters={"intent": "timeline"}, top_k=4)
    hits = retrieval["hits"]
    client = get_llm_client(provider_config)
    prompt = build_game_summary_prompt(
        role=role,
        score=score,
        unlocked_nodes="、".join(unlocked_nodes) if unlocked_nodes else "暂无",
        context="\n\n".join(_context_from_hits(hits)),
    )
    result = client.generate_with_context(
        prompt=f"{LONG_MARCH_GUIDE_ROLE_PROMPT}\n\n{prompt}",
        context_blocks=_context_from_hits(hits),
        temperature=0.4,
    )
    return {
        "summary": result.get("content", ""),
        "warning": result.get("warning", ""),
        "fallback_used": result.get("fallback_used", False),
        "recommend_topics": ["遵义会议", "湘江战役", "长征精神"],
        "retrieved_metadata": [item["metadata"] for item in hits],
        "sources": _source_cards(hits),
    }
