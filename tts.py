"""Lightweight TTS helpers for exhibition narration."""

from __future__ import annotations

import asyncio
import hashlib
import math
import re
import struct
import wave
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from utils import AUDIO_DIR, get_settings

try:
    import edge_tts  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    edge_tts = None


DEFAULT_VOICE = "zh-CN-XiaoxiaoNeural"
PREBUILT_AUDIO_DIR = AUDIO_DIR / "prebuilt"
GENERATED_AUDIO_DIR = AUDIO_DIR / "cache"
SUPPORTED_AUDIO_SUFFIXES = (".mp3", ".wav", ".m4a", ".ogg")


def _clean_text(text: str) -> str:
    """Normalize narration text for stable cache keys and synthesis."""
    cleaned = re.sub(r"\s+", " ", str(text or "")).strip()
    return cleaned


def _safe_cache_key(cache_key: str) -> str:
    """Convert a cache key into a filesystem-safe slug."""
    safe = re.sub(r"[^0-9A-Za-z_\-\u4e00-\u9fff]+", "-", str(cache_key or "").strip())
    safe = re.sub(r"-{2,}", "-", safe).strip("-")
    return safe or "narration"


def _audio_basename(text: str, cache_key: str, voice: str) -> str:
    """Generate a stable basename from cache key + text + voice."""
    digest = hashlib.md5(f"{cache_key}:{voice}:{text}".encode("utf-8")).hexdigest()[:16]
    return f"{_safe_cache_key(cache_key)}-{digest}"


def _provider_order(preferred: str) -> List[str]:
    """Resolve provider fallback order."""
    normalized = (preferred or "auto").strip().lower()
    if normalized in {"google", "google_reserved", "gemini"}:
        return ["prebuilt", "google_reserved", "edge_tts", "mock_audio"]
    if normalized in {"edge", "edge_tts"}:
        return ["prebuilt", "edge_tts", "mock_audio"]
    if normalized in {"mock", "mock_audio"}:
        return ["prebuilt", "mock_audio"]
    return ["prebuilt", "edge_tts", "mock_audio"]


def _write_mock_wav(path: Path, duration: float = 1.8, frequency: float = 523.25) -> Path:
    """Generate a placeholder tone when no live TTS provider is available."""
    sample_rate = 22050
    amplitude = 9000
    total_frames = int(sample_rate * duration)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "w") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        for index in range(total_frames):
            fade = min(index / (sample_rate * 0.2), 1.0)
            fade_out = min((total_frames - index) / (sample_rate * 0.2), 1.0)
            envelope = min(fade, fade_out)
            value = int(amplitude * envelope * math.sin(2 * math.pi * frequency * (index / sample_rate)))
            handle.writeframes(struct.pack("<h", value))
    return path


async def _save_edge_tts(text: str, path: Path, voice: str) -> Path:
    """Persist synthesized mp3 with edge-tts."""
    communicator = edge_tts.Communicate(text=text, voice=voice)
    await communicator.save(str(path))
    return path


def _candidate_audio_paths(text: str, cache_key: str, voice: str) -> Iterable[Path]:
    """Yield likely prebuilt or generated audio file paths."""
    safe_key = _safe_cache_key(cache_key)
    basename = _audio_basename(text, cache_key, voice)

    direct_names = [safe_key, basename]
    search_roots = [PREBUILT_AUDIO_DIR, AUDIO_DIR, GENERATED_AUDIO_DIR]

    yielded: set[str] = set()
    for root in search_roots:
        for base in direct_names:
            for suffix in SUPPORTED_AUDIO_SUFFIXES:
                candidate = root / f"{base}{suffix}"
                key = str(candidate.resolve())
                if key not in yielded:
                    yielded.add(key)
                    yield candidate

    # Legacy/generated files may include a digest after the key prefix.
    for root in [GENERATED_AUDIO_DIR, AUDIO_DIR]:
        if not root.exists():
            continue
        for suffix in SUPPORTED_AUDIO_SUFFIXES:
            for candidate in root.rglob(f"{safe_key}*{suffix}"):
                key = str(candidate.resolve())
                if key not in yielded:
                    yielded.add(key)
                    yield candidate


def resolve_existing_audio(text: str, cache_key: str, voice: str = DEFAULT_VOICE) -> Optional[Dict[str, str]]:
    """Find an already available audio asset for the narration."""
    for path in _candidate_audio_paths(_clean_text(text), cache_key, voice):
        if not path.exists():
            continue
        path_str = str(path)
        if PREBUILT_AUDIO_DIR in path.parents:
            mode = "prebuilt"
        elif path.suffix.lower() == ".mp3":
            mode = "edge_tts"
        else:
            mode = "mock_audio"
        return {
            "audio_path": path_str,
            "mode": mode,
            "provider": mode,
            "voice": voice,
            "cache_key": _safe_cache_key(cache_key),
        }
    return None


def get_tts_settings() -> Dict[str, str]:
    """Read TTS defaults from settings while keeping local fallbacks."""
    settings = get_settings()
    provider = str(settings.get("tts_provider", "auto") or "auto")
    voice = str(settings.get("tts_voice", DEFAULT_VOICE) or DEFAULT_VOICE)
    return {"provider": provider, "voice": voice}


def synthesize_text_to_audio(
    text: str,
    cache_key: str,
    voice: str = DEFAULT_VOICE,
    provider: str = "auto",
) -> Dict[str, str]:
    """Create or reuse narration audio with provider fallback."""
    cleaned = _clean_text(text)
    if not cleaned:
        cleaned = "欢迎进入长征主题展项，请沿着主线继续浏览。"

    settings = get_tts_settings()
    resolved_voice = voice or settings["voice"]
    provider_order = _provider_order(provider or settings["provider"])

    existing = resolve_existing_audio(cleaned, cache_key, voice=resolved_voice)
    if existing:
        return existing

    basename = _audio_basename(cleaned[:1200], cache_key, resolved_voice)

    for provider_name in provider_order:
        if provider_name == "prebuilt":
            continue

        if provider_name == "google_reserved":
            # We intentionally reserve the slot for a future Google provider,
            # but fall through locally for contest stability.
            continue

        if provider_name == "edge_tts" and edge_tts is not None:
            target = GENERATED_AUDIO_DIR / f"{basename}.mp3"
            if target.exists():
                return {
                    "audio_path": str(target),
                    "mode": "edge_tts",
                    "provider": "edge_tts",
                    "voice": resolved_voice,
                    "cache_key": _safe_cache_key(cache_key),
                }
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                asyncio.run(_save_edge_tts(cleaned, target, voice=resolved_voice))
                return {
                    "audio_path": str(target),
                    "mode": "edge_tts",
                    "provider": "edge_tts",
                    "voice": resolved_voice,
                    "cache_key": _safe_cache_key(cache_key),
                }
            except Exception:
                continue

        if provider_name == "mock_audio":
            fallback = GENERATED_AUDIO_DIR / f"{basename}.wav"
            if not fallback.exists():
                _write_mock_wav(fallback)
            return {
                "audio_path": str(fallback),
                "mode": "mock_audio",
                "provider": "mock_audio",
                "voice": resolved_voice,
                "cache_key": _safe_cache_key(cache_key),
            }

    fallback = GENERATED_AUDIO_DIR / f"{basename}.wav"
    if not fallback.exists():
        _write_mock_wav(fallback)
    return {
        "audio_path": str(fallback),
        "mode": "mock_audio",
        "provider": "mock_audio",
        "voice": resolved_voice,
        "cache_key": _safe_cache_key(cache_key),
    }
