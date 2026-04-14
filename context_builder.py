"""把检索结果整理为场景化上下文。"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple


def _clean_text(text: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", str(text or "").strip())


def _truncate(text: str, limit: int) -> str:
    text = _clean_text(text)
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "…"


def _unique_texts(items: List[str], limit: int = 3) -> List[str]:
    deduped: List[str] = []
    for item in items:
        text = _clean_text(item)
        if not text or text in deduped:
            continue
        deduped.append(text)
        if len(deduped) >= limit:
            break
    return deduped


def _to_source_card(item: Dict[str, Any]) -> Dict[str, Any]:
    metadata = item.get("metadata", {}) or {}
    return {
        "source_file": metadata.get("source_file", "未知文件"),
        "source_type": metadata.get("source_type", "unknown"),
        "title": metadata.get("title", "未命名"),
        "type": metadata.get("type", "raw"),
        "chapter_title": metadata.get("chapter_title", ""),
        "section_title": metadata.get("section_title", ""),
        "source_page": metadata.get("source_page", ""),
        "snippet": _truncate(item.get("text", ""), 180),
    }


def _extract_structured_fields(items: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    background: List[str] = []
    process: List[str] = []
    significance: List[str] = []
    figures: List[str] = []
    conclusions: List[str] = []
    for item in items:
        metadata = item.get("metadata", {}) or {}
        if metadata.get("summary"):
            conclusions.append(str(metadata.get("summary", "")))
        if metadata.get("background"):
            background.append(str(metadata.get("background", "")))
        if metadata.get("process"):
            process.append(str(metadata.get("process", "")))
        if metadata.get("significance"):
            significance.append(str(metadata.get("significance", "")))
        figures_text = str(metadata.get("figures", "") or "").strip()
        if figures_text:
            figures.append(figures_text)
    return {
        "background": _unique_texts(background),
        "process": _unique_texts(process),
        "significance": _unique_texts(significance),
        "figures": _unique_texts(figures),
        "conclusions": _unique_texts(conclusions),
    }


def _extract_raw_details(items: List[Dict[str, Any]]) -> List[str]:
    details: List[str] = []
    for item in items[:4]:
        metadata = item.get("metadata", {}) or {}
        prefix = f"{metadata.get('title', '资料片段')}"
        page = str(metadata.get("source_page", "") or "").strip()
        if page:
            prefix += f"（第{page}页）"
        details.append(f"{prefix}：{_truncate(item.get('text', ''), 160)}")
    return _unique_texts(details, limit=4)


def build_context(
    query: str,
    retrieved_items: List[Dict[str, Any]],
    intent: str,
    target: str,
) -> Dict[str, Any]:
    """按场景把检索结果整理为结构化上下文。"""

    structured_items = [item for item in retrieved_items if (item.get("metadata", {}) or {}).get("source_type") == "structured_card"]
    raw_items = [item for item in retrieved_items if (item.get("metadata", {}) or {}).get("source_type") != "structured_card"]

    structured_fields = _extract_structured_fields(structured_items)
    raw_details = _extract_raw_details(raw_items)
    source_cards = [_to_source_card(item) for item in retrieved_items]

    topic = target or query
    background = structured_fields["background"] or [item.get("text", "") for item in raw_items[:1]]
    process = structured_fields["process"] or [item.get("text", "") for item in raw_items[1:2]]
    significance = structured_fields["significance"] or [item.get("text", "") for item in raw_items[2:3]]
    conclusions = structured_fields["conclusions"]
    figures = structured_fields["figures"]

    sections: List[Tuple[str, List[str]]] = [
        ("主题", [topic]),
        ("历史背景", background),
        ("事件经过", process),
        ("历史意义", significance),
    ]
    if figures:
        sections.append(("关键人物", figures))
    if conclusions:
        sections.append(("关键结论", conclusions))
    if raw_details:
        sections.append(("补充细节", raw_details))
    sections.append(
        (
            "依据",
            [
                f"{index + 1}. {card['title']} | {card['type']} | {card['source_file']}"
                + (f" | 第{card['source_page']}页" if card.get("source_page") else "")
                for index, card in enumerate(source_cards[:6])
            ],
        )
    )

    context_lines: List[str] = []
    for title, values in sections:
        cleaned_values = _unique_texts(values, limit=4)
        if not cleaned_values:
            continue
        context_lines.append(f"【{title}】")
        context_lines.extend(_truncate(value, 240) for value in cleaned_values)
        context_lines.append("")

    context_text = "\n".join(line for line in context_lines if line is not None).strip()
    context_blocks = [context_text] if context_text else []
    return {
        "query": query,
        "intent": intent,
        "target": target,
        "structured_items": structured_items,
        "raw_items": raw_items,
        "context_text": context_text,
        "context_blocks": context_blocks,
        "source_cards": source_cards,
        "background": background,
        "process": process,
        "significance": significance,
        "figures": figures,
        "conclusions": conclusions,
        "raw_details": raw_details,
    }
