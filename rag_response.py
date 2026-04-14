"""RAG 回答、fallback 与调试输出。"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from content_store import build_source_card, build_static_sources_for_node, load_spirit_topics, match_faq, match_route_node
from llm import get_llm_client
from prompts import LONG_MARCH_GUIDE_ROLE_PROMPT, build_rag_qa_prompt, format_context_blocks
from rag_search import retrieve_knowledge


def _fit_text_range(text: str, min_chars: int, max_chars: int) -> str:
    """把静态输出控制在更适合展陈的长度区间。"""
    cleaned = str(text or "").strip()
    if len(cleaned) <= max_chars:
        return cleaned
    window = cleaned[:max_chars]
    cut = max(window.rfind("。"), window.rfind("！"), window.rfind("？"))
    if cut >= min_chars:
        return window[: cut + 1].strip()
    return window.rstrip("，；、 ") + "。"


def format_source_cards(hits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """整理前端展示依据所需的信息。"""
    cards: List[Dict[str, Any]] = []
    for item in hits:
        metadata = item.get("metadata", {}) or {}
        cards.append(
            {
                "source_file": metadata.get("source_file", "未知文件"),
                "source_type": metadata.get("source_type", "unknown"),
                "title": metadata.get("title", "未命名"),
                "type": metadata.get("type", "未知"),
                "topic": metadata.get("topic", ""),
                "place": metadata.get("place", ""),
                "route_stage": metadata.get("route_stage", ""),
                "chapter_title": metadata.get("chapter_title", ""),
                "section_title": metadata.get("section_title", ""),
                "source_page": metadata.get("source_page", ""),
                "chunk_id": metadata.get("chunk_id", ""),
                "snippet": item.get("text", "")[:220],
            }
        )
    return cards


def _summarize_hits(hits: List[Dict[str, Any]], limit: int = 4) -> str:
    lines: List[str] = []
    for index, item in enumerate(hits[:limit], start=1):
        metadata = item.get("metadata", {}) or {}
        text = str(item.get("text", "") or "").replace("\n", " ").strip()
        lines.append(f"{index}. {metadata.get('title', '未命名')}：{text[:120]}{'…' if len(text) > 120 else ''}")
    return "\n".join(lines)


def fallback_answer(
    question: str,
    matched_node: Optional[Dict[str, Any]],
    matched_faq: Optional[Dict[str, Any]],
    retrieved_hits: Optional[List[Dict[str, Any]]] = None,
    context_payload: Optional[Dict[str, Any]] = None,
    intent: str = "general",
    target: str = "",
) -> str:
    """无 LLM 时输出完整、正式的静态答案。"""
    node = matched_node or {}
    faq = matched_faq or {}
    hits = retrieved_hits or []
    context = context_payload or {}

    topic = target or node.get("title") or faq.get("title") or question
    background = context.get("background", []) or [node.get("background", "")]
    process = context.get("process", []) or [node.get("process", "")]
    significance = context.get("significance", []) or [node.get("significance", "")]
    figures = context.get("figures", []) or (["、".join(node.get("figures", []))] if node.get("figures") else [])
    raw_details = context.get("raw_details", []) or [_summarize_hits(hits)]

    sections: List[str] = [f"围绕“{topic}”来看，这一问题需要放在长征主线和历史转折中理解。"]
    if faq.get("answer"):
        sections.append(str(faq.get("answer", "")).strip())
    if any(background):
        sections.append(f"从历史背景看，{background[0]}")
    if any(process):
        sections.append(f"从事件经过看，{process[0]}")
    if any(significance):
        sections.append(f"从历史意义看，{significance[0]}")
    if any(figures):
        sections.append(f"相关关键人物主要包括：{figures[0]}。")
    if raw_details and raw_details[0]:
        sections.append(f"结合资料细节，还可以看到：{raw_details[0]}")
    if faq.get("extended_note"):
        sections.append(str(faq.get("extended_note", "")).strip())
    elif intent in {"spirit", "faq", "general"}:
        spirit_titles = "、".join(item.get("title", "") for item in load_spirit_topics()[:4])
        if spirit_titles:
            sections.append(f"若继续延伸，可进一步结合{spirit_titles}等专题理解这一问题。")

    answer = "\n\n".join(part for part in sections if str(part).strip())
    if len(answer) < 220 and hits:
        answer = f"{answer}\n\n资料依据补充：{_summarize_hits(hits)}"
    return _fit_text_range(answer, min_chars=240, max_chars=420)


def ask(
    question: str,
    provider_config: Dict[str, Any],
    filters: Optional[Dict[str, Any]] = None,
    top_k: Optional[int] = None,
) -> Dict[str, Any]:
    """长征史 RAG 问答入口。"""
    retrieval = retrieve_knowledge(question=question, filters=filters, top_k=top_k)
    hits = retrieval["hits"]
    context_payload = retrieval.get("context_payload", {})
    matched_node = match_route_node(question)
    matched_faq = match_faq(question)

    source_cards = context_payload.get("source_cards", []) or format_source_cards(hits)
    if matched_node:
        source_cards = build_static_sources_for_node(matched_node, [matched_faq] if matched_faq else [])[:1] + source_cards
    elif matched_faq:
        source_cards = [
            build_source_card(
                {
                    "title": matched_faq.get("title", "长征史问答"),
                    "type": matched_faq.get("type", "faq"),
                    "source_file": "data/faq.csv",
                    "summary": matched_faq.get("answer", ""),
                },
                snippet=matched_faq.get("answer", ""),
            )
        ] + source_cards

    prompt = build_rag_qa_prompt(question=question, context=format_context_blocks(context_payload.get("context_blocks", [])))
    static_mode = bool(provider_config.get("static_mode"))
    result: Dict[str, Any] = {}
    if not static_mode:
        client = get_llm_client(provider_config)
        result = client.chat(
            messages=[
                {"role": "system", "content": LONG_MARCH_GUIDE_ROLE_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            stream=False,
        )
    answer = result.get("content", "").strip()
    use_static = (
        static_mode
        or not answer
        or len(answer) < 180
        or result.get("fallback_used", False)
        or result.get("provider") == "mock"
    )
    if use_static:
        answer = fallback_answer(
            question=question,
            matched_node=matched_node,
            matched_faq=matched_faq,
            retrieved_hits=hits,
            context_payload=context_payload,
            intent=retrieval.get("intent", "general"),
            target=retrieval.get("target", ""),
        )
    provider_used = "static" if use_static else result.get("provider", provider_config.get("provider_name", "mock"))
    model_used = "builtin-longmarch-content" if use_static else result.get("model", provider_config.get("model", ""))
    return {
        "answer": answer,
        "provider_used": provider_used,
        "model_used": model_used,
        "warning": result.get("warning", ""),
        "fallback_used": bool(use_static and not static_mode),
        "mode_label": "知识导览模式" if use_static else "智能讲解增强",
        "intent": retrieval.get("intent", "general"),
        "target": retrieval.get("target", ""),
        "applied_filters": retrieval.get("applied_filters", {}),
        "retrieved_chunks": [item["text"] for item in hits],
        "retrieved_metadata": [item["metadata"] for item in hits],
        "source_file": [item["source_file"] for item in source_cards],
        "title": [item["title"] for item in source_cards],
        "sources": source_cards,
        "context_text": context_payload.get("context_text", ""),
        "output_length": len(answer),
    }


def test_retrieval(
    question: str,
    filters: Optional[Dict[str, Any]] = None,
    top_k: Optional[int] = None,
) -> Dict[str, Any]:
    """用于管理员后台调试检索。"""
    retrieval = retrieve_knowledge(question=question, filters=filters, top_k=top_k)
    hits = retrieval["hits"]
    preview_answer = fallback_answer(
        question=question,
        matched_node=match_route_node(question),
        matched_faq=match_faq(question),
        retrieved_hits=hits,
        context_payload=retrieval.get("context_payload", {}),
        intent=retrieval.get("intent", "general"),
        target=retrieval.get("target", ""),
    )
    return {
        "question": question,
        "intent": retrieval.get("intent", "general"),
        "target": retrieval.get("target", ""),
        "target_type": retrieval.get("target_type", ""),
        "applied_filters": retrieval.get("applied_filters", {}),
        "entities": retrieval.get("entities", {}),
        "hit_count": len(hits),
        "keyword_hits": [
            {
                "title": item.get("metadata", {}).get("title", "未命名"),
                "type": item.get("metadata", {}).get("type", "未知"),
                "source_type": item.get("metadata", {}).get("source_type", "unknown"),
                "keyword_score": round(float(item.get("keyword_score", 0.0)), 4),
                "snippet": item.get("text", "")[:180],
            }
            for item in retrieval.get("keyword_hits", [])[:8]
        ],
        "vector_hits": [
            {
                "title": item.get("metadata", {}).get("title", "未命名"),
                "type": item.get("metadata", {}).get("type", "未知"),
                "source_type": item.get("metadata", {}).get("source_type", "unknown"),
                "distance": round(float(item.get("distance", 0.0)), 4),
                "vector_score": round(float(item.get("vector_score", 0.0)), 4),
                "snippet": item.get("text", "")[:180],
            }
            for item in retrieval.get("vector_hits", [])[:8]
        ],
        "fused_hits": [
            {
                "title": item.get("metadata", {}).get("title", "未命名"),
                "type": item.get("metadata", {}).get("type", "未知"),
                "source_type": item.get("metadata", {}).get("source_type", "unknown"),
                "hybrid_score": round(float(item.get("hybrid_score", 0.0)), 6),
                "snippet": item.get("text", "")[:180],
            }
            for item in retrieval.get("fused_hits", [])[:8]
        ],
        "hits": [
            {
                "distance": round(float(item.get("distance", 0.0)), 4) if item.get("distance") is not None else None,
                "hybrid_score": round(float(item.get("hybrid_score", 0.0)), 6),
                "text": item.get("text", ""),
                "metadata": item.get("metadata", {}),
            }
            for item in hits
        ],
        "context": retrieval.get("context_payload", {}).get("context_text", ""),
        "answer_preview": preview_answer,
        "output_length": len(preview_answer),
        "fallback_used": True,
        "sources": format_source_cards(hits),
    }
