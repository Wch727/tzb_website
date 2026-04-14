"""文本切分工具。"""

from __future__ import annotations

import re
from typing import Any, Dict, List


def chunk_text(text: str, chunk_size: int = 420, overlap: int = 80) -> List[str]:
    """按字符数做兼容性的基础切分。"""
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


def _split_paragraphs(text: str) -> List[str]:
    """优先按段落拆分文本。"""
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", str(text or "").strip()) if part.strip()]
    if paragraphs:
        return paragraphs
    return [line.strip() for line in str(text or "").splitlines() if line.strip()]


def _split_long_paragraph(paragraph: str, chunk_size: int) -> List[str]:
    """把过长段落再按句子切开。"""
    paragraph = str(paragraph or "").strip()
    if not paragraph:
        return []
    if len(paragraph) <= chunk_size:
        return [paragraph]

    sentences = re.split(r"(?<=[。！？；])", paragraph)
    pieces: List[str] = []
    buffer = ""
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        candidate = f"{buffer}{sentence}".strip()
        if len(candidate) <= chunk_size:
            buffer = candidate
            continue
        if buffer:
            pieces.append(buffer)
        buffer = sentence
        while len(buffer) > chunk_size:
            pieces.append(buffer[:chunk_size].strip())
            buffer = buffer[chunk_size:].strip()
    if buffer:
        pieces.append(buffer)
    return pieces or [paragraph]


def _tail_overlap(text: str, overlap: int) -> str:
    """从上一块尾部取较平滑的重叠片段。"""
    if overlap <= 0:
        return ""
    snippet = str(text or "")[-overlap:].strip()
    if not snippet:
        return ""
    split_points = [snippet.rfind(mark) for mark in ["。", "！", "？", "；", "\n"]]
    cut = max(split_points)
    if cut > 0 and cut < len(snippet) - 8:
        return snippet[cut + 1 :].strip()
    return snippet


def _build_prefix(metadata: Dict[str, Any]) -> str:
    """为 chunk 生成标题前缀。"""
    prefix_parts: List[str] = []
    for value in [metadata.get("chapter_title", ""), metadata.get("section_title", ""), metadata.get("title", "")]:
        value = str(value or "").strip()
        if value and value not in prefix_parts:
            prefix_parts.append(value)
    return "\n".join(f"【{value}】" for value in prefix_parts).strip()


def _chunk_document_text(text: str, metadata: Dict[str, Any], chunk_size: int, overlap: int) -> List[str]:
    """按标题感知与段落优先的方式切分单个文档。"""
    prefix = _build_prefix(metadata)
    source_type = str(metadata.get("source_type", "") or "")
    if bool(metadata.get("pre_chunked")):
        prepared_text = str(text or "").strip()
        if not prepared_text:
            return []
        return [prepared_text]
    if source_type == "structured_card":
        structured_text = f"{prefix}\n{text}".strip() if prefix else str(text or "").strip()
        return [structured_text]

    prefix_len = len(prefix) + 1 if prefix else 0
    body_limit = max(180, chunk_size - prefix_len)

    raw_paragraphs = _split_paragraphs(text)
    paragraphs: List[str] = []
    for paragraph in raw_paragraphs:
        paragraphs.extend(_split_long_paragraph(paragraph, body_limit))

    chunks: List[str] = []
    body_buffer = ""
    for paragraph in paragraphs:
        candidate_body = f"{body_buffer}\n\n{paragraph}".strip() if body_buffer else paragraph
        candidate_text = f"{prefix}\n{candidate_body}".strip() if prefix else candidate_body
        if len(candidate_text) <= chunk_size:
            body_buffer = candidate_body
            continue
        if body_buffer:
            chunks.append(f"{prefix}\n{body_buffer}".strip() if prefix else body_buffer)
            overlap_text = _tail_overlap(body_buffer, overlap)
            body_buffer = f"{overlap_text}\n\n{paragraph}".strip() if overlap_text else paragraph
        else:
            chunks.append(candidate_text[:chunk_size].strip())
            body_buffer = ""

    if body_buffer:
        chunks.append(f"{prefix}\n{body_buffer}".strip() if prefix else body_buffer)
    return [chunk for chunk in chunks if chunk.strip()]


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
        pieces = _chunk_document_text(text, metadata=metadata, chunk_size=chunk_size, overlap=overlap)
        source_file = metadata.get("source_file", "source")
        title = metadata.get("title", "未命名")
        source_page = metadata.get("source_page", "")
        for index, piece in enumerate(pieces):
            chunk_metadata = metadata.copy()
            chunk_metadata["chunk_index"] = index
            chunk_metadata["chunk_length"] = len(piece)
            existing_chunk_id = str(chunk_metadata.get("chunk_id", "") or "").strip()
            if chunk_metadata.get("pre_chunked") and existing_chunk_id:
                chunk_metadata["chunk_id"] = existing_chunk_id
            else:
                chunk_metadata["chunk_id"] = f"{source_file}::{title}::{source_page or 'no-page'}::{index}"
            prepared.append({"text": piece, "metadata": chunk_metadata})
    return prepared
