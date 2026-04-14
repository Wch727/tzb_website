"""人物专题页。"""

from __future__ import annotations

import streamlit as st

from content_store import (
    build_figure_story_script,
    get_figure_data,
    get_related_nodes_for_figure,
    load_figures_data,
)
from media import render_node_image
from streamlit_ui import (
    render_curatorial_note,
    render_detail_panels,
    render_gallery_frame,
    render_ledger_cards,
    render_section,
    render_top_nav,
    setup_page,
)


def _jump_to_node(node_id: str) -> None:
    """跳转到主线节点。"""
    st.session_state["selected_node_id"] = node_id
    st.switch_page("pages/3_长征路线.py")


setup_page("人物专题", icon="🧑")
render_top_nav("人物专题")

all_figures = load_figures_data()
figure_names = [item.get("title", "") for item in all_figures if item.get("title")]
selected_name = st.session_state.get("selected_figure_name", figure_names[0] if figure_names else "")
if selected_name not in figure_names and figure_names:
    selected_name = figure_names[0]
    st.session_state["selected_figure_name"] = selected_name

selected_name = st.selectbox("选择人物专题", figure_names, index=figure_names.index(selected_name) if selected_name in figure_names else 0)
st.session_state["selected_figure_name"] = selected_name
figure = get_figure_data(selected_name) or {}
related_nodes = get_related_nodes_for_figure(figure, limit=4)
story_script = build_figure_story_script(figure)

render_gallery_frame("人物专题展区", "人物专题页以正式讲解、长征角色、历史贡献和官方资料来源为核心，便于课堂说明和专题讲述。")

hero_left, hero_right = st.columns([0.92, 1.18])
with hero_left:
    render_node_image(figure, caption=figure.get("image_caption", "") or figure.get("role", "重要人物"))
with hero_right:
    st.markdown(f"## {figure.get('title', '重要人物')}")
    st.caption(figure.get("role", "重要人物"))
    render_curatorial_note(
        title=f"{figure.get('title', '人物')}专题说明",
        body=figure.get("summary", "本页围绕人物经历、长征角色和历史贡献组织专题介绍。"),
        label="人物导语",
    )

render_ledger_cards(
    [
        {"label": "人物身份", "title": figure.get("role", "重要人物"), "desc": "从人物身份进入其在党史与长征史中的位置。"},
        {"label": "关联节点", "title": figure.get("route_stage", "主线相关"), "desc": "通过代表性节点回看人物在线路中的实际作用。"},
        {"label": "资料依据", "title": "官方党史与党媒资料", "desc": "专题文字依据中国共产党新闻网、人民网党史频道等公开资料整理。"},
    ]
)

render_section("人物正式讲解稿", "本页默认展示可直接讲述的人物讲解稿，不依赖现场生成。")
st.write(story_script)

render_section("专题信息板", "从人物经历、长征角色与历史贡献三个维度理解该人物。")
render_detail_panels(
    [
        {"title": "人物经历与历史背景", "desc": figure.get("background", "暂无补充说明。")},
        {"title": "长征中的作用", "desc": figure.get("long_march_role", figure.get("summary", "暂无补充说明。"))},
        {"title": "历史贡献", "desc": figure.get("significance", "暂无补充说明。")},
    ]
)

render_section("官方资料来源", "以下链接用于说明专题页面整理所依据的官方公开资料来源。")
sources = figure.get("official_sources", []) or []
if sources:
    for item in sources:
        title = item.get("title", "官方来源")
        url = item.get("url", "")
        publisher = item.get("publisher", "官方资料")
        if url:
            st.markdown(f"- [{title}]({url})  \n  来源：{publisher}")
        else:
            st.markdown(f"- {title}  \n  来源：{publisher}")
else:
    st.info("当前人物暂未配置官方资料来源链接。")

if related_nodes:
    render_section("相关长征节点", "从人物回到主线节点，更容易把人物作用放回具体历史情境中理解。")
    node_cols = st.columns(min(4, len(related_nodes)))
    for index, node in enumerate(related_nodes):
        with node_cols[index % len(node_cols)]:
            render_node_image(node, caption=node.get("place", ""))
            st.markdown(f"**{node.get('title', '')}**")
            st.caption(f"{node.get('date', '')} · {node.get('place', '')}")
            st.write(node.get("summary", ""))
            if st.button("查看相关节点", key=f"figure_node_{figure.get('title', '')}_{node.get('id', '')}", width="stretch"):
                _jump_to_node(node.get("id", ""))
