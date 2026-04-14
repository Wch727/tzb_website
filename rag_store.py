"""RAG 存储、导入与向量查询。"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import chromadb
except Exception as exc:  # pragma: no cover
    chromadb = None
    CHROMA_IMPORT_ERROR = exc
else:
    CHROMA_IMPORT_ERROR = None

from chunking import attach_metadata
from embeddings import get_embedding_provider
from knowledge_base import build_knowledge_base, load_uploaded_raw_docs
from utils import CHROMA_DIR, DATA_DIR, RUNTIME_DIR, get_settings, read_json, write_json


REPOSITORY_MANIFEST_PATH = RUNTIME_DIR / "repository_content_manifest.json"


def ensure_chroma_ready() -> None:
    """确保 Chroma 依赖可用。"""
    if chromadb is not None:
        return
    detail = str(CHROMA_IMPORT_ERROR) if CHROMA_IMPORT_ERROR else "未知依赖错误"
    raise RuntimeError(
        "Chroma 依赖加载失败，请检查 requirements.txt 中 chromadb、protobuf、opentelemetry 的版本是否兼容。"
        f" 当前错误：{detail}"
    )


def embedder():
    """获取当前 embedding provider。"""
    return get_embedding_provider()


def _client() -> chromadb.PersistentClient:
    ensure_chroma_ready()
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


def _repository_signature() -> str:
    tracked_files = [
        path
        for path in sorted(DATA_DIR.iterdir(), key=lambda item: item.name.lower())
        if path.is_file() and path.suffix.lower() in [".json", ".csv", ".txt", ".md", ".pdf", ".docx"]
    ]
    digest = hashlib.sha256()
    for path in tracked_files:
        digest.update(path.name.encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _write_repository_manifest() -> None:
    write_json(
        REPOSITORY_MANIFEST_PATH,
        {
            "signature": _repository_signature(),
            "tracked_dir": str(DATA_DIR),
        },
    )


def _repository_manifest_matches() -> bool:
    manifest = read_json(REPOSITORY_MANIFEST_PATH, {}) or {}
    return manifest.get("signature") == _repository_signature()


def _source_files_from_docs(documents: List[Dict[str, Any]]) -> List[str]:
    names = {
        doc.get("metadata", {}).get("source_file", "")
        for doc in documents
        if doc.get("metadata", {}).get("source_file")
    }
    return sorted(names)


def _upsert_documents(documents: List[Dict[str, Any]]) -> Dict[str, Any]:
    settings = get_settings()
    collection = get_collection()
    chunk_size = int(settings.get("chunk_size", 520))
    chunk_overlap = int(settings.get("chunk_overlap", 90))
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
    embeddings = embedder().embed_documents(texts)
    collection.add(ids=ids, documents=texts, metadatas=metadatas, embeddings=embeddings)

    source_type_counts: Dict[str, int] = {}
    for metadata in metadatas:
        source_type = str(metadata.get("source_type", "unknown") or "unknown")
        source_type_counts[source_type] = source_type_counts.get(source_type, 0) + 1
    return {
        "document_count": len(documents),
        "chunk_count": len(chunked_docs),
        "source_files": _source_files_from_docs(documents),
        "source_type_counts": source_type_counts,
        "embedding_provider": embedder().provider_name,
    }


def ingest_default_data() -> Dict[str, Any]:
    """导入仓库内置的结构化卡与原始资料。"""
    knowledge_base = build_knowledge_base(include_structured=True, include_repository_raw=True)
    result = _upsert_documents(knowledge_base["all_docs"])
    result["mode"] = "default_data"
    result["structured_card_count"] = len(knowledge_base["structured_docs"])
    result["repository_raw_count"] = len(knowledge_base["raw_docs"])
    _write_repository_manifest()
    return result


def ingest_uploaded_files() -> Dict[str, Any]:
    """增量导入管理员上传文件。"""
    documents = load_uploaded_raw_docs()
    if not documents:
        return {
            "mode": "uploaded_files",
            "document_count": 0,
            "chunk_count": 0,
            "source_files": [],
            "message": "当前没有需要导入的上传文件。",
        }
    result = _upsert_documents(documents)
    result["mode"] = "uploaded_files"
    return result


def rebuild_knowledge_base() -> Dict[str, Any]:
    """重建知识库索引。"""
    get_collection(reset=True)
    default_result = ingest_default_data()
    upload_result = ingest_uploaded_files()
    return {
        "message": "知识库已完成重建。",
        "default_result": default_result,
        "upload_result": upload_result,
        "status": get_rag_status(),
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
    """确保仓库内置知识库已经初始化。"""
    ensure_chroma_ready()
    collection = get_collection()
    if collection.count() == 0:
        default_result = ingest_default_data()
        return {
            "message": "已根据仓库内置 data/ 内容初始化知识库。",
            "initialized": True,
            "default_result": default_result,
            "status": get_rag_status(),
        }
    if not _repository_manifest_matches():
        rebuild_result = rebuild_knowledge_base()
        return {
            "message": "检测到仓库内置内容已更新，知识库已自动重建。",
            "initialized": True,
            "default_result": rebuild_result.get("default_result", {}),
            "status": rebuild_result.get("status", {}),
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


def query_by_vector(question: str, where: Optional[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
    """执行带过滤条件的向量检索。"""
    collection = get_collection()
    result = collection.query(
        query_embeddings=[embedder().embed_query(question)],
        n_results=max(limit, 1),
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
                "text": document or "",
                "metadata": metadata or {},
                "distance": float(distance),
                "vector_score": round(max(0.0, 1.2 - float(distance)), 6),
            }
        )
    return hits


def snapshot_items(where: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """读取指定过滤条件下的全部候选项。"""
    collection = get_collection()
    count = collection.count()
    if count <= 0:
        return []
    result = collection.get(where=where, limit=max(count, 1), include=["documents", "metadatas"])
    ids = result.get("ids", []) or []
    documents = result.get("documents", []) or []
    metadatas = result.get("metadatas", []) or []
    items: List[Dict[str, Any]] = []
    for index, (document, metadata) in enumerate(zip(documents, metadatas)):
        item_metadata = (metadata or {}).copy()
        if ids and index < len(ids) and not item_metadata.get("chunk_id"):
            item_metadata["chunk_id"] = ids[index]
        items.append({"text": document or "", "metadata": item_metadata})
    return items


def get_rag_status() -> Dict[str, Any]:
    """查看知识库状态。"""
    ensure_chroma_ready()
    collection = get_collection()
    chunk_count = collection.count()
    result = collection.get(limit=max(chunk_count, 1), include=["metadatas", "documents"])
    metadatas = result.get("metadatas", []) or []
    documents = result.get("documents", []) or []

    unique_documents = {
        (metadata.get("source_file", ""), metadata.get("title", ""))
        for metadata in metadatas
        if isinstance(metadata, dict)
    }
    source_type_counts: Dict[str, int] = {}
    metadata_samples = []
    for index, (metadata, document) in enumerate(zip(metadatas, documents)):
        source_type = str(metadata.get("source_type", "unknown") or "unknown")
        source_type_counts[source_type] = source_type_counts.get(source_type, 0) + 1
        if index < 6:
            metadata_samples.append({"metadata": metadata, "preview": (document or "")[:150]})
    return {
        "collection_name": _collection_name(),
        "chunk_count": chunk_count,
        "document_count": len(unique_documents),
        "source_type_counts": source_type_counts,
        "embedding_provider": embedder().provider_name,
        "metadata_samples": metadata_samples,
    }
