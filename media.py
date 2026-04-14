"""图片、音频与数字人展示组件。"""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any, Dict

import streamlit as st

from content_store import load_image_map
from tts import synthesize_text_to_audio
from utils import AVATAR_DIR, BASE_DIR, IMAGE_DIR, get_settings


def _resolve_asset_path(path_like: str) -> Path:
    """将相对路径转为绝对路径。"""
    path = Path(path_like)
    if path.is_absolute():
        return path
    return (BASE_DIR / path).resolve()


def _fallback_image_by_type(item_type: str) -> str:
    """按类型返回默认占位图。"""
    fallback_map = load_image_map().get("fallbacks", {})
    normalized = str(item_type or "event").strip().lower()
    configured = (
        fallback_map.get(normalized)
        or fallback_map.get("default")
        or f"assets/images/fallback_{normalized}.svg"
    )
    candidates = [
        configured,
        f"assets/images/placeholders/placeholder_{normalized}.png",
        f"assets/images/placeholders/placeholder_{normalized}.jpg",
        f"assets/images/placeholders/placeholder_{normalized}.svg",
        "assets/images/placeholders/default.png",
        "assets/images/placeholders/default.svg",
        f"assets/images/fallback_{normalized}.svg",
        "assets/images/route_placeholder.svg",
    ]
    for candidate in candidates:
        resolved = _resolve_asset_path(candidate)
        if resolved.exists():
            return candidate
    return configured


def _slugify_filename(text: str) -> str:
    """将标题转换为适合查找图片的文件名。"""
    safe = "".join(char if char.isalnum() or char in ["_", "-"] else "_" for char in str(text or "").strip().lower())
    while "__" in safe:
        safe = safe.replace("__", "_")
    return safe.strip("_")


def _candidate_local_images(item: Dict[str, Any]) -> list[Path]:
    """构造候选本地图路径列表。"""
    image_key = str(item.get("image_key", "") or "").strip()
    candidates = []
    for candidate in [
        image_key,
        item.get("id", ""),
        item.get("title", ""),
    ]:
        candidate_text = str(candidate or "").strip()
        if not candidate_text:
            continue
        candidates.append(candidate_text)
        candidates.append(_slugify_filename(candidate_text))

    seen = set()
    resolved_paths: list[Path] = []
    search_dirs = [
        IMAGE_DIR / "nodes",
        IMAGE_DIR / "figures",
        IMAGE_DIR / "topics",
        IMAGE_DIR,
    ]
    suffixes = [".png", ".jpg", ".jpeg", ".webp", ".svg"]
    for candidate in candidates:
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        for folder in search_dirs:
            for suffix in suffixes:
                path = folder / f"{candidate}{suffix}"
                resolved_paths.append(path)
    return resolved_paths


def resolve_image(item: Dict[str, Any]) -> Dict[str, Any]:
    """统一解析图片来源，确保缺图时能优雅降级。"""
    title = str(item.get("title", "长征史展项") or "长征史展项")
    image_path = str(item.get("image", "") or "").strip()
    if image_path:
        resolved = _resolve_asset_path(image_path)
        if resolved.exists():
            return {
                "mode": "local",
                "path": str(resolved),
                "alt": item.get("image_alt", title),
                "caption": item.get("image_caption", "") or item.get("place", "") or title,
            }

    for candidate in _candidate_local_images(item):
        if candidate.exists():
            return {
                "mode": "local",
                "path": str(candidate),
                "alt": item.get("image_alt", title),
                "caption": item.get("image_caption", "") or item.get("place", "") or title,
                "expected_filename": candidate.name,
            }

    remote_image_url = str(item.get("remote_image_url", "") or "").strip()
    if remote_image_url:
        return {
            "mode": "remote",
            "path": remote_image_url,
            "alt": item.get("image_alt", title),
            "caption": item.get("image_caption", "") or item.get("place", "") or title,
            "expected_filename": _candidate_local_images(item)[0].name if _candidate_local_images(item) else "",
        }

    fallback_path = _fallback_image_by_type(item.get("type", "event"))
    if fallback_path:
        resolved = _resolve_asset_path(fallback_path)
        if resolved.exists():
            return {
                "mode": "fallback_asset",
                "path": str(resolved),
                "alt": item.get("image_alt", title),
                "caption": item.get("image_caption", "") or item.get("place", "") or title,
                "expected_filename": _candidate_local_images(item)[0].name if _candidate_local_images(item) else "",
            }

    subtitle = item.get("place", "") or item.get("summary", "")[:40] or "长征史展项"
    return {
        "mode": "generated",
        "path": "",
        "alt": item.get("image_alt", title),
        "caption": item.get("image_caption", "") or item.get("place", "") or title,
        "svg": generate_placeholder_svg(title, subtitle, item.get("type", "event")),
        "expected_filename": _candidate_local_images(item)[0].name if _candidate_local_images(item) else "",
    }


def generate_placeholder_svg(title: str, subtitle: str = "长征史展项", item_type: str = "event") -> str:
    """生成节点占位图。"""
    safe_title = html.escape(title or "长征史")
    safe_subtitle = html.escape(subtitle or "长征史展项")
    type_text = html.escape(str(item_type or "event"))
    return f"""
    <svg xmlns="http://www.w3.org/2000/svg" width="1200" height="720" viewBox="0 0 1200 720">
      <defs>
        <linearGradient id="bg" x1="0" x2="1" y1="0" y2="1">
          <stop offset="0%" stop-color="#6f2219"/>
          <stop offset="55%" stop-color="#a54c3a"/>
          <stop offset="100%" stop-color="#d2a15d"/>
        </linearGradient>
      </defs>
      <rect width="1200" height="720" rx="36" fill="url(#bg)"/>
      <circle cx="1000" cy="120" r="120" fill="rgba(255,255,255,0.08)"/>
      <circle cx="170" cy="580" r="160" fill="rgba(255,255,255,0.08)"/>
      <text x="80" y="220" font-size="34" fill="#fcefd6" font-family="Microsoft YaHei">长征史互动导览</text>
      <text x="80" y="360" font-size="76" fill="#fffaf0" font-family="Microsoft YaHei" font-weight="700">{safe_title}</text>
      <text x="80" y="430" font-size="32" fill="#fbe8cf" font-family="Microsoft YaHei">{safe_subtitle}</text>
      <text x="80" y="560" font-size="28" fill="#fce8cf" font-family="Microsoft YaHei">类型：{type_text}</text>
      <text x="80" y="610" font-size="26" fill="#fce8cf" font-family="Microsoft YaHei">沿着长征主线继续浏览，进入这一节点的历史场景与精神世界</text>
    </svg>
    """.strip()


def render_node_image(node: Dict[str, Any], caption: str = "") -> None:
    """展示节点图片，缺图时使用占位图。"""
    resolved = resolve_image(node)
    final_caption = caption or resolved.get("caption", "") or node.get("title", "")
    if resolved.get("mode") in ["local", "remote", "fallback_asset"] and resolved.get("path"):
        try:
            st.image(
                resolved["path"],
                caption=final_caption,
                width="stretch",
            )
            return
        except Exception:
            pass

    st.image(
        resolved.get("svg", generate_placeholder_svg(node.get("title", "长征史"), node.get("place", ""), node.get("type", "event"))).encode("utf-8"),
        width="stretch",
    )
    if final_caption:
        st.caption(final_caption)
    if get_settings().get("debug_image_resolver") and resolved.get("expected_filename"):
        st.caption(f"图片调试：期待文件名 {resolved['expected_filename']} | 当前模式 {resolved.get('mode', 'generated')}")


def render_audio_player(
    text: str,
    cache_key: str,
    button_label: str = "播放语音讲解",
    voice: str = "zh-CN-XiaoxiaoNeural",
) -> str:
    """渲染语音生成与播放控件。"""
    state_key = f"audio::{cache_key}"
    mode_key = f"audio_mode::{cache_key}"
    if st.button(button_label, key=f"btn::{cache_key}", width="stretch"):
        result = synthesize_text_to_audio(text=text, cache_key=cache_key, voice=voice)
        st.session_state[state_key] = result["audio_path"]
        st.session_state[mode_key] = result["mode"]

    audio_path = st.session_state.get(state_key, "")
    if audio_path and Path(audio_path).exists():
        st.audio(audio_path)
    return audio_path


def render_digital_human(section_text: str, avatar_path: str, audio_path: str = "") -> None:
    """渲染轻量数字人讲解区。"""
    st.markdown("#### 数字人讲解模式")
    col1, col2 = st.columns([1, 1.4])
    with col1:
        resolved = _resolve_asset_path(avatar_path or str(AVATAR_DIR / "guide.svg"))
        if resolved.exists():
            if resolved.suffix.lower() in [".mp4", ".mov", ".webm"]:
                st.video(str(resolved))
            else:
                st.image(str(resolved), width="stretch")
        else:
            st.image(generate_placeholder_svg("数字讲解员", "长征史导览").encode("utf-8"), width="stretch")
    with col2:
        st.markdown(
            """
            <div style="background:rgba(255,251,245,0.92);border:1px solid rgba(154,113,61,0.18);
            border-radius:22px;padding:1rem 1.1rem;line-height:1.9;">
            数字讲解员已进入当前展项讲解状态，形象、语音与讲解文本将同步呈现。
            </div>
            """,
            unsafe_allow_html=True,
        )
        if audio_path and Path(audio_path).exists():
            st.audio(audio_path)
        st.write(section_text)
