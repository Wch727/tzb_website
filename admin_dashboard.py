"""后台统计与导出。"""

from __future__ import annotations

import csv
import io
from typing import Any, Dict, List

from activity_manager import list_activities
from content_store import load_all_knowledge_items, load_route_nodes_data
from leaderboard import export_leaderboard_rows, get_global_leaderboard


def build_admin_metrics() -> List[Dict[str, Any]]:
    """构建后台统计指标。"""
    leaderboard_rows = get_global_leaderboard(limit=500)
    unique_users = len({row.get("user_name") for row in leaderboard_rows})
    return [
        {"label": "活动数", "value": len(list_activities())},
        {"label": "主线关卡数", "value": len(load_route_nodes_data())},
        {"label": "知识条目数", "value": len(load_all_knowledge_items())},
        {"label": "参与用户数", "value": unique_users},
    ]


def export_rows_to_csv(rows: List[Dict[str, Any]]) -> bytes:
    """导出 CSV。"""
    if not rows:
        return b""
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8-sig")


def export_leaderboard_csv(activity_id: str = "") -> bytes:
    """导出排行榜 CSV。"""
    return export_rows_to_csv(export_leaderboard_rows(activity_id))

