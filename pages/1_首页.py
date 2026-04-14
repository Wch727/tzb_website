"""产品首页。"""

from __future__ import annotations

import streamlit as st

from content_store import get_route_chapters
from media import render_node_image
from rag import get_rag_status
from sample_content import load_home_sample_content
from streamlit_ui import (
    render_chapter_overview_cards,
    render_curatorial_note,
    render_detail_panels,
    render_hero,
    render_ledger_cards,
    render_metrics,
    render_section,
    render_top_nav,
    setup_page,
)
from utils import get_visible_user_models


def _jump_to_node(node_id: str) -> None:
    """记录用户想查看的节点并跳转。"""
    st.session_state["selected_node_id"] = node_id
    st.switch_page("pages/3_长征路线.py")


setup_page("首页", icon="🏛️")
render_top_nav("首页")

status = get_rag_status()
models = get_visible_user_models()
sample = load_home_sample_content()
chapters = get_route_chapters()
total_nodes = sum(len(item.get("nodes", [])) for item in chapters)

render_hero(
    title="《长征史》交互式导览与闯关学习系统",
    subtitle=(
        "以长征主线为展陈骨架，把路线导览、知识百问、讲解生成与互动答题组织成一个可浏览、可学习、可参与的线上主题展。"
    ),
    badges=["主线导览", "展项浏览", "知识百问", "互动闯关", "图文音一体"],
)

intro_left, intro_right = st.columns([1.2, 1])
with intro_left:
    render_node_image(
        {
            "title": "长征路线总览",
            "image": sample.get("hero_route_map", "assets/images/changzheng_route_map.jpg"),
            "place": "从瑞金出发到会宁会师的长征路线",
            "type": "route",
            "image_key": "changzheng_route_map",
        },
        caption="长征路线总览",
    )
with intro_right:
    render_curatorial_note(
        title="主展导语",
        body=(
            "本网站不以零散知识点为主，而是把长征放回完整历史进程之中。"
            "用户将沿着出发、转折、突破与会师四个篇章进入展线，在每个节点中依次看到历史背景、行动过程、战略意义、人物线索与互动学习入口。"
        ),
    )
    action_left, action_right, action_more = st.columns([1, 1, 1])
    with action_left:
        if st.button("开始长征导览", width="stretch", type="primary"):
            st.switch_page("pages/3_长征路线.py")
    with action_right:
        if st.button("进入互动闯关", width="stretch"):
            st.switch_page("pages/4_剧情答题.py")
    with action_more:
        if st.button("进入导览速览", width="stretch"):
            st.switch_page("pages/10_测试体验.py")

render_metrics(
    [
        {"label": "主线节点", "value": total_nodes},
        {"label": "知识切片", "value": status.get("chunk_count", 0)},
        {"label": "开放模型", "value": len(models)},
        {"label": "展陈篇章", "value": len(chapters)},
    ]
)

render_section("主展结构", "借鉴数字展的章节化组织方式，先看篇章，再进入展项，帮助用户形成更稳定的学习路线。")
render_chapter_overview_cards(chapters)

render_detail_panels(
    [
        {
            "title": "路线导览",
            "desc": "以长征时间线为骨架，把节点、人物、事件与精神专题组织成连续浏览的征程体验。",
        },
        {
            "title": "知识百问",
            "desc": "从推荐问题、节点相关问题与主题问答切入，把历史阅读与问题学习结合起来。",
        },
        {
            "title": "互动学习",
            "desc": "每个关键节点都可继续进入互动答题、讲解生成与学习延展，形成以题带学的闭环。",
        },
    ]
)

render_section("重点展项", "优先从最能代表长征主线与历史转折的节点进入，建立整条征程的基本认识。")
featured_nodes = sample.get("featured_nodes", [])
feature_cols = st.columns(3)
for index, node in enumerate(featured_nodes):
    with feature_cols[index % 3]:
        render_node_image(node, caption=node.get("image_caption", "") or node.get("place", ""))
        st.markdown(f"#### {node.get('title', '')}")
        st.caption(f"{node.get('date', '')} · {node.get('place', '')}")
        st.write(node.get("summary", ""))
        st.markdown(f"<div class='small-muted'>{node.get('significance', '')[:80]}...</div>", unsafe_allow_html=True)
        if st.button("进入展项", key=f"home_featured_{node.get('id')}", width="stretch"):
            _jump_to_node(node.get("id", ""))

render_section("长征路线总览", "四个篇章共同构成主展展线。每个篇章既有清晰的历史任务，也有代表性的关键展项。")
chapter_cols = st.columns(4)
for index, chapter in enumerate(chapters):
    with chapter_cols[index % 4]:
        render_curatorial_note(
            title=chapter.get("title", ""),
            body=chapter.get("subtitle", ""),
            label=chapter.get("badge", "篇章"),
        )
        for node in chapter.get("nodes", [])[:3]:
            st.markdown(f"- **{node.get('title', '')}**")
        if st.button("进入本篇章", key=f"home_chapter_{chapter.get('id')}", width="stretch"):
            st.session_state["selected_chapter_id"] = chapter.get("id", "")
            st.switch_page("pages/3_长征路线.py")

route_left, route_right = st.columns([1.15, 0.95])
with route_left:
    render_ledger_cards(
        [
            {
                "label": chapter.get("badge", "篇章"),
                "title": chapter.get("title", ""),
                "desc": " · ".join(node.get("title", "") for node in chapter.get("nodes", [])[:4]),
            }
            for chapter in chapters
        ]
    )
with route_right:
    render_curatorial_note(
        title="推荐参观方式",
        body="第一次进入可先沿四大篇章顺序浏览；若偏向互动学习，可先进入剧情闯关，再回到节点详情查看完整展项说明。",
        label="参观建议",
    )
    st.markdown("### 推荐学习路线")
    for item in sample.get("recommended_learning_paths", [])[:4]:
        st.markdown(f"- {item}")
    st.markdown("### 今日推荐路线")
    for item in sample.get("recommended_route", [])[:4]:
        st.markdown(f"- {item}")

render_section("重要人物", "人物专题不是附属内容，而是理解长征决策、组织、战斗和精神内核的重要入口。")
figure_cols = st.columns(3)
for index, item in enumerate(sample.get("figure_cards", [])[:6]):
    with figure_cols[index % 3]:
        render_node_image(item, caption=item.get("role", "重要人物"))
        st.markdown(f"#### {item.get('title', '')}")
        st.caption(item.get("role", "重要人物"))
        st.write(item.get("summary", ""))
        st.markdown(f"<div class='small-muted'>{item.get('significance', '')[:88]}...</div>", unsafe_allow_html=True)

render_section("长征精神专题", "把路线、事件与精神内涵联系起来，形成更完整的学习纵深。")
spirit_cols = st.columns(3)
for index, item in enumerate(sample.get("spirit_topics", [])[:6]):
    with spirit_cols[index % 3]:
        st.markdown(f"### {item.get('title', '')}")
        st.write(item.get("summary", ""))

render_section("推荐学习内容", "首页不仅是入口页，也承担导学作用。通过推荐问题、示范讲解与阶段路线，用户可以快速找到合适的进入方式。")
tab1, tab2, tab3, tab4 = st.tabs(["推荐问题", "示范讲解", "推荐学习路线", "导览速览"])
with tab1:
    render_curatorial_note(
        title="长征百问",
        body="问题式浏览适合第一次进入主题展的用户。先从核心问题开始，再逐步进入对应节点、人物与精神专题。",
        label="导学入口",
    )
    for question in sample.get("example_questions", [])[:8]:
        st.markdown(f"- {question}")
with tab2:
    render_curatorial_note(
        title="示范讲解",
        body="讲解稿以节点史实为中心组织，强调背景、经过和意义三层结构，便于课堂讲述与展项说明。",
        label="讲解样例",
    )
    st.write(sample.get("example_guide_script", ""))
with tab3:
    render_curatorial_note(
        title="分阶段学习路线",
        body="如果希望快速形成主线认知，可先从每个篇章中最具代表性的节点依次展开阅读与互动学习。",
        label="学习路线",
    )
    for item in sample.get("recommended_nodes_by_stage", []):
        st.markdown(f"**{item.get('title', '')}**")
        st.caption(item.get("subtitle", ""))
        for node in item.get("nodes", [])[:3]:
            st.markdown(f"- {node.get('title', '')}")
with tab4:
    render_curatorial_note(
        title="导览速览",
        body="导览速览适合课堂展示、答辩讲述和第一次现场介绍，能够在较短时间内浏览主线、展项、问答与互动功能。",
        label="快速入口",
    )
    if st.button("进入导览速览页", key="home_try_page", width="stretch"):
        st.switch_page("pages/10_测试体验.py")
