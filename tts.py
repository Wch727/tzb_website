"""轻量文本转语音模块。"""

from __future__ import annotations

import asyncio
import hashlib
import math
import struct
import wave
from pathlib import Path
from typing import Dict

from utils import AUDIO_DIR

try:
    import edge_tts  # type: ignore
except Exception:  # pragma: no cover - 允许无 TTS 环境运行
    edge_tts = None


def _audio_basename(text: str, cache_key: str) -> str:
    """根据文本与缓存键生成稳定文件名。"""
    digest = hashlib.md5(f"{cache_key}:{text}".encode("utf-8")).hexdigest()[:16]
    return f"{cache_key}-{digest}"


def _write_mock_wav(path: Path, duration: float = 1.6, frequency: float = 523.25) -> Path:
    """在没有 TTS 依赖时生成占位提示音。"""
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
    """调用 edge-tts 保存音频。"""
    communicator = edge_tts.Communicate(text=text, voice=voice)
    await communicator.save(str(path))
    return path


def synthesize_text_to_audio(
    text: str,
    cache_key: str,
    voice: str = "zh-CN-XiaoxiaoNeural",
) -> Dict[str, str]:
    """将文本转为音频，优先使用 edge-tts，失败时回退到占位音频。"""
    cleaned = (text or "").strip()
    if not cleaned:
        cleaned = "当前节点暂无讲解内容，以下为演示音频。"

    basename = _audio_basename(cleaned[:500], cache_key)
    if edge_tts is not None:
        target = AUDIO_DIR / f"{basename}.mp3"
        if target.exists():
            return {"audio_path": str(target), "mode": "edge_tts"}
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            asyncio.run(_save_edge_tts(cleaned, target, voice=voice))
            return {"audio_path": str(target), "mode": "edge_tts"}
        except Exception:
            pass

    fallback = AUDIO_DIR / f"{basename}.wav"
    if not fallback.exists():
        _write_mock_wav(fallback)
    return {"audio_path": str(fallback), "mode": "mock_audio"}
