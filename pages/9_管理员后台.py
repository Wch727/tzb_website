"""管理员后台页。"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from activity_manager import (
    build_activity_qr_bytes,
    build_activity_share_link,
    create_activity,
    get_activity,
    list_activities,
    update_activity,
)
from admin_dashboard import build_admin_metrics, export_leaderboard_csv, export_rows_to_csv
from auth import admin_login
from content_store import clear_content_caches, load_faq_items, load_route_nodes_data
from file_loader import load_file, persist_processed_text
from leaderboard import get_activity_leaderboard, get_global_leaderboard, get_unit_leaderboard
from rag import get_rag_status, incremental_ingest, rebuild_knowledge_base
from retrieval_debug import run_retrieval_debug
from streamlit_ui import render_hero, render_metrics, render_section, render_top_nav, setup_page
from utils import (
    CONFIG_DIR,
    DATA_DIR,
    PROCESSED_DIR,
    UPLOAD_DIR,
    get_provider_runtime_status,
    get_settings,
    get_visible_user_models,
    is_allowed_file,
    list_provider_configs,
    list_uploaded_files,
    read_json,
    remove_if_exists,
    safe_filename,
    save_binary_file,
    write_json,
)


ROUTE_NODE_PATH = DATA_DIR / "route_nodes.json"
FAQ_PATH = DATA_DIR / "faq.csv"


def _load_route_node_rows() -> list[dict]:
    """读取可编辑的路线节点原始数据。"""
    rows = read_json(ROUTE_NODE_PATH, []) or []
    return [item for item in rows if isinstance(item, dict)]


def _save_route_node_rows(rows: list[dict]) -> None:
    """保存路线节点原始数据。"""
    write_json(ROUTE_NODE_PATH, rows)
    clear_content_caches()


def _find_route_node_row(rows: list[dict], node_id: str) -> dict:
    """查找指定节点。"""
    for item in rows:
        if item.get("id") == node_id:
            return item
    return {}


def _load_faq_rows() -> list[dict]:
    """读取 FAQ 原始数据。"""
    if not FAQ_PATH.exists():
        return []
    frame = pd.read_csv(FAQ_PATH, encoding="utf-8-sig").fillna("")
    return frame.to_dict(orient="records")


def _save_faq_rows(rows: list[dict]) -> None:
    """保存 FAQ 原始数据。"""
    frame = pd.DataFrame(rows)
    frame.to_csv(FAQ_PATH, index=False, encoding="utf-8-sig")
    clear_content_caches()


setup_page("管理员后台", icon="🛡️")
render_top_nav("管理员后台")
render_hero(
    title="管理员后台",
    subtitle="后台用于演示最小 SaaS 管理能力：资料上传、RAG 导入、活动配置、题库内容维护、统计导出和模型开放策略。",
    badges=["文件管理", "活动管理", "题库维护", "数据导出"],
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
metrics = build_admin_metrics()
metrics.extend(
    [
        {"label": "上传文件数", "value": len(list_uploaded_files())},
        {"label": "Chunk 数量", "value": status.get("chunk_count", 0)},
        {"label": "开放模型数", "value": len(get_visible_user_models())},
    ]
)
render_metrics(metrics[:6])

file_tab, rag_tab, activity_tab, content_tab, data_tab, status_tab = st.tabs(
    ["文件管理", "RAG 导入", "活动管理", "题库/内容管理", "数据统计与导出", "系统状态"]
)

with file_tab:
    render_section("上传与文件列表", "支持 txt、md、pdf、docx、json、csv 上传。仓库内置 data/ 与 assets/ 是正式展示主内容源，后台上传主要用于临时补充演示。")
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
                st.caption(f"{row['filename']} | {row['size_kb']} KB | 处理文件：{row['processed_file']}")
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

with rag_tab:
    render_section("RAG 导入与检索调试", "管理员可以增量导入、重建索引，并现场演示检索命中效果。")
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

with activity_tab:
    render_section("活动管理", "后台可创建活动、维护活动说明、设置节点范围，并生成分享链接与二维码。")
    activity_rows = list_activities()
    activity_ids = [item["activity_id"] for item in activity_rows]

    with st.form("create_activity_form"):
        st.markdown("#### 新建活动")
        name = st.text_input("活动名称", placeholder="例如：长征精神主题竞赛")
        mode = st.selectbox("活动模式", ["知识竞赛", "党史学习日", "红色研学任务"])
        description = st.text_area("活动说明", placeholder="说明活动对象、规则和使用场景")
        time_range = st.text_input("活动时长", value="60分钟")
        node_scope = st.multiselect(
            "活动节点范围",
            [item.get("id", "") for item in load_route_nodes_data()],
            format_func=lambda item: next(
                (node.get("title", item) for node in load_route_nodes_data() if node.get("id") == item),
                item,
            ),
        )
        create_submitted = st.form_submit_button("创建活动", use_container_width=True, type="primary")
    if create_submitted and name.strip():
        activity = create_activity(
            name=name.strip(),
            mode=mode,
            description=description.strip(),
            time_range=time_range.strip(),
            node_scope=node_scope,
            created_by=profile.get("username", "admin"),
        )
        st.success(f"活动“{activity.get('name', '')}”已创建。")
        st.session_state["current_activity_id"] = activity.get("activity_id", "")
        st.rerun()

    if activity_ids:
        selected_activity_id = st.selectbox(
            "选择活动进行维护",
            activity_ids,
            index=activity_ids.index(st.session_state.get("current_activity_id", activity_ids[0]))
            if st.session_state.get("current_activity_id", activity_ids[0]) in activity_ids
            else 0,
            format_func=lambda item: next((activity["name"] for activity in activity_rows if activity["activity_id"] == item), item),
        )
        st.session_state["current_activity_id"] = selected_activity_id
        selected_activity = get_activity(selected_activity_id)

        left, right = st.columns([1.15, 1])
        with left:
            st.markdown(f"### {selected_activity.get('name', '')}")
            st.write(selected_activity.get("description", ""))
            st.caption(f"模式：{selected_activity.get('mode', '')}")
            st.caption(f"时长：{selected_activity.get('time_range', '')}")
            st.caption(f"状态：{selected_activity.get('status', '')}")
            st.caption(f"节点数：{len(selected_activity.get('node_scope', []))}")
        with right:
            share_link = build_activity_share_link(selected_activity)
            st.text_input("活动分享链接", value=share_link, disabled=True)
            qr_bytes = build_activity_qr_bytes(share_link)
            if qr_bytes:
                st.image(qr_bytes, caption="活动二维码", width=200)
            else:
                st.info("当前环境未安装二维码依赖，已保留分享链接。")

        with st.form("update_activity_form"):
            new_description = st.text_area("修改活动说明", value=selected_activity.get("description", ""))
            new_time_range = st.text_input("修改活动时长", value=selected_activity.get("time_range", ""))
            new_status = st.selectbox("活动状态", ["进行中", "已完成", "待开始"], index=["进行中", "已完成", "待开始"].index(selected_activity.get("status", "进行中")) if selected_activity.get("status", "进行中") in ["进行中", "已完成", "待开始"] else 0)
            new_scope = st.multiselect(
                "修改活动节点范围",
                [item.get("id", "") for item in load_route_nodes_data()],
                default=selected_activity.get("node_scope", []),
                format_func=lambda item: next(
                    (node.get("title", item) for node in load_route_nodes_data() if node.get("id") == item),
                    item,
                ),
            )
            update_submitted = st.form_submit_button("保存活动修改", use_container_width=True)
        if update_submitted:
            update_activity(
                selected_activity_id,
                {
                    "description": new_description.strip(),
                    "time_range": new_time_range.strip(),
                    "status": new_status,
                    "node_scope": new_scope,
                },
            )
            st.success("活动信息已更新。")
            st.rerun()

        ranking_rows = get_activity_leaderboard(selected_activity_id, limit=10)
        st.markdown("#### 活动排行榜预览")
        if ranking_rows:
            st.dataframe(pd.DataFrame(ranking_rows), use_container_width=True, hide_index=True)
        else:
            st.info("当前活动尚无成绩记录。")

with content_tab:
    render_section("题库与内容管理", "当前版本支持直接编辑主线节点题库和 FAQ，用于最小可演示的内容运营。")
    route_subtab, faq_subtab = st.tabs(["主线节点题库", "FAQ 问答维护"])

    with route_subtab:
        raw_rows = _load_route_node_rows()
        editable_node_ids = [item.get("id", "") for item in raw_rows]
        selected_node_id = st.selectbox(
            "选择要编辑的主线节点",
            editable_node_ids,
            format_func=lambda item: next((node.get("title", item) for node in raw_rows if node.get("id") == item), item),
        )
        selected_row = _find_route_node_row(raw_rows, selected_node_id)

        with st.form("edit_route_node_form"):
            st.markdown("#### 节点基础信息")
            title = st.text_input("标题", value=selected_row.get("title", ""))
            date = st.text_input("时间", value=selected_row.get("date", ""))
            place = st.text_input("地点", value=selected_row.get("place", ""))
            route_stage = st.text_input("路线阶段", value=selected_row.get("route_stage", ""))
            summary = st.text_area("摘要", value=selected_row.get("summary", ""), height=120)
            background = st.text_area("背景", value=selected_row.get("background", ""), height=180)
            process = st.text_area("经过", value=selected_row.get("process", ""), height=180)
            significance = st.text_area("意义", value=selected_row.get("significance", ""), height=160)
            key_points = st.text_area("关键知识点（每行一个）", value="\n".join(selected_row.get("key_points", []) or []), height=120)
            figures = st.text_area("关键人物（用顿号分隔）", value="、".join(selected_row.get("figures", []) or []), height=80)
            st.markdown("#### 互动题配置")
            quiz = selected_row.get("quiz", {}) or {}
            question = st.text_area("题目", value=quiz.get("question", ""), height=100)
            option1 = st.text_input("选项 A", value=(quiz.get("options", ["", "", "", ""]) + ["", "", "", ""])[0])
            option2 = st.text_input("选项 B", value=(quiz.get("options", ["", "", "", ""]) + ["", "", "", ""])[1])
            option3 = st.text_input("选项 C", value=(quiz.get("options", ["", "", "", ""]) + ["", "", "", ""])[2])
            option4 = st.text_input("选项 D", value=(quiz.get("options", ["", "", "", ""]) + ["", "", "", ""])[3])
            answer = st.text_input("正确答案", value=quiz.get("answer", ""))
            explanation = st.text_area("答案解析", value=quiz.get("explanation", ""), height=140)
            extended_note = st.text_area("延伸知识点", value=quiz.get("extended_note", ""), height=120)
            save_node_submitted = st.form_submit_button("保存节点与题目修改", use_container_width=True, type="primary")

        if save_node_submitted:
            for index, item in enumerate(raw_rows):
                if item.get("id") != selected_node_id:
                    continue
                raw_rows[index] = {
                    **item,
                    "title": title.strip(),
                    "date": date.strip(),
                    "place": place.strip(),
                    "route_stage": route_stage.strip(),
                    "summary": summary.strip(),
                    "background": background.strip(),
                    "process": process.strip(),
                    "significance": significance.strip(),
                    "key_points": [line.strip() for line in key_points.splitlines() if line.strip()],
                    "figures": [part.strip() for part in figures.replace("，", "、").split("、") if part.strip()],
                    "quiz": {
                        "question": question.strip(),
                        "options": [item for item in [option1.strip(), option2.strip(), option3.strip(), option4.strip()] if item],
                        "answer": answer.strip(),
                        "explanation": explanation.strip(),
                        "extended_note": extended_note.strip(),
                    },
                }
                break
            _save_route_node_rows(raw_rows)
            st.success("节点内容已保存。若要同步到向量检索，请回到“RAG 导入”执行重建索引。")
            st.rerun()

        preview_left, preview_right = st.columns([1, 1.1])
        with preview_left:
            st.markdown("#### 节点预览")
            st.write(selected_row.get("summary", ""))
            st.caption(f"{selected_row.get('date', '')} · {selected_row.get('place', '')}")
            st.write(selected_row.get("significance", ""))
        with preview_right:
            st.markdown("#### FAQ 预览")
            faq_rows = load_faq_items()[:8]
            st.dataframe(pd.DataFrame(faq_rows)[["question", "answer"]], use_container_width=True, hide_index=True)

    with faq_subtab:
        faq_rows = _load_faq_rows()
        if not faq_rows:
            st.info("当前没有 FAQ 数据。")
        else:
            faq_index = st.selectbox(
                "选择 FAQ 条目",
                list(range(len(faq_rows))),
                format_func=lambda idx: faq_rows[idx].get("question", f"FAQ {idx + 1}"),
            )
            selected_faq = faq_rows[faq_index]
            with st.form("edit_faq_form"):
                faq_question = st.text_area("问题", value=selected_faq.get("question", ""), height=100)
                faq_answer = st.text_area("答案", value=selected_faq.get("answer", ""), height=160)
                faq_keywords = st.text_input("关键词（用顿号分隔）", value=selected_faq.get("keywords", ""))
                faq_type = st.selectbox("类型", ["faq", "event", "spirit"], index=["faq", "event", "spirit"].index(selected_faq.get("type", "faq")) if selected_faq.get("type", "faq") in ["faq", "event", "spirit"] else 0)
                save_faq_submitted = st.form_submit_button("保存 FAQ 修改", use_container_width=True)
            if save_faq_submitted:
                faq_rows[faq_index] = {
                    **selected_faq,
                    "question": faq_question.strip(),
                    "answer": faq_answer.strip(),
                    "keywords": faq_keywords.strip(),
                    "type": faq_type,
                }
                _save_faq_rows(faq_rows)
                st.success("FAQ 已保存。")
                st.rerun()
            st.markdown("#### FAQ 预览")
            st.write(selected_faq.get("answer", ""))

with data_tab:
    render_section("数据统计与导出", "至少能够演示活动统计、排行榜查看与结果导出，支撑计划书中的后台运营表述。")
    global_rows = get_global_leaderboard(limit=100)
    activity_rows = get_activity_leaderboard(st.session_state.get("current_activity_id", ""), limit=100)
    unit_rows = get_unit_leaderboard(st.session_state.get("current_activity_id", ""), limit=100)

    stat_cols = st.columns(4)
    with stat_cols[0]:
        st.metric("活动数", len(list_activities()))
    with stat_cols[1]:
        st.metric("参与记录数", len(global_rows))
    with stat_cols[2]:
        st.metric("主线节点数", len(load_route_nodes_data()))
    with stat_cols[3]:
        st.metric("FAQ 数量", len(load_faq_items()))

    if global_rows:
        st.markdown("#### 全局排行榜数据")
        st.dataframe(pd.DataFrame(global_rows), use_container_width=True, hide_index=True)
        st.download_button(
            "导出全局排行榜 CSV",
            data=export_leaderboard_csv(""),
            file_name="global_leaderboard.csv",
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.info("暂无全局排行榜数据。")

    if activity_rows:
        st.markdown("#### 当前活动排行榜数据")
        st.dataframe(pd.DataFrame(activity_rows), use_container_width=True, hide_index=True)
        st.download_button(
            "导出当前活动排行榜 CSV",
            data=export_leaderboard_csv(st.session_state.get("current_activity_id", "")),
            file_name="activity_leaderboard.csv",
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.info("当前活动暂无排行榜数据。")

    if unit_rows:
        st.markdown("#### 当前活动单位排行")
        st.dataframe(pd.DataFrame(unit_rows), use_container_width=True, hide_index=True)
        st.download_button(
            "导出当前活动单位排行 CSV",
            data=export_rows_to_csv(unit_rows),
            file_name="unit_leaderboard.csv",
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.info("当前活动暂无单位排行数据。")

    route_rows = _load_route_node_rows()
    st.download_button(
        "导出主线题库 JSON",
        data=export_rows_to_csv(
            [
                {
                    "id": item.get("id", ""),
                    "title": item.get("title", ""),
                    "date": item.get("date", ""),
                    "place": item.get("place", ""),
                    "route_stage": item.get("route_stage", ""),
                    "question": (item.get("quiz", {}) or {}).get("question", ""),
                    "answer": (item.get("quiz", {}) or {}).get("answer", ""),
                }
                for item in route_rows
            ]
        ),
        file_name="route_question_bank.csv",
        mime="text/csv",
        use_container_width=True,
    )

with status_tab:
    render_section("系统状态", "查看当前知识库样例、Provider 配置情况以及可对外开放的模型数量。")
    provider_configs = list_provider_configs(include_disabled=True)
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
    st.markdown("#### Provider 状态")
    st.dataframe(pd.DataFrame(provider_rows), use_container_width=True, hide_index=True)
    st.caption(f"配置目录：{CONFIG_DIR}")

    st.markdown("#### RAG 样例")
    for sample in status.get("metadata_samples", []):
        with st.expander(str(sample.get("metadata", {}).get("title", "未命名片段")), expanded=False):
            st.json(sample.get("metadata", {}))
            st.write(sample.get("preview", ""))
