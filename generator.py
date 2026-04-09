"""内容生成模块。"""

from __future__ import annotations

from typing import Any, Dict, List

from content_store import build_static_sources_for_node, get_route_node_data, match_route_node
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


def _static_context_summary(hits: List[Dict[str, Any]]) -> str:
    """把检索结果整理成适合静态模式使用的摘要。"""
    sections: List[str] = []
    for index, item in enumerate(hits[:4], start=1):
        metadata = item.get("metadata", {})
        snippet = str(item.get("text", "") or "").replace("\n", " ").strip()
        sections.append(
            f"{index}. {metadata.get('title', '未命名')}："
            f"{snippet[:120]}{'...' if len(snippet) > 120 else ''}"
        )
    return "\n".join(sections)


def _match_node_data(topic: str) -> Dict[str, Any]:
    """根据主题匹配节点数据。"""
    direct = get_route_node_data(topic)
    if direct:
        return direct
    matched = match_route_node(topic)
    return matched or {}


def fallback_guide_script(
    topic: str,
    audience: str,
    duration: str,
    node_data: Dict[str, Any],
    hits: List[Dict[str, Any]] | None = None,
) -> str:
    """无 LLM 时输出完整讲解稿。"""
    node = node_data or {}
    title = node.get("title", topic or "长征史专题")
    background = node.get("background", "")
    process = node.get("process", "")
    significance = node.get("significance", "")
    summary = node.get("summary", "")
    figures = "、".join(node.get("figures", [])[:4]) if node.get("figures") else "长征中的重要领导人与广大红军指战员"
    points = "；".join(node.get("key_points", [])[:4]) if node.get("key_points") else _static_context_summary(hits or [])
    return (
        f"《{title}》讲解稿\n\n"
        f"一、开场引入\n"
        f"各位{audience}，下面我们围绕“{title}”展开导览。本段内容适合约{duration}的现场讲解，"
        "重点帮助大家把握长征主线中的关键转折、典型场景与精神内涵。\n\n"
        f"二、历史背景\n{background or summary or '这一节点处在长征主线的重要阶段，是理解战略转移全局的关键入口。'}\n\n"
        f"三、事件经过\n{process or '这一节点记录了红军在复杂敌情与艰险环境中作出的关键行动。'}\n\n"
        f"四、关键人物\n本节点涉及的主要人物包括：{figures}。他们在组织指挥、思想统一和部队行动方面发挥了重要作用。\n\n"
        f"五、历史意义\n{significance or '这一节点不仅影响了红军的行军路线，也加深了党对战略方向和革命道路的认识。'}\n\n"
        f"六、讲解提示\n可重点提醒听众关注以下要点：{points or '结合时间、地点、人物和意义进行理解。'}\n\n"
        "七、结语\n从这一节点可以看到，长征并不是单纯的远距离行军，而是在极端艰难条件下进行的一次伟大战略转移，"
        "也是中国共产党和红军在实践中不断校正方向、锤炼意志、凝聚精神的重要历程。"
    )


def fallback_video_script(
    topic: str,
    audience: str,
    style: str,
    node_data: Dict[str, Any],
    hits: List[Dict[str, Any]] | None = None,
) -> str:
    """无 LLM 时输出完整短视频脚本。"""
    node = node_data or {}
    title = node.get("title", topic or "长征史专题")
    summary = node.get("summary", "")
    background = node.get("background", "")
    process = node.get("process", "")
    significance = node.get("significance", "")
    static_context = _static_context_summary(hits or [])
    return (
        f"标题：《{title}》\n"
        f"受众：{audience}\n"
        f"风格：{style}\n\n"
        "镜头一：路线图与节点标题出现\n"
        f"旁白：{summary or '从长征主线中的关键节点切入，理解这段波澜壮阔的革命历程。'}\n\n"
        "镜头二：历史背景图文切换\n"
        f"旁白：{background or '这一节点形成于极其严峻的革命形势之中，既体现战略压力，也体现主动求变。'}\n\n"
        "镜头三：事件经过重点呈现\n"
        f"旁白：{process or '红军在复杂环境中完成了一次关键行动，为后续全局转折创造了条件。'}\n\n"
        "镜头四：人物与知识点叠加\n"
        f"字幕：{('、'.join(node.get('figures', [])[:4])) or '重要领导人与广大红军指战员'}\n"
        f"补充：{static_context or '可同步展示路线节点、关键人物和历史照片。'}\n\n"
        "镜头五：历史意义升华\n"
        f"旁白：{significance or '这一节点是长征历史逻辑中的关键环节，也集中体现了理想信念与革命意志。'}\n\n"
        "结尾：精神传承\n"
        "旁白：长征留给后人的，不只是行军路线，更是一种在艰难环境中坚定前行的精神力量。"
    )


def fallback_learning_summary(role: str, score: int, unlocked_nodes: List[str], hits: List[Dict[str, Any]]) -> str:
    """无 LLM 时输出学习总结。"""
    joined_nodes = "、".join(unlocked_nodes[:8]) if unlocked_nodes else "长征主线节点"
    context_text = _static_context_summary(hits)
    return (
        f"本轮学习中，你以“{role}”身份完成了长征史互动闯关，累计得分 {score} 分。"
        f"你已经重点学习了 {joined_nodes} 等节点，对长征的出发背景、路线转折、战略机动和胜利会师形成了较完整的认识。\n\n"
        "建议下一步把这些节点放回整条长征主线中综合理解，尤其关注战略转移、独立自主、群众路线和理想信念之间的关系。\n\n"
        f"本轮知识依据摘要：\n{context_text or '可继续围绕遵义会议、四渡赤水和长征精神展开深化学习。'}"
    )


def generate_guide_script(
    topic: str,
    audience: str,
    duration: str,
    provider_config: Dict[str, Any],
) -> Dict[str, Any]:
    """生成讲解稿。"""
    retrieval = retrieve_knowledge(question=topic, filters={"intent": "generate_script"}, top_k=5)
    hits = retrieval["hits"]
    node_data = _match_node_data(topic)
    prompt = build_guide_script_prompt(
        topic=topic,
        audience=audience,
        duration=duration,
        context="\n\n".join(_context_from_hits(hits)),
    )
    static_mode = bool(provider_config.get("static_mode"))
    result: Dict[str, Any] = {}
    if not static_mode:
        client = get_llm_client(provider_config)
        result = client.generate_with_context(
            prompt=f"{LONG_MARCH_GUIDE_ROLE_PROMPT}\n\n{prompt}",
            context_blocks=_context_from_hits(hits),
            temperature=0.4,
        )
    script = result.get("content", "").strip()
    use_static = static_mode or not script or result.get("fallback_used", False) or result.get("provider") == "mock"
    if use_static:
        script = fallback_guide_script(topic=topic, audience=audience, duration=duration, node_data=node_data, hits=hits)
    sources = _source_cards(hits)
    if node_data:
        sources = build_static_sources_for_node(node_data)[:1] + sources
    provider_used = "static" if use_static else result.get("provider", provider_config.get("provider_name", "mock"))
    model_used = "builtin-longmarch-content" if use_static else result.get("model", provider_config.get("model", ""))
    return {
        "script": script,
        "provider_used": provider_used,
        "model_used": model_used,
        "warning": result.get("warning", ""),
        "fallback_used": bool(use_static and not static_mode),
        "mode_label": "静态展示模式" if use_static else "AI增强模式",
        "intent": retrieval.get("intent", "generate_script"),
        "applied_filters": retrieval.get("applied_filters", {}),
        "retrieved_chunks": [item["text"] for item in hits],
        "retrieved_metadata": [item["metadata"] for item in hits],
        "sources": sources,
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
    node_data = _match_node_data(topic)
    prompt = build_short_video_script_prompt(
        topic=topic,
        audience=audience,
        style=style,
        context="\n\n".join(_context_from_hits(hits)),
    )
    static_mode = bool(provider_config.get("static_mode"))
    result: Dict[str, Any] = {}
    if not static_mode:
        client = get_llm_client(provider_config)
        result = client.generate_with_context(
            prompt=f"{LONG_MARCH_GUIDE_ROLE_PROMPT}\n\n{prompt}",
            context_blocks=_context_from_hits(hits),
            temperature=0.4,
        )
    script = result.get("content", "").strip()
    use_static = static_mode or not script or result.get("fallback_used", False) or result.get("provider") == "mock"
    if use_static:
        script = fallback_video_script(topic=topic, audience=audience, style=style, node_data=node_data, hits=hits)
    sources = _source_cards(hits)
    if node_data:
        sources = build_static_sources_for_node(node_data)[:1] + sources
    provider_used = "static" if use_static else result.get("provider", provider_config.get("provider_name", "mock"))
    model_used = "builtin-longmarch-content" if use_static else result.get("model", provider_config.get("model", ""))
    return {
        "script": script,
        "provider_used": provider_used,
        "model_used": model_used,
        "warning": result.get("warning", ""),
        "fallback_used": bool(use_static and not static_mode),
        "mode_label": "静态展示模式" if use_static else "AI增强模式",
        "intent": retrieval.get("intent", "generate_script"),
        "applied_filters": retrieval.get("applied_filters", {}),
        "retrieved_chunks": [item["text"] for item in hits],
        "retrieved_metadata": [item["metadata"] for item in hits],
        "sources": sources,
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
    prompt = build_game_summary_prompt(
        role=role,
        score=score,
        unlocked_nodes="、".join(unlocked_nodes) if unlocked_nodes else "暂无",
        context="\n\n".join(_context_from_hits(hits)),
    )
    static_mode = bool(provider_config.get("static_mode"))
    result: Dict[str, Any] = {}
    if not static_mode:
        client = get_llm_client(provider_config)
        result = client.generate_with_context(
            prompt=f"{LONG_MARCH_GUIDE_ROLE_PROMPT}\n\n{prompt}",
            context_blocks=_context_from_hits(hits),
            temperature=0.4,
        )
    summary = result.get("content", "").strip()
    use_static = static_mode or not summary or result.get("fallback_used", False) or result.get("provider") == "mock"
    if use_static:
        summary = fallback_learning_summary(role=role, score=score, unlocked_nodes=unlocked_nodes, hits=hits)
    sources = _source_cards(hits)
    return {
        "summary": summary,
        "warning": result.get("warning", ""),
        "fallback_used": bool(use_static and not static_mode),
        "mode_label": "静态展示模式" if use_static else "AI增强模式",
        "recommend_topics": ["遵义会议", "湘江战役", "四渡赤水", "长征精神"],
        "retrieved_metadata": [item["metadata"] for item in hits],
        "sources": sources,
    }
