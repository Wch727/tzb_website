"""Homepage exhibition components backed by external HTML templates."""

from __future__ import annotations

import base64
import html
import mimetypes
from pathlib import Path
from typing import Any, Dict, Iterable, List

import streamlit as st

from media import resolve_image
from template_renderer import render_template, render_template_block
from utils import BASE_DIR


def _asset_to_data_uri(path_like: str) -> str:
    """Convert a repository asset to a browser-safe data URI."""
    if not path_like:
        return ""
    candidate = Path(path_like)
    if not candidate.is_absolute():
        candidate = BASE_DIR / path_like
    if not candidate.exists():
        return ""
    mime, _ = mimetypes.guess_type(str(candidate))
    if candidate.suffix.lower() == ".svg":
        mime = "image/svg+xml"
    encoded = base64.b64encode(candidate.read_bytes()).decode("ascii")
    return f"data:{mime or 'application/octet-stream'};base64,{encoded}"


def _image_uri(item: Dict[str, Any], fallback: str = "assets/images/route_placeholder.svg") -> str:
    """Resolve an item image into a data URI or remote URL."""
    resolved = resolve_image(item)
    if resolved.get("mode") == "remote":
        return str(resolved.get("path", ""))
    path = str(resolved.get("path", ""))
    return _asset_to_data_uri(path) or _asset_to_data_uri(fallback)


def _text(value: Any) -> str:
    return html.escape(str(value or "").strip())


def _paragraph_html(text: str, limit: int = 4) -> str:
    parts = [part.strip() for part in str(text or "").splitlines() if part.strip()]
    if not parts:
        return ""
    return "".join(render_template("home_paragraph.html", text=_text(part)) for part in parts[:limit])


def render_home_hero(
    *,
    title: str,
    subtitle: str,
    hero_item: Dict[str, Any],
    badges: Iterable[str],
    chapters: List[Dict[str, Any]],
    panel_title: str,
    panel_text: str,
) -> None:
    """Render the first-screen museum-style homepage hero."""
    badges_html = "".join(render_template("home_badge.html", label=_text(item)) for item in badges)
    chapter_cards_html = "".join(
        render_template(
            "home_chapter_card.html",
            label=_text(chapter.get("badge", "篇章")),
            title=_text(chapter.get("title", "")),
            desc=_text(chapter.get("subtitle", ""))[:56],
        )
        for chapter in chapters[:4]
    )
    st.html(
        render_template_block(
            "home_hero.html",
            "home_exhibit.css",
            kicker="长征主题云端展馆",
            title=_text(title),
            subtitle=_text(subtitle),
            hero_image_uri=_image_uri(hero_item),
            badges_html=badges_html,
            panel_label="主展导览",
            panel_title=_text(panel_title),
            panel_text=_text(panel_text),
            chapter_cards_html=chapter_cards_html,
        )
    )


def render_home_section(title: str, subtitle: str, kicker: str = "展览单元") -> None:
    """Render a homepage section heading."""
    st.html(
        render_template(
            "home_section.html",
            kicker=_text(kicker),
            title=_text(title),
            subtitle=_text(subtitle),
        )
    )


def render_home_stats(items: Iterable[Dict[str, Any]]) -> None:
    """Render stats in a museum-style strip."""
    stats_html = "".join(
        render_template("home_stat_item.html", label=_text(item.get("label", "")), value=_text(item.get("value", "")))
        for item in items
    )
    st.html(render_template("home_stat_strip.html", stats_html=stats_html))


def node_card_html(node: Dict[str, Any], label: str = "重点展项") -> str:
    """Return external-template HTML for a node card."""
    meta = " · ".join(part for part in [str(node.get("date", "")), str(node.get("place", ""))] if part)
    return render_template(
        "home_node_card.html",
        image_uri=_image_uri(node),
        label=_text(label),
        title=_text(node.get("title", "")),
        meta=_text(meta),
        summary=_text(node.get("summary", "")),
    )


def topic_card_html(title: str, desc: str, label: str = "专题") -> str:
    """Return external-template HTML for a text topic card."""
    return render_template(
        "home_topic_card.html",
        label=_text(label),
        title=_text(title),
        desc=_text(desc),
    )


def render_story_panel(story: Dict[str, Any], fallback_script: str = "") -> None:
    """Render a story narration panel."""
    script = story.get("script", "") or fallback_script
    st.html(
        render_template(
            "home_story_panel.html",
            label="讲解服务",
            title=_text(story.get("title", "长征故事")),
            subtitle=_text(story.get("subtitle", "沿着长征主线继续进入这一段历史叙事。")),
            script_html=_paragraph_html(script, limit=5),
        )
    )


def route_card_html(route_text: str, label: str) -> str:
    """Return external-template HTML for a route recommendation card."""
    title = label
    body = str(route_text or "").strip()
    if "：" in body:
        title, body = body.split("：", 1)
    elif ":" in body:
        title, body = body.split(":", 1)
    nodes = [part.strip() for part in body.split("→") if part.strip()]
    nodes_html = "".join(render_template("home_route_node.html", title=_text(node)) for node in nodes[:5])
    return render_template(
        "home_route_card.html",
        label=_text(label),
        title=_text(title),
        body=_text(body),
        nodes_html=nodes_html,
    )
