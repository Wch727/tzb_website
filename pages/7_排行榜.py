"""排行榜页。"""

from __future__ import annotations

import streamlit as st

from activity_manager import get_activity, list_activities
from leaderboard import get_activity_leaderboard, get_global_leaderboard, get_unit_leaderboard, get_user_battles
from streamlit_ui import render_hero, render_section, render_top_nav, setup_page


setup_page("排行榜", icon="🏆")
render_top_nav("排行榜")
render_hero(
    title="排行榜",
    subtitle="当前版本提供全局排行榜、活动排行榜和个人战绩，作为后续小队协作与支部 PK 的最小可用基础。",
    badges=["全局排行", "活动排行", "个人战绩", "战绩分享"],
)

activities = list_activities()
activity_ids = [item["activity_id"] for item in activities]
current_activity_id = st.session_state.get("current_activity_id", activity_ids[0] if activity_ids else "")
if current_activity_id not in activity_ids and activity_ids:
    current_activity_id = activity_ids[0]
if activity_ids:
    current_activity_id = st.selectbox(
        "活动排行榜范围",
        activity_ids,
        index=activity_ids.index(current_activity_id) if current_activity_id in activity_ids else 0,
        format_func=lambda item: next((activity["name"] for activity in activities if activity["activity_id"] == item), item),
    )
    st.session_state["current_activity_id"] = current_activity_id
activity = get_activity(current_activity_id) if current_activity_id else {}

tab1, tab2, tab3, tab4 = st.tabs(["全局排行榜", "活动排行榜", "单位排行", "个人战绩"])

with tab1:
    render_section("全局排行榜", "展示平台范围内的历史最佳成绩，适合作为答辩现场的运营效果展示。")
    rows = get_global_leaderboard(limit=20)
    if rows:
        for item in rows:
            st.markdown(
                f"{item.get('rank', 0)}. **{item.get('user_name', '')}** · "
                f"{item.get('activity_name', '')} · {item.get('score', 0)} 分 · {item.get('rank_title', '')} · {item.get('unit_name', '未填写单位')}"
            )
    else:
        st.info("暂无全局成绩记录。")

with tab2:
    render_section("活动排行榜", "按活动查看参与者成绩，适合班级竞赛、团日活动和研学任务场景。")
    if activity:
        st.caption(f"当前活动：{activity.get('name', '')} · {activity.get('mode', '')}")
    rows = get_activity_leaderboard(current_activity_id, limit=20) if current_activity_id else []
    if rows:
        for item in rows:
            st.markdown(
                f"{item.get('rank', 0)}. **{item.get('user_name', '')}** · "
                f"{item.get('role_name', '')} · {item.get('score', 0)} 分 · "
                f"粮草 {item.get('grain', 0)} · {item.get('rank_title', '')} · {item.get('unit_name', '未填写单位')}"
            )
    else:
        st.info("当前活动还没有成绩记录。")

with tab3:
    render_section("单位排行", "将个人成绩按班级/单位/小组进行聚合，更接近实际活动组织与课堂竞赛场景。")
    rows = get_unit_leaderboard(current_activity_id, limit=20) if current_activity_id else []
    if rows:
        for item in rows:
            st.markdown(
                f"{item.get('rank', 0)}. **{item.get('unit_name', '')}** · "
                f"总分 {item.get('total_score', 0)} · 粮草 {item.get('total_grain', 0)} · "
                f"参与人数 {item.get('member_count', 0)} · 最高军衔 {item.get('best_rank_title', '')}"
            )
    else:
        st.info("当前活动还没有单位排行数据。先完成一次活动答题即可生成。")

with tab4:
    render_section("个人战绩", "记录最近完成的活动和关卡表现，可作为战绩分享的最小可演示版本。")
    user_name = st.session_state.get("user_name", "红色学习者")
    rows = get_user_battles(user_name, limit=10)
    if rows:
        latest = rows[0]
        share_text = (
            f"我在“{latest.get('activity_name', '')}”中获得 {latest.get('score', 0)} 分，"
            f"当前军衔为 {latest.get('rank_title', '')}，来自 {latest.get('unit_name', '未填写单位')}，欢迎一起重走长征路。"
        )
        st.text_area("战绩分享文案", value=share_text, height=80)
        for item in rows:
            st.markdown(
                f"- **{item.get('activity_name', '')}** · {item.get('score', 0)} 分 · "
                f"{item.get('rank_title', '')} · 完成时间 {item.get('finished_at', '')}"
            )
    else:
        st.info("当前用户还没有战绩记录。完成一次活动即可生成战绩。")

render_section("后续扩展位", "当前已实现个人与活动排行，作为“小队协作”“支部 PK”扩展的可演示基础。")
st.markdown(
    "\n".join(
        [
            "- 红军小队：可在后续版本中将活动参与者按小队聚合并计算小队总分。",
            "- 支部 PK：可在现有活动排行榜基础上增加单位字段与单位排行。",
            "- 大屏展示：可复用当前排行榜与活动统计数据，扩展为会场展示视图。",
        ]
    )
)
