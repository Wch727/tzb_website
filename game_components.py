"""Game-specific visual components for the closed-book challenge page."""

from __future__ import annotations

import html
from typing import Any, Dict, Iterable, List

import streamlit as st

from template_renderer import render_template, render_template_block


def _text(value: Any) -> str:
    """Escape text before injecting it into local HTML templates."""
    return html.escape(str(value or "").strip())


def _short(value: Any, limit: int = 96) -> str:
    text = str(value or "").strip()
    return text if len(text) <= limit else f"{text[:limit]}..."


def _render_html(markup: str) -> None:
    """Render project-owned HTML templates in Streamlit."""
    st.markdown(markup, unsafe_allow_html=True)


def render_campaign_map(nodes: List[Dict[str, Any]], current_index: int, completed_ids: Iterable[str]) -> None:
    """Render a horizontal level map so the route feels like selectable game stages."""
    completed = set(completed_ids or [])
    cards: List[str] = []
    for index, node in enumerate(nodes):
        node_id = node.get("id", "")
        if index == current_index:
            class_name = "game-map-node current"
            state_label = "当前关"
        elif node_id in completed or index < current_index:
            class_name = "game-map-node done"
            state_label = "已突破"
        else:
            class_name = "game-map-node locked"
            state_label = "待解锁"
        cards.append(
            render_template(
                "game_map_node.html",
                class_name=class_name,
                index=f"{index + 1:02d}",
                title=_text(node.get("title", "长征关卡")),
                place=_text(node.get("place", "")),
                state_label=_text(state_label),
            )
        )
    if cards:
        _render_html(
            render_template_block(
                "game_campaign_map.html",
                "game_components.css",
                nodes_html="".join(cards),
            )
        )


def render_command_center(stage: Dict[str, Any], node: Dict[str, Any], story_state: Dict[str, Any], team: Dict[str, Any]) -> None:
    """Render the current stage as a game mission command center."""
    difficulty = "★" * int(stage.get("difficulty_stars", 3) or 3)
    team_name = team.get("team_name") or "单人挑战"
    subtitle = (
        f"第 {stage.get('current_step', 1)} / {stage.get('total_steps', 1)} 关 · "
        f"{story_state.get('role_name', '侦察兵')} · {stage.get('question_type', '情境选择题')}"
    )
    _render_html(
        render_template_block(
            "game_command_center.html",
            "game_components.css",
            badge=_text(stage.get("stage_badge", "主线推进关")),
            title=_text(node.get("title", "当前关卡")),
            subtitle=_text(subtitle),
            campaign_title=_text(stage.get("campaign_title", story_state.get("activity_name", "长征主线闯关"))),
            place=_text(node.get("place", "长征沿线")),
            date=_text(node.get("date", "")),
            difficulty=_text(difficulty),
            team_name=_text(team_name),
            prologue=_text(stage.get("prologue", stage.get("mission_prompt", ""))),
            risk_hint=_text(stage.get("risk_hint", "看清节点处境，再作出判断。")),
            reward_hint=_text(stage.get("reward_hint", "答对即可推进主线，并获得积分与粮草。")),
        )
    )


def render_game_hud(progress: Dict[str, Any], team: Dict[str, Any], story_state: Dict[str, Any]) -> None:
    """Render a compact visual HUD instead of plain metric blocks."""
    items = [
        {"label": "红星积分", "value": progress.get("red_star_points", 0), "desc": "历史判断与关卡推进"},
        {"label": "虚拟粮草", "value": progress.get("grain", 0), "desc": "连续作战补给"},
        {"label": "当前军衔", "value": progress.get("rank_title", "红军新兵"), "desc": "成长等级"},
        {"label": "已获勋章", "value": len(progress.get("medals", [])), "desc": "阶段荣誉"},
        {"label": "红军小队", "value": team.get("team_name", "未加入"), "desc": "协作归属"},
        {"label": "连续命中", "value": progress.get("streak", 0), "desc": "当前连胜"},
    ]
    cards_html = "".join(
        render_template(
            "game_hud_card.html",
            label=_text(item["label"]),
            value=_text(item["value"]),
            desc=_text(item["desc"]),
        )
        for item in items
    )
    _render_html(
        render_template_block(
            "game_hud.html",
            "game_components.css",
            activity_name=_text(story_state.get("activity_name", "长征主线闯关")),
            cards_html=cards_html,
        )
    )


def render_tactic_preview(options: List[Dict[str, Any]], selected_id: str) -> None:
    """Render tactic cards for the selected role."""
    if not options:
        return
    cards: List[str] = []
    for index, item in enumerate(options, start=1):
        class_name = "game-tactic-card selected" if item.get("id") == selected_id else "game-tactic-card"
        cards.append(
            render_template(
                "game_tactic_card.html",
                class_name=class_name,
                index=f"{index:02d}",
                title=_text(item.get("title", "行动策略")),
                desc=_text(_short(item.get("desc", ""), 108)),
            )
        )
    _render_html(
        render_template_block(
            "game_tactic_grid.html",
            "game_components.css",
            cards_html="".join(cards),
        )
    )


def render_answer_arena(stage: Dict[str, Any], node: Dict[str, Any]) -> None:
    """Render the question prompt in a mission arena shell."""
    _render_html(
        render_template_block(
            "game_answer_arena.html",
            "game_components.css",
            question_type=_text(stage.get("question_type", "情境选择题")),
            node_title=_text(node.get("title", "当前关卡")),
            question=_text(stage.get("question", "暂无题目。")),
            material_title=_text(stage.get("material_title", "本关材料")),
            material_hint=_text(stage.get("mission_prompt", "请结合关卡情境作出判断。")),
        )
    )
