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
    subtitle="活动中心承载知识竞赛、党史学习日、研学任务等组织化场景，支持活动链接、二维码、红军小队协作、支部对抗与实时战绩播报。",
    badges=["活动模板", "红军小队", "支部对抗", "实时战绩"],
)

activities = list_activities()
activity_ids = [item["activity_id"] for item in activities]
current_activity_id = st.session_state.get("current_activity_id", activity_ids[0] if activity_ids else "")
if current_activity_id not in activity_ids and activity_ids:
    current_activity_id = activity_ids[0]

render_section("活动模板总览", "当前版本已提供知识竞赛、党史学习日和红色研学任务等模板，支持个人参与与小队协同。")
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
    render_section("活动信息", "活动可以作为班级竞赛、党史学习日、研学任务或支部对抗的组织单元进行分发。")
    st.markdown(f"## {activity.get('name', '')}")
    st.write(activity.get("description", ""))
    st.caption(f"活动模式：{activity.get('mode', '')}")
    st.caption(f"活动时长：{activity.get('time_range', '')}")
    st.caption(f"活动状态：{activity.get('status', '')}")
    st.caption(f"覆盖节点：{len(activity.get('node_scope', []))} 个")
    st.caption(f"支持红军小队：{'是' if activity.get('support_team_mode') else '否'}")
    st.caption(f"支持支部对抗：{'是' if activity.get('support_branch_pk') else '否'}")
    st.caption(f"当前参与身份：{st.session_state.get('user_name', '红色学习者')} | {st.session_state.get('unit_name', '体验组')}")
    if current_team:
        st.success(
            f"当前已加入小队：{current_team.get('team_name', '')} | "
            f"{current_team.get('branch_name', '')} | 队员 {len(current_team.get('members', []))} 人"
        )

    button_cols = st.columns(4)
    with button_cols[0]:
        if st.button("选择角色", width="stretch"):
            st.switch_page("pages/2_角色选择.py")
    with button_cols[1]:
        if st.button("进入路线", width="stretch"):
            st.switch_page("pages/3_长征路线.py")
    with button_cols[2]:
        if st.button("开始答题", width="stretch", type="primary"):
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
        st.info("当前已保留活动分享链接，可继续通过链接组织访问。")

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

    render_section("活动个人榜预览", "适合课堂竞赛和现场展示，便于快速看到本活动中的个人表现。")
    ranking = get_activity_leaderboard(current_activity_id, limit=8)
    if ranking:
        st.dataframe(pd.DataFrame(ranking), width="stretch", hide_index=True)
    else:
        st.info("当前活动还没有成绩记录。完成一次剧情答题后，这里将自动出现活动排行榜。")

    render_section("班级/单位榜预览", "可直接展示班级、单位或学习小组的聚合成绩。")
    unit_rows = get_unit_leaderboard(current_activity_id, limit=8)
    if unit_rows:
        st.dataframe(pd.DataFrame(unit_rows), width="stretch", hide_index=True)
    else:
        st.info("当前活动还没有班级/单位排行数据。")

with team_tab:
    render_section("红军小队协作", "支持创建红军小队、加入协作队伍，并把个人答题贡献自动汇总到小队总分。")
    if not activity.get("support_team_mode", True):
        st.warning("当前活动未开启红军小队协作，可在内容运营页面开启后使用。")
    else:
        current_team = _sync_current_team(current_activity_id)
        if current_team:
            st.success(
                f"你当前所在小队：{current_team.get('team_name', '')} | "
                f"{current_team.get('branch_name', '')} | 口号：{current_team.get('slogan', '暂无')}"
            )
            team_left, team_right = st.columns([1.05, 1])
            with team_left:
                st.markdown("### 当前小队成员贡献")
                member_rows = build_team_member_summary(current_team.get("team_id", ""))
                if member_rows:
                    st.dataframe(pd.DataFrame(member_rows), width="stretch", hide_index=True)
            with team_right:
                st.markdown("### 当前小队战力")
                st.metric("小队总分", current_team.get("total_score", 0))
                st.metric("小队粮草", current_team.get("total_grain", 0))
                st.metric("累计作答", current_team.get("answered_count", 0))
                st.metric("正确率", f"{round((current_team.get('correct_count', 0) / max(current_team.get('answered_count', 1), 1)) * 100, 1)}%")
                if st.button("退出当前小队", width="stretch"):
                    leave_team(current_team.get("team_id", ""), st.session_state.get("user_name", "红色学习者"))
                    _sync_current_team(current_activity_id)
                    st.success("已退出当前小队。")
                    st.rerun()

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
                st.info("当前活动还没有创建小队。")

        render_section("小队排行榜", "多名队员分别完成节点作答后，会自动合并为队伍协作成绩。")
        team_rows = get_team_leaderboard(current_activity_id, limit=10)
        if team_rows:
            st.dataframe(pd.DataFrame(team_rows), width="stretch", hide_index=True)
        else:
            st.info("当前活动还没有小队战绩。")

with pk_tab:
    render_section("支部对抗赛", "系统按支部或单位汇总各小队成绩，形成组织化学习对抗榜单。")
    if not activity.get("support_branch_pk", True):
        st.warning("当前活动未开启支部对抗模式，可在内容运营页面开启后使用。")
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
            st.info("当前活动还没有支部 PK 数据。先创建小队并完成答题后即可形成对抗榜。")

with share_tab:
    render_section("实时战绩分享", "支持生成个人战绩分享文案和小队播报文案，适合活动群、班级群和现场主持串场。")
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

    render_section("实时战绩播报流", "这里展示最近的小队协作贡献和战绩分享事件，可直接作为主持口播素材或活动播报内容。")
    live_rows = build_live_battle_rows(hours=48, limit=12)
    if live_rows:
        st.dataframe(pd.DataFrame(live_rows), width="stretch", hide_index=True)
    else:
        st.info("当前还没有可展示的实时战绩播报。")
