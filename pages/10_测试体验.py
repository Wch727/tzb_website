"""导览速览页。"""

from __future__ import annotations

import streamlit as st

from activity_manager import get_activity
from content_store import get_featured_route_nodes, get_recommended_questions, get_storytelling_tracks
from game import get_route_node
from generator import generate_guide_script
from media import render_audio_player, render_digital_human
from node_detail import render_node_detail
from rag import ask
from sample_content import load_home_sample_content
from streamlit_ui import (
    build_current_provider_config,
    render_formal_script,
    render_model_banner,
    render_runtime_notice,
    render_section,
    render_sources,
    render_top_nav,
    setup_page,
)


setup_page("导览速览", icon="🧭")
render_top_nav("导览速览")
render_section("导览速览", "从重点问题、代表性节点与讲解入口切入，快速把握整站主线内容。")
render_model_banner()

provider_config = build_current_provider_config()
sample = load_home_sample_content()
featured_nodes = get_featured_route_nodes(limit=6)
current_activity = get_activity(st.session_state.get("current_activity_id", ""))

if current_activity:
    st.info(f"所属活动：{current_activity.get('name', '')} · {current_activity.get('mode', '')}")

story_tracks = get_storytelling_tracks()

tab1, tab2, tab3, tab4 = st.tabs(["快速问答", "展项预览", "一键讲解", "长征故事"])

with tab1:
    render_section("推荐问题", "由典型问题切入长征史的核心脉络。")
    question_cols = st.columns(3)
    for index, question in enumerate(get_recommended_questions(limit=6)):
        with question_cols[index % 3]:
            if st.button(question, key=f"quick_try_{index}", width="stretch"):
                st.session_state["quick_try_question"] = question

    question = st.session_state.get("quick_try_question", "")
    if question:
        with st.spinner("正在生成回答..."):
            result = ask(question=question, provider_config=provider_config, filters={}, top_k=4)
        render_runtime_notice(result)
        st.markdown(f"### 问题：{question}")
        st.write(result.get("answer", ""))
        render_sources(result.get("sources", []), title="本次回答依据")

with tab2:
    render_section("代表性展项预览", "从重点节点中抽样浏览展项详情、讲解内容与互动入口。")
    preview_cols = st.columns(3)
    for index, node in enumerate(featured_nodes):
        with preview_cols[index % 3]:
            st.markdown(f"**{node.get('title', '')}**")
            st.caption(f"{node.get('date', '')} · {node.get('place', '')}")
            st.write(node.get("summary", ""))
            if st.button("打开该展项", key=f"test_node_{node.get('id')}", width="stretch"):
                st.session_state["selected_node_id"] = node.get("id", "")
                st.rerun()

    selected_node = get_route_node(st.session_state.get("selected_node_id", featured_nodes[0].get("id", "") if featured_nodes else ""))
    if selected_node:
        render_node_detail(
            node=selected_node,
            provider_config=provider_config,
            audience=st.session_state.get("selected_role_name", "大学生"),
            key_prefix="test-page-node",
        )

with tab3:
    render_section("一键讲解", "围绕单一节点生成讲解内容，并同步查看资料依据。")
    topic_node = st.selectbox(
        "选择讲解主题",
        [node.get("id", "") for node in featured_nodes],
        format_func=lambda node_id: next((node.get("title", "") for node in featured_nodes if node.get("id") == node_id), node_id),
    )
    selected_node = get_route_node(topic_node) or {}
    if st.button("生成该节点讲解稿", width="stretch", type="primary"):
        with st.spinner("正在检索资料并生成讲解稿..."):
            result = generate_guide_script(
                topic=selected_node.get("title", ""),
                audience=st.session_state.get("user_role", "大学生"),
                duration="3分钟",
                provider_config=provider_config,
            )
        st.session_state["test_page_guide"] = result

    guide_result = st.session_state.get("test_page_guide")
    if guide_result:
        render_runtime_notice(guide_result)
        render_formal_script(
            guide_result.get("script", ""),
            title=f"{selected_node.get('title', '长征节点')}讲解词",
            label="快速讲解词",
            meta=[
                f"讲解主题：{selected_node.get('title', '长征节点')}",
                f"地点：{selected_node.get('place', '未标注')}",
                    "场景：导览速览",
            ],
        )
        render_sources(guide_result.get("sources", []), title="本次讲解依据")
        st.markdown("#### 相关展项")
        for node in sample.get("featured_nodes", [])[:3]:
            st.markdown(f"- **{node.get('title', '')}**：{node.get('summary', '')}")

with tab4:
    render_section("长征故事", "从总讲述或分篇章讲述切入，再进入对应展项展开浏览。")
    story_id = st.selectbox(
        "选择讲述主题",
        [track.get("id", "") for track in story_tracks],
        format_func=lambda track_id: next((track.get("title", "") for track in story_tracks if track.get("id") == track_id), track_id),
    )
    current_story = next((track for track in story_tracks if track.get("id") == story_id), story_tracks[0] if story_tracks else {})
    st.markdown(f"### {current_story.get('title', '长征故事')}")
    st.caption(current_story.get("subtitle", ""))
    render_formal_script(
        current_story.get("script", ""),
        title=current_story.get("title", "长征故事"),
        label="故事讲述词",
        meta=[
            current_story.get("subtitle", ""),
            f"关联篇章：{current_story.get('lead_node_id', '总览讲述')}",
        ],
    )
    audio_path = render_audio_player(
        text=current_story.get("script", ""),
        cache_key=f"quick-story::{current_story.get('id', 'overall_story')}",
        button_label="播放这一段讲述",
    )
    if st.toggle("讲解员模式", key=f"quick_story_avatar::{current_story.get('id', '')}"):
        render_digital_human(
            section_text=current_story.get("script", ""),
            avatar_path="assets/avatar/guide_digital_host.png",
            audio_path=audio_path,
            title=current_story.get("title", "长征故事"),
            subtitle=current_story.get("subtitle", "沿着长征主线继续进入这一段历史叙事。"),
            cache_key=f"quick-story::{current_story.get('id', 'overall_story')}",
        )
    st.markdown("#### 延伸阅读")
    for question in current_story.get("questions", [])[:3]:
        if st.button(question, key=f"quick_story_question::{story_id}::{question}", width="stretch"):
            st.session_state["pending_question"] = question
            st.switch_page("pages/5_知识库.py")
    story_node = get_route_node(current_story.get("lead_node_id", "")) or {}
    if story_node:
        if st.button("打开对应展项", key=f"quick_story_node::{story_id}", width="stretch"):
            st.session_state["selected_node_id"] = story_node.get("id", "")
            st.switch_page("pages/3_长征路线.py")
