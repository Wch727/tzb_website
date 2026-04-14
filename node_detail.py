"""节点详情渲染逻辑。"""

from __future__ import annotations

from typing import Any, Dict, List

import streamlit as st

from content_store import (
    build_node_related_questions,
    build_static_sources_for_node,
    get_chapter_for_node,
    get_node_extended_reading,
    get_related_nodes,
)
from generator import generate_guide_script, generate_short_video_script
from media import render_audio_player, render_digital_human, render_node_image
from rag import retrieve_knowledge
from streamlit_ui import render_runtime_notice, render_section, render_sources


def _node_narration_text(node: Dict[str, Any], explanation: str = "", guide_script: str = "") -> str:
    """拼接节点讲解文本。"""
    if guide_script.strip():
        return guide_script
    if explanation.strip():
        return explanation
    return (
        f"{node.get('title', '')}。时间：{node.get('date', '未标注')}。地点：{node.get('place', '未标注')}。"
        f"简述：{node.get('summary', '')}。"
        f"历史背景：{node.get('background', '')}。"
        f"事件经过：{node.get('process', '')}。"
        f"历史意义：{node.get('significance', '')}。"
    )


def _source_cards_from_retrieval(node: Dict[str, Any], retrieval: Dict[str, Any]) -> List[Dict[str, Any]]:
    """整理节点详情使用到的依据卡片。"""
    source_cards = [
        {
            "source_file": item["metadata"].get("source_file", "未知文件"),
            "title": item["metadata"].get("title", "未命名"),
            "type": item["metadata"].get("type", "未知"),
            "chapter_title": item["metadata"].get("chapter_title", ""),
            "section_title": item["metadata"].get("section_title", ""),
            "source_page": item["metadata"].get("source_page", ""),
            "snippet": item.get("text", "")[:220],
        }
        for item in retrieval.get("hits", [])
    ]
    if not source_cards:
        return build_static_sources_for_node(node)
    return build_static_sources_for_node(node)[:1] + source_cards


def _render_figure_block(node: Dict[str, Any]) -> None:
    """渲染关键人物区。"""
    figures = node.get("figures", []) or []
    if not figures:
        return
    render_section("关键人物", "人物并非节点的附属信息，而是理解转折、决策与执行过程的重要入口。")
    chips = []
    for name in figures:
        chips.append(
            f"""
            <div class="info-card" style="padding:0.85rem 1rem;">
                <div class="card-label">人物线索</div>
                <div class="card-title" style="font-size:1rem;">{name}</div>
                <div class="card-desc">围绕该人物继续理解本节点中的组织决策、战略判断与行动执行。</div>
            </div>
            """
        )
    st.markdown(f"<div class='card-grid'>{''.join(chips)}</div>", unsafe_allow_html=True)


def _render_key_points(node: Dict[str, Any]) -> None:
    """渲染关键知识点。"""
    key_points = node.get("key_points", []) or []
    render_section("关键知识点", "把历史线索、战略节点与精神内涵结合起来，形成更稳定的学习记忆。")
    if key_points:
        for item in key_points:
            st.markdown(f"- {item}")
    else:
        st.info("当前节点暂未配置额外知识点。")


def _render_extended_reading(node: Dict[str, Any]) -> None:
    """渲染延伸阅读。"""
    extended = get_node_extended_reading(node, limit=4)
    if not extended:
        return
    render_section("延伸阅读", "从人物、问答和精神专题继续延展开来，让单个展项与更大的长征叙事连接起来。")
    cols = st.columns(min(4, len(extended)))
    for index, item in enumerate(extended):
        with cols[index % len(cols)]:
            st.markdown(f"**{item.get('title', item.get('question', '延伸阅读'))}**")
            st.write(item.get("summary", item.get("answer", "")))


def render_node_detail(
    node: Dict[str, Any],
    provider_config: Dict[str, Any],
    audience: str = "大学生",
    key_prefix: str = "node_detail",
    explanation: str = "",
) -> None:
    """渲染节点详情展项。"""
    node_id = node.get("id", key_prefix)
    chapter = get_chapter_for_node(node)
    retrieval = retrieve_knowledge(
        question=node.get("title", ""),
        filters={"route_stage": node.get("route_stage", "")},
        top_k=4,
    )
    source_cards = _source_cards_from_retrieval(node, retrieval)
    related_nodes = get_related_nodes(node, limit=3)
    related_questions = build_node_related_questions(node, limit=4)

    st.markdown(
        f"""
        <div class="notice-card" style="margin-top:0.2rem;">
            <strong>{chapter.get('badge', '展项单元')}</strong> · {chapter.get('title', '主线展项')}
            <br/>
            <span class="small-muted">{chapter.get('subtitle', '')}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    hero_left, hero_right = st.columns([1.02, 1.28])
    with hero_left:
        render_node_image(node, caption=node.get("image_caption", "") or f"{node.get('title', '')} · {node.get('place', '')}")
    with hero_right:
        st.markdown(f"## {node.get('title', '长征节点')}")
        st.markdown(
            f"**时间**：{node.get('date', '未标注')}  \n"
            f"**地点**：{node.get('place', '未标注')}  \n"
            f"**主线位置**：{node.get('route_stage', '未标注')}"
        )
        st.markdown("### 展项简述")
        st.write(node.get("summary", "暂无摘要说明。"))
        if related_questions:
            st.markdown("### 本节点可继续追问")
            for question in related_questions:
                st.markdown(f"- {question}")

    render_section("历史背景", "先理解处境，再理解决策，这样节点才不只是一个孤立的名称。")
    st.write(node.get("background", "暂无背景介绍。"))

    render_section("事件经过", "从行动脉络、转移路线和关键动作三个层次还原节点过程。")
    st.write(node.get("process", "暂无事件经过说明。"))

    render_section("历史意义", "把转折意义、战略价值与长征精神联系起来，形成更完整的学习闭环。")
    st.write(node.get("significance", "暂无历史意义说明。"))

    _render_figure_block(node)
    _render_key_points(node)

    render_section("讲解与互动", "语音讲解、数字讲解员与内容生成入口集中在同一区域，便于连续浏览。")
    action_left, action_mid, action_right = st.columns(3)
    with action_left:
        if st.button("进入互动题", key=f"quiz::{node_id}", width="stretch", type="primary"):
            st.session_state["story_state"] = {}
            st.session_state["selected_node_id"] = node_id
            st.switch_page("pages/4_剧情答题.py")
    with action_mid:
        if st.button("生成讲解稿", key=f"guide::{node_id}", width="stretch"):
            result = generate_guide_script(
                topic=node.get("title", ""),
                audience=audience,
                duration="3分钟",
                provider_config=provider_config,
            )
            st.session_state[f"guide_result::{node_id}"] = result
    with action_right:
        if st.button("生成短视频脚本", key=f"video::{node_id}", width="stretch"):
            result = generate_short_video_script(
                topic=node.get("title", ""),
                audience=audience,
                style="正式讲述",
                provider_config=provider_config,
            )
            st.session_state[f"video_result::{node_id}"] = result

    guide_result = st.session_state.get(f"guide_result::{node_id}")
    if guide_result:
        render_runtime_notice(guide_result)
        render_section("节点讲解稿", "即使没有模型，也会优先使用内置静态内容生成完整讲解。")
        st.write(guide_result.get("script", ""))
        render_sources(guide_result.get("sources", []), title="本次讲解依据")

    video_result = st.session_state.get(f"video_result::{node_id}")
    if video_result:
        render_runtime_notice(video_result)
        render_section("节点短视频脚本", "短视频脚本同样先检索再生成，用于口播展示与新媒体传播。")
        st.write(video_result.get("script", ""))
        render_sources(video_result.get("sources", []), title="本次脚本依据")

    narration_text = _node_narration_text(
        node=node,
        explanation=explanation,
        guide_script=guide_result.get("script", "") if isinstance(guide_result, dict) else "",
    )
    media_left, media_right = st.columns([1, 1])
    with media_left:
        audio_path = render_audio_player(
            text=narration_text,
            cache_key=f"{key_prefix}-{node_id}",
            button_label="播放语音讲解",
        )
    with media_right:
        if st.button("切换数字讲解员模式", key=f"digital::{node_id}", width="stretch"):
            st.session_state[f"show_digital::{node_id}"] = not st.session_state.get(f"show_digital::{node_id}", False)

    if st.session_state.get(f"show_digital::{node_id}", False):
        render_digital_human(
            section_text=narration_text,
            avatar_path=node.get("avatar", "assets/avatar/guide.svg"),
            audio_path=audio_path,
        )

    _render_extended_reading(node)

    if related_nodes:
        render_section("相关推荐节点", "沿着主线继续浏览，让单个展项与整条征程相互连接。")
        cols = st.columns(min(3, len(related_nodes)))
        for index, related in enumerate(related_nodes):
            with cols[index % len(cols)]:
                render_node_image(related, caption=related.get("place", ""))
                st.markdown(f"**{related.get('title', '')}**")
                st.caption(f"{related.get('date', '')} · {related.get('place', '')}")
                st.write(related.get("summary", ""))
                if st.button("查看该节点", key=f"related::{node_id}::{related.get('id', '')}", width="stretch"):
                    st.session_state["selected_node_id"] = related.get("id", "")
                    st.rerun()

    render_sources(source_cards, title="本节点内容依据")
