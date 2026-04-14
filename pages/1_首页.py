"""产品首页。"""

from __future__ import annotations

import streamlit as st

from content_store import get_route_chapters
from media import render_node_image
from rag import get_rag_status
from sample_content import load_home_sample_content
from streamlit_ui import render_hero, render_metrics, render_section, render_top_nav, setup_page
from utils import get_visible_user_models


def _jump_to_node(node_id: str) -> None:
    """记录用户想查看的节点并跳转。"""
    st.session_state["selected_node_id"] = node_id
    st.switch_page("pages/3_长征路线.py")


setup_page("首页", icon="🏛️")
render_top_nav("首页")

status = get_rag_status()
models = get_visible_user_models()
sample = load_home_sample_content()
chapters = get_route_chapters()
total_nodes = sum(len(item.get("nodes", [])) for item in chapters)

render_hero(
    title="《长征史》交互式导览与闯关学习系统",
    subtitle=(
        "以长征主线为展陈骨架，把路线导览、知识百问、讲解生成与互动答题组织成一个可浏览、可学习、可参与的线上主题展。"
    ),
    badges=["主线导览", "展项浏览", "知识百问", "互动闯关", "图文音一体"],
)

hero_left, hero_right, hero_more = st.columns([1.15, 1.15, 0.9])
with hero_left:
    if st.button("开始长征导览", use_container_width=True, type="primary"):
        st.switch_page("pages/3_长征路线.py")
with hero_right:
    if st.button("进入互动闯关", use_container_width=True):
        st.switch_page("pages/4_剧情答题.py")
with hero_more:
    if st.button("测试体验入口", use_container_width=True):
        st.switch_page("pages/10_测试体验.py")

render_metrics(
    [
        {"label": "主线节点", "value": total_nodes},
        {"label": "知识切片", "value": status.get("chunk_count", 0)},
        {"label": "开放模型", "value": len(models)},
        {"label": "展陈篇章", "value": len(chapters)},
    ]
)

render_section("长征主线推荐", "从关键转折点进入主展内容，先把整条征程的历史逻辑建立起来。")
featured_nodes = sample.get("featured_nodes", [])
feature_cols = st.columns(3)
for index, node in enumerate(featured_nodes):
    with feature_cols[index % 3]:
        render_node_image(node, caption=node.get("image_caption", "") or node.get("place", ""))
        st.markdown(f"#### {node.get('title', '')}")
        st.caption(f"{node.get('date', '')} · {node.get('place', '')}")
        st.write(node.get("summary", ""))
        if st.button("查看详情", key=f"home_featured_{node.get('id')}", use_container_width=True):
            _jump_to_node(node.get("id", ""))

render_section("长征路线总览", "把路线拆成四个篇章，每一篇都像独立展区，帮助用户形成清晰的征程感。")
chapter_cols = st.columns(4)
for index, chapter in enumerate(chapters):
    with chapter_cols[index % 4]:
        st.markdown(f"### {chapter.get('title', '')}")
        st.caption(chapter.get("subtitle", ""))
        for node in chapter.get("nodes", [])[:3]:
            st.markdown(f"- **{node.get('title', '')}**：{node.get('summary', '')[:34]}...")
        if st.button("进入本篇章", key=f"home_chapter_{chapter.get('id')}", use_container_width=True):
            st.session_state["selected_chapter_id"] = chapter.get("id", "")
            st.switch_page("pages/3_长征路线.py")

route_left, route_right = st.columns([1.15, 0.95])
with route_left:
    render_node_image(
        {
            "title": "长征路线总览",
            "image": sample.get("hero_route_map", "assets/images/changzheng_route_map.jpg"),
            "place": "从瑞金出发到会宁会师的长征路线",
            "type": "route",
        },
        caption="长征路线总览",
    )
with route_right:
    st.markdown("### 推荐学习路线")
    for item in sample.get("recommended_learning_paths", [])[:4]:
        st.markdown(f"- {item}")
    st.markdown("### 今日推荐路线")
    for item in sample.get("recommended_route", [])[:4]:
        st.markdown(f"- {item}")

render_section("重要人物", "以人物视角进入长征历史，更容易理解决策、组织与行动之间的关系。")
figure_cols = st.columns(3)
for index, item in enumerate(sample.get("figure_cards", [])[:6]):
    with figure_cols[index % 3]:
        render_node_image(item, caption=item.get("role", "重要人物"))
        st.markdown(f"#### {item.get('title', '')}")
        st.caption(item.get("role", "重要人物"))
        st.write(item.get("summary", ""))

render_section("长征精神专题", "把路线、事件与精神内涵联系起来，形成更完整的学习纵深。")
spirit_cols = st.columns(3)
for index, item in enumerate(sample.get("spirit_topics", [])[:6]):
    with spirit_cols[index % 3]:
        st.markdown(f"### {item.get('title', '')}")
        st.write(item.get("summary", ""))

render_section("推荐学习内容", "首页不仅是入口页，也承担导学作用，帮助用户快速进入问答、讲解与学习延伸。")
tab1, tab2, tab3, tab4 = st.tabs(["推荐问题", "示例讲解稿", "推荐学习路线", "测试体验"])
with tab1:
    for question in sample.get("example_questions", [])[:8]:
        st.markdown(f"- {question}")
with tab2:
    st.write(sample.get("example_guide_script", ""))
with tab3:
    for item in sample.get("recommended_nodes_by_stage", []):
        st.markdown(f"**{item.get('title', '')}**")
        st.caption(item.get("subtitle", ""))
        for node in item.get("nodes", [])[:3]:
            st.markdown(f"- {node.get('title', '')}")
with tab4:
    st.write("适合快速演示问答、展项浏览、讲解生成与互动闯关的组合体验。")
    if st.button("进入测试体验页", key="home_try_page", use_container_width=True):
        st.switch_page("pages/10_测试体验.py")
