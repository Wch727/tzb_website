"""Streamlit 多页面共享 UI 工具。"""

from __future__ import annotations

import base64
import html
import json
import mimetypes
import re
from pathlib import Path
from textwrap import dedent
from typing import Any, Dict, List

import streamlit as st

from activity_manager import get_activity
from template_renderer import render_script_block, render_template
from utils import (
    BASE_DIR,
    get_default_provider_name,
    get_settings,
    get_visible_user_models,
    is_user_key_allowed,
    now_text,
    resolve_provider_config,
)

APP_TITLE = "长征精神·沉浸式云端答题互动平台"
ROLE_OPTIONS = ["大学生", "研学团成员", "普通参观者"]
CONTENT_MODE_OPTIONS = [
    ("auto", "自动判断"),
    ("static", "知识导览模式"),
    ("ai", "智能讲解增强"),
]
TOPIC_FILTERS = [
    ("综合导览", {}),
    ("重大事件", {"type": "event"}),
    ("重要人物", {"type": "figure"}),
    ("重要地点", {"type": "place"}),
    ("路线节点", {"type": "route"}),
    ("长征精神", {"type": "spirit"}),
    ("常见问答", {"type": "faq"}),
]


def _background_image_uri() -> str:
    """读取背景素材并转换为 data URI。"""
    candidates = [
        BASE_DIR / "assets" / "images" / "route_map.svg",
        BASE_DIR / "assets" / "images" / "changzheng_route_map.jpg",
    ]
    for path in candidates:
        if not path.exists():
            continue
        return _asset_to_data_uri(path)
    return ""


def _asset_to_data_uri(path_like: Any) -> str:
    """将本地素材转换为 data URI。"""
    path = path_like if isinstance(path_like, str) else str(path_like)
    candidate = BASE_DIR / path if not str(path).startswith(str(BASE_DIR)) else Path(path)
    if not candidate.exists():
        candidate = BASE_DIR / str(path).lstrip("./")
    if not candidate.exists():
        return ""
    mime, _ = mimetypes.guess_type(str(candidate))
    if candidate.suffix.lower() == ".svg":
        mime = "image/svg+xml"
    encoded = base64.b64encode(candidate.read_bytes()).decode("ascii")
    return f"data:{mime or 'application/octet-stream'};base64,{encoded}"


def inject_custom_css() -> None:
    """注入统一的产品化样式。"""
    css_path = BASE_DIR / "assets" / "styles" / "site_core.css"
    css = css_path.read_text(encoding="utf-8")
    st.markdown(f"<style>\n{css}\n</style>", unsafe_allow_html=True)


def inject_interaction_scripts() -> None:
    """加载拆分到 assets/scripts 的轻量前端增强脚本。"""
    st.html(
        render_script_block("site_interactions.js"),
        unsafe_allow_javascript=True,
    )


def scroll_page_to_top(anchor_id: str = "codex-scroll-top") -> None:
    """在页面重渲染后把视角拉回顶部。"""
    st.html(
        render_script_block(
            "scroll_tools.js",
            anchor_id_json=json.dumps(anchor_id, ensure_ascii=False),
        ),
        unsafe_allow_javascript=True,
    )


def render_pending_scroll_to_top() -> None:
    """在页面主体渲染完成后再次触发回顶。"""
    if st.session_state.pop("_scroll_to_top_after_render", False):
        scroll_page_to_top()


def render_scroll_anchor(anchor_id: str = "codex-scroll-top") -> None:
    """在页面顶部渲染可供脚本定位的锚点。"""
    st.html(render_template("scroll_anchor.html", anchor_id=html.escape(anchor_id)))


def _clean_html(markup: str) -> str:
    """清理多行 HTML 的缩进，避免被 Markdown 误判为代码块。"""
    return dedent(markup).strip()


def init_session_state() -> None:
    """初始化前端会话状态。"""
    default_provider = get_default_provider_name()
    defaults = {
        "user_name": "红色学习者",
        "unit_name": "体验组",
        "user_role": "大学生",
        "selected_figure_name": "毛泽东",
        "selected_provider_name": default_provider,
        "selected_topic_label": "综合导览",
        "session_api_keys": {},
        "session_provider_overrides": {},
        "tts_voice_preset": "female",
        "tts_voice_gender": "female",
        "tts_voice": "",
        "qa_messages": [],
        "game_state": {},
        "game_started": False,
        "game_explanations": {},
        "admin_authenticated": False,
        "admin_profile": {},
        "admin_token": "",
        "content_mode_preference": "auto",
        "selected_role_id": "scout",
        "selected_role_name": "侦察兵",
        "current_activity_id": "knowledge-contest",
        "current_team_id": "",
        "current_team_name": "",
        "current_branch_name": "",
        "pending_team_id": "",
        "pending_game_start_node_id": "",
        "game_active": False,
        "story_state": {},
        "progress_snapshot": {},
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    ensure_user_model_selection()


def sync_activity_from_query() -> None:
    """从查询参数中同步活动与小队入口。"""
    try:
        activity_id = str(st.query_params.get("activity_id", "") or "").strip()
    except Exception:
        activity_id = ""
    if activity_id:
        st.session_state["current_activity_id"] = activity_id
    try:
        team_id = str(st.query_params.get("team_id", "") or "").strip()
    except Exception:
        team_id = ""
    if team_id:
        st.session_state["pending_team_id"] = team_id


def setup_page(page_title: str, icon: str = "🏔️") -> None:
    """设置页面基础配置。"""
    st.set_page_config(
        page_title=f"{page_title} | {APP_TITLE}",
        page_icon=icon,
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    inject_custom_css()
    inject_interaction_scripts()
    init_session_state()
    bootstrap_repository_content()
    sync_activity_from_query()
    should_scroll = st.session_state.pop("_scroll_to_top_once", False)
    if should_scroll:
        st.session_state["_scroll_to_top_after_render"] = True
        scroll_page_to_top()
    render_minimal_sidebar()


def render_minimal_sidebar() -> None:
    """在侧边栏仅保留导航与少量状态。"""
    current_model = get_selected_model_info()
    activity_info = get_activity(st.session_state.get("current_activity_id", ""))
    with st.sidebar:
        st.markdown("### 页面导航")
        st.page_link("app.py", label="应用入口")
        st.page_link("pages/1_首页.py", label="首页")
        st.page_link("pages/3_长征路线.py", label="长征路线")
        st.page_link("pages/14_节点展项.py", label="节点展项")
        st.page_link("pages/4_剧情答题.py", label="互动闯关")
        st.page_link("pages/5_知识库.py", label="知识百问")
        st.page_link("pages/6_活动中心.py", label="活动中心")
        st.page_link("pages/7_排行榜.py", label="排行榜")
        st.page_link("pages/8_配置页.py", label="使用设置")
        st.page_link("pages/9_管理员后台.py", label="内容运营")
        st.page_link("pages/10_测试体验.py", label="导览速览")
        st.page_link("pages/11_讲解生成.py", label="讲解工坊")
        st.page_link("pages/12_数据大屏.py", label="数据大屏")
        st.page_link("pages/13_人物专题.py", label="人物专题")
        st.divider()
        if st.session_state.get("game_active"):
            st.caption(f"当前闯关身份：{st.session_state.get('selected_role_name', '侦察兵')}")
        if activity_info:
            st.caption(f"当前活动：{activity_info.get('name', '')}")
        if st.session_state.get("current_team_name"):
            st.caption(f"当前小队：{st.session_state.get('current_team_name', '')}")
        if st.session_state.get("current_branch_name"):
            st.caption(f"支部归属：{st.session_state.get('current_branch_name', '')}")
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


def set_runtime_provider_override(provider_name: str, *, model: str = "", base_url: str = "") -> None:
    """保存当前会话中某个 provider 的临时连接参数。"""
    st.session_state.setdefault("session_provider_overrides", {})
    st.session_state["session_provider_overrides"][provider_name] = {
        "model": model.strip(),
        "base_url": base_url.strip(),
    }


def get_runtime_provider_override(provider_name: str) -> Dict[str, str]:
    """获取当前会话中某个 provider 的临时模型和 Base URL。"""
    override = st.session_state.get("session_provider_overrides", {}).get(provider_name, {})
    if not isinstance(override, dict):
        return {"model": "", "base_url": ""}
    return {
        "model": str(override.get("model", "") or "").strip(),
        "base_url": str(override.get("base_url", "") or "").strip(),
    }


def user_provider_allows_platform_key(provider_name: str) -> bool:
    """普通用户侧只有 Kimi / Moonshot 可使用平台统一 Key。"""
    normalized = str(provider_name or "").lower()
    return normalized in {"moonshot", "kimi", "mock"} or normalized.startswith("moonshot")


def build_current_provider_config() -> Dict[str, Any]:
    """构造当前页面使用的 provider 配置。"""
    model_info = get_selected_model_info()
    provider_name = model_info.get("provider_name", "mock")
    runtime_key = ""
    if model_info.get("allow_user_key"):
        runtime_key = get_runtime_api_key(provider_name)
        if not runtime_key:
            runtime_key = get_runtime_api_key(model_info.get("provider_group", ""))
        if not runtime_key:
            runtime_key = get_runtime_api_key(model_info.get("provider", ""))
    runtime_override = get_runtime_provider_override(provider_name)
    config = resolve_provider_config(
        provider_name=provider_name,
        runtime_api_key=runtime_key,
        runtime_model=runtime_override.get("model", ""),
        runtime_base_url=runtime_override.get("base_url", ""),
        allow_platform_key=user_provider_allows_platform_key(provider_name),
    )
    preference = st.session_state.get("content_mode_preference", "auto")
    has_real_key = config.get("provider_name") != "mock" and config.get("api_key_source") != "missing"
    static_mode = preference == "static" or not has_real_key
    if preference == "ai" and has_real_key:
        static_mode = False
    config["content_mode_preference"] = preference
    config["static_mode"] = static_mode
    config["mode_label"] = "知识导览模式" if static_mode else "智能讲解增强"
    if preference == "static":
        config["mode_reason"] = "当前已切换为知识导览模式，系统将优先依据内置史料与知识卡组织内容。"
    elif static_mode and not has_real_key:
        config["mode_reason"] = "当前未检测到可用模型密钥，系统将依据内置史料与知识卡完成导览与讲解。"
    else:
        config["mode_reason"] = "当前将结合知识检索结果进行智能讲解与生成。"
    return config


def bootstrap_repository_content() -> None:
    """确保应用启动时完成默认知识库初始化。"""
    if st.session_state.get("_repository_content_ready"):
        return
    try:
        from rag import ensure_default_knowledge_base

        with st.spinner("正在加载仓库内置内容..."):
            st.session_state["_repository_content_status"] = ensure_default_knowledge_base()
    except Exception as exc:
        st.session_state["_repository_content_status"] = {
            "message": "站点内置知识内容加载失败，请稍后刷新页面或联系维护人员检查环境配置。",
            "error": str(exc),
            "initialized": False,
        }
    st.session_state["_repository_content_ready"] = True


def _nav_action(label: str, target: str, current_page: str, current_aliases: List[str] | None = None) -> None:
    """渲染顶部导航按钮。"""
    aliases = {current_page}
    for item in current_aliases or []:
        aliases.add(item)
    is_current = label in aliases or target in aliases
    if st.button(label, key=f"topnav::{target}", width="stretch", type="primary" if is_current else "secondary"):
        if is_current:
            st.session_state["_scroll_to_top_once"] = True
            st.rerun()
        st.switch_page(target)


def render_top_nav(current_page: str) -> None:
    """渲染页内顶部导航。"""
    current_model = get_selected_model_info()
    current_role = st.session_state.get("selected_role_name", "侦察兵")
    current_activity = get_activity(st.session_state.get("current_activity_id", "")) or {}
    current_activity_name = current_activity.get("name", "")
    subtitle_map = {
        "首页": "从主展入口进入路线、人物、精神与互动学习内容。",
        "长征路线": "按四大篇章浏览长征主线展项，进入单节点深度阅读。",
        "节点展项": "单独浏览当前节点的图文讲解、语音导览与互动入口。",
        "剧情答题": "闭卷完成节点挑战，提交后进入解析、复盘与成长奖励。",
        "知识百问": "围绕长征史问题进入问答、延伸阅读与依据检索。",
        "讲解工坊": "围绕节点与专题生成讲解稿和短视频脚本。",
        "活动中心": "查看活动、分享入口、协作方式与参与路径。",
        "排行榜": "查看个人、小队、单位与活动排行。",
        "使用设置": "调整导览模式、模型选择与访问会话设置。",
        "内容运营": "维护内容、活动与知识库运行状态。",
        "导览速览": "从重点问题、展项与讲解入口快速进入长征主线。",
        "数据大屏": "集中呈现参与情况、热度变化与榜单数据。",
    }
    chips = []
    if current_page == "剧情答题":
        chips.append(render_template("masthead_chip.html", text=f"闯关身份：{html.escape(current_role)}"))
    if current_activity_name:
        chips.append(render_template("masthead_chip.html", text=f"活动：{html.escape(current_activity_name)}"))
    if current_model and current_page in {"知识百问", "讲解工坊", "使用设置"}:
        chips.append(
            render_template(
                "masthead_chip.html",
                text=f"模型：{html.escape(current_model.get('display_name', '知识导览模式'))}",
            )
        )
    st.html(
        render_template(
            "masthead.html",
            kicker="长征主题数字展",
            title=html.escape(APP_TITLE),
            subtitle=html.escape(subtitle_map.get(current_page, "沿着长征主线浏览展项、知识与互动学习内容。")),
            chips_html="".join(chips),
        )
    )
    st.html(render_template("nav_section_label.html", label="展览导览"))
    row1 = st.columns(6)
    with row1[0]:
        _nav_action("首页", "pages/1_首页.py", current_page)
    with row1[1]:
        _nav_action("长征路线", "pages/3_长征路线.py", current_page)
    with row1[2]:
        _nav_action("节点展项", "pages/14_节点展项.py", current_page)
    with row1[3]:
        _nav_action("知识百问", "pages/5_知识库.py", current_page)
    with row1[4]:
        _nav_action("人物专题", "pages/13_人物专题.py", current_page)
    with row1[5]:
        _nav_action("讲解工坊", "pages/11_讲解生成.py", current_page)

    st.html(render_template("nav_section_label.html", label="互动与活动"))
    row2 = st.columns(6)
    with row2[0]:
        _nav_action("互动闯关", "pages/4_剧情答题.py", current_page, current_aliases=["剧情答题", "互动闯关"])
    with row2[1]:
        _nav_action("活动中心", "pages/6_活动中心.py", current_page)
    with row2[2]:
        _nav_action("排行榜", "pages/7_排行榜.py", current_page)
    with row2[3]:
        _nav_action("导览速览", "pages/10_测试体验.py", current_page)
    with row2[4]:
        _nav_action("数据大屏", "pages/12_数据大屏.py", current_page)
    with row2[5]:
        _nav_action("使用设置", "pages/8_配置页.py", current_page)

    if st.session_state.get("admin_authenticated"):
        st.html(render_template("nav_section_label.html", label="运营入口"))
        admin_cols = st.columns(2)
        with admin_cols[0]:
            _nav_action("内容运营", "pages/9_管理员后台.py", current_page)
        with admin_cols[1]:
            _nav_action("使用设置", "pages/8_配置页.py", current_page)


def _hero_theme_class(title: str) -> str:
    """按页面类型给通用主视觉分配不同展陈色调。"""
    if any(keyword in title for keyword in ["排行榜", "数据大屏"]):
        return "hero-scoreboard"
    if any(keyword in title for keyword in ["活动中心", "活动"]):
        return "hero-activity"
    if any(keyword in title for keyword in ["内容运营", "管理员", "配置", "使用设置"]):
        return "hero-admin"
    if any(keyword in title for keyword in ["剧情答题", "互动闯关", "当前关卡"]):
        return "hero-game"
    if any(keyword in title for keyword in ["长征路线", "节点展项", "人物专题", "知识百问", "讲解"]):
        return "hero-exhibit"
    return ""


def render_hero(title: str, subtitle: str, badges: List[str] | None = None) -> None:
    """渲染主视觉区。"""
    badge_html = "".join(
        render_template("hero_badge.html", label=html.escape(item)) for item in (badges or []) if item
    )
    st.html(
        render_template(
            "hero_banner.html",
            hero_class=_hero_theme_class(title),
            badges_html=badge_html,
            title=html.escape(title),
            subtitle=html.escape(subtitle),
        )
    )


def render_metrics(items: List[Dict[str, str]]) -> None:
    """渲染指标条。"""
    cards = []
    for item in items:
        cards.append(
            render_template(
                "metric_box.html",
                label=html.escape(str(item.get("label", ""))),
                value=html.escape(str(item.get("value", ""))),
            )
        )
    st.html(render_template("metric_strip.html", cards_html="".join(cards)))


def render_game_status_board(items: List[Dict[str, str]]) -> None:
    """渲染更像网页 HUD 的状态面板。"""
    cards: List[str] = []
    for item in items:
        cards.append(
            render_template(
                "game_status_card.html",
                kicker=html.escape(str(item.get("kicker", "状态"))),
                value=html.escape(str(item.get("value", ""))),
                label=html.escape(str(item.get("label", ""))),
                note=html.escape(str(item.get("note", ""))),
            )
        )
    if cards:
        st.html(render_template("game_status_grid.html", cards_html="".join(cards)))


def render_cards(items: List[Dict[str, str]], timeline: bool = False) -> None:
    """渲染信息卡片。"""
    class_name = "card-grid timeline-grid" if timeline else "card-grid"
    cards = []
    for item in items:
        cards.append(
            render_template(
                "info_card.html",
                label=html.escape(str(item.get("label", ""))),
                title=html.escape(str(item.get("title", ""))),
                desc=html.escape(str(item.get("desc", ""))),
            )
        )
    st.html(render_template("card_grid.html", class_name=class_name, cards_html="".join(cards)))


def render_section(title: str, subtitle: str = "") -> None:
    """渲染区块标题。"""
    st.html(render_template("section_title.html", title=html.escape(title)))
    if subtitle:
        st.html(render_template("section_subtitle.html", subtitle=html.escape(subtitle)))


def render_curatorial_note(title: str, body: str, label: str = "专题导语") -> None:
    """渲染策展导语卡。"""
    st.html(
        render_template(
            "curator_note.html",
            label=html.escape(label),
            title=html.escape(title),
            body=html.escape(body),
        )
    )


def render_chapter_overview_cards(chapters: List[Dict[str, Any]], active_id: str = "") -> None:
    """渲染篇章总览卡。"""
    if not chapters:
        return

    cols = st.columns(min(4, len(chapters)))
    for index, chapter in enumerate(chapters):
        node_titles = " · ".join(node.get("title", "") for node in chapter.get("nodes", [])[:3]) or "沿线展项"
        class_name = "chapter-card active" if chapter.get("id") == active_id else "chapter-card"
        with cols[index % len(cols)]:
            st.html(
                render_template(
                    "chapter_card.html",
                    class_name=class_name,
                    badge=html.escape(str(chapter.get("badge", "主线篇章"))),
                    title=html.escape(str(chapter.get("title", "未命名篇章"))),
                    subtitle=html.escape(str(chapter.get("subtitle", ""))),
                    count=html.escape(str(chapter.get("count", len(chapter.get("nodes", []))))),
                    node_titles=html.escape(node_titles),
                    href=html.escape(f"/长征路线?chapter_id={chapter.get('id', '')}"),
                )
            )


def render_detail_panels(items: List[Dict[str, str]]) -> None:
    """渲染展项信息板。"""
    cards: List[str] = []
    for item in items:
        cards.append(
            render_template(
                "detail_panel.html",
                title=html.escape(str(item.get("title", ""))),
                desc=html.escape(str(item.get("desc", ""))),
            )
        )
    if cards:
        st.html(render_template("detail_grid.html", cards_html="".join(cards)))


def render_boss_stage_intro(data: Dict[str, Any]) -> None:
    """渲染大关专属过场。"""
    if not data:
        return
    orders_html = "".join(
        render_template(
            "boss_order_card.html",
            index=str(index),
            desc=html.escape(str(item)),
        )
        for index, item in enumerate(data.get("orders", []), start=1)
        if str(item).strip()
    )
    st.html(
        render_template(
            "boss_intro.html",
            label=html.escape(str(data.get("label", "章节攻坚关"))),
            title=html.escape(str(data.get("title", "关键大关"))),
            lead=html.escape(str(data.get("lead", ""))),
            focus=html.escape(str(data.get("focus", ""))),
            orders_html=orders_html,
            stakes=html.escape(str(data.get("stakes", ""))),
        )
    )


def render_boss_stage_outcome(data: Dict[str, Any]) -> None:
    """渲染大关答题后的专属结算语。"""
    if not data:
        return
    st.html(
        render_template(
            "boss_outcome.html",
            label=html.escape(str(data.get("label", "章节攻坚关"))),
            title=html.escape(str(data.get("title", "关键大关"))),
            lead=html.escape(str(data.get("lead", ""))),
            focus=html.escape(str(data.get("focus", ""))),
            closing=html.escape(str(data.get("closing", ""))),
        )
    )


def render_formal_script(
    script: str,
    *,
    title: str = "",
    label: str = "正式讲解词",
    meta: List[str] | None = None,
) -> None:
    """将讲解内容统一渲染为正式讲解词样式。"""
    content = (script or "").strip()
    if not content:
        st.info("当前暂无可展示的讲解内容。")
        return

    blocks = [part.strip() for part in re.split(r"\n\s*\n", content) if part.strip()]
    resolved_title = title.strip()
    if blocks:
        first_line = blocks[0].replace("：", "").replace(":", "").strip()
        if not resolved_title and len(first_line) <= 26 and any(
            marker in first_line for marker in ["讲解稿", "讲解词", "讲述稿", "脚本"]
        ):
            resolved_title = blocks.pop(0)

    section_patterns = (
        r"^[一二三四五六七八九十]+、",
        r"^[（(][一二三四五六七八九十0-9]+[)）]",
        r"^第[一二三四五六七八九十0-9]+部分",
        r"^第[一二三四五六七八九十0-9]+段",
        r"^(开场引入|历史背景|事件经过|历史意义|结尾升华|开场|主体|结尾|镜头[一二三四五六七八九十0-9]+)",
    )

    html_blocks: List[str] = []
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        first = lines[0]
        is_section = any(re.match(pattern, first) for pattern in section_patterns)
        if is_section:
            paragraphs = "".join(
                render_template("script_paragraph.html", text=html.escape(line)) for line in lines[1:] if line
            )
            fallback_paragraph = render_template("script_paragraph.html", text=html.escape(block))
            html_blocks.append(
                render_template(
                    "script_section_block.html",
                    title=html.escape(first),
                    paragraphs_html=paragraphs or fallback_paragraph,
                )
            )
        else:
            paragraphs = "".join(render_template("script_paragraph.html", text=html.escape(line)) for line in lines)
            html_blocks.append(render_template("script_block.html", content_html=paragraphs))

    meta_markup = ""
    if meta:
        chips = "".join(
            render_template("script_meta_chip.html", text=html.escape(item)) for item in meta if item and item.strip()
        )
        if chips:
            meta_markup = render_template("script_meta.html", chips_html=chips)

    st.html(
        render_template(
            "script_sheet.html",
            label=html.escape(label),
            title=html.escape(resolved_title or "长征主题讲解"),
            meta_html=meta_markup,
            blocks_html="".join(html_blocks),
        )
    )


def render_feature_ribbon(items: List[Dict[str, str]]) -> None:
    """渲染首页或篇章摘要带。"""
    cards: List[str] = []
    for item in items:
        cards.append(
            render_template(
                "feature_shell.html",
                label=html.escape(str(item.get("label", ""))),
                title=html.escape(str(item.get("title", ""))),
                desc=html.escape(str(item.get("desc", ""))),
            )
        )
    if cards:
        st.html(render_template("feature_ribbon.html", cards_html="".join(cards)))


def render_ledger_cards(items: List[Dict[str, str]]) -> None:
    """渲染路线或展项清单卡。"""
    cards: List[str] = []
    for item in items:
        cards.append(
            render_template(
                "ledger_card.html",
                label=html.escape(str(item.get("label", ""))),
                title=html.escape(str(item.get("title", ""))),
                desc=html.escape(str(item.get("desc", ""))),
            )
        )
    if cards:
        st.html(render_template("ledger_grid.html", cards_html="".join(cards)))


def render_gallery_frame(title: str, subtitle: str = "") -> None:
    """渲染展厅框架标题。"""
    st.html(render_template("gallery_frame.html", title=html.escape(title), subtitle=html.escape(subtitle)))


def render_exhibition_hero(
    *,
    title: str,
    subtitle: str,
    background_path: str,
    tags: List[str],
    storyline_items: List[Dict[str, str]],
    side_title: str,
    side_text: str,
    side_points: List[str],
) -> None:
    """渲染更具展厅感的首页第一屏。"""
    background_uri = _asset_to_data_uri(background_path)
    tag_markup = "".join(
        render_template("exhibition_tag.html", label=html.escape(item)) for item in tags if item
    )
    story_markup = "".join(
        render_template(
            "exhibition_story_card.html",
            label=html.escape(str(item.get("label", "展线"))),
            title=html.escape(str(item.get("title", ""))),
            desc=html.escape(str(item.get("desc", ""))),
        )
        for item in storyline_items
    )
    point_markup = "".join(render_template("exhibition_side_point.html", text=html.escape(item)) for item in side_points if item)
    st.html(
        render_template(
            "exhibition_hero.html",
            background_uri=background_uri,
            title=html.escape(title),
            subtitle=html.escape(subtitle),
            tag_markup=tag_markup,
            story_markup=story_markup,
            side_title=html.escape(side_title),
            side_text=html.escape(side_text),
            point_markup=point_markup,
        )
    )


def render_model_banner() -> None:
    """渲染当前模型说明。"""
    model_info = get_selected_model_info()
    provider_config = build_current_provider_config()
    description = model_info.get("description") or "该模型用于导览问答、讲解生成与学习辅助。"
    provider_name = provider_config.get("provider_name", "")
    if provider_name == "mock":
        allow_key_text = "本地知识导览"
    elif user_provider_allows_platform_key(provider_name):
        allow_key_text = "Kimi 平台接入"
    elif model_info.get("allow_user_key"):
        allow_key_text = "使用个人 API Key"
    else:
        allow_key_text = "当前未开放个人接入"
    readiness_text = "该模型可用于智能讲解与内容生成。"
    if provider_config.get("provider_name") != "mock" and provider_config.get("api_key_source") == "missing":
        readiness_text = "未检测到可用模型密钥，系统将自动切换到知识导览模式。"
    elif provider_config.get("api_key_source") == "streamlit_secrets":
        readiness_text = "已接入平台统一配置的模型密钥。"
    elif provider_config.get("api_key_source") == "environment":
        readiness_text = "已接入可用模型密钥。"
    elif provider_config.get("api_key_source") == "session":
        readiness_text = "正在使用本次访问会话中提供的个人密钥。"
    st.html(
        render_template(
            "model_banner.html",
            model_name=html.escape(model_info.get("display_name", "知识导览模式")),
            model_id=html.escape(model_info.get("model", "未配置")),
            mode_label=html.escape(provider_config.get("mode_label", "知识导览模式")),
            allow_key_text=html.escape(allow_key_text),
            readiness_text=html.escape(provider_config.get("mode_reason", readiness_text)),
            description=html.escape(description),
        )
    )


def render_runtime_notice(result: Dict[str, Any]) -> None:
    """展示模型运行时提示。"""
    if result.get("mode_label"):
        st.info(f"讲解模式：{result['mode_label']}")
    if result.get("warning"):
        st.warning(result["warning"])


def render_sources(sources: List[Dict[str, Any]], title: str = "本次回答依据") -> None:
    """渲染依据来源卡片。"""
    if not sources:
        st.info("暂无可展示的依据片段。")
        return
    with st.expander(title, expanded=False):
        cards = []
        for item in sources:
            meta_bits = [f"类型：{html.escape(str(item.get('type', '未知')))}"]
            if item.get("chapter_title"):
                meta_bits.append(f"章节：{html.escape(str(item.get('chapter_title', '')))}")
            if item.get("section_title"):
                meta_bits.append(f"小节：{html.escape(str(item.get('section_title', '')))}")
            if item.get("source_page"):
                meta_bits.append(f"页码：{html.escape(str(item.get('source_page', '')))}")
            cards.append(
                render_template(
                    "source_card.html",
                    source_file=html.escape(str(item.get("source_file", "未知文件"))),
                    title=html.escape(str(item.get("title", "未命名"))),
                    meta_text=" | ".join(meta_bits),
                    snippet=html.escape(str(item.get("snippet", ""))),
                )
            )
        st.html("".join(cards))


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


def get_content_mode_options() -> List[str]:
    """返回内容模式标签。"""
    return [item[1] for item in CONTENT_MODE_OPTIONS]


def get_content_mode_label(value: str) -> str:
    """把内容模式值转换成中文。"""
    for key, label in CONTENT_MODE_OPTIONS:
        if key == value:
            return label
    return "自动判断"


def content_mode_key_from_label(label: str) -> str:
    """把内容模式中文标签转回键值。"""
    for key, item_label in CONTENT_MODE_OPTIONS:
        if item_label == label:
            return key
    return "auto"


def get_filters_by_label(label: str) -> Dict[str, Any]:
    """根据标签获取过滤条件。"""
    for item_label, filters in TOPIC_FILTERS:
        if item_label == label:
            return filters.copy()
    return {}
