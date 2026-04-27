"""活动中心页。"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from activity_manager import build_activity_qr_bytes, build_activity_share_link, get_activity, list_activities
from dashboard_data import build_live_battle_rows, record_share_event
from game import get_route_node
from leaderboard import build_user_share_text, get_activity_leaderboard, get_unit_leaderboard
from streamlit_ui import render_cards, render_hero, render_section, render_top_nav, setup_page
from team_manager import (
    build_team_member_summary,
    build_team_share_text,
    get_branch_pk_board,
    get_team,
    get_team_leaderboard,
    get_user_team,
    join_team,
    leave_team,
    list_teams,
    create_team,
)


def _sync_current_team(activity_id: str) -> dict:
    """同步当前用户所在小队到 session。"""
    user_name = st.session_state.get("user_name", "红色学习者")
    team = get_user_team(user_name, activity_id)
    if team:
        st.session_state["current_team_id"] = team.get("team_id", "")
        st.session_state["current_team_name"] = team.get("team_name", "")
        st.session_state["current_branch_name"] = team.get("branch_name", "")
    else:
        st.session_state["current_team_id"] = ""
        st.session_state["current_team_name"] = ""
        st.session_state["current_branch_name"] = ""
    return team


setup_page("活动中心", icon="🎯")
render_top_nav("活动中心")
render_hero(
    title="活动中心",
    subtitle="围绕知识竞赛、党史学习日与研学任务等组织化场景，集中呈现活动入口、协作方式与对抗机制。",
    badges=["活动模板", "红军小队", "支部对抗", "实时战绩"],
)

activities = list_activities()
activity_ids = [item["activity_id"] for item in activities]
current_activity_id = st.session_state.get("current_activity_id", activity_ids[0] if activity_ids else "")
if current_activity_id not in activity_ids and activity_ids:
    current_activity_id = activity_ids[0]

render_section("活动模板总览", "不同活动模板对应不同的组织场景、节点评估范围与协作方式。")
render_cards(
    [
        {
            "label": item.get("mode", ""),
            "title": item.get("name", ""),
            "desc": (
                f"{item.get('description', '')} "
                f"时长：{item.get('time_range', '')}，"
                f"小队模式：{'开启' if item.get('support_team_mode') else '关闭'}，"
                f"支部对抗：{'开启' if item.get('support_branch_pk') else '关闭'}。"
            ),
        }
        for item in activities
    ]
)

current_activity_id = st.selectbox(
    "选择活动",
    activity_ids,
    index=activity_ids.index(current_activity_id) if current_activity_id in activity_ids else 0,
    format_func=lambda item: next((activity["name"] for activity in activities if activity["activity_id"] == item), item),
)
st.session_state["current_activity_id"] = current_activity_id
activity = get_activity(current_activity_id)
current_team = _sync_current_team(current_activity_id)

left, right = st.columns([1.1, 1])
with left:
    render_section("活动信息", "活动以节点范围、组织形式与协作规则为基本框架。")
    st.markdown(f"## {activity.get('name', '')}")
    st.write(activity.get("description", ""))
    st.caption(f"活动模式：{activity.get('mode', '')}")
    st.caption(f"活动时长：{activity.get('time_range', '')}")
    st.caption(f"活动状态：{activity.get('status', '')}")
    st.caption(f"覆盖节点：{len(activity.get('node_scope', []))} 个")
    st.caption(f"支持红军小队：{'是' if activity.get('support_team_mode') else '否'}")
    st.caption(f"支持支部对抗：{'是' if activity.get('support_branch_pk') else '否'}")
    st.caption(f"参与身份：{st.session_state.get('user_name', '红色学习者')} | {st.session_state.get('unit_name', '体验组')}")
    if current_team:
        st.success(
            f"所属小队：{current_team.get('team_name', '')} | "
            f"{current_team.get('branch_name', '')} | 队员 {len(current_team.get('members', []))} 人"
        )

    button_cols = st.columns(4)
    with button_cols[0]:
        if st.button("进入闯关大厅", width="stretch"):
            st.session_state["story_state"] = {}
            st.session_state["game_active"] = False
            st.switch_page("pages/4_剧情答题.py")
    with button_cols[1]:
        if st.button("进入路线", width="stretch"):
            st.switch_page("pages/3_长征路线.py")
    with button_cols[2]:
        if st.button("开始答题", width="stretch", type="primary"):
            st.session_state["story_state"] = {}
            st.session_state["game_active"] = False
            st.switch_page("pages/4_剧情答题.py")
    with button_cols[3]:
        if st.button("查看排行榜", width="stretch"):
            st.switch_page("pages/7_排行榜.py")

with right:
    share_link = build_activity_share_link(activity)
    st.text_input("活动分享链接", value=share_link, disabled=True)
    qr_bytes = build_activity_qr_bytes(share_link)
    if qr_bytes:
        st.image(qr_bytes, caption="活动二维码", width=220)
    else:
        st.info("活动分享链接已生成，可通过链接组织访问。")

pending_team_id = st.session_state.get("pending_team_id", "")
pending_team = get_team(pending_team_id) if pending_team_id else {}
if pending_team and pending_team.get("activity_id") == current_activity_id:
    st.info(
        f"你正在通过“{pending_team.get('team_name', '')}”小队二维码进入活动，"
        f"所属单位：{pending_team.get('branch_name', '')}。"
    )
    join_cols = st.columns([1, 1])
    with join_cols[0]:
        if st.button("加入该小队", key=f"join_pending_{pending_team_id}", width="stretch", type="primary"):
            joined = join_team(
                team_id=pending_team_id,
                user_name=st.session_state.get("user_name", "红色学习者"),
                unit_name=st.session_state.get("unit_name", pending_team.get("branch_name", "体验组")),
                role_name=st.session_state.get("selected_role_name", "侦察兵"),
            )
            if joined:
                st.session_state["current_team_id"] = joined.get("team_id", "")
                st.session_state["current_team_name"] = joined.get("team_name", "")
                st.session_state["current_branch_name"] = joined.get("branch_name", "")
                st.session_state["pending_team_id"] = ""
                st.success(f"已加入小队：{joined.get('team_name', '')}")
                st.rerun()
            st.error("加入失败，可能是队伍已满。")
    with join_cols[1]:
        if st.button("暂不加入", key=f"ignore_pending_{pending_team_id}", width="stretch"):
            st.session_state["pending_team_id"] = ""
            st.rerun()

info_tab, team_tab, pk_tab, share_tab = st.tabs(["活动范围", "红军小队", "支部对抗", "战绩分享"])

with info_tab:
    render_section("活动节点范围", "活动不是空壳链接，而是明确绑定了一组主线节点与题目范围。")
    node_scope = activity.get("node_scope", [])
    node_cols = st.columns(4)
    for index, node_id in enumerate(node_scope):
        node = get_route_node(node_id) or {}
        with node_cols[index % 4]:
            st.markdown(f"**{index + 1}. {node.get('title', node_id)}**")
            st.caption(f"{node.get('date', '')} | {node.get('place', '')}")
            summary = str(node.get("summary", "") or "")
            st.write(summary[:88] + ("..." if len(summary) > 88 else ""))

    render_section("活动个人榜预览", "呈现本活动范围内的个人作答表现。")
    ranking = get_activity_leaderboard(current_activity_id, limit=8)
    if ranking:
        st.dataframe(pd.DataFrame(ranking), width="stretch", hide_index=True)
    else:
        st.info("活动成绩尚未形成；完成一次剧情答题后，榜单将自动更新。")

    render_section("班级/单位榜预览", "按班级、单位或学习小组聚合呈现活动成绩。")
    unit_rows = get_unit_leaderboard(current_activity_id, limit=8)
    if unit_rows:
        st.dataframe(pd.DataFrame(unit_rows), width="stretch", hide_index=True)
    else:
        st.info("班级或单位榜单尚未形成。")

with team_tab:
    render_section("红军小队协作", "以小队为单位汇聚成员贡献，形成协作作答与集体推进的战绩结构。")
    if not activity.get("support_team_mode", True):
        st.warning("本场活动暂未开放红军小队协作。")
    else:
        current_team = _sync_current_team(current_activity_id)
        if current_team:
            st.success(
                f"所属小队：{current_team.get('team_name', '')} | "
                f"{current_team.get('branch_name', '')} | 口号：{current_team.get('slogan', '暂无')}"
            )
            team_left, team_right = st.columns([1.05, 1])
            with team_left:
                st.markdown("### 小队成员贡献")
                member_rows = build_team_member_summary(current_team.get("team_id", ""))
                if member_rows:
                    st.dataframe(pd.DataFrame(member_rows), width="stretch", hide_index=True)
            with team_right:
                st.markdown("### 小队战力")
                st.metric("小队总分", current_team.get("total_score", 0))
                st.metric("小队粮草", current_team.get("total_grain", 0))
                st.metric("累计作答", current_team.get("answered_count", 0))
                st.metric("正确率", f"{round((current_team.get('correct_count', 0) / max(current_team.get('answered_count', 1), 1)) * 100, 1)}%")
                if st.button("退出小队", width="stretch"):
                    leave_team(current_team.get("team_id", ""), st.session_state.get("user_name", "红色学习者"))
                    _sync_current_team(current_activity_id)
                    st.success("已退出小队。")
                    st.rerun()
                st.markdown("### 小队专属二维码")
                team_link = build_activity_share_link(activity, team_id=current_team.get("team_id", ""))
                st.text_input("小队分享链接", value=team_link, disabled=True, key=f"team_link_{current_team.get('team_id', '')}")
                team_qr = build_activity_qr_bytes(team_link)
                if team_qr:
                    st.image(team_qr, caption=f"{current_team.get('team_name', '')} 小队二维码", width=220)

        create_col, join_col = st.columns(2)
        with create_col:
            st.markdown("### 创建红军小队")
            with st.form("create_team_form"):
                team_name = st.text_input("小队名称", placeholder="例如：赤水先锋队")
                branch_name = st.text_input("所属支部/单位", value=st.session_state.get("unit_name", "体验组"))
                slogan = st.text_input("小队口号", placeholder="例如：重走长征路，争当先锋队")
                create_submitted = st.form_submit_button("创建并加入小队", width="stretch", type="primary")
            if create_submitted and team_name.strip():
                team = create_team(
                    activity_id=current_activity_id,
                    team_name=team_name.strip(),
                    branch_name=branch_name.strip(),
                    slogan=slogan.strip(),
                    created_by=st.session_state.get("user_name", "红色学习者"),
                    unit_name=st.session_state.get("unit_name", "体验组"),
                    role_name=st.session_state.get("selected_role_name", "侦察兵"),
                    max_team_size=activity.get("max_team_size", 6),
                )
                st.session_state["current_team_id"] = team.get("team_id", "")
                st.session_state["current_team_name"] = team.get("team_name", "")
                st.session_state["current_branch_name"] = team.get("branch_name", "")
                st.success(f"已创建并加入小队：{team.get('team_name', '')}")
                st.rerun()

        with join_col:
            st.markdown("### 加入现有小队")
            teams = list_teams(current_activity_id)
            if teams:
                for item in teams[:8]:
                    st.markdown(
                        f"**{item.get('team_name', '')}** | {item.get('branch_name', '')} | "
                        f"队员 {len(item.get('members', []))}/{item.get('max_team_size', 6)} | "
                        f"总分 {item.get('total_score', 0)}"
                    )
                    team_share_link = build_activity_share_link(activity, team_id=item.get("team_id", ""))
                    with st.expander("查看小队二维码", expanded=False):
                        st.text_input(
                            "小队分享链接",
                            value=team_share_link,
                            disabled=True,
                            key=f"team_list_link_{item.get('team_id', '')}",
                        )
                        team_list_qr = build_activity_qr_bytes(team_share_link)
                        if team_list_qr:
                            st.image(team_list_qr, caption=f"{item.get('team_name', '')} 小队二维码", width=180)
                    if st.button(f"加入 {item.get('team_name', '')}", key=f"join_{item.get('team_id')}", width="stretch"):
                        joined = join_team(
                            team_id=item.get("team_id", ""),
                            user_name=st.session_state.get("user_name", "红色学习者"),
                            unit_name=st.session_state.get("unit_name", "体验组"),
                            role_name=st.session_state.get("selected_role_name", "侦察兵"),
                        )
                        if joined:
                            st.session_state["current_team_id"] = joined.get("team_id", "")
                            st.session_state["current_team_name"] = joined.get("team_name", "")
                            st.session_state["current_branch_name"] = joined.get("branch_name", "")
                            st.success(f"已加入小队：{joined.get('team_name', '')}")
                            st.rerun()
                        st.error("加入失败，可能是队伍已满。")
            else:
                st.info("本场活动尚未组建红军小队。")

        render_section("小队排行榜", "各队伍作答成果按协作总分统一汇总。")
        team_rows = get_team_leaderboard(current_activity_id, limit=10)
        if team_rows:
            st.dataframe(pd.DataFrame(team_rows), width="stretch", hide_index=True)
        else:
            st.info("小队战绩尚未形成。")

with pk_tab:
    render_section("支部对抗赛", "按支部或单位汇总各小队成绩，形成组织化学习的对抗榜单。")
    if not activity.get("support_branch_pk", True):
        st.warning("本场活动暂未开放支部对抗。")
    else:
        pk_rows = get_branch_pk_board(current_activity_id, limit=12)
        if pk_rows:
            top_cards = [
                {
                    "label": f"第 {item.get('rank', 0)} 名",
                    "title": item.get("branch_name", ""),
                    "desc": (
                        f"总分 {item.get('total_score', 0)}，粮草 {item.get('total_grain', 0)}，"
                        f"小队数 {item.get('team_count', 0)}，成员 {item.get('member_count', 0)}。"
                    ),
                }
                for item in pk_rows[:4]
            ]
            render_cards(top_cards)
            st.dataframe(pd.DataFrame(pk_rows), width="stretch", hide_index=True)
        else:
            st.info("支部对抗数据尚未形成；完成小队编组与作答后即可生成榜单。")

with share_tab:
    render_section("实时战绩分享", "可生成个人战绩文案与小队播报文案，用于活动播报与成果传播。")
    personal_share = build_user_share_text(
        st.session_state.get("user_name", "红色学习者"),
        current_activity_id,
    )
    team_share = build_team_share_text(st.session_state.get("current_team_id", ""), st.session_state.get("user_name", ""))

    share_left, share_right = st.columns(2)
    with share_left:
        st.markdown("### 个人战绩分享")
        st.text_area("个人分享文案", value=personal_share, height=130)
        if st.button("记录个人分享播报", width="stretch", disabled=not personal_share):
            record_share_event(
                user_name=st.session_state.get("user_name", "红色学习者"),
                unit_name=st.session_state.get("unit_name", "体验组"),
                activity_id=current_activity_id,
                activity_name=activity.get("name", "长征活动"),
                share_text=personal_share,
                team_id=st.session_state.get("current_team_id", ""),
                team_name=st.session_state.get("current_team_name", ""),
                branch_name=st.session_state.get("current_branch_name", ""),
            )
            st.success("个人战绩已写入实时播报流。")
    with share_right:
        st.markdown("### 小队战绩分享")
        st.text_area("小队分享文案", value=team_share, height=130)
        if st.button("记录小队分享播报", width="stretch", disabled=not team_share):
            record_share_event(
                user_name=st.session_state.get("user_name", "红色学习者"),
                unit_name=st.session_state.get("unit_name", "体验组"),
                activity_id=current_activity_id,
                activity_name=activity.get("name", "长征活动"),
                share_text=team_share,
                team_id=st.session_state.get("current_team_id", ""),
                team_name=st.session_state.get("current_team_name", ""),
                branch_name=st.session_state.get("current_branch_name", ""),
            )
            st.success("小队战绩已写入实时播报流。")

    render_section("实时战绩播报流", "集中呈现近期的小队协作贡献与战绩播报记录。")
    live_rows = build_live_battle_rows(hours=48, limit=12)
    if live_rows:
        st.dataframe(pd.DataFrame(live_rows), width="stretch", hide_index=True)
    else:
        st.info("实时战绩播报暂未形成。")
