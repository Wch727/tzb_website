"""剧情答题页。"""

from __future__ import annotations

import streamlit as st

from certificate import generate_certificate_svg
from dashboard_data import record_answer_event, record_participation_event
from game import get_route_node
from knowledge_cards import build_related_knowledge_bundle
from leaderboard import record_leaderboard_entry
from media import render_audio_player, render_node_image
from quiz_engine import create_story_state, get_stage_package, submit_stage_answer
from streamlit_ui import render_hero, render_section, render_top_nav, setup_page


def _ensure_story_state() -> dict:
    """确保剧情状态存在。"""
    story_state = st.session_state.get("story_state", {})
    if story_state:
        return story_state
    role_id = st.session_state.get("selected_role_id", "scout")
    activity_id = st.session_state.get("current_activity_id", "knowledge-contest")
    story_state = create_story_state(role_id=role_id, activity_id=activity_id)
    st.session_state["story_state"] = story_state
    enter_key = f"dashboard_participation::{story_state.get('activity_id', 'global')}::{st.session_state.get('user_name', '红色学习者')}"
    if not st.session_state.get(enter_key):
        record_participation_event(
            user_name=st.session_state.get("user_name", "红色学习者"),
            unit_name=st.session_state.get("unit_name", "体验组"),
            role_name=story_state.get("role_name", "侦察兵"),
            activity_id=story_state.get("activity_id", "global"),
            activity_name=story_state.get("activity_name", "长征主线闯关"),
        )
        st.session_state[enter_key] = True
    return story_state


setup_page("剧情答题", icon="🎯")
render_top_nav("剧情答题")
render_hero(
    title="剧情答题",
    subtitle="围绕长征时间线逐关推进。每一关都包含历史导入、角色任务、多媒体题型、答案反馈、历史小课堂和成长激励。",
    badges=["主线关卡", "多媒体题型", "历史小课堂", "成长系统"],
)

if not st.session_state.get("selected_role_id"):
    st.warning("请先完成角色选择，再进入剧情答题。")
    st.page_link("pages/2_角色选择.py", label="前往角色选择", use_container_width=True)
    st.stop()

story_state = _ensure_story_state()

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
    render_section("结算页", "展示总积分、军衔、勋章、错题复盘和电子证书。")
    st.caption(f"参与身份：{st.session_state.get('user_name', '红色学习者')} · {st.session_state.get('unit_name', '体验组')}")
    st.metric("红星积分", progress.get("red_star_points", 0))
    st.metric("虚拟粮草", progress.get("grain", 0))
    st.metric("当前军衔", progress.get("rank_title", "红军新兵"))
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
    col1, col2 = st.columns(2)
    with col1:
        if st.button("查看排行榜", use_container_width=True):
            st.switch_page("pages/7_排行榜.py")
    with col2:
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
    f"第 {stage.get('current_step', 1)} / {stage.get('total_steps', 1)} 关 · "
    f"{story_state.get('activity_name', '长征主线闯关')} · {story_state.get('role_name', '侦察兵')} · "
    f"{st.session_state.get('unit_name', '体验组')}",
)

status_cols = st.columns(4)
with status_cols[0]:
    st.metric("红星积分", progress.get("red_star_points", 0))
with status_cols[1]:
    st.metric("虚拟粮草", progress.get("grain", 0))
with status_cols[2]:
    st.metric("当前军衔", progress.get("rank_title", "红军新兵"))
with status_cols[3]:
    st.metric("已获勋章", len(progress.get("medals", [])))

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
    st.write(node.get("background", "")[:220] + ("..." if len(node.get("background", "")) > 220 else ""))
    st.markdown("### 剧情旁白")
    st.write(node.get("summary", ""))

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
    result = submit_stage_answer(story_state, answer or "")
    answer_detail = result.get("answer_detail", {})
    answered_node = result.get("answered_node", {}) or {}
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

    st.markdown(f"### 正确答案解析 · {answered_node.get('title', node.get('title', '当前关卡'))}")
    st.write(detail.get("explanation", ""))
    st.markdown(f"**正确答案：** {detail.get('expected_answer', '')}")
    st.markdown("### 延伸知识点")
    st.write(detail.get("extended_note", ""))

    st.markdown("### 历史小课堂")
    for item in answered_bundle[:3]:
        st.markdown(f"- **{item.get('title', '')}**：{item.get('summary', item.get('answer', ''))}")

    if last_result.get("next_node"):
        next_node = last_result.get("next_node", {})
        st.markdown("### 下一节点推荐")
        st.write(f"{next_node.get('title', '')} · {next_node.get('summary', '')}")

render_section("知识卡片联动", "答题并不是终点，每一关都要把题目、知识点和节点背景关联起来。")
if knowledge_bundle:
    cols = st.columns(min(3, len(knowledge_bundle[:3])))
    for index, item in enumerate(knowledge_bundle[:3]):
        with cols[index % len(cols)]:
            st.markdown(f"**{item.get('title', '')}**")
            st.write(item.get("summary", item.get("answer", "")))
else:
    st.info("当前节点暂无额外知识卡片。")
