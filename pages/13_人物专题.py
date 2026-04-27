"""人物专题页。"""

from __future__ import annotations

import html

import streamlit as st

from content_store import (
    build_figure_story_script,
    get_figure_data,
    get_related_nodes_for_figure,
    load_figures_data,
)
from media import render_audio_player, render_digital_human, render_node_image
from streamlit_ui import (
    _clean_html,
    render_curatorial_note,
    render_formal_script,
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


def _script_paragraphs(script: str) -> list[str]:
    """把人物讲解词拆成可展陈阅读的段落。"""
    return [part.strip() for part in str(script or "").split("\n\n") if part.strip()]


def _without_source_note(text: str) -> str:
    """页面正文中不重复显示资料来源提示。"""
    cleaned = str(text or "").strip()
    for marker in ("依据", "资料依据", "从官方资料看"):
        if cleaned.startswith(marker):
            return ""
    return cleaned


def _merge_text(*parts: str) -> str:
    """合并文本，过滤空段落。"""
    return "\n\n".join(part.strip() for part in parts if str(part or "").strip())


def _render_figure_exhibit_wall(figure: dict, story_script: str, related_nodes: list[dict]) -> None:
    """渲染人物专题展墙，避免短卡片造成内容单薄。"""
    paragraphs = [_without_source_note(part) for part in _script_paragraphs(story_script)]
    paragraphs = [part for part in paragraphs if part]
    background = _merge_text(figure.get("background", ""), paragraphs[0] if paragraphs else "")
    role = _merge_text(
        figure.get("long_march_role", ""),
        "\n\n".join(paragraphs[1:3]) if len(paragraphs) > 1 else "",
    )
    significance = _merge_text(
        figure.get("significance", ""),
        "\n\n".join(paragraphs[3:]) if len(paragraphs) > 3 else "",
    )
    node_links = "".join(
        f"<span class='figure-node-pill'>{html.escape(node.get('title', '长征节点'))}</span>"
        for node in related_nodes[:5]
    )
    if not node_links:
        node_links = "<span class='figure-node-pill'>长征主线</span>"

    st.markdown(
        _clean_html(
            f"""
            <style>
            .figure-exhibit-wall {{
                display: grid;
                grid-template-columns: minmax(260px, 0.72fr) minmax(0, 1.6fr);
                gap: 1.2rem;
                margin: 1rem 0 1.6rem;
            }}
            .figure-archive-card,
            .figure-scroll-panel {{
                border: 1px solid rgba(137, 42, 54, 0.18);
                border-radius: 28px;
                background:
                    linear-gradient(135deg, rgba(255, 255, 255, 0.92), rgba(255, 247, 235, 0.88)),
                    radial-gradient(circle at 10% 0%, rgba(137, 42, 54, 0.08), transparent 34%);
                box-shadow: 0 18px 42px rgba(95, 35, 27, 0.08);
            }}
            .figure-archive-card {{
                padding: 1.35rem;
                position: sticky;
                top: 1rem;
                align-self: start;
            }}
            .figure-archive-label {{
                color: #9b3148;
                font-size: 0.88rem;
                font-weight: 800;
                letter-spacing: 0.16em;
            }}
            .figure-archive-card h3 {{
                margin: 0.35rem 0 0.55rem;
                color: #521824;
                font-size: clamp(1.45rem, 2vw, 2.1rem);
            }}
            .figure-archive-role {{
                color: #67514a;
                line-height: 1.75;
                font-size: 1rem;
            }}
            .figure-node-pills {{
                display: flex;
                flex-wrap: wrap;
                gap: 0.55rem;
                margin-top: 1rem;
            }}
            .figure-node-pill {{
                border: 1px solid rgba(137, 42, 54, 0.22);
                border-radius: 999px;
                padding: 0.36rem 0.68rem;
                color: #6b2432;
                background: rgba(255, 246, 235, 0.82);
                font-weight: 700;
                font-size: 0.9rem;
            }}
            .figure-scroll-panel {{
                padding: clamp(1.2rem, 2.4vw, 2.1rem);
            }}
            .figure-scroll-section + .figure-scroll-section {{
                border-top: 1px solid rgba(137, 42, 54, 0.12);
                margin-top: 1.35rem;
                padding-top: 1.35rem;
            }}
            .figure-scroll-section span {{
                color: #a33d52;
                font-size: 0.9rem;
                font-weight: 800;
                letter-spacing: 0.12em;
            }}
            .figure-scroll-section h3 {{
                margin: 0.28rem 0 0.8rem;
                color: #48141f;
                font-size: clamp(1.35rem, 2vw, 1.9rem);
            }}
            .figure-scroll-section p {{
                margin: 0 0 0.78rem;
                color: #3f312d;
                line-height: 2.02;
                font-size: 1.04rem;
                text-align: justify;
            }}
            @media (max-width: 900px) {{
                .figure-exhibit-wall {{
                    grid-template-columns: 1fr;
                }}
                .figure-archive-card {{
                    position: relative;
                    top: auto;
                }}
            }}
            </style>
            <div class="figure-exhibit-wall">
                <aside class="figure-archive-card">
                    <div class="figure-archive-label">人物档案</div>
                    <h3>{html.escape(figure.get('title', '重要人物'))}</h3>
                    <div class="figure-archive-role">{html.escape(figure.get('role', '党的重要领导人'))}</div>
                    <div class="figure-node-pills">{node_links}</div>
                </aside>
                <article class="figure-scroll-panel">
                    <section class="figure-scroll-section">
                        <span>第一部分</span>
                        <h3>走进历史现场</h3>
                        {''.join(f'<p>{html.escape(part)}</p>' for part in background.split(chr(10) + chr(10)) if part.strip())}
                    </section>
                    <section class="figure-scroll-section">
                        <span>第二部分</span>
                        <h3>长征中的关键作用</h3>
                        {''.join(f'<p>{html.escape(part)}</p>' for part in role.split(chr(10) + chr(10)) if part.strip())}
                    </section>
                    <section class="figure-scroll-section">
                        <span>第三部分</span>
                        <h3>历史贡献</h3>
                        {''.join(f'<p>{html.escape(part)}</p>' for part in significance.split(chr(10) + chr(10)) if part.strip())}
                    </section>
                </article>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )


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

render_gallery_frame("人物专题", "从人物生平、长征中的作用与历史贡献三个方面，理解其在革命进程中的位置。")

hero_left, hero_right = st.columns([0.92, 1.18])
with hero_left:
    render_node_image(figure, caption=figure.get("image_caption", "") or figure.get("role", "重要人物"))
with hero_right:
    st.markdown(f"## {figure.get('title', '重要人物')}")
    st.caption(figure.get("role", "重要人物"))
    render_curatorial_note(
        title=figure.get("title", "重要人物"),
        body=figure.get("summary", "围绕人物经历、长征中的作用和历史贡献展开介绍。"),
        label="人物导语",
    )

render_ledger_cards(
    [
        {"label": "人物身份", "title": figure.get("role", "重要人物"), "desc": "从人物身份进入其在党史与长征史中的位置。"},
        {"label": "关联节点", "title": figure.get("route_stage", "主线相关"), "desc": "通过代表性节点回看人物在线路中的实际作用。"},
        {"label": "资料依据", "title": "官方党史与党媒资料", "desc": "专题文字依据中国共产党新闻网、人民网党史频道等公开资料整理。"},
    ]
)

render_section("人物讲解", "围绕人物经历、长征中的作用和历史贡献展开讲解。")
render_formal_script(
    story_script,
    title=f"{figure.get('title', '重要人物')}人物讲解词",
    label="人物专题讲解词",
    meta=[
        figure.get("role", "重要人物"),
        "资料依据：官方党史资料",
    ],
)
audio_left, audio_right = st.columns([1, 1])
with audio_left:
    figure_audio_path = render_audio_player(
        text=story_script,
        cache_key=f"figure-story::{figure.get('id', figure.get('title', 'figure'))}",
        button_label="播放人物讲解",
    )
with audio_right:
    figure_state_key = f"figure_digital::{figure.get('id', figure.get('title', 'figure'))}"
    if st.button("切换人物讲解员模式", key=f"btn::{figure_state_key}", width="stretch"):
        st.session_state[figure_state_key] = not st.session_state.get(
            figure_state_key,
            False,
        )

if st.session_state.get(figure_state_key, False):
    render_digital_human(
        section_text=story_script,
        avatar_path=figure.get("avatar", "assets/avatar/guide_digital_host.png"),
        audio_path=figure_audio_path,
        title=f"{figure.get('title', '重要人物')}人物讲解",
        subtitle=figure.get("role", "党的重要领导人"),
        cache_key=f"figure-story::{figure.get('id', figure.get('title', 'figure'))}",
    )

render_section("人物专题长卷", "沿着人物经历、长征实践与历史贡献展开阅读。")
_render_figure_exhibit_wall(figure, story_script, related_nodes)

render_section("官方资料来源", "以下资料来自中国共产党新闻网、人民网党史频道等公开党史资料。")
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
    st.info("该人物专题正在补充官方资料链接。")

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
