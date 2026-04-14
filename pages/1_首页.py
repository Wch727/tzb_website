"""产品首页。"""

from __future__ import annotations

import streamlit as st

from activity_manager import list_activities
from game import load_route_nodes
from leaderboard import get_global_leaderboard
from media import render_node_image
from rag import get_rag_status
from role_system import list_roles
from sample_content import load_home_sample_content
from streamlit_ui import render_cards, render_hero, render_metrics, render_section, render_top_nav, setup_page
from team_manager import get_branch_pk_board, get_team_leaderboard
from utils import get_visible_user_models


def _jump_to_node(node_id: str) -> None:
    """记录用户想查看的节点并跳转。"""
    st.session_state["selected_node_id"] = node_id
    st.switch_page("pages/3_长征路线.py")


setup_page("首页", icon="🏔️")
render_top_nav("首页")

status = get_rag_status()
models = get_visible_user_models()
sample = load_home_sample_content()
all_nodes = load_route_nodes()
activities = list_activities()
roles = list_roles()
leaderboard_rows = get_global_leaderboard(limit=5)
team_preview_rows = get_team_leaderboard(limit=3)
branch_preview_rows = get_branch_pk_board(limit=3)

render_hero(
    title="《长征精神·沉浸式云端答题互动平台》",
    subtitle=(
        "平台围绕长征主线关卡、角色扮演、多媒体答题、知识库学习、活动组织与排行榜反馈构建完整闭环，"
        "既可作为红色教育互动平台进行展示，也可用于主题竞赛、研学任务和课堂活动。"
    ),
    badges=["主线关卡", "角色扮演", "多媒体答题", "活动中心", "排行榜"],
)

hero_col1, hero_col2, hero_col3, hero_col4, hero_col5 = st.columns([1.1, 1.1, 1, 1, 1])
with hero_col1:
    if st.button("选择角色并开始", use_container_width=True, type="primary"):
        st.switch_page("pages/2_角色选择.py")
with hero_col2:
    if st.button("进入主线关卡", use_container_width=True):
        st.switch_page("pages/3_长征路线.py")
with hero_col3:
    if st.button("打开活动中心", use_container_width=True):
        st.switch_page("pages/6_活动中心.py")
with hero_col4:
    if st.button("查看实时排行", use_container_width=True):
        st.switch_page("pages/7_排行榜.py")
with hero_col5:
    if st.button("打开数据大屏", use_container_width=True):
        st.switch_page("pages/12_数据大屏.py")

render_metrics(
    [
        {"label": "知识条目数", "value": status.get("document_count", 0)},
        {"label": "Chunk 数量", "value": status.get("chunk_count", 0)},
        {"label": "开放模型数", "value": len(models)},
        {"label": "主线节点数", "value": len(all_nodes)},
    ]
)

render_section("平台定位", "首页直接呈现商业计划书承诺的核心能力，避免老师打开后只看到空页面或零散工具入口。")
render_cards(
    [
        {
            "label": "产品价值",
            "title": "红色教育互动化",
            "desc": "以长征主线为骨架，把历史导览、知识学习、答题闯关和活动组织整合到同一平台。",
        },
        {
            "label": "核心体验",
            "title": "重走长征路",
            "desc": "用户从角色选择出发，沿着长征时间线逐关推进，在剧情导入中完成多媒体答题和知识延伸。",
        },
        {
            "label": "组织能力",
            "title": "活动化运营",
            "desc": "支持知识竞赛、党史学习日、红色研学任务等活动模板，并可生成分享链接和二维码。",
        },
        {
            "label": "后台能力",
            "title": "可维护可更新",
            "desc": "管理员可以维护题目内容、活动配置、知识库索引与模型开放策略，适合持续运营与展示。",
        },
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
    if sample.get("recommended_learning_paths"):
        st.markdown("### 推荐学习路径")
        for item in sample.get("recommended_learning_paths", [])[:4]:
            st.markdown(f"- {item}")

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
node_cols = st.columns(4)
for index, node in enumerate(sample.get("featured_nodes", [])):
    with node_cols[index % 4]:
        render_node_image(node, caption=node.get("place", ""))
        st.markdown(f"#### {node.get('title', '')}")
        st.caption(f"{node.get('date', '')} · {node.get('place', '')}")
        st.write(node.get("summary", ""))
        if st.button("查看节点详情", key=f"home_node_{node.get('id')}", use_container_width=True):
            _jump_to_node(node.get("id", ""))

render_section("示例角色与任务身份", "角色系统不是装饰，而是主线关卡中的任务提示与奖励加成入口。")
role_cards = [
    {
        "label": item.get("title", ""),
        "title": item.get("name", ""),
        "desc": f"{item.get('tagline', '')} {item.get('bonus_text', '')}",
    }
    for item in roles
]
render_cards(role_cards)

render_section("示例活动与组织场景", "平台可承载知识竞赛、党史学习日和红色研学任务等活动模板。")
activity_cards = [
    {
        "label": item.get("mode", ""),
        "title": item.get("name", ""),
        "desc": f"{item.get('description', '')} 活动时长：{item.get('time_range', '')}。",
    }
    for item in activities[:3]
]
render_cards(activity_cards)
activity_cols = st.columns(3)
for index, item in enumerate(activities[:3]):
    with activity_cols[index % 3]:
        if st.button(f"进入 {item.get('name', '')}", key=f"activity_home_{item.get('activity_id')}", use_container_width=True):
            st.session_state["current_activity_id"] = item.get("activity_id", "")
            st.switch_page("pages/6_活动中心.py")

render_section("红军小队与支部PK预览", "平台已经支持创建红军小队、团队协作答题、支部PK对抗和班级/单位排名展示。")
preview_left, preview_right = st.columns(2)
with preview_left:
    st.markdown("### 红军小队榜前列")
    if team_preview_rows:
        for item in team_preview_rows:
            st.markdown(
                f"{item.get('rank', 0)}. **{item.get('team_name', '')}** | "
                f"{item.get('branch_name', '')} | 总分 {item.get('total_score', 0)}"
            )
    else:
        st.info("当前暂无小队数据，进入活动中心即可创建。")
with preview_right:
    st.markdown("### 支部PK榜前列")
    if branch_preview_rows:
        for item in branch_preview_rows:
            st.markdown(
                f"{item.get('rank', 0)}. **{item.get('branch_name', '')}** | "
                f"总分 {item.get('total_score', 0)} | 小队数 {item.get('team_count', 0)}"
            )
    else:
        st.info("当前暂无支部PK数据，完成小队协作答题后将自动生成。")

render_section("长征精神专题", "把事件、路线与精神主题结合起来，突出思政教育与历史阐释价值。")
spirit_cols = st.columns(3)
for index, item in enumerate(sample.get("spirit_topics", [])):
    with spirit_cols[index % 3]:
        st.markdown(f"### {item.get('title', '')}")
        st.write(item.get("summary", ""))

tab1, tab2, tab3, tab4 = st.tabs(["示例问题推荐", "示例讲解稿", "示例短视频脚本", "推荐排行榜预览"])
with tab1:
    for question in sample.get("example_questions", []):
        st.markdown(f"- {question}")
    if sample.get("featured_faqs"):
        st.markdown("#### 高频问答")
        for item in sample.get("featured_faqs", [])[:4]:
            st.markdown(f"- **{item.get('question', item.get('title', ''))}**：{item.get('answer', '')}")

with tab2:
    st.markdown("#### 示例讲解稿展示")
    st.write(sample.get("example_guide_script", ""))

with tab3:
    st.markdown("#### 示例短视频脚本展示")
    st.code(sample.get("example_video_script", ""), language="markdown")

with tab4:
    if leaderboard_rows:
        for item in leaderboard_rows:
            st.markdown(
                f"{item.get('rank', 0)}. **{item.get('user_name', '')}** · "
                f"{item.get('activity_name', '')} · {item.get('score', 0)} 分 · {item.get('rank_title', '')}"
            )
    else:
        st.info("当前还没有真实战绩记录。完成一次剧情答题后，这里会自动生成排行榜数据。")

render_section("重点人物卡片", "通过人物视角理解长征中的组织、决策与精神力量。")
figure_cols = st.columns(4)
for index, item in enumerate(sample.get("figure_cards", [])):
    with figure_cols[index % 4]:
        render_node_image(item, caption=item.get("role", "重要人物"))
        st.markdown(f"#### {item.get('title', '')}")
        st.caption(item.get("role", "重要人物"))
        st.write(item.get("summary", ""))

render_section("关键事件卡片", "首页保留高密度内容展示，避免页面空荡，适合答辩时快速扫读。")
event_cols = st.columns(4)
for index, item in enumerate(sample.get("event_cards", [])):
    with event_cols[index % 4]:
        render_node_image(item, caption=item.get("place", ""))
        st.markdown(f"#### {item.get('title', '')}")
        st.caption(item.get("place", ""))
        st.write(item.get("summary", ""))
