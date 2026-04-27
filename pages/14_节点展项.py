"""单节点展项页。"""

from __future__ import annotations

import streamlit as st

from content_store import get_chapter_for_node, get_route_chapters
from game import get_route_node
from node_detail import render_node_detail
from quiz_engine import create_story_state, set_story_checkpoint
from streamlit_ui import (
    build_current_provider_config,
    render_curatorial_note,
    render_feature_ribbon,
    render_hero,
    render_section,
    render_top_nav,
    setup_page,
)


def _all_route_nodes() -> list[dict]:
    """按主线顺序读取全部节点。"""
    return [node for chapter in get_route_chapters() for node in chapter.get("nodes", [])]


def _set_node_and_rerun(node_id: str) -> None:
    """切换当前展项。"""
    if node_id:
        st.session_state["selected_node_id"] = node_id
    st.rerun()


setup_page("节点展项", icon="🎯")
render_top_nav("节点展项")

nodes = _all_route_nodes()
node_ids = [node.get("id", "") for node in nodes if node.get("id")]
selected_node_id = st.session_state.get("selected_node_id", "")

if selected_node_id not in node_ids:
    render_hero(
        title="选择一个节点展项",
        subtitle="请先从长征路线选关大厅选择一站，再进入该节点的独立展项页面。",
        badges=["节点展项", "讲解词", "互动入口"],
    )
    render_curatorial_note(
        title="从选关大厅进入",
        body="每一站都有独立展项。可先返回长征路线，选择想进入的篇章和节点，再展开这一站的讲解与互动任务。",
        label="展项入口",
    )
    if st.button("返回长征路线选关", width="stretch", type="primary"):
        st.switch_page("pages/3_长征路线.py")
    st.stop()

selected_node = get_route_node(selected_node_id) or {}
selected_index = node_ids.index(selected_node_id)
chapter = get_chapter_for_node(selected_node)
provider_config = build_current_provider_config()

render_hero(
    title=selected_node.get("title", "节点展项"),
    subtitle=(
        f"{chapter.get('badge', '主线篇章')} · {chapter.get('title', '长征路线')} | "
        f"{selected_node.get('date', '长征途中')} · {selected_node.get('place', '行军沿线')}"
    ),
    badges=["独立展项", "图文讲解", "语音导览", "互动闯关"],
)

nav_left, nav_mid, nav_right = st.columns([1, 1.2, 1])
with nav_left:
    if selected_index > 0:
        if st.button(f"上一站：{nodes[selected_index - 1].get('title', '')}", width="stretch"):
            _set_node_and_rerun(nodes[selected_index - 1].get("id", ""))
    else:
        st.button("已到起点", width="stretch", disabled=True)
with nav_mid:
    if st.button("返回长征路线选关大厅", width="stretch"):
        st.switch_page("pages/3_长征路线.py")
with nav_right:
    if selected_index + 1 < len(nodes):
        if st.button(f"下一站：{nodes[selected_index + 1].get('title', '')}", width="stretch", type="primary"):
            _set_node_and_rerun(nodes[selected_index + 1].get("id", ""))
    else:
        st.button("已到终点", width="stretch", disabled=True)

render_feature_ribbon(
    [
        {
            "label": "当前篇章",
            "title": chapter.get("title", "长征主线"),
            "desc": chapter.get("subtitle", "沿着长征主线继续浏览。"),
        },
        {
            "label": "展项位置",
            "title": f"第 {selected_index + 1} 站 / 共 {len(nodes)} 站",
            "desc": "当前展项聚焦这一站的历史情境、关键人物、行动经过与学习任务。",
        },
        {
            "label": "学习方式",
            "title": "先看展项，再进互动",
            "desc": "先通过图文讲解理解历史情境，再进入剧情答题完成本关挑战。",
        },
    ]
)

render_node_detail(
    node=selected_node,
    provider_config=provider_config,
    audience=st.session_state.get("selected_role_name", "大学生"),
    key_prefix=f"node-exhibit::{selected_node_id}",
)

render_section("继续体验", "完成本展项阅读后，可进入本节点互动题，也可以回到选关大厅选择其他节点。")
action_left, action_right = st.columns(2)
with action_left:
    if st.button("进入本节点互动题", width="stretch", type="primary"):
        story_state = create_story_state(
            role_id=st.session_state.get("selected_role_id", "scout"),
            activity_id=st.session_state.get("current_activity_id", ""),
            start_node_id=selected_node_id,
        )
        st.session_state["story_state"] = set_story_checkpoint(story_state, selected_node_id)
        st.switch_page("pages/4_剧情答题.py")
with action_right:
    if st.button("进入知识百问", width="stretch"):
        st.switch_page("pages/5_知识库.py")
