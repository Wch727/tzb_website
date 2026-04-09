"""文本切分工具。"""

from __future__ import annotations

from typing import Any, Dict, List


def chunk_text(text: str, chunk_size: int = 420, overlap: int = 80) -> List[str]:
    """按字符数做简洁切分，并保留重叠内容。"""
    text = (text or "").strip()
    if not text:
        return []
    if chunk_size <= 0:
        raise ValueError("chunk_size 必须大于 0。")
    if overlap >= chunk_size:
        overlap = 0

    chunks: List[str] = []
    start = 0
    step = chunk_size - overlap
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start += step
    return chunks


def attach_metadata(
    documents: List[Dict[str, Any]],
    chunk_size: int,
    overlap: int,
) -> List[Dict[str, Any]]:
    """将原始文档切分为带元数据的 chunk。"""
    prepared: List[Dict[str, Any]] = []
    for document in documents:
        text = document.get("text", "")
        metadata = document.get("metadata", {}).copy()
        pieces = chunk_text(text, chunk_size=chunk_size, overlap=overlap)
        source_file = metadata.get("source_file", "source")
        title = metadata.get("title", "未命名")
        for index, piece in enumerate(pieces):
            chunk_metadata = metadata.copy()
            chunk_metadata["chunk_index"] = index
            chunk_metadata["chunk_length"] = len(piece)
            chunk_metadata["chunk_id"] = f"{source_file}::{title}::{index}"
            prepared.append({"text": piece, "metadata": chunk_metadata})
    return prepared
