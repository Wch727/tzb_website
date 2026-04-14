"""产品首页。"""

from __future__ import annotations

import streamlit as st

from content_store import get_chapter_for_node, get_route_chapters, get_route_node_data
from media import render_node_image
from rag import get_rag_status
from sample_content import load_home_sample_content
from streamlit_ui import (
    render_chapter_overview_cards,
    render_curatorial_note,
    render_detail_panels,
    render_exhibition_hero,
    render_feature_ribbon,
    render_gallery_frame,
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
    """按推荐路线跳到首个可浏览节点。"""
    for title in _extract_route_titles(route_text):
        node = get_route_node_data(title)
        if node:
            st.session_state["selected_node_id"] = node.get("id", "")
            st.session_state["selected_chapter_id"] = get_chapter_for_node(node).get("id", "")
            st.switch_page("pages/3_长征路线.py")
            return


def _jump_to_question(question: str) -> None:
    """把推荐问题带入知识百问页。"""
    st.session_state["pending_question"] = question
    st.switch_page("pages/5_知识库.py")


setup_page("首页", icon="🏛️")
render_top_nav("首页")

status = get_rag_status()
models = get_visible_user_models()
sample = load_home_sample_content()
chapters = get_route_chapters()
total_nodes = sum(len(item.get("nodes", [])) for item in chapters)
featured_nodes = sample.get("featured_nodes", [])
lead_node = featured_nodes[0] if featured_nodes else {}

render_exhibition_hero(
    title="《长征史》交互式导览与闯关学习系统",
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
        "每个节点都可继续讲解、问答与互动答题",
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
        label="导览提示",
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

render_gallery_frame("长征故事总讲解", "沿着主线回望长征，从出发、转折、突破到会师，理解这段历史的整体脉络。")
story_left, story_right = st.columns([1.3, 0.9])
with story_left:
    render_curatorial_note(
        title="长征故事",
        body="从主线整体进入长征历史，有助于把各个节点、人物和精神专题放回完整历史进程中加以理解。",
        label="总讲解",
    )
    st.write(sample.get("long_march_story_script", ""))
with story_right:
    render_detail_panels(
        [
            {
                "title": "第一层理解",
                "desc": "先理解为什么出发、为什么会转折、为什么最终能够胜利会师。",
            },
            {
                "title": "第二层理解",
                "desc": "再把湘江战役、遵义会议、四渡赤水、泸定桥等节点放回整条主线中理解。",
            },
            {
                "title": "第三层理解",
                "desc": "最后从理想信念、实事求是、顾全大局、依靠群众等精神层面总结长征的历史价值。",
            },
        ]
    )

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
            "desc": "每个关键节点都可继续进入互动答题、讲解生成与学习延展，形成以题带学的闭环。",
        },
    ]
)

render_gallery_frame("重点展项导览", "从最能代表长征转折、战略机动和胜利会师的节点切入，快速建立主线认识。")
render_section("重点展项", "优先从最能代表长征主线与历史转折的节点进入，建立整条征程的基本认识。")
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
            "desc": "湘江战役、遵义会议、四渡赤水与泸定桥，是最适合快速理解长征精神与战略转折的展项。",
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
        title="推荐浏览顺序",
        body="如果希望尽快把握长征主线，可先沿四大篇章依次浏览；如果更想先体验互动学习，可从剧情闯关进入，再回到具体节点继续阅读。",
        label="主线提要",
    )
    st.markdown("### 推荐学习路线")
    for index, item in enumerate(sample.get("recommended_learning_paths", [])[:4]):
        render_curatorial_note(
            title=item.split("：", 1)[0] if "：" in item else f"学习路线 {index + 1}",
            body=item.split("：", 1)[1] if "：" in item else item,
            label="导览路线",
        )
        if st.button("按此路线浏览", key=f"learn_route_{index}", width="stretch"):
            _jump_to_route(item)
    st.markdown("### 今日推荐路线")
    for index, item in enumerate(sample.get("recommended_route", [])[:4]):
        render_curatorial_note(
            title=item.split("：", 1)[0] if "：" in item else f"推荐路线 {index + 1}",
            body=item.split("：", 1)[1] if "：" in item else item,
            label="今日路线",
        )
        if st.button("从首站进入", key=f"today_route_{index}", width="stretch"):
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
spirit_cols = st.columns(3)
for index, item in enumerate(sample.get("spirit_topics", [])[:6]):
    with spirit_cols[index % 3]:
        render_curatorial_note(
            title=item.get("title", ""),
            body=item.get("summary", ""),
            label="精神专题",
        )
        sources = item.get("official_sources", []) or []
        if sources:
            st.caption(f"资料来源：{sources[0].get('publisher', '官方资料')}")

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
            "desc": "如果想先试一遍主线、讲解和问答，可直接进入快速导览与互动体验区。",
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
                body="点击后可直接进入知识百问页，查看回答依据与延伸阅读。",
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
    st.write(sample.get("long_march_story_script", ""))
    st.divider()
    st.write(sample.get("example_guide_script", ""))
with tab3:
    render_curatorial_note(
        title="分阶段学习路线",
        body="如果希望沿着主线逐步深入，可先从每个篇章最具代表性的节点进入，再继续展开阅读与互动学习。",
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
                if st.button(f"查看 {node.get('title', '')}", key=f"stage_node_{item.get('title', '')}_{node.get('id', '')}", width="stretch"):
                    _jump_to_node(node.get("id", ""))
with tab4:
    render_curatorial_note(
        title="快速进入主题展",
        body="如果想先试一遍主线浏览、展项阅读、知识问答和互动学习，可以从这里直接进入。",
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
        if st.button("进入互动闯关", key="home_jump_quiz", width="stretch"):
            st.switch_page("pages/4_剧情答题.py")
