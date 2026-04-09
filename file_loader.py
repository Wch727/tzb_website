"""上传文件与默认数据的加载器。"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any, Dict, List

from docx import Document as DocxDocument
from pypdf import PdfReader

from utils import (
    PROCESSED_DIR,
    infer_knowledge_type,
    normalize_knowledge_type,
    processed_filename,
    save_text_file,
)


def _read_text(path: Path) -> str:
    """按常见编码读取文本文件。"""
    for encoding in ["utf-8", "utf-8-sig", "gbk"]:
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="ignore")


def _normalize_text(text: str) -> str:
    """做基础文本标准化，方便后续切片和检索。"""
    cleaned = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def _base_metadata(path: Path) -> Dict[str, Any]:
    """生成基础元数据。"""
    suffix = path.suffix.lower().lstrip(".")
    inferred_type = infer_knowledge_type(path.stem)
    return {
        "source_file": path.name,
        "doc_type": suffix,
        "topic": "长征史",
        "type": normalize_knowledge_type(inferred_type),
        "title": path.stem,
        "route_stage": "",
        "place": "",
    }


def _record_to_text(record: Dict[str, Any]) -> str:
    """将结构化记录转成便于检索的文本。"""
    lines: List[str] = []
    for key, value in record.items():
        if value in (None, ""):
            continue
        lines.append(f"{key}：{_value_to_text(value)}")
    return "\n".join(lines)


def _value_to_text(value: Any) -> str:
    """把复杂字段转换为可读文本。"""
    if isinstance(value, list):
        return "；".join(_value_to_text(item) for item in value)
    if isinstance(value, dict):
        return "；".join(f"{key}：{_value_to_text(item)}" for key, item in value.items())
    return str(value)


def _record_metadata(base: Dict[str, Any], record: Dict[str, Any]) -> Dict[str, Any]:
    """从记录中补齐元数据。"""
    metadata = base.copy()
    if record.get("title"):
        metadata["title"] = str(record["title"])
    if record.get("topic"):
        metadata["topic"] = str(record["topic"])
    if record.get("route_stage"):
        metadata["route_stage"] = str(record["route_stage"])
    if record.get("place"):
        metadata["place"] = str(record["place"])
    if record.get("date"):
        metadata["date"] = str(record["date"])
    if record.get("figures"):
        metadata["figures"] = _value_to_text(record["figures"])
    raw_type = record.get("type") or metadata.get("type", "")
    metadata["type"] = normalize_knowledge_type(str(raw_type))
    return metadata


def _build_card_title(base_title: str, text: str, index: int) -> str:
    """为拆出的知识卡片生成标题。"""
    first_line = next((line.strip() for line in text.splitlines() if line.strip()), "")
    candidate = first_line[:28] if first_line else base_title
    if not candidate:
        candidate = base_title or f"知识卡片 {index + 1}"
    if candidate == base_title:
        return candidate if index == 0 else f"{candidate}（片段 {index + 1}）"
    return candidate


def _text_to_docs(path: Path, text: str) -> List[Dict[str, Any]]:
    """将长文本整理成若干知识卡片。"""
    normalized = _normalize_text(text)
    if not normalized:
        return []

    base = _base_metadata(path)
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", normalized) if part.strip()]
    if not paragraphs:
        return [{"text": normalized, "metadata": base.copy()}]

    docs: List[Dict[str, Any]] = []
    buffer = ""
    card_index = 0
    for paragraph in paragraphs:
        candidate = f"{buffer}\n\n{paragraph}".strip() if buffer else paragraph
        if len(candidate) <= 700:
            buffer = candidate
            continue
        if buffer:
            metadata = base.copy()
            metadata["title"] = _build_card_title(base["title"], buffer, card_index)
            metadata["type"] = infer_knowledge_type(metadata["title"], buffer)
            docs.append({"text": buffer, "metadata": metadata})
            card_index += 1
        buffer = paragraph

    if buffer:
        metadata = base.copy()
        metadata["title"] = _build_card_title(base["title"], buffer, card_index)
        metadata["type"] = infer_knowledge_type(metadata["title"], buffer)
        docs.append({"text": buffer, "metadata": metadata})

    return docs or [{"text": normalized, "metadata": base.copy()}]


def load_txt(path: Path) -> Dict[str, Any]:
    """读取 txt 文件。"""
    text = _read_text(path).strip()
    docs = _text_to_docs(path, text)
    return {"docs": docs, "raw_text": _normalize_text(text)}


def load_md(path: Path) -> Dict[str, Any]:
    """读取 md 文件。"""
    return load_txt(path)


def load_pdf(path: Path) -> Dict[str, Any]:
    """提取 PDF 文本，不做 OCR。"""
    reader = PdfReader(str(path))
    pages: List[str] = []
    for index, page in enumerate(reader.pages, start=1):
        page_text = _normalize_text(page.extract_text() or "")
        if page_text:
            pages.append(f"第{index}页\n{page_text}")
    text = "\n\n".join(pages)
    docs = _text_to_docs(path, text)
    return {"docs": docs, "raw_text": _normalize_text(text)}


def load_docx(path: Path) -> Dict[str, Any]:
    """读取 docx 文本。"""
    document = DocxDocument(str(path))
    paragraphs = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
    text = "\n".join(paragraphs)
    docs = _text_to_docs(path, text)
    return {"docs": docs, "raw_text": _normalize_text(text)}


def load_json(path: Path) -> Dict[str, Any]:
    """读取 JSON 文件，可按记录导入。"""
    content = json.loads(_read_text(path))
    base = _base_metadata(path)
    docs: List[Dict[str, Any]] = []
    raw_parts: List[str] = []

    if isinstance(content, list):
        records = content
    elif isinstance(content, dict) and isinstance(content.get("items"), list):
        records = content["items"]
    else:
        records = [content]

    for record in records:
        if isinstance(record, dict):
            text = _record_to_text(record)
            metadata = _record_metadata(base, record)
        else:
            text = str(record)
            metadata = base.copy()
            metadata["type"] = infer_knowledge_type(base.get("title", ""), text)
        if text.strip():
            docs.append({"text": _normalize_text(text), "metadata": metadata})
            raw_parts.append(text)

    return {"docs": docs, "raw_text": _normalize_text("\n\n".join(raw_parts))}


def load_csv(path: Path) -> Dict[str, Any]:
    """读取 CSV 文件，可按行导入。"""
    docs: List[Dict[str, Any]] = []
    raw_parts: List[str] = []
    base = _base_metadata(path)

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            text = _record_to_text(row)
            if not text.strip():
                continue
            metadata = _record_metadata(base, row)
            docs.append({"text": _normalize_text(text), "metadata": metadata})
            raw_parts.append(text)

    return {"docs": docs, "raw_text": _normalize_text("\n\n".join(raw_parts))}


def load_file(path: Path) -> Dict[str, Any]:
    """按后缀自动选择加载器。"""
    suffix = path.suffix.lower()
    loaders = {
        ".txt": load_txt,
        ".md": load_md,
        ".pdf": load_pdf,
        ".docx": load_docx,
        ".json": load_json,
        ".csv": load_csv,
    }
    if suffix not in loaders:
        raise ValueError(f"暂不支持的文件类型：{suffix}")
    return loaders[suffix](path)


def persist_processed_text(source_filename: str, raw_text: str) -> Path:
    """将处理后的纯文本保存到 processed 目录。"""
    processed_name = processed_filename(source_filename)
    return save_text_file(PROCESSED_DIR, processed_name, _normalize_text(raw_text))
