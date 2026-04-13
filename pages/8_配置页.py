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


setup_page("配置页", icon="⚙️")
render_top_nav("配置页")
render_hero(
    title="配置页",
    subtitle="普通用户与管理员都在这里完成各自权限范围内的设置。面向云端部署时，长期配置以 GitHub 仓库与 Secrets 为准。",
    badges=["用户配置", "管理员开放策略", "Streamlit 部署"],
)

user_tab, admin_tab = st.tabs(["普通用户配置", "管理员配置"])

with user_tab:
    render_section("当前可用模型", "普通用户只能看到管理员已经开放的模型，不能改动全局 provider 配置。")
    st.caption(get_settings().get("repository_content_notice", "正式展示内容以仓库内置内容为准。"))
    visible_models = get_user_models()
    if not visible_models:
        st.warning("当前没有可用模型，请联系管理员在管理端开放至少一个 provider。")
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
                    "label": "当前模型",
                    "title": current_model.get("display_name", "未选择"),
                    "desc": (
                        f"模型标识：{current_model.get('model', '未配置')}。"
                        f"{' 当前为系统默认模型。' if current_model.get('provider_name') == default_provider_name else ''}"
                    ),
                },
                {
                    "label": "内容模式",
                    "title": current_mode_label,
                    "desc": "静态展示模式会优先使用仓库内置长文本内容；AI 增强模式会在有可用 Key 时调用模型。",
                },
                {
                    "label": "开放策略",
                    "title": "由管理员统一决定",
                    "desc": "普通用户只能看到管理员开放的模型，不能访问隐藏或未启用的 provider。",
                },
                {
                    "label": "主题偏好",
                    "title": st.session_state.get("selected_topic_label", "综合导览"),
                    "desc": "主题偏好只影响当前会话，不会修改系统级配置。",
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
                "个人 API Key（仅当前会话生效，不落盘）",
                type="password",
                value=st.session_state.get("session_api_keys", {}).get(selected, ""),
                placeholder="如管理员允许，可在此输入你自己的 API Key",
            )
            if st.button("保存当前会话 Key", use_container_width=True):
                set_runtime_api_key(selected, api_key.strip())
                st.success("已保存到当前会话。关闭页面或切换会话后将失效。")
        else:
            st.info("当前模型由管理员统一配置，不允许普通用户输入自己的 API Key。")

        preferred_topic = st.selectbox(
            "当前主题偏好",
            get_topic_filter_options(),
            index=get_topic_filter_options().index(st.session_state.get("selected_topic_label", "综合导览")),
        )
        st.session_state["selected_topic_label"] = preferred_topic
        st.caption("说明：这里的设置仅影响你当前的使用体验，不会修改管理员配置。")

with admin_tab:
    render_section("管理员开放策略", "管理员决定开放哪个 API / provider 给普通用户使用，并控制用户是否可输入个人 Key。")
    render_admin_badge()
    st.info("云端部署时，长期生效的配置建议直接修改 GitHub 仓库中的 config/ 文件并重新 push。此页面中的变更更适合当前容器内的临时演示。")

    if not admin_is_logged_in():
        st.info("请先前往“管理员后台”页面登录管理员账号，再返回此处进行配置。")
        st.page_link("pages/9_管理员后台.py", label="前往管理员后台登录", use_container_width=True)
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
        if st.button("保存默认模型", use_container_width=True):
            set_default_provider(default_provider)
            st.success("默认模型已更新。")
            st.rerun()

    st.markdown("#### Provider 管理")
    for provider in provider_configs:
        provider_name = provider["provider_name"]
        with st.expander(f"{provider.get('display_name', provider_name)}（{provider_name}）", expanded=False):
            runtime_status = get_provider_runtime_status(provider_name)
            st.caption(
                f"当前模型：{provider.get('model', '未配置')} | "
                f"密钥来源：{runtime_status.get('api_key_source_text', '未配置')} | "
                f"Secrets 名称：{provider.get('api_key_secret_name', '') or '未设置'}"
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

            if st.button(f"保存 {provider_name} 的开放策略", key=f"save_flags_{provider_name}", use_container_width=True):
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
                    "Secrets 名称",
                    value=provider.get("api_key_secret_name", ""),
                    help="优先从 Streamlit Secrets 或环境变量读取。例如：MOONSHOT_API_KEY。",
                )
                api_key = st.text_input(
                    "本地回退 API Key（选填）",
                    type="password",
                    placeholder="云端部署建议留空，改在 Secrets 中配置",
                )
                description = st.text_area("说明", value=provider.get("description", ""))
                submitted = st.form_submit_button("保存 provider 配置", use_container_width=True)

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
        submitted = st.form_submit_button("新增 provider", use_container_width=True)

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
