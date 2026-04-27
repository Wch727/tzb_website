"""主展首页。"""

from __future__ import annotations

import streamlit as st

from content_store import get_chapter_for_node, get_route_chapters, get_route_node_data
from home_components import (
    node_card_html,
    render_home_hero,
    render_home_section,
    render_home_stats,
    render_story_panel,
    route_card_html,
    topic_card_html,
)
from media import render_audio_player, render_digital_human
from rag import get_rag_status
from sample_content import load_home_sample_content
from streamlit_ui import render_top_nav, setup_page
from utils import get_visible_user_models


def _jump_to_node(node_id: str) -> None:
    """进入单节点展项。"""
    if node_id:
        st.session_state["selected_node_id"] = node_id
        st.session_state["_scroll_to_top_once"] = True
        st.switch_page("pages/14_节点展项.py")


def _jump_to_figure(name: str) -> None:
    """进入人物专题页。"""
    if name:
        st.session_state["selected_figure_name"] = name
        st.session_state["_scroll_to_top_once"] = True
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
    """按推荐路线进入对应篇章。"""
    for title in _extract_route_titles(route_text):
        node = get_route_node_data(title)
        if node:
            st.session_state["selected_chapter_id"] = get_chapter_for_node(node).get("id", "")
            st.session_state.pop("selected_node_id", None)
            st.session_state["_scroll_to_top_once"] = True
            st.switch_page("pages/3_长征路线.py")
            return
    st.switch_page("pages/3_长征路线.py")


def _jump_to_question(question: str) -> None:
    """把推荐问题带入知识百问页。"""
    st.session_state["pending_question"] = question
    st.session_state["_scroll_to_top_once"] = True
    st.switch_page("pages/5_知识库.py")


def _jump_to_chapter(chapter_id: str) -> None:
    """进入指定篇章。"""
    if chapter_id:
        st.session_state["selected_chapter_id"] = chapter_id
    st.session_state.pop("selected_node_id", None)
    st.session_state["_scroll_to_top_once"] = True
    st.switch_page("pages/3_长征路线.py")


setup_page("首页", icon="🏛️")
render_top_nav("首页")

sample = load_home_sample_content()
chapters = get_route_chapters()
featured_nodes = sample.get("featured_nodes", [])
story_tracks = sample.get("story_tracks", [])
status = get_rag_status()
models = get_visible_user_models()
total_nodes = sum(len(chapter.get("nodes", [])) for chapter in chapters)
lead_node = featured_nodes[0] if featured_nodes else {}

default_story_id = story_tracks[0].get("id", "overall_story") if story_tracks else "overall_story"
selected_story_id = st.session_state.get("home_story_track_id", default_story_id)
selected_story = next(
    (item for item in story_tracks if item.get("id") == selected_story_id),
    story_tracks[0] if story_tracks else {},
)

render_home_hero(
    title="长征精神·沉浸式云端答题互动平台",
    subtitle=(
        "以长征主线为展陈骨架，整合路线导览、节点展项、人物专题、知识问答和互动闯关，"
        "形成可浏览、可讲解、可参与的云端主题展。"
    ),
    hero_item=lead_node or {"image": sample.get("hero_route_map", "assets/images/changzheng_route_map.jpg")},
    badges=["主线陈列", "重点展项", "人物专题", "知识百问", "互动闯关"],
    chapters=chapters,
    panel_title=lead_node.get("title", "长征主线导览"),
    panel_text=lead_node.get("summary", "沿着长征主线进入四大篇章，从出发、转折、突破到会师逐步展开。"),
)

hero_left, hero_mid, hero_right = st.columns(3)
with hero_left:
    if st.button("开始长征导览", width="stretch", type="primary"):
        st.switch_page("pages/3_长征路线.py")
with hero_mid:
    if st.button("进入互动闯关", width="stretch"):
        st.switch_page("pages/4_剧情答题.py")
with hero_right:
    if st.button("进入导览速览", width="stretch"):
        st.switch_page("pages/10_测试体验.py")

render_home_stats(
    [
        {"label": "主线节点", "value": total_nodes},
        {"label": "展陈篇章", "value": len(chapters)},
        {"label": "知识切片", "value": status.get("chunk_count", 0)},
        {"label": "开放模型", "value": len(models)},
    ]
)

render_home_section(
    "主线陈列",
    "按照官方数字展常用的“基本陈列 + 专题单元”方式，把长征路线组织为四个连续篇章。",
    "基本陈列",
)
chapter_cols = st.columns(4)
for index, chapter in enumerate(chapters[:4]):
    with chapter_cols[index]:
        st.html(
            topic_card_html(
                chapter.get("title", ""),
                chapter.get("subtitle", ""),
                chapter.get("badge", "主线篇章"),
            )
        )
        if st.button("进入本篇章", key=f"home_chapter::{chapter.get('id', index)}", width="stretch"):
            _jump_to_chapter(chapter.get("id", ""))

render_home_section(
    "重点展项",
    "从长征史中最具代表性的节点切入，先建立整体路线感，再进入单节点展项阅读。",
    "正在展出",
)
node_cols = st.columns(3)
for index, node in enumerate(featured_nodes[:6]):
    with node_cols[index % 3]:
        st.html(node_card_html(node, label=f"展项 {index + 1:02d}"))
        if st.button("进入展项", key=f"home_featured::{node.get('id', index)}", width="stretch"):
            _jump_to_node(node.get("id", ""))

render_home_section(
    "讲解服务",
    "从长征故事进入展项，适合第一遍浏览，也适合现场讲解和课堂导览。",
    "自动导览",
)
if story_tracks:
    track_cols = st.columns(min(5, len(story_tracks)))
    for index, track in enumerate(story_tracks[:5]):
        with track_cols[index]:
            if st.button(
                track.get("title", "长征故事"),
                key=f"home_story::{track.get('id', index)}",
                width="stretch",
                type="primary" if track.get("id") == selected_story.get("id") else "secondary",
            ):
                st.session_state["home_story_track_id"] = track.get("id", "")
                st.rerun()

story_left, story_right = st.columns([1.35, 0.8], gap="large")
story_script = selected_story.get("script", "") or sample.get("long_march_story_script", "")
with story_left:
    render_story_panel(selected_story, fallback_script=sample.get("long_march_story_script", ""))
with story_right:
    audio_path = render_audio_player(
        text=story_script,
        cache_key=f"home-story::{selected_story.get('id', 'overall_story')}",
        button_label="播放讲解",
    )
    if st.button("进入对应篇章", key="home_story_chapter", width="stretch"):
        _jump_to_chapter(selected_story.get("chapter_id", ""))
    if st.button("打开对应展项", key="home_story_node", width="stretch"):
        _jump_to_node(selected_story.get("lead_node_id", ""))
    if st.toggle("讲解员模式", key=f"story_digital::{selected_story.get('id', 'overall')}"):
        render_digital_human(
            section_text=story_script,
            avatar_path="assets/avatar/guide_digital_host.png",
            audio_path=audio_path,
            title=selected_story.get("title", "长征故事"),
            subtitle=selected_story.get("subtitle", "沿着长征主线继续进入这一段历史叙事。"),
            cache_key=f"home-story::{selected_story.get('id', 'overall_story')}",
        )

render_home_section(
    "专题展厅",
    "在主线之外继续进入人物、精神、知识问答和学习活动，让参观路径更完整。",
    "专题展览",
)
topic_cols = st.columns(4)
topic_cards = [
    ("人物专题", "党的重要领导人与长征关键人物专题介绍。", "人物展厅", "pages/13_人物专题.py"),
    ("长征精神", "从理想信念、实事求是、顾全大局和依靠群众等维度理解精神内涵。", "精神专题", "pages/5_知识库.py"),
    ("知识百问", "围绕长征为什么开始、为什么转折、为什么胜利等问题展开学习。", "问答专题", "pages/5_知识库.py"),
    ("互动闯关", "完成展项阅读后进入闭卷挑战，答题后解锁解析与成长奖励。", "教育活动", "pages/4_剧情答题.py"),
]
for index, item in enumerate(topic_cards):
    with topic_cols[index]:
        st.html(topic_card_html(item[0], item[1], item[2]))
        if st.button("进入", key=f"home_topic::{index}", width="stretch"):
            st.switch_page(item[3])

render_home_section(
    "人物专题",
    "通过关键人物回看长征中的决策、组织、行军与战斗，更具体地理解主线进程。",
    "人物展厅",
)
figure_cols = st.columns(3)
for index, figure in enumerate(sample.get("figure_cards", [])[:6]):
    with figure_cols[index % 3]:
        st.html(
            topic_card_html(
                figure.get("title", ""),
                figure.get("summary", "") or figure.get("significance", ""),
                figure.get("role", "重要人物"),
            )
        )
        if st.button("查看人物专题", key=f"home_figure::{figure.get('title', index)}", width="stretch"):
            _jump_to_figure(figure.get("title", ""))

render_home_section(
    "推荐学习路线",
    "为第一次进入网站的参观者提供几条可直接开始的浏览路径。",
    "参观路线",
)
route_left, route_right = st.columns(2, gap="large")
with route_left:
    for index, item in enumerate(sample.get("recommended_learning_paths", [])[:3]):
        st.html(route_card_html(item, "推荐路线"))
        if st.button("按此路线进入", key=f"home_learning_route::{index}", width="stretch"):
            _jump_to_route(item)
with route_right:
    for index, item in enumerate(sample.get("recommended_route", [])[:3]):
        st.html(route_card_html(item, "今日导览"))
        if st.button("从这条路线开始", key=f"home_today_route::{index}", width="stretch"):
            _jump_to_route(item)

render_home_section(
    "教育活动",
    "活动、排行榜和数据大屏用于课堂、研学和集体学习场景。",
    "教育与活动",
)
activity_cols = st.columns(3)
activity_cards = [
    ("活动中心", "创建或进入知识竞赛、党史学习日和研学任务活动。", "活动入口", "pages/6_活动中心.py"),
    ("排行榜", "查看个人、小队、班级或单位的学习战绩。", "学习榜单", "pages/7_排行榜.py"),
    ("数据大屏", "集中呈现参与人数、答题热度和实时战绩播报。", "投屏展示", "pages/12_数据大屏.py"),
]
for index, item in enumerate(activity_cards):
    with activity_cols[index]:
        st.html(topic_card_html(item[0], item[1], item[2]))
        if st.button("打开", key=f"home_activity::{index}", width="stretch"):
            st.switch_page(item[3])

render_home_section(
    "长征百问",
    "从问题进入历史，再回到节点展项和人物专题中延展阅读。",
    "知识服务",
)
question_cols = st.columns(2)
for index, question in enumerate(sample.get("example_questions", [])[:8]):
    with question_cols[index % 2]:
        st.html(topic_card_html(question, "进入知识百问查看回答依据与延伸阅读。", "推荐问题"))
        if st.button("查看回答", key=f"home_question::{index}", width="stretch"):
            _jump_to_question(question)
