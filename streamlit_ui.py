"""Streamlit 多页面共享 UI 工具。"""

from __future__ import annotations

import html
from textwrap import dedent
from typing import Any, Dict, List

import streamlit as st

from utils import (
    get_default_provider_name,
    get_settings,
    get_visible_user_models,
    is_user_key_allowed,
    now_text,
    resolve_provider_config,
)

APP_TITLE = "《长征史》交互式 AI 导览系统"
ROLE_OPTIONS = ["大学生", "研学团成员", "普通参观者"]
TOPIC_FILTERS = [
    ("综合导览", {}),
    ("重大事件", {"type": "event"}),
    ("重要人物", {"type": "figure"}),
    ("重要地点", {"type": "place"}),
    ("路线节点", {"type": "route"}),
    ("长征精神", {"type": "spirit"}),
    ("常见问答", {"type": "faq"}),
]


def inject_custom_css() -> None:
    """注入统一的产品化样式。"""
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(177, 130, 63, 0.18), transparent 26%),
                radial-gradient(circle at bottom right, rgba(132, 49, 33, 0.14), transparent 24%),
                linear-gradient(180deg, #f8f2e8 0%, #f1e5d2 55%, #ead9c0 100%);
            color: #1d1815;
        }
        .block-container {
            padding-top: 1rem;
            padding-bottom: 3rem;
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #203546 0%, #29485e 100%);
        }
        [data-testid="stSidebar"] * {
            color: #f8f2e8;
        }
        .hero-banner {
            padding: 1.6rem 1.8rem;
            border-radius: 26px;
            background: linear-gradient(135deg, #6f2219 0%, #a03f2f 48%, #c88a49 100%);
            color: #fff9f0;
            box-shadow: 0 18px 46px rgba(82, 30, 20, 0.18);
            border: 1px solid rgba(255, 245, 230, 0.22);
            margin-bottom: 1rem;
        }
        .hero-title {
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.35rem;
        }
        .hero-subtitle {
            font-size: 1rem;
            line-height: 1.8;
            color: rgba(255, 249, 240, 0.92);
        }
        .badge-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.55rem;
            margin-bottom: 0.85rem;
        }
        .badge-pill {
            display: inline-flex;
            align-items: center;
            padding: 0.3rem 0.75rem;
            border-radius: 999px;
            background: rgba(255, 249, 240, 0.14);
            border: 1px solid rgba(255, 249, 240, 0.25);
            font-size: 0.86rem;
        }
        .card-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 0.95rem;
            margin: 0.8rem 0 1.2rem;
        }
        .card-grid.timeline-grid {
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
        }
        .info-card, .source-card, .status-card {
            background: rgba(255, 251, 245, 0.9);
            border: 1px solid rgba(154, 113, 61, 0.22);
            border-radius: 22px;
            padding: 1rem 1.1rem;
            box-shadow: 0 10px 28px rgba(72, 48, 29, 0.08);
        }
        .card-label, .source-label {
            color: #7b6147;
            font-size: 0.9rem;
        }
        .card-title, .source-title {
            color: #4b2119;
            font-size: 1.05rem;
            font-weight: 700;
            margin: 0.18rem 0 0.42rem;
        }
        .card-desc, .source-desc {
            color: #4c433d;
            line-height: 1.72;
            font-size: 0.93rem;
        }
        .section-title {
            font-size: 1.25rem;
            font-weight: 700;
            color: #4b2119;
            margin: 1rem 0 0.35rem;
        }
        .section-subtitle {
            color: #7a6350;
            margin-bottom: 0.8rem;
        }
        .metric-strip {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 0.8rem;
            margin: 0.8rem 0 1rem;
        }
        .metric-box {
            border-radius: 18px;
            padding: 0.9rem 1rem;
            background: rgba(255, 252, 247, 0.85);
            border: 1px solid rgba(141, 101, 57, 0.18);
        }
        .metric-name {
            color: #7a6147;
            font-size: 0.88rem;
        }
        .metric-value {
            font-size: 1.5rem;
            font-weight: 700;
            color: #69241b;
        }
        .notice-card {
            border-radius: 20px;
            padding: 1rem 1.1rem;
            background: rgba(255, 249, 239, 0.82);
            border: 1px solid rgba(166, 130, 85, 0.24);
            margin: 0.8rem 0 1rem;
        }
        .nav-caption {
            color: #e8ddcf;
            font-size: 0.85rem;
            margin-top: 0.35rem;
        }
        div[data-baseweb="tab-list"] {
            gap: 0.45rem;
            margin-bottom: 0.9rem;
        }
        div[data-baseweb="tab-list"] button {
            background: rgba(255, 251, 244, 0.76);
            border-radius: 14px;
            border: 1px solid rgba(142, 103, 61, 0.18);
            padding: 0.45rem 0.95rem;
        }
        div[data-baseweb="tab-list"] button[aria-selected="true"] {
            background: linear-gradient(135deg, #7c2a22 0%, #a44b3b 100%);
            color: #fff8ef;
            border-color: rgba(124, 42, 34, 0.6);
        }
        .small-muted {
            color: #7d6650;
            font-size: 0.88rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _clean_html(markup: str) -> str:
    """清理多行 HTML 的缩进，避免被 Markdown 误判为代码块。"""
    return dedent(markup).strip()


def init_session_state() -> None:
    """初始化前端会话状态。"""
    default_provider = get_default_provider_name()
    defaults = {
        "user_name": "",
        "user_role": "大学生",
        "selected_provider_name": default_provider,
        "selected_topic_label": "综合导览",
        "session_api_keys": {},
        "qa_messages": [],
        "game_state": {},
        "game_started": False,
        "game_explanations": {},
        "admin_authenticated": False,
        "admin_profile": {},
        "admin_token": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    ensure_user_model_selection()


def setup_page(page_title: str, icon: str = "🏔️") -> None:
    """设置页面基础配置。"""
    st.set_page_config(
        page_title=f"{page_title} | {APP_TITLE}",
        page_icon=icon,
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    inject_custom_css()
    init_session_state()
    bootstrap_repository_content()
    render_minimal_sidebar()


def render_minimal_sidebar() -> None:
    """在侧边栏仅保留导航与少量状态。"""
    current_model = get_selected_model_info()
    with st.sidebar:
        st.markdown("### 页面导航")
        st.page_link("app.py", label="应用入口")
        st.page_link("pages/1_首页.py", label="首页")
        st.page_link("pages/2_智能导览.py", label="智能导览")
        st.page_link("pages/3_讲解生成.py", label="讲解生成")
        st.page_link("pages/4_长征闯关.py", label="长征闯关")
        st.page_link("pages/5_配置页.py", label="配置页")
        st.page_link("pages/7_测试体验.py", label="测试体验")
        st.page_link("pages/6_管理员后台.py", label="管理员后台")
        st.markdown("<div class='nav-caption'>这里只保留导航与状态，不承载复杂配置。</div>", unsafe_allow_html=True)
        st.divider()
        st.caption(f"当前身份：{st.session_state.get('user_role', '大学生')}")
        if current_model:
            st.caption(f"当前模型：{current_model.get('display_name', '未选择')}")
        st.caption(f"更新时间：{now_text()}")


def ensure_user_model_selection() -> None:
    """确保当前会话中的模型选择仍然有效。"""
    visible_models = get_visible_user_models()
    if not visible_models:
        st.session_state["selected_provider_name"] = "mock"
        return

    allowed_names = [item["provider_name"] for item in visible_models]
    current = st.session_state.get("selected_provider_name", "")
    if current not in allowed_names:
        default_model = next((item for item in visible_models if item.get("is_default")), visible_models[0])
        st.session_state["selected_provider_name"] = default_model["provider_name"]


def get_selected_model_info() -> Dict[str, Any]:
    """获取当前选中的用户模型信息。"""
    ensure_user_model_selection()
    current = st.session_state.get("selected_provider_name", "")
    visible_models = get_visible_user_models()
    for item in visible_models:
        if item["provider_name"] == current:
            return item
    return visible_models[0] if visible_models else {}


def set_selected_provider(provider_name: str) -> None:
    """更新当前会话选择的模型。"""
    st.session_state["selected_provider_name"] = provider_name
    if not is_user_key_allowed(provider_name):
        st.session_state.setdefault("session_api_keys", {})
        st.session_state["session_api_keys"][provider_name] = ""


def get_runtime_api_key(provider_name: str) -> str:
    """获取当前会话中某个 provider 的临时 Key。"""
    return st.session_state.get("session_api_keys", {}).get(provider_name, "")


def set_runtime_api_key(provider_name: str, api_key: str) -> None:
    """保存当前会话中某个 provider 的临时 Key。"""
    st.session_state.setdefault("session_api_keys", {})
    st.session_state["session_api_keys"][provider_name] = api_key


def build_current_provider_config() -> Dict[str, Any]:
    """构造当前页面使用的 provider 配置。"""
    model_info = get_selected_model_info()
    provider_name = model_info.get("provider_name", "mock")
    runtime_key = get_runtime_api_key(provider_name) if model_info.get("allow_user_key") else ""
    return resolve_provider_config(provider_name=provider_name, runtime_api_key=runtime_key)


def bootstrap_repository_content() -> None:
    """确保应用启动时完成默认知识库初始化。"""
    if st.session_state.get("_repository_content_ready"):
        return
    from rag import ensure_default_knowledge_base

    with st.spinner("正在加载仓库内置内容..."):
        st.session_state["_repository_content_status"] = ensure_default_knowledge_base()
    st.session_state["_repository_content_ready"] = True


def render_top_nav(current_page: str) -> None:
    """渲染页内顶部导航。"""
    row1 = st.columns(4)
    with row1[0]:
        st.page_link("pages/1_首页.py", label="首页", use_container_width=True)
    with row1[1]:
        st.page_link("pages/2_智能导览.py", label="智能导览", use_container_width=True)
    with row1[2]:
        st.page_link("pages/3_讲解生成.py", label="讲解生成", use_container_width=True)
    with row1[3]:
        st.page_link("pages/4_长征闯关.py", label="长征闯关", use_container_width=True)
    row2 = st.columns(3)
    with row2[0]:
        st.page_link("pages/5_配置页.py", label="配置页", use_container_width=True)
    with row2[1]:
        st.page_link("pages/7_测试体验.py", label="测试体验", use_container_width=True)
    with row2[2]:
        st.page_link("pages/6_管理员后台.py", label="管理员后台", use_container_width=True)
    st.caption(f"当前页面：{current_page}")


def render_hero(title: str, subtitle: str, badges: List[str] | None = None) -> None:
    """渲染主视觉区。"""
    badge_html = "".join(
        f"<span class='badge-pill'>{html.escape(item)}</span>" for item in (badges or []) if item
    )
    st.markdown(
        _clean_html(
            f"""
        <div class="hero-banner">
          <div class="badge-row">{badge_html}</div>
          <div class="hero-title">{html.escape(title)}</div>
          <div class="hero-subtitle">{html.escape(subtitle)}</div>
        </div>
        """
        ),
        unsafe_allow_html=True,
    )


def render_metrics(items: List[Dict[str, str]]) -> None:
    """渲染指标条。"""
    cards = []
    for item in items:
        cards.append(
            _clean_html(
                f"""
            <div class="metric-box">
                <div class="metric-name">{html.escape(str(item.get('label', '')))}</div>
                <div class="metric-value">{html.escape(str(item.get('value', '')))}</div>
            </div>
            """
            )
        )
    st.markdown(f"<div class='metric-strip'>{''.join(cards)}</div>", unsafe_allow_html=True)


def render_cards(items: List[Dict[str, str]], timeline: bool = False) -> None:
    """渲染信息卡片。"""
    class_name = "card-grid timeline-grid" if timeline else "card-grid"
    cards = []
    for item in items:
        cards.append(
            _clean_html(
                f"""
            <div class="info-card">
                <div class="card-label">{html.escape(str(item.get('label', '')))}</div>
                <div class="card-title">{html.escape(str(item.get('title', '')))}</div>
                <div class="card-desc">{html.escape(str(item.get('desc', '')))}</div>
            </div>
            """
            )
        )
    st.markdown(f"<div class='{class_name}'>{''.join(cards)}</div>", unsafe_allow_html=True)


def render_section(title: str, subtitle: str = "") -> None:
    """渲染区块标题。"""
    st.markdown(f"<div class='section-title'>{html.escape(title)}</div>", unsafe_allow_html=True)
    if subtitle:
        st.markdown(f"<div class='section-subtitle'>{html.escape(subtitle)}</div>", unsafe_allow_html=True)


def render_model_banner() -> None:
    """渲染当前模型说明。"""
    model_info = get_selected_model_info()
    provider_config = build_current_provider_config()
    description = model_info.get("description") or "当前模型由管理员开放给普通用户使用。"
    allow_key_text = "允许输入个人 API Key" if model_info.get("allow_user_key") else "使用管理员统一配置"
    readiness_text = "当前模型可直接调用。"
    if provider_config.get("provider_name") != "mock" and provider_config.get("api_key_source") == "missing":
        readiness_text = "当前环境未检测到平台密钥，系统会自动回退到本地演示模式。"
    elif provider_config.get("api_key_source") == "streamlit_secrets":
        readiness_text = "当前优先使用 Streamlit Secrets 中的密钥。"
    elif provider_config.get("api_key_source") == "environment":
        readiness_text = "当前优先使用环境变量中的密钥。"
    elif provider_config.get("api_key_source") == "session":
        readiness_text = "当前正在使用你在本次会话中输入的个人 API Key。"
    st.markdown(
        _clean_html(
            f"""
        <div class="notice-card">
            <strong>当前模型：</strong>{html.escape(model_info.get('display_name', '本地演示模型'))}
            <br/>
            <span class="small-muted">模型标识：{html.escape(model_info.get('model', '未配置'))}</span>
            <br/>
            <span class="small-muted">开放策略：{html.escape(allow_key_text)}，普通用户只能看到管理员开放的模型。</span>
            <br/>
            <span class="small-muted">{html.escape(readiness_text)}</span>
            <br/>
            <span class="small-muted">{html.escape(description)}</span>
        </div>
        """
        ),
        unsafe_allow_html=True,
    )


def render_runtime_notice(result: Dict[str, Any]) -> None:
    """展示模型运行时提示。"""
    if result.get("warning"):
        st.warning(result["warning"])


def render_sources(sources: List[Dict[str, Any]], title: str = "本次回答依据") -> None:
    """渲染依据来源卡片。"""
    if not sources:
        st.info("当前没有可展示的依据片段。")
        return
    with st.expander(title, expanded=False):
        cards = []
        for item in sources:
            cards.append(
                _clean_html(
                    f"""
                <div class="source-card">
                    <div class="source-label">来源文件：{html.escape(str(item.get('source_file', '未知文件')))}</div>
                    <div class="source-title">{html.escape(str(item.get('title', '未命名')))}</div>
                    <div class="source-desc">
                        类型：{html.escape(str(item.get('type', '未知')))}<br/>
                        摘要片段：{html.escape(str(item.get('snippet', '')))}
                    </div>
                </div>
                """
                )
            )
        st.markdown("".join(cards), unsafe_allow_html=True)


def admin_is_logged_in() -> bool:
    """判断管理员是否已在前端登录。"""
    return bool(st.session_state.get("admin_authenticated"))


def render_admin_badge() -> None:
    """渲染管理员状态提示。"""
    if admin_is_logged_in():
        profile = st.session_state.get("admin_profile", {})
        st.success(f"管理员已登录：{profile.get('display_name', profile.get('username', 'admin'))}")
    else:
        st.info("当前未登录管理员账号。管理员相关配置仅在管理员登录后可用。")


def get_topic_filter_options() -> List[str]:
    """返回主题过滤标签。"""
    return [item[0] for item in TOPIC_FILTERS]


def get_filters_by_label(label: str) -> Dict[str, Any]:
    """根据标签获取过滤条件。"""
    for item_label, filters in TOPIC_FILTERS:
        if item_label == label:
            return filters.copy()
    return {}
