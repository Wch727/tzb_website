"""剧情答题页。"""

from __future__ import annotations

import streamlit as st

from certificate import generate_certificate_svg
from dashboard_data import record_answer_event, record_participation_event, record_share_event
from knowledge_cards import build_related_knowledge_bundle
from leaderboard import build_user_share_text, record_leaderboard_entry
from media import render_audio_player, render_node_image, render_svg_artwork
from quiz_engine import create_story_state, get_stage_package, submit_stage_answer
from streamlit_ui import (
    render_boss_stage_intro,
    render_detail_panels,
    render_formal_script,
    render_game_status_board,
    render_hero,
    render_section,
    render_top_nav,
    setup_page,
)
from team_manager import build_team_member_summary, build_team_share_text, get_team, record_team_progress


def _current_team() -> dict:
    """获取当前 session 绑定的小队。"""
    team_id = st.session_state.get("current_team_id", "")
    if not team_id:
        return {}
    team = get_team(team_id)
    if team:
        st.session_state["current_team_name"] = team.get("team_name", "")
        st.session_state["current_branch_name"] = team.get("branch_name", "")
    return team


def _ensure_story_state() -> dict:
    """确保剧情状态存在。"""
    story_state = st.session_state.get("story_state", {})
    if story_state:
        return story_state
    role_id = st.session_state.get("selected_role_id", "scout")
    activity_id = st.session_state.get("current_activity_id", "knowledge-contest")
    story_state = create_story_state(role_id=role_id, activity_id=activity_id)
    st.session_state["story_state"] = story_state
    team = _current_team()
    enter_key = f"dashboard_participation::{story_state.get('activity_id', 'global')}::{st.session_state.get('user_name', '红色学习者')}"
    if not st.session_state.get(enter_key):
        record_participation_event(
            user_name=st.session_state.get("user_name", "红色学习者"),
            unit_name=st.session_state.get("unit_name", "体验组"),
            role_name=story_state.get("role_name", "侦察兵"),
            activity_id=story_state.get("activity_id", "global"),
            activity_name=story_state.get("activity_name", "长征主线闯关"),
            team_id=team.get("team_id", ""),
            team_name=team.get("team_name", ""),
            branch_name=team.get("branch_name", ""),
        )
        st.session_state[enter_key] = True
    return story_state


setup_page("剧情答题", icon="🎮")
render_top_nav("剧情答题")
render_hero(
    title="剧情答题",
    subtitle="围绕长征时间线逐关推进。每一关都包含历史导入、角色任务、多媒体题型、答案反馈、历史小课堂和成长激励，同时支持将个人贡献同步到红军小队与支部对抗榜单。",
    badges=["主线关卡", "多媒体题型", "红军小队", "支部对抗"],
)

if not st.session_state.get("selected_role_id"):
    st.warning("请先完成角色选择，再进入剧情答题。")
    st.page_link("pages/2_角色选择.py", label="前往角色选择", width="stretch")
    st.stop()

story_state = _ensure_story_state()
team = _current_team()

if story_state.get("finished"):
    progress = story_state.get("progress", {})
    svg = generate_certificate_svg(
        user_name=st.session_state.get("user_name", "红色学习者"),
        unit_name=st.session_state.get("unit_name", "体验组"),
        activity_name=story_state.get("activity_name", "长征主线闯关"),
        rank_title=progress.get("rank_title", "红军新兵"),
        score=int(progress.get("red_star_points", 0)),
        medals=progress.get("medals", []),
    )
    st.session_state["story_state"]["progress"]["last_certificate_svg"] = svg

    render_section("结算页", "展示总积分、军衔、勋章、错题复盘、电子证书以及本次对小队/支部的贡献。")
    st.caption(
        f"参与身份：{st.session_state.get('user_name', '红色学习者')} | "
        f"{st.session_state.get('unit_name', '体验组')} | {story_state.get('role_name', '侦察兵')}"
    )
    render_game_status_board(
        [
            {
                "kicker": "成长状态",
                "symbol": "★",
                "value": progress.get("red_star_points", 0),
                "label": "红星积分",
                "note": "记录你在长征闯关中的历史判断与推进表现。",
            },
            {
                "kicker": "补给状态",
                "symbol": "粮",
                "value": progress.get("grain", 0),
                "label": "虚拟粮草",
                "note": "用于表现连续作战中的补给与行动稳定度。",
            },
            {
                "kicker": "身份状态",
                "symbol": "军",
                "value": progress.get("rank_title", "红军新兵"),
                "label": "当前军衔",
                "note": "随积分提升而晋升，体现你的主线成长轨迹。",
            },
            {
                "kicker": "荣誉状态",
                "symbol": "章",
                "value": len(progress.get("medals", [])),
                "label": "已获勋章",
                "note": "记录你在主线关卡、篇章推进与战术判断中的成就。",
            },
        ]
    )

    if team:
        team_box, member_box = st.columns([1, 1.05])
        with team_box:
            st.markdown("### 小队协作结果")
            st.write(
                f"当前小队：**{team.get('team_name', '')}** | "
                f"{team.get('branch_name', '')} | 总分 {team.get('total_score', 0)}"
            )
            st.write(
                f"累计作答 {team.get('answered_count', 0)} 次，"
                f"正确 {team.get('correct_count', 0)} 次，粮草 {team.get('total_grain', 0)}。"
            )
        with member_box:
            st.markdown("### 个人在小队中的贡献")
            member_rows = build_team_member_summary(team.get("team_id", ""))
            current_user = st.session_state.get("user_name", "红色学习者")
            current_member = next((item for item in member_rows if item.get("user_name") == current_user), {})
            if current_member:
                st.write(
                    f"你的累计贡献分：{current_member.get('contribution_score', 0)}，"
                    f"粮草：{current_member.get('contribution_grain', 0)}，"
                    f"作答：{current_member.get('answered_count', 0)} 次。"
                )

    if progress.get("medals"):
        st.markdown("### 已获得勋章")
        st.write("、".join(progress.get("medals", [])))
    if progress.get("wrong_book"):
        st.markdown("### 错题复盘")
        for item in progress.get("wrong_book", []):
            with st.expander(item.get("title", "错题"), expanded=False):
                st.write(f"题目：{item.get('question', '')}")
                st.write(f"你的答案：{item.get('selected_answer', '')}")
                st.write(f"正确答案：{item.get('expected_answer', '')}")
                st.write(f"解析：{item.get('explanation', '')}")

    record_key = f"leaderboard_recorded::{story_state.get('activity_id', 'global')}"
    if not st.session_state.get(record_key):
        record_leaderboard_entry(
            {
                "user_name": st.session_state.get("user_name", "红色学习者"),
                "unit_name": st.session_state.get("unit_name", "体验组"),
                "role_name": story_state.get("role_name", "侦察兵"),
                "activity_id": story_state.get("activity_id", "global"),
                "activity_name": story_state.get("activity_name", "长征主线闯关"),
                "team_id": team.get("team_id", ""),
                "team_name": team.get("team_name", ""),
                "branch_name": team.get("branch_name", st.session_state.get("unit_name", "体验组")),
                "score": progress.get("red_star_points", 0),
                "grain": progress.get("grain", 0),
                "rank_title": progress.get("rank_title", "红军新兵"),
                "medals": progress.get("medals", []),
                "completed_nodes": len(progress.get("completed_nodes", [])),
                "answered_count": progress.get("answered_count", 0),
            }
        )
        st.session_state[record_key] = True

    st.markdown("### 电子证书")
    render_svg_artwork(svg, "电子结业证书")
    st.download_button(
        "下载电子证书（SVG）",
        data=svg.encode("utf-8"),
        file_name="long_march_certificate.svg",
        mime="image/svg+xml",
        width="stretch",
    )

    personal_share = build_user_share_text(
        st.session_state.get("user_name", "红色学习者"),
        story_state.get("activity_id", "global"),
    )
    team_share = build_team_share_text(team.get("team_id", ""), st.session_state.get("user_name", ""))
    share_left, share_right = st.columns(2)
    with share_left:
        st.text_area("个人战绩分享文案", value=personal_share, height=130)
        if st.button("广播个人战绩", width="stretch", disabled=not personal_share):
            record_share_event(
                user_name=st.session_state.get("user_name", "红色学习者"),
                unit_name=st.session_state.get("unit_name", "体验组"),
                activity_id=story_state.get("activity_id", "global"),
                activity_name=story_state.get("activity_name", "长征主线闯关"),
                share_text=personal_share,
                team_id=team.get("team_id", ""),
                team_name=team.get("team_name", ""),
                branch_name=team.get("branch_name", st.session_state.get("unit_name", "体验组")),
            )
            st.success("个人战绩已写入实时播报流。")
    with share_right:
        st.text_area("小队战绩分享文案", value=team_share, height=130)
        if st.button("广播小队战绩", width="stretch", disabled=not team_share):
            record_share_event(
                user_name=st.session_state.get("user_name", "红色学习者"),
                unit_name=st.session_state.get("unit_name", "体验组"),
                activity_id=story_state.get("activity_id", "global"),
                activity_name=story_state.get("activity_name", "长征主线闯关"),
                share_text=team_share,
                team_id=team.get("team_id", ""),
                team_name=team.get("team_name", ""),
                branch_name=team.get("branch_name", st.session_state.get("unit_name", "体验组")),
            )
            st.success("小队战绩已写入实时播报流。")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("查看排行榜", width="stretch"):
            st.switch_page("pages/7_排行榜.py")
    with col2:
        if st.button("前往活动中心", width="stretch"):
            st.switch_page("pages/6_活动中心.py")
    with col3:
        if st.button("重新开始活动", width="stretch"):
            st.session_state.pop(record_key, None)
            st.session_state.pop("story_last_result", None)
            st.session_state["story_state"] = create_story_state(
                role_id=st.session_state.get("selected_role_id", "scout"),
                activity_id=st.session_state.get("current_activity_id", "knowledge-contest"),
            )
            st.rerun()
    st.stop()

stage = get_stage_package(story_state)
node = stage.get("node", {})
progress = stage.get("progress", {})
knowledge_bundle = build_related_knowledge_bundle(node)

render_section(
    "当前关卡",
    f"第 {stage.get('current_step', 1)} / {stage.get('total_steps', 1)} 关 | "
    f"{story_state.get('activity_name', '长征主线闯关')} | {story_state.get('role_name', '侦察兵')} | "
    f"{st.session_state.get('unit_name', '体验组')}",
)
render_detail_panels(
    [
        {
            "title": "所属篇章",
            "desc": stage.get("campaign_title", "长征主线"),
        },
        {
            "title": "关卡定位",
            "desc": stage.get("stage_badge", "主线推进关"),
        },
        {
            "title": "难度等级",
            "desc": f"{'★' * int(stage.get('difficulty_stars', 3))} {stage.get('difficulty_label', '主线学习关')}",
        },
        {
            "title": "推进提醒",
            "desc": stage.get("next_hint", "完成本关后继续沿主线推进。"),
        },
    ]
)
if stage.get("boss_stage"):
    render_boss_stage_intro(stage.get("boss_stage", {}))

render_game_status_board(
    [
        {
            "kicker": "作战积分",
            "symbol": "★",
            "value": progress.get("red_star_points", 0),
            "label": "红星积分",
            "note": "每完成一关都会累积，用于衡量你在主线中的综合表现。",
        },
        {
            "kicker": "战地补给",
            "symbol": "粮",
            "value": progress.get("grain", 0),
            "label": "虚拟粮草",
            "note": "连续推进、正确判断和战术加成都会影响当前补给值。",
        },
        {
            "kicker": "身份军衔",
            "symbol": "军",
            "value": progress.get("rank_title", "红军新兵"),
            "label": "当前军衔",
            "note": "军衔会随着积分提升而变化，体现你在征程中的成长。",
        },
        {
            "kicker": "荣誉记录",
            "symbol": "章",
            "value": len(progress.get("medals", [])),
            "label": "已获勋章",
            "note": "勋章来自主线推进、篇章突破、连胜与战术判断等关键表现。",
        },
        {
            "kicker": "协作单位",
            "symbol": "队",
            "value": team.get("team_name", "未加入"),
            "label": "红军小队",
            "note": "当前作答会同步计入小队贡献榜，用于活动协作与支部对抗。",
        },
        {
            "kicker": "组织归属",
            "symbol": "旗",
            "value": team.get("branch_name", st.session_state.get("unit_name", "体验组")),
            "label": "支部归属",
            "note": "当前单位会参与活动排行、支部对抗与数据大屏展示。",
        },
        {
            "kicker": "作战节奏",
            "symbol": "连",
            "value": progress.get("streak", 0),
            "label": "连续作战",
            "note": "答题连续命中越多，越能体现主线推进中的稳定判断。",
        },
        {
            "kicker": "个人纪录",
            "symbol": "冠",
            "value": progress.get("best_streak", 0),
            "label": "最佳连胜",
            "note": "记录你迄今为止保持的最高连续命中成绩。",
        },
    ]
)

top_left, top_right = st.columns([1.05, 1.35])
with top_left:
    render_node_image(node, caption=node.get("place", ""))
    if stage.get("question_type") == "地图纠错":
        render_node_image(
            {"title": "长征路线图", "image": "assets/images/changzheng_route_map.jpg", "place": "长征路线总览"},
            caption="地图纠错题辅助路线图",
        )
    if stage.get("question_type") == "听音辨曲" and stage.get("audio_text"):
        render_audio_player(
            text=stage.get("audio_text", ""),
            cache_key=f"quiz-audio-{node.get('id', '')}",
            button_label="播放音频线索",
        )
    st.caption(f"时间：{node.get('date', '未标注')}")
    st.caption(f"地点：{node.get('place', '未标注')}")

with top_right:
    st.markdown(f"## {node.get('title', '')}")
    if stage.get("prologue"):
        st.markdown(f"**过场导语：** {stage.get('prologue', '')}")
    st.markdown(f"**题型：** {stage.get('question_type', '情境选择题')}")
    st.markdown(f"**角色任务提示：** {stage.get('role_brief', '')}")
    if stage.get("opening_brief"):
        st.info(stage.get("opening_brief", ""))
    if stage.get("mission_prompt"):
        st.info(stage.get("mission_prompt", ""))
    role_task = stage.get("role_task", {}) or {}
    if role_task:
        st.markdown("### 本关角色任务卡")
        st.write(role_task.get("mission_brief", ""))
        for item in role_task.get("checklist", []):
            st.markdown(f"- {item}")
        if role_task.get("reward_hint"):
            st.caption(f"奖励提示：{role_task.get('reward_hint', '')}")
    st.markdown("### 本关故事导入")
    st.write(stage.get("story_opening", "") or node.get("summary", ""))
    if team:
        st.markdown("### 小队协作状态")
        st.write(
            f"你当前正在为 **{team.get('team_name', '')}** 作战，"
            f"小队总分 {team.get('total_score', 0)}，"
            f"队员 {len(team.get('members', []))} 人。"
        )

render_section("关前故事", "先进入当时的行军情境，再完成本关判断。每一道题都要放回长征主线中去理解。")
render_formal_script(
    stage.get("story_script", ""),
    title=f"{node.get('title', '长征节点')} · 关前故事",
    label="关前讲述",
    meta=[
        stage.get("campaign_title", "长征主线"),
        stage.get("stage_badge", "主线推进关"),
        stage.get("question_type", "情境选择题"),
    ],
)
if stage.get("story_panels"):
    render_detail_panels(stage.get("story_panels", []))

render_section("作战简报", "每一关都不仅是答题，还包含任务目标、风险提示和奖励预告。")
render_detail_panels(
    [
        {
            "title": "本关目标",
            "desc": "；".join(stage.get("mission_goals", [])[:2]) or "先看背景，再判断行动与历史意义。",
        },
        {
            "title": "风险提示",
            "desc": stage.get("risk_hint", "如果忽略节点背景，很容易把历史判断停留在表层。"),
        },
        {
            "title": "奖励预告",
            "desc": stage.get("reward_hint", "答对即可获得积分与粮草；策略契合还能获得额外奖励。"),
        },
    ]
)

if stage.get("squad_orders"):
    st.markdown("### 小队命令")
    for idx, item in enumerate(stage.get("squad_orders", []), start=1):
        st.markdown(f"- **命令 {idx}**：{item}")

st.markdown("### 战地日志")
for idx, log_line in enumerate(stage.get("battle_log", [])[:3], start=1):
    st.markdown(f"- **记录 {idx}**：{log_line}")

render_section("本关行动策略", "先选行动策略，再进入作答。策略与关卡环境越匹配，奖励越高。")
tactic_options = stage.get("tactic_options", []) or []
selected_tactic_id = ""
if tactic_options:
    tactic_map = {item.get("id", ""): item for item in tactic_options}
    selected_tactic_id = st.radio(
        "请选择本关行动策略",
        options=[item.get("id", "") for item in tactic_options],
        format_func=lambda option: tactic_map.get(option, {}).get("title", option),
        index=0,
        key=f"tactic::{node.get('id', '')}",
        horizontal=True,
    )
    selected_tactic = tactic_map.get(selected_tactic_id, {})
    render_detail_panels(
        [
            {
                "title": selected_tactic.get("title", "行动策略"),
                "desc": selected_tactic.get("desc", "请结合当前关卡环境选择策略。"),
            },
            {
                "title": "推荐策略",
                "desc": f"{stage.get('recommended_tactic_title', '默认推进')}：{stage.get('recommended_tactic_reason', '')}",
            },
        ]
    )

render_section("多媒体材料与作答线索", "不同题型会提供不同的观察重点，避免答题只剩下“裸选择”。")
material_left, material_right = st.columns([1.1, 1])
with material_left:
    st.markdown(f"**材料类型：** {stage.get('question_type', '情境选择题')}")
    if stage.get("material_title"):
        st.markdown(f"**{stage.get('material_title', '')}**")
    for point in stage.get("material_points", []):
        st.markdown(f"- {point}")
with material_right:
    if stage.get("question_type") == "看图识史":
        st.caption("请先观察左侧图片中的场景特征，再结合历史背景作答。")
    elif stage.get("question_type") == "地图纠错":
        st.caption("请先观察路线图，再判断哪一种路线理解或结论存在偏差。")
    elif stage.get("question_type") == "听音辨曲":
        st.caption("请先播放音频线索，再把诗句与节点环境、精神内涵对应起来。")
    else:
        st.caption("请先阅读剧情导入和角色任务卡，再进入题目判断。")

st.markdown("---")
st.markdown("## 开始作答")
st.write(stage.get("question", "暂无题目。"))
answer = st.radio("请选择你的答案", stage.get("options", []), index=None, key=f"story_answer_{node.get('id', '')}")

if st.button("提交答案", width="stretch", type="primary", disabled=not answer):
    old_progress = story_state.get("progress", {}) or {}
    result = submit_stage_answer(story_state, answer or "", tactic_id=selected_tactic_id)
    answer_detail = result.get("answer_detail", {})
    answered_node = result.get("answered_node", {}) or {}
    new_progress = result.get("progress", {}) or {}
    score_delta = int(new_progress.get("red_star_points", 0)) - int(old_progress.get("red_star_points", 0))
    grain_delta = int(new_progress.get("grain", 0)) - int(old_progress.get("grain", 0))

    if team:
        updated_team = record_team_progress(
            team_id=team.get("team_id", ""),
            user_name=st.session_state.get("user_name", "红色学习者"),
            unit_name=st.session_state.get("unit_name", "体验组"),
            role_name=story_state.get("role_name", "侦察兵"),
            node_id=answered_node.get("id", ""),
            node_title=answered_node.get("title", ""),
            score_delta=score_delta,
            grain_delta=grain_delta,
            correct=result.get("correct", False),
        )
        if updated_team:
            st.session_state["current_team_name"] = updated_team.get("team_name", "")
            st.session_state["current_branch_name"] = updated_team.get("branch_name", "")
            team = updated_team

    share_text = build_team_share_text(team.get("team_id", ""), st.session_state.get("user_name", "")) if team else ""
    record_answer_event(
        user_name=st.session_state.get("user_name", "红色学习者"),
        unit_name=st.session_state.get("unit_name", "体验组"),
        role_name=story_state.get("role_name", "侦察兵"),
        activity_id=story_state.get("activity_id", "global"),
        activity_name=story_state.get("activity_name", "长征主线闯关"),
        node_id=answered_node.get("id", ""),
        node_title=answered_node.get("title", ""),
        question_type=answer_detail.get("question_type", stage.get("question_type", "情境选择题")),
        correct=result.get("correct", False),
        mode_label="剧情答题",
        team_id=team.get("team_id", "") if team else "",
        team_name=team.get("team_name", "") if team else "",
        branch_name=team.get("branch_name", st.session_state.get("unit_name", "体验组")) if team else "",
        share_text=share_text,
    )
    result["reward_delta"] = {
        "score_delta": score_delta,
        "grain_delta": grain_delta,
    }
    st.session_state["story_state"] = result.get("state", story_state)
    st.session_state["story_last_result"] = result
    st.rerun()

last_result = st.session_state.get("story_last_result")
if last_result and last_result.get("answer_detail"):
    detail = last_result.get("answer_detail", {})
    answered_node = last_result.get("answered_node", {}) or {}
    answered_bundle = last_result.get("knowledge_cards", []) or []
    if last_result.get("correct"):
        st.success(last_result.get("feedback", "回答正确。"))
    else:
        st.warning(last_result.get("feedback", "回答未命中全部要点。"))
    if last_result.get("role_feedback"):
        st.info(last_result.get("role_feedback", ""))

    st.markdown(f"### 正确答案解析 | {answered_node.get('title', node.get('title', '当前关卡'))}")
    st.write(detail.get("explanation", ""))
    st.markdown(f"**正确答案：** {detail.get('expected_answer', '')}")
    st.markdown("### 作战结果")
    st.write(last_result.get("battle_outcome", ""))
    if last_result.get("after_action_report"):
        for item in last_result.get("after_action_report", []):
            st.markdown(f"- {item}")
    reward_delta = last_result.get("reward_delta", {}) or {}
    score_delta = int(reward_delta.get("score_delta", 0))
    grain_delta = int(reward_delta.get("grain_delta", 0))
    reward_text = f"本关奖励变化：红星积分 {score_delta:+d}，虚拟粮草 {grain_delta:+d}。"
    if reward_text:
        st.caption(reward_text)
    if last_result.get("tactic_match"):
        st.success("本关行动策略与节点环境匹配，已获得额外战术奖励。")
    review_manual = last_result.get("review_manual", []) or []
    if review_manual:
        render_section("战后复盘手册", "把这道题真正变成一次战役复盘，而不是只看对错。")
        render_detail_panels(review_manual)
    if last_result.get("continuation_story"):
        render_section("行军续报", "答题之后，继续沿主线看这场判断将把队伍带向哪里。")
        render_formal_script(
            last_result.get("continuation_story", ""),
            title=f"{answered_node.get('title', node.get('title', '当前关卡'))} · 行军续报",
            label="关后讲述",
            meta=["主线推进", answered_node.get("route_stage", "长征节点")],
        )
    chapter_completion = last_result.get("chapter_completion", {}) or {}
    if chapter_completion:
        render_section("阶段总结", "每完成一个长征篇章，都要停下来回望这一路是怎样走过来的。")
        render_detail_panels(
            [
                {
                    "title": "完成篇章",
                    "desc": f"{chapter_completion.get('badge', '篇章结算')} · {chapter_completion.get('title', '主线篇章')}",
                },
                {
                    "title": "阶段奖励",
                    "desc": chapter_completion.get("reward_text", "阶段奖励已发放。"),
                },
                {
                    "title": "已完成篇章数",
                    "desc": f"{chapter_completion.get('completed_count', 0)} / 4",
                },
                {
                    "title": "下一阶段",
                    "desc": chapter_completion.get("next_subtitle", "继续沿主线推进。"),
                },
            ]
        )
        render_formal_script(
            chapter_completion.get("script", ""),
            title=f"{chapter_completion.get('title', '长征篇章')}阶段讲述",
            label="阶段讲述稿",
            meta=[chapter_completion.get("badge", "篇章结算"), "阶段总结"],
        )
    st.markdown("### 延伸知识点")
    st.write(detail.get("extended_note", ""))

    if team:
        st.markdown("### 小队协作反馈")
        st.write(
            f"本次作答已经同步计入 **{team.get('team_name', st.session_state.get('current_team_name', '红军小队'))}**。"
            f"你的小队可在活动中心、排行榜和数据大屏中实时看到更新结果。"
        )

    st.markdown("### 历史小课堂")
    for item in answered_bundle[:3]:
        st.markdown(f"- **{item.get('title', '')}**：{item.get('summary', item.get('answer', ''))}")

    if last_result.get("next_node"):
        next_node = last_result.get("next_node", {})
        st.markdown("### 下一节点推荐")
        st.write(f"{next_node.get('title', '')} | {next_node.get('summary', '')}")

render_section("知识卡片联动", "答题并不是终点，每一关都要把题目、知识点和节点背景关联起来。")
if knowledge_bundle:
    cols = st.columns(min(3, len(knowledge_bundle[:3])))
    for index, item in enumerate(knowledge_bundle[:3]):
        with cols[index % len(cols)]:
            st.markdown(f"**{item.get('title', '')}**")
            st.write(item.get("summary", item.get("answer", "")))
else:
    st.info("当前节点暂无额外知识卡片。")
