"""长征路线页。"""

from __future__ import annotations

import streamlit as st

from activity_manager import get_activity
from content_store import get_route_chapters
from game import get_route_node
from media import render_node_image
from node_detail import render_node_detail
from quiz_engine import create_story_state, set_story_checkpoint
from streamlit_ui import (
    build_current_provider_config,
    render_chapter_overview_cards,
    render_curatorial_note,
    render_feature_ribbon,
    render_gallery_frame,
    render_hero,
    render_ledger_cards,
    render_section,
    render_top_nav,
    setup_page,
)


setup_page("长征路线", icon="🗺️")
render_top_nav("长征路线")

render_hero(
    title="长征路线导览",
    subtitle="以篇章化方式组织长征主线节点。用户可按阶段进入各个展区，再从具体节点展开图文阅读、讲解与互动答题。",
    badges=["四大篇章", "节点导览", "展项详情", "互动入口"],
)

provider_config = build_current_provider_config()
activity = get_activity(st.session_state.get("current_activity_id", ""))
allowed_node_ids = set(activity.get("node_scope", []) if activity else [])
chapters = get_route_chapters()

chapter_ids = [item.get("id", "") for item in chapters]
selected_chapter_id = st.session_state.get("selected_chapter_id", chapter_ids[0] if chapter_ids else "")
if selected_chapter_id not in chapter_ids and chapter_ids:
    selected_chapter_id = chapter_ids[0]
st.session_state["selected_chapter_id"] = selected_chapter_id

selected_chapter = next((item for item in chapters if item.get("id") == st.session_state.get("selected_chapter_id")), chapters[0] if chapters else {})

render_section("征程篇章", "四大篇章共同构成长征主线，各篇章分别呈现不同阶段的任务、转折与推进方向。")
render_chapter_overview_cards(chapters, active_id=selected_chapter.get("id", ""))
render_feature_ribbon(
    [
        {
            "label": selected_chapter.get("badge", "篇章"),
            "title": selected_chapter.get("title", "长征路线"),
            "desc": selected_chapter.get("subtitle", "按篇章进入主线节点，逐步理解长征的战略变化与历史意义。"),
        },
        {
            "label": "阅读方式",
            "title": "先篇章后节点",
            "desc": "先把握本篇章的任务和转折，再进入具体节点，避免在碎片信息中来回跳转。",
        },
        {
            "label": "互动方式",
            "title": "看展项再答题",
            "desc": "每个节点既可展开图文阅读，也可进入互动题，把导览体验直接转化成学习反馈。",
        },
    ]
)

chapter_nav_cols = st.columns(max(1, len(chapters)))
for index, chapter in enumerate(chapters):
    with chapter_nav_cols[index]:
        if st.button(chapter.get("title", ""), key=f"chapter_nav_{chapter.get('id')}", width="stretch"):
            st.session_state["selected_chapter_id"] = chapter.get("id", "")
            st.rerun()

render_gallery_frame("所在篇章", "围绕本篇章的关键节点、时间与地点展开浏览，再进入具体历史情境。")
chapter_left, chapter_right = st.columns([1.1, 0.95])
with chapter_left:
    render_curatorial_note(
        title=f"{selected_chapter.get('badge', '篇章')} · {selected_chapter.get('title', '长征主线')}",
        body=selected_chapter.get("subtitle", ""),
    )
    render_ledger_cards(
        [
            {
                "label": f"节点 {index + 1}",
                "title": node.get("title", ""),
                "desc": f"{node.get('date', '')} · {node.get('place', '')}",
            }
            for index, node in enumerate(selected_chapter.get("nodes", []))
        ]
    )
with chapter_right:
    if selected_chapter.get("nodes"):
        lead_node = selected_chapter["nodes"][0]
        render_node_image(
            lead_node,
            caption=f"{selected_chapter.get('title', '')}篇章入口展项",
        )
        st.markdown(
            f"<div class='small-muted'>本篇章可先从 {lead_node.get('title', '')} 进入，由此把握这一阶段的历史任务与转折意义。</div>",
            unsafe_allow_html=True,
        )

render_section("本篇章节点", "先看本篇章的关键节点，再进入具体展项，能够更清晰地理解这一阶段的历史变化。")
node_cols = st.columns(2)
for index, node in enumerate(selected_chapter.get("nodes", [])):
    with node_cols[index % 2]:
        render_node_image(node, caption=node.get("place", ""))
        st.markdown(f"#### {node.get('title', '')}")
        st.caption(f"{node.get('date', '')} · {node.get('place', '')}")
        st.write(node.get("summary", ""))
        st.markdown(f"<div class='small-muted'>{node.get('significance', '')[:110]}...</div>", unsafe_allow_html=True)
        if node.get("id") in allowed_node_ids:
            st.markdown("<div class='small-muted'><strong>互动节点：</strong>由此进入本段征程的闯关学习。</div>", unsafe_allow_html=True)
        action_left, action_right = st.columns(2)
        with action_left:
            if st.button("查看详情", key=f"chapter_node_{node.get('id')}", width="stretch"):
                st.session_state["selected_chapter_id"] = selected_chapter.get("id", "")
                st.session_state["selected_node_id"] = node.get("id", "")
                st.rerun()
        with action_right:
            if st.button("进入互动", key=f"chapter_quiz_{node.get('id')}", width="stretch"):
                story_state = create_story_state(
                    role_id=st.session_state.get("selected_role_id", "scout"),
                    activity_id=st.session_state.get("current_activity_id", ""),
                    start_node_id=node.get("id", ""),
                )
                st.session_state["story_state"] = set_story_checkpoint(story_state, node.get("id", ""))
                st.switch_page("pages/4_剧情答题.py")

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
        f"以下展项位于“{selected_chapter.get('title', '主线篇章')}”篇章之中，可继续查看讲解、史料依据与互动学习内容。",
    )
    render_node_detail(
        node=selected_node,
        provider_config=provider_config,
        audience=st.session_state.get("selected_role_name", "大学生"),
        key_prefix="route-page-node",
    )
    action_left, action_right = st.columns(2)
    with action_left:
        if st.button("从该节点进入互动题", width="stretch", type="primary"):
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
