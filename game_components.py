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
    streak = int(progress.get("streak", 0) or 0)
    items = [
        {"label": "红星积分", "value": progress.get("red_star_points", 0), "desc": "历史判断与关卡推进"},
        {"label": "虚拟粮草", "value": progress.get("grain", 0), "desc": "连续作战补给"},
        {"label": "当前军衔", "value": progress.get("rank_title", "红军新兵"), "desc": "成长等级"},
        {"label": "已获勋章", "value": len(progress.get("medals", [])), "desc": "阶段荣誉"},
        {"label": "红军小队", "value": team.get("team_name", "未加入"), "desc": "协作归属"},
        {
            "label": "连续命中",
            "value": f"{streak} 连胜",
            "desc": "连胜越高，结算越有压迫感",
        },
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
            streak_class=_text("hot" if streak >= 2 else ""),
            streak_text=_text(f"连胜火焰 x{streak}" if streak else "点燃首胜"),
            cards_html=cards_html,
        )
    )


def render_chapter_mission_grid(
    chapters: List[Dict[str, Any]],
    nodes_by_id: Dict[str, Dict[str, Any]],
    current_node_id: str,
    completed_ids: Iterable[str],
) -> None:
    """Render four campaign chapters as the main game mission selector."""
    completed = set(completed_ids or [])
    cards: List[str] = []
    for index, chapter in enumerate(chapters, start=1):
        node_ids = [node_id for node_id in chapter.get("node_ids", []) if node_id in nodes_by_id]
        if not node_ids:
            continue
        completed_count = len([node_id for node_id in node_ids if node_id in completed])
        is_active = current_node_id in node_ids or (not current_node_id and index == 1)
        is_done = bool(node_ids) and completed_count >= len(node_ids)
        class_name = "game-chapter-mission active" if is_active else "game-chapter-mission"
        if is_done:
            class_name += " done"
        node_names = "、".join(nodes_by_id[node_id].get("title", "") for node_id in node_ids[:3])
        if len(node_ids) > 3:
            node_names += "……"
        cards.append(
            render_template(
                "game_chapter_mission_card.html",
                class_name=class_name,
                badge=_text(chapter.get("badge", f"第{index}篇章")),
                title=_text(chapter.get("title", "行动篇章")),
                subtitle=_text(chapter.get("subtitle", "")),
                nodes=_text(node_names),
                progress=_text(f"{completed_count}/{len(node_ids)} 关"),
                reward=_text("篇章勋章 + 纪念卡" if not is_done else "篇章已突破"),
            )
        )
    if cards:
        _render_html(
            render_template_block(
                "game_chapter_mission_grid.html",
                "game_components.css",
                cards_html="".join(cards),
            )
        )


def render_reward_track(progress: Dict[str, Any], *, title: str = "成长奖励") -> None:
    """Render score, grain, medals and unlocked cards as a visible reward track."""
    unlocked_cards = progress.get("unlocked_cards", []) or []
    items = [
        {"label": "红星积分", "value": progress.get("red_star_points", 0), "desc": "进入排行榜"},
        {"label": "虚拟粮草", "value": progress.get("grain", 0), "desc": "连续作战资源"},
        {"label": "军衔", "value": progress.get("rank_title", "红军新兵"), "desc": "成长等级"},
        {"label": "勋章", "value": len(progress.get("medals", [])), "desc": "阶段荣誉"},
        {"label": "纪念卡", "value": len(unlocked_cards), "desc": "节点收藏"},
    ]
    items_html = "".join(
        render_template(
            "game_reward_item.html",
            label=_text(item["label"]),
            value=_text(item["value"]),
            desc=_text(item["desc"]),
        )
        for item in items
    )
    _render_html(
        render_template_block(
            "game_reward_track.html",
            "game_components.css",
            title=_text(title),
            items_html=items_html,
        )
    )


def render_collectible_unlock(card: Dict[str, Any]) -> None:
    """Render the newly unlocked node memory card."""
    if not card:
        return
    _render_html(
        render_template_block(
            "game_collectible_card.html",
            "game_components.css",
            rarity=_text(card.get("rarity", "精良")),
            title=_text(card.get("title", "长征记忆卡")),
            desc=_text(card.get("desc", "完成本关后解锁的长征记忆。")),
        )
    )


def _rarity_class(rarity: str) -> str:
    normalized = str(rarity or "").strip()
    if normalized == "传说":
        return "legend"
    if normalized == "史诗":
        return "epic"
    return "rare"


def render_collectible_wall(cards: Iterable[Dict[str, Any]]) -> None:
    """Render unlocked cards as a collectible wall instead of plain text."""
    card_items = [item for item in cards or [] if isinstance(item, dict)]
    if not card_items:
        return
    cards_html = "".join(
        render_template(
            "game_collectible_wall_card.html",
            class_name=_text(f"game-collectible-wall-card {_rarity_class(item.get('rarity', '精良'))}"),
            rarity=_text(item.get("rarity", "精良")),
            title=_text(item.get("title", "长征纪念卡")),
            desc=_text(item.get("desc", "完成节点后解锁的长征记忆。")),
        )
        for item in card_items
    )
    _render_html(
        render_template_block(
            "game_collectible_wall.html",
            "game_components.css",
            count=_text(len(card_items)),
            cards_html=cards_html,
        )
    )


def render_chapter_prologue(chapter: Dict[str, Any], nodes: List[Dict[str, Any]]) -> None:
    """Render the selected chapter as a game prologue before choosing levels."""
    if not chapter:
        return
    node_names = "、".join(item.get("title", "") for item in nodes[:5] if item.get("title"))
    boss_nodes = [
        item.get("title", "")
        for item in nodes
        if item.get("id", "") in {"xiangjiang_battle", "zunyi_meeting", "sidu_chishui", "luding_bridge", "huining_meeting"}
    ]
    _render_html(
        render_template_block(
            "game_chapter_prologue.html",
            "game_components.css",
            badge=_text(chapter.get("badge", "行动篇章")),
            title=_text(chapter.get("title", "长征主线")),
            subtitle=_text(chapter.get("subtitle", "进入本章行动地图。")),
            nodes=_text(node_names or "沿长征主线推进"),
            boss_hint=_text("攻坚关：" + "、".join(boss_nodes) if boss_nodes else "本章以连续推进和基础判断为主。"),
        )
    )


def render_hint_panel(stage: Dict[str, Any], role: Dict[str, Any]) -> None:
    """Render a concise hint after players spend grain or receive a role clue."""
    material_points = [str(item).strip() for item in stage.get("material_points", []) if str(item).strip()]
    clues = []
    if material_points:
        clues.append(material_points[0])
    if stage.get("recommended_tactic_reason"):
        clues.append(f"本关更适合从“{stage.get('recommended_tactic_title', '行动策略')}”切入：{stage.get('recommended_tactic_reason')}")
    if role.get("special_hint"):
        clues.append(role.get("special_hint"))
    body = " ".join(clues[:3]) or "先找出题干中的地点、时间和行动目的，再判断哪一项最符合长征主线。"
    _render_html(
        render_template_block(
            "game_hint_panel.html",
            "game_components.css",
            role=_text(role.get("name", "侦察兵")),
            title=_text("本关线索已解锁"),
            body=_text(body),
        )
    )


def render_quest_board(progress: Dict[str, Any], chapters: List[Dict[str, Any]]) -> None:
    """Render short-term goals so players know what to chase next."""
    completed_nodes = progress.get("completed_nodes", []) or []
    unlocked_cards = progress.get("unlocked_cards", []) or []
    streak = int(progress.get("streak", 0) or 0)
    chapter_total = len(chapters) or 4
    completed_chapters = len(progress.get("completed_chapters", []) or [])
    quests = [
        {
            "label": "主线推进",
            "title": "完成 3 个节点",
            "progress": f"{min(len(completed_nodes), 3)}/3",
            "desc": "达成后可形成第一段连续征程印象。",
        },
        {
            "label": "连胜挑战",
            "title": "达成 2 连胜",
            "progress": f"{min(streak, 2)}/2",
            "desc": "连续判断正确会点亮连胜火焰。",
        },
        {
            "label": "收藏目标",
            "title": "解锁 3 张纪念卡",
            "progress": f"{min(len(unlocked_cards), 3)}/3",
            "desc": "每张卡对应一个长征节点记忆。",
        },
        {
            "label": "篇章突破",
            "title": "突破全部行动篇章",
            "progress": f"{min(completed_chapters, chapter_total)}/{chapter_total}",
            "desc": "完成后获得长征全线贯通荣誉。",
        },
    ]
    items_html = "".join(
        render_template(
            "game_quest_item.html",
            label=_text(item["label"]),
            title=_text(item["title"]),
            progress=_text(item["progress"]),
            desc=_text(item["desc"]),
        )
        for item in quests
    )
    _render_html(
        render_template_block(
            "game_quest_board.html",
            "game_components.css",
            items_html=items_html,
        )
    )


def render_option_cards(stage: Dict[str, Any]) -> None:
    """Render answer options as visual action cards before the native radio control."""
    options = [str(item).strip() for item in stage.get("options", []) if str(item).strip()]
    if not options:
        return
    cards = []
    for index, option in enumerate(options, start=1):
        letter = chr(64 + index) if 1 <= index <= 26 else str(index)
        clean_option = option
        if len(clean_option) > 2 and clean_option[0].upper() == letter and clean_option[1] in [".", "、", "．"]:
            clean_option = clean_option[2:].strip()
        cards.append(
            render_template(
                "game_option_card.html",
                letter=_text(letter),
                text=_text(clean_option),
            )
        )
    _render_html(
        render_template_block(
            "game_option_grid.html",
            "game_components.css",
            cards_html="".join(cards),
        )
    )


def render_combo_banner(progress: Dict[str, Any]) -> None:
    """Render a compact combo banner when the player is on a streak."""
    streak = int(progress.get("streak", 0) or 0)
    if streak < 2:
        return
    _render_html(
        render_template_block(
            "game_combo_banner.html",
            "game_components.css",
            streak=_text(streak),
            title=_text("连续命中，战意升温"),
            desc=_text("继续保持判断准确度，后续结算会更有成就感。"),
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
    stage_rating = max(0, min(3, int(last_result.get("stage_rating", 0) or 0)))
    star_text = "★" * stage_rating + "☆" * (3 - stage_rating)
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
            "label": "本关星级",
            "value": star_text,
            "desc": "完成 / 正确 / 策略契合",
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
