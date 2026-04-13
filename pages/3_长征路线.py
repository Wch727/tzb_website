"""长征路线页。"""

from __future__ import annotations

import streamlit as st

from activity_manager import get_activity
from game import get_route_node, load_route_nodes
from node_detail import render_node_detail
from quiz_engine import create_story_state, set_story_checkpoint
from streamlit_ui import build_current_provider_config, render_hero, render_section, render_top_nav, setup_page


setup_page("长征路线", icon="🗺️")
render_top_nav("长征路线")
render_hero(
    title="长征主线剧情关卡",
    subtitle="按时间线与关键转折组织主线关卡，用户可先浏览节点，再从任一节点进入剧情答题。",
    badges=["时间线关卡", "节点导览", "剧情入口"],
)

provider_config = build_current_provider_config()
all_nodes = load_route_nodes()
activity = get_activity(st.session_state.get("current_activity_id", ""))
node_scope = activity.get("node_scope", []) if activity else []
route_nodes = [node for node in all_nodes if not node_scope or node.get("id") in node_scope]

render_section("路线总览", "从瑞金出发到会宁会师，关卡按照历史时间线顺序组织。点击节点即可查看详情并进入剧情答题。")

timeline_cols = st.columns(4)
for index, node in enumerate(route_nodes):
    with timeline_cols[index % 4]:
        st.markdown(f"**{index + 1}. {node.get('title', '')}**")
        st.caption(f"{node.get('date', '')} · {node.get('place', '')}")
        st.write(node.get("summary", "")[:70] + ("..." if len(node.get("summary", "")) > 70 else ""))
        if st.button("查看详情", key=f"route_node_{node.get('id')}", use_container_width=True):
            st.session_state["selected_node_id"] = node.get("id", "")
            st.rerun()

node_ids = [node["id"] for node in route_nodes]
selected_node_id = st.session_state.get("selected_node_id", node_ids[0] if node_ids else "")
if selected_node_id not in node_ids and node_ids:
    selected_node_id = node_ids[0]
selected_node_id = st.selectbox(
    "当前查看节点",
    node_ids,
    index=node_ids.index(selected_node_id) if selected_node_id in node_ids else 0,
    format_func=lambda node_id: next((node["title"] for node in route_nodes if node["id"] == node_id), node_id),
)
st.session_state["selected_node_id"] = selected_node_id

selected_node = get_route_node(selected_node_id)
if selected_node:
    render_node_detail(
        node=selected_node,
        provider_config=provider_config,
        audience=st.session_state.get("selected_role_name", "侦察兵"),
        key_prefix="route-page-node",
    )
    col1, col2 = st.columns(2)
    with col1:
        if st.button("从该节点开始剧情答题", use_container_width=True, type="primary"):
            story_state = create_story_state(
                role_id=st.session_state.get("selected_role_id", "scout"),
                activity_id=st.session_state.get("current_activity_id", ""),
                start_node_id=selected_node_id,
            )
            st.session_state["story_state"] = set_story_checkpoint(story_state, selected_node_id)
            st.switch_page("pages/4_剧情答题.py")
    with col2:
        if st.button("前往知识库延伸学习", use_container_width=True):
            st.switch_page("pages/5_知识库.py")

