"""长征路线页。"""

from __future__ import annotations

import streamlit as st

from activity_manager import get_activity
from content_store import get_route_chapters
from game import get_route_node
from media import render_node_image
from node_detail import render_node_detail
from quiz_engine import create_story_state, set_story_checkpoint
from streamlit_ui import build_current_provider_config, render_hero, render_section, render_top_nav, setup_page


setup_page("长征路线", icon="🗺️")
render_top_nav("长征路线")

render_hero(
    title="长征路线导览",
    subtitle="以篇章化方式组织长征主线节点。用户可按阶段浏览，也可从任意节点进入展项详情与互动答题。",
    badges=["四大篇章", "节点导览", "展项详情", "互动入口"],
)

provider_config = build_current_provider_config()
activity = get_activity(st.session_state.get("current_activity_id", ""))
allowed_node_ids = set(activity.get("node_scope", []) if activity else [])
chapters = get_route_chapters()
if allowed_node_ids:
    filtered_chapters = []
    for chapter in chapters:
        nodes = [node for node in chapter.get("nodes", []) if node.get("id") in allowed_node_ids]
        if nodes:
            chapter_copy = chapter.copy()
            chapter_copy["nodes"] = nodes
            filtered_chapters.append(chapter_copy)
    chapters = filtered_chapters

chapter_ids = [item.get("id", "") for item in chapters]
selected_chapter_id = st.session_state.get("selected_chapter_id", chapter_ids[0] if chapter_ids else "")
if selected_chapter_id not in chapter_ids and chapter_ids:
    selected_chapter_id = chapter_ids[0]
st.session_state["selected_chapter_id"] = selected_chapter_id

render_section("征程篇章", "不再以单一列表罗列节点，而是按历史阶段拆成多个展区，形成连续浏览的路线感。")
chapter_nav_cols = st.columns(max(1, len(chapters)))
for index, chapter in enumerate(chapters):
    with chapter_nav_cols[index]:
        if st.button(chapter.get("title", ""), key=f"chapter_nav_{chapter.get('id')}", use_container_width=True):
            st.session_state["selected_chapter_id"] = chapter.get("id", "")
            st.rerun()

selected_chapter = next((item for item in chapters if item.get("id") == st.session_state.get("selected_chapter_id")), chapters[0] if chapters else {})
for chapter in chapters:
    render_section(chapter.get("title", "路线篇章"), chapter.get("subtitle", ""))
    node_cols = st.columns(3)
    for index, node in enumerate(chapter.get("nodes", [])):
        with node_cols[index % 3]:
            render_node_image(node, caption=node.get("place", ""))
            st.markdown(f"#### {node.get('title', '')}")
            st.caption(f"{node.get('date', '')} · {node.get('place', '')}")
            st.write(node.get("summary", ""))
            if st.button("查看详情", key=f"chapter_node_{node.get('id')}", use_container_width=True):
                st.session_state["selected_chapter_id"] = chapter.get("id", "")
                st.session_state["selected_node_id"] = node.get("id", "")
                st.rerun()

all_nodes = [node for chapter in chapters for node in chapter.get("nodes", [])]
node_ids = [node.get("id", "") for node in all_nodes]
selected_node_id = st.session_state.get("selected_node_id", node_ids[0] if node_ids else "")
if selected_node_id not in node_ids and node_ids:
    selected_node_id = node_ids[0]
st.session_state["selected_node_id"] = selected_node_id

selected_node = get_route_node(selected_node_id)
if selected_node:
    render_section(
        "节点展项详情",
        f"当前位于“{selected_chapter.get('title', '主线篇章')}”篇章。每个节点都以小型线上展项的方式呈现，默认包含长文本、讲解与互动入口。",
    )
    render_node_detail(
        node=selected_node,
        provider_config=provider_config,
        audience=st.session_state.get("selected_role_name", "大学生"),
        key_prefix="route-page-node",
    )
    action_left, action_right = st.columns(2)
    with action_left:
        if st.button("从该节点进入互动题", use_container_width=True, type="primary"):
            story_state = create_story_state(
                role_id=st.session_state.get("selected_role_id", "scout"),
                activity_id=st.session_state.get("current_activity_id", ""),
                start_node_id=selected_node_id,
            )
            st.session_state["story_state"] = set_story_checkpoint(story_state, selected_node_id)
            st.switch_page("pages/4_剧情答题.py")
    with action_right:
        if st.button("前往知识百问", use_container_width=True):
            st.switch_page("pages/5_知识库.py")
