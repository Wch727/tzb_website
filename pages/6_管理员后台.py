"""管理员后台页。"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from auth import admin_login
from file_loader import load_file, persist_processed_text
from rag import get_rag_status, incremental_ingest, rebuild_knowledge_base
from retrieval_debug import run_retrieval_debug
from streamlit_ui import render_hero, render_metrics, render_section, render_top_nav, setup_page
from utils import (
    PROCESSED_DIR,
    UPLOAD_DIR,
    get_provider_runtime_status,
    get_settings,
    get_visible_user_models,
    is_allowed_file,
    list_provider_configs,
    list_uploaded_files,
    remove_if_exists,
    safe_filename,
    save_binary_file,
)


setup_page("管理员后台", icon="🛡️")
render_top_nav("管理员后台")
render_hero(
    title="管理员后台",
    subtitle="管理员负责上传补充资料、维护 RAG 索引、查看检索命中，并控制对普通用户开放哪些模型。",
    badges=["文件管理", "RAG 导入", "检索调试", "云端友好"],
)

if not st.session_state.get("admin_authenticated"):
    render_section("管理员登录", "只有管理员可以访问后台维护能力与全局配置。")
    st.caption("提示：云端部署时请在 Streamlit Secrets 中配置 ADMIN_PASSWORD。")
    with st.form("admin_login_form"):
        username = st.text_input("管理员账号", value="admin")
        password = st.text_input("管理员密码", type="password")
        submitted = st.form_submit_button("登录后台", use_container_width=True, type="primary")
    if submitted:
        try:
            result = admin_login(username=username, password=password)
        except Exception as exc:
            st.error(str(getattr(exc, "detail", exc)))
        else:
            st.session_state["admin_authenticated"] = True
            st.session_state["admin_profile"] = {
                "username": result.get("username", username),
                "display_name": result.get("display_name", username),
            }
            st.session_state["admin_token"] = result.get("access_token", "")
            st.success("管理员登录成功。")
            st.rerun()
    st.stop()

profile = st.session_state.get("admin_profile", {})
top_left, top_right = st.columns([3, 1])
with top_left:
    st.success(f"当前管理员：{profile.get('display_name', profile.get('username', 'admin'))}")
with top_right:
    if st.button("退出登录", use_container_width=True):
        st.session_state["admin_authenticated"] = False
        st.session_state["admin_profile"] = {}
        st.session_state["admin_token"] = ""
        st.rerun()

status = get_rag_status()
render_metrics(
    [
        {"label": "上传文件数", "value": len(list_uploaded_files())},
        {"label": "Chunk 数量", "value": status.get("chunk_count", 0)},
        {"label": "知识条目数", "value": status.get("document_count", 0)},
        {"label": "开放模型数", "value": len(get_visible_user_models())},
    ]
)

file_tab, ingest_tab, debug_tab, status_tab = st.tabs(["文件管理", "RAG 导入", "检索调试", "系统状态"])

with file_tab:
    render_section("上传与文件列表", "支持 txt、md、pdf、docx、json、csv 上传。仓库内置 data/ 与 assets/ 是默认主内容源，后台上传仅用于临时补充演示。")
    st.info(get_settings().get("repository_content_notice", "正式展示内容以仓库内置内容为准。"))
    uploaded_files = st.file_uploader(
        "上传知识文件",
        accept_multiple_files=True,
        type=["txt", "md", "pdf", "docx", "json", "csv"],
    )
    if st.button("保存上传文件", use_container_width=True, type="primary", disabled=not uploaded_files):
        success_files = []
        for uploaded in uploaded_files or []:
            filename = safe_filename(uploaded.name)
            if not is_allowed_file(filename):
                st.error(f"{filename} 的后缀不受支持。")
                continue
            target_path = save_binary_file(UPLOAD_DIR, filename, uploaded.getvalue())
            parsed = load_file(target_path)
            persist_processed_text(filename, parsed.get("raw_text", ""))
            success_files.append(filename)
        if success_files:
            st.success(f"已保存文件：{'、'.join(success_files)}")

    file_rows = list_uploaded_files()
    if file_rows:
        st.dataframe(pd.DataFrame(file_rows), use_container_width=True, hide_index=True)
        for row in file_rows:
            col1, col2 = st.columns([5, 1])
            with col1:
                st.caption(
                    f"{row['filename']} | {row['size_kb']} KB | 处理文件：{row['processed_file']}"
                )
            with col2:
                if st.button("删除", key=f"delete_{row['filename']}", use_container_width=True):
                    remove_if_exists(UPLOAD_DIR / row["filename"])
                    remove_if_exists(PROCESSED_DIR / f"{Path(row['filename']).stem}.txt")
                    from rag import delete_source_file_from_rag

                    delete_source_file_from_rag(row["filename"])
                    st.success(f"{row['filename']} 已删除。")
                    st.rerun()
    else:
        st.info("当前还没有上传文件。")

with ingest_tab:
    render_section("RAG 导入", "可以选择增量导入或重建索引。默认知识库来源于仓库内置 data/，上传文件用于临时补充导入。")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("执行增量导入", use_container_width=True, type="primary"):
            with st.spinner("正在执行增量导入..."):
                result = incremental_ingest()
            st.success(result.get("message", "增量导入完成。"))
            st.json(result)
    with col2:
        if st.button("重建知识库索引", use_container_width=True):
            with st.spinner("正在重建知识库..."):
                result = rebuild_knowledge_base()
            st.success(result.get("message", "知识库重建完成。"))
            st.json(result)

with debug_tab:
    render_section("检索调试", "输入测试问题，查看系统识别出的意图、实际过滤条件与命中片段。")
    with st.form("retrieval_debug_form"):
        question = st.text_input("测试问题", placeholder="例如：遵义会议为什么是长征转折点？")
        type_filter = st.selectbox("限定类型（可选）", ["全部", "event", "figure", "place", "route", "faq", "spirit"])
        top_k = st.slider("Top K", min_value=1, max_value=8, value=4)
        submitted = st.form_submit_button("开始检索调试", use_container_width=True, type="primary")

    if submitted and question.strip():
        filters = {}
        if type_filter != "全部":
            filters["type"] = type_filter
        result = run_retrieval_debug(question=question, filters=filters, top_k=top_k)
        st.markdown(
            f"**识别意图：** {result.get('intent', 'general')}  \n"
            f"**实际过滤：** `{result.get('applied_filters', {})}`  \n"
            f"**命中数量：** {result.get('hit_count', 0)}"
        )
        if result.get("sources"):
            st.dataframe(pd.DataFrame(result["sources"]), use_container_width=True, hide_index=True)
        if result.get("hits"):
            for index, hit in enumerate(result["hits"], start=1):
                with st.expander(f"命中片段 {index}", expanded=index == 1):
                    st.write(hit.get("text", ""))
                    st.json(hit.get("metadata", {}))

with status_tab:
    render_section("系统状态", "查看当前知识库样例、Provider 配置情况以及可对外开放的模型数量。")
    provider_configs = list_provider_configs(include_disabled=True)
    st.markdown("#### Provider 状态")
    provider_rows = [
        {
            "provider_name": item.get("provider_name", ""),
            "display_name": item.get("display_name", ""),
            "enabled": item.get("enabled", False),
            "visible_to_users": item.get("visible_to_users", item.get("visible_to_user", True)),
            "allow_user_key": item.get("allow_user_key", False),
            "model": item.get("model", ""),
            "secret_name": item.get("api_key_secret_name", ""),
            "key_source": get_provider_runtime_status(item.get("provider_name", "")).get("api_key_source_text", "未配置"),
        }
        for item in provider_configs
    ]
    st.dataframe(pd.DataFrame(provider_rows), use_container_width=True, hide_index=True)

    st.markdown("#### RAG 样例")
    for sample in status.get("metadata_samples", []):
        with st.expander(str(sample.get("metadata", {}).get("title", "未命名片段")), expanded=False):
            st.json(sample.get("metadata", {}))
            st.write(sample.get("preview", ""))
