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
from platform_components import rank_podium_html, render_platform_showcase
from streamlit_ui import render_metrics, render_section, render_top_nav, setup_page
from team_manager import build_team_share_text, get_branch_pk_board, get_team_leaderboard


def _render_rank_board(current_activity_id: str) -> None:
    """渲染排行榜主体。"""
    activity = get_activity(current_activity_id) if current_activity_id else {}
    live_rows_for_podium = get_live_leaderboard(activity_id="", limit=3, hours=72)
    if live_rows_for_podium:
        render_section("全服前三", "先看当前最突出的学习战绩，再进入各类榜单明细。")
        st.html(rank_podium_html(live_rows_for_podium, score_key="score"))
    render_metrics(
        [
            {"label": "全服实时榜单", "value": len(get_live_leaderboard(limit=100, hours=72))},
            {"label": "当前活动个人榜", "value": len(get_activity_leaderboard(current_activity_id, limit=100)) if current_activity_id else 0},
            {"label": "红军小队数", "value": len(get_team_leaderboard(current_activity_id, limit=100)) if current_activity_id else 0},
            {"label": "支部对抗条目", "value": len(get_branch_pk_board(current_activity_id, limit=100)) if current_activity_id else 0},
        ]
    )

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        ["全服实时榜", "活动个人榜", "红军小队榜", "支部对抗榜", "班级/单位榜", "实时战绩流"]
    )

    with tab1:
        render_section("全服实时排行榜", "集中呈现近期学习表现突出的个人与队伍。")
        rows = get_live_leaderboard(activity_id="", limit=20, hours=72)
        if rows:
            st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
        else:
            st.info("暂无全服实时成绩记录。")

    with tab2:
        render_section("活动个人榜", "按活动范围查看个人战绩。")
        if activity:
            st.caption(f"活动范围：{activity.get('name', '')} | {activity.get('mode', '')}")
        rows = get_activity_leaderboard(current_activity_id, limit=20) if current_activity_id else []
        if rows:
            st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
        else:
            st.info("活动成绩尚未形成。")

    with tab3:
        render_section("红军小队榜", "各队伍成员的作答成果将在此汇总为协作战绩。")
        rows = get_team_leaderboard(current_activity_id, limit=20) if current_activity_id else []
        if rows:
            st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
        else:
            st.info("小队战绩尚未形成。")

    with tab4:
        render_section("支部对抗榜", "以支部或单位为聚合维度，展示组织化学习对抗的阶段结果。")
        rows = get_branch_pk_board(current_activity_id, limit=20) if current_activity_id else []
        if rows:
            st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
        else:
            st.info("支部对抗成绩尚未形成。")

    with tab5:
        render_section("班级/单位榜", "把个人战绩按班级、单位或学习小组聚合，更贴近真实组织化活动的展示方式。")
        rows = get_unit_leaderboard(current_activity_id, limit=20) if current_activity_id else []
        if rows:
            st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
        else:
            st.info("班级或单位排行尚未形成。")

    with tab6:
        render_section("实时战绩流与分享", "汇集最新战绩播报与个人、小队分享内容。")
        live_left, live_right = st.columns([1.1, 1])
        with live_left:
            live_rows = build_live_battle_rows(hours=48, limit=12)
            if live_rows:
                st.dataframe(pd.DataFrame(live_rows), width="stretch", hide_index=True)
            else:
                st.info("实时战绩流尚未形成。")
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
                st.dataframe(pd.DataFrame(battle_rows), width="stretch", hide_index=True)
            else:
                st.info("个人战绩尚未形成。")


setup_page("排行榜", icon="🏆")
render_top_nav("排行榜")

activities = list_activities()
activity_ids = [item["activity_id"] for item in activities]
current_activity_id = st.session_state.get("current_activity_id", activity_ids[0] if activity_ids else "")
if current_activity_id not in activity_ids and activity_ids:
    current_activity_id = activity_ids[0]
activity = get_activity(current_activity_id) if current_activity_id else {}
render_platform_showcase(
    title="排行榜",
    subtitle="汇集个人、小队、单位和活动榜单，适合课堂竞赛、支部对抗和现场投屏展示。",
    kicker="学习战绩中心",
    tags=["全服实时榜", "活动个人榜", "红军小队榜", "支部对抗榜"],
    panel_title=activity.get("name", "当前活动榜单"),
    panel_text="完成互动闯关后，个人成绩、小队贡献和单位排行会自动进入榜单。",
    stats=[
        {"label": "全服记录", "value": len(get_live_leaderboard(limit=100, hours=72))},
        {"label": "活动个人", "value": len(get_activity_leaderboard(current_activity_id, limit=100)) if current_activity_id else 0},
        {"label": "红军小队", "value": len(get_team_leaderboard(current_activity_id, limit=100)) if current_activity_id else 0},
        {"label": "单位排行", "value": len(get_unit_leaderboard(current_activity_id, limit=100)) if current_activity_id else 0},
    ],
    variant="scoreboard",
)

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
    if st.button("立即刷新排行", width="stretch"):
        st.rerun()

if auto_refresh and hasattr(st, "fragment"):
    @st.fragment(run_every="12s")
    def _rank_fragment() -> None:
        _render_rank_board(current_activity_id)

    _rank_fragment()
else:
    _render_rank_board(current_activity_id)
