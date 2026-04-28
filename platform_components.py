"""Reusable visual components for activity, ranking, admin, and game pages."""

from __future__ import annotations

import html
from typing import Any, Dict, Iterable, List

import streamlit as st

from template_renderer import render_template, render_template_block


def _text(value: Any) -> str:
    return html.escape(str(value or "").strip())


def _tags_html(tags: Iterable[str]) -> str:
    return "".join(render_template("platform_tag.html", label=_text(tag)) for tag in tags if str(tag).strip())


def _stats_html(stats: Iterable[Dict[str, Any]]) -> str:
    return "".join(
        render_template(
            "platform_stat.html",
            label=_text(item.get("label", "")),
            value=_text(item.get("value", "")),
        )
        for item in stats
    )


def render_platform_showcase(
    *,
    title: str,
    subtitle: str,
    kicker: str,
    tags: Iterable[str],
    panel_title: str,
    panel_text: str,
    stats: Iterable[Dict[str, Any]],
    variant: str = "crimson",
) -> None:
    """Render a high-impact page showcase with external HTML/CSS."""
    allowed_variants = {"crimson", "activity", "scoreboard", "admin", "screen"}
    variant_class = f"platform-{variant}" if variant in allowed_variants else "platform-crimson"
    st.html(
        render_template_block(
            "platform_showcase.html",
            "platform_components.css",
            variant_class=variant_class,
            kicker=_text(kicker),
            title=_text(title),
            subtitle=_text(subtitle),
            tags_html=_tags_html(tags),
            panel_title=_text(panel_title),
            panel_text=_text(panel_text),
            stats_html=_stats_html(stats),
        )
    )


def activity_card_html(activity: Dict[str, Any], active: bool = False) -> str:
    """Return an activity card."""
    return render_template(
        "platform_activity_card.html",
        class_name="platform-activity-card active" if active else "platform-activity-card",
        mode=_text(activity.get("mode", "活动")),
        name=_text(activity.get("name", "未命名活动")),
        description=_text(activity.get("description", "")),
        time_range=_text(activity.get("time_range", "长期开放")),
        team_mode="小队协作" if activity.get("support_team_mode", True) else "个人参与",
        pk_mode="支部对抗" if activity.get("support_branch_pk", True) else "非对抗模式",
    )


def render_qr_panel(*, label: str, title: str, desc: str, link: str) -> None:
    """Render a QR/link explanation panel."""
    st.html(
        render_template(
            "platform_qr_panel.html",
            label=_text(label),
            title=_text(title),
            desc=_text(desc),
            link=_text(link),
        )
    )


def rank_podium_html(rows: List[Dict[str, Any]], score_key: str = "score") -> str:
    """Return a top-three podium block."""
    cards = []
    for index, row in enumerate(rows[:3], start=1):
        name = row.get("user_name") or row.get("team_name") or row.get("branch_name") or row.get("unit_name") or "学习者"
        score = row.get(score_key, row.get("total_score", row.get("score", 0)))
        desc = (
            f"{row.get('unit_name', row.get('branch_name', ''))} "
            f"{row.get('rank_title', '')} "
            f"作答 {row.get('answered_count', row.get('member_count', 0))} 次"
        ).strip()
        cards.append(
            render_template(
                "platform_rank_card.html",
                rank=str(index),
                name=_text(name),
                score=_text(score),
                desc=_text(desc),
            )
        )
    return render_template("platform_rank_podium.html", cards_html="".join(cards)) if cards else ""


def level_card_html(node: Dict[str, Any], index: int, selected: bool = False) -> str:
    """Return a game level selection card."""
    meta = " · ".join(part for part in [node.get("date", ""), node.get("place", "")] if part)
    return render_template(
        "platform_level_card.html",
        class_name="platform-level-card active" if selected else "platform-level-card",
        index=f"{index:02d}",
        title=_text(node.get("title", "长征关卡")),
        summary=_text(node.get("summary", "")),
        meta=_text(meta),
    )


def render_admin_banner(title: str, subtitle: str, cards: Iterable[Dict[str, Any]]) -> None:
    """Render admin console banner."""
    card_html = "".join(
        render_template(
            "platform_admin_card.html",
            label=_text(item.get("label", "")),
            value=_text(item.get("value", "")),
            desc=_text(item.get("desc", "")),
        )
        for item in cards
    )
    st.html(
        render_template_block(
            "platform_admin_banner.html",
            "platform_components.css",
            kicker="内容运营中枢",
            title=_text(title),
            subtitle=_text(subtitle),
            cards_html=card_html,
        )
    )
