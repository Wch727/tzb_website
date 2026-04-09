"""知识库、向量检索与 RAG 服务。"""

from __future__ import annotations

import csv
import hashlib
import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb

from chunking import attach_metadata
from file_loader import load_file, persist_processed_text
from llm import get_llm_client
from prompts import LONG_MARCH_GUIDE_ROLE_PROMPT, build_rag_qa_prompt, format_context_blocks
from utils import CHROMA_DIR, DATA_DIR, UPLOAD_DIR, get_settings, normalize_knowledge_type


class HashEmbeddingFunction:
    """纯本地哈希向量，便于无外部依赖运行。"""

    def __init__(self, dimension: int = 192) -> None:
        self.dimension = dimension

    def _tokens(self, text: str) -> List[str]:
        text = (text or "").strip()
        if not text:
            return []
        tokens: List[str] = []
        buffer = ""
        for char in text:
            if "\u4e00" <= char <= "\u9fff":
                if buffer:
                    tokens.append(buffer.lower())
                    buffer = ""
                tokens.append(char)
            elif char.isalnum():
                buffer += char
            else:
                if buffer:
                    tokens.append(buffer.lower())
                    buffer = ""
        if buffer:
            tokens.append(buffer.lower())
        return tokens or list(text)

    def embed(self, text: str) -> List[float]:
        vector = [0.0] * self.dimension
        tokens = self._tokens(text)
        if not tokens:
            return vector
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign
        norm = sum(value * value for value in vector) ** 0.5 or 1.0
        return [value / norm for value in vector]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self.embed(text) for text in texts]

    def embed_query(self, text: str) -> List[float]:
        return self.embed(text)


EMBEDDER = HashEmbeddingFunction()
INTENT_TYPES: Dict[str, List[str]] = {
    "event": ["event"],
    "place": ["place", "route"],
    "figure": ["figure", "event"],
    "route": ["route", "event"],
    "faq": ["faq", "event", "spirit"],
    "spirit": ["spirit", "event", "route"],
    "generate_script": ["event", "route", "figure", "place", "spirit"],
    "timeline": ["route", "event"],
    "general": [],
}


def _client() -> chromadb.PersistentClient:
    """创建持久化 Chroma 客户端。"""
    return chromadb.PersistentClient(path=str(CHROMA_DIR))


def _collection_name() -> str:
    return get_settings().get("collection_name", "long_march_history")


def get_collection(reset: bool = False):
    """获取或重置集合。"""
    client = _client()
    name = _collection_name()
    if reset:
        try:
            client.delete_collection(name)
        except Exception:
            pass
    return client.get_or_create_collection(name=name, metadata={"hnsw:space": "cosine"})


def _normalize_filters(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """标准化过滤条件。"""
    normalized: Dict[str, Any] = {}
    if not filters:
        return normalized
    for key in ["type", "route_stage", "place", "source_file", "topic", "intent"]:
        value = filters.get(key)
        if value in (None, "", "全部"):
            continue
        if key == "type":
            if isinstance(value, list):
                normalized[key] = [normalize_knowledge_type(item) for item in value if item]
            else:
                normalized[key] = normalize_knowledge_type(str(value))
        else:
            normalized[key] = str(value)
    return normalized


def _build_where(filters: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """将筛选条件转换成 Chroma where 语法。"""
    normalized = _normalize_filters(filters)
    if not normalized:
        return None

    clauses = []
    for key in ["type", "route_stage", "place", "source_file", "topic"]:
        value = normalized.get(key)
        if value in (None, "", "全部"):
            continue
        if isinstance(value, list):
            continue
        clauses.append({key: value})

    if not clauses:
        return None
    if len(clauses) == 1:
        return clauses[0]
    return {"$and": clauses}


def _source_files_from_docs(documents: List[Dict[str, Any]]) -> List[str]:
    """提取本次导入涉及的来源文件。"""
    names = {
        doc.get("metadata", {}).get("source_file", "")
        for doc in documents
        if doc.get("metadata", {}).get("source_file")
    }
    return sorted(names)


def _upsert_documents(documents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """将文档切块后写入 Chroma。"""
    settings = get_settings()
    collection = get_collection()
    chunk_size = int(settings.get("chunk_size", 420))
    chunk_overlap = int(settings.get("chunk_overlap", 80))
    chunked_docs = attach_metadata(documents, chunk_size=chunk_size, overlap=chunk_overlap)

    if not chunked_docs:
        return {"document_count": len(documents), "chunk_count": 0, "source_files": []}

    for source_file in _source_files_from_docs(documents):
        try:
            collection.delete(where={"source_file": source_file})
        except Exception:
            pass

    texts = [item["text"] for item in chunked_docs]
    metadatas = [item["metadata"] for item in chunked_docs]
    ids = [metadata.get("chunk_id", f"chunk-{index}") for index, metadata in enumerate(metadatas)]
    embeddings = EMBEDDER.embed_documents(texts)

    collection.add(
        ids=ids,
        documents=texts,
        metadatas=metadatas,
        embeddings=embeddings,
    )

    return {
        "document_count": len(documents),
        "chunk_count": len(chunked_docs),
        "source_files": _source_files_from_docs(documents),
    }


def _load_files(paths: List[Path], persist_processed: bool = False) -> List[Dict[str, Any]]:
    """批量读取文件。"""
    documents: List[Dict[str, Any]] = []
    for path in paths:
        parsed = load_file(path)
        documents.extend(parsed.get("docs", []))
        if persist_processed:
            persist_processed_text(path.name, parsed.get("raw_text", ""))
    return documents


def ingest_default_data() -> Dict[str, Any]:
    """导入内置样例数据。"""
    files = [
        path
        for path in sorted(DATA_DIR.iterdir(), key=lambda item: item.name.lower())
        if path.is_file() and path.suffix.lower() in [".json", ".csv", ".txt", ".md", ".pdf", ".docx"]
    ]
    documents = _load_files(files, persist_processed=False)
    result = _upsert_documents(documents)
    result["mode"] = "default_data"
    return result


def ingest_uploaded_files() -> Dict[str, Any]:
    """增量导入管理员上传文件。"""
    files = [path for path in sorted(UPLOAD_DIR.iterdir(), key=lambda item: item.name.lower()) if path.is_file()]
    documents = _load_files(files, persist_processed=True)
    result = _upsert_documents(documents)
    result["mode"] = "uploaded_files"
    return result


def rebuild_knowledge_base() -> Dict[str, Any]:
    """重建知识库索引。"""
    get_collection(reset=True)
    default_result = ingest_default_data()
    upload_result = ingest_uploaded_files()
    status = get_rag_status()
    return {
        "message": "知识库已完成重建。",
        "default_result": default_result,
        "upload_result": upload_result,
        "status": status,
    }


def incremental_ingest() -> Dict[str, Any]:
    """执行增量导入。"""
    collection = get_collection()
    if collection.count() == 0:
        ingest_default_data()
    upload_result = ingest_uploaded_files()
    return {
        "message": "增量导入完成。",
        "upload_result": upload_result,
        "status": get_rag_status(),
    }


def ensure_default_knowledge_base() -> Dict[str, Any]:
    """确保仓库内置知识内容已经初始化到向量库。"""
    collection = get_collection()
    if collection.count() == 0:
        default_result = ingest_default_data()
        return {
            "message": "已根据仓库内置 data/ 内容初始化知识库。",
            "initialized": True,
            "default_result": default_result,
            "status": get_rag_status(),
        }
    return {
        "message": "仓库内置知识库已就绪。",
        "initialized": False,
        "status": get_rag_status(),
    }


def delete_source_file_from_rag(filename: str) -> Dict[str, Any]:
    """删除某个来源文件对应的向量数据。"""
    collection = get_collection()
    try:
        collection.delete(where={"source_file": filename})
        return {"message": f"已从知识库中清理来源文件：{filename}"}
    except Exception as exc:
        return {"message": f"向量清理时出现提示：{exc}"}


@lru_cache(maxsize=1)
def _load_route_nodes() -> List[Dict[str, str]]:
    """读取路线节点，用于意图识别。"""
    json_path = DATA_DIR / "route_nodes.json"
    if json_path.exists():
        content = json.loads(json_path.read_text(encoding="utf-8"))
        if isinstance(content, list):
            return [item for item in content if isinstance(item, dict)]

    path = DATA_DIR / "routes.csv"
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _match_route_node(question: str) -> Dict[str, str]:
    """匹配最相关的路线节点。"""
    best_node: Dict[str, str] = {}
    best_length = 0
    for node in _load_route_nodes():
        for candidate in [node.get("route_stage", ""), node.get("title", "")]:
            if candidate and candidate in question and len(candidate) > best_length:
                best_node = node
                best_length = len(candidate)
    return best_node


@lru_cache(maxsize=1)
def _load_json_titles(filename: str) -> List[str]:
    """读取默认 JSON 标题。"""
    path = DATA_DIR / filename
    if not path.exists():
        return []
    content = json.loads(path.read_text(encoding="utf-8"))
    titles: List[str] = []
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict) and item.get("title"):
                titles.append(str(item["title"]))
    return titles


def _match_longest_term(question: str, candidates: List[str]) -> str:
    """从候选词中找出命中的最长词。"""
    hits = [item for item in candidates if item and item in question]
    if not hits:
        return ""
    return sorted(hits, key=len, reverse=True)[0]


def detect_query_intent(question: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """对问题做轻量意图识别。"""
    _ = filters
    text = (question or "").strip()
    lowered = text.lower()

    route_nodes = _load_route_nodes()
    place_terms = _load_json_titles("places.json") + [item.get("place", "") for item in route_nodes]
    figure_terms = _load_json_titles("figures.json")

    matched_route_node = _match_route_node(text)
    route_stage = matched_route_node.get("route_stage", "")
    place = _match_longest_term(text, place_terms)
    figure = _match_longest_term(text, figure_terms)
    if matched_route_node and not place:
        place = matched_route_node.get("place", "")

    if any(keyword in text for keyword in ["讲解稿", "解说稿", "导览词", "讲解词", "视频脚本", "短视频脚本"]):
        intent = "generate_script"
    elif any(keyword in text for keyword in ["时间线", "时间轴", "路线图", "路线节点", "经过了哪些", "沿线", "历程"]):
        intent = "timeline"
    elif any(keyword in text for keyword in ["长征精神", "精神", "意义", "启示", "价值"]) and "人物精神" not in text:
        intent = "spirit"
    elif figure or any(keyword in text for keyword in ["人物", "谁是", "谁领导", "毛泽东", "周恩来", "朱德", "陈云"]):
        intent = "figure"
    elif route_stage or any(keyword in text for keyword in ["路线", "渡江", "会师", "赤水", "泸定桥", "行军"]):
        intent = "route"
    elif any(keyword in lowered for keyword in ["战役", "会议", "事件", "发生了什么", "何时", "什么时候"]):
        intent = "event"
    elif any(keyword in text for keyword in ["为什么", "是什么", "怎么理解", "有何意义", "最后到了哪里"]):
        intent = "faq"
    elif place or any(keyword in text for keyword in ["地点", "哪里", "在哪", "哪座桥", "哪条河", "旧址"]):
        intent = "place"
    else:
        intent = "general"

    return {
        "intent": intent,
        "type_filters": INTENT_TYPES.get(intent, []),
        "route_stage": route_stage,
        "place": place,
        "figure": figure,
    }


def _merge_filters(question: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """合并用户筛选与意图识别结果。"""
    normalized = _normalize_filters(filters)
    intent_info = detect_query_intent(question, filters=normalized)

    merged = normalized.copy()
    if not merged.get("type") and intent_info.get("type_filters"):
        merged["type"] = intent_info["type_filters"]
    if not merged.get("route_stage") and intent_info.get("route_stage"):
        merged["route_stage"] = intent_info["route_stage"]
    if not merged.get("place") and not merged.get("route_stage") and intent_info.get("place"):
        merged["place"] = intent_info["place"]
    return {
        "intent": intent_info["intent"],
        "filters": merged,
        "entities": {
            "route_stage": intent_info.get("route_stage", ""),
            "place": intent_info.get("place", ""),
            "figure": intent_info.get("figure", ""),
        },
    }


def _expand_filter_variants(filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    """将多类型过滤展开为多个查询。"""
    normalized = _normalize_filters(filters)
    type_value = normalized.get("type")
    if not isinstance(type_value, list):
        return [normalized]
    variants: List[Dict[str, Any]] = []
    for item in type_value:
        variant = normalized.copy()
        variant["type"] = item
        variants.append(variant)
    return variants or [normalized]


def _query_collection(question: str, filters: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
    """执行单次带过滤的向量检索。"""
    collection = get_collection()
    where = _build_where(filters)
    result = collection.query(
        query_embeddings=[EMBEDDER.embed_query(question)],
        n_results=limit,
        where=where,
        include=["documents", "metadatas", "distances"],
    )
    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]

    hits: List[Dict[str, Any]] = []
    for document, metadata, distance in zip(documents, metadatas, distances):
        hits.append(
            {
                "text": document,
                "metadata": metadata,
                "distance": distance,
            }
        )
    return hits


def retrieve_knowledge(
    question: str,
    filters: Optional[Dict[str, Any]] = None,
    top_k: Optional[int] = None,
) -> Dict[str, Any]:
    """执行带意图识别的知识检索。"""
    collection = get_collection()
    if collection.count() == 0:
        ingest_default_data()

    settings = get_settings()
    limit = top_k or int(settings.get("retrieval_top_k", 4))
    debug_info = _merge_filters(question=question, filters=filters)
    variants = _expand_filter_variants(debug_info["filters"])

    merged_hits: Dict[str, Dict[str, Any]] = {}
    for variant in variants:
        for hit in _query_collection(question=question, filters=variant, limit=max(limit, 4)):
            metadata = hit.get("metadata", {}) or {}
            chunk_id = metadata.get("chunk_id") or (
                f"{metadata.get('source_file', 'source')}::{metadata.get('title', '未命名')}::{metadata.get('chunk_index', 0)}"
            )
            old = merged_hits.get(chunk_id)
            if old is None or hit.get("distance", 1.0) < old.get("distance", 1.0):
                merged_hits[chunk_id] = hit

    hits = sorted(merged_hits.values(), key=lambda item: item.get("distance", 1.0))[:limit]
    return {
        "hits": hits,
        "intent": debug_info["intent"],
        "applied_filters": debug_info["filters"],
        "entities": debug_info["entities"],
    }


def search_knowledge(
    question: str,
    filters: Optional[Dict[str, Any]] = None,
    top_k: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """兼容旧调用的检索入口。"""
    return retrieve_knowledge(question=question, filters=filters, top_k=top_k)["hits"]


def _format_source_cards(hits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """整理前端展示依据所需的信息。"""
    cards: List[Dict[str, Any]] = []
    for item in hits:
        metadata = item.get("metadata", {}) or {}
        cards.append(
            {
                "source_file": metadata.get("source_file", "未知文件"),
                "title": metadata.get("title", "未命名"),
                "type": metadata.get("type", "未知"),
                "topic": metadata.get("topic", ""),
                "place": metadata.get("place", ""),
                "route_stage": metadata.get("route_stage", ""),
                "chunk_id": metadata.get("chunk_id", ""),
                "snippet": item.get("text", "")[:220],
            }
        )
    return cards


def ask(
    question: str,
    provider_config: Dict[str, Any],
    filters: Optional[Dict[str, Any]] = None,
    top_k: Optional[int] = None,
) -> Dict[str, Any]:
    """长征史 RAG 问答入口。"""
    retrieval = retrieve_knowledge(question=question, filters=filters, top_k=top_k)
    hits = retrieval["hits"]
    context_blocks = [
        f"来源：{item['metadata'].get('source_file', '未知')} | "
        f"标题：{item['metadata'].get('title', '未命名')} | "
        f"类型：{item['metadata'].get('type', '未知')} | "
        f"路线节点：{item['metadata'].get('route_stage', '未标注')}\n"
        f"{item['text']}"
        for item in hits
    ]
    prompt = build_rag_qa_prompt(question=question, context=format_context_blocks(context_blocks))
    client = get_llm_client(provider_config)
    result = client.chat(
        messages=[
            {"role": "system", "content": LONG_MARCH_GUIDE_ROLE_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        stream=False,
    )

    source_cards = _format_source_cards(hits)
    return {
        "answer": result.get("content", ""),
        "provider_used": result.get("provider", provider_config.get("provider_name", "mock")),
        "model_used": result.get("model", provider_config.get("model", "")),
        "warning": result.get("warning", ""),
        "fallback_used": result.get("fallback_used", False),
        "intent": retrieval.get("intent", "general"),
        "applied_filters": retrieval.get("applied_filters", {}),
        "retrieved_chunks": [item["text"] for item in hits],
        "retrieved_metadata": [item["metadata"] for item in hits],
        "source_file": [item["source_file"] for item in source_cards],
        "title": [item["title"] for item in source_cards],
        "sources": source_cards,
    }


def test_retrieval(
    question: str,
    filters: Optional[Dict[str, Any]] = None,
    top_k: Optional[int] = None,
) -> Dict[str, Any]:
    """用于管理员后台调试检索。"""
    retrieval = retrieve_knowledge(question=question, filters=filters, top_k=top_k)
    hits = retrieval["hits"]
    return {
        "question": question,
        "intent": retrieval.get("intent", "general"),
        "applied_filters": retrieval.get("applied_filters", {}),
        "entities": retrieval.get("entities", {}),
        "hit_count": len(hits),
        "hits": [
            {
                "distance": round(item.get("distance", 0.0), 4),
                "text": item.get("text", ""),
                "metadata": item.get("metadata", {}),
            }
            for item in hits
        ],
        "sources": _format_source_cards(hits),
    }


def get_rag_status() -> Dict[str, Any]:
    """查看知识库状态。"""
    collection = get_collection()
    chunk_count = collection.count()
    sample = collection.get(limit=8, include=["metadatas", "documents"])
    full_metadatas = collection.get(
        limit=max(chunk_count, 1),
        include=["metadatas"],
    ).get("metadatas", [])
    metadatas = sample.get("metadatas", [])
    documents = sample.get("documents", [])

    unique_documents = {
        (
            metadata.get("source_file", ""),
            metadata.get("title", ""),
        )
        for metadata in full_metadatas
        if isinstance(metadata, dict)
    }
    metadata_samples = []
    for metadata, document in zip(metadatas[:5], documents[:5]):
        metadata_samples.append(
            {
                "metadata": metadata,
                "preview": (document or "")[:150],
            }
        )

    return {
        "collection_name": _collection_name(),
        "chunk_count": chunk_count,
        "document_count": len(unique_documents),
        "metadata_samples": metadata_samples,
    }
