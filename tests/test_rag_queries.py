"""RAG 查询基线测试。"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rag import ask, retrieve_knowledge


TEST_QUERIES = [
    "长征为什么开始？",
    "湘江战役为什么重要？",
    "遵义会议的意义是什么？",
    "四渡赤水体现了什么战略智慧？",
    "飞夺泸定桥为什么成为经典战例？",
    "长征精神包括哪些内容？",
]


def main() -> None:
    for question in TEST_QUERIES:
        retrieval = retrieve_knowledge(question=question, filters={}, top_k=5)
        result = ask(
            question=question,
            provider_config={"static_mode": True, "provider_name": "static", "model": "builtin-longmarch-content"},
            filters={},
            top_k=5,
        )
        first_hit = retrieval["hits"][0] if retrieval["hits"] else {"metadata": {}}
        first_meta = first_hit.get("metadata", {}) or {}
        uses_structured = any(
            (item.get("metadata", {}) or {}).get("source_type") == "structured_card"
            for item in retrieval.get("hits", [])
        )
        print("=" * 80)
        print(f"问题：{question}")
        print(f"识别意图：{retrieval.get('intent', 'general')}")
        print(f"识别目标：{retrieval.get('target', '') or '未识别'}")
        print(f"首个命中标题：{first_meta.get('title', '未命中')}")
        print(f"首个命中类型：{first_meta.get('type', '未知')}")
        print(f"回答字数：{result.get('output_length', len(result.get('answer', '')))}")
        print(f"是否达到目标字数：{(result.get('output_length', len(result.get('answer', ''))) >= 220)}")
        print(f"是否优先使用结构化知识卡：{uses_structured}")
        assert retrieval.get("hits"), f"问题未命中任何结果：{question}"
        assert result.get("output_length", len(result.get("answer", ""))) >= 220, f"回答过短：{question}"
        assert uses_structured, f"没有优先命中结构化知识卡：{question}"


if __name__ == "__main__":
    main()
