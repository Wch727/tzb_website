"""管理员检索调试工具。"""

from __future__ import annotations

from typing import Any, Dict, Optional

from rag import test_retrieval


def run_retrieval_debug(
    question: str,
    filters: Optional[Dict[str, Any]] = None,
    top_k: Optional[int] = None,
) -> Dict[str, Any]:
    """执行一次检索调试并返回结构化结果。"""
    return test_retrieval(question=question, filters=filters, top_k=top_k)
