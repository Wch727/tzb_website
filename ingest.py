"""初始化默认数据与知识库。"""

from __future__ import annotations

import argparse
import json

from rag import get_rag_status, incremental_ingest, rebuild_knowledge_base
from utils import ensure_directories


def main() -> None:
    """命令行入口。"""
    parser = argparse.ArgumentParser(description="初始化《长征史》RAG 样例数据。")
    parser.add_argument("--rebuild", action="store_true", help="重建整个知识库索引。")
    args = parser.parse_args()

    ensure_directories()
    result = rebuild_knowledge_base() if args.rebuild else incremental_ingest()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(json.dumps(get_rag_status(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
