"""FastAPI 后端接口。"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from auth import admin_login, get_current_admin
from file_loader import load_file, persist_processed_text
from game import start_game, submit_choice
from generator import generate_guide_script, generate_short_video_script
from models import (
    AdminLoginRequest,
    AskRequest,
    GameChoiceRequest,
    GameStartRequest,
    GenerateGuideRequest,
    GenerateVideoRequest,
    ProviderFlagRequest,
    ProviderUpsertRequest,
    RetrievalTestRequest,
    UserSelectModelRequest,
)
from rag import (
    ask,
    delete_source_file_from_rag,
    get_rag_status,
    incremental_ingest,
    rebuild_knowledge_base,
    test_retrieval,
)
from utils import (
    PROCESSED_DIR,
    UPLOAD_DIR,
    get_provider_runtime_status,
    get_visible_user_models,
    is_allowed_file,
    is_user_key_allowed,
    is_user_visible_provider,
    list_provider_configs,
    list_uploaded_files,
    mask_secret,
    remove_if_exists,
    resolve_provider_config,
    safe_filename,
    save_binary_file,
    set_provider_allow_user_key,
    set_provider_enabled,
    set_provider_visibility,
    upsert_provider_config,
)

app = FastAPI(title="《长征精神·沉浸式云端答题互动平台》API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _sanitize_provider_for_admin(config: Dict[str, Any]) -> Dict[str, Any]:
    """避免直接暴露敏感 Key，但保留管理员所需状态。"""
    data = config.copy()
    runtime_status = get_provider_runtime_status(data.get("provider_name", ""))
    data["masked_api_key"] = mask_secret(data.get("api_key", ""))
    data["has_api_key"] = bool(data.get("api_key"))
    data["api_key_source"] = runtime_status.get("api_key_source", "missing")
    data["api_key_source_text"] = runtime_status.get("api_key_source_text", "未配置")
    data["api_key"] = ""
    return data


def _resolve_user_provider_config(
    provider_name: str,
    runtime_api_key: str = "",
) -> Dict[str, Any]:
    """解析普通用户可用的 provider 配置。"""
    if not is_user_visible_provider(provider_name):
        raise HTTPException(
            status_code=403,
            detail="当前模型未对普通用户开放，请在配置页选择管理员已开放的模型。",
        )
    if runtime_api_key and not is_user_key_allowed(provider_name):
        raise HTTPException(
            status_code=403,
            detail="当前模型不允许普通用户输入自己的 API Key，请改用管理员开放的默认配置。",
        )
    return resolve_provider_config(
        provider_name=provider_name,
        runtime_api_key=runtime_api_key if runtime_api_key else "",
    )


def _handle_provider_error(exc: ValueError) -> None:
    """将配置层错误转成 API 可读报错。"""
    raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/health")
def health() -> Dict[str, Any]:
    """健康检查。"""
    return {
        "status": "ok",
        "service": "long-march-mvp",
        "rag": get_rag_status(),
    }


@app.post("/admin/login")
def admin_login_api(payload: AdminLoginRequest) -> Dict[str, Any]:
    """管理员登录。"""
    return admin_login(payload.username, payload.password)


@app.post("/admin/upload")
async def admin_upload_api(
    file: UploadFile = File(...),
    _: Dict[str, Any] = Depends(get_current_admin),
) -> Dict[str, Any]:
    """管理员上传文件。"""
    filename = safe_filename(file.filename or "")
    if not filename or not is_allowed_file(filename):
        raise HTTPException(status_code=400, detail="文件后缀不被支持。")

    content = await file.read()
    target_path = save_binary_file(UPLOAD_DIR, filename, content)
    parsed = load_file(target_path)
    persist_processed_text(filename, parsed.get("raw_text", ""))

    return {
        "message": "文件上传成功。",
        "file": filename,
        "document_count": len(parsed.get("docs", [])),
        "processed_file": (PROCESSED_DIR / f"{Path(filename).stem}.txt").name,
    }


@app.get("/admin/files")
def admin_files_api(_: Dict[str, Any] = Depends(get_current_admin)) -> Dict[str, Any]:
    """查看上传文件列表。"""
    return {"files": list_uploaded_files()}


@app.delete("/admin/files/{filename}")
def admin_delete_file_api(
    filename: str,
    _: Dict[str, Any] = Depends(get_current_admin),
) -> Dict[str, Any]:
    """删除上传文件，并同步清理处理后的文本与向量数据。"""
    safe_name = safe_filename(filename)
    removed_upload = remove_if_exists(UPLOAD_DIR / safe_name)
    removed_processed = remove_if_exists(PROCESSED_DIR / f"{Path(safe_name).stem}.txt")
    rag_message = delete_source_file_from_rag(safe_name)

    if not removed_upload:
        raise HTTPException(status_code=404, detail="未找到要删除的文件。")

    return {
        "message": "文件删除成功。",
        "removed_upload": removed_upload,
        "removed_processed": removed_processed,
        "rag": rag_message,
    }


@app.post("/admin/rag/rebuild")
def admin_rag_rebuild_api(_: Dict[str, Any] = Depends(get_current_admin)) -> Dict[str, Any]:
    """重建知识库索引。"""
    return rebuild_knowledge_base()


@app.post("/admin/rag/ingest")
def admin_rag_ingest_api(_: Dict[str, Any] = Depends(get_current_admin)) -> Dict[str, Any]:
    """增量导入知识库。"""
    return incremental_ingest()


@app.get("/admin/rag/status")
def admin_rag_status_api(_: Dict[str, Any] = Depends(get_current_admin)) -> Dict[str, Any]:
    """查看知识库状态。"""
    return get_rag_status()


@app.post("/admin/rag/test_retrieval")
def admin_rag_test_retrieval_api(
    payload: RetrievalTestRequest,
    _: Dict[str, Any] = Depends(get_current_admin),
) -> Dict[str, Any]:
    """管理员测试检索命中情况。"""
    return test_retrieval(question=payload.question, filters=payload.filters, top_k=payload.top_k)


@app.get("/admin/providers")
def admin_providers_api(_: Dict[str, Any] = Depends(get_current_admin)) -> Dict[str, Any]:
    """查看 provider 配置。"""
    providers = [_sanitize_provider_for_admin(config) for config in list_provider_configs(include_disabled=True)]
    return {"providers": providers}


@app.post("/admin/providers")
def admin_add_provider_api(
    payload: ProviderUpsertRequest,
    _: Dict[str, Any] = Depends(get_current_admin),
) -> Dict[str, Any]:
    """新增 provider。"""
    try:
        saved = upsert_provider_config(payload.model_dump())
    except ValueError as exc:
        _handle_provider_error(exc)
    return {"message": "provider 已保存。", "provider": _sanitize_provider_for_admin(saved)}


@app.put("/admin/providers/{provider_name}")
def admin_update_provider_api(
    provider_name: str,
    payload: ProviderUpsertRequest,
    _: Dict[str, Any] = Depends(get_current_admin),
) -> Dict[str, Any]:
    """编辑 provider。"""
    data = payload.model_dump()
    data["provider_name"] = provider_name
    try:
        saved = upsert_provider_config(data)
    except ValueError as exc:
        _handle_provider_error(exc)
    return {"message": "provider 已更新。", "provider": _sanitize_provider_for_admin(saved)}


@app.post("/admin/providers/{provider_name}/enable")
def admin_enable_provider_api(
    provider_name: str,
    _: Dict[str, Any] = Depends(get_current_admin),
) -> Dict[str, Any]:
    """启用 provider。"""
    try:
        config = set_provider_enabled(provider_name, True)
    except ValueError as exc:
        _handle_provider_error(exc)
    return {"message": f"{provider_name} 已启用。", "provider": _sanitize_provider_for_admin(config)}


@app.post("/admin/providers/{provider_name}/disable")
def admin_disable_provider_api(
    provider_name: str,
    _: Dict[str, Any] = Depends(get_current_admin),
) -> Dict[str, Any]:
    """禁用 provider。"""
    try:
        config = set_provider_enabled(provider_name, False)
    except ValueError as exc:
        _handle_provider_error(exc)
    return {"message": f"{provider_name} 已禁用。", "provider": _sanitize_provider_for_admin(config)}


@app.post("/admin/providers/{provider_name}/visible")
def admin_visible_provider_api(
    provider_name: str,
    payload: ProviderFlagRequest,
    _: Dict[str, Any] = Depends(get_current_admin),
) -> Dict[str, Any]:
    """设置 provider 是否对普通用户可见。"""
    try:
        config = set_provider_visibility(provider_name, payload.value)
    except ValueError as exc:
        _handle_provider_error(exc)
    return {
        "message": f"{provider_name} 的用户可见性已更新。",
        "provider": _sanitize_provider_for_admin(config),
    }


@app.post("/admin/providers/{provider_name}/allow_user_key")
def admin_allow_user_key_api(
    provider_name: str,
    payload: ProviderFlagRequest,
    _: Dict[str, Any] = Depends(get_current_admin),
) -> Dict[str, Any]:
    """设置普通用户是否可以输入自己的 Key。"""
    try:
        config = set_provider_allow_user_key(provider_name, payload.value)
    except ValueError as exc:
        _handle_provider_error(exc)
    return {
        "message": f"{provider_name} 的用户 Key 权限已更新。",
        "provider": _sanitize_provider_for_admin(config),
    }


@app.get("/user/models")
def user_models_api() -> Dict[str, Any]:
    """获取管理员开放给普通用户的模型列表。"""
    return {"models": get_visible_user_models()}


@app.post("/user/select_model")
def user_select_model_api(payload: UserSelectModelRequest) -> Dict[str, Any]:
    """校验普通用户选择的模型。"""
    provider_config = _resolve_user_provider_config(
        provider_name=payload.provider_name,
        runtime_api_key=payload.api_key,
    )
    return {
        "message": "模型选择有效。",
        "selected_provider": {
            "provider_name": provider_config.get("provider_name", "mock"),
            "display_name": provider_config.get("display_name", provider_config.get("provider_name", "mock")),
            "model": provider_config.get("model", ""),
            "allow_user_key": is_user_key_allowed(payload.provider_name),
        },
        "provider_name": provider_config.get("provider_name", "mock"),
        "display_name": provider_config.get("display_name", provider_config.get("provider_name", "mock")),
        "model": provider_config.get("model", ""),
        "allow_user_key": is_user_key_allowed(payload.provider_name),
    }


@app.post("/user/ask")
def user_ask_api(payload: AskRequest) -> Dict[str, Any]:
    """普通用户长征史问答。"""
    provider_config = _resolve_user_provider_config(
        provider_name=payload.provider_name,
        runtime_api_key=payload.api_key,
    )
    return ask(
        question=payload.question,
        provider_config=provider_config,
        filters=payload.filters,
        top_k=payload.top_k,
    )


@app.post("/user/generate/guide")
def user_generate_guide_api(payload: GenerateGuideRequest) -> Dict[str, Any]:
    """普通用户生成讲解稿。"""
    provider_config = _resolve_user_provider_config(
        provider_name=payload.provider_name,
        runtime_api_key=payload.api_key,
    )
    return generate_guide_script(
        topic=payload.topic,
        audience=payload.audience,
        duration=payload.duration,
        provider_config=provider_config,
    )


@app.post("/user/generate/video")
def user_generate_video_api(payload: GenerateVideoRequest) -> Dict[str, Any]:
    """普通用户生成短视频脚本。"""
    provider_config = _resolve_user_provider_config(
        provider_name=payload.provider_name,
        runtime_api_key=payload.api_key,
    )
    return generate_short_video_script(
        topic=payload.topic,
        audience=payload.audience,
        style=payload.style,
        provider_config=provider_config,
    )


@app.post("/user/game/start")
def user_game_start_api(payload: GameStartRequest) -> Dict[str, Any]:
    """开始闯关。"""
    provider_config = _resolve_user_provider_config(
        provider_name=payload.provider_name,
        runtime_api_key=payload.api_key,
    )
    state = start_game(role=payload.role, provider_config=provider_config)
    return {
        "message": "闯关已开始。",
        "state": state,
    }


@app.post("/user/game/choice")
def user_game_choice_api(payload: GameChoiceRequest) -> Dict[str, Any]:
    """提交闯关答案。"""
    provider_config = _resolve_user_provider_config(
        provider_name=payload.provider_name,
        runtime_api_key=payload.api_key,
    )
    node_id = payload.node_id or payload.route_stage
    return submit_choice(
        current_state=payload.current_state,
        node_id=node_id,
        answer=payload.answer,
        provider_config=provider_config,
    )
