"""智能导览页。"""

from __future__ import annotations

import streamlit as st

from game import get_route_node, load_route_nodes
from node_detail import render_node_detail
from rag import ask
from sample_content import load_home_sample_content
from streamlit_ui import (
    build_current_provider_config,
    get_filters_by_label,
    get_selected_model_info,
    get_topic_filter_options,
    render_model_banner,
    render_runtime_notice,
    render_section,
    render_sources,
    render_top_nav,
    setup_page,
)


setup_page("智能导览", icon="🗺️")
render_top_nav("智能导览")

provider_config = build_current_provider_config()
model_info = get_selected_model_info()
route_nodes = load_route_nodes()
sample = load_home_sample_content()

render_section("智能导览", "你可以直接提问，也可以点击路线节点进入展项式导览。问答、节点详情、讲解稿和短视频脚本都会显式展示知识依据。")
render_model_banner()

topic_options = get_topic_filter_options()
current_label = st.session_state.get("selected_topic_label", "综合导览")
selected_label = st.radio(
    "选择导览主题",
    options=topic_options,
    horizontal=True,
    index=topic_options.index(current_label) if current_label in topic_options else 0,
)
st.session_state["selected_topic_label"] = selected_label

left, right = st.columns([1.45, 1])
with left:
    quick_cols = st.columns(2)
    for index, question in enumerate(sample.get("example_questions", [])[:4]):
        with quick_cols[index % 2]:
            if st.button(question, key=f"quick_q_{index}", use_container_width=True):
                st.session_state["pending_question"] = question

    messages = st.session_state.get("qa_messages", [])
    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(message.get("content", ""))
            if message["role"] == "assistant":
                if message.get("provider_used"):
                    if message.get("provider_used") == "static":
                        st.caption(f"当前回答来源：静态知识模式 | 识别意图：{message.get('intent', 'general')}")
                    else:
                        st.caption(
                            f"回答模型：{message.get('provider_used')} / {message.get('model_used', '未标注')} | "
                            f"识别意图：{message.get('intent', 'general')}"
                        )
                if message.get("warning"):
                    st.warning(message["warning"])
                render_sources(message.get("sources", []))

    question = st.chat_input("请输入你想了解的长征史问题")
    if st.session_state.get("pending_question") and not question:
        question = st.session_state.pop("pending_question")

    if question:
        st.session_state.setdefault("qa_messages", []).append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        filters = get_filters_by_label(selected_label)
        with st.chat_message("assistant"):
            with st.spinner("正在整理资料并生成讲解..."):
                result = ask(question=question, provider_config=provider_config, filters=filters, top_k=4)
            render_runtime_notice(result)
            st.markdown(result.get("answer", ""))
            if result.get("provider_used") == "static":
                st.caption(f"当前回答来源：静态知识模式 | 识别意图：{result.get('intent', 'general')}")
            else:
                st.caption(
                    f"回答模型：{result.get('provider_used', model_info.get('provider_name', 'mock'))} / "
                    f"{result.get('model_used', model_info.get('model', ''))} | "
                    f"识别意图：{result.get('intent', 'general')}"
                )
            render_sources(result.get("sources", []))

        st.session_state["qa_messages"].append(
            {
                "role": "assistant",
                "content": result.get("answer", ""),
                "sources": result.get("sources", []),
                "warning": result.get("warning", ""),
                "provider_used": result.get("provider_used", ""),
                "model_used": result.get("model_used", ""),
                "intent": result.get("intent", "general"),
            }
        )

with right:
    st.markdown("### 热门节点导览")
    option_ids = [node["id"] for node in route_nodes]
    selected_node_id = st.session_state.get("selected_node_id", option_ids[0] if option_ids else "")
    if selected_node_id not in option_ids and option_ids:
        selected_node_id = option_ids[0]
    selected_node_id = st.selectbox(
        "选择一个长征节点",
        option_ids,
        index=option_ids.index(selected_node_id) if selected_node_id in option_ids else 0,
        format_func=lambda node_id: next((node["title"] for node in route_nodes if node["id"] == node_id), node_id),
    )
    st.session_state["selected_node_id"] = selected_node_id

    for item in sample.get("featured_nodes", [])[:5]:
        st.markdown(f"**{item.get('title', '')}**")
        st.caption(item.get("summary", ""))
    st.markdown("### 示例问题")
    for item in sample.get("example_questions", [])[:4]:
        st.markdown(f"- {item}")

render_section("节点展项详情", "点击节点后，将以“展项”方式展示时间、地点、背景、经过、意义、人物、图片、语音与数字人讲解。")
selected_node = get_route_node(st.session_state.get("selected_node_id", ""))
if selected_node:
    render_node_detail(
        node=selected_node,
        provider_config=provider_config,
        audience=st.session_state.get("user_role", "大学生"),
        key_prefix="guide-node",
    )
