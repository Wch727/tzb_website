"""Streamlit 启动入口。"""

from __future__ import annotations

import streamlit as st

from streamlit_ui import render_hero, render_top_nav, setup_page


def main() -> None:
    """应用入口。"""
    setup_page("启动入口", icon="🧭")
    render_top_nav("启动入口")
    render_hero(
        title="《长征精神·沉浸式云端答题互动平台》",
        subtitle="应用已完成启动，可直接在 Streamlit 中运行，无需额外启动后端服务。若页面未自动跳转，可使用下方入口继续访问。",
        badges=["主线关卡", "角色扮演", "活动中心", "排行榜"],
    )
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.page_link("pages/1_首页.py", label="进入首页", use_container_width=True)
    with col2:
        st.page_link("pages/2_角色选择.py", label="角色选择", use_container_width=True)
    with col3:
        st.page_link("pages/6_活动中心.py", label="活动中心", use_container_width=True)
    with col4:
        st.page_link("pages/9_管理员后台.py", label="进入管理员后台", use_container_width=True)

    st.switch_page("pages/1_首页.py")


if __name__ == "__main__":
    main()
