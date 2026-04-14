"""初始化默认数据与知识库。"""

from __future__ import annotations

import argparse
import json

from knowledge_base import export_uploaded_docs_as_prebuilt_chunks
from rag import get_rag_status, incremental_ingest, rebuild_knowledge_base
from utils import ensure_directories


def main() -> None:
    """命令行入口。"""
    parser = argparse.ArgumentParser(description="初始化《长征史》RAG 样例数据。")
    parser.add_argument("--rebuild", action="store_true", help="重建整个知识库索引。")
    parser.add_argument(
        "--export-local-chunks",
        action="store_true",
        help="将当前 storage/uploads 中的本地资料预切块并导出到 data/prebuilt_uploaded_chunks.jsonl。",
    )
    args = parser.parse_args()

    ensure_directories()
    if args.export_local_chunks:
        print(json.dumps(export_uploaded_docs_as_prebuilt_chunks(), ensure_ascii=False, indent=2))

    if args.rebuild or not args.export_local_chunks:
        result = rebuild_knowledge_base() if args.rebuild else incremental_ingest()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    print(json.dumps(get_rag_status(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
