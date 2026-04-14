"""排行榜与战绩记录。"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List

from utils import RUNTIME_DIR, read_json, write_json

LEADERBOARD_PATH = RUNTIME_DIR / "leaderboard.json"


def _load_entries() -> List[Dict[str, Any]]:
    """读取原始战绩。"""
    return read_json(LEADERBOARD_PATH, []) or []


def _save_entries(entries: List[Dict[str, Any]]) -> None:
    """写入原始战绩。"""
    write_json(LEADERBOARD_PATH, entries)


def _parse_time(value: str) -> datetime | None:
    """解析时间。"""
    try:
        return datetime.strptime(str(value or ""), "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


def record_leaderboard_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    """写入一次活动成绩。"""
    entries = _load_entries()
    normalized = {
        "user_name": str(entry.get("user_name", "匿名学习者") or "匿名学习者"),
        "unit_name": str(entry.get("unit_name", "未填写单位") or "未填写单位"),
        "role_name": str(entry.get("role_name", "") or ""),
        "activity_id": str(entry.get("activity_id", "global") or "global"),
        "activity_name": str(entry.get("activity_name", "全局闯关") or "全局闯关"),
        "team_id": str(entry.get("team_id", "") or ""),
        "team_name": str(entry.get("team_name", "") or ""),
        "branch_name": str(entry.get("branch_name", entry.get("unit_name", "未填写单位")) or entry.get("unit_name", "未填写单位")),
        "score": int(entry.get("score", 0) or 0),
        "grain": int(entry.get("grain", 0) or 0),
        "rank_title": str(entry.get("rank_title", "红军新兵") or "红军新兵"),
        "medals": list(entry.get("medals", []) or []),
        "completed_nodes": int(entry.get("completed_nodes", 0) or 0),
        "answered_count": int(entry.get("answered_count", 0) or 0),
        "finished_at": entry.get("finished_at") or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    entries.append(normalized)
    if len(entries) > 5000:
        entries = entries[-5000:]
    _save_entries(entries)
    return normalized


def _rank_entries(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """按成绩排序。"""
    sorted_entries = sorted(
        entries,
        key=lambda row: (
            -int(row.get("score", 0)),
            -int(row.get("grain", 0)),
            -int(row.get("completed_nodes", 0)),
            row.get("finished_at", ""),
        ),
    )
    ranked: List[Dict[str, Any]] = []
    for index, item in enumerate(sorted_entries, start=1):
        row = item.copy()
        row["rank"] = index
        ranked.append(row)
    return ranked


def _best_rows_by_user(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """按用户保留最佳成绩。"""
    buckets: Dict[str, Dict[str, Any]] = {}
    for item in entries:
        key = f"{item.get('activity_id', 'global')}::{item.get('user_name', '')}"
        current = buckets.get(key)
        if not current:
            buckets[key] = item
            continue
        better = (
            int(item.get("score", 0)),
            int(item.get("grain", 0)),
            int(item.get("completed_nodes", 0)),
            item.get("finished_at", ""),
        ) > (
            int(current.get("score", 0)),
            int(current.get("grain", 0)),
            int(current.get("completed_nodes", 0)),
            current.get("finished_at", ""),
        )
        if better:
            buckets[key] = item
    return list(buckets.values())


def get_global_leaderboard(limit: int = 20) -> List[Dict[str, Any]]:
    """查看全局排行榜。"""
    return _rank_entries(_load_entries())[:limit]


def get_activity_leaderboard(activity_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    """查看活动排行榜。"""
    rows = [item for item in _load_entries() if item.get("activity_id") == activity_id]
    return _rank_entries(rows)[:limit]


def get_live_leaderboard(activity_id: str = "", limit: int = 20, hours: int = 72) -> List[Dict[str, Any]]:
    """查看全服实时排行榜。"""
    cutoff = datetime.now() - timedelta(hours=max(1, hours))
    rows = []
    for item in _load_entries():
        ts = _parse_time(item.get("finished_at", ""))
        if ts and ts < cutoff:
            continue
        if activity_id and item.get("activity_id") != activity_id:
            continue
        rows.append(item)
    ranked = _rank_entries(_best_rows_by_user(rows))
    return ranked[:limit]


def get_live_battle_feed(activity_id: str = "", limit: int = 20, hours: int = 72) -> List[Dict[str, Any]]:
    """返回实时战绩流。"""
    cutoff = datetime.now() - timedelta(hours=max(1, hours))
    rows = []
    for item in _load_entries():
        ts = _parse_time(item.get("finished_at", ""))
        if ts and ts < cutoff:
            continue
        if activity_id and item.get("activity_id") != activity_id:
            continue
        row = item.copy()
        row["share_text"] = (
            f"{row.get('user_name', '匿名学习者')} 在“{row.get('activity_name', '长征活动')}”中"
            f"获得 {row.get('score', 0)} 分，当前军衔为 {row.get('rank_title', '红军新兵')}。"
        )
        rows.append(row)
    rows.sort(key=lambda item: item.get("finished_at", ""), reverse=True)
    return rows[:limit]


def get_user_battles(user_name: str, limit: int = 10) -> List[Dict[str, Any]]:
    """查看用户战绩。"""
    rows = [item for item in _load_entries() if item.get("user_name") == user_name]
    rows = sorted(rows, key=lambda item: item.get("finished_at", ""), reverse=True)
    return rows[:limit]


def build_user_share_text(user_name: str, activity_id: str = "") -> str:
    """生成个人战绩分享文案。"""
    rows = get_user_battles(user_name, limit=20)
    if activity_id:
        rows = [item for item in rows if item.get("activity_id") == activity_id]
    if not rows:
        return ""
    latest = rows[0]
    return (
        f"【长征战绩分享】{latest.get('user_name', '匿名学习者')} 在“{latest.get('activity_name', '长征活动')}”中"
        f"取得 {latest.get('score', 0)} 分、粮草 {latest.get('grain', 0)}，"
        f"当前军衔为 {latest.get('rank_title', '红军新兵')}，来自 {latest.get('unit_name', '未填写单位')}。"
    )


def get_unit_leaderboard(activity_id: str = "", limit: int = 20) -> List[Dict[str, Any]]:
    """按班级/单位聚合排行榜。"""
    rows = _load_entries()
    if activity_id:
        rows = [item for item in rows if item.get("activity_id") == activity_id]
    buckets: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        unit_name = str(row.get("unit_name", "未填写单位") or "未填写单位")
        bucket = buckets.setdefault(
            unit_name,
            {
                "unit_name": unit_name,
                "total_score": 0,
                "total_grain": 0,
                "member_names": set(),
                "best_rank_title": "",
                "_best_score": -1,
            },
        )
        bucket["total_score"] += int(row.get("score", 0))
        bucket["total_grain"] += int(row.get("grain", 0))
        bucket["member_names"].add(str(row.get("user_name", "") or "匿名学习者"))
        if int(row.get("score", 0)) >= int(bucket.get("_best_score", -1)):
            bucket["_best_score"] = int(row.get("score", 0))
            bucket["best_rank_title"] = str(row.get("rank_title", "") or "")
    ranked = sorted(
        buckets.values(),
        key=lambda item: (-int(item.get("total_score", 0)), -int(item.get("total_grain", 0)), item.get("unit_name", "")),
    )
    result: List[Dict[str, Any]] = []
    for index, item in enumerate(ranked[:limit], start=1):
        result.append(
            {
                "rank": index,
                "unit_name": item.get("unit_name", ""),
                "total_score": item.get("total_score", 0),
                "total_grain": item.get("total_grain", 0),
                "member_count": len(item.get("member_names", set())),
                "best_rank_title": item.get("best_rank_title", ""),
            }
        )
    return result


def export_leaderboard_rows(activity_id: str = "") -> List[Dict[str, Any]]:
    """导出排行榜数据。"""
    if activity_id:
        return get_activity_leaderboard(activity_id, limit=500)
    return get_global_leaderboard(limit=500)

