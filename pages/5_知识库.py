"""知识库页。"""

from __future__ import annotations

import streamlit as st

from content_store import build_node_related_questions, get_node_extended_reading, get_recommended_questions
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


setup_page("知识百问", icon="📚")
render_top_nav("知识百问")

provider_config = build_current_provider_config()
model_info = get_selected_model_info()
route_nodes = load_route_nodes()
sample = load_home_sample_content()

render_section("长征百问", "把推荐问题、节点相关问题、问答依据和延伸阅读放在同一页中，形成更强的学习闭环。")
render_model_banner()

tab1, tab2, tab3 = st.tabs(["智能导览问答", "图文知识卡片", "学习复盘"])

with tab1:
    topic_options = get_topic_filter_options()
    current_label = st.session_state.get("selected_topic_label", "综合导览")
    selected_label = st.radio(
        "问答主题",
        options=topic_options,
        horizontal=True,
        index=topic_options.index(current_label) if current_label in topic_options else 0,
    )
    st.session_state["selected_topic_label"] = selected_label

    selected_node_id = st.session_state.get("selected_node_id", route_nodes[0]["id"] if route_nodes else "")
    selected_node = get_route_node(selected_node_id) if selected_node_id else None

    quick_left, quick_right = st.columns([1, 1])
    with quick_left:
        render_section("推荐问题", "从高频问题开始进入长征知识脉络。")
        for index, question in enumerate(get_recommended_questions(limit=6)):
            if st.button(question, key=f"knowledge_hot_{index}", width="stretch"):
                st.session_state["pending_question"] = question
    with quick_right:
        render_section("节点相关问题", "当你已经在浏览某个节点时，可以沿着该节点继续发问。")
        if selected_node:
            for index, question in enumerate(build_node_related_questions(selected_node, limit=4)):
                if st.button(question, key=f"knowledge_node_q_{index}", width="stretch"):
                    st.session_state["pending_question"] = question
        else:
            st.info("先从路线页选择一个节点，这里会自动出现该节点的相关追问。")

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
                render_sources(message.get("sources", []), title="本次回答依据")
                if message.get("extended_reading"):
                    st.markdown("#### 延伸阅读")
                    for item in message.get("extended_reading", []):
                        st.markdown(f"- **{item.get('title', item.get('question', ''))}**：{item.get('summary', item.get('answer', ''))}")

    question = st.chat_input("请输入你想进一步了解的长征史问题")
    if st.session_state.get("pending_question") and not question:
        question = st.session_state.pop("pending_question")
    if question:
        st.session_state.setdefault("qa_messages", []).append({"role": "user", "content": question})
        filters = get_filters_by_label(selected_label)
        result = ask(question=question, provider_config=provider_config, filters=filters, top_k=4)
        matched_node = get_route_node(st.session_state.get("selected_node_id", "")) if st.session_state.get("selected_node_id") else None
        extended_reading = get_node_extended_reading(matched_node, limit=4) if matched_node else []
        st.session_state["qa_messages"].append(
            {
                "role": "assistant",
                "content": result.get("answer", ""),
                "sources": result.get("sources", []),
                "provider_used": result.get("provider_used", ""),
                "model_used": result.get("model_used", ""),
                "intent": result.get("intent", "general"),
                "extended_reading": extended_reading,
            }
        )
        st.rerun()

with tab2:
    render_section("图文知识卡片", "内置人物、事件、地点、精神专题和常见问答内容，即使不启用模型也能完成完整学习。")
    category = st.selectbox("知识分类", ["全部", "路线节点", "重大事件", "重要人物", "重要地点", "长征精神", "常见问答"])
    keyword = st.text_input("关键词搜索", placeholder="例如：遵义、泸定桥、毛泽东")
    cards = get_knowledge_cards(category=category, keyword=keyword)
    if cards:
        card_cols = st.columns(3)
        for index, item in enumerate(cards[:12]):
            with card_cols[index % 3]:
                st.markdown(f"**{item.get('title', item.get('question', ''))}**")
                st.write(item.get("summary", item.get("answer", "")))
                if item.get("id") and st.button("查看展项", key=f"knowledge_node_{item.get('id')}", width="stretch"):
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
            audience=st.session_state.get("selected_role_name", "大学生"),
            key_prefix="knowledge-node",
        )

with tab3:
    render_section("学习复盘", "把作答中的薄弱点重新拉回到知识理解上，而不是只留下对错结果。")
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
