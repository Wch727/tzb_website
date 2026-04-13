"""知识库页。"""

from __future__ import annotations

import streamlit as st

from game import get_route_node, load_route_nodes
from knowledge_cards import get_knowledge_cards
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


setup_page("知识库", icon="📚")
render_top_nav("知识库")

provider_config = build_current_provider_config()
model_info = get_selected_model_info()
route_nodes = load_route_nodes()
sample = load_home_sample_content()

render_section("红色科普知识库", "这里同时承载图文知识卡片、长征史问答与错题复盘，形成“以题带学”的知识服务闭环。")
render_model_banner()

tab1, tab2, tab3 = st.tabs(["智能问答", "图文知识卡片", "错题复盘"])

with tab1:
    topic_options = get_topic_filter_options()
    current_label = st.session_state.get("selected_topic_label", "综合导览")
    selected_label = st.radio(
        "知识问答主题",
        options=topic_options,
        horizontal=True,
        index=topic_options.index(current_label) if current_label in topic_options else 0,
    )
    st.session_state["selected_topic_label"] = selected_label

    quick_cols = st.columns(2)
    for index, question in enumerate(sample.get("example_questions", [])[:4]):
        with quick_cols[index % 2]:
            if st.button(question, key=f"knowledge_quick_q_{index}", use_container_width=True):
                st.session_state["pending_question"] = question

    messages = st.session_state.get("qa_messages", [])
    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(message.get("content", ""))
            if message["role"] == "assistant":
                if message.get("provider_used") == "static":
                    st.caption(f"当前回答来源：静态知识模式 | 识别意图：{message.get('intent', 'general')}")
                elif message.get("provider_used"):
                    st.caption(
                        f"回答模型：{message.get('provider_used')} / {message.get('model_used', '未标注')} | "
                        f"识别意图：{message.get('intent', 'general')}"
                    )
                render_sources(message.get("sources", []))

    question = st.chat_input("请输入你想了解的长征史问题")
    if st.session_state.get("pending_question") and not question:
        question = st.session_state.pop("pending_question")
    if question:
        st.session_state.setdefault("qa_messages", []).append({"role": "user", "content": question})
        filters = get_filters_by_label(selected_label)
        result = ask(question=question, provider_config=provider_config, filters=filters, top_k=4)
        st.session_state["qa_messages"].append(
            {
                "role": "assistant",
                "content": result.get("answer", ""),
                "sources": result.get("sources", []),
                "provider_used": result.get("provider_used", ""),
                "model_used": result.get("model_used", ""),
                "intent": result.get("intent", "general"),
            }
        )
        st.rerun()

with tab2:
    render_section("图文知识卡片", "内置人物、战役、地点、精神专题和 FAQ 内容，保证无 LLM 条件下也能完整展示。")
    category = st.selectbox("知识分类", ["全部", "路线节点", "重大事件", "重要人物", "重要地点", "长征精神", "常见问答"])
    keyword = st.text_input("关键词搜索", placeholder="例如：遵义、泸定桥、毛泽东")
    cards = get_knowledge_cards(category=category, keyword=keyword)
    if cards:
        card_cols = st.columns(3)
        for index, item in enumerate(cards[:12]):
            with card_cols[index % 3]:
                st.markdown(f"**{item.get('title', item.get('question', ''))}**")
                st.write(item.get("summary", item.get("answer", "")))
                if item.get("id") and st.button("查看节点展项", key=f"knowledge_node_{item.get('id')}", use_container_width=True):
                    st.session_state["selected_node_id"] = item.get("id", "")
                    st.rerun()
    else:
        st.info("没有找到匹配的知识卡片。")

    selected_node_id = st.session_state.get("selected_node_id", route_nodes[0]["id"] if route_nodes else "")
    selected_node = get_route_node(selected_node_id)
    if selected_node:
        render_node_detail(
            node=selected_node,
            provider_config=provider_config,
            audience=st.session_state.get("selected_role_name", "侦察兵"),
            key_prefix="knowledge-node",
        )

with tab3:
    render_section("错题复盘", "错题会自动收录到个人复盘列表，便于在活动结束后继续学习。")
    wrong_book = st.session_state.get("story_state", {}).get("progress", {}).get("wrong_book", [])
    if wrong_book:
        for item in wrong_book:
            with st.expander(item.get("title", "错题"), expanded=False):
                st.write(f"题目：{item.get('question', '')}")
                st.write(f"你的答案：{item.get('selected_answer', '')}")
                st.write(f"正确答案：{item.get('expected_answer', '')}")
                st.write(f"解析：{item.get('explanation', '')}")
    else:
        st.info("当前还没有错题记录。完成剧情答题后，这里会自动显示复盘内容。")

