"""给组员快速试用的测试体验页。"""

from __future__ import annotations

import streamlit as st

from activity_manager import get_activity
from game import get_route_node, load_route_nodes
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


setup_page("测试体验", icon="🧪")
render_top_nav("测试体验")
render_section("测试体验", "这一页适合直接发给组员试用：既能快速提问，也能预览节点、活动与讲解生成效果。")
render_model_banner()

provider_config = build_current_provider_config()
sample = load_home_sample_content()
route_nodes = load_route_nodes()
current_activity = get_activity(st.session_state.get("current_activity_id", ""))

if current_activity:
    st.info(f"当前活动：{current_activity.get('name', '')} · {current_activity.get('mode', '')}")

tab1, tab2, tab3 = st.tabs(["一键提问", "节点速览", "一键生成讲解稿"])

with tab1:
    render_section("试用问题", "点击下方按钮即可快速体验知识问答和依据展示。")
    quick_questions = sample.get("quick_try_questions") or sample.get("example_questions", [])[:3]
    cols = st.columns(3)
    for index, question in enumerate(quick_questions[:3]):
        with cols[index % 3]:
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
    render_section("节点速览", "选择一个节点，快速查看图文、人物、讲解与互动入口。")
    selected_node_id = st.selectbox(
        "选择节点",
        [node["id"] for node in route_nodes],
        format_func=lambda node_id: next((node["title"] for node in route_nodes if node["id"] == node_id), node_id),
    )
    selected_node = get_route_node(selected_node_id)
    if selected_node:
        render_node_detail(
            node=selected_node,
            provider_config=provider_config,
            audience=st.session_state.get("selected_role_name", "侦察兵"),
            key_prefix="test-page-node",
        )
        if st.button("从该节点进入剧情答题", use_container_width=True, key="jump_story_from_test"):
            st.session_state["selected_node_id"] = selected_node_id
            st.switch_page("pages/4_剧情答题.py")

with tab3:
    render_section("一键生成讲解稿", "适合快速验证讲解生成是否可用。")
    selected_node_id = st.selectbox(
        "选择讲解主题",
        [node["id"] for node in route_nodes],
        key="test_page_topic",
        format_func=lambda node_id: next((node["title"] for node in route_nodes if node["id"] == node_id), node_id),
    )
    selected_node = get_route_node(selected_node_id) or {}
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
        render_sources(guide_result.get("sources", []), title="本次讲解稿依据")
        st.markdown("#### 继续体验推荐")
        for item in sample.get("featured_nodes", [])[:3]:
            st.markdown(f"- {item.get('title', '')}：{item.get('summary', '')}")
