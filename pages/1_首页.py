"""产品首页。"""

from __future__ import annotations

import html

import streamlit as st

from content_store import get_chapter_for_node, get_route_chapters, get_route_node_data
from media import render_audio_player, render_digital_human, render_node_image
from rag import get_rag_status
from sample_content import load_home_sample_content
from streamlit_ui import (
    render_chapter_overview_cards,
    render_curatorial_note,
    render_detail_panels,
    render_exhibition_hero,
    render_feature_ribbon,
    render_formal_script,
    render_gallery_frame,
    render_ledger_cards,
    render_metrics,
    render_section,
    render_top_nav,
    setup_page,
)
from template_renderer import render_template, render_template_block
from utils import get_visible_user_models


def _jump_to_node(node_id: str) -> None:
    """记录用户想查看的节点并跳转。"""
    st.session_state["selected_node_id"] = node_id
    st.switch_page("pages/14_节点展项.py")


def _jump_to_figure(name: str) -> None:
    """记录用户想查看的人物并跳转。"""
    st.session_state["selected_figure_name"] = name
    st.switch_page("pages/13_人物专题.py")


def _extract_route_titles(route_text: str) -> list[str]:
    """从推荐路线文案中提取节点标题。"""
    body = route_text
    for separator in ["：", ":"]:
        if separator in body:
            body = body.split(separator, 1)[1]
            break
    return [item.strip() for item in body.split("→") if item.strip()]


def _jump_to_route(route_text: str) -> None:
    """按推荐路线进入对应篇章的选关大厅。"""
    for title in _extract_route_titles(route_text):
        node = get_route_node_data(title)
        if node:
            st.session_state["selected_chapter_id"] = get_chapter_for_node(node).get("id", "")
            st.session_state.pop("selected_node_id", None)
            st.switch_page("pages/3_长征路线.py")
            return


def _split_route_item(route_text: str, fallback_prefix: str) -> tuple[str, str, list[str]]:
    """拆分路线标题、说明与节点序列。"""
    title = fallback_prefix
    body = route_text.strip()
    for separator in ["：", ":"]:
        if separator in route_text:
            left, right = route_text.split(separator, 1)
            title = left.strip() or fallback_prefix
            body = right.strip() or route_text.strip()
            break
    nodes = _extract_route_titles(route_text)
    return title, body, nodes


def _jump_to_question(question: str) -> None:
    """把推荐问题带入知识百问页。"""
    st.session_state["pending_question"] = question
    st.switch_page("pages/5_知识库.py")


def _jump_to_chapter(chapter_id: str, node_id: str = "") -> None:
    """跳到指定篇章选关大厅。"""
    if chapter_id:
        st.session_state["selected_chapter_id"] = chapter_id
    st.session_state.pop("selected_node_id", None)
    st.switch_page("pages/3_长征路线.py")


def _render_game_page_link(label: str = "进入互动闯关") -> None:
    """渲染稳定的互动闯关直达入口。"""
    link_html = render_template(
        "home_action_link.html",
        label=html.escape(label),
        href="/剧情答题",
        class_name="home-action-link solid single",
    )
    st.markdown(
        render_template_block(
            "home_action_links.html",
            "home_exhibit.css",
            links_html=link_html,
            extra_class="single-action",
        ),
        unsafe_allow_html=True,
    )


def _render_home_action_links() -> None:
    """渲染首页首屏的三枚主入口按钮。"""
    items = [
        {"label": "开始长征导览", "href": "/长征路线", "class_name": "home-action-link primary"},
        {"label": "进入互动闯关", "href": "/剧情答题", "class_name": "home-action-link solid"},
        {"label": "进入导览速览", "href": "/测试体验", "class_name": "home-action-link outline"},
    ]
    links_html = "".join(
        render_template(
            "home_action_link.html",
            label=html.escape(item["label"]),
            href=html.escape(item["href"]),
            class_name=html.escape(item["class_name"]),
        )
        for item in items
    )
    st.markdown(
        render_template_block(
            "home_action_links.html",
            "home_exhibit.css",
            links_html=links_html,
            extra_class="",
        ),
        unsafe_allow_html=True,
    )


def _render_spirit_topics_grid(topics: list[dict]) -> None:
    """渲染等高对齐的长征精神专题卡片。"""
    cards_html = ""
    for item in topics[:6]:
        sources = item.get("official_sources", []) or []
        source_text = f"资料来源：{sources[0].get('publisher', '官方资料')}" if sources else "资料来源：官方资料"
        cards_html += render_template(
            "home_spirit_card.html",
            label="精神专题",
            title=html.escape(item.get("title", "")),
            summary=html.escape(item.get("summary", "")),
            source=html.escape(source_text),
        )
    if cards_html:
        st.markdown(
            render_template_block("home_spirit_grid.html", "home_exhibit.css", cards_html=cards_html),
            unsafe_allow_html=True,
        )


def _render_route_entry_card(title: str, body: str, nodes: list[str], label: str) -> None:
    """渲染路线入口卡。"""
    render_curatorial_note(title=title, body=body, label=label)
    if nodes:
        render_ledger_cards(
            [
                {
                    "label": f"{index + 1:02d}",
                    "title": node,
                    "desc": "沿线节点",
                }
                for index, node in enumerate(nodes[:4])
            ]
        )
    else:
        st.caption("沿着这条路线进入对应节点。")


def _render_route_overview_board(chapters: list[dict[str, object]]) -> None:
    """渲染首页路线总览展板。"""
    render_curatorial_note(
        title="沿着主线进入长征征程",
        body="先把握“出发与突围、转折与调整、巧渡与突破、北上会师”四大篇章，再从具体路线进入代表节点，浏览时会更像沿着主线逐步展开，而不是零散地点开。",
        label="路线总览",
    )
    render_ledger_cards(
        [
            {
                "label": str(chapter.get("badge", "篇章")),
                "title": str(chapter.get("title", "")),
                "desc": "代表节点：" + "、".join(
                    node.get("title", "") for node in chapter.get("nodes", [])[:3] if node.get("title")
                ),
            }
            for chapter in chapters[:4]
        ]
    )


setup_page("首页", icon="🏛️")
render_top_nav("首页")

status = get_rag_status()
models = get_visible_user_models()
sample = load_home_sample_content()
chapters = get_route_chapters()
total_nodes = sum(len(item.get("nodes", [])) for item in chapters)
featured_nodes = sample.get("featured_nodes", [])
lead_node = featured_nodes[0] if featured_nodes else {}
story_tracks = sample.get("story_tracks", [])
default_story_id = story_tracks[0].get("id", "overall_story") if story_tracks else "overall_story"
selected_story_id = st.session_state.get("home_story_track_id", default_story_id)
selected_story = next((item for item in story_tracks if item.get("id") == selected_story_id), story_tracks[0] if story_tracks else {})

render_exhibition_hero(
    title="长征精神·沉浸式云端答题互动平台",
    subtitle=(
        "以长征主线为展陈骨架，把路线导览、知识百问、讲解生成与互动答题组织成一个更接近数字展馆入口的线上主题展。"
    ),
    background_path=lead_node.get("image", "") or sample.get("hero_route_map", "assets/images/changzheng_route_map.jpg"),
    tags=["主线导览", "展项浏览", "知识百问", "互动闯关", "图文音一体"],
    storyline_items=[
        {"label": chapter.get("badge", "篇章"), "title": chapter.get("title", ""), "desc": chapter.get("subtitle", "")[:42]}
        for chapter in chapters[:4]
    ],
    side_title=lead_node.get("title", "长征主线导览"),
    side_text=(
        lead_node.get("summary", "")
        or "从瑞金出发到会宁会师，网站把长征主线拆解为可连续浏览的篇章与展项，让用户像在专题展中一样逐步进入历史情境。"
    ),
    side_points=[
        "先看四大篇章，再进入具体展项",
        "各节点均收录讲解、问答与互动学习内容",
        "没有模型时也能依靠静态厚内容完整浏览",
    ],
)

intro_left, intro_right = st.columns([1.2, 1])
with intro_left:
    render_curatorial_note(
        title="长征主题展",
        body=(
            "从中央苏区出发，到陕甘会师胜利结束，长征既是一段波澜壮阔的革命征程，也是一部理想信念、战略智慧和人民力量共同书写的历史篇章。"
        ),
        label="主题导语",
    )
with intro_right:
    render_curatorial_note(
        title="主线导览",
        body=(
            "可先沿四大篇章浏览，再进入重点节点。湘江战役、遵义会议、四渡赤水和飞夺泸定桥，是理解长征转折、战略机动和胜利意义的重要入口。"
        ),
        label="导览提要",
    )
    _render_home_action_links()

render_metrics(
    [
        {"label": "主线节点", "value": total_nodes},
        {"label": "知识切片", "value": status.get("chunk_count", 0)},
        {"label": "开放模型", "value": len(models)},
        {"label": "展陈篇章", "value": len(chapters)},
    ]
)

render_feature_ribbon(
    [
        {
            "label": "主展定位",
            "title": "以路线为主轴",
            "desc": "从出发、转折、突破到会师，网站采用章节式展陈结构，而不是零散知识点堆叠。",
        },
        {
            "label": "学习方式",
            "title": "以题带学",
            "desc": "通过节点阅读、知识百问、讲解生成与互动答题，把浏览体验转化为学习过程。",
        },
        {
            "label": "阅读路径",
            "title": "先主线，后专题",
            "desc": "推荐先看长征主线，再进入人物、精神、讲解与活动入口，形成更完整的认知链路。",
        },
    ]
)

render_gallery_frame("长征故事", "从整条主线或单个篇章切入，先听一遍长征，再进入对应展项继续浏览。")
track_cols = st.columns(len(story_tracks) if 0 < len(story_tracks) <= 5 else 5)
for index, track in enumerate(story_tracks[:5]):
    with track_cols[index]:
        if st.button(
            track.get("title", "长征故事"),
            key=f"home_story_track_{track.get('id', index)}",
            width="stretch",
            type="primary" if track.get("id") == selected_story.get("id") else "secondary",
        ):
            st.session_state["home_story_track_id"] = track.get("id", "")
            st.rerun()

story_left, story_right = st.columns([1.28, 0.92])
with story_left:
    render_curatorial_note(
        title=selected_story.get("title", "长征故事"),
        body=selected_story.get("subtitle", "沿着长征主线继续进入这段历史。"),
        label="故事讲述",
    )
    render_formal_script(
        selected_story.get("script", sample.get("long_march_story_script", "")),
        title=selected_story.get("title", "长征故事"),
        label="故事讲述词",
        meta=[
            selected_story.get("subtitle", ""),
            f"对应篇章：{selected_story.get('chapter_id', '总览') or '总览'}",
        ],
    )
    story_action_left, story_action_mid, story_action_right = st.columns(3)
    with story_action_left:
        audio_path = render_audio_player(
            text=selected_story.get("script", ""),
            cache_key=f"home-story::{selected_story.get('id', 'overall_story')}",
            button_label="播放讲述",
        )
    with story_action_mid:
        if st.button("进入这一篇章", key=f"home_story_chapter::{selected_story.get('id', '')}", width="stretch"):
            _jump_to_chapter(selected_story.get("chapter_id", ""))
    with story_action_right:
        if st.button("打开对应展项", key=f"home_story_node::{selected_story.get('id', '')}", width="stretch"):
            _jump_to_node(selected_story.get("lead_node_id", ""))
    if st.toggle("讲解员模式", key=f"story_digital::{selected_story.get('id', '')}"):
        render_digital_human(
            section_text=selected_story.get("script", ""),
            avatar_path="assets/avatar/guide_digital_host.png",
            audio_path=audio_path,
            title=selected_story.get("title", "长征故事"),
            subtitle=selected_story.get("subtitle", "沿着长征主线继续进入这一段历史叙事。"),
            cache_key=f"home-story::{selected_story.get('id', 'overall_story')}",
        )
with story_right:
    lead_story_node = get_route_node_data(selected_story.get("lead_node_id", "")) or {}
    render_detail_panels(
        [
            {
                "title": "这一段会讲到什么",
                "desc": selected_story.get("subtitle", "围绕长征主线中的关键场景展开讲述。"),
            },
            {
                "title": "先看哪一站",
                "desc": lead_story_node.get("title", "由本篇章起点展开") if selected_story.get("lead_node_id") else "由长征主线起点展开",
            },
            {
                "title": "继续追问",
                "desc": "、".join(selected_story.get("questions", [])[:2]) or "相关问题与史料可在知识百问中延展阅读。",
            },
        ]
    )
    render_section("延伸阅读", "沿着这一段故事继续深入，可转入相关问题、篇章与代表性节点。")
    for index, question in enumerate(selected_story.get("questions", [])[:3]):
        if st.button(question, key=f"home_story_question::{selected_story.get('id', '')}::{index}", width="stretch"):
            _jump_to_question(question)

render_section("主展结构", "四大篇章共同构成长征主展线，可先整体浏览，再进入关键节点。")
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
            "desc": "每个关键节点均收录互动答题、讲解生成与相关史料，形成完整学习链路。",
        },
    ]
)

render_gallery_frame("重点展项导览", "从最能代表长征转折、战略机动和胜利会师的节点切入，快速建立主线认识。")
render_section("重点展项", "从最能代表长征主线与历史转折的节点进入，逐步建立整条征程的整体认识。")
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

render_feature_ribbon(
    [
        {
            "label": "序厅导览",
            "title": "从路线总览进入",
            "desc": "先看全线，再进入四大篇章中的具体节点，更容易把握长征的整体逻辑。",
        },
        {
            "label": "重点建议",
            "title": "优先看转折节点",
            "desc": "湘江战役、遵义会议、四渡赤水与泸定桥，集中呈现长征精神与战略转折的关键面貌。",
        },
        {
            "label": "延展阅读",
            "title": "人物与精神专题",
            "desc": "在主线基础上继续看人物专题与长征精神，可把节点理解提升到更完整的历史叙事层面。",
        },
    ]
)

render_section("长征路线总览", "从出发、转折、突破到会师，沿着篇章顺序浏览，更容易把握整条征程。")
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

render_gallery_frame("路线导览总板", "先看四大篇章，再从推荐线路进入代表节点，把整条长征主线真正走起来。")
route_shell_left, route_shell_right = st.columns([1.08, 1.12], gap="large")
with route_shell_left:
    _render_route_overview_board(chapters)
    route_map_path = sample.get("hero_route_map", "assets/images/changzheng_route_map.jpg")
    if route_map_path:
        st.image(route_map_path, caption="长征路线总览图", width="stretch")
    chapter_jump_cols = st.columns(2)
    for index, chapter in enumerate(chapters[:4]):
        with chapter_jump_cols[index % 2]:
            if st.button(
                f"进入{chapter.get('title', '')}",
                key=f"route_overview_jump_{chapter.get('id', index)}",
                width="stretch",
            ):
                _jump_to_chapter(chapter.get("id", ""))
    if st.button("打开完整路线展厅", key="home_open_full_route_hall", width="stretch", type="primary"):
        st.switch_page("pages/3_长征路线.py")

with route_shell_right:
    route_shell_mid, route_shell_right_inner = st.columns(2, gap="large")
    with route_shell_mid:
        render_section("推荐学习路线", "沿主线梳理长征征程，从整体历史脉络进入主题展。")
        for index, item in enumerate(sample.get("recommended_learning_paths", [])[:3]):
            route_title, route_body, route_nodes = _split_route_item(item, f"学习路线 {index + 1}")
            _render_route_entry_card(route_title, route_body, route_nodes, "推荐路线")
            if st.button("按此路线进入", key=f"learn_route_{index}", width="stretch"):
                _jump_to_route(item)

    with route_shell_right_inner:
        render_section("今日推荐路线", "聚焦关键转折与胜利场景，用一条更紧凑的路径把握长征主线的核心印象。")
        for index, item in enumerate(sample.get("recommended_route", [])[:3]):
            route_title, route_body, route_nodes = _split_route_item(item, f"今日路线 {index + 1}")
            _render_route_entry_card(route_title, route_body, route_nodes, "今日导览")
            if st.button("从这条路线开始", key=f"today_route_{index}", width="stretch"):
                _jump_to_route(item)

render_gallery_frame("人物与专题", "在主线之外，从人物与精神专题继续深入，理解长征何以发生、如何转折、为何胜利。")
render_section("重要人物", "通过关键人物回看决策、组织与战斗过程，能够更完整地理解长征主线。")
figure_cols = st.columns(3)
for index, item in enumerate(sample.get("figure_cards", [])[:6]):
    with figure_cols[index % 3]:
        render_node_image(item, caption=item.get("role", "重要人物"))
        st.markdown(f"#### {item.get('title', '')}")
        st.caption(item.get("role", "重要人物"))
        st.write(item.get("summary", ""))
        st.markdown(f"<div class='small-muted'>{item.get('significance', '')[:88]}...</div>", unsafe_allow_html=True)
        if st.button("查看人物专题", key=f"home_figure_{item.get('title', '')}", width="stretch"):
            _jump_to_figure(item.get("title", ""))

render_section("长征精神专题", "从理想信念、独立自主、顾全大局和依靠群众等方面，继续理解长征留下的精神财富。")
_render_spirit_topics_grid(sample.get("spirit_topics", []))

render_feature_ribbon(
    [
        {
            "label": "推荐问题",
            "title": "从问题进入历史",
            "desc": "围绕“为什么开始、为何转折、精神何在”这些核心问题阅读，更容易建立知识框架。",
        },
        {
            "label": "示范讲解",
            "title": "从讲解进入表达",
            "desc": "通过示范讲解稿与脚本，把静态史料组织成可讲述、可展示、可传播的内容。",
        },
        {
            "label": "速览入口",
            "title": "从重点入口进入",
            "desc": "可从导览速览进入主线浏览、讲解阅读与互动问答的综合体验。",
        },
    ]
)

render_section("推荐学习内容", "从问题、讲解与路线三个方向进入主题，逐步形成对长征历史的整体理解。")
tab1, tab2, tab3, tab4 = st.tabs(["推荐问题", "示范讲解", "推荐学习路线", "导览速览"])
with tab1:
    render_curatorial_note(
        title="长征百问",
        body="从核心问题进入长征史，可先把握主线，再继续深入到具体节点、人物和精神专题。",
        label="推荐问题",
    )
    question_cols = st.columns(2)
    for index, question in enumerate(sample.get("example_questions", [])[:8]):
        with question_cols[index % 2]:
            render_curatorial_note(
                title=question,
                body="由此进入知识百问页，查看相关回答依据与延伸阅读。",
                label="推荐问题",
            )
            if st.button("进入这个问题", key=f"home_question_{index}", width="stretch"):
                _jump_to_question(question)
with tab2:
    render_curatorial_note(
        title="示范讲解",
        body="从整条征程到关键节点，讲解内容可帮助观众更连贯地理解长征的背景、经过与历史意义。",
        label="讲解样例",
    )
    render_formal_script(
        sample.get("long_march_story_script", ""),
        title="长征故事总讲解",
        label="主题总讲解",
        meta=["适用场景：展厅导览", "讲述范围：长征主线总览"],
    )
    st.divider()
    render_formal_script(
        sample.get("example_guide_script", ""),
        title="重点节点讲解示例",
        label="示范讲解词",
        meta=["适用场景：重点展项讲解", "表达方式：正式讲述"],
    )
with tab3:
    render_curatorial_note(
        title="分阶段学习路线",
        body="可由各篇章代表节点入手，再沿篇章内部的展项展开阅读与互动学习。",
        label="学习路线",
    )
    stage_cols = st.columns(2)
    for index, item in enumerate(sample.get("recommended_nodes_by_stage", [])):
        with stage_cols[index % 2]:
            render_curatorial_note(
                title=item.get("title", ""),
                body=item.get("subtitle", ""),
                label="分段浏览",
            )
            for node in item.get("nodes", [])[:3]:
                render_curatorial_note(
                    title=node.get("title", ""),
                    body=node.get("summary", "")[:88] or "由此进入对应节点展项。",
                    label=node.get("date", "") or "节点入口",
                )
                if st.button(f"进入 {node.get('title', '')}", key=f"stage_node_{item.get('title', '')}_{node.get('id', '')}", width="stretch"):
                    _jump_to_node(node.get("id", ""))
with tab4:
    render_curatorial_note(
        title="快速进入主题展",
        body="由此进入，可集中浏览主线展项、知识问答与互动学习内容。",
        label="快速入口",
    )
    quick_cols = st.columns(3)
    with quick_cols[0]:
        if st.button("进入快速导览", key="home_try_page", width="stretch"):
            st.switch_page("pages/10_测试体验.py")
    with quick_cols[1]:
        if st.button("打开知识百问", key="home_jump_qa", width="stretch"):
            st.switch_page("pages/5_知识库.py")
    with quick_cols[2]:
        _render_game_page_link("进入互动闯关")
