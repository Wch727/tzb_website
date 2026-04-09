"""图片、音频与数字人展示组件。"""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any, Dict

import streamlit as st

from content_store import load_image_map
from tts import synthesize_text_to_audio
from utils import AVATAR_DIR, BASE_DIR, IMAGE_DIR


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
    return (
        fallback_map.get(normalized)
        or fallback_map.get("default")
        or f"assets/images/fallback_{normalized}.svg"
    )


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

    remote_image_url = str(item.get("remote_image_url", "") or "").strip()
    if remote_image_url:
        return {
            "mode": "remote",
            "path": remote_image_url,
            "alt": item.get("image_alt", title),
            "caption": item.get("image_caption", "") or item.get("place", "") or title,
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
            }

    subtitle = item.get("place", "") or item.get("summary", "")[:40] or "长征史展项"
    return {
        "mode": "generated",
        "path": "",
        "alt": item.get("image_alt", title),
        "caption": item.get("image_caption", "") or item.get("place", "") or title,
        "svg": generate_placeholder_svg(title, subtitle, item.get("type", "event")),
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
      <text x="80" y="610" font-size="26" fill="#fce8cf" font-family="Microsoft YaHei">当前未检索到对应图片，系统已启用内置展项占位卡片</text>
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
                use_container_width=True,
            )
            return
        except Exception:
            pass

    st.image(
        resolved.get("svg", generate_placeholder_svg(node.get("title", "长征史"), node.get("place", ""), node.get("type", "event"))).encode("utf-8"),
        use_container_width=True,
    )
    if final_caption:
        st.caption(final_caption)


def render_audio_player(
    text: str,
    cache_key: str,
    button_label: str = "播放语音讲解",
    voice: str = "zh-CN-XiaoxiaoNeural",
) -> str:
    """渲染语音生成与播放控件。"""
    state_key = f"audio::{cache_key}"
    mode_key = f"audio_mode::{cache_key}"
    if st.button(button_label, key=f"btn::{cache_key}", use_container_width=True):
        result = synthesize_text_to_audio(text=text, cache_key=cache_key, voice=voice)
        st.session_state[state_key] = result["audio_path"]
        st.session_state[mode_key] = result["mode"]

    audio_path = st.session_state.get(state_key, "")
    if audio_path and Path(audio_path).exists():
        st.audio(audio_path)
        if st.session_state.get(mode_key) == "mock_audio":
            st.caption("当前为占位音频演示。安装并启用 edge-tts 后可生成真实中文播报。")
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
                st.image(str(resolved), use_container_width=True)
        else:
            st.image(generate_placeholder_svg("数字讲解员", "长征史导览").encode("utf-8"), use_container_width=True)
    with col2:
        st.markdown(
            """
            <div style="background:rgba(255,251,245,0.92);border:1px solid rgba(154,113,61,0.18);
            border-radius:22px;padding:1rem 1.1rem;line-height:1.9;">
            数字讲解员已进入节点讲解模式，当前区域将同步展示形象、音频与讲解文本。
            </div>
            """,
            unsafe_allow_html=True,
        )
        if audio_path and Path(audio_path).exists():
            st.audio(audio_path)
        st.write(section_text)
