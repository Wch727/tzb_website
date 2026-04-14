"""混合检索与上下文组装。"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from context_builder import build_context
from rag_intent import build_where, expand_filter_variants, merge_filters
from rag_store import ensure_default_knowledge_base, query_by_vector, snapshot_items
from utils import get_settings


QUERY_STOPWORDS = {
    "为什么",
    "是什么",
    "怎么",
    "如何",
    "哪些",
    "哪里",
    "意义",
    "原因",
    "介绍",
    "一段",
    "写一段",
    "生成",
    "讲解稿",
    "脚本",
    "视频",
    "短视频",
    "解析",
    "题目",
    "问题",
    "长征",
    "历史",
}


def _chunk_identity(metadata: Dict[str, Any], fallback_index: int = 0) -> str:
    return metadata.get("chunk_id") or (
        f"{metadata.get('source_file', 'source')}::{metadata.get('title', '未命名')}::{metadata.get('source_page', 'no-page')}::{fallback_index}"
    )


def _query_terms(question: str, target: str = "") -> List[str]:
    terms: List[str] = []
    if target:
        terms.append(target)
    raw_terms = re.findall(r"[\u4e00-\u9fffA-Za-z0-9]{2,}", question or "")
    for term in raw_terms:
        if term in QUERY_STOPWORDS:
            continue
        if term not in terms:
            terms.append(term)
    return terms[:10]


def _split_meta_terms(value: Any) -> List[str]:
    raw = str(value or "")
    for old in ["；", ";", ",", "，", "||"]:
        raw = raw.replace(old, "、")
    return [part.strip() for part in raw.split("、") if part.strip()]


def _keyword_score(item: Dict[str, Any], query_terms: List[str], debug_info: Dict[str, Any], filters: Dict[str, Any]) -> float:
    metadata = item.get("metadata", {}) or {}
    text = str(item.get("text", "") or "")
    title = str(metadata.get("title", "") or "")
    source_type = str(metadata.get("source_type", "raw_book") or "raw_book")
    target = str(debug_info.get("target", "") or "")
    target_type = str(debug_info.get("target_type", "") or "")

    score = 0.0
    if target:
        if target == title:
            score += 140.0
        elif target in title:
            score += 110.0
        elif target in text:
            score += 70.0
    if target_type and metadata.get("type") == target_type:
        score += 28.0
    if filters.get("route_stage") and str(filters.get("route_stage")) == str(metadata.get("route_stage", "")):
        score += 24.0
    if filters.get("place") and str(filters.get("place")) in str(metadata.get("place", "")):
        score += 18.0
    if debug_info.get("intent") == metadata.get("intent_hint"):
        score += 12.0
    if source_type == "structured_card":
        score += 26.0
    elif source_type == "uploaded_doc":
        score += 8.0
    else:
        score += 4.0

    meta_terms = set(_split_meta_terms(metadata.get("keywords", "")) + _split_meta_terms(metadata.get("aliases", "")))
    for term in query_terms:
        if term in title:
            score += 16.0
        elif term in meta_terms:
            score += 12.0
        elif term in text:
            score += 4.0

    if metadata.get("summary") and source_type == "structured_card":
        score += 6.0
    return score


def keyword_search(question: str, variants: List[Dict[str, Any]], limit: int, debug_info: Dict[str, Any]) -> List[Dict[str, Any]]:
    """执行关键词检索。"""
    query_terms = _query_terms(question, target=debug_info.get("target", ""))
    merged: Dict[str, Dict[str, Any]] = {}
    for variant in variants:
        for item in snapshot_items(build_where(variant)):
            metadata = item.get("metadata", {}) or {}
            item_id = _chunk_identity(metadata)
            score = _keyword_score(item, query_terms, debug_info, variant)
            if score <= 0:
                continue
            candidate = item.copy()
            candidate["keyword_score"] = round(score, 4)
            old = merged.get(item_id)
            if old is None or candidate["keyword_score"] > old.get("keyword_score", 0.0):
                merged[item_id] = candidate
    ranked = sorted(merged.values(), key=lambda item: item.get("keyword_score", 0.0), reverse=True)
    for rank, item in enumerate(ranked, start=1):
        item["keyword_rank"] = rank
    return ranked[: max(limit, 6)]


def vector_search(question: str, variants: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
    """执行向量检索。"""
    merged_hits: Dict[str, Dict[str, Any]] = {}
    for variant in variants:
        for index, hit in enumerate(query_by_vector(question, build_where(variant), max(limit, 6)), start=1):
            item_id = _chunk_identity(hit.get("metadata", {}) or {}, fallback_index=index)
            old = merged_hits.get(item_id)
            if old is None or hit.get("distance", 99.0) < old.get("distance", 99.0):
                merged_hits[item_id] = hit
    ranked = sorted(merged_hits.values(), key=lambda item: item.get("distance", 99.0))
    for rank, item in enumerate(ranked, start=1):
        item["vector_rank"] = rank
    return ranked[: max(limit, 6)]


def _fusion_bonus(item: Dict[str, Any], debug_info: Dict[str, Any], filters: Dict[str, Any]) -> float:
    metadata = item.get("metadata", {}) or {}
    bonus = 0.0
    target = str(debug_info.get("target", "") or "")
    if target and target == str(metadata.get("title", "") or ""):
        bonus += 0.30
    if target and target in str(item.get("text", "") or ""):
        bonus += 0.08
    if metadata.get("source_type") == "structured_card":
        bonus += 0.12
    priority = int(metadata.get("priority", 0) or 0)
    bonus += min(priority / 1000.0, 0.12)
    if filters.get("route_stage") and filters.get("route_stage") == metadata.get("route_stage"):
        bonus += 0.05
    if filters.get("place") and str(filters.get("place")) in str(metadata.get("place", "")):
        bonus += 0.03
    return bonus


def fuse_hits(
    keyword_hits: List[Dict[str, Any]],
    vector_hits: List[Dict[str, Any]],
    limit: int,
    debug_info: Dict[str, Any],
    filters: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """使用轻量 RRF 融合关键词检索与向量检索。"""
    fused: Dict[str, Dict[str, Any]] = {}
    rrf_k = 50.0

    for rank, item in enumerate(keyword_hits, start=1):
        metadata = item.get("metadata", {}) or {}
        item_id = _chunk_identity(metadata, fallback_index=rank)
        entry = fused.setdefault(item_id, {"text": item.get("text", ""), "metadata": metadata.copy()})
        entry["keyword_score"] = item.get("keyword_score", 0.0)
        entry["keyword_rank"] = rank
        entry["hybrid_score"] = entry.get("hybrid_score", 0.0) + (1.0 / (rrf_k + rank))

    for rank, item in enumerate(vector_hits, start=1):
        metadata = item.get("metadata", {}) or {}
        item_id = _chunk_identity(metadata, fallback_index=rank)
        entry = fused.setdefault(item_id, {"text": item.get("text", ""), "metadata": metadata.copy()})
        entry["distance"] = item.get("distance", 99.0)
        entry["vector_score"] = item.get("vector_score", 0.0)
        entry["vector_rank"] = rank
        entry["hybrid_score"] = entry.get("hybrid_score", 0.0) + (1.0 / (rrf_k + rank))

    ranked: List[Dict[str, Any]] = []
    for item in fused.values():
        item["hybrid_score"] = round(item.get("hybrid_score", 0.0) + _fusion_bonus(item, debug_info, filters), 6)
        ranked.append(item)
    ranked.sort(key=lambda item: item.get("hybrid_score", 0.0), reverse=True)
    for rank, item in enumerate(ranked, start=1):
        item["hybrid_rank"] = rank
    return ranked[: max(limit, 6)]


def retrieve_knowledge(
    question: str,
    filters: Optional[Dict[str, Any]] = None,
    top_k: Optional[int] = None,
) -> Dict[str, Any]:
    """执行带意图识别的结构化混合检索。"""
    ensure_default_knowledge_base()
    settings = {"retrieval_top_k": 5}
    settings.update(get_settings())
    limit = top_k or int(settings.get("retrieval_top_k", 5))
    debug_info = merge_filters(question=question, filters=filters)
    variants = expand_filter_variants(debug_info["filters"])

    keyword_hits = keyword_search(question=question, variants=variants, limit=max(limit * 2, 6), debug_info=debug_info)
    vector_hits = vector_search(question=question, variants=variants, limit=max(limit * 2, 6))
    fused_hits = fuse_hits(
        keyword_hits=keyword_hits,
        vector_hits=vector_hits,
        limit=max(limit * 2, 6),
        debug_info=debug_info,
        filters=debug_info["filters"],
    )
    hits = fused_hits[:limit]
    context_payload = build_context(
        query=question,
        retrieved_items=hits,
        intent=debug_info["intent"],
        target=debug_info["target"],
    )
    return {
        "hits": hits,
        "intent": debug_info["intent"],
        "target": debug_info["target"],
        "target_type": debug_info.get("target_type", ""),
        "applied_filters": debug_info["filters"],
        "entities": debug_info["entities"],
        "keyword_hits": keyword_hits,
        "vector_hits": vector_hits,
        "fused_hits": fused_hits,
        "context_payload": context_payload,
    }


def search_knowledge(
    question: str,
    filters: Optional[Dict[str, Any]] = None,
    top_k: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """兼容旧调用的检索入口。"""
    return retrieve_knowledge(question=question, filters=filters, top_k=top_k)["hits"]
