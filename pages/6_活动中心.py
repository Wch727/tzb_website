"""活动中心页。"""

from __future__ import annotations

import streamlit as st

from activity_manager import build_activity_qr_bytes, build_activity_share_link, get_activity, list_activities
from game import get_route_node
from leaderboard import get_activity_leaderboard
from streamlit_ui import render_cards, render_hero, render_section, render_top_nav, setup_page


setup_page("活动中心", icon="📚")
render_top_nav("活动中心")
render_hero(
    title="活动中心",
    subtitle="活动中心承载知识竞赛、党史学习日、红色研学任务等组织化场景，支持活动链接、二维码与活动排行榜展示。",
    badges=["活动模板", "分享链接", "二维码", "活动排行"],
)

activities = list_activities()
activity_ids = [item["activity_id"] for item in activities]
current_activity_id = st.session_state.get("current_activity_id", activity_ids[0] if activity_ids else "")
if current_activity_id not in activity_ids and activity_ids:
    current_activity_id = activity_ids[0]

render_section("活动模板总览", "当前版本已经提供最小可演示的活动能力：活动模板、节点范围、分享链接、二维码、活动排行。")
render_cards(
    [
        {
            "label": item.get("mode", ""),
            "title": item.get("name", ""),
            "desc": f"{item.get('description', '')} 活动时长：{item.get('time_range', '')}。",
        }
        for item in activities
    ]
)

current_activity_id = st.selectbox(
    "选择活动",
    activity_ids,
    index=activity_ids.index(current_activity_id) if current_activity_id in activity_ids else 0,
    format_func=lambda item: next((activity["name"] for activity in activities if activity["activity_id"] == item), item),
)
st.session_state["current_activity_id"] = current_activity_id
activity = get_activity(current_activity_id)

left, right = st.columns([1.1, 1])
with left:
    render_section("活动信息", "活动可作为班级竞赛、党史学习日、研学任务等组织单元进行分发。")
    st.markdown(f"## {activity.get('name', '')}")
    st.write(activity.get("description", ""))
    st.caption(f"活动模式：{activity.get('mode', '')}")
    st.caption(f"活动时长：{activity.get('time_range', '')}")
    st.caption(f"活动状态：{activity.get('status', '')}")
    st.caption(f"覆盖节点：{len(activity.get('node_scope', []))} 个")
    if st.button("进入该活动并选择角色", use_container_width=True, type="primary"):
        st.switch_page("pages/2_角色选择.py")
    if st.button("查看该活动排行榜", use_container_width=True):
        st.switch_page("pages/7_排行榜.py")

with right:
    share_link = build_activity_share_link(activity)
    st.text_input("活动分享链接", value=share_link, disabled=True)
    qr_bytes = build_activity_qr_bytes(share_link)
    if qr_bytes:
        st.image(qr_bytes, caption="活动二维码", width=220)
    else:
        st.info("当前环境未安装二维码依赖，已保留活动分享链接。")

render_section("活动节点范围", "活动不是空壳链接，而是明确绑定了一组主线节点与题目范围。")
node_cols = st.columns(4)
for index, node_id in enumerate(activity.get("node_scope", [])):
    node = get_route_node(node_id) or {}
    with node_cols[index % 4]:
        st.markdown(f"**{index + 1}. {node.get('title', node_id)}**")
        st.caption(f"{node.get('date', '')} · {node.get('place', '')}")
        st.write(node.get("summary", "")[:88] + ("..." if len(node.get("summary", "")) > 88 else ""))

render_section("活动规则说明", "老师或组织者可以直接说明活动的使用方式，便于现场扫码或课堂统一参与。")
st.markdown(
    "\n".join(
        [
            "- 参与者先在角色选择页选择身份，再沿着活动节点范围进入主线答题。",
            "- 每完成一关都会累计红星积分、粮草、勋章与军衔，并自动进入活动排行榜。",
            "- 分享链接和二维码可直接发给班级、支部或研学团队使用。",
        ]
    )
)

render_section("活动排行榜预览", "每个活动都可以查看独立排行，便于课堂、团日活动和研学任务进行结果展示。")
ranking = get_activity_leaderboard(current_activity_id, limit=10)
if ranking:
    for item in ranking:
        st.markdown(
            f"{item.get('rank', 0)}. **{item.get('user_name', '')}** · "
            f"{item.get('role_name', '')} · {item.get('score', 0)} 分 · "
            f"粮草 {item.get('grain', 0)} · {item.get('rank_title', '')}"
        )
else:
    st.info("当前活动还没有成绩记录。完成一次剧情答题后，这里将自动出现活动排行榜。")
