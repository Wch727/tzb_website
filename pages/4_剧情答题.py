"""剧情答题页。"""

from __future__ import annotations

import streamlit as st

from certificate import generate_certificate_svg
from dashboard_data import record_answer_event, record_participation_event, record_share_event
from knowledge_cards import build_related_knowledge_bundle
from leaderboard import build_user_share_text, record_leaderboard_entry
from media import render_audio_player, render_node_image
from quiz_engine import create_story_state, get_stage_package, submit_stage_answer
from streamlit_ui import render_hero, render_section, render_top_nav, setup_page
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
    subtitle="围绕长征时间线逐关推进。每一关都包含历史导入、角色任务、多媒体题型、答案反馈、历史小课堂和成长激励，同时支持将个人贡献同步到红军小队与支部PK战场。",
    badges=["主线关卡", "多媒体题型", "红军小队", "支部PK"],
)

if not st.session_state.get("selected_role_id"):
    st.warning("请先完成角色选择，再进入剧情答题。")
    st.page_link("pages/2_角色选择.py", label="前往角色选择", use_container_width=True)
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
    metrics = st.columns(4)
    with metrics[0]:
        st.metric("红星积分", progress.get("red_star_points", 0))
    with metrics[1]:
        st.metric("虚拟粮草", progress.get("grain", 0))
    with metrics[2]:
        st.metric("当前军衔", progress.get("rank_title", "红军新兵"))
    with metrics[3]:
        st.metric("已获勋章", len(progress.get("medals", [])))

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
    st.image(svg.encode("utf-8"), use_container_width=True)
    st.download_button(
        "下载电子证书（SVG）",
        data=svg.encode("utf-8"),
        file_name="long_march_certificate.svg",
        mime="image/svg+xml",
        use_container_width=True,
    )

    personal_share = build_user_share_text(
        st.session_state.get("user_name", "红色学习者"),
        story_state.get("activity_id", "global"),
    )
    team_share = build_team_share_text(team.get("team_id", ""), st.session_state.get("user_name", ""))
    share_left, share_right = st.columns(2)
    with share_left:
        st.text_area("个人战绩分享文案", value=personal_share, height=130)
        if st.button("广播个人战绩", use_container_width=True, disabled=not personal_share):
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
        if st.button("广播小队战绩", use_container_width=True, disabled=not team_share):
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
        if st.button("查看排行榜", use_container_width=True):
            st.switch_page("pages/7_排行榜.py")
    with col2:
        if st.button("前往活动中心", use_container_width=True):
            st.switch_page("pages/6_活动中心.py")
    with col3:
        if st.button("重新开始活动", use_container_width=True):
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

status_cols = st.columns(6)
with status_cols[0]:
    st.metric("红星积分", progress.get("red_star_points", 0))
with status_cols[1]:
    st.metric("虚拟粮草", progress.get("grain", 0))
with status_cols[2]:
    st.metric("当前军衔", progress.get("rank_title", "红军新兵"))
with status_cols[3]:
    st.metric("已获勋章", len(progress.get("medals", [])))
with status_cols[4]:
    st.metric("红军小队", team.get("team_name", "未加入"))
with status_cols[5]:
    st.metric("支部归属", team.get("branch_name", st.session_state.get("unit_name", "体验组")))

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
    st.markdown(f"**题型：** {stage.get('question_type', '情境选择题')}")
    st.markdown(f"**角色任务提示：** {stage.get('role_brief', '')}")
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
    st.markdown("### 背景导入")
    background = str(node.get("background", "") or "")
    st.write(background[:220] + ("..." if len(background) > 220 else ""))
    st.markdown("### 剧情旁白")
    st.write(node.get("summary", ""))
    if team:
        st.markdown("### 小队协作状态")
        st.write(
            f"你当前正在为 **{team.get('team_name', '')}** 作战，"
            f"小队总分 {team.get('total_score', 0)}，"
            f"队员 {len(team.get('members', []))} 人。"
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

if st.button("提交答案", use_container_width=True, type="primary", disabled=not answer):
    old_progress = story_state.get("progress", {}) or {}
    result = submit_stage_answer(story_state, answer or "")
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

