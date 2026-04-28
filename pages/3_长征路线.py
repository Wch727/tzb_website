"""长征路线页。"""

from __future__ import annotations

import streamlit as st

from activity_manager import get_activity
from content_store import get_route_chapters
from media import render_node_image
from streamlit_ui import (
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
    subtitle="以篇章化方式组织长征主线节点。观众可按阶段进入各个展区，再从具体节点展开图文阅读、讲解与互动闯关。",
    badges=["四大篇章", "节点导览", "展项详情", "互动入口"],
)

activity = get_activity(st.session_state.get("current_activity_id", ""))
allowed_node_ids = set(activity.get("node_scope", []) if activity else [])
chapters = get_route_chapters()

chapter_ids = [item.get("id", "") for item in chapters]
query_chapter_id = st.query_params.get("chapter_id", "")
if isinstance(query_chapter_id, list):
    query_chapter_id = query_chapter_id[0] if query_chapter_id else ""
selected_chapter_id = query_chapter_id or st.session_state.get("selected_chapter_id", chapter_ids[0] if chapter_ids else "")
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
            st.query_params["chapter_id"] = chapter.get("id", "")
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
        st.caption(f"本篇章可由 {lead_node.get('title', '')} 展开，以把握这一阶段的历史任务与转折意义。")

render_section("本篇章节点", "先看本篇章的关键节点，再进入具体展项，能够更清晰地理解这一阶段的历史变化。")
node_cols = st.columns(2)
for index, node in enumerate(selected_chapter.get("nodes", [])):
    with node_cols[index % 2]:
        render_node_image(node, caption=node.get("place", ""))
        st.markdown(f"#### {node.get('title', '')}")
        st.caption(f"{node.get('date', '')} · {node.get('place', '')}")
        st.write(node.get("summary", ""))
        st.caption(f"{node.get('significance', '')[:110]}...")
        if node.get("id") in allowed_node_ids:
            st.caption("互动节点：由此进入本段征程的闯关学习。")
        action_left, action_right = st.columns(2)
        with action_left:
            if st.button("进入展项", key=f"chapter_node_{node.get('id')}", width="stretch", type="primary"):
                st.session_state["selected_chapter_id"] = selected_chapter.get("id", "")
                st.session_state["selected_node_id"] = node.get("id", "")
                st.switch_page("pages/14_节点展项.py")
        with action_right:
            if st.button("进入闭卷闯关", key=f"chapter_quiz_{node.get('id')}", width="stretch"):
                st.session_state["selected_node_id"] = node.get("id", "")
                st.session_state["pending_game_start_node_id"] = node.get("id", "")
                st.session_state["story_state"] = {}
                st.session_state["game_active"] = False
                st.session_state["_scroll_to_top_once"] = True
                st.switch_page("pages/4_剧情答题.py")

render_feature_ribbon(
    [
        {
            "label": "选关大厅",
            "title": "先选一站，再进展项",
            "desc": "从这里选择一站进入，抵达节点后即可看到图文讲解、语音导览与互动闯关入口。",
        },
        {
            "label": "闯关建议",
            "title": "按顺序推进更完整",
            "desc": "第一次体验建议从出发与突围篇开始，沿着节点顺序进入，像选关游戏一样逐步解锁主线。",
        },
        {
            "label": "快速玩法",
            "title": "重点关卡可直达",
            "desc": "如果时间有限，可优先进入湘江战役、遵义会议、四渡赤水、飞夺泸定桥和会宁会师等关键节点。",
        },
    ]
)
