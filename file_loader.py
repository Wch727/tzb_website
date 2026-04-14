"""上传文件与默认数据的加载器。"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional

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
    cleaned = cleaned.replace("\u3000", " ")
    cleaned = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", "", cleaned)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def _normalize_line(line: str) -> str:
    """标准化单行文本。"""
    line = str(line or "").replace("\u3000", " ").strip()
    line = re.sub(r"[ \t]+", " ", line)
    return line


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
        "chapter_title": "",
        "section_title": "",
        "source_page": "",
        "source_page_start": "",
        "source_page_end": "",
    }


def _docs_to_blocks(path: Path, docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """把结构化文档进一步展开为 block 视图，便于调试与后续扩展。"""
    blocks: List[Dict[str, Any]] = []
    page_orders: Dict[str, int] = {}
    emitted_headings: set[tuple[str, str, str]] = set()
    for doc in docs:
        metadata = doc.get("metadata", {}) or {}
        page = str(
            metadata.get("source_page_start")
            or metadata.get("source_page")
            or metadata.get("source_page_end")
            or ""
        )
        chapter_title = str(metadata.get("chapter_title", "") or "")
        section_title = str(metadata.get("section_title", "") or "")
        source_file = str(metadata.get("source_file", path.name) or path.name)
        key = page or "global"
        page_orders.setdefault(key, 0)

        for block_text, block_type in [
            (chapter_title, "title"),
            (section_title, "heading"),
        ]:
            heading_key = (key, block_type, block_text)
            if block_text and heading_key not in emitted_headings:
                page_orders[key] += 1
                blocks.append(
                    {
                        "text": block_text,
                        "page": page,
                        "source_file": source_file,
                        "chapter_title": chapter_title,
                        "section_title": section_title,
                        "block_type": block_type,
                        "order_in_page": page_orders[key],
                    }
                )
                emitted_headings.add(heading_key)

        page_orders[key] += 1
        blocks.append(
            {
                "text": _normalize_text(doc.get("text", "")),
                "page": page,
                "source_file": source_file,
                "chapter_title": chapter_title,
                "section_title": section_title,
                "block_type": "paragraph",
                "order_in_page": page_orders[key],
            }
        )
    return [block for block in blocks if block.get("text")]


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
    if record.get("chapter_title"):
        metadata["chapter_title"] = str(record["chapter_title"])
    if record.get("section_title"):
        metadata["section_title"] = str(record["section_title"])
    if record.get("source_page"):
        metadata["source_page"] = str(record["source_page"])
    raw_type = record.get("type") or metadata.get("type", "")
    metadata["type"] = normalize_knowledge_type(str(raw_type))
    return metadata


def _is_noise_line(line: str) -> bool:
    """识别明显无意义的页眉页脚或页码。"""
    text = _normalize_line(line)
    if not text:
        return True
    if re.fullmatch(r"[—\-_=·•…\.\s]+", text):
        return True
    if re.fullmatch(r"第?\s*\d+\s*页", text):
        return True
    if re.fullmatch(r"\d+", text):
        return True
    return False


def _is_probable_heading(line: str) -> bool:
    """用轻量规则识别标题。"""
    text = _normalize_line(line)
    if not text:
        return False
    if len(text) > 34:
        return False
    if text.endswith(("。", "？", "！", "；")):
        return False
    if text.count("，") >= 2:
        return False
    heading_patterns = [
        r"^第[一二三四五六七八九十百千万0-9]+[章节篇部分]",
        r"^[一二三四五六七八九十]+[、.]",
        r"^\(?[0-9一二三四五六七八九十]+\)?[、.]",
    ]
    if any(re.match(pattern, text) for pattern in heading_patterns):
        return True
    keywords = ["会议", "战役", "会师", "转兵", "出发", "渡河", "桥", "雪山", "草地", "精神", "意义"]
    return any(keyword in text for keyword in keywords) and len(text) <= 22


def _is_probable_chapter_heading(line: str) -> bool:
    """识别更高层级的章节标题。"""
    text = _normalize_line(line)
    return bool(re.match(r"^第[一二三四五六七八九十百千万0-9]+[章节篇部分]", text))


def _clean_page_lines(text: str) -> List[str]:
    """把页面文本整理成较稳定的行列表。"""
    normalized = _normalize_text(text)
    lines = []
    for line in normalized.splitlines():
        cleaned = _normalize_line(line)
        lines.append(cleaned)
    return lines


def _strip_repeated_page_noise(pages: List[List[str]]) -> List[List[str]]:
    """剔除多页中重复出现的页眉页脚。"""
    counter: Counter[str] = Counter()
    for lines in pages:
        unique_lines = {line for line in lines if 2 <= len(line) <= 30}
        counter.update(unique_lines)

    repeated = {
        line
        for line, count in counter.items()
        if count >= max(3, len(pages) // 3) and not _is_probable_heading(line)
    }
    cleaned_pages: List[List[str]] = []
    for lines in pages:
        cleaned_pages.append([line for line in lines if line not in repeated and not _is_noise_line(line)])
    return cleaned_pages


def _build_doc_title(base_title: str, chapter_title: str, section_title: str, index: int) -> str:
    """为结构化块生成标题。"""
    if section_title:
        return section_title
    if chapter_title:
        return chapter_title if index == 0 else f"{chapter_title}（片段{index + 1}）"
    return base_title if index == 0 else f"{base_title}（片段{index + 1}）"


def _build_structured_block(
    base: Dict[str, Any],
    paragraph: str,
    index: int,
    chapter_title: str,
    section_title: str,
    source_page_start: Optional[int] = None,
    source_page_end: Optional[int] = None,
) -> Dict[str, Any]:
    """把单个结构化段落转成知识卡片。"""
    metadata = base.copy()
    metadata["chapter_title"] = chapter_title or base.get("title", "")
    metadata["section_title"] = section_title
    if source_page_start:
        metadata["source_page_start"] = str(source_page_start)
        metadata["source_page_end"] = str(source_page_end or source_page_start)
        metadata["source_page"] = (
            str(source_page_start)
            if source_page_start == (source_page_end or source_page_start)
            else f"{source_page_start}-{source_page_end or source_page_start}"
        )
    title = _build_doc_title(base.get("title", ""), chapter_title, section_title, index)
    metadata["title"] = title
    metadata["type"] = infer_knowledge_type(title, paragraph)
    return {
        "text": _normalize_text(paragraph),
        "metadata": metadata,
    }


def _coalesce_blocks(blocks: List[Dict[str, Any]], max_chars: int = 960) -> List[Dict[str, Any]]:
    """把相邻的小段落合并成更完整的知识块。"""
    if not blocks:
        return []

    merged: List[Dict[str, Any]] = []
    current = blocks[0].copy()
    for block in blocks[1:]:
        current_text = str(current.get("text", "") or "")
        block_text = str(block.get("text", "") or "")
        current_meta = current.get("metadata", {})
        block_meta = block.get("metadata", {})
        same_scope = (
            current_meta.get("chapter_title", "") == block_meta.get("chapter_title", "")
            and current_meta.get("section_title", "") == block_meta.get("section_title", "")
            and current_meta.get("source_file", "") == block_meta.get("source_file", "")
        )
        if same_scope and len(current_text) + len(block_text) <= max_chars:
            current["text"] = f"{current_text}\n\n{block_text}".strip()
            start_page = current_meta.get("source_page_start", "") or block_meta.get("source_page_start", "")
            end_page = block_meta.get("source_page_end", "") or current_meta.get("source_page_end", "")
            if start_page:
                current_meta["source_page_start"] = start_page
                current_meta["source_page_end"] = end_page or start_page
                current_meta["source_page"] = (
                    str(start_page)
                    if str(start_page) == str(end_page or start_page)
                    else f"{start_page}-{end_page or start_page}"
                )
            continue
        merged.append(current)
        current = block.copy()
    merged.append(current)

    for index, block in enumerate(merged):
        metadata = block.get("metadata", {})
        metadata["title"] = _build_doc_title(
            metadata.get("title", metadata.get("source_file", "文档")),
            metadata.get("chapter_title", ""),
            metadata.get("section_title", ""),
            index,
        )
    return merged


def _structured_docs_from_lines(
    path: Path,
    lines: List[str],
    page_number: Optional[int] = None,
    initial_chapter_title: str = "",
) -> List[Dict[str, Any]]:
    """根据文本行抽取结构化块。"""
    base = _base_metadata(path)
    chapter_title = initial_chapter_title or base.get("title", "")
    section_title = ""
    paragraph_buffer: List[str] = []
    blocks: List[Dict[str, Any]] = []

    def flush_paragraph() -> None:
        nonlocal paragraph_buffer
        paragraph = "\n".join(paragraph_buffer).strip()
        if paragraph:
            blocks.append(
                _build_structured_block(
                    base=base,
                    paragraph=paragraph,
                    index=len(blocks),
                    chapter_title=chapter_title,
                    section_title=section_title,
                    source_page_start=page_number,
                    source_page_end=page_number,
                )
            )
        paragraph_buffer = []

    for raw_line in lines:
        line = _normalize_line(raw_line)
        if not line:
            flush_paragraph()
            continue
        if _is_probable_heading(line):
            flush_paragraph()
            if _is_probable_chapter_heading(line):
                chapter_title = line
                section_title = ""
            else:
                section_title = line
            continue
        paragraph_buffer.append(line)

    flush_paragraph()
    return _coalesce_blocks(blocks)


def _text_to_docs(path: Path, text: str) -> List[Dict[str, Any]]:
    """将长文本整理成带结构元数据的知识卡片。"""
    normalized = _normalize_text(text)
    if not normalized:
        return []
    lines = []
    for paragraph in re.split(r"\n\s*\n", normalized):
        part = _normalize_text(paragraph)
        if not part:
            continue
        lines.extend(part.splitlines())
        lines.append("")
    docs = _structured_docs_from_lines(path, lines)
    if docs:
        return docs
    return [{"text": normalized, "metadata": _base_metadata(path)}]


def load_txt(path: Path) -> Dict[str, Any]:
    """读取 txt 文件。"""
    text = _read_text(path).strip()
    docs = _text_to_docs(path, text)
    return {"docs": docs, "raw_text": _normalize_text(text), "blocks": _docs_to_blocks(path, docs)}


def load_md(path: Path) -> Dict[str, Any]:
    """读取 md 文件。"""
    return load_txt(path)


def load_pdf(path: Path) -> Dict[str, Any]:
    """提取 PDF 文本，并尽量保留页码与标题层级。"""
    reader = PdfReader(str(path))
    page_line_bundles: List[List[str]] = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        page_lines = _clean_page_lines(page_text)
        page_line_bundles.append(page_lines)

    cleaned_pages = _strip_repeated_page_noise(page_line_bundles)
    docs: List[Dict[str, Any]] = []
    raw_pages: List[str] = []
    current_chapter_title = ""
    for index, lines in enumerate(cleaned_pages, start=1):
        if not lines:
            continue
        raw_pages.append(f"第{index}页\n" + "\n".join(lines))
        page_docs = _structured_docs_from_lines(
            path=path,
            lines=lines,
            page_number=index,
            initial_chapter_title=current_chapter_title,
        )
        if page_docs:
            current_chapter_title = page_docs[-1].get("metadata", {}).get("chapter_title", current_chapter_title)
        docs.extend(page_docs)

    docs = _coalesce_blocks(docs, max_chars=1100)
    text = "\n\n".join(raw_pages)
    final_docs = docs or _text_to_docs(path, text)
    return {"docs": final_docs, "raw_text": _normalize_text(text), "blocks": _docs_to_blocks(path, final_docs)}


def load_docx(path: Path) -> Dict[str, Any]:
    """读取 docx 文本，并保留段落与标题结构。"""
    document = DocxDocument(str(path))
    lines: List[str] = []
    for paragraph in document.paragraphs:
        text = _normalize_line(paragraph.text)
        if not text:
            lines.append("")
            continue
        style_name = str(getattr(paragraph.style, "name", "") or "").lower()
        if "heading" in style_name:
            lines.append(text)
            lines.append("")
        else:
            lines.append(text)
    raw_text = "\n".join(line for line in lines if line is not None)
    docs = _structured_docs_from_lines(path, lines)
    final_docs = docs or _text_to_docs(path, raw_text)
    return {"docs": final_docs, "raw_text": _normalize_text(raw_text), "blocks": _docs_to_blocks(path, final_docs)}


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

    return {"docs": docs, "raw_text": _normalize_text("\n\n".join(raw_parts)), "blocks": _docs_to_blocks(path, docs)}


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

    return {"docs": docs, "raw_text": _normalize_text("\n\n".join(raw_parts)), "blocks": _docs_to_blocks(path, docs)}


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
