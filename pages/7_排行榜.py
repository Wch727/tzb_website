"""排行榜页。"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from activity_manager import get_activity, list_activities
from dashboard_data import build_live_battle_rows
from leaderboard import (
    build_user_share_text,
    get_activity_leaderboard,
    get_live_leaderboard,
    get_unit_leaderboard,
    get_user_battles,
)
from streamlit_ui import render_hero, render_metrics, render_section, render_top_nav, setup_page
from team_manager import build_team_share_text, get_branch_pk_board, get_team_leaderboard


def _render_rank_board(current_activity_id: str) -> None:
    """渲染排行榜主体。"""
    activity = get_activity(current_activity_id) if current_activity_id else {}
    render_metrics(
        [
            {"label": "全服实时榜单", "value": len(get_live_leaderboard(limit=100, hours=72))},
            {"label": "当前活动个人榜", "value": len(get_activity_leaderboard(current_activity_id, limit=100)) if current_activity_id else 0},
            {"label": "红军小队数", "value": len(get_team_leaderboard(current_activity_id, limit=100)) if current_activity_id else 0},
            {"label": "支部PK条目", "value": len(get_branch_pk_board(current_activity_id, limit=100)) if current_activity_id else 0},
        ]
    )

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        ["全服实时榜", "活动个人榜", "红军小队榜", "支部PK榜", "班级/单位榜", "实时战绩流"]
    )

    with tab1:
        render_section("全服实时排行榜", "展示平台近阶段的最佳战绩，适合答辩现场和活动现场直接投屏。")
        rows = get_live_leaderboard(activity_id="", limit=20, hours=72)
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info("暂无全服实时成绩记录。")

    with tab2:
        render_section("活动个人榜", "按活动查看个人战绩，适合课堂竞赛、主题活动和研学任务场景。")
        if activity:
            st.caption(f"当前活动：{activity.get('name', '')} | {activity.get('mode', '')}")
        rows = get_activity_leaderboard(current_activity_id, limit=20) if current_activity_id else []
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info("当前活动还没有成绩记录。")

    with tab3:
        render_section("红军小队榜", "多名队员分别完成剧情关卡后，会自动汇总到小队总分，用于展示协作答题效果。")
        rows = get_team_leaderboard(current_activity_id, limit=20) if current_activity_id else []
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info("当前活动还没有小队战绩。")

    with tab4:
        render_section("支部PK榜", "以支部或单位为聚合维度，展示支部PK对抗赛的最小可演示版结果。")
        rows = get_branch_pk_board(current_activity_id, limit=20) if current_activity_id else []
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info("当前活动还没有支部PK成绩。")

    with tab5:
        render_section("班级/单位榜", "把个人战绩按班级、单位或学习小组聚合，更贴近真实组织化活动的展示方式。")
        rows = get_unit_leaderboard(current_activity_id, limit=20) if current_activity_id else []
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info("当前活动还没有班级/单位排行数据。")

    with tab6:
        render_section("实时战绩流与分享", "用于展示最新战绩播报、主持口播文案和个人/小队分享内容。")
        live_left, live_right = st.columns([1.1, 1])
        with live_left:
            live_rows = build_live_battle_rows(hours=48, limit=12)
            if live_rows:
                st.dataframe(pd.DataFrame(live_rows), use_container_width=True, hide_index=True)
            else:
                st.info("当前还没有实时战绩流。")
        with live_right:
            user_name = st.session_state.get("user_name", "红色学习者")
            personal_share = build_user_share_text(user_name, current_activity_id)
            team_share = build_team_share_text(
                st.session_state.get("current_team_id", ""),
                st.session_state.get("user_name", ""),
            )
            st.text_area("个人分享文案", value=personal_share, height=120)
            st.text_area("小队分享文案", value=team_share, height=120)

            st.markdown("### 最近个人战绩")
            battle_rows = get_user_battles(user_name, limit=6)
            if battle_rows:
                st.dataframe(pd.DataFrame(battle_rows), use_container_width=True, hide_index=True)
            else:
                st.info("当前用户还没有战绩记录。")


setup_page("排行榜", icon="🏆")
render_top_nav("排行榜")
render_hero(
    title="排行榜",
    subtitle="当前版本已提供全服实时榜、活动个人榜、红军小队榜、支部PK榜、班级/单位榜以及实时战绩流，便于老师直接看到协作答题和组织化对抗确实存在。",
    badges=["全服实时榜", "红军小队榜", "支部PK榜", "战绩分享"],
)

activities = list_activities()
activity_ids = [item["activity_id"] for item in activities]
current_activity_id = st.session_state.get("current_activity_id", activity_ids[0] if activity_ids else "")
if current_activity_id not in activity_ids and activity_ids:
    current_activity_id = activity_ids[0]

if activity_ids:
    current_activity_id = st.selectbox(
        "排行榜活动范围",
        activity_ids,
        index=activity_ids.index(current_activity_id) if current_activity_id in activity_ids else 0,
        format_func=lambda item: next((activity["name"] for activity in activities if activity["activity_id"] == item), item),
    )
    st.session_state["current_activity_id"] = current_activity_id

refresh_left, refresh_right = st.columns([1, 2])
with refresh_left:
    auto_refresh = st.toggle("自动刷新", value=True, help="开启后排行榜每 12 秒自动刷新一次。")
with refresh_right:
    if st.button("立即刷新排行", use_container_width=True):
        st.rerun()

if auto_refresh and hasattr(st, "fragment"):
    @st.fragment(run_every="12s")
    def _rank_fragment() -> None:
        _render_rank_board(current_activity_id)

    _rank_fragment()
else:
    _render_rank_board(current_activity_id)
