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
    material_points = [
        str(item).strip()
        for item in stage.get("material_points", [])
        if str(item).strip()
    ]
    material_points_html = "".join(
        f"<li>{_text(item)}</li>"
        for item in material_points[:4]
    )
    _render_html(
        render_template_block(
            "game_answer_arena.html",
            "game_components.css",
            question_type=_text(stage.get("question_type", "情境选择题")),
            node_title=_text(node.get("title", "当前关卡")),
            question=_text(stage.get("question", "暂无题目。")),
            material_title=_text(stage.get("material_title", "本关材料")),
            material_hint=_text(stage.get("mission_prompt", "请结合关卡情境作出判断。")),
            material_points_html=material_points_html,
        )
    )


def render_result_banner(last_result: Dict[str, Any], team: Dict[str, Any]) -> None:
    """Render the post-answer result as a game settlement card."""
    detail = last_result.get("answer_detail", {}) or {}
    answered_node = last_result.get("answered_node", {}) or {}
    next_node = last_result.get("next_node", {}) or {}
    reward_delta = last_result.get("reward_delta", {}) or {}
    correct = bool(last_result.get("correct"))
    class_name = "game-result-banner victory" if correct else "game-result-banner review"
    stats = [
        {
            "label": "完成节点",
            "value": answered_node.get("title", "上一关"),
            "desc": answered_node.get("route_stage", "长征主线"),
        },
        {
            "label": "正确答案",
            "value": detail.get("expected_answer", "待复盘"),
            "desc": "提交后解锁标准解析",
        },
        {
            "label": "奖励变化",
            "value": f"{int(reward_delta.get('score_delta', 0)):+d} 星 / {int(reward_delta.get('grain_delta', 0)):+d} 粮",
            "desc": "红星积分与虚拟粮草",
        },
        {
            "label": "下一站",
            "value": next_node.get("title", "完成结算"),
            "desc": next_node.get("place", "继续沿主线推进"),
        },
    ]
    stats_html = "".join(
        render_template(
            "game_result_stat.html",
            label=_text(item["label"]),
            value=_text(item["value"]),
            desc=_text(item["desc"]),
        )
        for item in stats
    )
    role_feedback = last_result.get("role_feedback") or (
        f"本次战绩已计入{team.get('team_name', '当前挑战')}。" if team else "本关记录已写入个人闯关进度。"
    )
    _render_html(
        render_template_block(
            "game_result_banner.html",
            "game_components.css",
            class_name=class_name,
            kicker="突破成功" if correct else "进入复盘",
            title=_text(last_result.get("feedback", "本关作答已完成")),
            feedback=_text(last_result.get("battle_outcome", "作答结果已经记录。")),
            stats_html=stats_html,
            role_label=_text("角色反馈"),
            role_feedback=_text(role_feedback),
        )
    )


def render_debrief_panel(*, label: str, title: str, body: str) -> None:
    """Render a single debrief paragraph with game styling."""
    _render_html(
        render_template_block(
            "game_debrief_panel.html",
            "game_components.css",
            label=_text(label),
            title=_text(title),
            body=_text(body),
        )
    )


def render_report_cards(items: Iterable[str], label_prefix: str = "记录") -> None:
    """Render after-action report bullets as cards."""
    cards = []
    for index, item in enumerate(items or [], start=1):
        text = str(item or "").strip()
        if not text:
            continue
        cards.append(
            render_template(
                "game_report_card.html",
                label=_text(f"{label_prefix} {index:02d}"),
                text=_text(text),
            )
        )
    if cards:
        _render_html(
            render_template_block(
                "game_report_grid.html",
                "game_components.css",
                cards_html="".join(cards),
            )
        )
