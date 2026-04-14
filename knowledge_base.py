"""结构化知识卡与原始文档的统一入口。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from chunking import attach_metadata
from content_store import (
    load_events_data,
    load_faq_items,
    load_figures_data,
    load_places_data,
    load_route_nodes_data,
    load_spirit_topics,
)
from file_loader import load_file
from utils import DATA_DIR, UPLOAD_DIR, get_settings, normalize_knowledge_type


STRUCTURED_SOURCE_FILES = {
    "events.json",
    "figures.json",
    "places.json",
    "route_nodes.json",
    "faq.csv",
    "spirit.json",
}

PREBUILT_CHUNKS_PATH = DATA_DIR / "prebuilt_uploaded_chunks.jsonl"


def _split_terms(text: str) -> List[str]:
    """拆分关键词字段。"""
    raw = str(text or "").replace("；", "、").replace(";", "、").replace(",", "、")
    return [part.strip() for part in raw.split("、") if part.strip()]


def _keyword_list(item: Dict[str, Any]) -> List[str]:
    """从静态内容中提取关键词。"""
    keywords: List[str] = []
    for value in [
        item.get("title", ""),
        item.get("topic", ""),
        item.get("route_stage", ""),
        item.get("place", ""),
        item.get("role", ""),
    ]:
        text = str(value or "").strip()
        if text and text not in keywords:
            keywords.append(text)
    for key in ["figures", "key_points"]:
        for value in item.get(key, []) or []:
            text = str(value or "").strip()
            if text and text not in keywords:
                keywords.append(text)
    for value in _split_terms(item.get("keywords", "")):
        if value not in keywords:
            keywords.append(value)
    return keywords


def _alias_list(item: Dict[str, Any], keywords: List[str]) -> List[str]:
    """补充目标识别时可用的别名。"""
    aliases: List[str] = []
    for value in [item.get("title", ""), item.get("id", ""), item.get("route_stage", ""), item.get("place", "")]:
        text = str(value or "").strip()
        if text and text not in aliases:
            aliases.append(text)
    for key in ["figures", "key_points"]:
        for value in item.get(key, []) or []:
            text = str(value or "").strip()
            if text and text not in aliases:
                aliases.append(text)
    for value in keywords:
        if value and value not in aliases:
            aliases.append(value)
    return aliases


def _card_priority(item_type: str) -> int:
    """给结构化卡设置优先级。"""
    mapping = {
        "route": 120,
        "event": 115,
        "faq": 112,
        "spirit": 110,
        "figure": 108,
        "place": 106,
    }
    return mapping.get(item_type, 96)


def _card_intent_hint(item_type: str) -> str:
    """为结构化卡补充默认意图提示。"""
    mapping = {
        "route": "timeline",
        "event": "event",
        "faq": "faq",
        "spirit": "spirit",
        "figure": "figure",
        "place": "place",
    }
    return mapping.get(item_type, "general")


def _card_source_file(item_type: str) -> str:
    """为不同卡片类型补充来源文件名。"""
    mapping = {
        "route": "data/route_nodes.json",
        "event": "data/events.json",
        "figure": "data/figures.json",
        "place": "data/places.json",
        "faq": "data/faq.csv",
        "spirit": "data/spirit.json",
    }
    return mapping.get(item_type, "data/static_cards.json")


def _row_to_structured_card(item: Dict[str, Any], item_type: str) -> Dict[str, Any]:
    """把静态内容统一整理为结构化知识卡。"""
    normalized_type = normalize_knowledge_type(item_type)
    title = str(item.get("title", item.get("question", "")) or "").strip()
    summary = str(item.get("summary", item.get("answer", "")) or "").strip()
    background = str(item.get("background", item.get("detail", "")) or "").strip()
    process = str(item.get("process", item.get("answer", "")) or "").strip()
    significance = str(item.get("significance", item.get("extended_note", "")) or "").strip()
    figures = item.get("figures", []) if isinstance(item.get("figures"), list) else []
    keywords = _keyword_list(item)
    aliases = _alias_list(item, keywords)
    return {
        "id": f"{normalized_type}::{item.get('id', title)}",
        "card_type": f"{normalized_type}_card",
        "title": title,
        "type": normalized_type,
        "source_type": "structured_card",
        "source_file": _card_source_file(normalized_type),
        "source_page": str(item.get("source_page", "") or ""),
        "chapter_title": str(item.get("chapter_title", "") or ""),
        "section_title": str(item.get("section_title", "") or ""),
        "summary": summary,
        "background": background,
        "process": process,
        "significance": significance,
        "figures": figures,
        "place": str(item.get("place", "") or ""),
        "route_stage": str(item.get("route_stage", "") or ""),
        "keywords": keywords,
        "aliases": aliases,
        "priority": int(item.get("priority", _card_priority(normalized_type))),
        "intent_hint": str(item.get("intent_hint", _card_intent_hint(normalized_type))),
        "date": str(item.get("date", "") or ""),
        "topic": str(item.get("topic", "长征史") or "长征史"),
    }


def load_structured_cards() -> List[Dict[str, Any]]:
    """统一加载结构化知识卡。"""
    cards: List[Dict[str, Any]] = []
    cards.extend(_row_to_structured_card(item, "route") for item in load_route_nodes_data())
    cards.extend(_row_to_structured_card(item, "event") for item in load_events_data())
    cards.extend(_row_to_structured_card(item, "figure") for item in load_figures_data())
    cards.extend(_row_to_structured_card(item, "place") for item in load_places_data())
    cards.extend(_row_to_structured_card(item, "faq") for item in load_faq_items())
    cards.extend(_row_to_structured_card(item, "spirit") for item in load_spirit_topics())
    return cards


def structured_card_to_doc(card: Dict[str, Any]) -> Dict[str, Any]:
    """把结构化卡转成检索友好的文档对象。"""
    figures = "、".join(card.get("figures", []) or [])
    keywords = "、".join(card.get("keywords", []) or [])
    aliases = "、".join(card.get("aliases", []) or [])
    text_parts = [
        f"【{card.get('title', '')}｜结构化知识卡】",
        f"摘要：{card.get('summary', '')}",
        f"历史背景：{card.get('background', '')}",
        f"事件经过：{card.get('process', '')}",
        f"历史意义：{card.get('significance', '')}",
        f"关键人物：{figures}" if figures else "",
        f"地点：{card.get('place', '')}" if card.get("place") else "",
        f"路线阶段：{card.get('route_stage', '')}" if card.get("route_stage") else "",
        f"关键词：{keywords}" if keywords else "",
        f"别名：{aliases}" if aliases else "",
    ]
    metadata = {
        "source_file": card.get("source_file", "data/static_cards.json"),
        "source_type": "structured_card",
        "doc_type": "structured_card",
        "title": card.get("title", ""),
        "chapter_title": card.get("chapter_title", ""),
        "section_title": card.get("section_title", ""),
        "type": card.get("type", "event"),
        "route_stage": card.get("route_stage", ""),
        "place": card.get("place", ""),
        "date": card.get("date", ""),
        "figures": "、".join(card.get("figures", []) or []),
        "keywords": "、".join(card.get("keywords", []) or []),
        "aliases": "、".join(card.get("aliases", []) or []),
        "priority": int(card.get("priority", 100)),
        "intent_hint": card.get("intent_hint", "general"),
        "topic": card.get("topic", "长征史"),
        "summary": card.get("summary", ""),
        "background": card.get("background", ""),
        "process": card.get("process", ""),
        "significance": card.get("significance", ""),
        "source_page": card.get("source_page", ""),
        "source_page_start": card.get("source_page", ""),
        "source_page_end": card.get("source_page", ""),
        "card_id": card.get("id", ""),
    }
    return {"text": "\n".join(part for part in text_parts if part.strip()), "metadata": metadata}


def _mark_raw_doc_source(docs: List[Dict[str, Any]], source_type: str) -> List[Dict[str, Any]]:
    """给原始文档打上来源类型。"""
    prepared: List[Dict[str, Any]] = []
    for doc in docs:
        metadata = doc.get("metadata", {}).copy()
        metadata["source_type"] = source_type
        metadata["priority"] = int(metadata.get("priority", 40 if source_type == "raw_book" else 35))
        metadata["intent_hint"] = metadata.get("intent_hint", "general")
        metadata["keywords"] = metadata.get("keywords", "")
        metadata["aliases"] = metadata.get("aliases", "")
        prepared.append({"text": doc.get("text", ""), "metadata": metadata})
    return prepared


def load_raw_docs(paths: Optional[List[Path]] = None, source_type: str = "uploaded_doc") -> List[Dict[str, Any]]:
    """加载原始文档块。"""
    docs: List[Dict[str, Any]] = []
    for path in paths or []:
        parsed = load_file(path)
        docs.extend(parsed.get("docs", []))
    return _mark_raw_doc_source(docs, source_type=source_type)


def load_repository_raw_docs() -> List[Dict[str, Any]]:
    """加载仓库内置的原始资料文档。"""
    paths = [
        path
        for path in sorted(DATA_DIR.iterdir(), key=lambda item: item.name.lower())
        if path.is_file()
        and path.name not in STRUCTURED_SOURCE_FILES
        and path.suffix.lower() in [".pdf", ".docx", ".txt", ".md"]
    ]
    return load_raw_docs(paths, source_type="raw_book")


def load_uploaded_raw_docs() -> List[Dict[str, Any]]:
    """加载管理员上传的原始资料。"""
    paths = [path for path in sorted(UPLOAD_DIR.iterdir(), key=lambda item: item.name.lower()) if path.is_file()]
    return load_raw_docs(paths, source_type="uploaded_doc")


def load_prebuilt_chunk_docs(path: Path = PREBUILT_CHUNKS_PATH) -> List[Dict[str, Any]]:
    """加载已经预切分好的本地 chunk。"""
    if not path.exists():
        return []

    docs: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        payload = json.loads(line)
        metadata = (payload.get("metadata", {}) or {}).copy()
        metadata["source_type"] = str(metadata.get("source_type", "prebuilt_chunk") or "prebuilt_chunk")
        metadata["pre_chunked"] = True
        metadata["priority"] = int(metadata.get("priority", 72))
        docs.append({"text": str(payload.get("text", "") or ""), "metadata": metadata})
    return docs


def export_uploaded_docs_as_prebuilt_chunks(path: Path = PREBUILT_CHUNKS_PATH) -> Dict[str, Any]:
    """把本地上传资料导出为可跟仓库走的 chunk 文件。"""
    uploaded_docs = load_uploaded_raw_docs()
    if not uploaded_docs:
        if path.exists():
            path.unlink()
        return {
            "message": "当前没有本地上传资料，未生成预构建 chunk 文件。",
            "chunk_count": 0,
            "source_files": [],
            "output_file": str(path),
        }

    settings = get_settings()
    chunk_size = int(settings.get("chunk_size", 520))
    overlap = int(settings.get("chunk_overlap", 90))
    chunked_docs = attach_metadata(uploaded_docs, chunk_size=chunk_size, overlap=overlap)

    lines: List[str] = []
    source_files = set()
    for item in chunked_docs:
        metadata = (item.get("metadata", {}) or {}).copy()
        metadata["source_type"] = "prebuilt_chunk"
        metadata["origin_source_type"] = metadata.get("origin_source_type", "uploaded_doc")
        metadata["pre_chunked"] = True
        metadata["priority"] = int(metadata.get("priority", 72))
        metadata["source_file"] = str(metadata.get("source_file", "") or "")
        if metadata["source_file"]:
            source_files.add(metadata["source_file"])
        lines.append(
            json.dumps(
                {
                    "text": str(item.get("text", "") or ""),
                    "metadata": metadata,
                },
                ensure_ascii=False,
            )
        )

    path.write_text("\n".join(lines), encoding="utf-8")
    return {
        "message": "已将本地上传资料导出为预构建 chunk 文件。",
        "chunk_count": len(chunked_docs),
        "source_files": sorted(source_files),
        "output_file": str(path),
    }


def build_knowledge_base(
    include_structured: bool = True,
    include_repository_raw: bool = True,
    include_prebuilt_chunks: bool = True,
) -> Dict[str, Any]:
    """构建知识库所需的双层内容。"""
    structured_cards = load_structured_cards() if include_structured else []
    structured_docs = [structured_card_to_doc(card) for card in structured_cards]
    repository_raw_docs = load_repository_raw_docs() if include_repository_raw else []
    prebuilt_chunk_docs = load_prebuilt_chunk_docs() if include_prebuilt_chunks else []
    return {
        "structured_cards": structured_cards,
        "structured_docs": structured_docs,
        "raw_docs": repository_raw_docs + prebuilt_chunk_docs,
        "repository_raw_docs": repository_raw_docs,
        "prebuilt_chunk_docs": prebuilt_chunk_docs,
        "all_docs": structured_docs + repository_raw_docs + prebuilt_chunk_docs,
    }


def load_card_targets() -> List[Dict[str, str]]:
    """为 query intent 识别提供可匹配目标列表。"""
    targets: List[Dict[str, str]] = []
    for card in load_structured_cards():
        targets.append(
            {
                "title": str(card.get("title", "") or ""),
                "type": str(card.get("type", "event") or "event"),
                "route_stage": str(card.get("route_stage", "") or ""),
                "place": str(card.get("place", "") or ""),
                "aliases": "||".join(card.get("aliases", []) or []),
                "keywords": "||".join(card.get("keywords", []) or []),
            }
        )
    return targets
