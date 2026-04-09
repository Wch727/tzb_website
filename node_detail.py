"""节点详情渲染逻辑。"""

from __future__ import annotations

from typing import Any, Dict

import streamlit as st

from content_store import build_static_sources_for_node, get_related_nodes
from generator import generate_guide_script, generate_short_video_script
from media import render_audio_player, render_digital_human, render_node_image
from rag import retrieve_knowledge
from streamlit_ui import render_runtime_notice, render_sources


def _node_narration_text(node: Dict[str, Any], explanation: str = "", guide_script: str = "") -> str:
    """拼接节点讲解文本。"""
    if guide_script.strip():
        return guide_script
    if explanation.strip():
        return explanation
    return (
        f"{node.get('title', '')}。时间：{node.get('date', '未标注')}。地点：{node.get('place', '未标注')}。"
        f"背景介绍：{node.get('background', '')}。事件经过：{node.get('process', '')}。"
        f"历史意义：{node.get('significance', '')}。"
    )


def render_node_detail(
    node: Dict[str, Any],
    provider_config: Dict[str, Any],
    audience: str = "大学生",
    key_prefix: str = "node_detail",
    explanation: str = "",
) -> None:
    """渲染节点详情展项。"""
    node_id = node.get("id", key_prefix)
    retrieval = retrieve_knowledge(
        question=node.get("title", ""),
        filters={"route_stage": node.get("route_stage", "")},
        top_k=4,
    )
    source_cards = [
        {
            "source_file": item["metadata"].get("source_file", "未知文件"),
            "title": item["metadata"].get("title", "未命名"),
            "type": item["metadata"].get("type", "未知"),
            "snippet": item.get("text", "")[:220],
        }
        for item in retrieval.get("hits", [])
    ]
    if not source_cards:
        source_cards = build_static_sources_for_node(node)
    else:
        source_cards = build_static_sources_for_node(node)[:1] + source_cards

    left, right = st.columns([1.05, 1.35])
    with left:
        render_node_image(node, caption=node.get("image_caption", "") or f"{node.get('title', '')} · {node.get('place', '')}")
        st.caption(f"时间：{node.get('date', '未标注')}")
        st.caption(f"地点：{node.get('place', '未标注')}")
        if node.get("figures"):
            st.caption("关键人物：" + "、".join(node.get("figures", [])))

    with right:
        st.markdown(f"## {node.get('title', '长征节点')}")
        st.markdown(
            f"**节点定位：** {node.get('route_stage', '未标注')}  \n"
            f"**历史摘要：** {node.get('summary', '暂无摘要')}"
        )
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["历史背景", "事件经过", "历史意义", "关键知识点", "互动操作"])
        with tab1:
            st.write(node.get("background", "暂无背景介绍。"))
        with tab2:
            st.write(node.get("process", "暂无事件经过说明。"))
        with tab3:
            st.write(node.get("significance", "暂无历史意义说明。"))
        with tab4:
            key_points = node.get("key_points", []) or []
            if key_points:
                for item in key_points:
                    st.markdown(f"- {item}")
            else:
                st.info("当前节点暂未配置额外知识点。")
        with tab5:
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("进入互动答题", key=f"quiz::{node_id}", use_container_width=True):
                    st.session_state["preferred_game_node"] = node_id
                    st.switch_page("pages/4_长征闯关.py")
            with col2:
                if st.button("生成该节点讲解稿", key=f"guide::{node_id}", use_container_width=True):
                    result = generate_guide_script(
                        topic=node.get("title", ""),
                        audience=audience,
                        duration="3分钟",
                        provider_config=provider_config,
                    )
                    st.session_state[f"guide_result::{node_id}"] = result
            with col3:
                if st.button("生成该节点短视频脚本", key=f"video::{node_id}", use_container_width=True):
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
        st.markdown("### 节点讲解稿")
        st.write(guide_result.get("script", ""))
        render_sources(guide_result.get("sources", []), title="本次讲解稿依据")

    video_result = st.session_state.get(f"video_result::{node_id}")
    if video_result:
        render_runtime_notice(video_result)
        st.markdown("### 节点短视频脚本")
        st.write(video_result.get("script", ""))
        render_sources(video_result.get("sources", []), title="本次脚本依据")

    narration_text = _node_narration_text(
        node=node,
        explanation=explanation,
        guide_script=guide_result.get("script", "") if isinstance(guide_result, dict) else "",
    )
    audio_path = render_audio_player(
        text=narration_text,
        cache_key=f"{key_prefix}-{node_id}",
        button_label="播放语音讲解",
    )

    if st.button("数字人讲解模式", key=f"digital::{node_id}", use_container_width=True):
        st.session_state[f"show_digital::{node_id}"] = not st.session_state.get(f"show_digital::{node_id}", False)

    if st.session_state.get(f"show_digital::{node_id}", False):
        render_digital_human(
            section_text=narration_text,
            avatar_path=node.get("avatar", "assets/avatar/guide.svg"),
            audio_path=audio_path,
        )

    related_nodes = get_related_nodes(node, limit=3)
    if related_nodes:
        st.markdown("### 相关推荐节点")
        cols = st.columns(min(3, len(related_nodes)))
        for index, related in enumerate(related_nodes):
            with cols[index % len(cols)]:
                render_node_image(related, caption=related.get("place", ""))
                st.markdown(f"**{related.get('title', '')}**")
                st.write(related.get("summary", ""))
                if st.button("查看该节点", key=f"related::{node_id}::{related.get('id', '')}", use_container_width=True):
                    st.session_state["selected_node_id"] = related.get("id", "")
                    st.rerun()

    render_sources(source_cards, title="本节点知识依据")
