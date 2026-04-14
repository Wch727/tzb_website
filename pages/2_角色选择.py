"""角色选择页。"""

from __future__ import annotations

import streamlit as st

from activity_manager import get_activity, list_activities
from game import load_route_nodes
from role_system import get_role, list_roles
from streamlit_ui import render_cards, render_hero, render_section, render_top_nav, setup_page


setup_page("角色选择", icon="🪖")
render_top_nav("角色选择")
render_hero(
    title="角色选择",
    subtitle="选择你的长征身份后，再进入主线剧情关卡。不同角色会在任务提示、历史导入和奖励加成上体现差异。",
    badges=["侦察兵", "卫生员", "通讯员", "角色任务"],
)

current_activity = get_activity(st.session_state.get("current_activity_id", ""))
if current_activity:
    st.info(f"当前活动：{current_activity.get('name', '')}｜模式：{current_activity.get('mode', '')}")
else:
    default_activity = list_activities()[0]
    st.session_state["current_activity_id"] = default_activity.get("activity_id", "")
    current_activity = default_activity

render_section("选择你的红军身份", "角色机制是剧情答题的重要入口。当前版本已实现角色差异化任务提示、节点推荐与奖励加成。")
roles = list_roles()
role_cards = [
    {
        "label": item.get("title", ""),
        "title": item.get("name", ""),
        "desc": f"{item.get('tagline', '')} {item.get('bonus_text', '')}",
    }
    for item in roles
]
render_cards(role_cards)

identity_left, identity_right = st.columns(2)
with identity_left:
    st.session_state["user_name"] = st.text_input(
        "参与者姓名",
        value=st.session_state.get("user_name", "红色学习者"),
        help="将用于排行榜、战绩展示和电子证书。",
    )
with identity_right:
    st.session_state["unit_name"] = st.text_input(
        "班级 / 单位 / 小组",
        value=st.session_state.get("unit_name", "体验组"),
        help="用于活动排行和单位排行展示。",
    )

selected_role_id = st.session_state.get("selected_role_id", "scout")
selected_role_id = st.radio(
    "请选择角色",
    [item["role_id"] for item in roles],
    horizontal=True,
    index=[item["role_id"] for item in roles].index(selected_role_id)
    if selected_role_id in [item["role_id"] for item in roles]
    else 0,
    format_func=lambda item: get_role(item).get("name", item),
)

selected_role = get_role(selected_role_id)
st.session_state["selected_role_id"] = selected_role_id
st.session_state["selected_role_name"] = selected_role.get("name", "侦察兵")

left, right = st.columns([1.15, 1])
with left:
    st.markdown(f"## {selected_role.get('name', '')}")
    st.write(selected_role.get("tagline", ""))
    st.markdown(f"**任务重点：** {selected_role.get('mission_focus', '')}")
    st.markdown(f"**专属提示：** {selected_role.get('special_hint', '')}")
    st.markdown(f"**成长加成：** {selected_role.get('bonus_text', '')}")
    if selected_role.get("recommended_nodes"):
        st.markdown("**推荐优先体验节点：**")
        for node_id in selected_role.get("recommended_nodes", []):
            st.markdown(
                f"- {next((node.get('title', node_id) for node in load_route_nodes() if node.get('id') == node_id), node_id)}"
            )

with right:
    st.markdown("### 当前活动任务")
    st.write(current_activity.get("description", ""))
    st.caption(f"活动模式：{current_activity.get('mode', '')}")
    st.caption(f"活动时长：{current_activity.get('time_range', '')}")
    st.caption(f"节点范围：{len(current_activity.get('node_scope', []))} 个核心节点")
    st.caption(f"当前参与身份：{st.session_state.get('user_name', '红色学习者')} · {st.session_state.get('unit_name', '体验组')}")

btn1, btn2 = st.columns(2)
with btn1:
    if st.button("进入长征路线", use_container_width=True, type="primary"):
        st.switch_page("pages/3_长征路线.py")
with btn2:
    if st.button("直接开始剧情答题", use_container_width=True):
        st.switch_page("pages/4_剧情答题.py")
