"""Image, audio, and lightweight digital-human presentation helpers."""

from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st

from content_store import load_image_map
from tts import resolve_existing_audio, synthesize_text_to_audio
from utils import AVATAR_DIR, BASE_DIR, IMAGE_DIR, get_settings

DEFAULT_GUIDE_AVATAR = "assets/avatar/guide_photo.jpg"


def _resolve_asset_path(path_like: str) -> Path:
    """Resolve relative asset paths against the project base directory."""
    path = Path(path_like)
    if path.is_absolute():
        return path
    return (BASE_DIR / path).resolve()


def _fallback_image_by_type(item_type: str) -> str:
    """Return the configured fallback artwork by content type."""
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
    """Convert titles or keys into a safe local image filename stem."""
    safe = "".join(char if char.isalnum() or char in ["_", "-"] else "_" for char in str(text or "").strip().lower())
    while "__" in safe:
        safe = safe.replace("__", "_")
    return safe.strip("_")


def _candidate_local_images(item: Dict[str, Any]) -> list[Path]:
    """Build candidate local image paths from explicit keys and ids."""
    image_key = str(item.get("image_key", "") or "").strip()
    candidates = []
    for candidate in [image_key, item.get("id", ""), item.get("title", "")]:
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
                resolved_paths.append(folder / f"{candidate}{suffix}")
    return resolved_paths


def resolve_image(item: Dict[str, Any]) -> Dict[str, Any]:
    """Resolve local, remote, fallback, or generated imagery for an exhibit item."""
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
    """Generate a simple exhibition-style placeholder artwork."""
    safe_title = html.escape(title or "长征史")
    safe_subtitle = html.escape(subtitle or "长征史展项")
    type_text = html.escape(str(item_type or "event"))
    return f"""
    <svg xmlns="http://www.w3.org/2000/svg" width="1200" height="720" viewBox="0 0 1200 720">
      <defs>
        <linearGradient id="bg" x1="0" x2="1" y1="0" y2="1">
          <stop offset="0%" stop-color="#8f1b3f"/>
          <stop offset="55%" stop-color="#b4435f"/>
          <stop offset="100%" stop-color="#d7a766"/>
        </linearGradient>
      </defs>
      <rect width="1200" height="720" rx="36" fill="url(#bg)"/>
      <circle cx="980" cy="120" r="120" fill="rgba(255,255,255,0.08)"/>
      <circle cx="170" cy="580" r="160" fill="rgba(255,255,255,0.08)"/>
      <text x="80" y="220" font-size="34" fill="#fcefd6" font-family="Microsoft YaHei">长征精神·沉浸式云端答题互动平台</text>
      <text x="80" y="360" font-size="76" fill="#fffaf0" font-family="Microsoft YaHei" font-weight="700">{safe_title}</text>
      <text x="80" y="430" font-size="32" fill="#fbe8cf" font-family="Microsoft YaHei">{safe_subtitle}</text>
      <text x="80" y="560" font-size="28" fill="#fce8cf" font-family="Microsoft YaHei">类型：{type_text}</text>
      <text x="80" y="610" font-size="26" fill="#fce8cf" font-family="Microsoft YaHei">沿着长征主线继续浏览，进入这一展项的历史场景与精神世界</text>
    </svg>
    """.strip()


def render_svg_artwork(svg_markup: str, caption: str = "") -> None:
    """Render SVG inline to avoid PIL svg decoding issues in Streamlit."""
    if not svg_markup:
        return
    normalized = re.sub(
        r"<svg\b",
        '<svg style="width:100%;height:auto;display:block;border-radius:22px;overflow:hidden;box-shadow:0 14px 34px rgba(72,48,29,0.08);"',
        svg_markup,
        count=1,
    )
    st.markdown(
        f"<div style='width:100%;margin:0.35rem 0 0.2rem;'>{normalized}</div>",
        unsafe_allow_html=True,
    )
    if caption:
        st.caption(caption)


def render_node_image(node: Dict[str, Any], caption: str = "") -> None:
    """Render node imagery with graceful fallback handling."""
    resolved = resolve_image(node)
    final_caption = caption or resolved.get("caption", "") or node.get("title", "")
    if resolved.get("mode") in ["local", "remote", "fallback_asset"] and resolved.get("path"):
        try:
            st.image(resolved["path"], caption=final_caption, width="stretch")
            return
        except Exception:
            pass

    render_svg_artwork(
        resolved.get("svg", generate_placeholder_svg(node.get("title", "长征史"), node.get("place", ""), node.get("type", "event"))),
        final_caption,
    )
    if get_settings().get("debug_image_resolver") and resolved.get("expected_filename"):
        st.caption(f"图片调试：期待文件名 {resolved['expected_filename']} | 当前模式 {resolved.get('mode', 'generated')}")


def _audio_state_keys(cache_key: str) -> tuple[str, str]:
    normalized = cache_key or "narration"
    return f"audio::{normalized}", f"audio_meta::{normalized}"


def _ensure_existing_audio(text: str, cache_key: str, voice: str) -> str:
    """Load an already-generated audio track into session state if present."""
    state_key, meta_key = _audio_state_keys(cache_key)
    existing_path = st.session_state.get(state_key, "")
    if existing_path and Path(existing_path).exists():
        return existing_path

    existing = resolve_existing_audio(text=text, cache_key=cache_key, voice=voice)
    if existing and Path(existing["audio_path"]).exists():
        st.session_state[state_key] = existing["audio_path"]
        st.session_state[meta_key] = existing
        return existing["audio_path"]
    return ""


def render_audio_player(
    text: str,
    cache_key: str,
    button_label: str = "播放语音讲解",
    voice: str = "zh-CN-XiaoxiaoNeural",
) -> str:
    """Render a narration audio control with synthesis + cache reuse."""
    state_key, meta_key = _audio_state_keys(cache_key)
    audio_path = _ensure_existing_audio(text=text, cache_key=cache_key, voice=voice)

    if st.button(button_label, key=f"btn::{cache_key}", width="stretch"):
        result = synthesize_text_to_audio(text=text, cache_key=cache_key, voice=voice)
        st.session_state[state_key] = result["audio_path"]
        st.session_state[meta_key] = result
        audio_path = result["audio_path"]

    if audio_path and Path(audio_path).exists():
        st.audio(audio_path)
    return audio_path


def _split_narration_sections(text: str) -> List[str]:
    """Split narration text into clean transcript blocks for the digital human."""
    content = (text or "").replace("\r", "\n").strip()
    if not content:
        return []

    blocks = [part.strip() for part in re.split(r"\n\s*\n", content) if part.strip()]
    if blocks and len(blocks[0]) <= 34 and any(
        marker in blocks[0] for marker in ("讲解稿", "讲解词", "讲述稿", "篇章讲述", "人物专题", "脚本")
    ):
        blocks = blocks[1:]
    return blocks[:6]


def _render_avatar_panel(avatar_path: str, caption: str) -> None:
    """Render avatar or fallback figure illustration."""
    resolved = _resolve_asset_path(avatar_path or DEFAULT_GUIDE_AVATAR)
    if resolved.exists():
        if resolved.suffix.lower() in [".mp4", ".mov", ".webm"]:
            st.video(str(resolved))
        elif resolved.suffix.lower() == ".svg":
            render_svg_artwork(resolved.read_text(encoding="utf-8"), caption)
        else:
            st.image(str(resolved), width="stretch")
            if caption:
                st.caption(caption)
    else:
        render_svg_artwork(generate_placeholder_svg("数字讲解员", caption or "长征主题讲解"), caption or "数字讲解员")


def render_digital_human(
    section_text: str,
    avatar_path: str,
    audio_path: str = "",
    *,
    title: str = "数字讲解员",
    subtitle: str = "",
    cache_key: str = "",
    voice: str = "zh-CN-XiaoxiaoNeural",
) -> None:
    """Render a lightweight digital-human block with audio + segmented transcript."""
    blocks = _split_narration_sections(section_text)
    if not section_text.strip():
        st.info("当前暂无可展示的讲解内容。")
        return

    resolved_audio_path = audio_path or ""
    if cache_key:
        resolved_audio_path = resolved_audio_path or _ensure_existing_audio(
            text=section_text,
            cache_key=cache_key,
            voice=voice,
        )

    header_html = f"""
    <div style="
        border-radius:24px;
        padding:1rem 1.05rem;
        background:linear-gradient(180deg, rgba(255,252,250,0.98), rgba(246,238,235,0.95));
        border:1px solid rgba(139,38,66,0.16);
        box-shadow:0 14px 36px rgba(78,16,33,0.08);
        margin:0.35rem 0 1rem;
    ">
        <div style="color:#8a2947;font-size:0.8rem;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:0.25rem;">数字讲解员</div>
        <div style="color:#5b112d;font-size:1.42rem;font-weight:700;margin-bottom:0.35rem;">{html.escape(title)}</div>
        <div style="color:#655448;font-size:0.96rem;line-height:1.76;">{html.escape(subtitle or '以正式讲解词、语音与字幕并行呈现当前展项内容。')}</div>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)

    left_col, right_col = st.columns([0.82, 1.18])
    with left_col:
        _render_avatar_panel(avatar_path, "讲解员形象")
        st.markdown(
            """
            <div style="
                border-radius:18px;
                padding:0.95rem 1rem;
                background:linear-gradient(180deg, rgba(255,252,250,0.98), rgba(248,240,237,0.96));
                border:1px solid rgba(139,38,66,0.12);
                margin-top:0.7rem;
            ">
                <div style="color:#8a2947;font-size:0.78rem;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:0.28rem;">讲解席位</div>
                <div style="color:#5b112d;font-size:1.06rem;font-weight:700;margin-bottom:0.25rem;">数字讲解员</div>
                <div style="color:#6a5a4d;font-size:0.92rem;line-height:1.72;">围绕正式讲解词、节点事实与主线线索同步展开讲述，适合在节点页、人物页和大关过场中持续播放。</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        status_label = "讲解音频已就绪" if resolved_audio_path and Path(resolved_audio_path).exists() else "讲解词已就绪"
        st.markdown(
            f"""
            <div style="
                border-radius:18px;
                padding:0.9rem 0.95rem;
                background:rgba(255,252,250,0.96);
                border:1px solid rgba(139,38,66,0.12);
                margin-top:0.6rem;
            ">
                <div style="color:#8a2947;font-size:0.78rem;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:0.25rem;">讲解状态</div>
                <div style="color:#5b112d;font-size:1.02rem;font-weight:700;margin-bottom:0.25rem;">{html.escape(status_label)}</div>
                <div style="color:#6a5a4d;font-size:0.9rem;line-height:1.7;">围绕正式讲解稿、节点事实与历史线索同步展开讲述。</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if cache_key and not resolved_audio_path:
            if st.button("准备讲解音频", key=f"digital_prepare::{cache_key}", width="stretch"):
                result = synthesize_text_to_audio(text=section_text, cache_key=cache_key, voice=voice)
                resolved_audio_path = result["audio_path"]
                state_key, meta_key = _audio_state_keys(cache_key)
                st.session_state[state_key] = resolved_audio_path
                st.session_state[meta_key] = result
        if resolved_audio_path and Path(resolved_audio_path).exists():
            st.audio(resolved_audio_path)

    with right_col:
        if blocks:
            for index, block in enumerate(blocks, start=1):
                st.markdown(
                    f"""
                    <div style="
                        border-radius:18px;
                        padding:0.9rem 1rem;
                        background:rgba(255,252,250,0.96);
                        border:1px solid rgba(139,38,66,0.12);
                        box-shadow:0 8px 24px rgba(78,16,33,0.05);
                        margin:0 0 0.75rem;
                    ">
                        <div style="color:#8a2947;font-size:0.78rem;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:0.28rem;">讲解片段 {index:02d}</div>
                        <div style="color:#352822;font-size:1rem;line-height:1.9;">{html.escape(block)}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                f"""
                <div style="
                    border-radius:18px;
                    padding:1rem 1.05rem;
                    background:rgba(255,252,250,0.96);
                    border:1px solid rgba(139,38,66,0.12);
                ">
                    <div style="color:#352822;font-size:1rem;line-height:1.92;">{html.escape(section_text)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
