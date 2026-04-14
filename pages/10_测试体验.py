"""导览速览页。"""

from __future__ import annotations

import streamlit as st

from activity_manager import get_activity
from content_store import get_featured_route_nodes, get_recommended_questions
from game import get_route_node
from generator import generate_guide_script
from node_detail import render_node_detail
from rag import ask
from sample_content import load_home_sample_content
from streamlit_ui import (
    build_current_provider_config,
    render_model_banner,
    render_runtime_notice,
    render_section,
    render_sources,
    render_top_nav,
    setup_page,
)


setup_page("导览速览", icon="🧭")
render_top_nav("导览速览")
render_section("导览速览", "适合第一次进入站点时快速浏览问答、展项详情与讲解生成，在几分钟内建立对整站内容的整体印象。")
render_model_banner()

provider_config = build_current_provider_config()
sample = load_home_sample_content()
featured_nodes = get_featured_route_nodes(limit=6)
current_activity = get_activity(st.session_state.get("current_activity_id", ""))

if current_activity:
    st.info(f"当前活动：{current_activity.get('name', '')} · {current_activity.get('mode', '')}")

tab1, tab2, tab3 = st.tabs(["快速问答", "展项预览", "一键讲解"])

with tab1:
    render_section("推荐问题体验", "点击任意问题即可快速体验静态内容底座与 AI 增强回答。")
    question_cols = st.columns(3)
    for index, question in enumerate(get_recommended_questions(limit=6)):
        with question_cols[index % 3]:
            if st.button(question, key=f"quick_try_{index}", use_container_width=True):
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
    render_section("代表性展项预览", "从重点节点中任选一个，查看完整展项详情、语音讲解和互动题入口。")
    preview_cols = st.columns(3)
    for index, node in enumerate(featured_nodes):
        with preview_cols[index % 3]:
            st.markdown(f"**{node.get('title', '')}**")
            st.caption(f"{node.get('date', '')} · {node.get('place', '')}")
            st.write(node.get("summary", ""))
            if st.button("打开该展项", key=f"test_node_{node.get('id')}", use_container_width=True):
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
    render_section("一键讲解", "选择一个主题节点，快速验证讲解生成、依据展示与展项联动效果。")
    topic_node = st.selectbox(
        "选择讲解主题",
        [node.get("id", "") for node in featured_nodes],
        format_func=lambda node_id: next((node.get("title", "") for node in featured_nodes if node.get("id") == node_id), node_id),
    )
    selected_node = get_route_node(topic_node) or {}
    if st.button("生成该节点讲解稿", use_container_width=True, type="primary"):
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
        st.write(guide_result.get("script", ""))
        render_sources(guide_result.get("sources", []), title="本次讲解依据")
        st.markdown("#### 推荐继续体验")
        for node in sample.get("featured_nodes", [])[:3]:
            st.markdown(f"- **{node.get('title', '')}**：{node.get('summary', '')}")
