"""Streamlit 启动入口。"""

from __future__ import annotations

import streamlit as st

from streamlit_ui import render_hero, render_top_nav, setup_page


def main() -> None:
    """应用入口。"""
    setup_page("启动入口", icon="🧭")
    render_top_nav("启动入口")
    render_hero(
        title="《长征史》交互式 AI 导览系统",
        subtitle="应用已完成启动，可直接在 Streamlit 中运行，无需额外启动后端服务。若页面未自动跳转，可使用下方入口继续访问。",
        badges=["多模型接入", "RAG 知识导览", "智能讲解"],
    )
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.page_link("pages/1_首页.py", label="进入首页", use_container_width=True)
    with col2:
        st.page_link("pages/7_测试体验.py", label="测试体验", use_container_width=True)
    with col3:
        st.page_link("pages/5_配置页.py", label="进入配置页", use_container_width=True)
    with col4:
        st.page_link("pages/6_管理员后台.py", label="进入管理员后台", use_container_width=True)

    st.switch_page("pages/1_首页.py")


if __name__ == "__main__":
    main()
