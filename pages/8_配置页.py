"""配置页。"""

from __future__ import annotations

import streamlit as st

from streamlit_ui import (
    admin_is_logged_in,
    content_mode_key_from_label,
    get_content_mode_label,
    get_content_mode_options,
    get_selected_model_info,
    get_topic_filter_options,
    render_admin_badge,
    render_cards,
    render_hero,
    render_section,
    render_top_nav,
    set_runtime_api_key,
    set_selected_provider,
    setup_page,
)
from utils import (
    get_default_provider_name,
    get_provider_runtime_status,
    get_settings,
    list_provider_configs,
    set_default_provider,
    set_provider_allow_user_key,
    set_provider_enabled,
    set_provider_visibility,
    upsert_provider_config,
)


def get_user_models():
    """获取用户可见模型。"""
    from utils import get_visible_user_models

    return get_visible_user_models()


setup_page("使用设置", icon="⚙️")
render_top_nav("使用设置")
render_hero(
    title="使用设置",
    subtitle="围绕导览模式、可用模型与主题偏好进行设置；运营范围与模型策略由内容运营统一维护。",
    badges=["个人设置", "开放策略", "模型管理"],
)

user_tab, admin_tab = st.tabs(["个人设置", "运营设置"])

with user_tab:
    render_section("可用模型", "此处展示站点已开放的讲解模型与导览模式。")
    st.caption(get_settings().get("repository_content_notice", "正式展示内容以内置史料与知识卡为准。"))
    visible_models = get_user_models()
    if not visible_models:
        st.warning("站点暂未开放可用讲解模型。")
    else:
        current_model = get_selected_model_info()
        provider_names = [item["provider_name"] for item in visible_models]
        selected = st.selectbox(
            "选择可用模型",
            provider_names,
            index=provider_names.index(current_model.get("provider_name", provider_names[0])),
            format_func=lambda name: next(
                (item["display_name"] for item in visible_models if item["provider_name"] == name),
                name,
            ),
        )
        if selected != current_model.get("provider_name"):
            set_selected_provider(selected)
            st.rerun()

        current_model = get_selected_model_info()
        default_provider_name = get_default_provider_name()
        current_mode_label = get_content_mode_label(st.session_state.get("content_mode_preference", "auto"))
        render_cards(
            [
                {
                    "label": "模型",
                    "title": current_model.get("display_name", "未选择"),
                    "desc": (
                        f"模型标识：{current_model.get('model', '未配置')}。"
                        f"{' 系统默认模型。' if current_model.get('provider_name') == default_provider_name else ''}"
                    ),
                },
                {
                    "label": "内容模式",
                    "title": current_mode_label,
                    "desc": "知识导览模式会优先使用内置长文本内容；智能讲解增强会在具备可用模型时提供更灵活的表达。",
                },
                {
                    "label": "开放策略",
                    "title": "由运营人员统一决定",
                    "desc": "普通访问者只能看到已开放的模型范围，不能访问隐藏或未启用的服务。",
                },
                {
                    "label": "主题偏好",
                    "title": st.session_state.get("selected_topic_label", "综合导览"),
                    "desc": "主题偏好仅影响本次浏览中的导览与问答侧重。",
                },
            ]
        )

        mode_label = st.selectbox(
            "内容模式",
            get_content_mode_options(),
            index=get_content_mode_options().index(current_mode_label)
            if current_mode_label in get_content_mode_options()
            else 0,
        )
        st.session_state["content_mode_preference"] = content_mode_key_from_label(mode_label)

        if current_model.get("allow_user_key"):
            api_key = st.text_input(
                "个人 API Key（仅本次会话生效）",
                type="password",
                value=st.session_state.get("session_api_keys", {}).get(selected, ""),
                placeholder="如已开放个人接入，可在此填写个人 API Key",
            )
            if st.button("保存当前会话 Key", width="stretch"):
                set_runtime_api_key(selected, api_key.strip())
                st.success("个人密钥已保存到本次会话。")
        else:
            st.info("个人 API Key 输入未开放。")

        preferred_topic = st.selectbox(
            "主题偏好",
            get_topic_filter_options(),
            index=get_topic_filter_options().index(st.session_state.get("selected_topic_label", "综合导览")),
        )
        st.session_state["selected_topic_label"] = preferred_topic
        st.caption("以上设置仅影响本次浏览中的导览与学习体验。")

with admin_tab:
    render_section("运营开放策略", "由内容运营统一管理模型开放范围、展示名称与接入方式。")
    render_admin_badge()
    st.info("此处用于维护站点对外开放的模型范围与接入策略。")

    if not admin_is_logged_in():
        st.info("请先前往“内容运营”页面完成登录，再返回此处进行开放策略配置。")
        st.page_link("pages/9_管理员后台.py", label="前往内容运营页面登录", width="stretch")
        st.stop()

    provider_configs = list_provider_configs(include_disabled=True)
    enabled_provider_names = [item["provider_name"] for item in provider_configs if item.get("enabled")]
    if enabled_provider_names:
        default_provider = st.selectbox(
            "系统默认模型",
            enabled_provider_names,
            index=enabled_provider_names.index(get_default_provider_name())
            if get_default_provider_name() in enabled_provider_names
            else 0,
        )
        if st.button("保存默认模型", width="stretch"):
            set_default_provider(default_provider)
            st.success("默认模型已更新。")
            st.rerun()

    st.markdown("#### Provider 管理")
    for provider in provider_configs:
        provider_name = provider["provider_name"]
        with st.expander(f"{provider.get('display_name', provider_name)}（{provider_name}）", expanded=False):
            runtime_status = get_provider_runtime_status(provider_name)
            st.caption(
                f"模型：{provider.get('model', '未配置')} | "
                f"密钥来源：{runtime_status.get('api_key_source_text', '未配置')} | "
                f"平台密钥标识：{provider.get('api_key_secret_name', '') or '未设置'}"
            )

            col1, col2, col3 = st.columns(3)
            with col1:
                enabled = st.toggle(
                    "启用",
                    value=provider.get("enabled", False),
                    key=f"enabled_{provider_name}",
                )
            with col2:
                visible = st.toggle(
                    "对普通用户可见",
                    value=provider.get("visible_to_users", provider.get("visible_to_user", True)),
                    key=f"visible_{provider_name}",
                )
            with col3:
                allow_user_key = st.toggle(
                    "允许用户输入个人 Key",
                    value=provider.get("allow_user_key", False),
                    key=f"user_key_{provider_name}",
                )

            if st.button(f"保存 {provider_name} 的开放策略", key=f"save_flags_{provider_name}", width="stretch"):
                set_provider_enabled(provider_name, enabled)
                set_provider_visibility(provider_name, visible)
                set_provider_allow_user_key(provider_name, allow_user_key)
                st.success(f"{provider_name} 的开放策略已更新。")
                st.rerun()

            with st.form(f"edit_provider_{provider_name}"):
                display_name = st.text_input("展示名称", value=provider.get("display_name", ""))
                base_url = st.text_input("Base URL", value=provider.get("base_url", ""))
                model = st.text_input("模型名称", value=provider.get("model", ""))
                api_key_secret_name = st.text_input(
                    "平台密钥标识",
                    value=provider.get("api_key_secret_name", ""),
                    help="优先从平台密钥配置或环境变量读取，例如：MOONSHOT_API_KEY。",
                )
                api_key = st.text_input(
                    "本地回退 API Key（选填）",
                    type="password",
                    placeholder="如使用平台统一密钥，可留空本地回退值",
                )
                description = st.text_area("说明", value=provider.get("description", ""))
                submitted = st.form_submit_button("保存 provider 配置", width="stretch")

            if submitted:
                upsert_provider_config(
                    {
                        "provider_name": provider_name,
                        "display_name": display_name,
                        "provider": provider.get("provider", provider_name),
                        "base_url": base_url,
                        "api_key": api_key.strip(),
                        "api_key_secret_name": api_key_secret_name.strip(),
                        "model": model,
                        "enabled": enabled,
                        "visible_to_users": visible,
                        "allow_user_key": allow_user_key,
                        "description": description,
                    }
                )
                st.success(f"{provider_name} 已更新。")
                st.rerun()

    st.markdown("#### 新增 provider")
    with st.form("create_provider"):
        provider_name = st.text_input("provider_name", placeholder="例如：moonshot-new")
        display_name = st.text_input("display_name", placeholder="例如：Kimi 备用模型")
        provider_type = st.selectbox("provider 类型", ["moonshot", "qwen", "minimax", "deepseek", "mock"])
        base_url = st.text_input("base_url", placeholder="兼容 OpenAI 的接口地址")
        model = st.text_input("model", placeholder="模型名称")
        api_key_secret_name = st.text_input("api_key_secret_name", placeholder="例如：MOONSHOT_API_KEY")
        api_key = st.text_input("本地回退 api_key（选填）", type="password")
        description = st.text_area("说明", placeholder="用于管理员识别该 provider 的展示说明")
        enabled = st.checkbox("创建后立即启用", value=False)
        visible = st.checkbox("创建后立即开放给普通用户", value=False)
        allow_user_key = st.checkbox("允许普通用户输入自己的 Key", value=False)
        submitted = st.form_submit_button("新增 provider", width="stretch")

    if submitted and provider_name.strip():
        upsert_provider_config(
            {
                "provider_name": provider_name.strip(),
                "display_name": display_name.strip() or provider_name.strip(),
                "provider": provider_type,
                "base_url": base_url.strip(),
                "api_key": api_key.strip(),
                "api_key_secret_name": api_key_secret_name.strip(),
                "model": model.strip(),
                "enabled": enabled,
                "visible_to_users": visible,
                "allow_user_key": allow_user_key,
                "description": description.strip(),
            }
        )
        st.success(f"{provider_name.strip()} 已创建。")
        st.rerun()
