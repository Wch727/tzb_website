"""Streamlit 启动入口。"""

from __future__ import annotations

import streamlit as st

from streamlit_ui import render_hero, render_top_nav, setup_page


def main() -> None:
    """应用入口。"""
    setup_page("启动入口", icon="🧭")
    render_top_nav("启动入口")
    render_hero(
        title="《长征史》交互式导览与闯关学习系统",
        subtitle="这里是整站的统一入口。你可以从主展首页、角色选择、活动中心或内容运营页面进入不同使用场景。",
        badges=["主线导览", "角色任务", "活动组织", "学习榜单"],
    )
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.page_link("pages/1_首页.py", label="进入首页", width="stretch")
    with col2:
        st.page_link("pages/2_角色选择.py", label="角色选择", width="stretch")
    with col3:
        st.page_link("pages/6_活动中心.py", label="活动中心", width="stretch")
    with col4:
        st.page_link("pages/9_管理员后台.py", label="进入内容运营", width="stretch")

    st.switch_page("pages/1_首页.py")


if __name__ == "__main__":
    main()
