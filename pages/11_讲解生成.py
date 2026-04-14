"""讲解与脚本生成页。"""

from __future__ import annotations

import streamlit as st

from game import get_route_node, load_route_nodes
from generator import generate_guide_script, generate_short_video_script
from media import render_audio_player, render_digital_human, render_node_image
from streamlit_ui import (
    build_current_provider_config,
    render_model_banner,
    render_runtime_notice,
    render_section,
    render_sources,
    render_top_nav,
    setup_page,
)


setup_page("讲解生成", icon="📝")
render_top_nav("讲解生成")

render_section("讲解与脚本生成", "基于长征史知识库先检索、再生成。结果不仅可阅读，也可直接进行语音播报和数字人讲解展示。")
render_model_banner()

provider_config = build_current_provider_config()
route_nodes = load_route_nodes()

top_col1, top_col2 = st.columns([1.1, 1])
with top_col1:
    selected_node_id = st.selectbox(
        "快速选择一个节点主题",
        [node["id"] for node in route_nodes],
        format_func=lambda node_id: next((node["title"] for node in route_nodes if node["id"] == node_id), node_id),
    )
    selected_node = get_route_node(selected_node_id) or {}
    st.caption(f"已选择：{selected_node.get('title', '')} · {selected_node.get('place', '')}")
with top_col2:
    st.info("你也可以直接手动输入主题，不局限于路线节点。")

preview_left, preview_right = st.columns([1.05, 1.2])
with preview_left:
    if selected_node:
        render_node_image(selected_node, caption=selected_node.get("place", ""))
with preview_right:
    if selected_node:
        background_preview = (selected_node.get("background", "") or "").strip()
        st.markdown(f"### {selected_node.get('title', '')}")
        st.write(selected_node.get("summary", ""))
        st.caption(f"时间：{selected_node.get('date', '未标注')} · 地点：{selected_node.get('place', '未标注')}")
        if selected_node.get("figures"):
            st.caption("关键人物：" + "、".join(selected_node.get("figures", [])))
        if background_preview:
            st.write((background_preview[:180] + "...") if len(background_preview) > 180 else background_preview)

tab1, tab2 = st.tabs(["讲解稿生成", "短视频脚本生成"])

with tab1:
    with st.form("guide_form"):
        topic = st.text_input("讲解主题", value=selected_node.get("title", ""), placeholder="例如：遵义会议的历史意义")
        audience = st.selectbox("受众对象", ["大学生", "研学团成员", "普通参观者"])
        duration = st.selectbox("讲解时长", ["2分钟", "3分钟", "5分钟"])
        submitted = st.form_submit_button("生成讲解稿", use_container_width=True, type="primary")

    if submitted and topic.strip():
        with st.spinner("正在检索资料并生成讲解稿..."):
            result = generate_guide_script(
                topic=topic,
                audience=audience,
                duration=duration,
                provider_config=provider_config,
            )
        st.session_state["guide_page_result"] = result
        st.session_state["guide_page_topic"] = topic

    result = st.session_state.get("guide_page_result")
    if result:
        render_runtime_notice(result)
        st.markdown("#### 讲解稿结果")
        st.write(result.get("script", ""))
        audio_path = render_audio_player(
            text=result.get("script", ""),
            cache_key=f"guide-page-{st.session_state.get('guide_page_topic', 'topic')}",
            button_label="播放讲解稿语音",
        )
        if st.button("数字人讲解模式", key="guide_digital", use_container_width=True):
            st.session_state["guide_digital_mode"] = not st.session_state.get("guide_digital_mode", False)
        if st.session_state.get("guide_digital_mode", False):
            render_digital_human(
                section_text=result.get("script", ""),
                avatar_path=selected_node.get("avatar", "assets/avatar/guide.svg"),
                audio_path=audio_path,
            )
        render_sources(result.get("sources", []), title="本次讲解稿使用的知识片段")

with tab2:
    with st.form("video_form"):
        topic = st.text_input("脚本主题", value=selected_node.get("title", ""), placeholder="例如：飞夺泸定桥")
        audience = st.selectbox("目标受众", ["大学生", "研学团成员", "普通参观者"], key="video_audience")
        style = st.selectbox("呈现风格", ["正式讲述", "历史叙事", "青年宣讲"])
        submitted = st.form_submit_button("生成短视频脚本", use_container_width=True)

    if submitted and topic.strip():
        with st.spinner("正在检索资料并生成短视频脚本..."):
            result = generate_short_video_script(
                topic=topic,
                audience=audience,
                style=style,
                provider_config=provider_config,
            )
        st.session_state["video_page_result"] = result
        st.session_state["video_page_topic"] = topic

    result = st.session_state.get("video_page_result")
    if result:
        render_runtime_notice(result)
        st.markdown("#### 短视频脚本结果")
        st.write(result.get("script", ""))
        audio_path = render_audio_player(
            text=result.get("script", ""),
            cache_key=f"video-page-{st.session_state.get('video_page_topic', 'topic')}",
            button_label="播放脚本文案语音",
        )
        if st.button("切换数字讲解员模式", key="video_digital", use_container_width=True):
            st.session_state["video_digital_mode"] = not st.session_state.get("video_digital_mode", False)
        if st.session_state.get("video_digital_mode", False):
            render_digital_human(
                section_text=result.get("script", ""),
                avatar_path=selected_node.get("avatar", "assets/avatar/guide.svg"),
                audio_path=audio_path,
            )
        render_sources(result.get("sources", []), title="本次脚本使用的知识片段")
