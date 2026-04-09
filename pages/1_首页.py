"""产品首页。"""

from __future__ import annotations

import streamlit as st

from game import load_route_nodes
from media import render_node_image
from rag import get_rag_status
from sample_content import load_home_sample_content
from streamlit_ui import render_cards, render_hero, render_metrics, render_section, render_top_nav, setup_page
from utils import get_visible_user_models


def _jump_to_node(node_id: str) -> None:
    """记录用户想查看的节点并跳转。"""
    st.session_state["selected_node_id"] = node_id
    st.switch_page("pages/2_智能导览.py")


setup_page("首页", icon="🏔️")
render_top_nav("首页")

status = get_rag_status()
models = get_visible_user_models()
sample = load_home_sample_content()
all_nodes = load_route_nodes()

render_hero(
    title="《长征史》交互式 AI 导览系统",
    subtitle=(
        "这是一个“图文音结合”的长征史学习产品。"
        "系统将路线探索、知识问答、讲解生成、语音播报、数字人讲解与互动闯关整合为一体。"
    ),
    badges=["图文音结合", "RAG 导览", "多模型接入", "智能讲解"],
)

hero_col1, hero_col2, hero_col3, hero_col4 = st.columns([1.1, 1.1, 1, 1])
with hero_col1:
    if st.button("开始智能导览", use_container_width=True, type="primary"):
        st.switch_page("pages/2_智能导览.py")
with hero_col2:
    if st.button("进入长征闯关", use_container_width=True):
        st.switch_page("pages/4_长征闯关.py")
with hero_col3:
    if st.button("测试体验", use_container_width=True):
        st.switch_page("pages/7_测试体验.py")
with hero_col4:
    if st.button("前往配置页", use_container_width=True):
        st.switch_page("pages/5_配置页.py")

render_metrics(
    [
        {"label": "知识条目数", "value": status.get("document_count", 0)},
        {"label": "Chunk 数量", "value": status.get("chunk_count", 0)},
        {"label": "开放模型数", "value": len(models)},
        {"label": "核心节点", "value": len(all_nodes)},
    ]
)

render_section("长征路线总览", "把路线图、时间轴与推荐节点放在同一页面，帮助用户快速建立对长征全程的整体认识。")
overview_left, overview_right = st.columns([1.05, 1])
with overview_left:
    render_node_image(
        {
            "title": "长征路线总览",
            "image": sample.get("hero_route_map", "assets/images/changzheng_route_map.jpg"),
            "place": "从瑞金到会宁的战略转移路线",
        },
        caption="长征路线图示意",
    )
with overview_right:
    st.markdown("### 今日推荐学习路线")
    for route in sample.get("recommended_route", []):
        st.markdown(f"- {route}")
    st.markdown("### 路线特点")
    st.write("从中央苏区出发，到遵义实现转折，再到雪山草地中的坚韧行军，最终在西北实现胜利会师。")

timeline_cards = [
    {
        "label": node.get("date", "未标注"),
        "title": node.get("title", ""),
        "desc": f"{node.get('place', '')} · {node.get('summary', '')[:42]}",
    }
    for node in sample.get("timeline_nodes", all_nodes)
]
render_cards(timeline_cards, timeline=True)

render_section("热门长征节点推荐", "从关键节点进入展项式浏览，每个节点都支持图文、讲解稿、短视频脚本与互动答题。")
node_cols = st.columns(3)
for index, node in enumerate(sample.get("featured_nodes", [])):
    with node_cols[index % 3]:
        render_node_image(node, caption=node.get("place", ""))
        st.markdown(f"#### {node.get('title', '')}")
        st.caption(f"{node.get('date', '')} · {node.get('place', '')}")
        st.write(node.get("summary", ""))
        if st.button("查看节点详情", key=f"home_node_{node.get('id')}", use_container_width=True):
            _jump_to_node(node.get("id", ""))

render_section("长征精神专题", "把事件、路线与精神主题结合起来，突出思政教育与历史阐释价值。")
spirit_cols = st.columns(3)
for index, item in enumerate(sample.get("spirit_topics", [])):
    with spirit_cols[index % 3]:
        st.markdown(f"### {item.get('title', '')}")
        st.write(item.get("summary", ""))

tab1, tab2, tab3, tab4 = st.tabs(["示例问题推荐", "示例讲解稿", "示例短视频脚本", "学习路线建议"])
with tab1:
    for question in sample.get("example_questions", []):
        st.markdown(f"- {question}")

with tab2:
    st.markdown("#### 示例讲解稿展示")
    st.write(sample.get("example_guide_script", ""))

with tab3:
    st.markdown("#### 示例短视频脚本展示")
    st.code(sample.get("example_video_script", ""), language="markdown")

with tab4:
    for route in sample.get("recommended_route", []):
        st.markdown(f"- {route}")

render_section("重点人物卡片", "通过人物视角理解长征中的组织、决策与精神力量。")
figure_cols = st.columns(3)
for index, item in enumerate(sample.get("figure_cards", [])):
    with figure_cols[index % 3]:
        st.markdown(f"#### {item.get('title', '')}")
        st.caption(item.get("role", "重要人物"))
        st.write(item.get("summary", ""))

render_section("关键事件卡片", "首页保留高密度内容展示，避免页面空荡，适合比赛答辩快速扫读。")
event_cols = st.columns(3)
for index, item in enumerate(sample.get("event_cards", [])):
    with event_cols[index % 3]:
        st.markdown(f"#### {item.get('title', '')}")
        st.caption(item.get("place", ""))
        st.write(item.get("summary", ""))
