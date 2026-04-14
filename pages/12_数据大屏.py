"""数据大屏页。"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard_data import build_dashboard_payload, build_dashboard_summary
from streamlit_ui import render_hero, render_metrics, render_section, render_top_nav, setup_page


def _render_dashboard_body(hours: int) -> None:
    """渲染大屏主体。"""
    payload = build_dashboard_payload(hours=hours)
    summary = payload.get("summary", {})
    render_metrics(
        [
            {"label": f"近 {hours} 小时参与人数", "value": summary.get("recent_participant_count", 0)},
            {"label": f"近 {hours} 小时答题数", "value": summary.get("recent_answer_count", 0)},
            {"label": "近 24 小时正确率", "value": f"{summary.get('correct_rate', 0)}%"},
            {"label": "活跃活动数", "value": summary.get("activity_count", 0)},
            {"label": "红军小队数", "value": summary.get("team_count", 0)},
            {"label": "支部数", "value": summary.get("branch_count", 0)},
        ]
    )

    top_left, top_right = st.columns([1.2, 1])
    with top_left:
        render_section("答题热度趋势", "按小时汇总答题提交次数，可直接用于投屏展示近期互动热度。")
        heat_rows = payload.get("answer_heat", [])
        if heat_rows:
            heat_df = pd.DataFrame(heat_rows).set_index("time_label")
            st.line_chart(heat_df)
        else:
            st.info("当前时间窗口内暂无答题热度数据。")
    with top_right:
        render_section("活动动态概览", "展示各活动的参与人数、答题数、小队数和正确率。")
        activity_live = payload.get("activity_live", [])
        if activity_live:
            st.dataframe(pd.DataFrame(activity_live), use_container_width=True, hide_index=True)
        else:
            st.info("当前暂无活动动态数据。")

    middle_left, middle_right = st.columns(2)
    with middle_left:
        render_section("全服实时排行榜", "展示近期表现突出的用户与队伍，适合课堂、展陈和活动现场投屏。")
        realtime_rows = payload.get("realtime_leaderboard", [])
        if realtime_rows:
            st.dataframe(pd.DataFrame(realtime_rows), use_container_width=True, hide_index=True)
        else:
            st.info("当前暂无全服实时排行数据。")
    with middle_right:
        render_section("红军小队排行榜", "展示协作答题形成的小队总分与粮草表现。")
        team_rows = payload.get("team_leaderboard", [])
        if team_rows:
            st.dataframe(pd.DataFrame(team_rows), use_container_width=True, hide_index=True)
        else:
            st.info("当前暂无红军小队排行数据。")

    pk_left, pk_right = st.columns(2)
    with pk_left:
        render_section("支部对抗榜", "按支部或单位汇总队伍成绩，适合组织化学习活动中的集体展示。")
        branch_rows = payload.get("branch_pk", [])
        if branch_rows:
            st.dataframe(pd.DataFrame(branch_rows), use_container_width=True, hide_index=True)
        else:
            st.info("当前暂无支部对抗成绩。")
    with pk_right:
        render_section("班级/单位排行预览", "用于课堂、班级、支部等组织化学习场景。")
        unit_rows = payload.get("unit_leaderboard", [])
        if unit_rows:
            st.dataframe(pd.DataFrame(unit_rows), use_container_width=True, hide_index=True)
        else:
            st.info("当前暂无班级/单位排行数据。")

    chart_left, chart_right = st.columns(2)
    with chart_left:
        render_section("节点热度排行", "统计被答题最频繁的主线节点。")
        node_rows = payload.get("node_heat", [])
        if node_rows:
            node_df = pd.DataFrame(node_rows).set_index("node_title")
            st.bar_chart(node_df[["answer_count"]])
            st.dataframe(pd.DataFrame(node_rows), use_container_width=True, hide_index=True)
        else:
            st.info("当前暂无节点热度数据。")
    with chart_right:
        render_section("题型与角色分布", "展示多媒体题型与角色参与使用情况。")
        question_rows = payload.get("question_type_distribution", [])
        role_rows = payload.get("role_distribution", [])
        if question_rows:
            question_df = pd.DataFrame(question_rows).set_index("question_type")
            st.bar_chart(question_df[["count"]])
        if role_rows:
            role_df = pd.DataFrame(role_rows).set_index("role_name")
            st.bar_chart(role_df[["count"]])
        if not question_rows and not role_rows:
            st.info("当前暂无题型与角色分布数据。")

    render_section("实时战绩播报流", "可作为活动主持口播、现场播报和大屏轮播数据源。")
    live_rows = payload.get("live_feed", [])
    if live_rows:
        st.dataframe(pd.DataFrame(live_rows), use_container_width=True, hide_index=True)
    else:
        st.info("当前暂无实时战绩播报数据。")


setup_page("数据大屏", icon="📳")
render_top_nav("数据大屏")
render_hero(
    title="数据大屏",
    subtitle="该页面用于大屏投屏展示，集中呈现答题热度、参与人数、全服实时榜、红军小队榜、支部对抗榜、班级或单位排名和实时战绩流。",
    badges=["全服实时榜", "红军小队榜", "支部对抗榜", "实时战绩流"],
)

hours = st.selectbox("统计时间窗口", [6, 12, 24, 48], index=2, format_func=lambda item: f"最近 {item} 小时")
summary = build_dashboard_summary(hours=hours)
st.caption(
    f"当前窗口：最近 {hours} 小时 | 参与人数 {summary.get('recent_participant_count', 0)} | "
    f"答题数 {summary.get('recent_answer_count', 0)} | 正确率 {summary.get('correct_rate', 0)}%"
)

refresh_col1, refresh_col2 = st.columns([1, 2])
with refresh_col1:
    auto_refresh = st.toggle("自动刷新", value=True, help="开启后页面每 15 秒自动刷新一次。")
with refresh_col2:
    if st.button("立即刷新数据", use_container_width=True):
        st.rerun()

if auto_refresh and hasattr(st, "fragment"):
    @st.fragment(run_every="15s")
    def _dashboard_fragment() -> None:
        _render_dashboard_body(hours)

    _dashboard_fragment()
else:
    _render_dashboard_body(hours)
