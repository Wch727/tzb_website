"""RAG 统一对外入口。"""

from rag_intent import detect_query_intent
from rag_response import ask, fallback_answer, format_source_cards, test_retrieval
from rag_search import retrieve_knowledge, search_knowledge
from rag_store import (
    delete_source_file_from_rag,
    ensure_default_knowledge_base,
    get_collection,
    get_rag_status,
    incremental_ingest,
    rebuild_knowledge_base,
)

__all__ = [
    "ask",
    "delete_source_file_from_rag",
    "detect_query_intent",
    "ensure_default_knowledge_base",
    "fallback_answer",
    "format_source_cards",
    "get_collection",
    "get_rag_status",
    "incremental_ingest",
    "rebuild_knowledge_base",
    "retrieve_knowledge",
    "search_knowledge",
    "test_retrieval",
]
