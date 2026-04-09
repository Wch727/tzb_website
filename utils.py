"""项目通用工具函数。"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

BASE_DIR = Path(__file__).resolve().parent
CONFIG_DIR = BASE_DIR / "config"
STORAGE_DIR = BASE_DIR / "storage"
ASSETS_DIR = BASE_DIR / "assets"
IMAGE_DIR = ASSETS_DIR / "images"
AUDIO_DIR = ASSETS_DIR / "audio"
AVATAR_DIR = ASSETS_DIR / "avatar"
UPLOAD_DIR = STORAGE_DIR / "uploads"
PROCESSED_DIR = STORAGE_DIR / "processed"
CHROMA_DIR = STORAGE_DIR / "chroma_db"
RUNTIME_DIR = STORAGE_DIR / "runtime_sessions"
DATA_DIR = BASE_DIR / "data"

DEFAULT_SETTINGS: Dict[str, Any] = {
    "app_name": "《长征史》交互式 AI 导览与闯关学习系统",
    "collection_name": "long_march_history",
    "chunk_size": 420,
    "chunk_overlap": 80,
    "retrieval_top_k": 4,
    "max_preview_chars": 180,
    "default_topic": "长征史",
    "default_provider": "mock",
    "default_model": "mock-longmarch-v1",
    "allow_mock_provider": True,
    "supported_extensions": [".txt", ".md", ".pdf", ".docx", ".json", ".csv"],
}

PROVIDER_KEYS = [
    "provider_name",
    "display_name",
    "provider",
    "base_url",
    "api_key",
    "api_key_secret_name",
    "model",
    "enabled",
    "visible_to_users",
    "allow_user_key",
    "description",
]

PROVIDER_SECRET_NAME_MAP = {
    "moonshot": "MOONSHOT_API_KEY",
    "qwen": "DASHSCOPE_API_KEY",
    "minimax": "MINIMAX_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
}


def ensure_directories() -> None:
    """确保运行所需目录全部存在。"""
    for path in [
        CONFIG_DIR,
        STORAGE_DIR,
        ASSETS_DIR,
        IMAGE_DIR,
        AUDIO_DIR,
        AVATAR_DIR,
        UPLOAD_DIR,
        PROCESSED_DIR,
        CHROMA_DIR,
        RUNTIME_DIR,
        DATA_DIR,
    ]:
        path.mkdir(parents=True, exist_ok=True)


def read_yaml(path: Path, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """读取 YAML 文件。"""
    if not path.exists():
        return default or {}
    content = path.read_text(encoding="utf-8").strip()
    if not content:
        return default or {}
    return yaml.safe_load(content) or (default or {})


def write_yaml(path: Path, data: Dict[str, Any]) -> None:
    """写入 YAML 文件。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def read_json(path: Path, default: Optional[Any] = None) -> Any:
    """读取 JSON 文件。"""
    if not path.exists():
        return default
    content = path.read_text(encoding="utf-8").strip()
    if not content:
        return default
    return json.loads(content)


def write_json(path: Path, data: Any) -> None:
    """写入 JSON 文件。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def get_settings() -> Dict[str, Any]:
    """读取系统设置。"""
    settings = DEFAULT_SETTINGS.copy()
    settings.update(read_yaml(CONFIG_DIR / "system_settings.yaml", {}))
    return settings


def update_settings(patch: Dict[str, Any]) -> Dict[str, Any]:
    """更新系统设置。"""
    settings = get_settings()
    settings.update(patch)
    write_yaml(CONFIG_DIR / "system_settings.yaml", settings)
    return settings


def allowed_extensions() -> List[str]:
    """返回允许上传的后缀列表。"""
    return [suffix.lower() for suffix in get_settings().get("supported_extensions", [])]


def safe_filename(filename: str) -> str:
    """生成安全文件名，防止路径穿越。"""
    base_name = Path(filename).name
    sanitized = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff._-]", "_", base_name)
    return sanitized or "uploaded_file"


def is_allowed_file(filename: str) -> bool:
    """检查文件后缀是否合法。"""
    return Path(filename).suffix.lower() in allowed_extensions()


def save_binary_file(directory: Path, filename: str, data: bytes) -> Path:
    """保存二进制文件。"""
    ensure_directories()
    safe_name = safe_filename(filename)
    target_path = directory / safe_name
    target_path.write_bytes(data)
    return target_path


def save_text_file(directory: Path, filename: str, content: str) -> Path:
    """保存文本文件。"""
    ensure_directories()
    safe_name = safe_filename(filename)
    target_path = directory / safe_name
    target_path.write_text(content, encoding="utf-8")
    return target_path


def processed_filename(source_filename: str) -> str:
    """生成处理后文本文件名。"""
    stem = Path(source_filename).stem
    return f"{safe_filename(stem)}.txt"


def mask_secret(secret: str) -> str:
    """遮挡敏感信息。"""
    if not secret:
        return ""
    if len(secret) <= 6:
        return "*" * len(secret)
    return f"{secret[:3]}***{secret[-3:]}"


def now_text() -> str:
    """返回当前时间字符串。"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def file_stat_dict(path: Path) -> Dict[str, Any]:
    """生成文件状态字典。"""
    stat = path.stat()
    processed_path = PROCESSED_DIR / processed_filename(path.name)
    return {
        "filename": path.name,
        "size_bytes": stat.st_size,
        "size_kb": round(stat.st_size / 1024, 2),
        "modified_at": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
        "processed_exists": processed_path.exists(),
        "processed_file": processed_path.name,
    }


def list_uploaded_files() -> List[Dict[str, Any]]:
    """列出当前已上传文件。"""
    ensure_directories()
    files = [path for path in UPLOAD_DIR.iterdir() if path.is_file()]
    return [file_stat_dict(path) for path in sorted(files, key=lambda item: item.name.lower())]


def remove_if_exists(path: Path) -> bool:
    """如果文件存在则删除。"""
    if path.exists():
        path.unlink()
        return True
    return False


def load_admin_users() -> List[Dict[str, Any]]:
    """读取管理员账号列表。"""
    data = read_yaml(CONFIG_DIR / "admin_users.yaml", {"admins": []})
    admins = data.get("admins", [])
    if admins:
        return admins
    return [{"username": "admin", "display_name": "管理员"}]


def get_streamlit_secret(name: str, default: str = "") -> str:
    """从 Streamlit Secrets 读取配置。"""
    if not name:
        return default
    try:
        import streamlit as st

        value = st.secrets.get(name, default)
        if value in (None, ""):
            return default
        return str(value).strip()
    except Exception:
        return default


def get_env_value(name: str, default: str = "") -> str:
    """从环境变量读取配置。"""
    if not name:
        return default
    return str(os.getenv(name, default) or "").strip()


def get_secret_or_env(name: str, default: str = "") -> str:
    """按优先级读取 Streamlit Secrets 与环境变量。"""
    secret_value = get_streamlit_secret(name, "")
    if secret_value:
        return secret_value
    env_value = get_env_value(name, "")
    if env_value:
        return env_value
    return default


def resolve_secret_value_with_source(name: str) -> Dict[str, str]:
    """返回某个 Secrets/环境变量配置的取值与来源。"""
    secret_value = get_streamlit_secret(name, "")
    if secret_value:
        return {"value": secret_value, "source": "streamlit_secrets"}
    env_value = get_env_value(name, "")
    if env_value:
        return {"value": env_value, "source": "environment"}
    return {"value": "", "source": "missing"}


def describe_secret_source(source: str) -> str:
    """将密钥来源转换成可读中文。"""
    mapping = {
        "session": "当前会话输入",
        "streamlit_secrets": "Streamlit Secrets",
        "environment": "环境变量",
        "config": "本地配置文件",
        "missing": "未配置",
    }
    return mapping.get(source, source or "未配置")


def get_admin_password() -> str:
    """读取管理员密码，优先使用 Secrets / 环境变量。"""
    return get_secret_or_env("ADMIN_PASSWORD", "")


def default_secret_name_for_provider(provider_name: str) -> str:
    """获取 provider 默认对应的 Secrets 名称。"""
    return PROVIDER_SECRET_NAME_MAP.get(str(provider_name or "").strip().lower(), "")


def normalize_knowledge_type(raw_type: str) -> str:
    """统一知识类型名称，兼容旧数据。"""
    mapping = {
        "events": "event",
        "event": "event",
        "figures": "figure",
        "figure": "figure",
        "places": "place",
        "place": "place",
        "routes": "route",
        "route": "route",
        "faq": "faq",
        "faqs": "faq",
        "spirit": "spirit",
        "spirits": "spirit",
        "timeline": "route",
        "uploaded": "event",
        "reference": "event",
    }
    normalized = str(raw_type or "").strip().lower()
    return mapping.get(normalized, normalized or "event")


def infer_knowledge_type(title: str, text: str = "") -> str:
    """根据标题和文本推断知识类型。"""
    haystack = f"{title}\n{text}".lower()
    if any(keyword in haystack for keyword in ["精神", "意义", "启示", "信念"]):
        return "spirit"
    if any(keyword in haystack for keyword in ["问答", "faq", "常见问题", "为什么", "是什么"]):
        return "faq"
    if any(keyword in haystack for keyword in ["路线", "行军", "会师", "渡江", "泸定桥", "赤水"]):
        return "route"
    if any(keyword in haystack for keyword in ["人物", "毛泽东", "周恩来", "朱德", "陈云"]):
        return "figure"
    if any(keyword in haystack for keyword in ["地点", "旧址", "瑞金", "遵义", "会宁", "泸定"]):
        return "place"
    return "event"


def normalize_provider_config(config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """统一 provider 配置结构并兼容旧字段。"""
    config = config or {}
    provider_name = str(config.get("provider_name") or config.get("provider") or "").strip() or "mock"
    provider = str(config.get("provider") or provider_name).strip() or provider_name
    display_name = str(config.get("display_name") or provider_name).strip() or provider_name
    api_key_secret_name = str(
        config.get("api_key_secret_name") or default_secret_name_for_provider(provider_name)
    ).strip()
    visible_to_users = bool(config.get("visible_to_users", config.get("visible_to_user", True)))
    allow_user_key = bool(config.get("allow_user_key", provider_name == "mock"))
    normalized = {
        "provider_name": provider_name,
        "display_name": display_name,
        "provider": provider,
        "base_url": str(config.get("base_url", "") or "").strip(),
        "api_key": str(config.get("api_key", "") or "").strip(),
        "api_key_secret_name": api_key_secret_name,
        "model": str(config.get("model", "") or "").strip(),
        "enabled": bool(config.get("enabled", False)),
        "visible_to_users": visible_to_users,
        "visible_to_user": visible_to_users,
        "allow_user_key": allow_user_key,
        "description": str(config.get("description", "") or "").strip(),
    }
    return normalized


def load_provider_store() -> Dict[str, Any]:
    """读取 provider 配置。"""
    ensure_directories()
    raw = read_yaml(CONFIG_DIR / "enabled_models.yaml", {"providers": {}})
    providers = raw.get("providers", {})
    if not isinstance(providers, dict):
        return {}
    normalized: Dict[str, Any] = {}
    for key, value in providers.items():
        config = normalize_provider_config(value if isinstance(value, dict) else {"provider_name": key})
        normalized[config["provider_name"]] = config
    return normalized


def save_provider_store(providers: Dict[str, Any]) -> None:
    """保存 provider 配置。"""
    normalized: Dict[str, Any] = {}
    for key, value in providers.items():
        config = normalize_provider_config(value if isinstance(value, dict) else {"provider_name": key})
        normalized[config["provider_name"]] = {field: config.get(field) for field in PROVIDER_KEYS}
    write_yaml(CONFIG_DIR / "enabled_models.yaml", {"providers": normalized})


def list_provider_configs(include_disabled: bool = True) -> List[Dict[str, Any]]:
    """列出 provider 配置。"""
    providers = load_provider_store()
    items: List[Dict[str, Any]] = []
    for _, config in providers.items():
        if include_disabled or config.get("enabled"):
            items.append(config.copy())
    return sorted(items, key=lambda item: item.get("provider_name", ""))


def get_provider_config(provider_name: str) -> Optional[Dict[str, Any]]:
    """按名称获取 provider 配置。"""
    providers = load_provider_store()
    config = providers.get(provider_name)
    return config.copy() if config else None


def get_default_provider_name() -> str:
    """返回系统默认 provider。"""
    settings = get_settings()
    provider_name = str(settings.get("default_provider", "") or "").strip()
    if provider_name:
        config = get_provider_config(provider_name)
        if config and config.get("enabled"):
            return provider_name

    for config in list_provider_configs(include_disabled=False):
        if config.get("visible_to_users"):
            return config.get("provider_name", "mock")
    return "mock"


def get_default_provider_config() -> Dict[str, Any]:
    """获取系统默认 provider 配置。"""
    default_name = get_default_provider_name()
    return resolve_provider_config(default_name)


def get_visible_user_models() -> List[Dict[str, Any]]:
    """获取对普通用户可见的模型列表。"""
    default_provider = get_default_provider_name()
    models: List[Dict[str, Any]] = []
    for config in list_provider_configs(include_disabled=False):
        if not config.get("visible_to_users"):
            continue
        models.append(
            {
                "provider_name": config.get("provider_name", ""),
                "display_name": config.get("display_name", config.get("provider_name", "")),
                "provider": config.get("provider", config.get("provider_name", "")),
                "model": config.get("model", ""),
                "enabled": bool(config.get("enabled", False)),
                "visible_to_users": bool(config.get("visible_to_users", True)),
                "allow_user_key": bool(config.get("allow_user_key", False)),
                "description": config.get("description", ""),
                "is_default": config.get("provider_name") == default_provider,
            }
        )

    if not models:
        mock_config = get_provider_config("mock")
        if mock_config:
            models.append(
                {
                    "provider_name": mock_config.get("provider_name", "mock"),
                    "display_name": mock_config.get("display_name", "本地演示模型"),
                    "provider": mock_config.get("provider", "mock"),
                    "model": mock_config.get("model", "mock-longmarch-v1"),
                    "enabled": bool(mock_config.get("enabled", True)),
                    "visible_to_users": bool(mock_config.get("visible_to_users", True)),
                    "allow_user_key": bool(mock_config.get("allow_user_key", False)),
                    "description": mock_config.get("description", ""),
                    "is_default": True,
                }
            )
    return models


def is_user_visible_provider(provider_name: str) -> bool:
    """判断某个 provider 是否对普通用户开放。"""
    config = get_provider_config(provider_name)
    if not config:
        return False
    return bool(config.get("enabled")) and bool(config.get("visible_to_users"))


def is_user_key_allowed(provider_name: str) -> bool:
    """判断普通用户是否允许为某个 provider 输入自己的 Key。"""
    config = get_provider_config(provider_name)
    if not config:
        return False
    return bool(config.get("enabled")) and bool(config.get("visible_to_users")) and bool(
        config.get("allow_user_key")
    )


def upsert_provider_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """新增或更新 provider 配置。"""
    providers = load_provider_store()
    normalized = normalize_provider_config(config)
    provider_name = normalized["provider_name"]
    if provider_name in providers and not normalized["api_key"]:
        normalized["api_key"] = providers[provider_name].get("api_key", "")
    if provider_name in providers and not normalized["api_key_secret_name"]:
        normalized["api_key_secret_name"] = providers[provider_name].get("api_key_secret_name", "")
    providers[provider_name] = normalized
    save_provider_store(providers)

    settings = get_settings()
    if settings.get("default_provider") == provider_name and normalized.get("model"):
        update_settings({"default_model": normalized["model"]})
    return normalize_provider_config(providers[provider_name])


def set_provider_enabled(provider_name: str, enabled: bool) -> Dict[str, Any]:
    """启用或禁用 provider。"""
    providers = load_provider_store()
    if provider_name not in providers:
        raise ValueError(f"未找到 provider：{provider_name}")
    providers[provider_name]["enabled"] = enabled
    save_provider_store(providers)
    return normalize_provider_config(providers[provider_name])


def set_provider_visibility(provider_name: str, visible_to_users: bool) -> Dict[str, Any]:
    """设置 provider 是否对普通用户可见。"""
    providers = load_provider_store()
    if provider_name not in providers:
        raise ValueError(f"未找到 provider：{provider_name}")
    providers[provider_name]["visible_to_users"] = visible_to_users
    providers[provider_name]["visible_to_user"] = visible_to_users
    save_provider_store(providers)
    return normalize_provider_config(providers[provider_name])


def set_provider_allow_user_key(provider_name: str, allow_user_key: bool) -> Dict[str, Any]:
    """设置普通用户是否可为 provider 输入自己的 Key。"""
    providers = load_provider_store()
    if provider_name not in providers:
        raise ValueError(f"未找到 provider：{provider_name}")
    providers[provider_name]["allow_user_key"] = allow_user_key
    save_provider_store(providers)
    return normalize_provider_config(providers[provider_name])


def set_default_provider(provider_name: str) -> Dict[str, Any]:
    """设置系统默认 provider。"""
    config = get_provider_config(provider_name)
    if not config:
        raise ValueError(f"未找到 provider：{provider_name}")
    if not config.get("enabled"):
        raise ValueError("默认 provider 必须处于启用状态。")
    update_settings(
        {
            "default_provider": provider_name,
            "default_model": config.get("model", ""),
        }
    )
    return normalize_provider_config(config)


def get_provider_runtime_status(provider_name: str, runtime_api_key: str = "") -> Dict[str, Any]:
    """分析 provider 实际运行时使用的密钥来源。"""
    config = normalize_provider_config(get_provider_config(provider_name))
    if runtime_api_key:
        return {
            "provider_name": provider_name,
            "api_key": runtime_api_key,
            "api_key_source": "session",
            "api_key_source_text": describe_secret_source("session"),
            "api_key_secret_name": config.get("api_key_secret_name", ""),
        }

    secret_name = config.get("api_key_secret_name", "") or default_secret_name_for_provider(provider_name)
    if secret_name:
        secret_status = resolve_secret_value_with_source(secret_name)
        if secret_status["value"]:
            return {
                "provider_name": provider_name,
                "api_key": secret_status["value"],
                "api_key_source": secret_status["source"],
                "api_key_source_text": describe_secret_source(secret_status["source"]),
                "api_key_secret_name": secret_name,
            }

    if config.get("api_key"):
        return {
            "provider_name": provider_name,
            "api_key": config.get("api_key", ""),
            "api_key_source": "config",
            "api_key_source_text": describe_secret_source("config"),
            "api_key_secret_name": secret_name,
        }

    return {
        "provider_name": provider_name,
        "api_key": "",
        "api_key_source": "missing",
        "api_key_source_text": describe_secret_source("missing"),
        "api_key_secret_name": secret_name,
    }


def resolve_provider_config(
    provider_name: str,
    runtime_api_key: str = "",
    runtime_model: str = "",
    runtime_base_url: str = "",
) -> Dict[str, Any]:
    """合并管理员配置与用户会话输入。"""
    config = get_provider_config(provider_name) or {
        "provider_name": "mock",
        "display_name": "本地演示模型",
        "provider": "mock",
        "base_url": "",
        "api_key": "",
        "model": "mock-longmarch-v1",
        "enabled": True,
        "visible_to_users": True,
        "allow_user_key": False,
        "description": "本地演示模型。",
    }
    merged = normalize_provider_config(config)
    runtime_status = get_provider_runtime_status(provider_name=merged.get("provider_name", provider_name), runtime_api_key=runtime_api_key)
    merged["api_key"] = runtime_status.get("api_key", "")
    merged["api_key_source"] = runtime_status.get("api_key_source", "missing")
    merged["api_key_source_text"] = runtime_status.get("api_key_source_text", "未配置")
    if runtime_status.get("api_key_secret_name"):
        merged["api_key_secret_name"] = runtime_status.get("api_key_secret_name", "")
    if runtime_model:
        merged["model"] = runtime_model
    if runtime_base_url:
        merged["base_url"] = runtime_base_url
    return merged


def normalize_answer(text: str) -> str:
    """用于闯关比对答案的简易归一化。"""
    lowered = text.strip().lower()
    return re.sub(r"[\s，。！？,.!?:：；;（）()\[\]\"'“”‘’、]+", "", lowered)


ensure_directories()
