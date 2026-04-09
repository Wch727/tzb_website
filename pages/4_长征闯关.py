"""长征闯关页。"""

from __future__ import annotations

import streamlit as st

from game import generate_node_explanation, get_route_node, load_route_nodes, start_game, submit_choice
from media import render_audio_player, render_digital_human, render_node_image
from streamlit_ui import (
    ROLE_OPTIONS,
    build_current_provider_config,
    render_model_banner,
    render_runtime_notice,
    render_section,
    render_sources,
    render_top_nav,
    setup_page,
)


setup_page("长征闯关", icon="🎯")
render_top_nav("长征闯关")
render_section("长征闯关", "每一道题都会先呈现展项背景，再进入互动答题，让答题不再是“裸题”。")
render_model_banner()

provider_config = build_current_provider_config()
route_nodes = load_route_nodes()

if not st.session_state.get("game_started"):
    st.markdown(f"### 共设 {len(route_nodes)} 个核心节点，覆盖长征主要路线与历史转折。")
    with st.form("game_start_form"):
        role = st.selectbox("请选择身份", ROLE_OPTIONS, index=ROLE_OPTIONS.index(st.session_state.get("user_role", "大学生")))
        submitted = st.form_submit_button("开始闯关", use_container_width=True, type="primary")
    if submitted:
        st.session_state["user_role"] = role
        st.session_state["game_state"] = start_game(role=role, provider_config=provider_config)
        preferred = st.session_state.pop("preferred_game_node", "")
        if preferred:
            st.session_state["game_state"]["current_stage"] = preferred
        st.session_state["game_started"] = True
        st.session_state["game_explanations"] = {}
        st.session_state["game_last_result"] = None
        st.rerun()
    st.stop()

game_state = st.session_state.get("game_state", {})
if not game_state:
    st.session_state["game_started"] = False
    st.rerun()

if game_state.get("phase") == "summary":
    render_section("闯关结算", "展示总分、已解锁节点与你的长征学习总结。")
    st.metric("总分", game_state.get("score", 0))
    titles = [get_route_node(node_id).get("title", node_id) for node_id in game_state.get("unlocked_nodes", []) if get_route_node(node_id)]
    st.write("已解锁节点：" + ("、".join(titles) if titles else "暂无"))
    summary = st.session_state.get("game_summary")
    if summary:
        render_runtime_notice(summary)
        st.markdown("#### 你的长征学习总结")
        st.write(summary.get("summary", ""))
        render_sources(summary.get("sources", []), title="本次学习总结依据")
        st.markdown("#### 推荐继续学习主题")
        for topic in summary.get("recommend_topics", []):
            st.markdown(f"- {topic}")

    if st.button("重新开始闯关", use_container_width=True):
        st.session_state["game_started"] = False
        st.session_state["game_state"] = {}
        st.session_state["game_summary"] = None
        st.session_state["game_explanations"] = {}
        st.session_state["game_last_result"] = None
        st.rerun()
    st.stop()

render_section("路线探索", "从节点列表中选择一站，系统会先给出背景说明、图文展项与 AI 讲解摘要，再进入答题。")

node_options = [item["id"] for item in game_state.get("available_nodes", [])]
current_stage = game_state.get("current_stage", node_options[0] if node_options else "")
if current_stage not in node_options and node_options:
    current_stage = node_options[0]
selected_stage = st.selectbox(
    "选择路线节点",
    node_options,
    index=node_options.index(current_stage) if current_stage in node_options else 0,
    format_func=lambda node_id: next((node["title"] for node in route_nodes if node["id"] == node_id), node_id),
)
game_state["current_stage"] = selected_stage
st.session_state["game_state"] = game_state

if selected_stage not in st.session_state["game_explanations"]:
    with st.spinner("正在生成该节点的讲解内容..."):
        st.session_state["game_explanations"][selected_stage] = generate_node_explanation(
            node_id=selected_stage,
            role=game_state.get("role", st.session_state.get("user_role", "大学生")),
            provider_config=provider_config,
        )

explanation = st.session_state["game_explanations"][selected_stage]
render_runtime_notice(explanation)

top_left, top_right = st.columns([1.05, 1.35])
with top_left:
    render_node_image(explanation.get("node", {}), caption=explanation.get("place", ""))
    st.caption(f"时间：{explanation.get('date', '未标注')}")
    st.caption(f"地点：{explanation.get('place', '未标注')}")
    if explanation.get("figures"):
        st.caption("关键人物：" + "、".join(explanation.get("figures", [])))

with top_right:
    st.markdown(f"## {explanation.get('feedback_title', explanation.get('node', {}).get('title', '节点展项'))}")
    st.markdown("### 节点背景说明")
    st.write((explanation.get("background", "") or "")[:220] or "暂无背景说明。")
    st.markdown("### AI 讲解摘要")
    st.write(explanation.get("explanation", ""))
    audio_path = render_audio_player(
        text=explanation.get("explanation") or explanation.get("background", ""),
        cache_key=f"game-{selected_stage}",
        button_label="播放节点语音讲解",
    )
    if st.button("数字人讲解模式", key=f"game_digital_{selected_stage}", use_container_width=True):
        st.session_state[f"game_digital_mode::{selected_stage}"] = not st.session_state.get(
            f"game_digital_mode::{selected_stage}",
            False,
        )
    if st.session_state.get(f"game_digital_mode::{selected_stage}", False):
        render_digital_human(
            section_text=explanation.get("explanation", ""),
            avatar_path=explanation.get("avatar", "assets/avatar/guide.svg"),
            audio_path=audio_path,
        )

detail_tab1, detail_tab2, detail_tab3 = st.tabs(["事件经过", "历史意义", "本次讲解依据"])
with detail_tab1:
    st.write(explanation.get("process", "暂无过程说明。"))
with detail_tab2:
    st.write(explanation.get("significance", "暂无意义说明。"))
with detail_tab3:
    render_sources(explanation.get("sources", []), title="本节点讲解依据")

st.markdown("---")
st.markdown("## 进入互动答题")
st.write(explanation.get("question", "暂无题目。"))
options = explanation.get("options", [])
answer = st.radio("请选择一个答案", options=options, index=None, key=f"answer_{selected_stage}")

if st.button("提交答案", use_container_width=True, type="primary", disabled=not answer):
    result = submit_choice(
        current_state=game_state,
        node_id=selected_stage,
        answer=answer or "",
        provider_config=provider_config,
    )
    st.session_state["game_state"] = result.get("state", game_state)
    st.session_state["game_last_result"] = result
    if result.get("summary"):
        st.session_state["game_summary"] = result["summary"]
    st.rerun()

last_result = st.session_state.get("game_last_result")
if last_result and selected_stage == st.session_state.get("game_state", {}).get("current_stage"):
    detail = last_result.get("answer_detail", {})
    if last_result.get("correct"):
        st.success(last_result.get("feedback", "回答正确。"))
    else:
        st.warning(last_result.get("feedback", "回答未命中全部要点。"))

    st.markdown("### 正确答案解析")
    st.write(detail.get("explanation", "暂无答案解析。"))
    st.markdown(f"**正确答案：** {detail.get('expected_answer', '未标注')}")
    st.markdown("### 延伸知识点")
    st.write(detail.get("extended_note", "暂无延伸知识点。"))
    next_node = detail.get("next_node")
    if next_node:
        st.markdown("### 下一节点推荐")
        next_left, next_right = st.columns([0.9, 1.1])
        with next_left:
            render_node_image(next_node, caption=next_node.get("place", ""))
        with next_right:
            st.write(f"{next_node.get('title', '')} · {next_node.get('summary', '')}")
            if st.button("进入下一节点", key=f"next_node_{next_node.get('id', '')}", use_container_width=True):
                st.session_state["game_state"]["current_stage"] = next_node.get("id", "")
                st.session_state["game_last_result"] = None
                st.session_state.pop(f"answer_{selected_stage}", None)
                st.rerun()
